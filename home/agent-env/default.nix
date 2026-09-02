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
  # mise command-wrappers holds the cargo -> mbx shim ([wrappers.cargo] in
  # ../mise). It goes ahead of the shims farm so the wrapper wins PATH
  # resolution, and ahead of the nix profile so `cargo` reaches the wrapper
  # rather than rustup's shim. fish and nushell get wrappers through mise
  # activate and add the same directory in their own modules.
  path = ''
    export PATH="$HOME/.local/share/mise/command-wrappers/bin:$HOME/.local/share/mise/shims:$PATH"
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

    # Interactive zsh, login or not. It runs after /etc/zprofile's path_helper
    # (login) and /etc/zshrc, so this re-wins the mise ordering too. Also the
    # only place opencode2 reaches PATH: the v2 installer drops the binary in
    # ~/.opencode/bin and touches no shell config of its own.
    ".zshrc".text = ''
      . "$HOME/.local/bin/env"
    ''
    + path
    + ''
      export PATH="$HOME/.opencode/bin:$PATH"
    '';

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
