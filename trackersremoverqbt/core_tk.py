import threading
import time
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog

try:
    from . import core
except ImportError:
    import core
import multiprocessing
import subprocess
import sys
import os

from qbittorrentapi import Client


DEFAULT_IGNORED_TRACKERS = {"** [DHT] **", "** [PeX] **", "** [LSD] **"}
connection_lost = False


def start_mac_menu_subprocess(host, port, username, password):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    launcher_path = os.path.join(script_dir, "mmqbt.py")
    cmd = [sys.executable, launcher_path, host, str(port), username, password]
    p = subprocess.Popen(cmd)
    return p


class QBTApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Trackers Remover qBittorrent")
        self.geometry("700x720")

        frame_params = tk.Frame(self)
        frame_params.pack(padx=10, pady=5, fill="x")

        tk.Label(frame_params, text="Host:").grid(row=0, column=0, sticky="e")
        self.entry_host = tk.Entry(frame_params)
        self.entry_host.insert(0, "localhost")
        self.entry_host.grid(row=0, column=1)

        tk.Label(frame_params, text="Port:").grid(row=0, column=2, sticky="e")
        self.entry_port = tk.Entry(frame_params, width=6)
        self.entry_port.insert(0, "8080")
        self.entry_port.grid(row=0, column=3)

        tk.Label(frame_params, text="Username:").grid(row=1, column=0, sticky="e")
        self.entry_user = tk.Entry(frame_params)
        self.entry_user.insert(0, "admin")
        self.entry_user.grid(row=1, column=1)

        tk.Label(frame_params, text="Password:").grid(row=1, column=2, sticky="e")
        self.entry_password = tk.Entry(frame_params, show="*")
        self.entry_password.insert(0, "123456")
        self.entry_password.grid(row=1, column=3)

        tk.Label(frame_params, text="Min DL Speed (KB/s):").grid(row=2, column=0, sticky="e")
        self.entry_min_dl = tk.Entry(frame_params, width=10)
        self.entry_min_dl.insert(0, "10")
        self.entry_min_dl.grid(row=2, column=1, sticky="w")

        tk.Label(frame_params, text="Add ignored tracker:").grid(row=2, column=2, sticky="e")
        self.entry_ignored_tracker = tk.Entry(frame_params, width=30)
        self.entry_ignored_tracker.grid(row=2, column=3, sticky="w")

        self.btn_add_tracker = tk.Button(frame_params, text="Add", command=self.add_ignored_tracker)
        self.btn_add_tracker.grid(row=3, column=3, sticky="w", pady=(2, 2))

        self.btn_add_from_file = tk.Button(frame_params, text="Add from file...", command=self.add_ignored_from_file)
        self.btn_add_from_file.grid(row=3, column=3, sticky="w", pady=(2, 2), padx=(75, 75))

        tk.Label(frame_params, text="Ignored trackers:").grid(row=5, column=0, sticky="ne")
        self.list_ignored = tk.Listbox(frame_params, height=6, width=60, selectmode=tk.EXTENDED)
        self.list_ignored.grid(row=5, column=1, columnspan=3, sticky="w")

        btn_frame = tk.Frame(frame_params)
        btn_frame.grid(row=6, column=1, columnspan=3, sticky="w", pady=(5, 10))

        self.btn_remove_tracker = tk.Button(btn_frame, text="Remove selected", command=self.delete_selected_tracker)
        self.btn_remove_tracker.pack(side="left", padx=(0, 10))

        self.btn_reset_default = tk.Button(btn_frame, text="Reset default trackers", command=self.reset_default_trackers)
        self.btn_reset_default.pack(side="left")

        self.reset_default_trackers(initial=True)

        self.var_verify_ssl = tk.BooleanVar(value=True)
        self.chk_verify_ssl = tk.Checkbutton(frame_params, text="Verify WebUI Certificate",
                                             variable=self.var_verify_ssl)
        self.chk_verify_ssl.grid(row=3, column=1, sticky="w", pady=(5, 5))

        if sys.platform == "darwin":
            self.var_mac_menu = tk.BooleanVar(value=False)
            self.chk_mac_menu = tk.Checkbutton(frame_params, text="Enable macOS Menu Bar Icon",
                                               variable=self.var_mac_menu)
            self.chk_mac_menu.grid(row=7, column=1, sticky="w", pady=(5, 5), columnspan=2)

        frame_buttons = tk.Frame(self)
        frame_buttons.pack(padx=10, pady=10, fill="x")

        self.btn_start = tk.Button(frame_buttons, text="Start", command=self.start_thread)
        self.btn_start.pack(side="left")

        self.btn_stop = tk.Button(frame_buttons, text="Stop", command=self.stop, state="disabled")
        self.btn_stop.pack(side="left", padx=5)

        self.log_area = scrolledtext.ScrolledText(self, state="disabled", height=20)
        self.log_area.pack(padx=10, pady=5, fill="both", expand=True)

        self.log_area.tag_config('error', foreground='red')
        self.log_area.tag_config('success', foreground='green')
        self.log_area.tag_config('warning', foreground='orange')
        self.log_area.tag_config('info', foreground='blue')
        self.log_area.tag_config('debug', foreground='cyan')

        self._running = False
        self.client = None
        self.thread = None
        self.mac_menu_process = None

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        core.check_for_update()

    def add_ignored_tracker(self):
        tracker = self.entry_ignored_tracker.get().strip()
        if not tracker:
            messagebox.showwarning("Warning", "Tracker URL cannot be empty")
            return
        current = self.list_ignored.get(0, tk.END)
        if tracker in current:
            messagebox.showinfo("Info", "Tracker already in ignored list")
            return
        self.list_ignored.insert(tk.END, tracker)
        self.entry_ignored_tracker.delete(0, tk.END)
        self.log(f"Added ignored tracker: {tracker}", tag="success")

    def add_ignored_from_file(self):
        filepath = filedialog.askopenfilename(
            title="Select trackers file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not filepath:
            return
        added = 0
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            current = set(self.list_ignored.get(0, tk.END))
            for line in lines:
                tracker = line.strip()
                if tracker and tracker not in current:
                    self.list_ignored.insert(tk.END, tracker)
                    current.add(tracker)
                    added += 1
            self.log(f"Added {added} tracker(s) from file.", tag="success")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file:\n{e}")
            self.log(f"Error reading file: {e}", tag="error")

    def delete_selected_tracker(self):
        selected = self.list_ignored.curselection()
        if not selected:
            messagebox.showinfo("Info", "No tracker selected to remove")
            return
        for i in reversed(selected):
            self.list_ignored.delete(i)
        self.log("Removed selected ignored tracker(s)", tag="warning")

    def reset_default_trackers(self, initial=False):
        self.list_ignored.delete(0, tk.END)
        for tr in DEFAULT_IGNORED_TRACKERS:
            self.list_ignored.insert(tk.END, tr)
        if not initial:
            self.log("Reset ignored trackers to default list.", tag="info")

    def log(self, message, tag=None):
        self.log_area.config(state="normal")
        if tag:
            self.log_area.insert(tk.END, message + "\n", tag)
        else:
            self.log_area.insert(tk.END, message + "\n")
        self.log_area.yview(tk.END)
        self.log_area.config(state="disabled")

    def start_thread(self):
        if self._running:
            self.log("Already running.", tag="warning")
            return

        host = self.entry_host.get()
        try:
            port = int(self.entry_port.get())
        except ValueError:
            messagebox.showerror("Error", "Port must be an integer")
            return
        username = self.entry_user.get()
        password = self.entry_password.get()

        try:
            min_dl = int(self.entry_min_dl.get())
            if min_dl < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Min DL Speed must be a positive integer")
            return

        verify_ssl = self.var_verify_ssl.get()
        ignored_list = set(self.list_ignored.get(0, tk.END))

        self._running = True
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")

        self.thread = threading.Thread(
            target=self.run,
            args=(host, port, username, password, ignored_list, min_dl, verify_ssl),
            daemon=True
        )
        self.thread.start()

        if sys.platform == "darwin" and self.var_mac_menu.get():
            self.mac_menu_process = start_mac_menu_subprocess(
                host, port, username, password)

    def stop(self):
        self._running = False
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.log("Stopping...", tag="info")

        if sys.platform == "darwin" and self.mac_menu_process:
            self.mac_menu_process.terminate()
            self.mac_menu_process = None

    def on_closing(self):
        self.stop()
        self.destroy()

    def run(self, host, port, username, password, ignored_trackers, min_dl_speed, verify_ssl):
        global connection_lost

        core.launch_qbittorrent()
        time.sleep(3)

        self.log("Connecting to qBittorrent Web UI...", tag="info")

        self.client = Client(
            host=host,
            port=port,
            username=username,
            password=password,
            VERIFY_WEBUI_CERTIFICATE=verify_ssl,
        )

        while self._running:
            try:
                self.client.auth_log_in()
                self.log("[Connected]", tag="success")
                break
            except Exception as e:
                self.log(f"[Error] Connection failed: {e}", tag="error")
                time.sleep(3)

        while self._running:
            try:
                torrents = self.client.torrents_info()
                for t in torrents:
                    trackers = self.client.torrents_trackers(t.hash)
                    filtered = [tr.url for tr in trackers if tr.url not in ignored_trackers]

                    if filtered:
                        self.log(f"Torrent: {t.name} ({t.hash}) - DL: {t.dlspeed / 1024:.1f} KB/s", tag="info")
                        self.log(f"Trackers: {', '.join(filtered)}", tag="debug")

                        if t.state in ['downloading', 'forcedDL'] and t.dlspeed > min_dl_speed * 1024:
                            for tr in filtered:
                                try:
                                    self.client.torrents_remove_trackers(t.hash, [tr])
                                    self.log(f"Removed tracker {tr} from {t.name}", tag="success")
                                except Exception as err:
                                    self.log(f"Failed to remove tracker {tr}: {err}", tag="error")

                time.sleep(5)
            except Exception as err:
                self.log(f"[Error] {err}", tag="error")
                time.sleep(3)

        self.log("Stopped.", tag="info")


def main():
    multiprocessing.set_start_method('spawn')
    app = QBTApp()
    app.mainloop()


if __name__ == "__main__":
    main()
