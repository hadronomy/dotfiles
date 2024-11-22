{ pkgs, config, specialArgs, ... }:
let
  inherit (specialArgs) flakePkgs;
in
{
  programs.nushell = {
    enable = true;
    configFile.text = (builtins.replaceStrings [
        "# use NIX_BASH_ENV_NU_MODULE"
      ] [
        "use ${flakePkgs.bash-env-nushell}/bash-env.nu"
      ]
      (builtins.readFile ./config.nu)
    );
    envFile.source = ./env.nu;
    shellAliases = {
      c = "clear";
      ll = "ls -l";
      la = "ls -la";
      command = "which";
      pbcopy = "xsel --clipboard --input";
      pbpaste = "xsel --clipboard --output";
      wormhole = "wormhole-rs";
      inv = "se";
    };
  };

  home.packages = with pkgs; [
    flakePkgs.bash-env-nushell
  ];
}