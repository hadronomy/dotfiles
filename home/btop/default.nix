{ pkgs, config, ... }:
{
  xdg.configFile."btop/themes/catppuccin_mocha.theme" = {
    source = ./catppuccin_mocha.theme;
  };
  programs.btop = {
    enable = true;
    settings = {
      color_theme = "${config.xdg.configHome}/btop/themes/catppuccin_mocha.theme";
      update_ms = 100;
    };
  };
}