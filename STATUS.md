# Module Status

| Module | Status | Notes |
|--------|--------|-------|
| **core/protocol.py** | `stable` | JSON wire protocol with framing, thread-safe |
| **core/encrypted_protocol.py** | `stable` | ECDH+AES-256-GCM wrapper |
| **core/connection.py** | `stable` | Reconnect loop, TLS support |
| **core/dispatcher.py** | `stable` | Command dispatch via registry |
| **core/beacon.py** | `beta` | Task queue + beacon config ready, not yet wired into dispatcher |
| **modules/file_ops.py** | `stable` | Full file system operations |
| **modules/shell.py** | `stable` | subprocess wrapper |
| **modules/shell_pty.py** | `beta` | PTY interactive shell |
| **modules/sysinfo.py** | `stable` | System info gathering |
| **modules/keylogger.py** | `stable` | pynput keylogger, window-aware |
| **modules/persistence.py** | `stable` | 8 persistence methods with install/remove/check |
| **modules/persist/** | `stable` | Linux: crontab, systemd, bashrc, xdg; Windows: registry, scheduled_task, startup_folder, wmi |
| **modules/surveillance/screenshot.py** | `stable` | pyautogui screenshot |
| **modules/surveillance/webcam.py** | `stable` | OpenCV webcam capture |
| **modules/surveillance/clipboard.py** | `stable` | PowerShell + pyperclip |
| **modules/surveillance/stream.py** | `beta` | screenshot streaming |
| **modules/credentials/wifi.py** | `stable` | Windows WiFi dump |
| **modules/credentials/browser.py** | `stable` | Chrome/Edge cred extraction |
| **modules/credentials/browser_v2.py** | `beta` | Firefox, Opera, Edge credential extraction |
| **modules/credentials/sam_dump.py** | `beta` | SAM/SYSTEM/SECURITY hive dump |
| **modules/stealth/evasion.py** | `stable` | AMSI/ETW bypass + AV/EDR detection |
| **modules/stealth/opsec.py** | `beta` | Log clearing, timestomp, self-delete |
| **modules/stealth/injection.py** | `beta` | CreateRemoteThread injection |
| **modules/stealth/tokens.py** | `beta` | Token steal/impersonate/privilege enable |
| **modules/stealth/hollowing.py** | `beta` | Process hollowing + PPID spoofing + migration |
| **modules/stealth/lsass.py** | `beta` | comsvcs.dll MiniDump LSASS dump |
| **modules/stealth/sleep_obfuscation.py** | `beta` | Heap noise, encrypted strings, debugger check |
| **modules/stealth/syscalls.py** | `beta` | syscall direct invocation, bypasses EDR hooks |
| **modules/stealth/unhook.py** | `beta` | ntdll.dll unhooking, hook detection |
| **modules/stealth/etw_patch.py** | `beta` | ETW event write patching |
| **modules/stealth/injection_v2.py** | `beta` | QueueUserAPC, Early Bird, SetThreadContext |
| **modules/pivot/socks5.py** | `beta` | RFC 1928 SOCKS5 relay over C2 tunnel protocol |
| **modules/lateral/movement.py** | `beta` | PSExec, WMI, SSH spread + network ping sweep |
| **modules/privesc/linux.py** | `beta` | sudo -l, SUID find, kernel version, writable services |
| **modules/privesc/windows.py** | `beta` | UAC check, service enumeration, unquoted paths, AlwaysInstallElevated |
| **modules/exfil/transfer.py** | `beta` | Chunked upload implemented; server-side reassembly pending |
| **modules/rat/control.py** | `beta` | Keystroke injection, mouse control, screen lock; requires pyautogui |
| **server/core/listener.py** | `stable` | Threaded accept loop with TLS |
| **server/core/session.py** | `stable` | Agent shell + master prompt + auto-recon + background tasking |
| **server/core/agent_registry.py** | `stable` | Thread-safe singleton |
| **server/core/audit.py** | `stable` | AuditLogger (JSONL), LootManager, CredentialStore (SQLite) |
| **server/core/background.py** | `stable` | BackgroundManager — async task queue + daemon threads |
| **server/payloads/generate.py** | `beta` | HTA, VBS, PS1, BAT, SCT payload generation |
| **server/ui/shell.py** | `stable` | Enhanced shell with tab completion + history |
| **server/ui/prompt.py** | `stable` | ANSI colors, table formatting |
| **server/ui/completer.py** | `stable` | Context-aware tab completion |
| **server/tui.py** | `stub` | Textual TUI — skeleton, needs full wiring |
| **common/protocol.py** | `stable` | Shared JSON wire protocol |
| **common/encrypted_protocol.py** | `stable` | ECDH + AES-256-GCM (deduplicated from client/server) |
| **common/http_protocol.py** | `stable` | HttpBeaconProtocol + HttpC2Server + domain fronting |
| **common/http_profile.py** | `stable` | 6 malleable HTTP profiles (default, chrome, cdn, api, office, stealth) |
| **common/udp_protocol.py** | `beta` | UDP transport with session tracking |
| **common/logging.py** | `stable` | Structured Logger: rotation, levels, file/console handlers |
| **c-implant/agent.c** | `beta` | v2 — 20 commands (keylogger, persistence, screenshot, b64 download/upload) |
| **c-implant/stager.c** | `stable` | 14KB C stager, HTTP download+execute |

### Status Legend
- `stable` — tested, production-ready
- `beta` — implemented, works, needs more field testing
- `alpha` — implemented, tested locally, may need edge-case work
- `stub` — skeleton/placeholder, not yet functional

### Command Count: 65
### Tests: 29 passing
### Module Import: 60+ modules importable
