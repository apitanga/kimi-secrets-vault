# 🔐 Nakimi

Secure, plugin-based API credential management for AI assistants.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-GitHub_Pages-blue)](https://apitanga.github.io/nakimi/)

## What is this?

A secure vault that stores your API credentials encrypted at rest, decrypts them just-in-time for AI assistant sessions, and automatically cleans up when done.

**Key feature**: Plugin-based architecture. Each service (Gmail, Calendar, GitHub, etc.) is a separate plugin that auto-loads when you add credentials.

**Optional YubiKey support**: Hardware-based encryption for age private keys requiring physical presence and PIN authentication.

## Who Is This For?

| ✅ This Tool Is For | ❌ This Tool Is NOT For |
|---------------------|-------------------------|
| **Individual developers** who want AI assistants to access their personal APIs | **Enterprise teams** needing audit logs, RBAC, and shared secrets |
| **Local-only usage** on your personal machine | **Multi-user/shared vaults** where secrets need to be distributed |
| **Convenience + reasonable security** - you accept "good enough" protection | **Maximum security environments** requiring HSMs, air-gapping, or zero-knowledge |
| **Personal projects** where you control the entire stack | **Production systems** with compliance requirements (SOC2, PCI-DSS, etc.) |
| **AI assistant integrations** (Claude, ChatGPT, local LLMs) | **Server deployments** or CI/CD pipelines |

**Bottom line**: This is a **personal developer tool**, not an enterprise secrets manager. If you need HashiCorp Vault, AWS Secrets Manager, or 1Password for Teams, use those instead.

## Use Cases

### Use Case 1: AI Assistant CLI Integration
**Scenario**: You want AI assistants (Kimi, Claude CLI, etc.) to check your Gmail or calendar without hardcoding credentials.

```bash
# AI assistant runs in secure session
nakimi session
$ nakimi gmail.search "meeting tomorrow"
$ nakimi calendar.today
```

**Threat assumptions**:
- Attacker has access to your user account (can read ~/.nakimi/)
- Attacker does NOT have root (can't dump locked memory)
- Physical machine is secure (laptop in your possession)
- Full Disk Encryption is enabled

**Future**: MCP server mode planned for direct Claude Desktop integration.

### Use Case 2: Local CLI Automation
**Scenario**: You have scripts that need API access but you don't want credentials in shell history or env vars.

```bash
# In your script
nakimi session --exec ./deploy.sh
# deploy.sh can use gmail.send, github.issues, etc.
```

**Threat assumptions**:
- Machine is single-user
- No malware/keyloggers present
- Scripts run interactively (not in shared CI/CD)
- Temporary files in RAM are acceptable risk

### Use Case 3: AI Coding Assistants
**Scenario**: You're using Cursor, Copilot, or Kimi CLI and want them to interact with your GitHub repos or cloud services.

```bash
# Ask AI: "Show me my unread GitHub notifications"
# AI runs: nakimi github.notifications
```

**Threat assumptions**:
- You trust the AI assistant tool itself
- API access is read-only or low-risk
- Compromised AI tool = compromised credentials
- Acceptable for personal projects, NOT for production infra

## Plugins Available

| Plugin | Status | Description |
|--------|--------|-------------|
| **gmail** | ✅ Ready | Read, search, and send emails |
| **calendar** | 🚧 Planned | Google Calendar integration |
| **github** | 🚧 Planned | GitHub API integration |

## Quick Start

### 1. Install age (REQUIRED - System Dependency)

**nakimi requires the `age` encryption tool.** Install it first:

```bash
# macOS
brew install age

# Ubuntu/Debian  
sudo apt install age

# Fedora
sudo dnf install age

# Or download from https://github.com/FiloSottile/age/releases
```

### 2. Install nakimi

**Option A: Install from GitHub (Recommended for users)**

```bash
# Latest version
pip install git+https://github.com/apitanga/nakimi.git

# Specific version
pip install git+https://github.com/apitanga/nakimi.git@v1.0.0
```

**Option B: Clone and install locally (for development)**

```bash
git clone https://github.com/apitanga/nakimi.git
cd nakimi
pip install .

# Or for development (editable install):
pip install -e .
```

**Option C: One-line install script**

```bash
curl -sSL https://raw.githubusercontent.com/apitanga/nakimi/main/install.sh | bash
```

### 2. Initialize Vault

```bash
# Generate encryption key pair
nakimi init

# Output:
# 🔐 Generating new age key pair...
# ✅ Key generated!
#    Private key: ~/.nakimi/key.txt
#    Public key: age1...
#
# ⚠️  IMPORTANT: Back up your private key!
```

### 3. Add API Credentials

**For Gmail:**

```bash
# 1. Copy template
cp config/secrets.template.json ~/.nakimi/secrets.json

# 2. Edit with your Gmail OAuth credentials
vim ~/.nakimi/secrets.json

# 3. Encrypt
age -r $(cat ~/.nakimi/key.txt.pub) \
  -o ~/.nakimi/secrets.json.age \
  ~/.nakimi/secrets.json

# 4. Securely delete plaintext
shred -u ~/.nakimi/secrets.json
```

See [docs/plugins/GMAIL_SETUP.md](docs/plugins/GMAIL_SETUP.md) for detailed Gmail OAuth instructions.

### 4. Use It

```bash
# Plugin commands work immediately
nakimi gmail.unread              # List unread emails
nakimi gmail.search "from:boss"  # Search emails
nakimi gmail.profile             # Show account info

# Start a secure session
nakimi session
# Inside session, same commands work:
# $ nakimi gmail.unread
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Layer                                │
│  nakimi <plugin>.<command> [args]                           │
│  Example: nakimi gmail.unread --limit=5                     │
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
- Private key stored in `~/.nakimi/key.txt`

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
nakimi init                              # Generate encryption keys
nakimi encrypt <file> [-o output]        # Encrypt a file
nakimi decrypt <file.age> [-o output]    # Decrypt a file
nakimi session                           # Start secure session
nakimi --version                         # Show version info
```

### Upgrading

```bash
# Check current version
nakimi --version

# Upgrade to latest version from GitHub
nakimi upgrade

# Upgrade to specific version
nakimi upgrade --version 1.1.0

# Or use pip directly
pip install --upgrade git+https://github.com/apitanga/nakimi.git
```

### Plugin Commands

#### Gmail Plugin

```bash
nakimi gmail.unread [limit]              # List unread emails
nakimi gmail.search <query> [limit]      # Search emails
nakimi gmail.labels                      # List labels
nakimi gmail.profile                     # Show account info
nakimi gmail.draft <to> <subject> <body> # Create draft
nakimi gmail.send <to> <subject> <body>  # Send email
```

**Examples:**

```bash
# List 5 unread emails
nakimi gmail.unread 5

# Search for emails from boss
nakimi gmail.search "from:boss@company.com"

# Search with date range
nakimi gmail.search "after:2026/01/01 before:2026/01/31"

# Send quick email
nakimi gmail.send "colleague@example.com" "Quick question" "Hey, can we chat?"
```

### Plugin Management

```bash
nakimi plugins list                      # List loaded plugins
nakimi plugins commands                  # List all available commands
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NAKIMI_DIR` | Vault directory | `~/.nakimi` |
| `NAKIMI_KEY` | Private key path | `~/.nakimi/key.txt` |
| `NAKIMI_SECRETS` | Encrypted secrets path | `~/.nakimi/secrets.json.age` |

### Config File

Create `~/.config/nakimi/config`:

```bash
vault_dir = ~/.nakimi
key_file = ~/.nakimi/key.txt
```

## Creating a Plugin

Want to add a new service? Here's the pattern:

### 1. Create Plugin Directory

```bash
mkdir src/nakimi/plugins/myservice
touch src/nakimi/plugins/myservice/__init__.py
```

### 2. Implement Plugin Class

```python
# src/nakimi/plugins/myservice/plugin.py
from nakimi.core.plugin import Plugin, PluginCommand, PluginError

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
nakimi myservice.list
```

## Python API

### Using Plugins Directly

```python
from nakimi.core import Vault, get_config
from nakimi.plugins.gmail import GmailClient

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
from nakimi.core import secure_delete
secure_delete(secrets_path)
```

### Creating Custom Plugins

```python
from nakimi.core.plugin import Plugin, PluginCommand

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
- **Hardware security**: Optional [YubiKey](https://www.yubico.com) PIV support via `age-plugin-yubikey` (requires physical key + PIN)
- **Key storage**: Private key never leaves your machine
- **At-rest**: All secrets encrypted
- **In-use**: Decrypted to temp files with strict permissions (0600)
- **Cleanup**: Securely shredded via `shred` (not just deleted)
- **Session isolation**: Each session gets unique temp file

**⚠️ Important:** Back up your `~/.nakimi/key.txt` offline. Lose this key = lose access to all secrets.

**⚠️ Security Note on SSDs:** 

This tool uses multiple layers of protection for temporary decrypted files:

1. **RAM-backed storage** (`/dev/shm` on Linux) - Preferred destination; secrets never touch physical disk when available
2. **Memory locking** (`mlock`) - Prevents RAM pages from being swapped to disk under memory pressure
3. **Strict permissions** (`chmod 600`) - Only owner can read
4. **Secure deletion** (`shred`) - Overwrites before removing; used when files land on physical storage

**Note:** `/dev/shm` is not guaranteed — it requires a tmpfs mount and write access. In environments where it's unavailable (e.g. some containers), decrypted files fall back to `/tmp` on physical disk. In that case, `chmod 600` + `shred` on cleanup are the active protections. `mlock` and `/dev/shm` are best-effort.

This means:
- ✅ Secrets prefer RAM-only storage, but fall back gracefully to disk
- ✅ Protected from swapping when `mlock` succeeds (best effort)
- ✅ Secure deletion on physical storage via `shred`
- ✅ Automatic cleanup on reboot (both `/dev/shm` and `/tmp`)

For systems without RAM disk support or maximum security, we still recommend **Full Disk Encryption** (FileVault on macOS, BitLocker on Windows, or LUKS on Linux).

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

See [Git Hooks Documentation](docs/development/GIT_HOOKS.md) for detailed documentation.

## Requirements

- Python 3.9+
- [age](https://age-encryption.org) encryption tool
- API credentials for services you want to use
- **Optional hardware security**: [YubiKey](https://www.yubico.com) PIV support via `age-plugin-yubikey` (requires separate installation)

### Optional Hardware Security

For enhanced security, Nakimi supports hardware-based encryption using YubiKey PIV slots via the [`age-plugin-yubikey`](https://github.com/str4d/age-plugin-yubikey) plugin. This requires:

- YubiKey 4/5 series with PIV support
- `age-plugin-yubikey` binary installed (see [YubiKey documentation](docs/security/yubikey.md))
- Configuration via environment variables or config file

See the [YubiKey Integration Guide](docs/security/yubikey.md) for detailed setup instructions.

## Installation & Upgrading

### Fresh Install

```bash
# Install from GitHub (recommended)
pip install git+https://github.com/apitanga/nakimi.git

# Or clone and install locally
git clone https://github.com/apitanga/nakimi.git
cd nakimi
pip install .
```

### Upgrading

```bash
# Built-in upgrade command
nakimi upgrade

# Upgrade to specific version
nakimi upgrade --version 1.1.0

# Or reinstall with pip
pip install --upgrade git+https://github.com/apitanga/nakimi.git
```

### Development Install

```bash
git clone https://github.com/apitanga/nakimi.git
cd nakimi
pip install -e .  # Editable install
```

See [docs/getting-started/INSTALL.md](docs/getting-started/INSTALL.md) for detailed instructions.

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
