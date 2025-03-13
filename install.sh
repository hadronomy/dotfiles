#!/bin/bash

set -euo pipefail

# Set the repository URL
REPO_URL="https://github.com/hadronomy/dotfiles" # Replace with your repo URL
INSTALL_PY_URL="${REPO_URL}/raw/main/install.py"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
  echo "uv is not installed. Installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Source uv to make it available in this session
  if [ -f "$HOME/.cargo/env" ]; then
    source "$HOME/.cargo/env"
  fi
  echo "uv installed successfully."
fi

# Check if uv is now in PATH
if ! command -v uv &> /dev/null; then
  echo "uv was installed but is not in PATH. Please add it to your PATH and try again."
  echo "You may need to restart your shell or source ~/.profile."
  exit 1
fi

# Download the install.py script
echo "Downloading install.py from ${INSTALL_PY_URL}..."
curl -sSfL "${INSTALL_PY_URL}" -o install.py

# Run the Python script using uv
echo "Running install.py with uv..."
uv run install.py "$@"

# Clean up the downloaded script
rm install.py
