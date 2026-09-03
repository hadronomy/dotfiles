{ pkgs, ... }:
{
  programs = {
    fish = {
      enable = true;
      # opencode2 (v2 beta) lands here via its own installer. Prepended, like
      # .zshrc. fish_add_path -g keeps it session-scoped instead of writing a
      # universal variable outside Nix's control.
      shellInit = "fish_add_path -g $HOME/.opencode/bin";
      # mbx keeps build output on Yggdrasil. An alias rather than a PATH shim:
      # it only rewrites what is typed here, so mbx's own cargo lookup still
      # finds the real binary and cannot re-enter itself. See ../mbx.
      shellAliases = {
        cargo = "mbx";
      };
    };
  };
}
