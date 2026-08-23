#!/usr/bin/env bash
# Regenerates packages/mise/sources.json against a mise release.
# Usage: ./update.sh [version]   (defaults to the current release)
set -euo pipefail
cd "$(dirname "$0")"

# system:asset pairs. Linux points at the static musl tarball on purpose: the
# glibc build is BOLT-optimized, and running patchelf over a BOLT-rewritten ELF
# to repoint the loader is a reliable way to break it. musl still gets PGO and
# the `serious` profile, and needs no patching at all.
SYSTEMS="aarch64-darwin:macos-arm64 x86_64-linux:linux-x64-musl"

version="${1:-$(curl -fsSL https://mise.jdx.dev/VERSION)}"
echo "mise $version" >&2

{
  printf '{\n  "version": "%s",\n  "platforms": {\n' "$version"
  sep=""
  for pair in $SYSTEMS; do
    system="${pair%%:*}"
    asset="${pair#*:}"
    url="https://github.com/jdx/mise/releases/download/v$version/mise-v$version-$asset.tar.gz"
    echo "  fetching $asset" >&2
    hash=$(nix hash convert --hash-algo sha256 --to sri "$(nix-prefetch-url --type sha256 "$url" 2>/dev/null)")
    printf '%s    "%s": {\n      "url": "%s",\n      "hash": "%s"\n    }' "$sep" "$system" "$url" "$hash"
    sep=$',\n'
  done
  printf '\n  }\n}\n'
} >sources.json.new

mv sources.json.new sources.json
echo "wrote sources.json" >&2
