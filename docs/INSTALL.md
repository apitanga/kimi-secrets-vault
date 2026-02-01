# Installation Guide

## Prerequisites

- Python 3.9 or higher
- `age` encryption tool
- (Optional) Google Cloud account for Gmail plugin

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

### Verify installation
```bash
age --version
```

## Step 2: Install kimi-secrets-vault

### Option A: Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/kimi-secrets-vault.git
cd kimi-secrets-vault

# Run the installer
./install.sh
```

This will:
- Install Python dependencies
- Set up the vault directory (`~/.kimi-vault`)
- Generate encryption keys
- Add CLI tools to your PATH

### Option B: Manual Install

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/kimi-secrets-vault.git
cd kimi-secrets-vault

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python package
pip install -e .
```

## Step 3: Initialize Vault

```bash
# Generate encryption key pair
kimi-vault init
```

This creates:
- `~/.kimi-vault/key.txt` - Private key (keep this safe!)
- `~/.kimi-vault/key.txt.pub` - Public key (can be shared)

**IMPORTANT**: Back up your private key to a secure location (password manager, encrypted USB). If you lose this key, you cannot decrypt your secrets.

## Step 4: Configure (Optional)

Create config file at `~/.config/kimi-vault/config`:

```bash
mkdir -p ~/.config/kimi-vault
cat > ~/.config/kimi-vault/config << 'EOF'
# Kimi Secrets Vault Configuration

# vault_dir = ~/.kimi-vault
# key_file = ~/.kimi-vault/key.txt
EOF
```

## Step 5: Set Up Plugins

Plugins are loaded automatically when you add their credentials to the vault.

### Gmail Plugin

To enable the Gmail plugin:

1. Set up Gmail API credentials (see [GMAIL_SETUP.md](GMAIL_SETUP.md))

2. Add credentials to your secrets:
   ```bash
   # Copy template
   cp config/secrets.template.json ~/.kimi-vault/secrets.json
   
   # Edit with your credentials
   vim ~/.kimi-vault/secrets.json
   ```

3. Encrypt the secrets:
   ```bash
   age -r $(cat ~/.kimi-vault/key.txt.pub) \
     -o ~/.kimi-vault/secrets.json.age \
     ~/.kimi-vault/secrets.json
   
   # Securely delete plaintext
   shred -u ~/.kimi-vault/secrets.json
   ```

4. Verify the plugin loads:
   ```bash
   kimi-vault plugins list
   # Output: gmail - Gmail integration - read, search, and send emails
   ```

5. Test it:
   ```bash
   kimi-vault gmail.profile
   ```

## Verification

Test your installation:

```bash
# Check CLI is available
kimi-vault --help

# Test vault initialization
kimi-vault init

# Check which plugins are available
kimi-vault plugins list

# List available commands
kimi-vault plugins commands
```

## Uninstallation

```bash
# Remove the package
cd kimi-secrets-vault
pip uninstall kimi-secrets-vault

# Remove vault (WARNING: This deletes your encrypted secrets!)
rm -rf ~/.kimi-vault

# Remove config
rm -rf ~/.config/kimi-vault

# Remove the repository
cd ..
rm -rf kimi-secrets-vault
```

## Troubleshooting

### "age: command not found"

Make sure `age` is installed and in your PATH. See Step 1.

### "Permission denied" when running scripts

```bash
chmod +x bin/kimi-vault bin/kimi-vault-session
```

### Python module not found

Make sure you've activated your virtual environment, or use the full path:
```bash
PYTHONPATH=src python -m kimi_vault.cli --help
```

### Can't decrypt vault

- Check that your private key exists: `ls ~/.kimi-vault/key.txt`
- Check that your encrypted secrets exist: `ls ~/.kimi-vault/secrets.json.age`
- Try decrypting manually: `age -d -i ~/.kimi-vault/key.txt ~/.kimi-vault/secrets.json.age`

### Plugin not loading

1. Check that credentials are in your secrets file:
   ```bash
   # Decrypt and view
   age -d -i ~/.kimi-vault/key.txt ~/.kimi-vault/secrets.json.age | python -m json.tool
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
   kimi-vault plugins list
   ```

### "No module named 'google'" (Gmail plugin)

Install Google API libraries:
```bash
pip install google-auth google-auth-oauthlib google-api-python-client
```

## Next Steps

- Read [GMAIL_SETUP.md](GMAIL_SETUP.md) to set up Gmail API access
- See the main [README.md](../README.md) for usage examples
- Learn how to [create custom plugins](../README.md#creating-a-plugin)
