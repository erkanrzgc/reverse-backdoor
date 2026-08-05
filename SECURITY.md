# Security Policy

## Supported Versions

Only the latest commit on the `main` branch is supported with security updates.

| Version | Supported |
| ------- | :-------: |
| main    | ✅ |
| < main  | ❌ |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**Do not open a public GitHub issue.** Instead:

1. Navigate to the [Security tab](https://github.com/erkanrzgc/reverse-backdoor/security) on the repository
2. Click **"Report a vulnerability"**
3. Fill in the advisory form with a detailed description

Alternatively, contact the maintainer via the GitHub profile linked on the repository.

### What to Include

- Description of the vulnerability and its impact
- Steps to reproduce (proof-of-concept code if applicable)
- Affected component(s) and version(s)
- Any potential mitigations you have identified

### Disclosure Timeline

- Initial report → acknowledgment within **72 hours**
- Investigation and patch development → typically within **7–14 days**
- Coordinated public disclosure after a fix is released

## Security Model

### C2 Communication

- **Agent ↔ Server**: Supports raw TCP, TLS-wrapped TCP, and optional ECDH (X25519) + AES-256-GCM application-layer encryption. Use `--tls --encryption` for defense-in-depth.
- Unencrypted TCP is available for lab/testing only. Production deployments should always enable at minimum one encryption layer.

### Sensitive Data Handling

- `.env` files containing server addresses and ports are listed in `.gitignore` and must not be committed.
- Exfiltrated data is organized under `loot/<hostname>_<ip>/<date>/` per agent.
- Browser credential decryption uses Windows DPAPI (`CryptUnprotectData`) and AES-GCM — decryption keys are derived from the target machine's local state and are never transmitted.
- Operator audit log: all commands are timestamped to `loot/audit.jsonl`.

### Known Detection Risks

- **pywin32**: The `pywin32` package (providing `win32crypt` for browser credential decryption, `win32com` for COM operations) is flagged by many antimalware products. Browser credential harvesting should only be attempted when operational security permits — consider extracting credentials via alternative methods (LSASS dump, token manipulation) on defended targets.
- **Python payload size**: PyInstaller-compiled Python agents are ~7-10 MB. For smaller payloads with lower detection surface, use the planned C-language implant.
- **AMSI/ETW bypass**: The built-in AMSI/ETW bypass patches in-memory functions via `VirtualProtect`. This is effective against default Windows Defender but may be detected by advanced EDRs employing kernel callbacks. Consider combining with unhooking or indirect syscalls for defended targets.

### Agent Hardening Recommendations

For production red-team deployments:

- **PyInstaller packaging**: Compile the agent into a single executable to avoid Python dependency issues.
- **Network obfuscation**: Tunnel agent traffic through your preferred anonymization layer, or use the built-in TLS option.
- **String obfuscation**: Consider obfuscating embedded strings to evade signature-based detection.
- **Avoid writing artifacts to disk**: Configure ephemeral storage for screenshots and keylogs where possible.
- **Avoid pywin32 on defended targets**: Use token manipulation + LSASS dump instead of `win32crypt` for credential extraction on EDR-protected machines.

## Scope

This security policy covers:

- The C2 server and agent code in this repository
- Default configurations provided in `.env.example` files

Out of scope:

- Issues in third-party dependencies (report those upstream)
- Misconfigurations in custom deployments
- Social engineering or physical attacks
- Denial-of-service against the C2 server

## Acknowledgments

Researchers who report valid vulnerabilities will be credited here (with permission) after the issue is resolved and publicly disclosed.
