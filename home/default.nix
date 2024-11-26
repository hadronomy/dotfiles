{ config, pkgs, ... }:
let
  importDir = ./.;
  importFiles = builtins.attrNames (builtins.readDir importDir);
  filteredFiles = builtins.filter (file: file != "default.nix") importFiles;
  importsList = map (file: importDir + "/${file}") filteredFiles;
in
{
  imports = importsList;

  programs.home-manager.enable = true;
  programs.nix-index.enable = true;

  home.username = "hadronomy";
  home.homeDirectory = "/home/${config.home.username}";
  xdg.enable = true;

  home.sessionVariables = {
    GOPATH = "${config.home.homeDirectory}/.go";
  };

  home.packages = with pkgs; [
    delta
    clang
    rustup
    gofumpt
    golines
    goimports-reviser
    golangci-lint
    air
    gnumake
    templ
    tailwindcss
    tailwindcss-language-server
    vivid
    magic-wormhole-rs
    hyperfine
    dust
    ffmpeg
    macchina
    ouch
    uv
  ];

  # This value determines the Home Manager release that your configuration is
  # compatible with. This helps avoid breakage when a new Home Manager release
  # introduces backwards incompatible changes.
  #
  # You should not change this value, even if you update Home Manager. If you do
  # want to update the value, then make sure to first check the Home Manager
  # release notes.
  home.stateVersion = "24.05"; # Please read the comment before changing.

  home.activation.developer = ''
    mkdir -p ~/repos
  '';
}
