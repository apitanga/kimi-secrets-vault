#!/bin/bash
#
# Kimi Secrets Vault - Installation Script
#
# Usage: ./install.sh [--dev]
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
INSTALL_MODE="${1:-user}"  # user, dev, or system
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_DIR="${HOME}/.kimi-vault"
CONFIG_DIR="${HOME}/.config/kimi-vault"
BIN_DIR="${HOME}/.local/bin"

echo -e "${GREEN}🔐 Kimi Secrets Vault Installer${NC}"
echo "================================="
echo ""

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python $PYTHON_VERSION found, but Python $REQUIRED_VERSION+ required${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

# Check age installation
echo ""
echo -e "${BLUE}Checking age installation...${NC}"
if ! command -v age &> /dev/null; then
    echo -e "${YELLOW}⚠️  age is not installed${NC}"
    echo "age is required for encryption/decryption."
    echo ""
    echo "Install it:"
    echo "  macOS:    brew install age"
    echo "  Linux:    See https://age-encryption.org"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ age $(age --version 2>&1) found${NC}"
fi

# Install Python package
echo ""
echo -e "${BLUE}Installing Python package...${NC}"

cd "$SCRIPT_DIR"

if [ "$INSTALL_MODE" = "--dev" ] || [ "$INSTALL_MODE" = "dev" ]; then
    echo "Installing in development mode..."
    pip install -e ".[dev]" || pip3 install -e ".[dev]"
else
    echo "Installing for user..."
    pip install --user -e . || pip3 install --user -e .
fi

echo -e "${GREEN}✅ Package installed${NC}"

# Create directories
echo ""
echo -e "${BLUE}Setting up directories...${NC}"
mkdir -p "$VAULT_DIR"
mkdir -p "$CONFIG_DIR"
chmod 700 "$VAULT_DIR"
chmod 700 "$CONFIG_DIR"
echo -e "${GREEN}✅ Directories created${NC}"

# Set up CLI scripts
echo ""
echo -e "${BLUE}Setting up CLI scripts...${NC}"

# Determine where to put scripts
if [ -d "$BIN_DIR" ]; then
    TARGET_BIN="$BIN_DIR"
elif [[ ":$PATH:" == *":$HOME/bin:"* ]]; then
    TARGET_BIN="$HOME/bin"
    mkdir -p "$TARGET_BIN"
else
    TARGET_BIN="$HOME/.local/bin"
    mkdir -p "$TARGET_BIN"
fi

# Create symlinks or wrapper scripts
for script in kimi-vault-session kimi-vault-oauth; do
    if [ -f "$SCRIPT_DIR/bin/$script" ]; then
        # Make script executable
        chmod +x "$SCRIPT_DIR/bin/$script"
        
        # Create symlink or copy
        if [ -L "$TARGET_BIN/$script" ]; then
            rm "$TARGET_BIN/$script"
        fi
        
        # Use absolute path in wrapper script
        cat > "$TARGET_BIN/$script" << EOF
#!/bin/bash
# Wrapper for $script
export PYTHONPATH="$SCRIPT_DIR/src:\${PYTHONPATH:-}"
exec "$SCRIPT_DIR/bin/$script" "\$@"
EOF
        chmod +x "$TARGET_BIN/$script"
        echo "  ✅ $script -> $TARGET_BIN/$script"
    fi
done

# Also ensure python -m works
if [ -f "$SCRIPT_DIR/src/kimi_vault/cli.py" ]; then
    # Create wrapper for kimi-vault CLI
    cat > "$TARGET_BIN/kimi-vault" << EOF
#!/bin/bash
# Wrapper for kimi-vault CLI
export PYTHONPATH="$SCRIPT_DIR/src:\${PYTHONPATH:-}"
exec python3 -m kimi_vault.cli "\$@"
EOF
    chmod +x "$TARGET_BIN/kimi-vault"
    echo "  ✅ kimi-vault -> $TARGET_BIN/kimi-vault"
fi

echo -e "${GREEN}✅ CLI scripts installed${NC}"

# Check PATH
echo ""
if [[ ":$PATH:" != *":$TARGET_BIN:"* ]]; then
    echo -e "${YELLOW}⚠️  $TARGET_BIN is not in your PATH${NC}"
    echo "Add this to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
    echo ""
    echo "  export PATH=\"$TARGET_BIN:\$PATH\""
    echo ""
    
    # Offer to add it
    read -p "Add to PATH automatically? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        SHELL_RC=""
        if [ -f "$HOME/.zshrc" ] && [ -n "${ZSH_VERSION:-}" ]; then
            SHELL_RC="$HOME/.zshrc"
        elif [ -f "$HOME/.bashrc" ]; then
            SHELL_RC="$HOME/.bashrc"
        elif [ -f "$HOME/.bash_profile" ]; then
            SHELL_RC="$HOME/.bash_profile"
        fi
        
        if [ -n "$SHELL_RC" ]; then
            echo "" >> "$SHELL_RC"
            echo "# Added by kimi-secrets-vault installer" >> "$SHELL_RC"
            echo "export PATH=\"$TARGET_BIN:\$PATH\"" >> "$SHELL_RC"
            echo -e "${GREEN}✅ Added to $SHELL_RC${NC}"
            echo "Run 'source $SHELL_RC' or restart your shell to use it."
        fi
    fi
else
    echo -e "${GREEN}✅ $TARGET_BIN is already in PATH${NC}"
fi

# Generate key if it doesn't exist
echo ""
echo -e "${BLUE}Checking encryption keys...${NC}"
if [ -f "$VAULT_DIR/key.txt" ]; then
    echo -e "${GREEN}✅ Key already exists: $VAULT_DIR/key.txt${NC}"
else
    echo -e "${YELLOW}🔐 Generating new age key pair...${NC}"
    if command -v age-keygen &> /dev/null; then
        age-keygen -o "$VAULT_DIR/key.txt" 2>&1
        chmod 600 "$VAULT_DIR/key.txt"
        echo -e "${GREEN}✅ Key generated${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  IMPORTANT: Back up your private key!${NC}"
        echo "   Location: $VAULT_DIR/key.txt"
        echo "   Public key: $(cat "$VAULT_DIR/key.txt.pub" 2>/dev/null || echo 'N/A')"
        echo ""
        echo "   Store a copy in your password manager or encrypted USB."
        echo "   If you lose this key, you CANNOT decrypt your secrets."
    else
        echo -e "${YELLOW}⚠️  age-keygen not found. Run 'kimi-vault init' after installing age.${NC}"
    fi
fi

# Create example config
echo ""
echo -e "${BLUE}Setting up configuration...${NC}"
if [ -f "$CONFIG_DIR/config" ]; then
    echo -e "${GREEN}✅ Config already exists: $CONFIG_DIR/config${NC}"
else
    cat > "$CONFIG_DIR/config" << 'EOF'
# Kimi Secrets Vault Configuration
# Uncomment and modify as needed

# vault_dir = ~/.kimi-vault
# key_file = ~/.kimi-vault/key.txt
# secrets_file = ~/.kimi-vault/secrets.json.age

# Gmail OAuth credentials (optional - can also be in secrets.json)
# client_id = your-client-id.apps.googleusercontent.com
# client_secret = your-client-secret
EOF
    chmod 600 "$CONFIG_DIR/config"
    echo -e "${GREEN}✅ Created example config: $CONFIG_DIR/config${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo "Quick start:"
echo ""
echo "  1. Set up Gmail API (optional):"
echo "     See docs/GMAIL_SETUP.md for instructions"
echo ""
echo "  2. Add your secrets:"
echo "     cp config/secrets.template.json $VAULT_DIR/secrets.json"
echo "     # Edit secrets.json with your credentials"
echo "     age -r \$(cat $VAULT_DIR/key.txt.pub) -o $VAULT_DIR/secrets.json.age $VAULT_DIR/secrets.json"
echo "     shred -u $VAULT_DIR/secrets.json"
echo ""
echo "  3. Start a secure session:"
echo "     kimi-vault-session"
echo ""
echo "  4. Use the CLI:"
echo "     kimi-vault unread"
echo "     kimi-vault search \"from:boss\""
echo ""
echo "Documentation:"
echo "  - README.md - Overview and usage"
echo "  - docs/INSTALL.md - Detailed installation"
echo "  - docs/GMAIL_SETUP.md - Gmail API setup"
echo ""
