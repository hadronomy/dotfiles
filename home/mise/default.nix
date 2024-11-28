{ pkgs, config, specialArgs, ... }:
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
      };
      settings.activate_aggresive = true;
    };
  };
}
