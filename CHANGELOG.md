# Changelog

## [2.3.0] — Unreleased

### Added
- Shared protocol layer (`common/`) — deduplicated Protocol/EncryptedProtocol/ECDHEncryption
- Operator audit log (`loot/audit.jsonl`) — every command timestamped per agent
- Loot organization by agent ID and date
- Credential store (`loot/creds.db`) — structured SQLite storage for harvested credentials
- Module status markers — `STATUS.md` for production-readiness tracking
- CI pipeline — linting (ruff) + smoke test on push
- Pinned dependency versions with hashes

### Changed
- Client/server Protocol imports now delegate to `common/`
- Server session writes structured audit events
- `download`/`screenshot`/`webcam` output organized under `loot/<agent-id>/<date>/`

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
