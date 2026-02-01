# 🔐 Kimi Secrets Vault

Secure, just-in-time access to API credentials with modern encryption.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🔐 **Modern Encryption** - Uses [age](https://age-encryption.org) for simple, secure encryption
- ⏱️ **Just-in-Time Decryption** - Secrets decrypted only when needed, cleaned up automatically
- 🔄 **Auto-Refresh Tokens** - Gmail OAuth tokens refresh automatically before expiry
- 🛡️ **Secure Cleanup** - Secrets are shredded (not just deleted) when done
- 🔧 **Configurable** - Environment variables or config file
- 🤖 **AI-Ready** - Designed for use with AI assistants like Kimi, Claude, etc.

## Quick Start

### 1. Install

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/kimi-secrets-vault.git
cd kimi-secrets-vault

# Run the installer
./install.sh

# Or install manually
pip install -e .
```

### 2. Initialize Vault

```bash
# Generate encryption key
kimi-vault init
```

### 3. Set Up Gmail (optional)

See [docs/GMAIL_SETUP.md](docs/GMAIL_SETUP.md) for detailed Gmail API setup.

Quick version:
1. Get OAuth credentials from [Google Cloud Console](https://console.cloud.google.com/)
2. Run `kimi-vault-oauth` to get a refresh token
3. Add credentials to `~/.kimi-vault/secrets.json`
4. Encrypt: `age -r $(cat ~/.kimi-vault/key.txt.pub) -o secrets.json.age secrets.json`
5. Secure delete: `shred -u secrets.json`

### 4. Use It

```bash
# Start a secure session
kimi-vault-session

# Inside the session, use the CLI
kimi-vault unread
kimi-vault search "from:boss"

# Or use Python
python3 -c "
from kimi_vault import GmailClient
client = GmailClient()
for email in client.list_unread():
    print(f'{email['subject']} from {email['from']}')
"
```

## How It Works

```
┌─────────────────┐
│  secrets.json   │  ← Your plaintext secrets (temporary)
│   (in /tmp/)    │
└────────┬────────┘
         │ Decrypt on session start
         ▼
┌─────────────────┐
│ secrets.json.age│  ← Encrypted at rest
│  (in ~/.kimi-vault/)
└────────┬────────┘
         │ Age encryption
         ▼
┌─────────────────┐
│    key.txt      │  ← Your private key (guard this!)
│  (in ~/.kimi-vault/)
└─────────────────┘
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KIMI_VAULT_DIR` | Vault directory | `~/.kimi-vault` |
| `KIMI_VAULT_KEY` | Private key path | `~/.kimi-vault/key.txt` |
| `KIMI_VAULT_SECRETS` | Encrypted secrets path | `~/.kimi-vault/secrets.json.age` |
| `KIMI_VAULT_CLIENT_ID` | OAuth client ID | (from config) |
| `KIMI_VAULT_CLIENT_SECRET` | OAuth client secret | (from config) |

### Config File

Create `~/.config/kimi-vault/config`:

```bash
# Example config
client_id = your-client-id.apps.googleusercontent.com
client_secret = your-client-secret
vault_dir = ~/.kimi-vault
```

## CLI Reference

```bash
# Initialize vault (generate key)
kimi-vault init

# List unread emails
kimi-vault unread

# Search emails
kimi-vault search "from:boss@example.com"

# List labels
kimi-vault labels

# Show profile
kimi-vault profile

# Create draft
kimi-vault draft to@example.com "Subject" "Body text"

# Send email
kimi-vault send to@example.com "Subject" "Body text"

# Get OAuth tokens
kimi-vault-oauth
```

## Python API

```python
from kimi_vault import GmailClient, VaultCrypto, VaultConfig

# Use default config
config = VaultConfig()
print(f"Vault dir: {config.vault_dir}")

# Encrypt/decrypt files
crypto = VaultCrypto()
crypto.encrypt("secrets.json")
decrypted_path = crypto.decrypt("secrets.json.age")

# Use Gmail client
client = GmailClient()  # Auto-detects secrets from env
emails = client.list_unread(max_results=5)
for email in emails:
    print(f"{email['subject']} from {email['from']}")

# Create draft
client.create_draft(
    to="recipient@example.com",
    subject="Hello",
    body="Message body"
)

# Send email
client.send_email(
    to="recipient@example.com",
    subject="Hello",
    body="Message body"
)
```

## Security Considerations

- **Backup your key**: `~/.kimi-vault/key.txt` is the ONLY way to decrypt your secrets. Back it up offline (password manager, encrypted USB).
- **Don't commit secrets**: The `.gitignore` is set up to prevent accidental commits, but always double-check.
- **Testing mode**: Gmail OAuth refresh tokens expire after 7 days in testing mode. For personal use, just re-authorize. For production apps, you'd need to go through Google's verification process.
- **Scope limitations**: The default Gmail scope is `readonly` + `compose`. You can read emails and create drafts/send emails, but cannot delete or modify existing emails.

## Requirements

- Python 3.9+
- [age](https://age-encryption.org) encryption tool
- Google API credentials (for Gmail features)

## License

MIT License - See [LICENSE](LICENSE) file.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Acknowledgments

- [age](https://age-encryption.org) by Filippo Valsorda for modern encryption
- Google API Client Libraries
