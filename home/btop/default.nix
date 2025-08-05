{ pkgs, config, ... }:
{
  programs.btop = {
    enable = true;
    settings = {
      update_ms = 100;
    };
  };
}
