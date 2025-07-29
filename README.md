# TrackersRemover-qBittorrent 🗑️

TrackersRemover-qBittorrent is a Python script that connects to qBittorrent's Web UI and removes trackers from torrents once their download speed exceeds a configurable threshold. This can help improve privacy or reduce reliance on certain trackers.

---

## Features

- Starts qBittorrent (Windows and macOS)
- Connects to qBittorrent Web UI via `qbittorrent-api`.
- Lists torrents and their trackers.
- Removes non-ignored trackers from torrents actively downloading above a minimum speed.
- Configurable ignored trackers list and minimum download speed threshold.

---

## Installation via PyPI

1. **Start qBittorrent and configure qBittorrent Web UI**

2. **Install Python >=3.8 if it is not done**

3. **Open CMD (Terminal) and install the python package directly using pip:**

    ```bash
    pip install trackersremoverqbt
    ```

4. **Then simply run it from the command line in CMD:**

    ```bash
    trackersremoverqbt
    # or
    trqbt
    ```

**Available options:**

```bash
# Exemple (works with trqbt instead of trackersremoverqbt)
trackersremoverqbt --host localhost --port 8080 --username admin --password 123456 --no-verify True --min-dl-speed 15 --launch-qbt True --ignored-trackers "tracker1.example.com" "tracker2.example.com"
# or
trackersremoverqbt -H localhost -P 8080 -U admin -PSW 123456 --no-verify True -MDL 15 -QBT True --ignored-trackers "tracker1.example.com" "tracker2.example.com"

# For version
trackersremoverqbt -V
# or
trackersremoverqbt --version

# For help
trackersremoverqbt --help
```

| Argument             | Alias(s) | Description                                               | Default Value                             |
|----------------------|----------|-----------------------------------------------------------|-------------------------------------------|
| `--host`             | `-H`     | qBittorrent Web UI address                                | `localhost`                               |
| `--port`             | `-P`     | Web UI port                                               | `8080`                                    |
| `--username`         | `-U`     | Web UI username                                           | `admin`                                   |
| `--password`         | `-PSW`   | Web UI password                                           | `123456`                                  |
| `--no-verify`        |          | Disable SSL certificate verification                      | `True` (verification disabled by default) |
| `--min-dl-speed`     | `-MDL`   | Minimum download speed in KB/s to trigger tracker removal | `10`                                      |
| `--ignored-trackers` |          | Additional list of trackers to ignore (added to defaults) | `[]` (empty by default)                   |
| `--launch-qbt`       | `-QBT`   | Launch qBittorrent if not running                         | `True`                                    |
| `--version`          | `-V`     | Show program version and exit                             |                                           |
| `--help`             |          | Show this help message and exit                           |                                           |
  
## Usage
The script runs in a loop, periodically checking torrents and removing trackers that meet the criteria. It outputs a 
formatted table of torrents with their trackers and logs removal actions.

![alt text](img/login.png)

![alt text](img/torrent.png)

![alt text](img/remove.png)

### Disclaimer

Removing trackers from torrents goes against the principles of traditional P2P sharing. By using this plugin, you acknowledge and agree:

- You understand the implications of modifying torrent behavior.
- You are solely responsible for any consequences that arise from using this plugin.
- The author(s) of TrackersRemover are not responsible for any misuse or unlawful use of this software.

## Notes

This tool is intended for advanced users aware of torrenting implications.

Tested on Python 3.12 and qBittorrent Web UI 5.x.