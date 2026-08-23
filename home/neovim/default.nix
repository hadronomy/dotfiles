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
      sideloadInitLua = true;
      withPython3 = true;
      withRuby = true;
    };
  };

  catppuccin = {
    nvim.enable = false;
  };

  xdg.configFile."nvim".source =
    mkOutOfStoreSymlink "${config.home.homeDirectory}/.dotfiles/home/neovim/config";
}
