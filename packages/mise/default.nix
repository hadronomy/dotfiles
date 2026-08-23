# mise from jdx's own release tarballs instead of a source build.
#
# nixpkgs (and mise's own flake) compile mise with the stock `release` profile.
# The published binaries use `--profile serious` (fat LTO, panic=abort), a
# trimmed feature set, and profile-guided optimization; the macOS ones also
# target macOS 12 so dyld gets chained fixups instead of ~170k rebase opcodes.
# jdx measures that at 20-30% faster startup and ~40% smaller than a plain
# source build, which matters because mise runs on every prompt.
{
  lib,
  stdenvNoCC,
  fetchurl,
  installShellFiles,
  writeText,
}:

let
  sources = lib.importJSON ./sources.json;
  inherit (stdenvNoCC.hostPlatform) system;
  platform =
    sources.platforms.${system}
      or (throw "mise: no release binary recorded for ${system} — add it to SYSTEMS in packages/mise/update.sh and re-run it");

  # Replaces mise's "run `mise self-update`" hint, which cannot work against a
  # read-only store, with the way this install is actually upgraded.
  selfUpdateInstructions = writeText "mise-self-update-instructions.toml" ''
    message = "mise is managed by Nix. Update it with: ~/.dotfiles/packages/mise/update.sh && dot-apply"
  '';
in
stdenvNoCC.mkDerivation {
  pname = "mise";
  version = sources.version;

  src = fetchurl { inherit (platform) url hash; };

  sourceRoot = "mise";

  nativeBuildInputs = [ installShellFiles ];

  # The macOS binaries carry jdx's Developer ID signature and the Linux ones are
  # PGO'd static musl. Both have to reach the store byte-for-byte: stripping
  # invalidates the signature, and patchelf would undo the point of the build.
  dontStrip = true;
  dontPatchELF = true;

  installPhase = ''
    runHook preInstall

    install -Dm755 bin/mise $out/bin/mise
    installManPage man/man1/mise.1

    # mise looks for both of these two directories above its own binary. The
    # marker is what turns `mise self-update` off.
    install -Dm644 /dev/null $out/lib/.disable-self-update
    install -Dm644 ${selfUpdateInstructions} $out/lib/mise-self-update-instructions.toml

    runHook postInstall
  '';

  # share/fish/vendor_conf.d/mise-activate.fish is deliberately left out: the
  # home-manager module already runs `mise activate fish`, and home-manager puts
  # package vendor_conf.d files on fish's path, so shipping it activates twice.

  doInstallCheck = true;
  installCheckPhase = ''
    $out/bin/mise --version | grep -F '${sources.version}'
  '';

  passthru.updateScript = ./update.sh;

  meta = {
    description = "Dev tools, env vars, and tasks in one CLI (official optimized binary)";
    homepage = "https://mise.jdx.dev";
    changelog = "https://github.com/jdx/mise/releases/tag/v${sources.version}";
    license = lib.licenses.mit;
    mainProgram = "mise";
    platforms = lib.attrNames sources.platforms;
    sourceProvenance = [ lib.sourceTypes.binaryNativeCode ];
  };
}
