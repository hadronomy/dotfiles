# mbx (Mr Boxington) -- jdx's caching Cargo wrapper.
#
# The point of the paths below is to keep Rust build output off the internal
# disk, which sits at 89% full. Yggdrasil is APFS, so the store and the target
# directories share a volume and mbx can reflink outputs into target/ instead of
# copying them. Splitting them across volumes would silently lose that.
{ ... }:
{
  # mbx reads the platform config directory, not XDG. On macOS that is
  # ~/Library/Application Support, confirmed against 0.4.0 -- a file under
  # ~/.config/mbx is ignored without comment.
  home.file."Library/Application Support/mbx/config.toml".text = ''
    cache_dir = "/Volumes/Yggdrasil/mbx/cache"

    [target]
    views = true
    root = "/Volumes/Yggdrasil/mbx/targets"
  '';

  # `cargo` routed through mbx for the shells agents use. mbx resolves cargo
  # from PATH -- which is this script -- so without the guard it would invoke
  # itself forever. On re-entry the guard hands mbx the real binary.
  #
  # Leading flags go straight to cargo: `cargo --version` has to answer as
  # cargo, or anything that parses that version gets mbx's instead.
  home.file.".local/share/agent-bin/cargo" = {
    executable = true;
    text = ''
      #!/bin/sh
      real_cargo="''${MBX_REAL_CARGO:-$HOME/.nix-profile/bin/cargo}"

      if [ -n "''${MBX_CARGO_SHIM:-}" ]; then
        exec "$real_cargo" "$@"
      fi

      if [ $# -eq 0 ]; then
        exec "$real_cargo"
      fi

      case "$1" in
        -*) exec "$real_cargo" "$@" ;;
      esac

      MBX_CARGO_SHIM=1
      export MBX_CARGO_SHIM
      exec mbx "$@"
    '';
  };
}
