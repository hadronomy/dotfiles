{ pkgs, ... }:
let
  inherit (pkgs) tmuxPlugins fetchFromGitHub;
  inherit (pkgs.tmuxPlugins) mkTmuxPlugin;

  # https://github.com/junegunn/tmux-fzf-url
  fzf-url = mkTmuxPlugin {
    pluginName = "fzf-url";
    version = "1ffce23";
    src = fetchFromGitHub {
      owner = "junegunn";
      repo = "tmux-fzf-url";
      rev = "1ffce234173d0bc8004fc5934599e473e36af01c";
      sha256 = "0v9s1m46slryz6hbvxr2cw6ssjswmvnp5gigw076jzcmh17clg59";
    };
  };
in
{
  home.packages = with pkgs; [
    sesh
  ];

  programs = { 
    tmux = {
      enable = true;
      extraConfig = builtins.readFile ./tmux.conf;
      plugins = with pkgs.tmuxPlugins; [
        sensible
        resurrect
        continuum
        catppuccin
        fzf-url
      ];
    };
  };
}