---
title: Security Policy
nav_order: 81
---

# Security Policy

## Reporting Security Issues

**DO NOT** create a public issue for security vulnerabilities.

Security issues can be responsibly disclosed by emailing:
`security@pitanga.org`

### What to Include
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if known)
- Your contact information for follow-up

### Encryption
For sensitive reports, you can encrypt your message using our public key:
```
-----BEGIN AGE PUBLIC KEY-----
age1y8f8qk0h2qjq7q6q5q4q3q2q1q0q9q8q7q6q5q4q3q2q1q0q9q8q7q6q5q4q3q2q1q0q9q8
-----END AGE PUBLIC KEY-----
```

## Security Response Process

1. **Acknowledgment**: We will acknowledge receipt within 48 hours
2. **Investigation**: Our security team will investigate and validate the report
3. **Patch Development**: We will develop a fix and test it thoroughly
4. **Release**: We will release a patched version
5. **Disclosure**: We will coordinate public disclosure with the reporter

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| 0.x.x   | :white_check_mark: |

## Security Best Practices

### For Users
- Keep your `age` private key secure and backed up
- Use strong, unique passwords for encrypted files
- Regularly update to the latest version
- Review plugin permissions before installation
- Monitor audit logs for suspicious activity

### For Contributors
- Follow secure coding practices
- Never commit secrets or credentials
- Use the vault's encryption methods for any credential storage
- Validate all user input
- Write tests for security-critical code

## Security Architecture

### Encryption
- Uses `age` (Actually Good Encryption) for modern, auditable encryption
- Public-key cryptography for key management
- Secure memory handling with `mlock()` when available
- RAM-backed temporary files

### Threat Model
Kimi Secrets Vault assumes:
- The user's machine is not compromised
- The `age` implementation is secure
- Plugins are from trusted sources
- Users follow security best practices

### Limitations
- Not designed for multi-user environments
- Does not protect against compromised host systems
- Requires manual key backup
- Plugin security depends on plugin implementation

## Security Updates

Security updates are released as patch versions (e.g., 1.0.0 → 1.0.1). We recommend:
- Subscribing to security announcements
- Enabling automatic updates where possible
- Regularly checking for updates

## Security Audits

We welcome security audits from reputable security researchers. Please contact us before starting an audit to coordinate.

## Acknowledgements

We credit security researchers who responsibly disclose vulnerabilities in our security advisories.

## Contact

For security-related inquiries: `security@pitanga.org`

*Last updated: 2026-02-01*