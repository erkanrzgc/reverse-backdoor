# MITRE ATT&CK Technique Mapping

| ID | Tactic | Technique | Implementation |
|----|--------|-----------|----------------|
| T1566.001 | Initial Access | Spearphishing Attachment | `payload.hta`, `.vbs` generation |
| T1189 | Initial Access | Drive-by Compromise | `.sct` via regsvr32 UNC fetch |
| T1204.002 | Execution | User Execution: Malicious File | `.bat`, `.vbs` double-click bait |
| T1059.001 | Execution | Command and Scripting Interpreter: PowerShell | PS1 reverse shell, Base64-encoded payloads |
| T1059.006 | Execution | Command and Scripting Interpreter: Python | `client/client.py` agent |
| T1106 | Execution | Native API | `syscall_inject` via raw NT syscalls |
| T1055.001 | Defense Evasion | Process Injection: DLL Injection | `inject <pid> <b64_shellcode>` |
| T1055.004 | Defense Evasion | Process Injection: Asynchronous Procedure Call | `early_bird <exe> <shellcode>`, `syscall_inject` |
| T1055.012 | Defense Evasion | Process Hollowing | `hollow <target_exe> <shellcode>` |
| T1055.015 | Defense Evasion | ListPlanting | `migrate <pid>` |
| T1562.001 | Defense Evasion | Disable or Modify Tools | AMSI patch via `evasion`, ETW patch |
| T1562.002 | Defense Evasion | Disable or Modify System Firewall | `evasion` context checks |
| T1562.006 | Defense Evasion | Indicator Blocking | `unhook` — refresh ntdll .text from disk |
| T1027.001 | Defense Evasion | Obfuscated Files or Information: Binary Padding | `sleep_obfuscation` heap noise, XOR strings |
| T1027.006 | Defense Evasion | HTML Smuggling | `.hta` payload with embedded VBScript |
| T1036.005 | Defense Evasion | Masquerading: Match Legitimate Name | `svchost.exe` payload naming |
| T1134.001 | Defense Evasion | Access Token Manipulation: Token Impersonation | `steal_token <pid>`, `rev2self` |
| T1134.002 | Defense Evasion | Access Token Manipulation: Create Process with Token | `hollow` with PPID spoofing |
| T1070.001 | Defense Evasion | Indicator Removal: Clear Windows Event Logs | `clear_logs` |
| T1070.006 | Defense Evasion | Indicator Removal: Timestomp | `timestomp <path>` |
| T1612 | Defense Evasion | Build Image on Host | `hollow` — spawn suspended, overwrite in memory |
| T1071.001 | Command and Control | Web Protocols | `HttpBeaconProtocol` GET/POST polling |
| T1090.004 | Command and Control | Proxy: Domain Fronting | `front_host` in HTTP profile |
| T1573.001 | Command and Control | Encrypted Channel: Symmetric Cryptography | ECDH + AES-256-GCM via `EncryptedProtocol` |
| T1573.002 | Command and Control | Encrypted Channel: Asymmetric Cryptography | ECDH key exchange |
| T1003.001 | Credential Access | OS Credential Dumping: LSASS Memory | `lsass_dump` via comsvcs.dll MiniDump |
| T1003.002 | Credential Access | OS Credential Dumping: SAM | `sam_dump` — reg save SAM + SYSTEM |
| T1003.003 | Credential Access | OS Credential Dumping: NTDS | VSS shadow copy + ntdsutil |
| T1003.005 | Credential Access | OS Credential Dumping: Cached Domain Credentials | SECURITY hive dump |
| T1555.003 | Credential Access | Credentials from Web Browsers | `browser_creds`, `browser_dump` — Chrome/Edge Chromium decrypt |
| T1555.003 | Credential Access | Credentials from Web Browsers (Firefox) | `browser_dump` — profiles/sqlite extraction |
| T1040 | Credential Access | Network Sniffing | `wifi_dump` — netsh wlan profiles |
| T1082 | Discovery | System Information Discovery | `sysinfo` |
| T1033 | Discovery | System Owner/User Discovery | `whoami`, `check_admin` |
| T1057 | Discovery | Process Discovery | `ps` |
| T1016.001 | Discovery | System Network Configuration Discovery: Internet Connection | `ifconfig` |
| T1018 | Discovery | Remote System Discovery | `scan <subnet>` — ICMP sweep |
| T1069.001 | Discovery | Permission Groups Discovery: Local Groups | `priv_enable`, `check_admin` |
| T1049 | Discovery | System Network Connections Discovery | `ifconfig` |
| T1547.001 | Persistence | Boot or Logon Autostart: Registry Run Keys | `persistence install registry` |
| T1053.005 | Persistence | Scheduled Task/Job: Scheduled Task | `persistence install scheduled_task` |
| T1547.001 | Persistence | Boot or Logon Autostart: Startup Folder | `persistence install startup_folder` |
| T1546.003 | Persistence | Event Triggered Execution: WMI | `persistence install wmi` |
| T1543.002 | Persistence | Systemd Service | `persistence install systemd` |
| T1053.003 | Persistence | Cron | `persistence install crontab` |
| T1547.013 | Persistence | XDG Autostart Entries | `persistence install xdg` |
| T1546.004 | Persistence | Event Triggered Execution: .bash_profile/.bashrc | `persistence install bashrc` |
| T1021.002 | Lateral Movement | Remote Services: SMB/Windows Admin Shares | `psexec` |
| T1021.004 | Lateral Movement | Remote Services: SSH | `ssh_spread` |
| T1090 | Lateral Movement | Proxy | `socks5` relay |
| T1570 | Lateral Movement | Lateral Tool Transfer | SCP payload transfer in `ssh_spread` |
| T1068 | Privilege Escalation | Exploitation for Privilege Escalation | `privesc_linux`, `privesc_windows` |
| T1548.001 | Privilege Escalation | Abuse Elevation Control Mechanism: Setuid/Setgid | `privesc_linux` — SUID scan |
| T1113 | Collection | Screen Capture | `screenshot`, `stream_start`/`stream_stop` |
| T1125 | Collection | Video Capture | `webcam` |
| T1056.001 | Collection | Input Capture: Keylogging | `keylog_start`, `keylog_dump`, `keylog_stop` |
| T1115 | Collection | Clipboard Data | `clipboard` |
| T1025 | Collection | Data from Removable Media | `ls` / `cd` file system traversal |
| T1560.001 | Exfiltration | Exfiltration Over Alternative Protocol: Data Transfer Size Limits | `chunked_download` — 512KB chunks |
| T1041 | Exfiltration | Exfiltration Over C2 Channel | HTTP POST `/push`, encrypted TCP |
| T1530 | Exfiltration | Data from Cloud Storage | `browser_creds` browser-stored cloud credentials |
| T1074.001 | Collection | Data Staged: Local Data Staging | `loot/` directory, log files |
| T1485 | Impact | Data Destruction | `keylog_stop` + self-destruct, `self_delete` |
| T1490 | Impact | Inhibit System Recovery | `clear_logs` |
