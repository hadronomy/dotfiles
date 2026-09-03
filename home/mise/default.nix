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
          "npm:@google/gemini-cli" = "latest";

          # Executor (executor.sh) -- local MCP gateway. One daemon at
          # 127.0.0.1:4788 serves every configured integration (MCP, OpenAPI,
          # GraphQL) to every agent over a single endpoint. See ../agents.
          "npm:executor" = "latest";
          dotnet = "latest";

          # mbx -- cargo wrapper that keeps the build cache and target dirs on
          # Yggdrasil instead of the internal disk. See ~/Library/Application
          # Support/mbx/config.toml. Pinned rather than "latest": pinned
          # versions are reproducible, and 1.4.1 is what the docs and jdx's
          # benchmarks describe.
          "github:jdx/mr-boxington" = "1.4.1";

          # Typst document toolchain -- pinned as a set: tinymist and
          # typstyle track the compiler release. Agents compile-verify
          # every edit, so the shims must resolve without a project file.
          typst = "0.15.1";
          tinymist = "0.15.2";
          typstyle = "0.15.1";
        };
        wrappers.cargo = {
          # Route plain cargo through mbx. MBX_CARGO_SHIM_MODE tells mbx it was
          # invoked as a shim: it then resolves the real cargo from PATH while
          # skipping mise's dispatch directories, so the wrapper cannot
          # re-enter itself. Requires mise 2026.8.16+.
          command = "mbx";
          env = {
            MBX_CARGO_SHIM_MODE = "1";
          };
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
