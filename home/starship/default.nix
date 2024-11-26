{ pkgs, ... }:
{
  programs.starship = {
    enable = true;
    catppuccin.enable = false;
  };

  xdg.configFile."starship.toml" = {
    source = ./starship.toml;
  };
}
