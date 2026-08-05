# Architecture

```
reverse-backdoor/
├── common/                  # Shared protocol, encryption, logging
│   ├── protocol.py          # JSON + newline wire protocol
│   ├── encrypted_protocol.py# ECDH (X25519) + AES-256-GCM
│   ├── http_protocol.py     # HTTP beacon + C2 server
│   ├── http_profile.py      # 6 malleable HTTP profiles
│   └── logging.py           # Structured logger with rotation
├── client/                  # Agent (Python)
│   ├── client.py            # Entry point
│   ├── core/
│   │   ├── dispatcher.py    # Command dispatch loop
│   │   ├── connection.py    # Reconnect logic + TLS
│   │   ├── beacon.py        # Beacon task queue
│   │   └── session_context.py
│   ├── commands/            # Command implementations (50 total)
│   │   ├── base.py          # Command interface
│   │   ├── file_commands.py
│   │   ├── transfer_commands.py
│   │   ├── shell_commands.py
│   │   ├── system_commands.py
│   │   ├── surveillance_commands.py
│   │   ├── keylogger_commands.py
│   │   ├── credential_commands.py
│   │   ├── persistence_commands.py
│   │   ├── stealth_commands.py
│   │   ├── privesc_commands.py
│   │   └── rat_commands.py
│   └── modules/             # Feature modules
│       ├── file_ops.py
│       ├── shell.py
│       ├── sysinfo.py
│       ├── keylogger.py
│       ├── persistence.py
│       ├── persist/         # 8 persistence methods
│       ├── stealth/         # Evasion, OPSEC, injection, tokens
│       │   ├── evasion.py   # AMSI/ETW bypass
│       │   ├── opsec.py     # Log clearing, timestomp
│       │   ├── injection.py # CreateRemoteThread
│       │   ├── tokens.py    # Token steal/impersonate
│       │   ├── hollowing.py # Process hollowing + migration
│       │   ├── lsass.py     # LSASS dump (comsvcs.dll)
│       │   └── sleep_obfuscation.py
│       ├── surveillance/    # Screenshot, webcam, clipboard
│       ├── credentials/     # WiFi, browser creds
│       ├── privesc/         # Linux + Windows privesc
│       ├── pivot/socks5.py  # SOCKS5 relay over C2
│       ├── lateral/movement.py # PSExec, WMI, SSH spread
│       ├── exfil/transfer.py   # Chunked upload
│       └── rat/control.py   # Keystroke, mouse, lock
├── server/                  # C2 Server
│   ├── server.py            # Entry point
│   ├── cli.py               # Click-based CLI
│   ├── tui.py               # Textual TUI
│   ├── core/
│   │   ├── listener.py      # Threaded listener + TLS
│   │   ├── session.py       # Agent session handler
│   │   ├── agent_registry.py# Thread-safe agent list
│   │   ├── audit.py         # AuditLogger + CredentialStore
│   │   └── background.py    # Async task queuing
│   ├── commands/            # Server-side command handlers
│   │   ├── base.py          # ServerCommand interface
│   │   ├── system_commands.py
│   │   └── transfer_commands.py
│   ├── handlers/
│   │   ├── file_transfer.py # Base64 upload/download
│   │   └── chunked_receiver.py # Chunked file reassembly
│   └── ui/
│       ├── shell.py         # Interactive agent shell
│       ├── prompt.py        # ANSI colors, tables
│       └── completer.py     # Tab completion
├── c-implant/               # Native C agent + stager
│   ├── agent.c              # 330 lines, 12 commands
│   └── stager.c             # HTTP download + execute
├── tests/                   # Unit tests
└── AGENTS.md                # Dev conventions
```

## Flow

```
Target (agent/client)
  │ connect back via TCP/TLS/HTTP
  ▼
Listener (threaded accept loop)
  │ spawns session thread
  ▼
Session (AgentShell)
  │ commands via registry dispatch
  ▼
Client dispatcher
  │ receives command → executes module → returns result
  ▼
Session receives result → logs → displays to operator
```

## Protocol Wire Format

```
JSON + newline:  {"key": "value"}\n
Encrypted:       base64(nonce + ciphertext + tag)
HTTP Beacon:     GET /poll?aid=agent-1  |  POST /push?aid=agent-1
```

## Command Registration

```python
# New command
class MyCommand(Command):
    name = 'my_cmd'
    def execute(self, ctx, raw):
        ctx.protocol.send('result')
        return True  # keep session alive

# In client/commands/__init__.py:
registry.register(MyCommand())
```
