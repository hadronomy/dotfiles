#!/usr/bin/env bash

# Set strict mode
set -euo pipefail

echo "============================================="
echo "Testing dotfiles customization functionality"
echo "============================================="

# Create a temporary directory to test the script
TEST_DIR=$(mktemp -d)
cd "${TEST_DIR}"

echo "Testing in directory: ${TEST_DIR}"

# Copy the install.py script to the test directory
cp /home/tester/dotfiles/install.py .

# Make the script executable
chmod +x ./install.py

# Install dependencies with pip
echo "Installing dependencies"
pip install typer rich pygithub requests psutil

# Test customization with the --customize flag
echo "Testing with --customize flag and full installation"
# Provide predetermined responses to prompts
echo -e "tester\nTest User\ntest@example.com\ny\n2\n~/.ssh/id_test_ed25519\nn\n" | python3 ./install.py --customize

# Check the exit status
EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "\n\033[32m✓ Test passed! Full customization worked successfully\033[0m"
else
    echo -e "\n\033[31m✗ Test failed! Customization test exited with code ${EXIT_CODE}\033[0m"
    exit 1
fi

# Verify dotfiles were cloned
if [ -d ~/.dotfiles ]; then
    echo -e "\033[32m✓ Dotfiles repo was cloned successfully\033[0m"
else
    echo -e "\033[31m✗ Test failed! Dotfiles repo was not cloned\033[0m"
    exit 1
fi

# Verify git configuration was updated
if grep -q "Test User" ~/.dotfiles/home/git/default.nix 2>/dev/null; then
    echo -e "\033[32m✓ Git configuration was updated successfully\033[0m"
fi

# Verify home-manager has applied the configuration
if command -v home-manager &> /dev/null && home-manager generations | grep -q "current"; then
    echo -e "\033[32m✓ Home Manager has applied the configuration\033[0m"
fi

# Clean up
cd /home/tester
rm -rf "${TEST_DIR}"
echo -e "\033[32m✓ Full customization test completed successfully\033[0m"
