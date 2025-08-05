{
  config,
  lib,
  pkgs,
  ...
}:

with lib;

let
  cfg = config.programs.hadronomy.macchina;
  tomlFormat = pkgs.formats.toml { };
in
{
  options = {
    programs.hadronomy.macchina = {
      enable = mkEnableOption "macchina";

      package = mkPackageOption pkgs "macchina" { };

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

      theme = mkOption {
        type = tomlFormat.type;
        default = { };
        example = literalExpression ''
            theme = {
            spacing = 1;
            padding = 0;
            hide_ascii = false;
            prefer_small_ascii = true;
            separator = "λ";
            separator_color = "White";
            palette = {
              type = "Dark";
              visible = true;
              glyph = " ⬤ ";
            };
            box = {
              title = " hadronomy ";
              border = "rounded";
              visible = true;
              inner_margin = {
                x = 3;
                y = 1;
              };
            };
            randomize = {
              key_color = false;
              separator_color = false;
            };
            keys = {
              host = "User/Hostname";
              kernel = "Kernel";
              battery = "Battery Info";
              os = "Operating System";
              de = "Desktop Environment";
              wm = "Window Manager";
              distro = "Distribution";
              terminal = "Terminal Emulator";
              shell = "Shell";
              packages = "Packages (mgr)";
              uptime = "Uptime";
              memory = "Memory";
              machine = "Machine";
              local_ip = "Local IP";
              backlight = "Brightness";
              resolution = "Resolution";
              cpu_load = "CPU Load";
              cpu = "Processor (cores)";
              gpu = "Graphics Processor";
              disk_space = "Disk Space";
            };
          };
        '';
        description = ''
          Config written to {file}`$XDG_CONFIG_HOME/macchina/themes/default.toml`.
        '';
      };

      settings = mkOption {
        type = tomlFormat.type;
        default = {
          theme = mkIf (cfg.theme != { }) "default";
        };
        example = literalExpression ''
          theme = "default";
        '';
        description = ''
          Config written to {file}`$XDG_CONFIG_HOME/macchina/macchina.toml`.
        '';
      };
    };
  };

  config = mkIf cfg.enable {
    home.packages = [ cfg.package ];

    xdg.configFile = {
      "macchina/macchina.toml" = mkIf (cfg.settings != { }) {
        source = tomlFormat.generate "macchina-settings" cfg.settings;
      };
      "macchina/themes/default.toml" = mkIf (cfg.theme != { }) {
        source = tomlFormat.generate "macchina-theme" cfg.theme;
      };
    };

    programs = {
      bash.shellAliases = mkIf cfg.enableBashIntegration {
        m = "macchina";
      };

      zsh.shellAliases = mkIf cfg.enableZshIntegration {
        m = "macchina";
      };

      fish.shellAliases = mkIf cfg.enableFishIntegration {
        m = "macchina";
      };

      nushell.shellAliases = mkIf cfg.enableNushellIntegration {
        m = "macchina";
      };
    };
  };
}
