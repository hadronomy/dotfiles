#!/usr/bin/env uv run

# /// script
# dependencies = [
#   "typer",
#   "rich",
# ]
# ///

import getpass
import os
import platform
import re
import shlex
import subprocess
import sys

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

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
}


def run_command(command, check=True, shell=False):
    """Runs a shell command and streams the output in real-time with rich formatting."""
    if not shell:
        cmd_str = " ".join(shlex.quote(arg) for arg in command)
    else:
        cmd_str = command
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
        sys.exit(1)
    except FileNotFoundError as e:
        console.print(f"[bold red]Command not found: {e}[/bold red]")
        sys.exit(1)


def install_nix():
    """Installs Nix package manager."""
    console.print("[bold]Nix not found. Installing...[/bold]")
    system = platform.system()

    if system == "Linux":
        try:
            # Download the Nix installation script
            run_command(
                [
                    "curl",
                    "-L",
                    "-o",
                    "/tmp/nix_install.sh",
                    "https://nixos.org/nix/install",
                ],
                check=True,
            )
            # Run the Nix installation script
            run_command(["sudo", "sh", "/tmp/nix_install.sh"], check=True)

            # Refresh the environment
            console.print("[bold]Refreshing environment...[/bold]")
            # Source nix.sh and capture the environment
            proc = subprocess.Popen(
                f"source {os.path.expanduser('~')}/.nix-profile/etc/profile.d/nix.sh && env",
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
            nix_conf_dir = os.path.expanduser("~/.config/nix")
            nix_conf_file = os.path.join(nix_conf_dir, "nix.conf")

            # Check if ~/.config/nix exists, if not, check /etc/nix
            if not os.path.exists(nix_conf_dir):
                nix_conf_dir = "/etc/nix"
                nix_conf_file = os.path.join(nix_conf_dir, "nix.conf")

            # Create the directory if it doesn't exist
            if not os.path.exists(nix_conf_dir):
                os.makedirs(nix_conf_dir, exist_ok=True)

            # Check if the line already exists in the file
            line_exists = False
            if os.path.exists(nix_conf_file):
                with open(nix_conf_file, "r") as f:
                    for line in f:
                        if "experimental-features = nix-command flakes" in line:
                            line_exists = True
                            break

            if not line_exists:
                with open(nix_conf_file, "a") as f:
                    f.write("experimental-features = nix-command flakes\n")
                console.print("[green]Added experimental features to nix.conf.[/green]")
            else:
                console.print(
                    "[yellow]Experimental features already present in nix.conf.[/yellow]"
                )

            console.print(
                "[green]Nix installation complete.  Please open a new terminal or source ~/.nix-profile/etc/profile.d/nix.sh for the changes to take effect.[/green]"
            )

        except Exception as e:
            console.print(
                f"[bold red]Error installing Nix: {str(e).replace(chr(92), chr(92) * 2).replace('[', '').replace(']', '')}[/bold red]"
            )
            sys.exit(1)

    elif system == "Darwin":  # macOS
        console.print(
            "[bold yellow]Installing Nix on macOS requires manual steps.  Please see https://nixos.org/download.html[/bold yellow]"
        )
        sys.exit(1)
    else:
        console.print(
            "[bold red]Unsupported operating system for automatic Nix installation.[/bold red]"
        )
        sys.exit(1)

    console.print(
        "[green]Nix installation complete.  You may need to open a new terminal.[/green]"
    )


def install_home_manager():
    """Installs Home Manager."""
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


def clone_dotfiles():
    """Clones the dotfiles repository."""
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


def customize_dotfiles():
    """Customize dotfiles for the current user if not the default user."""
    if CURRENT_USER == DEFAULT_USER:
        console.print(
            "[green]Running as the default user, no customization needed.[/green]"
        )
        return

    console.print(
        "[bold yellow]Running as a non-default user, customization recommended.[/bold yellow]"
    )
    if Confirm.ask(
        "Would you like to customize the dotfiles for your user?", default=True
    ):
        collect_user_info()
        replace_username_in_files()
        update_git_config()
        console.print("[green]Customization complete![/green]")


def collect_user_info():
    """Collect user information for customization."""
    console.print("[bold]Collecting user information for customization...[/bold]")

    USER_CONFIG["username"] = Prompt.ask("Username", default=CURRENT_USER)

    USER_CONFIG["git_name"] = Prompt.ask("Your full name (for Git config)", default="")

    USER_CONFIG["git_email"] = Prompt.ask("Your email (for Git config)", default="")

    if Confirm.ask(
        "Would you like to use a GPG key for Git commit signing?", default=False
    ):
        USER_CONFIG["use_signing_key"] = True
        USER_CONFIG["git_signing_key"] = Prompt.ask(
            "Your GPG key ID for signing commits", default=""
        )


def replace_username_in_files():
    """Replace instances of the default username with the current user's username."""
    console.print(
        f"[bold]Replacing '{DEFAULT_USER}' with '{USER_CONFIG['username']}' in dotfiles...[/bold]"
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
                    modified_content = content.replace(
                        DEFAULT_USER, USER_CONFIG["username"]
                    )

                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(modified_content)

                    console.print(f"  Updated: {file_path}")
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not process {file_path}: {e}[/yellow]"
                )


def update_git_config():
    """Update Git configuration with user information."""
    if not USER_CONFIG["git_name"] and not USER_CONFIG["git_email"]:
        return

    console.print("[bold]Updating Git configuration...[/bold]")

    git_config_path = os.path.join(DOTFILES_DIR, "home", "git", "default.nix")
    if not os.path.exists(git_config_path):
        console.print(
            "[yellow]Git config file not found, skipping Git configuration.[/yellow]"
        )
        return

    try:
        with open(git_config_path, "r") as f:
            content = f.read()

        # Update user name if provided
        if USER_CONFIG["git_name"]:
            content = re.sub(
                r'userName\s*=\s*"[^"]*"',
                f'userName = "{USER_CONFIG["git_name"]}"',
                content,
            )

        # Update email if provided
        if USER_CONFIG["git_email"]:
            content = re.sub(
                r'userEmail\s*=\s*"[^"]*"',
                f'userEmail = "{USER_CONFIG["git_email"]}"',
                content,
            )

        # Update signing key if provided
        if USER_CONFIG["use_signing_key"] and USER_CONFIG["git_signing_key"]:
            if "signing.key" in content:
                # If signing key already exists, update it
                content = re.sub(
                    r'signing\.key\s*=\s*"[^"]*"',
                    f'signing.key = "{USER_CONFIG["git_signing_key"]}"',
                    content,
                )
            else:
                # If signing key doesn't exist, add it
                signing_config = f'signing.key = "{USER_CONFIG["git_signing_key"]}";\nsigning.signByDefault = true;'
                content = re.sub(
                    r"(extraConfig\s*=\s*{)", f"\\1\n      {signing_config}", content
                )

        with open(git_config_path, "w") as f:
            f.write(content)

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


def command_exists(command):
    """Checks if a command exists."""
    try:
        subprocess.run(
            ["command", "-v", command],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def apply_home_manager():
    """Applies the Home Manager configuration."""
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


@app.command()
def install(
    repo_url: str = typer.Option(REPO_URL, help="The URL of the dotfiles repository."),
    dotfiles_dir: str = typer.Option(
        DOTFILES_DIR, help="The directory to clone the dotfiles into."
    ),
    impure: bool = typer.Option(True, help="Use the --impure flag for home-manager."),
    skip_customization: bool = typer.Option(False, help="Skip the customization step."),
):
    """Installs Nix, Home Manager, and applies the dotfiles configuration."""
    global REPO_URL, DOTFILES_DIR
    REPO_URL = repo_url
    DOTFILES_DIR = dotfiles_dir

    if not command_exists("nix"):
        install_nix()

    if not command_exists("home-manager"):
        install_home_manager()

    clone_dotfiles()

    if not skip_customization:
        customize_dotfiles()

    apply_home_manager()


if __name__ == "__main__":
    app()
