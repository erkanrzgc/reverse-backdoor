# AGENTS.md

## Project Conventions

### No God Files
- Files must stay under ~200 lines
- Split packages when growing (see `client/modules/credentials/`, `client/modules/surveillance/`, `client/modules/stealth/`)

### Command Pattern
- Every agent command is a class implementing `Command` with `.name` and `.execute(ctx, raw)`
- Register in `client/commands/__init__.py` → `build_client_registry()`
- Server commands use `ServerCommand` from `server/commands/base.py`

### Windows Guards
- All `ctypes`, `winreg`, `win32api` imports guarded: `if os.name != 'nt': return`
- File: `client/modules/stealth/*.py`, `client/modules/credentials/*.py`, `client/modules/privesc/windows.py`

### Protocol
- JSON + newline framing → `common/protocol.py`
- ECDH + AES-256-GCM → `common/encrypted_protocol.py`
- HTTP beacon → `common/http_protocol.py`
- Malleable profiles → `common/http_profile.py`

### Logging
- Structured logger → `common/logging.py` (singleton)
- Audit trail → `server/core/audit.py` (AuditLogger, LootManager, CredentialStore)
- Per-agent logs auto-created in `loot/logs/<agent_id>.log`

### Testing
- `tests/` directory with unittest
- Run: `python3 -m pytest tests/ -v` or `python3 -m unittest discover tests/`

### Linting
```bash
ruff check . --fix
```

### Env Vars
```
REVERSE_BACKDOOR_SERVER_IP
REVERSE_BACKDOOR_SERVER_PORT
REVERSE_BACKDOOR_TLS
REVERSE_BACKDOOR_AUTO_BYPASS
REVERSE_BACKDOOR_ENCRYPTION_KEY
```

### C Implant
```
gcc -o agent c-implant/agent.c -s -O2
gcc -o stager c-implant/stager.c -s -O2
```

### Commit Style
- `vX.Y.Z: short title`
- Bullet list of changes in body
