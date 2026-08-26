# PATH for the shells that agent CLIs run commands in.
#
# mise activates only in fish and nushell. Agents shell out through zsh and
# bash, and codex rewrites every tool call into `bash -lc` (openai/codex#4210),
# so without this they resolve node, cargo and friends to whatever Homebrew
# happens to have rather than the pinned versions.
#
# Prepended in each file rather than exported once, because macOS path_helper
# (/etc/zprofile -> /etc/profile) rebuilds PATH in every login shell and would
# otherwise leave Homebrew ahead of mise. Each file below runs after the
# reordering that affects it.
{ ... }:
let
  # cargo-shim holds the cargo -> mbx wrapper (see ../mbx). It goes ahead of
  # the nix profile so `cargo` reaches the wrapper rather than rustup's shim.
  # fish and nushell add the same directory in their own modules.
  path = ''
    export PATH="$HOME/.local/share/cargo-shim:$HOME/.local/share/mise/shims:$PATH"
    case ":''${LIBRARY_PATH:-}:" in
      *":/opt/homebrew/opt/libiconv/lib:"*) ;;
      *) export LIBRARY_PATH="/opt/homebrew/opt/libiconv/lib''${LIBRARY_PATH:+:$LIBRARY_PATH}" ;;
    esac
  '';
in
{
  home.file = {
    # zsh -c: the only file a non-interactive zsh reads. Login shells skip it
    # and let .zprofile do the work, so PATH gets one entry, not two.
    ".zshenv".text = ''
      if [[ ! -o login ]]; then
      ${path}fi
    '';

    # zsh -lc: runs after /etc/zprofile, so this re-wins the ordering.
    ".zprofile".text = path;

    # bash -c reads neither of these, but codex's profile snapshot sources
    # .bashrc directly, and bash -lc falls back to .profile when there is no
    # .bash_profile. Both keep the lines that were already there.
    ".bashrc".text = ''
      export PATH="$PATH:$HOME/.local/bin"
    ''
    + path;

    ".profile".text = ''
      . "$HOME/.local/bin/env"
      eval "$(/opt/homebrew/bin/brew shellenv)"
    ''
    + path;
  };
}
