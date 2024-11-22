{ pkgs, ... }:
{
  enable = true;
  shellAliases = {
    c = "clear";
    ll = "ls -l";
    la = "ls -la";
    command = "which";
    pbcopy = "xsel --clipboard --input";
    pbpaste = "xsel --clipboard --output";
    wormhole = "wormhole-rs";
  };
}