import argparse
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import importlib.metadata
import sys
import shlex

import qbittorrentapi
from qbittorrentapi import Client, NotFound404Error
from rich import print
from rich.table import Table

DEFAULT_IGNORED_TRACKERS = {"** [DHT] **", "** [PeX] **", "** [LSD] **"}
connection_lost = False


class Spinner:
    busy = False
    delay = 0.1
    message = "\033[93mWaiting for connection to qBittorrent Web UI... \033[0m"

    @staticmethod
    def spinning_cursor():
        while 1:
            for cursor in '|/-\\':
                yield cursor

    def __init__(self, message=None, delay=None):
        self.spinner_generator = self.spinning_cursor()
        if delay and float(delay):
            self.delay = delay
        if message:
            self.message = f"\033[93m{message}\033[0m"

    def spinner_task(self):
        while self.busy:
            sys.stdout.write(f"\r{self.message}{next(self.spinner_generator)}")
            sys.stdout.flush()
            time.sleep(self.delay)

    def __enter__(self):
        self.busy = True
        threading.Thread(target=self.spinner_task).start()

    def __exit__(self, exception, value, tb):
        self.busy = False
        time.sleep(self.delay)
        print()
        if exception is not None:
            return False


def launch_qbittorrent():
    system = platform.system()

    if system == "Darwin":  # macOS
        app_path = "/Applications/qbittorrent.app"
        if os.path.exists(app_path):
            print("[yellow]Launching qBittorrent on macOS...[/yellow]")
            subprocess.Popen(["open", app_path])
        else:
            print("[red]qBittorrent.app not found in /Applications[/red]")

    elif system == "Windows":
        print("[yellow]Attempting to launch qBittorrent on Windows...[/yellow]")

        qbittorrent_path = shutil.which("qbittorrent")
        if qbittorrent_path:
            subprocess.Popen([qbittorrent_path], shell=True)
            print("[green]qBittorrent launched from PATH[/green]")
            return

        common_paths = [
            r"C:\Program Files\qBittorrent\qbittorrent.exe",
            r"C:\Program Files (x86)\qBittorrent\qbittorrent.exe"
        ]
        for path in common_paths:
            if os.path.exists(path):
                subprocess.Popen([path], shell=True)
                print(f"[green]qBittorrent launched from {path}[/green]")
                return

        print("[red]qBittorrent not found in PATH or standard locations[/red]")

    else:
        print("[yellow]Autolaunch not supported on this platform[/yellow]")


def login_qbittorrent(client, message):
    global connection_lost
    with Spinner(message=message):
        while True:
            try:
                client.auth_log_in()
                print("")
                print("[green]Connected to web qBittorrent Web UI[/green]")
                connection_lost = False
                break
            except Exception as e:
                msg = str(e) if str(e) else "Error authenticating with qBittorrent Web UI"
                print("")
                print(f"\n[red]Connection failed: {msg}[/red]")
                if not str(e):
                    print("[yellow]Please verify your host, port, username and password[/yellow]")
                    exit(1)
                print("[yellow]Please start qBittorrent Web UI[/yellow]")
                time.sleep(5)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Remove non-ignored trackers from active qBittorrent downloads.")

    parser.add_argument("-H", "--host", default="localhost", help="qBittorrent Web UI host")
    parser.add_argument("-P", "--port", type=int, default=8080, help="qBittorrent Web UI port")
    parser.add_argument("-U", "--username", default="admin", help="qBittorrent Web UI username")
    parser.add_argument("-PSW", "--password", default="123456", help="qBittorrent Web UI password")
    parser.add_argument("--no-verify", default=True, help="Disable SSL certificate verification")
    parser.add_argument("-MDL", "--min-dl-speed", type=int, default=10,
                        help="Minimum download speed in KB/s to remove trackers")
    parser.add_argument("--ignored-trackers", nargs="*", default=[],
                        help="Additional trackers to ignore (added to defaults)")
    parser.add_argument("-QBT", "--launch-qbt", default=True, help="Launch qBittorrent if not running")

    # Version
    try:
        version = importlib.metadata.version("trackersremoverqbt")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"
    parser.add_argument("-V", "--version", action="version", version=f"TrackersRemover-qBittorrent {version}",
                        help="Show program version and exit")

    return parser.parse_args(argv)


def main(host=None, port=None, username=None, password=None, no_verify=True, min_dl_speed=None,
         ignored_trackers=None, launch_qbt=True):

    argv = []

    if host is not None:
        argv += ["--host", host]
    if port is not None:
        argv += ["--port", str(port)]
    if username is not None:
        argv += ["--username", username]
    if password is not None:
        argv += ["--password", password]
    if no_verify is False:
        argv += ["--no-verify", "False"]
    if min_dl_speed is not None:
        argv += ["--min-dl-speed", str(min_dl_speed)]
    if ignored_trackers:
        argv += ["--ignored-trackers"] + ignored_trackers
    if launch_qbt is False:
        argv += ["--launch-qbt", "False"]

    args = parse_args(argv if argv else None)
    global connection_lost

    if args.launch_qbt:
        print("[blue]Attempting to launch qBittorrent...[/blue]")
        launch_qbittorrent()
        time.sleep(3)

    client = Client(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        VERIFY_WEBUI_CERTIFICATE=not args.no_verify
    )

    login_qbittorrent(client, message="Waiting for connection to qBittorrent Web UI...")

    IGNORED_TRACKERS = DEFAULT_IGNORED_TRACKERS.union(args.ignored_trackers)
    MIN_DL_SPEED = args.min_dl_speed

    previous_snapshot = {}

    while True:
        if connection_lost:
            login_qbittorrent(client, message="Connection lost, reconnecting to qBittorrent Web UI...")

        else:
            with Spinner(message="Trackers remover running..."):
                while True:
                    if not client.is_logged_in:
                        connection_lost = True
                        break

                    try:
                        all_torrents = client.torrents_info()
                        current_snapshot = {}

                        table = Table(title="Torrents with Non-Ignored Trackers")
                        table.add_column("Name", style="cyan", no_wrap=True)
                        table.add_column("Hash", style="dim", overflow="fold")
                        table.add_column("State", style="green")
                        table.add_column("DL Speed", justify="right")
                        table.add_column("Trackers", style="magenta", overflow="fold")

                        for t in all_torrents:
                            try:
                                current_trackers = client.torrents_trackers(t.hash)
                                filtered_trackers = [tr.url for tr in current_trackers if tr.url not in IGNORED_TRACKERS]

                                if filtered_trackers:
                                    key = t.hash
                                    snapshot_data = {
                                        "name": t.name,
                                        "state": t.state,
                                        "dlspeed": t.dlspeed,
                                        "trackers": tuple(sorted(filtered_trackers)),
                                    }

                                    current_snapshot[key] = snapshot_data

                                    if previous_snapshot.get(key) != snapshot_data:
                                        trackers_str = ", ".join(filtered_trackers)
                                        table.add_row(
                                            t.name,
                                            t.hash,
                                            t.state,
                                            f"{t.dlspeed / 1024:.1f} KB/s",
                                            trackers_str
                                        )

                                        if current_snapshot != previous_snapshot:
                                            print()
                                            print(table)

                            except Exception as e:
                                print(f"[red]Error retrieving trackers for {t.name}: {e}[/red]")

                        previous_snapshot = current_snapshot

                        torrents_to_clean = [t for t in all_torrents if t.state in ['downloading', 'forcedDL'] and t.dlspeed > MIN_DL_SPEED * 1024]

                        for torrent in torrents_to_clean:
                            try:
                                current_trackers = client.torrents_trackers(torrent.hash)

                                for tr in current_trackers:
                                    if tr.url in IGNORED_TRACKERS:
                                        continue

                                    try:
                                        print(f"[cyan]Tracker cleaning for: [bold]{torrent.name}[/bold] ({torrent.hash}), DL speed {torrent.dlspeed / 1024:.1f} KB/s[/cyan]")

                                        client.torrents_remove_trackers(
                                            torrent_hash=torrent.hash,
                                            urls=[tr.url]
                                        )
                                        print(f"[green]Tracker deleted for [bold]{torrent.name}[/bold] ({torrent.hash}): [bold]{tr.url}[/bold][/green]")
                                    except Exception as remove_err:
                                        print(f"[red]Error deleting tracker {tr.url} for {torrent.name}: {remove_err}[/red]")

                            except NotFound404Error:
                                print("[red]Torrent not found[/red]")
                            except Exception as err:
                                print(f"[red]Processing error: {err}[/red]")

                    except Exception as e:
                        print(f"[red]Overall error: {e}[/red]")

                    time.sleep(1)


if __name__ == "__main__":
    main()
