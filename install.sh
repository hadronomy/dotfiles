#!/bin/bash

set -euo pipefail

# Set the repository URL
REPO_URL="https://github.com/hadronomy/dotfiles" # Replace with your repo URL
INSTALL_PY_URL="${REPO_URL}/raw/main/install.py"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
  echo "uv is not installed. Installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  echo "uv installed successfully. Please restart your shell or source ~/.profile."
fi

# Download the install.py script
echo "Downloading install.py from ${INSTALL_PY_URL}..."
curl -sSfL "${INSTALL_PY_URL}" -o install.py

# Run the Python script using uv
echo "Running install.py with uv..."
uv run install.py "$@"

# Clean up the downloaded script
rm install.py
