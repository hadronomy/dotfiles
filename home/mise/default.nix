{
  pkgs,
  config,
  specialArgs,
  ...
}:
let
  inherit (specialArgs) flakePkgs;
in
{
  programs = {
    hadronomy.mise = {
      enable = true;
      package = flakePkgs.mise;
      globalConfig.tools = {
        node = "lts";
        bun = "latest";
        deno = "latest";
        go = "latest";
        "cargo:cargo-nextest" = "latest";
        "cargo:cargo-dist" = "latest";
        "cargo:cargo-mutants" = "latest";
        "cargo:cargo-binstall" = "latest";
        "cargo:cargo-edit" = "latest";
        watchexec = "latest";
      };
      settings.activate_aggresive = true;
    };
  };
}
