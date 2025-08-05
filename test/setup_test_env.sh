#!/usr/bin/env bash

# Set strict mode
set -euo pipefail

echo "Setting up test environment for Nix and Home Manager tests"

# Create necessary directories for Nix
sudo mkdir -p /nix
sudo chown -R tester:tester /nix

# Make sure we have the latest packages
sudo apt-get update -y

# Create a basic SSH key for testing signing
if [ ! -f ~/.ssh/id_test_ed25519 ]; then
    mkdir -p ~/.ssh
    chmod 700 ~/.ssh
    ssh-keygen -t ed25519 -f ~/.ssh/id_test_ed25519 -N "" -C "test@example.com"
    chmod 600 ~/.ssh/id_test_ed25519
    echo "Created test SSH key"
fi

# Create basic Git config so tests don't prompt
git config --global user.name "Test User"
git config --global user.email "test@example.com"

echo "Test environment setup complete"
