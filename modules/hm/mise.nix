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

      settings = mkOption {
        type = tomlFormat.type;
        default = { };
        example = literalExpression ''
          verbose = false;
          experimental = false;
          disable_tools = ["node"];
        '';
        description = ''
          Settings written to {file}`$XDG_CONFIG_HOME/mise/settings.toml`.

          See <https://mise.jdx.dev/configuration.html#settings-file-config-mise-settings-toml>
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

      "mise/settings.toml" = mkIf (cfg.settings != { }) {
        source = tomlFormat.generate "mise-settings" cfg.settings;
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

      nushell = mkIf cfg.enableNushellIntegration {
        extraEnv = ''
          let mise_cache = "${config.xdg.cacheHome}/mise"
          if not ($mise_cache | path exists) {
            mkdir $mise_cache
          }
          ${cfg.package}/bin/mise activate nu |
            save --force ${config.xdg.cacheHome}/mise/init.nu
        '';
        extraConfig = ''
          source ${config.xdg.cacheHome}/mise/init.nu
        '';
      };
    };
  };
}
