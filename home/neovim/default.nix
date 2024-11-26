{ pkgs, config, ... }:
let
  inherit (config.lib.file) mkOutOfStoreSymlink;
in
{
  programs = {
    neovim = {
      enable = true;
      defaultEditor = true;
      viAlias = true;
      vimAlias = true;
      catppuccin.enable = false;
    };
  };

  xdg.configFile."nvim".source = mkOutOfStoreSymlink "${config.home.homeDirectory}/.dotfiles/home/neovim/config";
}
