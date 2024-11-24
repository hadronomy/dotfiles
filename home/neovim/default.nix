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
    };
  };
  
  xdg.configFile."nvim".source = mkOutOfStoreSymlink ./config;
}