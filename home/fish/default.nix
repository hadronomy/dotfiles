{ pkgs, ... }:
{
  programs = {
    fish = {
      enable = true;
      # mbx keeps build output on Yggdrasil. An alias rather than a PATH shim:
      # it only rewrites what is typed here, so mbx's own cargo lookup still
      # finds the real binary and cannot re-enter itself. See ../mbx.
      shellAliases = {
        cargo = "mbx";
      };
    };
  };
}
