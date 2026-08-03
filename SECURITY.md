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

- **Agent ↔ Server**: JSON messages are transmitted over raw TCP. No TLS is applied at this stage. Assume the underlying network is trusted or obfuscated via an external tunnel (VPN, SSH, Tor).
- Future versions will implement optional ECDH key exchange + AES-256-GCM encryption.

### Sensitive Data Handling

- `.env` files containing server addresses and ports are listed in `.gitignore` and must not be committed.
- Exfiltrated data (screenshots, keylogs, downloaded files) is stored in the `./loot` directory, which is also excluded from version control.
- Browser credential decryption uses Windows DPAPI (`CryptUnprotectData`) and AES-GCM — decryption keys are derived from the target machine's local state and are never transmitted.

### Agent Hardening Recommendations

For production red-team deployments:

- **PyInstaller packaging**: Compile the agent into a single executable to avoid Python dependency issues.
- **Network obfuscation**: Tunnel agent traffic through your preferred anonymization layer.
- **String obfuscation**: Consider obfuscating embedded strings to evade signature-based detection.
- **Avoid writing artifacts to disk**: Configure ephemeral storage for screenshots and keylogs where possible.

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
