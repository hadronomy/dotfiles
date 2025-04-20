{
  ...
}:
{
  programs = {
    hadronomy.mise = {
      enable = true;
      globalConfig.tools = {
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
      };
      settings.activate_aggresive = true;
    };
  };
}
