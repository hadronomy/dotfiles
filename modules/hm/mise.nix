# Adds nushell integration to the mise package
{
  config,
  lib,
  pkgs,
  ...
}:

with lib;

let
  cfg = config.programs.hadronomy.mise;
  tomlFormat = pkgs.formats.toml { };
in
{
  # imports = let
  #   mkRemovedWarning = opt:
  #     (mkRemovedOptionModule [ "programs" "rtx" opt ] ''
  #       The `rtx` package has been replaced by `mise`, please switch over to
  #       using the options under `programs.mise.*` instead.
  #     '');

  # in map mkRemovedWarning [
  #   "enable"
  #   "package"
  #   "enableBashIntegration"
  #   "enableZshIntegration"
  #   "enableFishIntegration"
  #   "settings"
  # ];

  options = {
    programs.hadronomy.mise = {
      enable = mkEnableOption "mise";

      package = mkPackageOption pkgs "mise" { };

      enableBashIntegration = mkEnableOption "Bash Integration" // {
        default = true;
      };

      enableZshIntegration = mkEnableOption "Zsh Integration" // {
        default = true;
      };

      enableFishIntegration = mkEnableOption "Fish Integration" // {
        default = true;
      };

      enableNushellIntegration = mkEnableOption "Nushell Integration" // {
        default = true;
      };

      globalConfig = mkOption {
        type = tomlFormat.type;
        default = { };
        example = literalExpression ''
          tools = {
            node = "lts";
            python = ["3.10" "3.11"];
          };

          aliases = {
            my_custom_node = "20";
          };
        '';
        description = ''
          Config written to {file}`$XDG_CONFIG_HOME/mise/config.toml`.

          See <https://mise.jdx.dev/configuration.html#global-config-config-mise-config-toml>
          for details on supported values.
        '';
      };

    };
  };

  config = mkIf cfg.enable {
    home.packages = [ cfg.package ];

    xdg.configFile = {
      "mise/config.toml" = mkIf (cfg.globalConfig != { }) {
        source = tomlFormat.generate "mise-config" cfg.globalConfig;
      };

    };

    programs = {
      bash.initExtra = mkIf cfg.enableBashIntegration ''
        eval "$(${getExe cfg.package} activate bash)"
      '';

      zsh.initExtra = mkIf cfg.enableZshIntegration ''
        eval "$(${getExe cfg.package} activate zsh)"
      '';

      fish.interactiveShellInit = mkIf cfg.enableFishIntegration ''
        ${getExe cfg.package} activate fish | source
      '';

      # Generated at build time and used straight from the store. Writing it at
      # runtime cannot work: nushell resolves the file at parse time, so config.nu
      # always saw the previous run's copy. The store path also keeps a reference
      # to the mise binary it came from, so the GC cannot collect it out from
      # under a shell that is about to source it.
      #
      # The extra directory is what makes the module name `mise` instead of the
      # store hash. `activate nu` ends in `export def --env --wrapped main`, and
      # that only binds to `mise` when the module is named `mise` -- which is what
      # lets `mise shell` and `mise deactivate` change the current environment
      # rather than a subprocess's.
      nushell = mkIf cfg.enableNushellIntegration {
        extraConfig = ''
          use ${
            pkgs.runCommand "mise-nu" { } ''
              mkdir -p $out
              ${getExe cfg.package} activate nu > $out/mise.nu
            ''
          }/mise.nu
        '';
      };
    };
  };
}
