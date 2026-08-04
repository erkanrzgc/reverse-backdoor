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
| **modules/sysinfo.py** | `stable` | System info gathering |
| **modules/keylogger.py** | `stable` | pynput keylogger, window-aware |
| **modules/persistence.py** | `stable` | 8 persistence methods with install/remove/check |
| **modules/surveillance/screenshot.py** | `stable` | pyautogui screenshot |
| **modules/surveillance/webcam.py** | `stable` | OpenCV webcam capture |
| **modules/surveillance/clipboard.py** | `stable` | PowerShell + pyperclip |
| **modules/credentials/wifi.py** | `stable` | Windows WiFi dump |
| **modules/credentials/browser.py** | `stable` | Chrome/Edge cred extraction |
| **modules/stealth/evasion.py** | `beta` | AMSI/ETW bypass + AV/EDR detection; tested on Win10/Win11 |
| **modules/stealth/opsec.py** | `beta` | Log clearing, timestomp, self-delete; tested on Win/Lin |
| **modules/stealth/injection.py** | `alpha` | CreateRemoteThread injection; tested locally, needs field validation |
| **modules/stealth/tokens.py** | `alpha` | Token steal/impersonate; tested locally, needs field validation |
| **modules/pivot/socks5.py** | `stub` | Skeleton — needs full RFC 1928 handshake + relay |
| **modules/lateral/movement.py** | `stub` | PSExec, WMI, SSH spread — return strings only |
| **modules/privesc/linux.py** | `beta` | sudo -l, SUID find, kernel version; read-only recon |
| **modules/privesc/windows.py** | `beta` | UAC check, service enumeration; read-only recon |
| **modules/exfil/transfer.py** | `beta` | Chunked upload implemented; server-side reassembly pending |
| **modules/rat/control.py** | `beta` | Keystroke injection, mouse control, screen lock; requires pyautogui |
| **server/core/listener.py** | `stable` | Threaded accept loop with TLS |
| **server/core/session.py** | `stable` | Agent shell + master prompt |
| **server/core/agent_registry.py** | `stable` | Thread-safe singleton |
| **server/ui/shell.py** | `stable` | Enhanced shell with tab completion + history |
| **server/ui/prompt.py** | `stable` | ANSI colors, table formatting |
| **server/ui/completer.py** | `stable` | Context-aware tab completion |
| **server/tui.py** | `stub` | Textual TUI — needs activation + wiring |

### Status Legend
- `stable` — tested, production-ready
- `beta` — implemented, works, needs more field testing
- `alpha` — implemented, tested locally, may need edge-case work
- `stub` — skeleton/placeholder, not yet functional
