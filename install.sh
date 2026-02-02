#!/bin/bash
# Install or upgrade nakimi from GitHub
# Usage: curl -sSL https://raw.githubusercontent.com/apitanga/nakimi/main/install.sh | bash

set -e

REPO_URL="https://github.com/apitanga/nakimi.git"
VERSION="${1:-main}"  # Default to main branch, or specify version

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       Nakimi Installer/Upgrader                ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "   Found Python $PYTHON_VERSION"

# Check pip
echo "Checking pip..."
if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
    echo "❌ pip is required but not installed"
    echo "   Install with: python3 -m ensurepip --upgrade"
    exit 1
fi
echo "   ✓ pip available"

# Check age (required dependency)
echo "Checking age (encryption tool)..."
if ! command -v age &> /dev/null; then
    echo "   ⚠️  age not found. You'll need to install it:"
    echo "       macOS: brew install age"
    echo "       Ubuntu/Debian: sudo apt install age"
    echo "       Other: https://age-encryption.org"
    echo ""
fi

# Check if already installed
echo ""
if command -v nakimi &> /dev/null; then
    CURRENT_VERSION=$(nakimi --version 2>&1 | head -1)
    echo "Current installation: $CURRENT_VERSION"
    echo ""
    
    if [ "$VERSION" = "main" ]; then
        echo "Upgrading to latest version from main branch..."
    else
        echo "Upgrading to version: $VERSION"
    fi
else
    echo "Fresh installation..."
fi

# Uninstall old version (if exists)
echo ""
echo "Step 1: Removing old installation (if any)..."
pip3 uninstall nakimi -y 2>/dev/null || true
echo "   ✓ Cleaned up"

# Install new version
echo ""
echo "Step 2: Installing from GitHub..."
if [ "$VERSION" = "main" ]; then
    echo "   Installing latest from main branch..."
    pip3 install "git+${REPO_URL}" --quiet
else
    echo "   Installing version ${VERSION}..."
    pip3 install "git+${REPO_URL}@${VERSION}" --quiet
fi
echo "   ✓ Installation complete"

# Verify installation
echo ""
echo "Step 3: Verifying installation..."
if command -v nakimi &> /dev/null; then
    echo ""
    nakimi --version
    echo ""
    echo "✅ nakimi is now installed!"
    echo ""
    echo "Next steps:"
    echo "   1. Initialize your vault:"
    echo "      nakimi init"
    echo ""
    echo "   2. Check available plugins:"
    echo "      nakimi plugins list"
    echo ""
    echo "   3. Start using it:"
    echo "      nakimi gmail.inbox"
    echo ""
    echo "For help: nakimi --help"
else
    echo "❌ Installation verification failed"
    echo "   Try running: pip3 install --user git+${REPO_URL}"
    exit 1
fi
