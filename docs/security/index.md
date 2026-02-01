---
title: Security Documentation
nav_order: 80
---

# Security Documentation

## Overview

This document covers security aspects of Kimi Secrets Vault, including threat model, encryption details, and security policies.

## Security Policy

For reporting security vulnerabilities, see the [Security Policy](SECURITY.md).

**Important**: Do not report security issues publicly. Email `security@pitanga.org` instead.

## Encryption Architecture

Kimi Secrets Vault uses [age](https://age-encryption.org) (Actually Good Encryption) for modern, auditable encryption.

### Key Features

- **Public-key cryptography**: Each vault has a key pair (private/public)
- **Encryption at rest**: All secrets are encrypted with age before storage
- **Just-in-time decryption**: Secrets are decrypted only during active sessions
- **RAM-backed storage**: Decrypted secrets stay in RAM (`/dev/shm`) and never touch disk
- **Memory locking**: Uses `mlock()` to prevent swapping to disk
- **Secure deletion**: Plaintext files are shredded with `shred` (not just deleted)

### Key Management

- Private key: `~/.kimi-vault/key.txt` (keep this safe!)
- Public key: `~/.kimi-vault/key.txt.pub` (can be shared for encryption)
- **Critical**: Back up your private key offline. Losing it means losing access to all encrypted secrets.

## Threat Model

### Assumptions

1. **User machine is not compromised** - No malware, keyloggers, or rootkits present
2. **Full Disk Encryption (FDE)** is enabled on the system
3. **Physical security** - Laptop is in your possession or secured
4. **Trusted plugins** - Plugins are from trusted sources and properly implemented
5. **Age implementation is secure** - We rely on the age encryption library

### Protection Provided

| Threat | Protection |
|--------|------------|
| Stolen laptop with FDE | Secrets remain encrypted at rest |
| Accidental file exposure | Secrets are encrypted (`.age` files) |
| Process memory inspection | Secrets only in RAM during sessions |
| Swap file exposure | `mlock()` prevents swapping |
| Temporary file residue | RAM-backed storage, secure deletion |
| Shoulder surfing | No protection (use screen privacy) |

### Limitations

- **Not for multi-user environments** - Designed for single-user personal use
- **No protection against compromised host** - If system is hacked, secrets can be exfiltrated
- **Manual key backup required** - No automated key recovery
- **Plugin security varies** - Each plugin's security depends on its implementation
- **No audit logging** - No record of secret access or usage

## Session Security

### How Sessions Work

1. User runs `kimi-vault session`
2. Vault decrypts secrets to a temporary file in `/dev/shm` (RAM disk)
3. Environment variables point plugins to the decrypted file
4. User executes commands within the session
5. On exit, the temporary file is securely shredded

### Session Isolation

- Each session gets a unique temporary file
- File permissions: `0600` (read/write only by owner)
- Automatic cleanup on session exit
- No persistence between sessions

## Plugin Security

### Plugin Trust Model

Plugins are Python modules that:
- Run with the same privileges as the vault process
- Have access to decrypted secrets for their specific service
- Can make network calls to external APIs

### Security Recommendations for Plugin Developers

1. **Validate all inputs** - Prevent injection attacks
2. **Use minimal required scopes** - Request only necessary permissions
3. **Implement proper error handling** - Don't leak sensitive information
4. **Follow least privilege** - Don't request unnecessary access
5. **Secure network communication** - Use HTTPS, validate certificates

### Plugin Auditing

Users should:
- Review plugin source code before use
- Understand what permissions each plugin requires
- Monitor plugin behavior (network calls, file access)
- Report suspicious plugins to security@pitanga.org

## Security Best Practices

### For Users

1. **Back up your private key** - Store it in a password manager or encrypted USB
2. **Use strong authentication** - Protect your Google/GitHub accounts with 2FA
3. **Regular updates** - Keep kimi-secrets-vault and plugins updated
4. **Monitor for anomalies** - Watch for unexpected behavior
5. **Minimize plugin use** - Only enable plugins you actually need
6. **Review permissions** - Understand what each plugin can access

### For Developers

1. **Never commit secrets** - Use `.gitignore` for `key.txt` and `secrets.json.age`
2. **Use the vault for testing** - Don't hardcode test credentials
3. **Write security tests** - Include tests for edge cases and potential vulnerabilities
4. **Follow secure coding guidelines** - Validate inputs, handle errors securely
5. **Review dependencies** - Keep dependencies updated and audit for vulnerabilities

## Incident Response

If you suspect a security incident:

1. **Immediate action**:
   - Terminate all active sessions
   - Revoke API tokens (Google, GitHub, etc.)
   - Change passwords for affected accounts

2. **Investigation**:
   - Check system logs for unauthorized access
   - Review recent vault usage
   - Scan for malware or keyloggers

3. **Recovery**:
   - Generate new age key pair (`kimi-vault init --force`)
   - Re-encrypt secrets with new key
   - Update API credentials with new tokens

## Security Updates

Security updates are released as patch versions (e.g., 1.0.0 → 1.0.1).

### Update Methods

- **Built-in**: `kimi-vault upgrade`
- **pip**: `pip install --upgrade kimi-secrets-vault`
- **Manual**: Clone latest version and reinstall

### Monitoring for Updates

- Watch GitHub releases
- Subscribe to security announcements
- Enable automatic updates where possible

## Compliance Considerations

Kimi Secrets Vault is **NOT** suitable for:

- **Regulated environments** (HIPAA, PCI-DSS, SOC2)
- **Enterprise use** (no RBAC, audit logging, or centralized management)
- **Multi-tenant systems** (no isolation between users)
- **High-security environments** (no HSM integration, air-gapping)

## Related Documentation

- [Architecture](../development/ARCHITECTURE.md) - System design and security model
- [Plugin Development](../development/PLUGIN_DEVELOPMENT.md) - Secure plugin creation
- [Testing Guide](../development/TESTS.md) - Security testing practices
- [Security Policy](SECURITY.md) - Vulnerability reporting

---

*Last updated: 2026-02-01*