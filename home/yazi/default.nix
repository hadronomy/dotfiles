{ pkgs, ... }:
{
  programs = {
    yazi = {
      enable = true;
    };
  };
  xdg.configFile."yazi/theme.toml".source = ./theme.toml;
}
