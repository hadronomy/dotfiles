{ pkgs, username, ... }:
let 
  homeDirectory = "/home/${username}";
in
{
  imports = [
    ./git.nix
    ./sh.nix
    ./packages.nix
  ];

  targets.genericLinux.enable = true;

  nix = {
    package = pkgs.nix;
    settings = {
      experimental-features = [ "nix-command" "flakes" ];
      warn-dirty = false;
    };
  };

  home = {
    inherit username homeDirectory;

    sessionPath = [
      "$HOME/.local/bin"
    ];
  };

  programs.home-manager.enable = true;
  home.stateVersion = "24.05";
}