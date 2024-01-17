{ pkgs, ... }:
{
  xdg.desktopEntries = {
    "lf" = {
      name = "lf";
      noDisplay = true;
    };
  };

  home.packages = with pkgs; with nodePackages_latest; with gnome; [
    sway
    # colorscript
    # (import ./colorscript.nix { inherit pkgs; })

    # gui
    # obsidian
    # (mpv.override { scripts = [mpvScripts.mpris]; })
    spotify
    # d-spy
    # easyeffects
    # gimp
    # transmission_4-gtk
    discord
    # bottles
    icon-library
    # dconf-editor

    # tools
    starship
    atuin
    zoxide
    bat
    eza
    fd
    ripgrep
    fzf
    socat
    jq
    acpi
    inotify-tools
    ffmpeg
    libnotify
    killall
    zip
    unzip
    glib

    # hyprland
    wl-gammactl
    wl-clipboard
    wf-recorder
    hyprpicker
    wayshot
    swappy
    slurp
    imagemagick
    pavucontrol
    brightnessctl
    swww

    # fun
    glow
    slides
    skate
    yabridge
    yabridgectl
    wine-staging
    distrobox

    # langs
    # nodejs
    fnm
    rustup
    bun
    go
    gcc
    typescript
    eslint
  ];
}