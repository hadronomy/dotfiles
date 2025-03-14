#!/usr/bin/env uv run

# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "typer",
#   "rich",
#   "pygithub",
#   "requests",
# ]
# ///

import getpass
import os
import platform
import re
import shlex
import signal
import subprocess
import sys
from typing import Literal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

app = typer.Typer()
console = Console()

DOTFILES_DIR = os.path.expanduser("~/.dotfiles")
REPO_URL = "https://github.com/hadronomy/dotfiles"
DEFAULT_USER = "hadronomy"
CURRENT_USER = getpass.getuser()
USER_CONFIG = {
    "username": CURRENT_USER,
    "git_name": "",
    "git_email": "",
    "git_signing_key": "",
    "use_signing_key": False,
    "signing_method": "",  # "gpg" or "ssh"
    "onepassword_disable": True,  # Default to disabling 1Password
}


def run_command(command, check=True, shell=False, dry_run=False):
    """Runs a shell command and streams the output in real-time with rich formatting."""
    if not shell:
        cmd_str = " ".join(shlex.quote(arg) for arg in command)
    else:
        cmd_str = command

    if dry_run:
        console.print(
            f"[bold yellow][DRY RUN][/bold yellow] [bold blue]Would run:[/bold blue] {cmd_str}"
        )
        return None

    console.print(f"[bold blue]Running:[/bold blue] {cmd_str}")
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=shell,
        )

        while True:
            stdout_line = process.stdout.readline()
            stderr_line = process.stderr.readline()

            if stdout_line:
                console.print(stdout_line.strip())
            if stderr_line:
                console.print(f"[dim]{stderr_line.strip()}[/dim]")

            if not stdout_line and not stderr_line and process.poll() is not None:
                break

        return_code = process.returncode
        if check and return_code != 0:
            raise subprocess.CalledProcessError(return_code, command)

        return process

    except subprocess.CalledProcessError as e:
        console.print(
            f"[bold red]Command failed with error code {e.returncode}[/bold red]"
        )
        if not dry_run:
            raise  # Re-raise to handle in the calling function
        return None
    except FileNotFoundError as e:
        console.print(f"[bold red]Command not found: {e}[/bold red]")
        if not dry_run:
            raise  # Re-raise to handle in the calling function
        return None


def install_nix(dry_run=False):
    """Installs Nix package manager."""
    if dry_run:
        console.print(
            "[bold yellow][DRY RUN][/bold yellow] Would install Nix package manager"
        )
        return

    console.print("[bold]Nix not found. Installing...[/bold]")
    system = platform.system()

    if system == "Linux":
        try:
            # Use a temporary directory in the user's home directory to avoid permission issues
            temp_dir = os.path.expanduser("~/.dotfiles/tmp")
            os.makedirs(temp_dir, exist_ok=True)
            install_script_path = os.path.join(temp_dir, "nix_install.sh")

            # Download the Nix installation script
            console.print("[yellow]Downloading Nix installer...[/yellow]")
            try:
                # Try with curl first (most robust for redirects)
                run_command(
                    [
                        "curl",
                        "-L",
                        "-o",
                        install_script_path,
                        "https://nixos.org/nix/install",
                    ],
                    check=True,
                )
            except Exception as curl_error:
                console.print(
                    f"[yellow]Curl failed: {curl_error}, trying wget...[/yellow]"
                )
                try:
                    # Try wget as backup
                    run_command(
                        [
                            "wget",
                            "-O",
                            install_script_path,
                            "https://nixos.org/nix/install",
                        ],
                        check=True,
                    )
                except Exception as wget_error:
                    # Last resort, try Python's urllib
                    console.print(
                        f"[yellow]Wget failed: {wget_error}, using Python...[/yellow]"
                    )
                    import urllib.request

                    urllib.request.urlretrieve(
                        "https://nixos.org/nix/install", install_script_path
                    )

            # Make the script executable
            os.chmod(install_script_path, 0o755)

            # Run the Nix installation script - try with sudo first, then fallback to regular user
            console.print("[yellow]Running Nix installer...[/yellow]")
            try:
                run_command(["sudo", install_script_path], check=True)
            except Exception as sudo_error:
                console.print(
                    f"[yellow]Sudo installation failed: {sudo_error}, trying without sudo...[/yellow]"
                )
                run_command([install_script_path], check=True)

            # Refresh the environment
            console.print("[bold]Refreshing environment...[/bold]")
            # Source nix.sh and capture the environment
            nix_profile_path = os.path.expanduser("~/.nix-profile/etc/profile.d/nix.sh")
            if os.path.exists(nix_profile_path):
                proc = subprocess.Popen(
                    f"source {nix_profile_path} && env",
                    stdout=subprocess.PIPE,
                    shell=True,
                )
                # Update current process environment with new variables
                for line in proc.stdout:
                    line = line.decode().strip()
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key] = value

            # Add experimental features to nix.conf
            configure_nix_experimental_features()

            # Clean up
            try:
                os.remove(install_script_path)
            except Exception:
                pass

            console.print(
                "[green]Nix installation complete. Please open a new terminal or source ~/.nix-profile/etc/profile.d/nix.sh for the changes to take effect.[/green]"
            )

        except Exception as e:
            console.print(
                f"[bold red]Error installing Nix: {str(e).replace(chr(92), chr(92) * 2).replace('[', '').replace(']', '')}[/bold red]"
            )
            cleanup(1)  # Call cleanup to delete the script on failure

    elif system == "Darwin":  # macOS
        console.print(
            "[bold yellow]Installing Nix on macOS requires manual steps. Please see https://nixos.org/download.html[/bold yellow]"
        )
        cleanup(1)  # Call cleanup to delete the script on failure
    else:
        console.print(
            "[bold red]Unsupported operating system for automatic Nix installation.[/bold red]"
        )
        cleanup(1)  # Call cleanup to delete the script on failure

    console.print(
        "[green]Nix installation complete. You may need to open a new terminal.[/green]"
    )


def configure_nix_experimental_features():
    """Configure experimental features in nix.conf."""
    try:
        # First try user's config directory
        nix_conf_dir = os.path.expanduser("~/.config/nix")
        nix_conf_file = os.path.join(nix_conf_dir, "nix.conf")

        # Check if ~/.config/nix exists, if not, check /etc/nix
        if not os.path.exists(nix_conf_dir):
            # Try to create user directory first
            try:
                os.makedirs(nix_conf_dir, exist_ok=True)
            except Exception:
                # Fall back to /etc/nix if user directory creation fails
                nix_conf_dir = "/etc/nix"
                nix_conf_file = os.path.join(nix_conf_dir, "nix.conf")

        # Create the directory if it doesn't exist
        if not os.path.exists(nix_conf_dir):
            try:
                os.makedirs(nix_conf_dir, exist_ok=True)
            except Exception as e:
                console.print(f"[yellow]Could not create {nix_conf_dir}: {e}[/yellow]")
                # Try to use a user-specific configuration as fallback
                nix_conf_dir = os.path.expanduser("~/.dotfiles/nix")
                os.makedirs(nix_conf_dir, exist_ok=True)
                nix_conf_file = os.path.join(nix_conf_dir, "nix.conf")
                console.print(
                    f"[yellow]Using fallback configuration at {nix_conf_file}[/yellow]"
                )

        # Check if the experimental features line already exists in the file
        line_exists = False
        if os.path.exists(nix_conf_file):
            try:
                with open(nix_conf_file, "r") as f:
                    for line in f:
                        if "experimental-features = nix-command flakes" in line:
                            line_exists = True
                            break
            except Exception as e:
                console.print(f"[yellow]Could not read {nix_conf_file}: {e}[/yellow]")
                line_exists = False

        if not line_exists:
            try:
                with open(nix_conf_file, "a") as f:
                    f.write("experimental-features = nix-command flakes\n")
                console.print("[green]Added experimental features to nix.conf.[/green]")
            except Exception as e:
                console.print(
                    f"[yellow]Could not write to {nix_conf_file}: {e}[/yellow]"
                )
                # If writing fails, create a user environment variable as workaround
                os.environ["NIX_CONFIG"] = "experimental-features = nix-command flakes"
                console.print(
                    "[yellow]Set NIX_CONFIG environment variable as fallback.[/yellow]"
                )
                # Also append to .bashrc or .zshrc for future sessions
                shell_rc_file = os.path.expanduser("~/.bashrc")
                if os.path.exists(os.path.expanduser("~/.zshrc")):
                    shell_rc_file = os.path.expanduser("~/.zshrc")

                try:
                    with open(shell_rc_file, "a") as f:
                        f.write(
                            '\n# Added by dotfiles installer\nexport NIX_CONFIG="experimental-features = nix-command flakes"\n'
                        )
                    console.print(
                        f"[green]Added NIX_CONFIG to {shell_rc_file}.[/green]"
                    )
                except Exception:
                    console.print(
                        "[yellow]Could not add NIX_CONFIG to shell config.[/yellow]"
                    )
        else:
            console.print(
                "[yellow]Experimental features already present in nix.conf.[/yellow]"
            )
    except Exception as e:
        console.print(
            f"[yellow]Error configuring Nix experimental features: {e}[/yellow]"
        )


def install_home_manager(dry_run=False):
    """Installs Home Manager."""
    if dry_run:
        console.print("[bold yellow][DRY RUN][/bold yellow] Would install Home Manager")
        return

    console.print("[bold]Installing Home Manager...[/bold]")
    try:
        run_command(
            [
                "nix-channel",
                "--add",
                "https://nixos.org/channels/nixpkgs-unstable",
                "nixpkgs",
            ]
        )
        run_command(
            [
                "nix-channel",
                "--add",
                "https://github.com/nix-community/home-manager/archive/master.tar.gz",
                "home-manager",
            ]
        )
        run_command(["nix-channel", "--update"])
        run_command(["nix-shell", "<home-manager>", "-A", "install"])
    except Exception as e:
        console.print(f"[bold red]Error installing Home Manager: {e}[/bold red]")
        sys.exit(1)
    console.print("[green]Home Manager installed successfully.[/green]")


def clone_dotfiles(dry_run=False):
    """Clones the dotfiles repository."""
    if dry_run:
        console.print(
            f"[bold yellow][DRY RUN][/bold yellow] Would clone {REPO_URL} to {DOTFILES_DIR}"
        )
        return

    if not os.path.exists(DOTFILES_DIR):
        console.print("[bold]Cloning dotfiles repository...[/bold]")
        os.makedirs(os.path.dirname(DOTFILES_DIR), exist_ok=True)
        try:
            run_command(["git", "clone", "--depth", "1", REPO_URL, DOTFILES_DIR])
        except Exception as e:
            console.print(f"[bold red]Error cloning dotfiles: {e}[/bold red]")
            sys.exit(1)
    else:
        console.print("[bold]Dotfiles repository already exists.[/bold]")


def customize_dotfiles(dry_run=False, force_customize=False):
    """Customize dotfiles for the current user if not the default user."""
    if CURRENT_USER == DEFAULT_USER and not force_customize:
        console.print(
            "[green]Running as the default user, no customization needed.[/green]"
        )
        return

    if not force_customize:
        console.print(
            "[bold yellow]Running as a non-default user, customization recommended.[/bold yellow]"
        )
    else:
        console.print(
            "[bold yellow]Customization forced by command line flag.[/bold yellow]"
        )

    # Always collect user information, even in dry run mode
    if force_customize or Confirm.ask(
        "Would you like to customize the dotfiles for your user?", default=True
    ):
        collect_user_info()

        # Apply the customizations, respecting dry run mode
        replace_username_in_files(dry_run=dry_run)
        update_git_config(dry_run=dry_run)

        if dry_run:
            console.print(
                "[bold yellow][DRY RUN][/bold yellow] Customization would be applied with these settings"
            )
        else:
            console.print("[green]Customization complete![/green]")


def collect_user_info():
    """Collect user information for customization."""
    console.print("[bold]Collecting user information for customization...[/bold]")

    USER_CONFIG["username"] = Prompt.ask("Username", default=CURRENT_USER)

    USER_CONFIG["git_name"] = Prompt.ask("Your full name (for Git config)", default="")

    USER_CONFIG["git_email"] = Prompt.ask("Your email (for Git config)", default="")

    # OnePassword settings
    USER_CONFIG["onepassword_disable"] = Confirm.ask(
        "Do you want to disable 1Password integration?", default=True
    )

    # Signing key options
    if Confirm.ask("Would you like to use commit signing?", default=True):
        USER_CONFIG["use_signing_key"] = True

        # Ask which signing method to use
        signing_methods = {"1": "GPG", "2": "SSH"}
        console.print(
            Panel.fit(
                "\n".join(
                    [
                        "[bold]Select a signing method:[/bold]",
                        "1. GPG key (traditional, works across all Git clients)",
                        "2. SSH key (simpler, uses your SSH credentials)",
                    ]
                ),
                title="Signing Methods",
            )
        )

        signing_choice = Prompt.ask(
            "Select a signing method [1-2]", default="2", choices=["1", "2"]
        )

        signing_method = signing_methods[signing_choice]
        USER_CONFIG["signing_method"] = signing_method.lower()

        if signing_method == "GPG":
            gpg_key_options(USER_CONFIG)
        else:  # SSH
            ssh_key_options(USER_CONFIG)


def gpg_key_options(config):
    """Handle GPG key options for Git commit signing."""
    existing_gpg_keys = list_gpg_keys()

    if existing_gpg_keys:
        console.print("[green]Found existing GPG keys:[/green]")

        table = Table(show_header=True)
        table.add_column("#", justify="right", style="cyan", no_wrap=True)
        table.add_column("Key ID", style="magenta")
        table.add_column("User Info", style="green")

        for idx, (key_id, user_info) in enumerate(existing_gpg_keys, 1):
            table.add_row(str(idx), key_id, user_info)

        console.print(table)

        if Confirm.ask("Would you like to use an existing key?", default=True):
            # Fix: Use choices with Prompt instead of IntPrompt with min/max values
            choices = [str(i) for i in range(1, len(existing_gpg_keys) + 1)]
            choice_str = Prompt.ask(
                "Enter the number of the key to use", default="1", choices=choices
            )
            choice = int(choice_str)
            config["git_signing_key"] = existing_gpg_keys[choice - 1][0]
            console.print(f"[green]Using GPG key: {config['git_signing_key']}[/green]")

            # Optionally add to GitHub
            if Confirm.ask(
                "Would you like to add this key to your GitHub account?", default=False
            ):
                add_key_to_github("gpg", config["git_signing_key"])

            return

    # Create a new GPG key if desired
    if Confirm.ask("Would you like to create a new GPG key?", default=True):
        console.print("[bold]Creating new GPG key...[/bold]")
        key_id = create_gpg_key(config["git_name"], config["git_email"])

        if key_id:
            config["git_signing_key"] = key_id
            console.print(f"[green]Created GPG key: {key_id}[/green]")

            # Changed default to True for newly created keys
            if Confirm.ask(
                "Would you like to add this key to your GitHub account?", default=True
            ):
                add_key_to_github("gpg", key_id)
        else:
            console.print("[yellow]GPG key creation failed or was cancelled.[/yellow]")
            config["git_signing_key"] = Prompt.ask(
                "Enter your GPG key ID manually", default=""
            )
    else:
        config["git_signing_key"] = Prompt.ask(
            "Enter your GPG key ID manually", default=""
        )


def ssh_key_options(config):
    """Handle SSH key options for Git commit signing."""
    existing_ssh_keys = list_ssh_keys()

    if existing_ssh_keys:
        console.print("[green]Found existing SSH keys:[/green]")

        table = Table(show_header=True)
        table.add_column("#", justify="right", style="cyan", no_wrap=True)
        table.add_column("Key Path", style="magenta")

        for idx, key_path in enumerate(existing_ssh_keys, 1):
            table.add_row(str(idx), key_path)

        console.print(table)

        if Confirm.ask("Would you like to use an existing key?", default=True):
            # Fix: Use choices with Prompt instead of IntPrompt with min/max values
            choices = [str(i) for i in range(1, len(existing_ssh_keys) + 1)]
            choice_str = Prompt.ask(
                "Enter the number of the key to use", default="1", choices=choices
            )
            choice = int(choice_str)
            config["git_signing_key"] = existing_ssh_keys[choice - 1]
            console.print(f"[green]Using SSH key: {config['git_signing_key']}[/green]")

            # Optionally add to GitHub
            if Confirm.ask(
                "Would you like to add this key to your GitHub account for signing?",
                default=False,
            ):
                add_key_to_github("ssh-signing", config["git_signing_key"])

            return

    # Create a new SSH key if desired
    if Confirm.ask("Would you like to create a new SSH key for signing?", default=True):
        console.print("[bold]Creating new SSH key...[/bold]")
        key_path = create_ssh_key(config["git_email"])

        if key_path:
            config["git_signing_key"] = key_path
            console.print(f"[green]Created SSH key: {key_path}[/green]")

            # Changed default to True for newly created keys
            if Confirm.ask(
                "Would you like to add this key to your GitHub account?", default=True
            ):
                add_key_to_github("ssh-signing", key_path)
        else:
            console.print("[yellow]SSH key creation failed or was cancelled.[/yellow]")
            config["git_signing_key"] = Prompt.ask(
                "Enter your SSH key path manually", default="~/.ssh/id_ed25519"
            )
    else:
        config["git_signing_key"] = Prompt.ask(
            "Enter your SSH key path manually", default="~/.ssh/id_ed25519"
        )


def list_gpg_keys():
    """List existing GPG keys."""
    try:
        result = subprocess.run(
            ["gpg", "--list-secret-keys", "--keyid-format", "long"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            return []

        output = result.stdout
        keys = []

        key_id = None
        user_info = None

        for line in output.splitlines():
            if "sec" in line and "/" in line:
                # Extract the key ID
                parts = line.split("/")
                if len(parts) >= 2:
                    key_id = parts[1].split(" ")[0]
            elif "uid" in line and key_id:
                # Extract user info
                if "]" in line:
                    user_info = line.split("]")[1].strip()
                else:
                    user_info = line.split("uid")[1].strip()

                if key_id and user_info:
                    keys.append((key_id, user_info))
                    key_id = None
                    user_info = None

        return keys
    except Exception as e:
        console.print(f"[yellow]Error listing GPG keys: {e}[/yellow]")
        return []


def create_gpg_key(name, email):
    """Create a new GPG key."""
    try:
        # Create a batch file for GPG key generation
        batch_file = os.path.expanduser("~/.gnupg/batch")
        os.makedirs(os.path.dirname(batch_file), exist_ok=True)

        with open(batch_file, "w") as f:
            f.write(
                f"""
Key-Type: RSA
Key-Length: 4096
Name-Real: {name}
Name-Email: {email}
Expire-Date: 0
%no-protection
%commit
            """.strip()
            )

        # Generate the key
        console.print("[yellow]Generating GPG key... this may take a moment.[/yellow]")
        result = subprocess.run(
            ["gpg", "--batch", "--generate-key", batch_file],
            capture_output=True,
            text=True,
            check=False,
        )

        # Clean up the batch file
        try:
            os.remove(batch_file)
        except Exception:
            pass

        if result.returncode != 0:
            console.print(f"[red]GPG key generation failed:[/red]\n{result.stderr}")
            return None

        # Get the key ID of the newly created key
        list_result = subprocess.run(
            ["gpg", "--list-secret-keys", "--keyid-format", "long", email],
            capture_output=True,
            text=True,
            check=False,
        )

        output = list_result.stdout
        for line in output.splitlines():
            if "sec" in line and "/" in line:
                parts = line.split("/")
                if len(parts) >= 2:
                    return parts[1].split(" ")[0]

        return None
    except Exception as e:
        console.print(f"[red]Error creating GPG key: {e}[/red]")
        return None


def list_ssh_keys():
    """List existing SSH keys."""
    ssh_dir = os.path.expanduser("~/.ssh")
    if not os.path.exists(ssh_dir):
        return []

    keys = []
    for file in os.listdir(ssh_dir):
        if file.endswith(".pub") and not file.startswith("known_hosts"):
            private_key = os.path.join(ssh_dir, file[:-4])  # Remove .pub extension
            if os.path.exists(private_key):
                keys.append(private_key)

    return keys


def create_ssh_key(email):
    """Create a new SSH key."""
    try:
        key_path = os.path.expanduser("~/.ssh/id_signing_ed25519")

        # Create .ssh directory if it doesn't exist
        os.makedirs(os.path.dirname(key_path), exist_ok=True)

        # Generate the key
        console.print("[yellow]Generating SSH key...[/yellow]")
        result = subprocess.run(
            [
                "ssh-keygen",
                "-t",
                "ed25519",
                "-C",
                email,
                "-f",
                key_path,
                "-N",
                "",  # No passphrase
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            console.print(f"[red]SSH key generation failed:[/red]\n{result.stderr}")
            return None

        return key_path
    except Exception as e:
        console.print(f"[red]Error creating SSH key: {e}[/red]")
        return None


def add_key_to_github(key_type: Literal["gpg", "ssh", "ssh-signing"], key_path_or_id):
    """Add a key to GitHub."""
    try:
        # Check if gh CLI is available
        if command_exists("gh"):
            if key_type == "gpg":
                # Export the GPG public key
                export_result = subprocess.run(
                    ["gpg", "--armor", "--export", key_path_or_id],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if export_result.returncode != 0:
                    console.print("[red]Failed to export GPG key.[/red]")
                    return False

                gpg_key = export_result.stdout

                # Save to a temporary file
                tmp_file = os.path.expanduser("~/gpg_key.asc")
                with open(tmp_file, "w") as f:
                    f.write(gpg_key)

                # Add to GitHub using gh CLI
                console.print("[yellow]Adding GPG key to GitHub...[/yellow]")
                gh_result = subprocess.run(
                    ["gh", "gpg-key", "add", tmp_file],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                # Clean up
                try:
                    os.remove(tmp_file)
                except Exception:
                    pass

                if gh_result.returncode != 0:
                    console.print(
                        f"[red]Failed to add GPG key to GitHub:[/red]\n{gh_result.stderr}"
                    )
                    return False

                console.print("[green]GPG key added to GitHub successfully![/green]")
                return True

            elif key_type == "ssh" or key_type == "ssh-signing":
                # Read the SSH public key
                pub_key_path = f"{key_path_or_id}.pub"
                if not os.path.exists(pub_key_path):
                    console.print(
                        f"[red]SSH public key not found: {pub_key_path}[/red]"
                    )
                    return False

                with open(pub_key_path, "r") as f:
                    ssh_key = f.read().strip()

                # Add to GitHub using gh CLI
                title = (
                    f"{platform.node()}-signing-key"
                    if key_type == "ssh-signing"
                    else f"{platform.node()}-key"
                )

                console.print(
                    f"[yellow]Adding SSH key to GitHub as {key_type}...[/yellow]"
                )

                if key_type == "ssh-signing":
                    # First, ensure we have the proper scope for SSH signing keys
                    auth_status = subprocess.run(
                        ["gh", "auth", "status"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    if "admin:ssh_signing_key" not in auth_status.stdout:
                        console.print(
                            "[yellow]The GitHub CLI needs additional permissions for SSH signing keys.[/yellow]"
                        )
                        console.print(
                            "[yellow]Running: gh auth refresh -h github.com -s admin:ssh_signing_key[/yellow]"
                        )

                        # Use direct execution with subprocess.call to show output in real-time
                        console.print(
                            "[bold]Follow the instructions in the browser to authorize the additional scopes:[/bold]"
                        )

                        # Don't capture output - let it go straight to the terminal
                        refresh_result = subprocess.call(
                            [
                                "gh",
                                "auth",
                                "refresh",
                                "-h",
                                "github.com",
                                "-s",
                                "admin:ssh_signing_key",
                            ]
                        )

                        if refresh_result != 0:
                            console.print(
                                f"[red]Failed to update GitHub CLI permissions (exit code: {refresh_result})[/red]"
                            )
                            console.print(
                                "[yellow]You may need to manually add your SSH signing key to GitHub.[/yellow]"
                            )
                            return False

                        console.print(
                            "[green]Successfully updated GitHub CLI permissions.[/green]"
                        )

                # Now add the key
                cmd = ["gh", "ssh-key", "add", pub_key_path, "--title", title]
                if key_type == "ssh-signing":
                    cmd.append("--type")
                    cmd.append("signing")

                gh_result = subprocess.run(
                    cmd, capture_output=True, text=True, check=False
                )

                if gh_result.returncode != 0:
                    console.print(
                        f"[red]Failed to add SSH key to GitHub:[/red]\n{gh_result.stderr}"
                    )
                    return False

                console.print("[green]SSH key added to GitHub successfully![/green]")
                return True
        else:
            # GitHub CLI not available
            console.print(
                "[yellow]GitHub CLI (gh) not found. Using web authentication flow instead.[/yellow]"
            )

            # Use device flow authentication
            if Confirm.ask(
                "Would you like to authenticate with GitHub to add your key?",
                default=True,
            ):
                try:
                    import json
                    import time
                    import webbrowser

                    import requests

                    # GitHub OAuth Device Flow
                    client_id = "4c1b8d54bc04094aa3c8"  # Client ID for a generic GitHub OAuth App

                    # Update scope to include ssh_signing_key permissions
                    scope = "admin:public_key admin:gpg_key admin:ssh_signing_key"

                    # Step 1: Request device code
                    device_code_url = "https://github.com/login/device/code"
                    device_response = requests.post(
                        device_code_url,
                        headers={"Accept": "application/json"},
                        data={"client_id": client_id, "scope": scope},
                    )

                    if device_response.status_code != 200:
                        console.print(
                            "[red]Failed to start GitHub authentication.[/red]"
                        )
                        return False

                    device_data = device_response.json()
                    device_code = device_data["device_code"]
                    user_code = device_data["user_code"]
                    verification_uri = device_data["verification_uri"]
                    expires_in = device_data["expires_in"]
                    interval = device_data["interval"]

                    # Display instructions to the user
                    console.print(
                        Panel.fit(
                            f"\n[bold green]GitHub Authentication Required[/bold green]\n\n"
                            f"1. Go to: [bold blue]{verification_uri}[/bold blue]\n"
                            f"2. Enter code: [bold yellow]{user_code}[/bold yellow]\n"
                            f"3. Authorize this application\n",
                            title="GitHub Device Flow",
                        )
                    )

                    # Try to open the browser automatically
                    try:
                        webbrowser.open(verification_uri)
                    except Exception:
                        pass

                    # Step 2: Poll for the access token
                    token_url = "https://github.com/login/oauth/access_token"
                    start_time = time.time()
                    access_token = None

                    with console.status(
                        "[bold green]Waiting for GitHub authorization..."
                    ) as _:
                        while time.time() - start_time < expires_in:
                            token_response = requests.post(
                                token_url,
                                headers={"Accept": "application/json"},
                                data={
                                    "client_id": client_id,
                                    "device_code": device_code,
                                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                                },
                            )

                            token_data = token_response.json()

                            if "error" not in token_data:
                                access_token = token_data["access_token"]
                                break

                            if token_data["error"] != "authorization_pending":
                                if token_data["error"] == "slow_down":
                                    interval += 5
                                else:
                                    console.print(
                                        f"[red]Error: {token_data['error']}[/red]"
                                    )
                                    return False

                            time.sleep(interval)

                    if not access_token:
                        console.print("[red]GitHub authorization timed out.[/red]")
                        return False

                    # Now use the token with PyGithub
                    from github import Github, GithubException

                    g = Github(access_token)
                    user = g.get_user()

                    if key_type == "gpg":
                        # Export the GPG public key
                        export_result = subprocess.run(
                            ["gpg", "--armor", "--export", key_path_or_id],
                            capture_output=True,
                            text=True,
                            check=False,
                        )

                        if export_result.returncode != 0:
                            console.print("[red]Failed to export GPG key.[/red]")
                            return False

                        gpg_key = export_result.stdout
                        user.create_gpg_key(gpg_key)
                        console.print(
                            "[green]GPG key added to GitHub successfully![/green]"
                        )

                    elif key_type == "ssh" or key_type == "ssh-signing":
                        # Read the SSH public key
                        pub_key_path = f"{key_path_or_id}.pub"
                        if not os.path.exists(pub_key_path):
                            console.print(
                                f"[red]SSH public key not found: {pub_key_path}[/red]"
                            )
                            return False

                        with open(pub_key_path, "r") as f:
                            ssh_key = f.read().strip()

                        title = f"{platform.node()}-{'signing-' if key_type == 'ssh-signing' else ''}key"

                        if key_type == "ssh-signing":
                            # For signing keys, we need to use the REST API directly since PyGithub
                            # doesn't support the key_type parameter yet
                            headers = {
                                "Accept": "application/vnd.github+json",
                                "Authorization": f"Bearer {access_token}",
                                "X-GitHub-Api-Version": "2022-11-28",
                            }

                            data = {
                                "title": title,
                                "key": ssh_key,
                            }

                            response = requests.post(
                                "https://api.github.com/user/ssh_signing_keys",
                                headers=headers,
                                data=json.dumps(data),
                            )

                            if response.status_code == 201:
                                console.print(
                                    "[green]SSH signing key added to GitHub successfully![/green]"
                                )
                                return True
                            else:
                                console.print(
                                    f"[red]Failed to add SSH signing key: {response.json().get('message', 'Unknown error')}[/red]"
                                )
                                return False
                        else:
                            # Regular SSH key
                            user.create_key(title=title, key=ssh_key)
                            console.print(
                                "[green]SSH key added to GitHub successfully![/green]"
                            )

                    return True

                except ImportError as e:
                    console.print(f"[red]Failed to import necessary modules: {e}[/red]")
                except requests.RequestException as e:
                    console.print(f"[red]Network error: {e}[/red]")
                except GithubException as e:
                    console.print(f"[red]GitHub API error: {e}[/red]")
                except Exception as e:
                    console.print(f"[red]Error adding key to GitHub: {e}[/red]")

            console.print(
                "[yellow]You can add your keys manually at https://github.com/settings/keys[/yellow]"
            )
        return False
    except Exception as e:
        console.print(f"[red]Error adding key to GitHub: {e}[/red]")
        return False


def replace_username_in_files(dry_run=False):
    """Replace instances of the default username with the current user's username."""
    console.print(
        f"[bold]{'[bold yellow][DRY RUN][/bold yellow] Would replace' if dry_run else 'Replacing'} '{DEFAULT_USER}' with '{USER_CONFIG['username']}' in dotfiles...[/bold]"
    )

    # Define patterns to avoid changing in certain files or types
    excluded_dirs = [".git", "node_modules", ".cache", "target"]
    excluded_exts = [
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ico",
        ".svg",
        ".ttf",
        ".woff",
        ".woff2",
    ]

    for root, dirs, files in os.walk(DOTFILES_DIR):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in excluded_dirs]

        for file in files:
            if any(file.endswith(ext) for ext in excluded_exts):
                continue

            file_path = os.path.join(root, file)

            try:
                # Skip binary files
                if is_binary(file_path):
                    continue

                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Replace only if content contains the pattern
                if DEFAULT_USER in content:
                    if not dry_run:
                        modified_content = content.replace(
                            DEFAULT_USER, USER_CONFIG["username"]
                        )
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(modified_content)

                    console.print(
                        f"  {'[bold yellow][DRY RUN][/bold yellow] Would update' if dry_run else 'Updated'}: {file_path}"
                    )
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not process {file_path}: {e}[/yellow]"
                )


def update_git_config(dry_run=False):
    """Update Git configuration with user information."""
    if (
        not USER_CONFIG["git_name"]
        and not USER_CONFIG["git_email"]
        and not USER_CONFIG["use_signing_key"]
    ):
        return

    console.print(
        f"[bold]{'[bold yellow][DRY RUN][/bold yellow] Updating' if dry_run else 'Updating'} Git configuration...[/bold]"
    )

    git_config_path = os.path.join(DOTFILES_DIR, "home", "git", "default.nix")
    if not os.path.exists(git_config_path):
        console.print(
            "[yellow]Git config file not found, skipping Git configuration.[/yellow]"
        )
        return

    try:
        with open(git_config_path, "r") as f:
            content = f.read()

        original_content = content

        # Update user name if provided
        if USER_CONFIG["git_name"]:
            content = re.sub(
                r'userName\s*=\s*"[^"]*"',
                f'userName = "{USER_CONFIG["git_name"]}"',
                content,
            )
            console.print(
                f"  {'[bold yellow][DRY RUN][/bold yellow] Would set' if dry_run else 'Set'} Git user name to: {USER_CONFIG['git_name']}"
            )

        # Update email if provided
        if USER_CONFIG["git_email"]:
            content = re.sub(
                r'userEmail\s*=\s*"[^"]*"',
                f'userEmail = "{USER_CONFIG["git_email"]}"',
                content,
            )
            console.print(
                f"  {'[bold yellow][DRY RUN][/bold yellow] Would set' if dry_run else 'Set'} Git email to: {USER_CONFIG['git_email']}"
            )

        # Update signing configuration
        if USER_CONFIG["use_signing_key"]:
            signing_method = USER_CONFIG["signing_method"]
            signing_key = USER_CONFIG["git_signing_key"]

            if signing_method == "gpg":
                # Configure GPG signing
                if "gpg.format" in content:
                    content = re.sub(
                        r'gpg\.format\s*=\s*"[^"]*"',
                        'gpg.format = "openpgp"',
                        content,
                    )
                else:
                    content = re.sub(
                        r"(extraConfig\s*=\s*{)",
                        '\\1\n      gpg.format = "openpgp";',
                        content,
                    )

                if "user.signingkey" in content:
                    content = re.sub(
                        r'user\.signingkey\s*=\s*"[^"]*"',
                        f'user.signingkey = "{signing_key}"',
                        content,
                    )
                else:
                    content = re.sub(
                        r"(extraConfig\s*=\s*{)",
                        f'\\1\n      user.signingkey = "{signing_key}";',
                        content,
                    )

                console.print(
                    f"  {'[bold yellow][DRY RUN][/bold yellow] Would set' if dry_run else 'Set'} Git GPG signing key to: {signing_key}"
                )

            elif signing_method == "ssh":
                # Configure SSH signing
                if "gpg.format" in content:
                    content = re.sub(
                        r'gpg\.format\s*=\s*"[^"]*"',
                        'gpg.format = "ssh"',
                        content,
                    )
                else:
                    content = re.sub(
                        r"(extraConfig\s*=\s*{)",
                        '\\1\n      gpg.format = "ssh";',
                        content,
                    )

                if "user.signingkey" in content:
                    content = re.sub(
                        r'user\.signingkey\s*=\s*"[^"]*"',
                        f'user.signingkey = "{signing_key}"',
                        content,
                    )
                else:
                    content = re.sub(
                        r"(extraConfig\s*=\s*{)",
                        f'\\1\n      user.signingkey = "{signing_key}";',
                        content,
                    )

                # Add SSH specific configuration
                ssh_config_lines = [
                    'gpg.ssh.allowedSignersFile = "~/.ssh/allowed_signers";',
                    'gpg.ssh.program = "ssh-keygen";',
                ]

                for line in ssh_config_lines:
                    if line.split("=")[0].strip() not in content:
                        content = re.sub(
                            r"(extraConfig\s*=\s*{)",
                            f"\\1\n      {line}",
                            content,
                        )

                console.print(
                    f"  {'[bold yellow][DRY RUN][/bold yellow] Would set' if dry_run else 'Set'} Git SSH signing key to: {signing_key}"
                )

            # Set commit.gpgsign regardless of method
            if "commit.gpgSign" in content:
                content = re.sub(
                    r"commit\.gpgSign\s*=\s*(true|false)",
                    "commit.gpgSign = true",
                    content,
                )
            else:
                content = re.sub(
                    r"(extraConfig\s*=\s*{)",
                    "\\1\n      commit.gpgSign = true;",
                    content,
                )

        # Configure OnePassword if needed
        if "onepassword" in content and USER_CONFIG["onepassword_disable"]:
            # Check if we need to disable 1Password
            if "credential.helper" in content and "op" in content:
                content = re.sub(
                    r'credential\.helper\s*=\s*"1password"',
                    'credential.helper = "store"',  # Use the default store instead
                    content,
                )
                console.print(
                    f"  {'[bold yellow][DRY RUN][/bold yellow] Would disable' if dry_run else 'Disabled'} 1Password integration"
                )

        if not dry_run and content != original_content:
            with open(git_config_path, "w") as f:
                f.write(content)

            # If SSH signing was configured, also set up allowed_signers file
            if (
                USER_CONFIG["use_signing_key"]
                and USER_CONFIG["signing_method"] == "ssh"
            ):
                allowed_signers_path = os.path.expanduser("~/.ssh/allowed_signers")
                os.makedirs(os.path.dirname(allowed_signers_path), exist_ok=True)

                # Get the public key content
                pub_key_path = f"{USER_CONFIG['git_signing_key']}.pub"
                if os.path.exists(pub_key_path):
                    with open(pub_key_path, "r") as f:
                        pub_key = f.read().strip()

                    # Write to allowed_signers
                    with open(allowed_signers_path, "w") as f:
                        f.write(f"{USER_CONFIG['git_email']} {pub_key}\n")

                    console.print(
                        f"[green]Created SSH allowed_signers file at {allowed_signers_path}[/green]"
                    )

            console.print("[green]Git configuration updated successfully![/green]")

    except Exception as e:
        console.print(
            f"[yellow]Warning: Could not update Git configuration: {e}[/yellow]"
        )


def is_binary(file_path):
    """Check if a file is binary."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            return b"\0" in chunk
    except IOError:
        return True


def command_exists(command, dry_run=False):
    """Checks if a command exists."""
    if dry_run:
        # In dry-run mode, just assume the command might exist
        return False

    try:
        # Use 'which' instead of 'command -v' as it's more likely to be available
        # as an actual executable rather than a shell builtin
        result = subprocess.run(
            ["which", command],
            check=False,  # Don't raise exception on non-zero exit
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        # If 'which' is not available, try a different approach
        try:
            # Try with shutil.which which is a pure Python solution
            import shutil

            return shutil.which(command) is not None
        except Exception:
            return False


def apply_home_manager(dry_run=False):
    """Applies the Home Manager configuration."""
    if dry_run:
        console.print(
            "[bold yellow][DRY RUN][/bold yellow] Would apply Home Manager configuration"
        )
        return

    console.print("[bold]Applying Home Manager configuration...[/bold]")
    try:
        run_command(
            [
                "home-manager",
                "switch",
                "--flake",
                DOTFILES_DIR,
                "-b",
                "backup",
                "--impure",
            ]
        )
    except Exception as e:
        console.print(
            f"[bold red]Error applying Home Manager configuration: {e}[/bold red]"
        )
        sys.exit(1)
    console.print("[green]Dotfiles applied successfully![/green]")


def handle_exit_signal(signum, frame):
    """Handle exit signals by cleaning up and deleting the script."""
    console.print("\n[bold red]Received termination signal. Cleaning up...[/bold red]")
    cleanup(1)


def is_run_from_install_sh():
    """Check if the script is being run from the install.sh wrapper."""
    # Check environment for a marker or inspect the stack
    parent_process = None
    try:
        import psutil

        current_process = psutil.Process()
        parent_process = current_process.parent()
        if parent_process:
            # Check if the parent process command contains install.sh
            cmdline = " ".join(parent_process.cmdline()).lower()
            return "install.sh" in cmdline
    except (ImportError, psutil.Error):
        # Fallback method if psutil is not available
        try:
            # Check for an environment variable that could be set by install.sh
            return os.environ.get("FROM_DOTFILES_INSTALLER") == "true"
        except Exception:
            pass

    # As a last resort, check if we were invoked by curl/wget piping to bash
    try:
        import traceback

        stack = traceback.extract_stack()
        for frame in stack:
            if "install.sh" in frame.filename:
                return True
    except Exception:
        pass

    return False


def cleanup(exit_code=0):
    """Clean up by deleting the script and exiting with the specified code."""
    script_path = os.path.abspath(__file__)

    # Only delete the script if we're being run from install.sh
    if is_run_from_install_sh():
        console.print(
            f"[bold red]Installation failed! Removing script: {script_path}[/bold red]"
        )
        try:
            os.remove(script_path)
            console.print("[yellow]Script removed successfully.[/yellow]")
        except Exception as e:
            console.print(f"[bold red]Failed to remove script: {e}[/bold red]")
    else:
        console.print(
            f"[bold red]Installation failed! Script not removed as it wasn't run from install.sh.[/bold red]"
        )

    sys.exit(exit_code)


@app.command()
def install(
    repo_url: str = typer.Option(REPO_URL, help="The URL of the dotfiles repository."),
    dotfiles_dir: str = typer.Option(
        DOTFILES_DIR, help="The directory to clone the dotfiles into."
    ),
    impure: bool = typer.Option(True, help="Use the --impure flag for home-manager."),
    skip_customization: bool = typer.Option(False, help="Skip the customization step."),
    customize: bool = typer.Option(
        False, help="Force customization regardless of username."
    ),
    dry_run: bool = typer.Option(
        False, help="Perform a dry run without making any changes."
    ),
):
    """Installs Nix, Home Manager, and applies the dotfiles configuration."""
    global REPO_URL, DOTFILES_DIR
    REPO_URL = repo_url
    DOTFILES_DIR = dotfiles_dir

    # Set up signal handlers for clean termination
    signal.signal(signal.SIGINT, handle_exit_signal)  # Ctrl+C
    signal.signal(signal.SIGTERM, handle_exit_signal)  # Termination signal

    try:
        # Check for incompatible flags
        if skip_customization and customize:
            console.print(
                "[bold red]Error: --skip-customization and --customize cannot be used together.[/bold red]"
            )
            cleanup(1)

        if dry_run:
            console.print(
                "[bold yellow]Running in DRY RUN mode. No changes will be made.[/bold yellow]"
            )

        # Pass dry_run parameter to command_exists
        if not command_exists("nix", dry_run=dry_run):
            install_nix(dry_run=dry_run)

        # Pass dry_run parameter to command_exists
        if not command_exists("home-manager", dry_run=dry_run) and not dry_run:
            install_home_manager(dry_run=dry_run)

        clone_dotfiles(dry_run=dry_run)

        if customize:
            customize_dotfiles(dry_run=dry_run, force_customize=True)
        elif not skip_customization:
            customize_dotfiles(dry_run=dry_run)

        apply_home_manager(dry_run=dry_run)

        if dry_run:
            console.print(
                "[bold yellow]Dry run complete. No changes were made.[/bold yellow]"
            )

    except Exception as e:
        console.print(f"[bold red]Installation failed with error: {e}[/bold red]")
        if not dry_run:
            cleanup(1)


if __name__ == "__main__":
    try:
        app()
    except Exception as e:
        console.print(f"[bold red]Fatal error: {e}[/bold red]")
        cleanup(1)
