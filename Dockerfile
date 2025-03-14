FROM ubuntu:22.04

# Set non-interactive mode for apt
ENV DEBIAN_FRONTEND=noninteractive

# Install essential tools
RUN apt-get update && apt-get install -y \
  curl \
  git \
  wget \
  python3 \
  python3-pip \
  sudo \
  xz-utils \
  gnupg \
  openssh-client \
  ca-certificates \
  coreutils \
  file

# Set up for Nix installation
RUN mkdir -p /etc/nix && \
  echo "build-users-group =" > /etc/nix/nix.conf && \
  echo "experimental-features = nix-command flakes" >> /etc/nix/nix.conf

# Create a test user that can use sudo
RUN useradd -m tester && \
  echo "tester ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/tester

# Set working directory
WORKDIR /home/tester/dotfiles

# Copy dotfiles to the container
COPY . .

# Set proper ownership
RUN chown -R tester:tester /home/tester

# Make test scripts executable
RUN chmod +x test/*.sh || echo "No test scripts to make executable yet"

# Switch to test user
USER tester

# Set up SSH directory for the test user
RUN mkdir -p /home/tester/.ssh && \
  chmod 700 /home/tester/.ssh

# Command that will be run when container starts
CMD ["/bin/bash"]
