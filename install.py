#!/usr/bin/env uv run

# /// script
# dependencies = [
#   "typer",
#   "rich",
# ]
# ///

import os
import platform
import shlex
import subprocess
import sys

import typer
from rich.console import Console

app = typer.Typer()
console = Console()

DOTFILES_DIR = os.path.expanduser("~/.dotfiles")
REPO_URL = "https://github.com/hadronomy/dotfiles"  # Replace with your repo URL


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


@app.command()
def install(
    repo_url: str = typer.Option(REPO_URL, help="The URL of the dotfiles repository."),
    dotfiles_dir: str = typer.Option(
        DOTFILES_DIR, help="The directory to clone the dotfiles into."
    ),
    impure: bool = typer.Option(True, help="Use the --impure flag for home-manager."),
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
    apply_home_manager()


app()
