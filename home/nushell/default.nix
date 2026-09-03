{
  pkgs,
  config,
  specialArgs,
  ...
}:
let
  inherit (specialArgs) flakePkgs;
in
{
  programs.nushell = {
    enable = true;
    configFile.text = (
      builtins.replaceStrings
        [
          "# use NIX_BASH_ENV_NU_MODULE"
        ]
        [
          "use ${flakePkgs.bash-env-nushell}/bash-env.nu"
        ]
        (builtins.readFile ./config.nu)
    );
    envFile.source = ./env.nu;
    shellAliases = {
      # mbx keeps build output on Yggdrasil. An alias rather than a PATH shim:
      # it only rewrites what is typed here, so mbx's own cargo lookup still
      # finds the real binary and cannot re-enter itself. See ../mbx.
      cargo = "mbx";
      c = "clear";
      ll = "ls -l";
      la = "ls -la";
      command = "which";
      pbcopy = "xsel --clipboard --input";
      pbpaste = "xsel --clipboard --output";
      wormhole = "wormhole-rs";
      inv = "se";
      v = "nvim";
    };
  };

  home.packages = with pkgs; [
    flakePkgs.bash-env-nushell
  ];

  # Worktrunk worktree switching. The nu wrapper exports `def wt`, so it must
  # be sourced rather than `use`d -- a module import would bind it as `wt wt`.
  # Nushell sources every file in the vendor autoload dir at startup, which is
  # the install path upstream documents. Generated at build time, same
  # reasoning as ../modules/hm/mise.nix: the store path cannot go stale or be
  # garbage collected out from under a shell that is about to source it.
  xdg.dataFile."nushell/vendor/autoload/wt.nu".source =
    (pkgs.runCommand "worktrunk-nu" { } ''
      mkdir -p $out
      ${flakePkgs.worktrunk}/bin/wt config shell init nu > $out/wt.nu
    '') + "/wt.nu";
}
