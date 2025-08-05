{ pkgs, ... }:
{
  programs.starship = {
    enable = true;
  };

  catppuccin = {
    starship.enable = false;
  };

  xdg.configFile."starship.toml" = {
    source = ./starship.toml;
  };
}
