#!/bin/bash
# wiz-central-toolkit System Dependencies Installer
# Auto-detects OS and installs missing CLI tools (especially jq)

set -e

echo "=========================================="
echo "wiz-central-toolkit Dependency Installer"
echo "=========================================="

# Check for jq
if command -v jq &> /dev/null; then
    echo "[✓] jq already installed ($(jq --version))"
else
    echo "[!] jq not found. Installing..."
    
    # Debian/Ubuntu
    if [ -f /etc/debian_version ]; then
        sudo apt-get update && sudo apt-get install -y jq
    
    # Arch Linux
    elif [ -f /etc/arch-release ]; then
        sudo pacman -S jq
    
    # macOS
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install jq
    
    # Termux (Android)
    elif [ -d /data/data/com.termux ]; then
        pkg install jq -y
    
    # Fallback
    else
        echo "[✗] ERROR: Unsupported OS. Please install jq manually:"
        echo "    Debian/Ubuntu: sudo apt-get install jq"
        echo "    Arch: sudo pacman -S jq"
        echo "    macOS: brew install jq"
        echo "    Termux: pkg install jq"
        exit 1
    fi
    
    echo "[✓] jq installed successfully"
fi

echo ""
echo "=========================================="
echo "Dependency installation complete."
echo "=========================================="

echo "Next steps:"
echo "  1. python3 -m venv fixy-env"
echo "  2. source fixy-env/bin/activate"
echo "  3. pip install -e ."

