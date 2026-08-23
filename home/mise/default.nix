{
  ...
}:
{
  programs = {
    hadronomy.mise = {
      enable = true;
      globalConfig = {
        tools = {
          node = "lts";
          bun = "latest";
          deno = "latest";
          go = "latest";
          "cargo:cargo-nextest" = "latest";
          "cargo:cargo-dist" = "latest";
          "cargo:cargo-mutants" = "latest";
          "cargo:cargo-binstall" = "latest";
          "cargo:cargo-binutils" = "latest";
          "cargo:cargo-edit" = "latest";
          watchexec = "latest";
          "npm:@antfu/ni" = "latest";
          dotnet = "latest";
          zig = "0.14.0";
          zls = "0.14.0";
          "npm:@google/gemini-cli" = "latest";
        };
        settings = {
          idiomatic_version_file_enable_tools = [
            "node"
          ];
          activate_aggressive = true;
        };
      };
    };
  };

  # mise activates only in fish and nushell, but agent CLIs shell out through
  # zsh and bash. Shims rather than `mise activate`: activation costs ~27ms per
  # shell, and shims already carry [env] through to the tool they launch.
  #
  # Prepended in each file rather than set once, because macOS path_helper
  # (/etc/zprofile -> /etc/profile) rebuilds PATH in every login shell and would
  # otherwise leave Homebrew's node ahead of mise's. Each file below runs after
  # the reordering that affects it.
  home.file =
    let
      shims = ''
        export PATH="$HOME/.local/share/mise/shims:$PATH"
      '';
    in
    {
      # zsh -c: the only file a non-interactive zsh reads. Login shells skip
      # it and let .zprofile do the work, so PATH gets one entry, not two.
      ".zshenv".text = ''
        [[ -o login ]] || export PATH="$HOME/.local/share/mise/shims:$PATH"
      '';

      # zsh -lc: runs after /etc/zprofile, so this re-wins the ordering.
      ".zprofile".text = shims;

      # bash -c reads neither of these, but codex's profile snapshot sources
      # .bashrc directly, and bash -lc falls back to .profile when there is no
      # .bash_profile. Both keep the lines that were already there.
      ".bashrc".text = ''
        export PATH="$PATH:$HOME/.local/bin"
      ''
      + shims;

      ".profile".text = ''
        . "$HOME/.local/bin/env"
        eval "$(/opt/homebrew/bin/brew shellenv)"
      ''
      + shims;
    };
}
