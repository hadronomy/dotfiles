{ pkgs, ... }:
{
  programs = {
    direnv = {
      enable = true;
      mise = {
        enable = true;
      };
    };
  };
}
