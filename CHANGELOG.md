# Changelog

## [3.5.0] — 2026-08-06

### Added
- **Syscall direct invocation** (`stealth/syscalls.py`) — bypasses EDR userland hooks via direct syscalls
- **ntdll.dll unhooking** (`stealth/unhook.py`) — hook detection + fresh ntdll reload
- **ETW patching** (`stealth/etw_patch.py`) — EtwEventWrite patch to silence event tracing
- **Injection techniques v2** (`stealth/injection_v2.py`) — QueueUserAPC, Early Bird, SetThreadContext
- **Payload generation** (`server/payloads/generate.py`) — HTA, VBS, PS1, BAT, SCT stager output
- **UDP transport** (`common/udp_protocol.py`) — UDP C2 with session tracking
- **PTY shell** (`shell_pty.py`) — interactive PTY-based shell session
- **SAM hive dump** (`credentials/sam_dump.py`) — SAM/SYSTEM/SECURITY registry hive extraction
- **Browser credentials v2** (`credentials/browser_v2.py`) — Firefox, Opera, Edge credential extraction
- **Screenshot streaming** (`surveillance/stream.py`) — continuous screenshot stream to server
- **C implant v2** (`c-implant/agent.c`) — expanded to 20 commands (keylogger, persistence, screenshot, b64 download/upload)

### Changed
- Command count: **65** (8 new commands added)
- Test suite: **29 tests passing** (14 new tests added)
- All **60+ modules** verified importable
- Updated STATUS.md — all new modules listed, c-implant v2 reflected

## [3.4.0] — 2026-08-05

### Added
- **Structured logging system** (`common/logging.py`) — Logger singleton with per-agent log files
- Command-response correlation: duration, response size, status (ok/error) logged per command
- `logs` master command — summary table / per-agent history viewer
- `logs <agent-id> [n]` — view last N commands for an agent
- **Server-side chunked file download** — `ChunkedReceiver` with ordered reassembly + SHA256
- `download_large <path> [chunk_size_kb]` command for large file transfers
- **Privilege escalation commands** — `privesc_linux` (sudo/SUID/kernel/services), `privesc_windows` (UAC/services/unquoted paths/AlwaysInstallElevated)
- **RAT control commands** — `keystroke`, `mouse`, `click`, `lock_screen`
- **Full TUI implementation** (`server/tui.py`) — Textual-based panels, DataTable, RichLog, live agent refresh
- **Test suite** — 15 unit tests covering protocol, logging, registry, imports, HTTP profiles
- **Architecture docs** — `AGENTS.md` (dev conventions), `ARCHITECTURE.md` (directory map + flow)
- Logging wired into AgentShell — every command timed and logged

### Changed
- Updated STATUS.md — all modules re-evaluated, SOCKS5/LSASS/lateral now `beta`
- Total command count: **57** (51 Python + 6 server-only)
- Logging directory: `loot/logs/<agent_id>.log` (auto-created, rotating)

## [3.3.0] — 2026-08-05

### Added
- **SOCKS5 proxy** (`pivot/socks5.py`) — RFC 1928 handshake + relay via C2 protocol
- **LSASS dump** (`stealth/lsass.py`) — comsvcs.dll MiniDump technique
- **Lateral movement** (`lateral/movement.py`) — PSExec, WMI, SSH spread + ping sweep
- `lsass_dump`, `socks5`, `scan`, `psexec`, `ssh_spread` commands (5 added)
- **Structured logging** (`common/logging.py`) — levels, rotation, file/console handlers

## [2.2.0] — 2026-08-04

### Added
- Enhanced interactive shell (tab completion, command history, rich prompt)
- Dynamic prompt: `agent-1@10.0.0.5 Administrator in /var/www>`
- Tab completion for commands, file paths, agent IDs, persistence methods, process names
- Per-agent persistent history (`loot/.history/<agent_id>.history`)
- Command aliases (ll→ls, cls→clear, exit→quit, ?→help)
- `help <command>` per-command documentation
- Rich table output for `agents` command
- Auto color-coding of `[+]` `[-]` `[!]` `[*]` prefixes

## [2.1.0] — 2026-08-04

### Added
- AMSI + ETW bypass (VirtualProtect patch via ctypes)
- Context-aware evasion engine (AV/EDR detection, sandbox/VM detection)
- TLS transport (`--tls` flag, per-connection SSL wrapping)
- Beacon mode (sleep/jitter/kill_date/working hours + TaskQueue)
- OPSEC tools: log cleaning (Windows Event Log + Linux syslog), timestomp, self-delete
- Process injection (CreateRemoteThread shellcode injection)
- Token manipulation (steal, impersonate, revert, privilege enable)
- 10 new commands: evasion, detect_vm, inject, steal_token, rev2self, whoami, priv_enable, clear_logs, timestomp, self_delete
- LICENSE updated to match vibeprint style (MIT © erkanrzgc)

### Changed
- Agent auto-applies AMSI+ETW bypass on connect (configurable)
- Connection flow now supports TLS wrapping before key exchange
- Config env vars: `REVERSE_BACKDOOR_TLS`, `REVERSE_BACKDOOR_AUTO_BYPASS`

## [2.0.0] — 2026-08-03

### Added
- Complete architecture rewrite — Command Pattern, Protocol class, package splits
- Multi-agent support (threaded listener, AgentRegistry, interact/background/broadcast)
- Optional ECDH (X25519) + AES-256-GCM encryption
- CLI entry point (`cli.py` — click-based with server/client/generate commands)
- Textual TUI skeleton (`server/tui.py`)
- 8 persistence methods (Linux: crontab, systemd, bashrc, xdg; Windows: registry, scheduled_task, startup_folder, wmi)
- Module suite: pivot, privesc, lateral, exfil, persist, stealth, rat
- SECURITY.md with vulnerability reporting policy

### Changed
- Zero god files — dispatcher 145→25 lines, credentials/surveillance split into packages
- Protocol: instance-based (no global buffer), sock.sendall() fix
- Connection: UnboundLocalError fix, connect timeout, reconnect_interval passthrough
- Persistence: fixed copying interpreter bug, now copies actual script/executable
- grep/findstr: fixed stdin blocking
- Path traversal: sanitized download paths
- Deps: removed unused termcolor, added pycryptodome+pywin32+click
- Dockerfile: removed duplicate pip install
- wmic deprecated → ctypes GlobalMemoryStatusEx (Windows)
- Branding: all CYBERM4FIA references removed (28 occurrences)

### Removed
- ASCII art banner (per request)
- `client/modules/surveillance.py` → split into package
- `client/modules/credentials.py` → split into package

## [1.0.0] — 2024-12-19

### Added
- Initial release — modular C2 framework with reverse TCP + JSON protocol
- Cross-platform agent (Windows/Linux)
- File manager, shell execution, keylogger, screenshot, webcam, clipboard
- Browser credential extraction (Chrome/Edge), WiFi dump
- Persistence (registry Run key, crontab @reboot)
- Docker deployment
