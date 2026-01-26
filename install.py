#!/usr/bin/env uv run

# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "typer",
#   "rich",
#   "pygithub",
#   "requests",
#   "psutil",
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
from dataclasses import dataclass, field
from typing import Literal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

app = typer.Typer()

DEFAULT_USER = "hadronomy"
CURRENT_USER = getpass.getuser()


@dataclass
class InstallContext:
    """Context object holding all configuration for the installation process."""

    dry_run: bool = False
    console: Console = field(default_factory=Console)
    dotfiles_dir: str = field(default_factory=lambda: os.path.expanduser("~/.dotfiles"))
    repo_url: str = "https://github.com/hadronomy/dotfiles"
    user_config: dict = field(
        default_factory=lambda: {
            "username": CURRENT_USER,
            "git_name": "",
            "git_email": "",
            "git_signing_key": "",
            "use_signing_key": False,
            "signing_method": "",  # "gpg" or "ssh"
            "onepassword_disable": True,  # Default to disabling 1Password
        }
    )


def run_command(
    command, check=True, shell=False, dry_run=False, env=None, console=None
):
    """Runs a shell command and streams the output in real-time with rich
    formatting."""
    if console is None:
        console = Console()

    if not shell:
        cmd_str = " ".join(shlex.quote(arg) for arg in command)
    else:
        cmd_str = command

    if dry_run:
        console.print(
            "[bold yellow][DRY RUN][/bold yellow] [bold blue]Would "
            f"run:[/bold blue] {cmd_str}"
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
            env=env,
        )

        while True:
            stdout_line = process.stdout.readline() if process.stdout else ""
            stderr_line = process.stderr.readline() if process.stderr else ""

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
            raise
        return None
    except FileNotFoundError as e:
        console.print(f"[bold red]Command not found: {e}[/bold red]")
        if not dry_run:
            raise
        return None


def install_nix(ctx: InstallContext):
    """Installs Nix package manager."""
    if ctx.dry_run:
        ctx.console.print(
            "[bold yellow][DRY RUN][/bold yellow] Would install Nix package manager"
        )
        return

    ctx.console.print("[bold]Nix not found. Installing...[/bold]")
    system = platform.system()

    if system == "Linux":
        try:
            temp_dir = os.path.expanduser("~/.dotfiles/tmp")
            os.makedirs(temp_dir, exist_ok=True)
            install_script_path = os.path.join(temp_dir, "nix_install.sh")

            ctx.console.print("[yellow]Downloading Nix installer...[/yellow]")
            try:
                run_command(
                    [
                        "curl",
                        "-L",
                        "-o",
                        install_script_path,
                        "https://nixos.org/nix/install",
                    ],
                    check=True,
                    console=ctx.console,
                )
            except Exception as curl_error:
                ctx.console.print(
                    f"[yellow]Curl failed: {curl_error}, trying wget...[/yellow]"
                )
                try:
                    run_command(
                        [
                            "wget",
                            "-O",
                            install_script_path,
                            "https://nixos.org/nix/install",
                        ],
                        check=True,
                        console=ctx.console,
                    )
                except Exception as wget_error:
                    ctx.console.print(
                        f"[yellow]Wget failed: {wget_error}, using Python...[/yellow]"
                    )
                    import urllib.request

                    urllib.request.urlretrieve(
                        "https://nixos.org/nix/install", install_script_path
                    )

            os.chmod(install_script_path, 0o755)

            ctx.console.print("[yellow]Running Nix installer...[/yellow]")
            try:
                run_command([install_script_path], check=True, console=ctx.console)
            except Exception as no_sudo_error:
                ctx.console.print(
                    "[yellow]Installation failed without sudo: "
                    f"{no_sudo_error}, trying with sudo...[/yellow]"
                )
                try:
                    run_command(
                        ["sudo", install_script_path], check=True, console=ctx.console
                    )
                except Exception as sudo_error:
                    ctx.console.print(
                        "[yellow]Sudo installation failed: "
                        f"{sudo_error}, Nix installation "
                        "unsuccessful.[/yellow]"
                    )
                    cleanup(1)

            ctx.console.print("[bold]Activating Nix environment...[/bold]")
            source_nix_profile()

            configure_nix_experimental_features()

            try:
                os.remove(install_script_path)
            except Exception:
                pass

            if verify_nix_installation():
                ctx.console.print(
                    "[green]Nix successfully installed and activated![/green]"
                )
            else:
                ctx.console.print(
                    "[yellow]Nix installed but not fully activated in "
                    "current process.[/yellow]"
                )
                ctx.console.print(
                    "[yellow]Attempting to reload environment and continue...[/yellow]"
                )
                force_reload_nix_env()

        except Exception as e:
            error_msg = (
                str(e).replace(chr(92), chr(92) * 2).replace("[", "").replace("]", "")
            )
            ctx.console.print(f"[bold red]Error installing Nix: {error_msg}[/bold red]")
            cleanup(1)

    elif system == "Darwin":
        ctx.console.print(
            "[bold yellow]Installing Nix on macOS requires manual "
            "steps. Please see https://nixos.org/download.html[/bold "
            "yellow]"
        )
        cleanup(1)
    else:
        ctx.console.print(
            "[bold red]Unsupported operating system for automatic Nix "
            "installation.[/bold red]"
        )
        cleanup(1)

    ctx.console.print(
        "[green]Nix installation complete. You may need to open a new terminal.[/green]"
    )


def source_nix_profile():
    """Source Nix profile and update environment variables in the current
    process."""
    possible_nix_profiles = [
        os.path.expanduser("~/.nix-profile/etc/profile.d/nix.sh"),
        "/etc/profile.d/nix.sh",
        "/nix/var/nix/profiles/default/etc/profile.d/nix.sh",
        "/root/.nix-profile/etc/profile.d/nix.sh",
    ]

    nix_profile_path = None
    for profile in possible_nix_profiles:
        if os.path.exists(profile):
            nix_profile_path = profile
            console.print(f"[green]Found Nix profile at {profile}[/green]")
            break

    if nix_profile_path:
        console.print(f"[yellow]Sourcing {nix_profile_path}...[/yellow]")
        source_env = f"source {nix_profile_path} && env"
        try:
            proc = subprocess.Popen(
                source_env,
                stdout=subprocess.PIPE,
                shell=True,
                executable="/bin/bash",
            )

            for line in proc.stdout or []:
                line = line.decode().strip()
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value

            if "PATH" in os.environ:
                console.print(f"[dim]Updated PATH: {os.environ['PATH']}[/dim]")

            os.environ["NIXPKGS_ALLOW_UNFREE"] = "1"
            os.environ["NIXPKGS_ALLOW_INSECURE"] = "1"

            return verify_nix_installation()

        except Exception as e:
            console.print(f"[yellow]Error sourcing Nix profile: {e}[/yellow]")
            return False
    else:
        console.print("[yellow]Could not find Nix profile to source.[/yellow]")
        for nix_bin in [
            "~/.nix-profile/bin",
            "/nix/var/nix/profiles/default/bin",
        ]:
            expanded_path = os.path.expanduser(nix_bin)
            if os.path.exists(expanded_path):
                os.environ["PATH"] = f"{expanded_path}:{os.environ['PATH']}"
                console.print(f"[green]Added {expanded_path} to PATH[/green]")

        return False


def force_reload_nix_env():
    """Aggressively try to reload Nix environment when normal sourcing
    doesn't work."""
    console.print("[yellow]Performing aggressive Nix environment reload...[/yellow]")

    nix_bin_paths = [
        "~/.nix-profile/bin",
        "/nix/var/nix/profiles/default/bin",
        "/run/current-system/sw/bin",
    ]

    for path in nix_bin_paths:
        expanded_path = os.path.expanduser(path)
        if os.path.exists(expanded_path):
            os.environ["PATH"] = f"{expanded_path}:{os.environ['PATH']}"
            console.print(f"[dim]Added {expanded_path} to PATH[/dim]")

    os.environ["NIX_PATH"] = (
        f"nixpkgs={os.path.expanduser('~/.nix-defexpr/channels/nixpkgs')}"
    )
    os.environ["NIX_SSL_CERT_FILE"] = "/etc/ssl/certs/ca-certificates.crt"

    try:
        subprocess.run(["nix", "--version"], check=True, capture_output=True, text=True)
        console.print("[green]Nix command is now available![/green]")
        return True
    except Exception:
        console.print("[red]Failed to activate Nix in current process.[/red]")
        console.print(
            "[yellow]You may need to run these commands manually in a "
            "new terminal:[/yellow]"
        )
        console.print("  source ~/.nix-profile/etc/profile.d/nix.sh")
        console.print("  nix-channel --update")
        return False


def verify_nix_installation():
    """Verify that Nix is properly installed and available."""
    try:
        result = subprocess.run(
            ["nix", "--version"], check=False, capture_output=True, text=True
        )

        if result.returncode == 0:
            console.print(f"[green]Nix verified: {result.stdout.strip()}[/green]")
            return True
        else:
            console.print("[yellow]Nix command found but returned error.[/yellow]")
            return False
    except Exception:
        console.print("[yellow]Could not verify Nix installation.[/yellow]")
        return False


def configure_nix_experimental_features():
    """Configure experimental features in nix.conf."""
    try:
        nix_conf_dir = os.path.expanduser("~/.config/nix")
        nix_conf_file = os.path.join(nix_conf_dir, "nix.conf")

        if not os.path.exists(nix_conf_dir):
            try:
                os.makedirs(nix_conf_dir, exist_ok=True)
            except Exception:
                nix_conf_dir = "/etc/nix"
                nix_conf_file = os.path.join(nix_conf_dir, "nix.conf")

        if not os.path.exists(nix_conf_dir):
            try:
                os.makedirs(nix_conf_dir, exist_ok=True)
            except Exception as e:
                console.print(f"[yellow]Could not create {nix_conf_dir}: {e}[/yellow]")
                nix_conf_dir = os.path.expanduser("~/.dotfiles/nix")
                os.makedirs(nix_conf_dir, exist_ok=True)
                nix_conf_file = os.path.join(nix_conf_dir, "nix.conf")
                console.print(
                    f"[yellow]Using fallback configuration at {nix_conf_file}[/yellow]"
                )

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
                os.environ["NIX_CONFIG"] = "experimental-features = nix-command flakes"
                console.print(
                    "[yellow]Set NIX_CONFIG environment variable as fallback.[/yellow]"
                )
                shell_rc_file = os.path.expanduser("~/.bashrc")
                if os.path.exists(os.path.expanduser("~/.zshrc")):
                    shell_rc_file = os.path.expanduser("~/.zshrc")

                try:
                    with open(shell_rc_file, "a") as f:
                        f.write(
                            "\n# Added by dotfiles installer\nexport "
                            'NIX_CONFIG="experimental-features = '
                            'nix-command flakes"\n'
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


def install_home_manager_standalone(ctx: InstallContext):
    """Install Home Manager directly using nix-env to avoid permission
    issues."""
    if ctx.dry_run:
        ctx.console.print(
            "[bold yellow][DRY RUN][/bold yellow] Would install Home Manager directly"
        )
        return True

    ctx.console.print("[bold]Installing Home Manager using standalone method...[/bold]")

    try:
        ctx.console.print("[yellow]Trying nix-env direct installation...[/yellow]")
        run_command(["nix-env", "-iA", "nixpkgs.home-manager"], check=True, console=ctx.console)
        ctx.console.print(
            "[green]Home Manager installed successfully using nix-env![/green]"
        )
        return True
    except Exception as e:
        ctx.console.print(f"[yellow]nix-env installation failed: {e}[/yellow]")

    try:
        ctx.console.print("[yellow]Trying flake-based installation...[/yellow]")
        run_command(
            ["nix", "profile", "install", "github:nix-community/home-manager"],
            check=True,
        )
        ctx.console.print(
            "[green]Home Manager installed successfully using flakes![/green]"
        )

        try:
            shell_rc = None
            if os.path.exists(os.path.expanduser("~/.zshrc")):
                shell_rc = os.path.expanduser("~/.zshrc")
            elif os.path.exists(os.path.expanduser("~/.bashrc")):
                shell_rc = os.path.expanduser("~/.bashrc")

            if shell_rc:
                with open(shell_rc, "a") as f:
                    f.write(
                        "\n# Added by dotfiles installer\nexport "
                        "NIX_PATH=$HOME/.nix-defexpr/channels:/nix/var/"
                        "nix/profiles/per-user/root/channels"
                        "${NIX_PATH:+:$NIX_PATH}\n"
                    )
                ctx.console.print(f"[green]Added NIX_PATH to {shell_rc}[/green]")
        except Exception as e:
            ctx.console.print(f"[yellow]Could not update shell configuration: {e}[/yellow]")

        return True
    except Exception as e:
        ctx.console.print(f"[yellow]Flake-based installation failed: {e}[/yellow]")

    try:
        ctx.console.print("[yellow]Trying direct installation from GitHub...[/yellow]")
        tmp_dir = os.path.expanduser("~/.dotfiles/tmp")
        os.makedirs(tmp_dir, exist_ok=True)

        repo_path = os.path.join(tmp_dir, "home-manager")
        if os.path.exists(repo_path):
            ctx.console.print(
                "[yellow]Removing existing home-manager directory...[/yellow]"
            )
            import shutil

            shutil.rmtree(repo_path)

        run_command(
            [
                "git",
                "clone",
                "https://github.com/nix-community/home-manager.git",
                repo_path,
            ],
            check=True,
        )

        run_command(["nix-shell", "-A", "install", repo_path], check=True, console=ctx.console)
        ctx.console.print("[green]Home Manager installed successfully from GitHub![/green]")
        return True
    except Exception as e:
        ctx.console.print(f"[yellow]Direct GitHub installation failed: {e}[/yellow]")

    return False


def install_home_manager(ctx: InstallContext):
    """Installs Home Manager."""
    if ctx.dry_run:
        ctx.console.print("[bold yellow][DRY RUN][/bold yellow] Would install Home Manager")
        return

    ctx.console.print("[bold]Installing Home Manager...[/bold]")

    if install_home_manager_standalone(ctx.dry_run):
        ctx.console.print(
            "[green]Home Manager installation completed successfully.[/green]"
        )
        return

    try:
        nix_channel_path = None
        for path in os.environ.get("PATH", "").split(":"):
            if os.path.exists(os.path.join(path, "nix-channel")):
                nix_channel_path = os.path.join(path, "nix-channel")
                break

        try:
            if os.path.exists("/nix/var/nix/db/big-lock") and not os.access(
                "/nix/var/nix/db/big-lock", os.W_OK
            ):
                ctx.console.print(
                    "[yellow]Detected permission issues with Nix lock files.[/yellow]"
                )
                ctx.console.print(
                    "[yellow]Trying single-user approach with separate "
                    "commands...[/yellow]"
                )

                env = os.environ.copy()
                env["NIX_USER_CHANNEL_ROOT"] = os.path.expanduser("~/.nix-channels")

                ctx.console.print("[yellow]Adding nixpkgs channel...[/yellow]")
                result = subprocess.run(
                    [
                        nix_channel_path,
                        "--add",
                        "https://nixos.org/channels/nixpkgs-unstable",
                        "nixpkgs",
                    ],
                    env=env,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    ctx.console.print(
                        f"[red]Failed to add nixpkgs channel: {result.stderr}[/red]"
                    )
                    raise Exception("Failed to add nixpkgs channel")

                ctx.console.print("[yellow]Adding home-manager channel...[/yellow]")
                result = subprocess.run(
                    [
                        nix_channel_path,
                        "--add",
                        "https://github.com/nix-community/"
                        "home-manager/archive/master.tar.gz",
                        "home-manager",
                    ],
                    env=env,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    ctx.console.print(
                        "[red]Failed to add home-manager channel: "
                        f"{result.stderr}[/red]"
                    )
                    raise Exception("Failed to add home-manager channel")

                ctx.console.print("[yellow]Updating channels...[/yellow]")
                result = subprocess.run(
                    [nix_channel_path, "--update"],
                    env=env,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    ctx.console.print(
                        f"[red]Failed to update channels: {result.stderr}[/red]"
                    )
                    raise Exception("Failed to update channels")
            else:
                result = subprocess.run(
                    [
                        nix_channel_path,
                        "--add",
                        "https://nixos.org/channels/nixpkgs-unstable",
                        "nixpkgs",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    ctx.console.print(
                        f"[red]Failed to add nixpkgs channel: {result.stderr}[/red]"
                    )

                result = subprocess.run(
                    [
                        nix_channel_path,
                        "--add",
                        "https://github.com/nix-community/"
                        "home-manager/archive/master.tar.gz",
                        "home-manager",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    ctx.console.print(
                        "[red]Failed to add home-manager channel: "
                        f"{result.stderr}[/red]"
                    )

                result = subprocess.run(
                    [nix_channel_path, "--update"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    ctx.console.print(
                        f"[red]Failed to update channels: {result.stderr}[/red]"
                    )

                    if "Permission denied" in result.stderr:
                        ctx.console.print(
                            "[yellow]Permission denied, trying with sudo...[/yellow]"
                        )
                        try:
                            sudo_result = subprocess.run(
                                ["sudo", nix_channel_path, "--update"],
                                check=False,
                                capture_output=True,
                                text=True,
                            )
                            if sudo_result.returncode != 0:
                                ctx.console.print(
                                    "[red]Sudo update failed: "
                                    f"{sudo_result.stderr}[/red]"
                                )
                                raise Exception("Failed to update channels with sudo")
                        except Exception:
                            ctx.console.print(
                                "[yellow]Channel update failed, falling "
                                "back to standalone installation..."
                                "[/yellow]"
                            )
                            if install_home_manager_standalone(ctx.dry_run):
                                return
                            raise Exception(
                                "All home manager installation methods failed"
                            )

        except Exception as e:
            if "Permission denied" in str(e):
                ctx.console.print(
                    "[yellow]Permission denied when updating channels.[/yellow]"
                )
                if install_home_manager_standalone(ctx.dry_run):
                    return
            raise Exception(f"Home Manager installation failed: {e}")

        nix_shell_cmd = "nix-shell"
        for path in os.environ.get("PATH", "").split(":"):
            if os.path.exists(os.path.join(path, "nix-shell")):
                nix_shell_cmd = os.path.join(path, "nix-shell")
                break

        try:
            ctx.console.print("[yellow]Running home-manager installation...[/yellow]")
            result = subprocess.run(
                [nix_shell_cmd, "<home-manager>", "-A", "install"],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                ctx.console.print(
                    f"[red]Home Manager installation failed: {result.stderr}[/red]"
                )
                raise Exception("Home Manager installation failed")

            ctx.console.print("[green]Home Manager installed successfully![/green]")
        except Exception as e:
            ctx.console.print(f"[yellow]Error during installation: {e}[/yellow]")
            ctx.console.print("[yellow]Trying direct installation...[/yellow]")

            if install_home_manager_standalone(ctx.dry_run):
                return

            raise Exception("All Home Manager installation methods failed")

    except Exception as e:
        ctx.console.print(f"[bold red]Error installing Home Manager: {e}[/bold red]")
        ctx.console.print(
            "[yellow]Please try installing Home Manager manually using one "
            "of these methods:[/yellow]"
        )
        ctx.console.print("\n[bold]Method 1: nix-env[/bold]")
        ctx.console.print("Run: nix-env -iA nixpkgs.home-manager")

        ctx.console.print("\n[bold]Method 2: Flakes[/bold]")
        ctx.console.print("Run: nix profile install github:nix-community/home-manager")
        ctx.console.print("Then add to your shell config file:")
        ctx.console.print(
            "export NIX_PATH=$HOME/.nix-defexpr/channels:/nix/var/nix/"
            "profiles/per-user/root/channels${NIX_PATH:+:$NIX_PATH}"
        )

        ctx.console.print("\n[bold]Method 3: Channels[/bold]")
        ctx.console.print(
            "1. nix-channel --add https://nixos.org/channels/nixpkgs-unstable nixpkgs"
        )
        ctx.console.print(
            "2. nix-channel --add https://github.com/nix-community/"
            "home-manager/archive/master.tar.gz home-manager"
        )
        ctx.console.print("3. nix-channel --update")
        ctx.console.print("4. nix-shell '<home-manager>' -A install")
        sys.exit(1)


def clone_dotfiles(ctx: InstallContext):
    """Clones the dotfiles repository."""
    if ctx.dry_run:
        ctx.console.print(
            "[bold yellow][DRY RUN][/bold yellow] Would clone "
            f"{ctx.repo_url} to {ctx.dotfiles_dir}"
        )
        return

    if not os.path.exists(ctx.dotfiles_dir):
        ctx.console.print("[bold]Cloning dotfiles repository...[/bold]")
        os.makedirs(os.path.dirname(ctx.dotfiles_dir), exist_ok=True)
        try:
            run_command(["git", "clone", "--depth", "1", ctx.repo_url, ctx.dotfiles_dir], console=ctx.console)
        except Exception as e:
            ctx.console.print(f"[bold red]Error cloning dotfiles: {e}[/bold red]")
            sys.exit(1)
    else:
        ctx.console.print("[bold]Dotfiles repository already exists.[/bold]")


def customize_dotfiles(ctx: InstallContext, force_customize=False):
    """Customize dotfiles for the current user if not the default user."""
    if CURRENT_USER == DEFAULT_USER and not force_customize:
        ctx.console.print(
            "[green]Running as the default user, no customization needed.[/green]"
        )
        return

    if not force_customize:
        ctx.console.print(
            "[bold yellow]Running as a non-default user, customization "
            "recommended.[/bold yellow]"
        )
    else:
        ctx.console.print(
            "[bold yellow]Customization forced by command line flag.[/bold yellow]"
        )

    if force_customize or Confirm.ask(
        "Would you like to customize the dotfiles for your user?", default=True
    ):
        collect_user_info(ctx)
        replace_username_in_files(ctx)
        update_git_config(ctx)

        if ctx.dry_run:
            ctx.console.print(
                "[bold yellow][DRY RUN][/bold yellow] Customization would "
                "be applied with these settings"
            )
        else:
            ctx.console.print("[green]Customization complete![/green]")


def collect_user_info(ctx: InstallContext):
    """Collect user information for customization."""
    ctx.console.print("[bold]Collecting user information for customization...[/bold]")
    ctx.console.print("")

    ctx.user_config["username"] = Prompt.ask("Username", default=CURRENT_USER)
    ctx.user_config["git_name"] = Prompt.ask("Your full name (for Git config)", default="")
    ctx.user_config["git_email"] = Prompt.ask("Your email (for Git config)", default="")

    ctx.user_config["onepassword_disable"] = Confirm.ask(
        "Do you want to disable 1Password integration?", default=True
    )

    use_signing_key = Confirm.ask("Would you like to use commit signing?", default=True)
    ctx.user_config["use_signing_key"] = use_signing_key

    if use_signing_key:
        signing_methods = {"1": "GPG", "2": "SSH"}
        ctx.console.print(
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
        ctx.user_config["signing_method"] = signing_method.lower()

        if signing_method == "GPG":
            gpg_key_options(ctx)
        else:
            ssh_key_options(ctx)


def gpg_key_options(ctx: InstallContext):
    """Handle GPG key options for Git commit signing."""
    existing_gpg_keys = list_gpg_keys(ctx)

    if existing_gpg_keys:
        ctx.console.print("[green]Found existing GPG keys:[/green]")

        table = Table(show_header=True)
        table.add_column("#", justify="right", style="cyan", no_wrap=True)
        table.add_column("Key ID", style="magenta")
        table.add_column("User Info", style="green")

        for idx, (key_id, user_info) in enumerate(existing_gpg_keys, 1):
            table.add_row(str(idx), key_id, user_info)

        ctx.console.print(table)

        if Confirm.ask("Would you like to use an existing key?", default=True):
            choices = [str(i) for i in range(1, len(existing_gpg_keys) + 1)]

            choice_str = Prompt.ask(
                "Enter the number of the key to use", default="1", choices=choices
            )
            choice = int(choice_str)
            ctx.user_config["git_signing_key"] = existing_gpg_keys[choice - 1][0]
            ctx.console.print(
                f"[green]Using GPG key: {ctx.user_config['git_signing_key']}[/green]"
            )

            if Confirm.ask(
                "Would you like to add this key to your GitHub account?",
                default=False,
            ):
                add_key_to_github(ctx, "gpg", ctx.user_config["git_signing_key"])

            return

    if Confirm.ask("Would you like to create a new GPG key?", default=True):
        ctx.console.print("[bold]Creating new GPG key...[/bold]")
        key_id = create_gpg_key(ctx, ctx.user_config["git_name"], ctx.user_config["git_email"])

        if key_id:
            ctx.user_config["git_signing_key"] = key_id
            ctx.console.print(f"[green]Created GPG key: {key_id}[/green]")

            if Confirm.ask(
                "Would you like to add this key to your GitHub account?",
                default=True,
            ):
                add_key_to_github(ctx, "gpg", key_id)
        else:
            ctx.console.print("[yellow]GPG key creation failed or was cancelled.[/yellow]")
            ctx.user_config["git_signing_key"] = Prompt.ask(
                "Enter your GPG key ID manually", default=""
            )
    else:
        ctx.user_config["git_signing_key"] = Prompt.ask(
            "Enter your GPG key ID manually", default=""
        )


def ssh_key_options(ctx: InstallContext):
    """Handle SSH key options for Git commit signing."""
    existing_ssh_keys = list_ssh_keys(ctx)

    if existing_ssh_keys:
        ctx.console.print("[green]Found existing SSH keys:[/green]")

        table = Table(show_header=True)
        table.add_column("#", justify="right", style="cyan", no_wrap=True)
        table.add_column("Key Path", style="magenta")

        for idx, key_path in enumerate(existing_ssh_keys, 1):
            table.add_row(str(idx), key_path)

        ctx.console.print(table)

        if Confirm.ask("Would you like to use an existing key?", default=True):
            choices = [str(i) for i in range(1, len(existing_ssh_keys) + 1)]

            choice_str = Prompt.ask(
                "Enter the number of the key to use", default="1", choices=choices
            )
            choice = int(choice_str)
            ctx.user_config["git_signing_key"] = existing_ssh_keys[choice - 1]
            ctx.console.print(
                f"[green]Using SSH key: {ctx.user_config['git_signing_key']}[/green]"
            )

            if Confirm.ask(
                "Would you like to add this key to your GitHub account for signing?",
                default=False,
            ):
                add_key_to_github(ctx, "ssh-signing", ctx.user_config["git_signing_key"])

            return

    if Confirm.ask("Would you like to create a new SSH key for signing?", default=True):
        ctx.console.print("[bold]Creating new SSH key...[/bold]")
        key_path = create_ssh_key(ctx, ctx.user_config["git_email"])

        if key_path:
            ctx.user_config["git_signing_key"] = key_path
            ctx.console.print(f"[green]Created SSH key: {key_path}[/green]")

            if Confirm.ask(
                "Would you like to add this key to your GitHub account?",
                default=True,
            ):
                add_key_to_github(ctx, "ssh-signing", key_path)
        else:
            ctx.console.print("[yellow]SSH key creation failed or was cancelled.[/yellow]")
            ctx.user_config["git_signing_key"] = Prompt.ask(
                "Enter your SSH key path manually", default="~/.ssh/id_ed25519"
            )
    else:
        ctx.user_config["git_signing_key"] = Prompt.ask(
            "Enter your SSH key path manually", default="~/.ssh/id_ed25519"
        )


def list_gpg_keys(ctx: InstallContext):
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
                parts = line.split("/")
                if len(parts) >= 2:
                    key_id = parts[1].split(" ")[0]
            elif "uid" in line and key_id:
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
        ctx.console.print(f"[yellow]Error listing GPG keys: {e}[/yellow]")
        return []


def create_gpg_key(ctx: InstallContext, name, email):
    """Create a new GPG key."""
    try:
        batch_file = os.path.expanduser("~/.gnupg/batch")
        os.makedirs(os.path.dirname(batch_file), exist_ok=True)

        with open(batch_file, "w") as f:
            f.write(
                (
                    "Key-Type: RSA\n"
                    "Key-Length: 4096\n"
                    f"Name-Real: {name}\n"
                    f"Name-Email: {email}\n"
                    "Expire-Date: 0\n"
                    "%no-protection\n"
                    "%commit\n"
                )
            )

        ctx.console.print("[yellow]Generating GPG key... this may take a moment.[/yellow]")
        result = subprocess.run(
            ["gpg", "--batch", "--generate-key", batch_file],
            capture_output=True,
            text=True,
            check=False,
        )

        try:
            os.remove(batch_file)
        except Exception:
            pass

        if result.returncode != 0:
            ctx.console.print(f"[red]GPG key generation failed:[/red]\n{result.stderr}")
            return None

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
        ctx.console.print(f"[red]Error creating GPG key: {e}[/red]")
        return None


def list_ssh_keys(ctx: InstallContext):
    """List existing SSH keys."""
    ssh_dir = os.path.expanduser("~/.ssh")
    if not os.path.exists(ssh_dir):
        return []

    keys = []
    for file in os.listdir(ssh_dir):
        if file.endswith(".pub") and not file.startswith("known_hosts"):
            private_key = os.path.join(ssh_dir, file[:-4])
            if os.path.exists(private_key):
                keys.append(private_key)

    return keys


def create_ssh_key(ctx: InstallContext, email):
    """Create a new SSH key."""
    try:
        key_path = os.path.expanduser("~/.ssh/id_signing_ed25519")

        os.makedirs(os.path.dirname(key_path), exist_ok=True)

        ctx.console.print("[yellow]Generating SSH key...[/yellow]")
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
                "",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            ctx.console.print(f"[red]SSH key generation failed:[/red]\n{result.stderr}")
            return None

        return key_path
    except Exception as e:
        ctx.console.print(f"[red]Error creating SSH key: {e}[/red]")
        return None


def add_key_to_github(ctx: InstallContext, key_type: Literal["gpg", "ssh", "ssh-signing"], key_path_or_id):
    """Add a key to GitHub."""
    try:
        if command_exists("gh"):
            if key_type == "gpg":
                export_result = subprocess.run(
                    ["gpg", "--armor", "--export", key_path_or_id],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if export_result.returncode != 0:
                    ctx.console.print("[red]Failed to export GPG key.[/red]")
                    return False

                gpg_key = export_result.stdout

                tmp_file = os.path.expanduser("~/gpg_key.asc")
                with open(tmp_file, "w") as f:
                    f.write(gpg_key)

                ctx.console.print("[yellow]Adding GPG key to GitHub...[/yellow]")
                gh_result = subprocess.run(
                    ["gh", "gpg-key", "add", tmp_file],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                try:
                    os.remove(tmp_file)
                except Exception:
                    pass

                if gh_result.returncode != 0:
                    ctx.console.print(
                        "[red]Failed to add GPG key to GitHub:[/red]\n"
                        f"{gh_result.stderr}"
                    )
                    return False

                ctx.console.print("[green]GPG key added to GitHub successfully![/green]")
                return True

            elif key_type in ("ssh", "ssh-signing"):
                pub_key_path = f"{key_path_or_id}.pub"
                if not os.path.exists(pub_key_path):
                    ctx.console.print(
                        f"[red]SSH public key not found: {pub_key_path}[/red]"
                    )
                    return False

                with open(pub_key_path, "r") as f:
                    ssh_key = f.read().strip()

                title = (
                    f"{platform.node()}-signing-key"
                    if key_type == "ssh-signing"
                    else f"{platform.node()}-key"
                )

                ctx.console.print(
                    f"[yellow]Adding SSH key to GitHub as {key_type}...[/yellow]"
                )

                if key_type == "ssh-signing":
                    auth_status = subprocess.run(
                        ["gh", "auth", "status"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    if "admin:ssh_signing_key" not in auth_status.stdout:
                        ctx.console.print(
                            "[yellow]The GitHub CLI needs additional "
                            "permissions for SSH signing keys.[/yellow]"
                        )
                        ctx.console.print(
                            "[yellow]Running: gh auth refresh -h "
                            "github.com -s admin:ssh_signing_key[/yellow]"
                        )
                        ctx.console.print(
                            "[bold]Follow the instructions in the "
                            "browser to authorize the additional scopes:"
                            "[/bold]"
                        )

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
                            ctx.console.print(
                                "[red]Failed to update GitHub CLI "
                                "permissions (exit code: "
                                f"{refresh_result})[/red]"
                            )
                            ctx.console.print(
                                "[yellow]You may need to manually add "
                                "your SSH signing key to GitHub.[/yellow]"
                            )
                            return False

                        ctx.console.print(
                            "[green]Successfully updated GitHub CLI "
                            "permissions.[/green]"
                        )

                cmd = ["gh", "ssh-key", "add", pub_key_path, "--title", title]
                if key_type == "ssh-signing":
                    cmd += ["--type", "signing"]

                gh_result = subprocess.run(
                    cmd, capture_output=True, text=True, check=False
                )

                if gh_result.returncode != 0:
                    ctx.console.print(
                        "[red]Failed to add SSH key to GitHub:[/red]\n"
                        f"{gh_result.stderr}"
                    )
                    return False

                ctx.console.print("[green]SSH key added to GitHub successfully![/green]")
                return True
        else:
            ctx.console.print(
                "[yellow]GitHub CLI (gh) not found. Using web "
                "authentication flow instead.[/yellow]"
            )

            if Confirm.ask(
                "Would you like to authenticate with GitHub to add your key?",
                default=True,
            ):
                try:
                    import json
                    import time
                    import webbrowser

                    import requests

                    client_id = "Iv1.5da81c42435d41c5"
                    scope = "admin:public_key admin:gpg_key admin:ssh_signing_key"

                    device_code_url = "https://github.com/login/device/code"
                    device_response = requests.post(
                        device_code_url,
                        headers={"Accept": "application/json"},
                        data={"client_id": client_id, "scope": scope},
                    )

                    if device_response.status_code != 200:
                        ctx.console.print(
                            "[red]Failed to start GitHub authentication.[/red]"
                        )
                        return False

                    device_data = device_response.json()
                    device_code = device_data["device_code"]
                    user_code = device_data["user_code"]
                    verification_uri = device_data["verification_uri"]
                    expires_in = device_data["expires_in"]
                    interval = device_data["interval"]

                    ctx.console.print(
                        Panel.fit(
                            "\n[bold green]GitHub Authentication "
                            "Required[/bold green]\n\n"
                            f"1. Go to: [bold blue]{verification_uri}"
                            "[/bold blue]\n"
                            "2. Enter code: "
                            f"[bold yellow]{user_code}[/bold yellow]\n"
                            "3. Authorize this application\n",
                            title="GitHub Device Flow",
                        )
                    )

                    try:
                        webbrowser.open(verification_uri)
                    except Exception:
                        pass

                    token_url = "https://github.com/login/oauth/access_token"
                    start_time = time.time()
                    access_token = None

                    with ctx.console.status(
                        "[bold green]Waiting for GitHub authorization...[/bold green]"
                    ):
                        while time.time() - start_time < expires_in:
                            token_response = requests.post(
                                token_url,
                                headers={"Accept": "application/json"},
                                data={
                                    "client_id": client_id,
                                    "device_code": device_code,
                                    "grant_type": (
                                        "urn:ietf:params:oauth:grant-type:device_code"
                                    ),
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
                                    ctx.console.print(
                                        f"[red]Error: {token_data['error']}[/red]"
                                    )
                                    return False

                            time.sleep(interval)

                    if not access_token:
                        ctx.console.print("[red]GitHub authorization timed out.[/red]")
                        return False

                    from github import Github, GithubException

                    g = Github(access_token)
                    user = g.get_user()

                    if key_type == "gpg":
                        export_result = subprocess.run(
                            ["gpg", "--armor", "--export", key_path_or_id],
                            capture_output=True,
                            text=True,
                            check=False,
                        )

                        if export_result.returncode != 0:
                            ctx.console.print("[red]Failed to export GPG key.[/red]")
                            return False

                        gpg_key = export_result.stdout
                        user.create_gpg_key(ctx, gpg_key)
                        ctx.console.print(
                            "[green]GPG key added to GitHub successfully![/green]"
                        )

                    elif key_type in ("ssh", "ssh-signing"):
                        pub_key_path = f"{key_path_or_id}.pub"
                        if not os.path.exists(pub_key_path):
                            ctx.console.print(
                                f"[red]SSH public key not found: {pub_key_path}[/red]"
                            )
                            return False

                        with open(pub_key_path, "r") as f:
                            ssh_key = f.read().strip()

                        key_suffix = "signing-" if key_type == "ssh-signing" else ""
                        title = f"{platform.node()}-{key_suffix}key"

                        if key_type == "ssh-signing":
                            headers = {
                                "Accept": "application/vnd.github+json",
                                "Authorization": f"Bearer {access_token}",
                                "X-GitHub-Api-Version": "2022-11-28",
                            }

                            data = {"title": title, "key": ssh_key}

                            response = requests.post(
                                "https://api.github.com/user/ssh_signing_keys",
                                headers=headers,
                                data=json.dumps(data),
                            )

                            if response.status_code == 201:
                                ctx.console.print(
                                    "[green]SSH signing key added to "
                                    "GitHub successfully![/green]"
                                )
                                return True
                            else:
                                error_message = response.json().get(
                                    "message", "Unknown error"
                                )
                                ctx.console.print(
                                    f"[red]Failed to add SSH signing key: {error_message}[/red]"
                                )
                                return False
                        else:
                            user.create_key(title=title, key=ssh_key)
                            ctx.console.print(
                                "[green]SSH key added to GitHub successfully![/green]"
                            )

                    return True

                except ImportError as e:
                    ctx.console.print(f"[red]Failed to import necessary modules: {e}[/red]")
                except requests.RequestException as e:
                    ctx.console.print(f"[red]Network error: {e}[/red]")
                except GithubException as e:
                    ctx.console.print(f"[red]GitHub API error: {e}[/red]")
                except Exception as e:
                    ctx.console.print(f"[red]Error adding key to GitHub: {e}[/red]")

            ctx.console.print(
                "[yellow]You can add your keys manually at "
                "https://github.com/settings/keys[/yellow]"
            )
        return False
    except Exception as e:
        ctx.console.print(f"[red]Error adding key to GitHub: {e}[/red]")
        return False


def replace_username_in_files(ctx: InstallContext):
    """Replace instances of the default username with the current user's
    username."""
    action_text = (
        "[bold yellow][DRY RUN][/bold yellow] Would replace" if ctx.dry_run else "Replacing"
    )
    ctx.console.print(
        f"[bold]{action_text} '{DEFAULT_USER}' with '{ctx.user_config['username']}' in dotfiles...[/bold]"
    )

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

    for root, dirs, files in os.walk(ctx.dotfiles_dir):
        dirs[:] = [d for d in dirs if d not in excluded_dirs]

        for file in files:
            if any(file.endswith(ext) for ext in excluded_exts):
                continue

            file_path = os.path.join(root, file)

            try:
                if is_binary(file_path):
                    continue

                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                if DEFAULT_USER in content:
                    if not ctx.dry_run:
                        modified_content = content.replace(
                            DEFAULT_USER, ctx.user_config["username"]
                        )
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(modified_content)

                    update_text = (
                        "[bold yellow][DRY RUN][/bold yellow] Would update"
                        if ctx.dry_run
                        else "Updated"
                    )
                    ctx.console.print(f"  {update_text}: {file_path}")
            except Exception as e:
                ctx.console.print(
                    f"[yellow]Warning: Could not process {file_path}: {e}[/yellow]"
                )


def update_git_config(ctx: InstallContext):
    """Update Git configuration with user information."""
    if (
        not ctx.user_config["git_name"]
        and not ctx.user_config["git_email"]
        and not ctx.user_config["use_signing_key"]
    ):
        return

    updating_text = (
        "[bold yellow][DRY RUN][/bold yellow] Updating" if ctx.dry_run else "Updating"
    )
    ctx.console.print(f"[bold]{updating_text} Git configuration...[/bold]")

    git_config_path = os.path.join(ctx.dotfiles_dir, "home", "git", "default.nix")
    if not os.path.exists(git_config_path):
        ctx.console.print(
            "[yellow]Git config file not found, skipping Git configuration.[/yellow]"
        )
        return

    try:
        with open(git_config_path, "r") as f:
            content = f.read()

        original_content = content

        if ctx.user_config["git_name"]:
            content = re.sub(
                r'userName\s*=\s*"[^"]*"',
                f'userName = "{ctx.user_config["git_name"]}"',
                content,
            )
            set_text = (
                "[bold yellow][DRY RUN][/bold yellow] Would set" if ctx.dry_run else "Set"
            )
            ctx.console.print(f"  {set_text} Git user name to: {ctx.user_config['git_name']}")

        if ctx.user_config["git_email"]:
            content = re.sub(
                r'userEmail\s*=\s*"[^"]*"',
                f'userEmail = "{ctx.user_config["git_email"]}"',
                content,
            )
            # Escape double quotes inside f-string properly
            content = re.sub(
                r'userEmail\s*=\s*"[^"]*"',
                'userEmail = "{}"'.format(ctx.user_config["git_email"]),
                content,
            )
            set_text = (
                "[bold yellow][DRY RUN][/bold yellow] Would set" if ctx.dry_run else "Set"
            )
            ctx.console.print(f"  {set_text} Git email to: {ctx.user_config['git_email']}")

        if ctx.user_config["use_signing_key"]:
            signing_method = ctx.user_config["signing_method"]
            signing_key = ctx.user_config["git_signing_key"]

            if signing_method == "gpg":
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

                set_text = (
                    "[bold yellow][DRY RUN][/bold yellow] Would set"
                    if ctx.dry_run
                    else "Set"
                )
                ctx.console.print(f"  {set_text} Git GPG signing key to: {signing_key}")

            elif signing_method == "ssh":
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

                ssh_config_lines = [
                    'gpg.ssh.allowedSignersFile = "~/.ssh/allowed_signers";',
                    'gpg.ssh.program = "ssh-keygen";',
                ]

                for line in ssh_config_lines:
                    key_prefix = line.split("=")[0].strip()
                    if key_prefix not in content:
                        content = re.sub(
                            r"(extraConfig\s*=\s*{)",
                            f"\\1\n      {line}",
                            content,
                        )

                set_text = (
                    "[bold yellow][DRY RUN][/bold yellow] Would set"
                    if ctx.dry_run
                    else "Set"
                )
                ctx.console.print(f"  {set_text} Git SSH signing key to: {signing_key}")

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

        if "onepassword" in content and ctx.user_config["onepassword_disable"]:
            if "credential.helper" in content and "op" in content:
                content = re.sub(
                    r'credential\.helper\s*=\s*"1password"',
                    'credential.helper = "store"',
                    content,
                )
                disable_text = (
                    "[bold yellow][DRY RUN][/bold yellow] Would disable"
                    if ctx.dry_run
                    else "Disabled"
                )
                ctx.console.print(f"  {disable_text} 1Password integration")

        if not ctx.dry_run and content != original_content:
            with open(git_config_path, "w") as f:
                f.write(content)

            if (
                ctx.user_config["use_signing_key"]
                and ctx.user_config["signing_method"] == "ssh"
            ):
                allowed_signers_path = os.path.expanduser("~/.ssh/allowed_signers")
                os.makedirs(os.path.dirname(allowed_signers_path), exist_ok=True)

                pub_key_path = f"{ctx.user_config['git_signing_key']}.pub"
                if os.path.exists(pub_key_path):
                    with open(pub_key_path, "r") as f:
                        pub_key = f.read().strip()

                    with open(allowed_signers_path, "w") as f:
                        f.write(f"{ctx.user_config['git_email']} {pub_key}\n")

                    ctx.console.print(
                        "[green]Created SSH allowed_signers file at "
                        f"{allowed_signers_path}[/green]"
                    )

            ctx.console.print("[green]Git configuration updated successfully![/green]")

    except Exception as e:
        ctx.console.print(
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
        return False

    try:
        result = subprocess.run(
            ["which", command],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        try:
            import shutil

            return shutil.which(command) is not None
        except Exception:
            return False


def apply_home_manager(ctx: InstallContext):
    """Applies the Home Manager configuration."""
    if ctx.dry_run:
        ctx.console.print(
            "[bold yellow][DRY RUN][/bold yellow] Would apply Home Manager "
            "configuration"
        )
        return

    ctx.console.print("[bold]Applying Home Manager configuration...[/bold]")

    # Detect OS and select appropriate flake output
    system = platform.system()
    if system == "Darwin":
        flake_output = "#hadronomy"
    elif system == "Linux":
        flake_output = "#hadronomy-linux"
    else:
        ctx.console.print(f"[bold red]Unsupported operating system: {system}[/bold red]")
        sys.exit(1)

    ctx.console.print(
        f"[dim]Detected OS: {system}, using flake output: {flake_output}[/dim]"
    )

    try:
        run_command(
            [
                "home-manager",
                "switch",
                "--flake",
                f"{ctx.dotfiles_dir}{flake_output}",
                "-b",
                "backup",
                "--impure",
            ]
        )
    except Exception as e:
        ctx.console.print(
            f"[bold red]Error applying Home Manager configuration: {e}[/bold red]"
        )
        sys.exit(1)
    ctx.console.print("[green]Dotfiles applied successfully![/green]")


def handle_exit_signal(signum, frame):
    """Handle exit signals by cleaning up and deleting the script."""
    console.print("\n[bold red]Received termination signal. Cleaning up...[/bold red]")
    cleanup(1)


def is_run_from_install_sh():
    """Check if the script is being run from the install.sh wrapper."""
    try:
        import psutil

        try:
            current_process = psutil.Process()
            parent_process = current_process.parent()
            if parent_process:
                cmdline = " ".join(parent_process.cmdline()).lower()
                return "install.sh" in cmdline
        except Exception:
            pass
    except ImportError:
        pass

    try:
        return os.environ.get("FROM_DOTFILES_INSTALLER") == "true"
    except Exception:
        pass

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

    try:
        is_from_installer = is_run_from_install_sh()
    except Exception:
        is_from_installer = False

    if is_from_installer:
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
            "[bold red]Installation failed! Script not removed as it wasn't "
            "run from install.sh.[/bold red]"
        )

    sys.exit(exit_code)


@app.command()
def install(
    repo_url: str = typer.Option(
        "https://github.com/hadronomy/dotfiles",
        help="The URL of the dotfiles repository.",
    ),
    dotfiles_dir: str = typer.Option(
        "~/.dotfiles", help="The directory to clone the dotfiles into."
    ),
    impure: bool = typer.Option(True, help="Use the --impure flag for home-manager."),
    skip_customization: bool = typer.Option(False, help="Skip the customization step."),
    customize: bool = typer.Option(
        False, help="Force customization regardless of username."
    ),
    dry_run: bool = typer.Option(
        False, help="Perform a dry run without making any changes."
    ),
    standalone: bool = typer.Option(
        False, help="Use standalone installation for Home Manager."
    ),
):
    """Installs Nix, Home Manager, and applies the dotfiles configuration."""
    # Initialize context
    ctx = InstallContext(
        dry_run=dry_run,
        console=Console(),
        dotfiles_dir=os.path.expanduser(dotfiles_dir),
        repo_url=repo_url,
    )

    signal.signal(signal.SIGINT, handle_exit_signal)
    signal.signal(signal.SIGTERM, handle_exit_signal)

    try:
        if skip_customization and customize:
            ctx.console.print(
                "[bold red]Error: --skip-customization and --customize "
                "cannot be used together.[/bold red]"
            )
            cleanup(1)

        if dry_run:
            ctx.console.print(
                "[bold yellow]Running in DRY RUN mode. No changes will be "
                "made.[/bold yellow]"
            )

        if not command_exists("nix", dry_run=dry_run):
            install_nix(ctx)

        if not command_exists("home-manager", dry_run=dry_run) and not dry_run:
            if standalone:
                install_home_manager_standalone(ctx)
            else:
                install_home_manager(ctx)

        clone_dotfiles(ctx)

        if customize:
            customize_dotfiles(ctx, force_customize=True)
        elif not skip_customization:
            customize_dotfiles(ctx)

        apply_home_manager(ctx)

        if dry_run:
            ctx.console.print(
                "[bold yellow]Dry run complete. No changes were made.[/bold yellow]"
            )

    except Exception as e:
        ctx.console.print(f"[bold red]Installation failed with error: {e}[/bold red]")
        if not dry_run:
            cleanup(1)


if __name__ == "__main__":
    try:
        app()
    except Exception as e:
        console.print(f"[bold red]Fatal error: {e}[/bold red]")
        cleanup(1)
