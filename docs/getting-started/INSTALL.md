---
title: Installation Guide
nav_order: 11
parent: Getting Started
---

# Installation Guide

## Prerequisites

- Python 3.9 or higher
- `age` encryption tool
- (Optional) Google Cloud account for Gmail plugin
- (Optional) YubiKey hardware support requires `age-plugin-yubikey` binary and YubiKey 4/5 series (see [YubiKey Integration Guide](../security/yubikey.md))

## Step 1: Install age

### macOS
```bash
brew install age
```

### Linux

**Ubuntu/Debian:**
```bash
sudo apt install age
```

**Fedora:**
```bash
sudo dnf install age
```

**Other distros** - Download latest release:
```bash
# For example:
wget https://github.com/FiloSottile/age/releases/download/v1.1.1/age-v1.1.1-linux-amd64.tar.gz
tar -xzf age-v1.1.1-linux-amd64.tar.gz
sudo mv age/age /usr/local/bin/
sudo mv age/age-keygen /usr/local/bin/
```

### Windows
```bash
# Using Scoop
scoop install age

# Using Chocolatey
choco install age
```

### Verify installation
```bash
age --version
```

## Step 2: Install nakimi

### Option A: Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/apitanga/nakimi.git
cd nakimi

# Run the installer
./install.sh
```

This will:
- Install Python dependencies
- Set up the vault directory (`~/.nakimi`)
- Generate encryption keys
- Add CLI tools to your PATH

### Option B: Manual Install

```bash
# Clone the repository
git clone https://github.com/apitanga/nakimi.git
cd nakimi

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python package
pip install -e .
```

## Step 3: Initialize Vault

```bash
# Generate encryption key pair
nakimi init
```

This creates:
- `~/.nakimi/key.txt` - Private key (keep this safe!)
- `~/.nakimi/key.txt.pub` - Public key (can be shared)

**IMPORTANT**: Back up your private key to a secure location (password manager, encrypted USB). If you lose this key, you cannot decrypt your secrets.

## Step 4: Configure (Optional)

Create config file at `~/.config/nakimi/config`:

```bash
mkdir -p ~/.config/nakimi
cat > ~/.config/nakimi/config << 'EOF'
# Nakimi Configuration

# vault_dir = ~/.nakimi
# key_file = ~/.nakimi/key.txt
EOF
```

## Step 5: Add Your First Secret

1. Create or edit secrets template:

   ```bash
   # Copy template
   cp config/secrets.template.json ~/.nakimi/secrets.json

   # Edit with your credentials
   vim ~/.nakimi/secrets.json
   ```

2. Encrypt the secrets:

   ```bash
   age -r $(cat ~/.nakimi/key.txt.pub) \
     -o ~/.nakimi/secrets.json.age \
     ~/.nakimi/secrets.json

   # Securely delete plaintext
   shred -u ~/.nakimi/secrets.json
   ```

## Step 6: Set Up Plugins

Plugins are loaded automatically when you add their credentials to the vault.

### Available Plugins

| Plugin | Status | Description |
|--------|--------|-------------|
| **Gmail** | ✅ Ready | Read and send emails |
| **Calendar** | 🚧 Planned | Google Calendar integration |
| **GitHub** | 🚧 Planned | GitHub API access |

### Gmail Plugin
To enable the Gmail plugin, see [Gmail Setup Guide](../plugins/GMAIL_SETUP.md).

## Step 7: Test Your Installation

```bash
# Check CLI is available
nakimi --help

# Test vault initialization
nakimi init --check

# Check which plugins are available
nakimi plugins list

# List available commands
nakimi plugins commands

# Start a secure session
nakimi session

# Inside session, test commands
$ nakimi gmail.profile
$ nakimi gmail.unread 5
```

## Verification

Test your installation:

```bash
# Check CLI is available
nakimi --help

# Test vault initialization
nakimi init

# Check which plugins are available
nakimi plugins list

# List available commands
nakimi plugins commands
```

## Uninstallation

```bash
# Remove the package
cd nakimi
pip uninstall nakimi

# Remove vault (WARNING: This deletes your encrypted secrets!)
rm -rf ~/.nakimi

# Remove config
rm -rf ~/.config/nakimi

# Remove the repository
cd ..
rm -rf nakimi
```

## Troubleshooting

### "age: command not found"

Make sure `age` is installed and in your PATH. See Step 1.

### "Permission denied" when running scripts

```bash
chmod +x bin/nakimi bin/nakimi-session
```

### Python module not found

Make sure you've activated your virtual environment, or use the full path:
```bash
PYTHONPATH=src python -m nakimi.cli --help
```

### Can't decrypt vault

- Check that your private key exists: `ls ~/.nakimi/key.txt`
- Check that your encrypted secrets exist: `ls ~/.nakimi/secrets.json.age`
- Try decrypting manually: `age -d -i ~/.nakimi/key.txt ~/.nakimi/secrets.json.age`

### Plugin not loading

1. Check that credentials are in your secrets file:
   ```bash
   # Decrypt and view
   age -d -i ~/.nakimi/key.txt ~/.nakimi/secrets.json.age | python -m json.tool
   ```

2. Verify the plugin section name matches:
   ```json
   {
     "gmail": {  <-- Must match plugin name
       "client_id": "...",
       ...
     }
   }
   ```

3. Check plugin list:
   ```bash
   nakimi plugins list
   ```

### "No module named 'google'" (Gmail plugin)

Install Google API libraries:
```bash
pip install google-auth google-auth-oauthlib google-api-python-client
```

## Next Steps

- Read [Gmail Plugin Setup](../plugins/GMAIL_SETUP.md) to set up Gmail API access
- Add hardware security with [YubiKey Integration](../security/yubikey.md)
- Learn how to [create custom plugins](../development/PLUGIN_DEVELOPMENT.md)
- Review the [Architecture](../development/ARCHITECTURE.md) to understand the system design
- Check [Testing Guide](../development/TESTS.md) for development practices