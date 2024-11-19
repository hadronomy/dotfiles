{ inputs, config, pkgs, ... }:
let
  inherit (config.lib.file) mkOutOfStoreSymlink;
in
{
  programs.home-manager.enable = true;
  programs.nix-index.enable = true;

  home.username = "hadronomy";
  home.homeDirectory = "/home/hadronomy";
  xdg.enable = true;

  home.packages = with pkgs; [
  ];

  # This value determines the Home Manager release that your configuration is
  # compatible with. This helps avoid breakage when a new Home Manager release
  # introduces backwards incompatible changes.
  #
  # You should not change this value, even if you update Home Manager. If you do
  # want to update the value, then make sure to first check the Home Manager
  # release notes.
  home.stateVersion = "24.05"; # Please read the comment before changing.

  programs = {
    tmux = (import ./tmux.nix { inherit pkgs; });
    # neovim = (import ./neovim.nix { inherit config pkgs; });
    # git = (import ./git.nix { inherit config pkgs; });
    # gpg = (import ./gpg.nix { inherit config pkgs; });
    # firefox = (import ./firefox.nix { inherit pkgs; });
    # zoxide = (import ./zoxide.nix { inherit pkgs; });
    # password-store = (import ./pass.nix { inherit pkgs; });
    fzf = (import ./fzf.nix { inherit pkgs; });
    fish = (import ./fish.nix { inherit pkgs; });
    nushell = (import ./nushell.nix { inherit pkgs; });
    starship = (import ./starship.nix { inherit pkgs; });
  };

  home.activation.developer = ''
    mkdir -p ~/repos
  '';
}