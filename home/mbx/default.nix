# mbx (Mr Boxington) -- jdx's caching Cargo wrapper.
#
# The point of the paths below is to keep Rust build output off the internal
# disk, which sits at 89% full. Yggdrasil is APFS, so the store and the target
# directories share a volume and mbx can reflink outputs into target/ instead of
# copying them. Splitting them across volumes would silently lose that.
{ ... }:
{
  # libiconv comes from the environment rather than a `-L` rustflag. Build
  # scripts here (blake3, zstd-sys) link -liconv and fail without it, so the
  # search path is load-bearing -- but mbx cannot cache any compilation that
  # carries a rustc search path, and reports every one as
  # `unsupported-search-path`. LIBRARY_PATH reaches the linker without rustc
  # ever seeing a -L, which keeps the build working and the cache usable:
  # measured 0 -> 183 hits on a 4-crate workspace.
  home.sessionVariables.LIBRARY_PATH = "/opt/homebrew/opt/libiconv/lib";

  # `-C link-arg=-fuse-ld=lld` is gone for the same reason. Every -C codegen
  # option bypasses the cache as `unknown-codegen-option`, and `-C linker=` to
  # a wrapper script does too -- there is no cacheable way to force lld. The
  # cache is worth more here than the linker; put the flag back if that flips.
  home.file.".cargo/config.toml".text = ''
    # Deliberately carries no rustflags. A `-L` search path or any `-C` option
    # here disables the mbx build cache for every compilation in every project.
    # libiconv is supplied through LIBRARY_PATH instead; see home/mbx.
  '';

  # mbx reads the platform config directory, not XDG. On macOS that is
  # ~/Library/Application Support, confirmed against 0.4.0 -- a file under
  # ~/.config/mbx is ignored without comment.
  home.file."Library/Application Support/mbx/config.toml".text = ''
    cache_dir = "/Volumes/Yggdrasil/mbx/cache"

    [target]
    views = true
    root = "/Volumes/Yggdrasil/mbx/targets"
  '';

  # `cargo` routed through mbx for agents. fish and nushell use a plain alias
  # instead; this exists because non-interactive shells expand no aliases and
  # agents exec cargo directly. mbx resolves cargo from PATH -- which is this
  # script -- so without the guard it would invoke itself forever. On re-entry
  # the guard hands mbx the real binary.
  #
  # Leading flags go straight to cargo: `cargo --version` has to answer as
  # cargo, or anything that parses that version gets mbx's instead.
  home.file.".local/share/cargo-shim/cargo" = {
    executable = true;
    text = ''
      #!/bin/sh
      real_cargo="''${MBX_REAL_CARGO:-$HOME/.nix-profile/bin/cargo}"

      # mbx sets RUSTC_WRAPPER to its own rustc shim before it spawns cargo.
      # Seeing it means mbx is the caller and wants the real binary -- this is
      # what keeps a direct `mbx build` from re-entering mbx through here. A
      # foreign RUSTC_WRAPPER (sccache) also lands here, which is right: do not
      # fight a wrapper the user chose.
      case "''${RUSTC_WRAPPER:-}" in
        *mbx-rustc*) exec "$real_cargo" "$@" ;;
      esac

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
