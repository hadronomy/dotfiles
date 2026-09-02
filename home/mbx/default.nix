# mbx (Mr Boxington) -- jdx's caching Cargo wrapper.
#
# The point of the paths below is to keep Rust build output off the internal
# disk, which sits at 89% full. Yggdrasil is APFS, so the store and the target
# directories share a volume and mbx can reflink outputs into target/ instead of
# copying them. Splitting them across volumes would silently lose that.
#
# Plain `cargo` reaches mbx through mise's [wrappers.cargo] entry in ../mise;
# agent shells get the wrapper onto PATH in ../agent-env. fish and nushell use
# a plain alias instead; this exists because non-interactive shells expand no
# aliases and agents exec cargo directly.
{ ... }:
{
  # `-C link-arg=-fuse-ld=lld` is gone for the same reason. Every -C codegen
  # option bypasses the cache as `unknown-codegen-option`, and `-C linker=` to
  # a wrapper script does too -- there is no cacheable way to force lld. The
  # cache is worth more here than the linker; put the flag back if that flips.
  home.file.".cargo/config.toml".text = ''
    # Deliberately carries no rustflags. A `-L` search path or any `-C` option
    # here disables the mbx build cache for every compilation in every project.
    # libiconv resolves from the macOS SDK through /usr/bin/cc; see home/default.nix.
  '';

  # mbx reads the platform config directory, not XDG. On macOS that is
  # ~/Library/Application Support -- confirmed against 1.4.1 by mbx doctor
  # reading this file. A file under ~/.config/mbx is ignored without comment.
  home.file."Library/Application Support/mbx/config.toml".text = ''
    cache_dir = "/Volumes/Yggdrasil/mbx/cache"

    [target]
    views = true
    root = "/Volumes/Yggdrasil/mbx/targets"
  '';
}
