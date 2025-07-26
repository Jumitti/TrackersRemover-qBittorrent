# TrackersRemover-qBittorrent 🗑️

TrackersRemover-qBittorrent is a Python script that connects to qBittorrent's Web UI and removes trackers from torrents once their download speed exceeds a configurable threshold. This can help improve privacy or reduce reliance on certain trackers.

---

## Features

- Connects to qBittorrent Web UI via `qbittorrent-api`.
- Lists torrents and their trackers.
- Removes non-ignored trackers from torrents actively downloading above a minimum speed.
- Configurable ignored trackers list and minimum download speed threshold.

---

## Installation

### Install via PyPI

Install the package directly using pip:

```bash
pip install trackersremoverqbt
```

Then simply run it from the command line:

```bash
trackersremoverqbt
```
or
```bash
trqbt
```

Available options:

```bash
# Exemple
trackersremoverqbt --host localhost --port 8080 --username admin --password 123456 --verify-webui-certificate True --min-dl-speed 15 --ignored-trackers "tracker1.example.com" "tracker2.example.com"
```

```--host``` : qBittorrent Web UI address (default: localhost)

```--port``` : Web UI port (default: 8080)

```--username``` : Web UI username (default: admin)

```--password``` : Web UI password (default: 123456)

```--verify-webui-certificate``` : Verify SSL certificate (default: False)

```--min-dl-speed``` : Minimum download speed in KB/s to trigger tracker removal (default: 10)

```--ignored-trackers``` : Additional list of trackers to ignore (default includes DHT, PeX, LSD)

### Or manually

1. **Download the script**

   Clone this repository or download the `TRqBt.py` script directly.

2. **Set up Python environment**

   Make sure you have Python 3 installed (tested with Python 3.12).

   Install the required packages via pip:

   ```bash
   pip install qbittorrent-api rich
   ```
   
3. **Configure the script**

- Open the TRqBt.py file and update the qBittorrent connection settings to match your setup:

    ```python
    client = Client(
        host="localhost",   # qBittorrent Web UI address
        port=8080,          # Web UI port
        username="admin",   # Web UI username
        password="123456",  # Web UI password
        VERIFY_WEBUI_CERTIFICATE=False
    )
    ```

- Optionally adjust the minimum download speed (in KB/s) to trigger tracker removal:

    ```python
    MIN_DL_SPEED = 10  # Minimum download speed in KB/s
    ```

- You can also customize the list of trackers to ignore (default includes DHT, PeX, LSD):

    ```python
    IGNORED_TRACKERS = {"** [DHT] **", "** [PeX] **", "** [LSD] **"}
    ```

- Run the script

    Make sure qBittorrent is running and the Web UI is enabled.
    
    ```bash
    python TRqBt.py
    ```
  
## Usage
The script runs in a loop, periodically checking torrents and removing trackers that meet the criteria. It outputs a 
formatted table of torrents with their trackers and logs removal actions.

### Disclaimer

Removing trackers from torrents goes against the principles of traditional P2P sharing. By using this plugin, you acknowledge and agree:

- You understand the implications of modifying torrent behavior.
- You are solely responsible for any consequences that arise from using this plugin.
- The author(s) of TrackersRemover are not responsible for any misuse or unlawful use of this software.

## Notes

This tool is intended for advanced users aware of torrenting implications.

Tested on Python 3.12 and qBittorrent Web UI 5.x.