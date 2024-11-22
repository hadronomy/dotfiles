{ inputs, config, pkgs, ... }:
{
  imports = [
    ./gh
    ./btop
    ./nushell
    ./starship
    ./tmux
    ./neovim
  ];

  programs.home-manager.enable = true;
  programs.nix-index.enable = true;

  home.username = "hadronomy";
  home.homeDirectory = "/home/hadronomy";
  xdg.enable = true;

  home.sessionVariables = {
    GOPATH = "${config.home.homeDirectory}/.go";
  };

  home.packages = with pkgs; [
    delta
    clang
    rustup
    gofumpt
    golines
    goimports-reviser
    air
    gnumake
    templ
    tailwindcss
    tailwindcss-language-server
    vivid
    magic-wormhole-rs
    hyperfine
    dust
    ffmpeg
  ];

  # This value determines the Home Manager release that your configuration is
  # compatible with. This helps avoid breakage when a new Home Manager release
  # introduces backwards incompatible changes.
  #
  # You should not change this value, even if you update Home Manager. If you do
  # want to update the value, then make sure to first check the Home Manager
  # release notes.
  home.stateVersion = "24.05"; # Please read the comment before changing.

  programs = {
    tmux = (import ./tmux.nix { inherit pkgs; });
    fzf = (import ./fzf.nix { inherit pkgs; });
    fish = (import ./fish.nix { inherit pkgs; });
    carapace = (import ./carapace.nix { inherit pkgs; });
    bat = (import ./bat.nix { inherit pkgs; });
    atuin = (import ./atuin.nix { inherit pkgs; });
    mise-hadronomy = (import ./mise.nix { inherit pkgs; });
    direnv = (import ./direnv.nix { inherit pkgs; });
    zoxide = (import ./zoxide.nix { inherit pkgs; });
    yazi = (import ./yazi.nix { inherit pkgs; });
    tealdeer = (import ./tealdeer.nix { inherit pkgs; });
    eza = (import ./eza.nix { inherit pkgs; });
    ripgrep = (import ./ripgrep.nix { inherit pkgs; });
  };

  home.activation.developer = ''
    mkdir -p ~/repos
  '';
}