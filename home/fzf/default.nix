{ pkgs, ... }:
{
  programs = {
    fzf = {
      enable = true;
      historyWidget.command = "";
    };
  };
}
