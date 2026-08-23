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

  # zsh is not a configured shell here, but every agent CLI shells out through
  # it -- and Claude Code rebuilds its whole environment from a zsh snapshot,
  # so it never sees the mise activation that fish and nushell get. .zshenv is
  # the only file a non-interactive `zsh -c` reads, which makes it the one place
  # that reaches all of them. Shims rather than `mise activate`: activation
  # needs a prompt hook that never fires in a non-interactive shell.
  home.file.".zshenv".text = ''
    export PATH="$HOME/.local/share/mise/shims:$PATH"
  '';
}
