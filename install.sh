#!/bin/bash

set -euo pipefail

# Set the repository URL
REPO_URL="https://github.com/hadronomy/dotfiles" # Replace with your repo URL
INSTALL_PY_URL="${REPO_URL}/raw/main/install.py"

# Set environment variable to indicate script is being run from installer
export FROM_DOTFILES_INSTALLER="true"

# Function to check for uv and get its path
get_uv_path() {
  if command -v uv &> /dev/null; then
    echo "uv"
    return 0
  elif [ -f "$HOME/.local/bin/uv" ]; then
    echo "$HOME/.local/bin/uv"
    return 0
  fi
  return 1
}

# Check if uv is installed
UV_PATH=""
if ! UV_PATH=$(get_uv_path); then
  echo "uv is not installed. Installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Source uv to make it available in this session
  if [ -f "$HOME/.cargo/env" ]; then
    source "$HOME/.cargo/env"
  fi
  echo "uv installed successfully."
  
  # Check again for uv
  if ! UV_PATH=$(get_uv_path); then
    echo "uv was installed but could not be found in PATH or ~/.local/bin."
    echo "You may need to restart your shell or source ~/.profile."
    exit 1
  fi
fi

# Download the install.py script
echo "Downloading install.py from ${INSTALL_PY_URL}..."
curl -sSfL "${INSTALL_PY_URL}" -o install.py

# Run the Python script using uv
echo "Running install.py with uv..."
"$UV_PATH" run install.py "$@"

# Clean up the downloaded script
rm install.py
