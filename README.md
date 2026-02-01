# 🔐 Kimi Secrets Vault

Secure, plugin-based API credential management for AI assistants.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What is this?

A secure vault that stores your API credentials encrypted at rest, decrypts them just-in-time for AI assistant sessions, and automatically cleans up when done.

**Key feature**: Plugin-based architecture. Each service (Gmail, Calendar, GitHub, etc.) is a separate plugin that auto-loads when you add credentials.

## Plugins Available

| Plugin | Status | Description |
|--------|--------|-------------|
| **gmail** | ✅ Ready | Read, search, and send emails |
| **calendar** | 🚧 Planned | Google Calendar integration |
| **github** | 🚧 Planned | GitHub API integration |

## Quick Start

### 1. Install age (REQUIRED - System Dependency)

**kimi-secrets-vault requires the `age` encryption tool.** Install it first:

```bash
# macOS
brew install age

# Ubuntu/Debian  
sudo apt install age

# Fedora
sudo dnf install age

# Or download from https://github.com/FiloSottile/age/releases
```

### 2. Install kimi-secrets-vault

```bash
git clone https://github.com/YOUR_USERNAME/kimi-secrets-vault.git
cd kimi-secrets-vault
./install.sh
```

### 2. Initialize Vault

```bash
# Generate encryption key pair
kimi-vault init

# Output:
# 🔐 Generating new age key pair...
# ✅ Key generated!
#    Private key: ~/.kimi-vault/key.txt
#    Public key: age1...
#
# ⚠️  IMPORTANT: Back up your private key!
```

### 3. Add API Credentials

**For Gmail:**

```bash
# 1. Copy template
cp config/secrets.template.json ~/.kimi-vault/secrets.json

# 2. Edit with your Gmail OAuth credentials
vim ~/.kimi-vault/secrets.json

# 3. Encrypt
age -r $(cat ~/.kimi-vault/key.txt.pub) \
  -o ~/.kimi-vault/secrets.json.age \
  ~/.kimi-vault/secrets.json

# 4. Securely delete plaintext
shred -u ~/.kimi-vault/secrets.json
```

See [docs/GMAIL_SETUP.md](docs/GMAIL_SETUP.md) for detailed Gmail OAuth instructions.

### 4. Use It

```bash
# Plugin commands work immediately
kimi-vault gmail.unread              # List unread emails
kimi-vault gmail.search "from:boss"  # Search emails
kimi-vault gmail.profile             # Show account info

# Start a secure session
kimi-vault session
# Inside session, same commands work:
# $ kimi-vault gmail.unread
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Layer                                │
│  kimi-vault <plugin>.<command> [args]                           │
│  Example: kimi-vault gmail.unread --limit=5                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Plugin Manager                               │
│  • Auto-discovers plugins with credentials                       │
│  • Routes commands to correct plugin                             │
│  • Loads secrets on demand                                       │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │ gmail plugin │   │calendar plugin│  │ github plugin│
   │              │   │   (planned)   │   │  (planned)   │
   │ • unread     │   │ • today       │   │ • issues     │
   │ • search     │   │ • week        │   │ • prs        │
   │ • send       │   │ • add         │   │ • repos      │
   └──────────────┘   └──────────────┘   └──────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Vault Core                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Config     │  │    Vault     │  │ Session Management   │  │
│  │  (paths,     │  │  (age enc/   │  │ (env vars, cleanup)  │  │
│  │   env vars)  │  │   dec)       │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## How It Works

**At Rest:**
- Credentials encrypted with [age](https://age-encryption.org)
- Private key stored in `~/.kimi-vault/key.txt`

**In Session:**
- Vault decrypts to temp file on demand
- Plugins load credentials from temp file
- Temp file shredded on exit

**Plugin Discovery:**
- Plugins auto-load if credentials exist in `secrets.json`
- No credentials = plugin not loaded
- Add credentials → plugin appears

## CLI Reference

### Vault Management

```bash
kimi-vault init                              # Generate encryption keys
kimi-vault encrypt <file> [-o output]        # Encrypt a file
kimi-vault decrypt <file.age> [-o output]    # Decrypt a file
kimi-vault session                           # Start secure session
```

### Plugin Commands

#### Gmail Plugin

```bash
kimi-vault gmail.unread [limit]              # List unread emails
kimi-vault gmail.search <query> [limit]      # Search emails
kimi-vault gmail.labels                      # List labels
kimi-vault gmail.profile                     # Show account info
kimi-vault gmail.draft <to> <subject> <body> # Create draft
kimi-vault gmail.send <to> <subject> <body>  # Send email
```

**Examples:**

```bash
# List 5 unread emails
kimi-vault gmail.unread 5

# Search for emails from boss
kimi-vault gmail.search "from:boss@company.com"

# Search with date range
kimi-vault gmail.search "after:2026/01/01 before:2026/01/31"

# Send quick email
kimi-vault gmail.send "colleague@example.com" "Quick question" "Hey, can we chat?"
```

### Plugin Management

```bash
kimi-vault plugins list                      # List loaded plugins
kimi-vault plugins commands                  # List all available commands
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KIMI_VAULT_DIR` | Vault directory | `~/.kimi-vault` |
| `KIMI_VAULT_KEY` | Private key path | `~/.kimi-vault/key.txt` |
| `KIMI_VAULT_SECRETS` | Encrypted secrets path | `~/.kimi-vault/secrets.json.age` |

### Config File

Create `~/.config/kimi-vault/config`:

```bash
vault_dir = ~/.kimi-vault
key_file = ~/.kimi-vault/key.txt
```

## Creating a Plugin

Want to add a new service? Here's the pattern:

### 1. Create Plugin Directory

```bash
mkdir src/kimi_vault/plugins/myservice
touch src/kimi_vault/plugins/myservice/__init__.py
```

### 2. Implement Plugin Class

```python
# src/kimi_vault/plugins/myservice/plugin.py
from kimi_vault.core.plugin import Plugin, PluginCommand, PluginError

class MyServicePlugin(Plugin):
    @property
    def name(self) -> str:
        return "myservice"
    
    @property
    def description(self) -> str:
        return "MyService integration"
    
    def _validate_secrets(self):
        required = ['api_key']
        missing = [f for f in required if not self.secrets.get(f)]
        if missing:
            raise PluginError(f"Missing: {missing}")
    
    def get_commands(self) -> list[PluginCommand]:
        return [
            PluginCommand(
                name="list",
                description="List things",
                handler=self.cmd_list,
                args=[]
            ),
        ]
    
    def cmd_list(self) -> str:
        # Implement your logic
        return "Results here"
```

### 3. Add Credentials Template

Update `config/secrets.template.json`:

```json
{
  "myservice": {
    "api_key": "your-api-key"
  }
}
```

### 4. Use It

```bash
kimi-vault myservice.list
```

## Python API

### Using Plugins Directly

```python
from kimi_vault.core import Vault, get_config
from kimi_vault.plugins.gmail import GmailClient

# Load secrets
config = get_config()
vault = Vault()
secrets_path = vault.decrypt(config.secrets_file)

import json
with open(secrets_path) as f:
    secrets = json.load(f)

# Use plugin
client = GmailClient(secrets['gmail'])
for email in client.list_unread():
    print(f"{email['subject']} from {email['from']}")

# Clean up
from kimi_vault.core import secure_delete
secure_delete(secrets_path)
```

### Creating Custom Plugins

```python
from kimi_vault.core.plugin import Plugin, PluginCommand

class CustomPlugin(Plugin):
    @property
    def name(self):
        return "custom"
    
    def get_commands(self):
        return [PluginCommand("hello", "Say hello", self.hello, [])]
    
    def hello(self):
        return f"Hello, {self.secrets.get('name', 'world')}"
```

## Security

- **Encryption**: [age](https://age-encryption.org) - modern, auditable, simple
- **Key storage**: Private key never leaves your machine
- **At-rest**: All secrets encrypted
- **In-use**: Decrypted to temp files with strict permissions (0600)
- **Cleanup**: Securely shredded via `shred` (not just deleted)
- **Session isolation**: Each session gets unique temp file

**⚠️ Important:** Back up your `~/.kimi-vault/key.txt` offline. Lose this key = lose access to all secrets.

## Git Hooks for Test Protection

The project includes git hooks that automatically run tests before commits and pushes:

### Pre-push Hook
- Runs full test suite before `git push`
- Blocks push if any tests fail
- Ensures no broken code reaches remote repositories

### Pre-commit Hook  
- Runs quick tests on staged files before `git commit`
- Catches test failures early in development workflow

**To skip hooks temporarily**: Use `--no-verify` flag:
```bash
git commit --no-verify -m "Emergency fix"
git push --no-verify
```

See [GIT_HOOKS.md](GIT_HOOKS.md) for detailed documentation.

## Requirements

- Python 3.9+
- [age](https://age-encryption.org) encryption tool
- API credentials for services you want to use

## Installation

```bash
./install.sh           # User install
./install.sh --dev     # Development install with test deps
```

See [docs/INSTALL.md](docs/INSTALL.md) for detailed instructions.

## Roadmap

- [x] Plugin architecture
- [x] Gmail plugin
- [ ] Google Calendar plugin
- [ ] GitHub plugin
- [ ] Custom HTTP API plugin
- [ ] MCP server mode

## Contributing

Contributions welcome! The plugin architecture makes it easy to add new services.

## License

MIT License - See [LICENSE](LICENSE) file.
