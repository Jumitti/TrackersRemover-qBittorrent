import time
from rich import print
from rich.table import Table
from qbittorrentapi import Client, NotFound404Error

# --- Connecting to web qBittorrent ---
client = Client(
    host="localhost",   # to adapt
    port=8080,          # to adapt
    username="admin",   # to adapt
    password="123456",  # to adapt
    VERIFY_WEBUI_CERTIFICATE=False
)

try:
    client.auth_log_in()
    print("[green]Connected to web qBittorrent[/green]")
except Exception as e:
    print(f"[red]Connection to web qBittorrent failed : {e}[/red]")
    exit(1)

IGNORED_TRACKERS = {"** [DHT] **", "** [PeX] **", "** [LSD] **"}
MIN_DL_SPEED = 10  # KB/S

previous_snapshot = {}

while True:
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

        # Cleaning trackers for actively downloading torrents
        torrents_to_clean = [t for t in all_torrents if t.state == 'downloading' and t.dlspeed > MIN_DL_SPEED * 1024]

        for torrent in torrents_to_clean:
            try:
                current_trackers = client.torrents_trackers(torrent.hash)

                for tr in current_trackers:
                    if tr.url in IGNORED_TRACKERS:
                        continue

                    try:
                        print(
                            f"[cyan]Tracker cleaning for: [bold]{torrent.name}[/bold] ({torrent.hash}), DL speed {torrent.dlspeed / 1024:.1f} KB/s[/cyan]")

                        client.torrents_remove_trackers(
                            torrent_hash=torrent.hash,
                            urls=[tr.url]
                        )
                        print(f"[green]Tracker deleted for [bold]{torrent.name}[/bold] ({torrent.hash}): [bold]{tr.url}[/bold][/green]")
                    except Exception as remove_err:
                        print(f"[red]Deletion tracker [bold]{tr.url}[/bold] error for [bold]{torrent.name}[/bold] ({torrent.hash}): {remove_err}[/red]")

            except NotFound404Error:
                print("[red]Torrent not found[/red]")
            except Exception as err:
                print(f"[red]Processing error: {err}[/red]")

    except Exception as e:
        print(f"[red]Overall error: {e}[/red]")

    time.sleep(1)
