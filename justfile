# Dotfiles test commands

# Set default recipe to list commands
default:
    @just --list

# Build the Docker image
build-test-image:
    @echo "Building Docker image 'dotfiles-test'..."
    docker build -t dotfiles-test .

# Run a shell in the container for manual testing
test-shell: build-test-image
    @echo "Starting shell in test container..."
    docker run -it --rm dotfiles-test

# Test the install.sh script (full installation)
test-install-sh: build-test-image
    @echo "Running install.sh test..."
    docker run -it --rm --privileged dotfiles-test bash -c "./test/setup_test_env.sh && ./test/test_install_sh.sh"

# Test the install.py script directly (full installation)
test-install-py: build-test-image
    @echo "Running install.py test..."
    docker run -it --rm --privileged dotfiles-test bash -c "./test/setup_test_env.sh && ./test/test_install_py.sh"

# Test full installation flow with different usernames
test-custom: build-test-image
    @echo "Running customization test..."
    docker run -it --rm --privileged dotfiles-test bash -c "./test/setup_test_env.sh && ./test/test_customization.sh"

# Run all tests sequentially
test-all: build-test-image
    @echo "Running all tests in sequence..."
    @just test-install-sh
    @just test-install-py
    @just test-custom
    @echo "All tests completed successfully!"

# Run a specific test with privileged mode and volume mounting for Nix
test-single TEST_FILE="": build-test-image
    @if [ -z "{{TEST_FILE}}" ]; then \
        echo "Usage: just test-single TEST_FILE_NAME"; \
        echo "Example: just test-single test_install_sh.sh"; \
        exit 1; \
    fi
    @echo "Running test: {{TEST_FILE}}..."
    docker run -it --rm \
        --privileged \
        -v /nix:/nix \
        -e "NIX_REMOTE=daemon" \
        -e "NIX_INSTALLER_NO_MODIFY_PROFILE=1" \
        dotfiles-test \
        bash -c "./test/setup_test_env.sh && ./test/{{TEST_FILE}}"
