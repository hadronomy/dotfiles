{ pkgs, ... }:
{
  # NOTE: This is a simple derivation that echoes "Hello World!" when run.
  # You can run it with `nix run .` or `nix-build . -A hello-world`.
  # TODO: Autosetup script for the dotfiles
  default = pkgs.stdenv.mkDerivation {
    name = "hello-world-fzf";
    src = null;
    buildInputs = [ pkgs.fzf ];
    phases = [ "installPhase" ];
    installPhase = ''
      mkdir -p $out/bin
      echo '#!/bin/sh' > $out/bin/hello-world-fzf
      echo 'echo "Hello World!" | ${pkgs.fzf}/bin/fzf' >> $out/bin/hello-world-fzf
      chmod +x $out/bin/hello-world-fzf
    '';
  };
}
