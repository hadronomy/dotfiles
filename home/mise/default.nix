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

          # mbx -- cargo wrapper that keeps the build cache and target dirs on
          # Yggdrasil instead of the internal disk. See ~/.config/mbx/config.toml.
          # Pinned rather than "latest": mise's release-age guard still hides
          # 0.4.0, and 0.4.0 is what the docs and jdx's benchmarks describe.
          "github:jdx/mr-boxington" = "0.4.0";
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
}
