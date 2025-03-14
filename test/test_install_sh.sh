#!/usr/bin/env bash

# Set strict mode
# set -euo pipefail

# echo "============================================="
# echo "Testing install.sh script with full installation"
# echo "============================================="

# # Create a temporary directory to test the script
# TEST_DIR=$(mktemp -d)
# cd "${TEST_DIR}"

# echo "Testing in directory: ${TEST_DIR}"

# # Copy the install.sh script to the test directory
# cp /home/tester/dotfiles/install.sh .

# # Make the script executable
# chmod +x ./install.sh

# # Run the install.sh with full installation
# echo "Running full installation - this will install nix and home-manager"
# ./install.sh

# # Check the exit status
# EXIT_CODE=$?
# if [ $EXIT_CODE -eq 0 ]; then
#     echo -e "\n\033[32m✓ Test passed! install.sh executed successfully\033[0m"
# else
#     echo -e "\n\033[31m✗ Test failed! install.sh exited with code ${EXIT_CODE}\033[0m"
#     exit 1
# fi

# # Verify nix is installed
# if command -v nix &> /dev/null; then
#     echo -e "\033[32m✓ Nix was successfully installed\033[0m"
# else
#     echo -e "\033[31m✗ Test failed! Nix was not installed\033[0m"
#     exit 1
# fi

# # Verify home-manager is installed
# if command -v home-manager &> /dev/null; then
#     echo -e "\033[32m✓ Home Manager was successfully installed\033[0m"
# else
#     echo -e "\033[31m✗ Test failed! Home Manager was not installed\033[0m"
#     exit 1
# fi

# # Clean up
# cd /home/tester
# rm -rf "${TEST_DIR}"
# echo -e "\033[32m✓ Full installation test completed successfully\033[0m"
