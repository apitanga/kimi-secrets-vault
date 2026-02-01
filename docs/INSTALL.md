# Installation Guide

## Prerequisites

- Python 3.9 or higher
- `age` encryption tool
- (Optional) Google Cloud account for Gmail API

## Step 1: Install age

### macOS
```bash
brew install age
```

### Linux (Ubuntu/Debian)
```bash
# Download latest release from https://github.com/FiloSottile/age/releases
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
- Set up the vault directory
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

# Or install without venv
pip install --user -e .
```

### Option C: pip install (when published)

```bash
pip install kimi-secrets-vault
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

# OAuth credentials (optional - can also be in secrets.json)
# client_id = your-client-id.apps.googleusercontent.com
# client_secret = your-client-secret
EOF
```

## Step 5: Set Up Gmail (Optional)

If you want to use Gmail features, follow [GMAIL_SETUP.md](GMAIL_SETUP.md).

## Verification

Test your installation:

```bash
# Check CLI is available
kimi-vault --help

# Test vault initialization (should show key info)
kimi-vault init

# Test session (will fail if no secrets, that's ok)
kimi-vault-session
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
chmod +x bin/kimi-vault-session bin/kimi-vault-oauth
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

## Next Steps

- Read [GMAIL_SETUP.md](GMAIL_SETUP.md) to set up Gmail API access
- See the main [README.md](../README.md) for usage examples
