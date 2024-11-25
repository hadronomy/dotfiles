{ pkgs, ... }:
let
  inherit (pkgs) tmuxPlugins fetchFromGitHub;
  inherit (pkgs.tmuxPlugins) mkTmuxPlugin;

  # https://github.com/junegunn/tmux-fzf-url
  fzf-url = mkTmuxPlugin {
    pluginName = "fzf-url";
    version = "1ffce23";
    src = fetchFromGitHub {
      owner = "junegunn";
      repo = "tmux-fzf-url";
      rev = "1ffce234173d0bc8004fc5934599e473e36af01c";
      sha256 = "0v9s1m46slryz6hbvxr2cw6ssjswmvnp5gigw076jzcmh17clg59";
    };
  };
in
{
  home.packages = with pkgs; [
    sesh
    fd
  ];

  programs = { 
    tmux = {
      enable = true;
      extraConfig = builtins.readFile ./tmux.conf;
      plugins = with pkgs.tmuxPlugins; [
        sensible
        resurrect
        continuum
        tmux-fzf
        fzf-url
        vim-tmux-navigator
        {
          plugin = catppuccin;
          extraConfig = ''
            # Catppuccin theme
            set -g @catppuccin_flavor "mocha"

            # Menu styling options
            set -g @catppuccin_menu_selected_style "fg=#{@thm_fg},bold,bg=#{@thm_overlay_0}"

            # Pane styling options
            set -g @catppuccin_pane_left_separator "█"
            set -g @catppuccin_pane_middle_separator "█"
            set -g @catppuccin_pane_right_separator "█"
            set -g @catppuccin_pane_color "#{@thm_green}"
            set -g @catppuccin_pane_background_color "#{@thm_surface_0}"
            set -g @catppuccin_pane_default_text "##{b:pane_current_path}"
            set -g @catppuccin_pane_default_fill "number"
            set -g @catppuccin_pane_number_position "left" # right, left

            set -g @catppuccin_window_status_style "basic" # basic, rounded, slanted, custom, or none
            set -g @catppuccin_window_text_color "#{@thm_surface_0}"
            set -g @catppuccin_window_number_color "#{@thm_overlay_2}"
            set -g @catppuccin_window_text " #T"
            set -g @catppuccin_window_number "#I"
            set -g @catppuccin_window_current_text_color "#{@thm_surface_1}"
            set -g @catppuccin_window_current_number_color "#{@thm_mauve}"
            set -g @catppuccin_window_current_text " #T"
            set -g @catppuccin_window_current_number "#I"
            set -g @catppuccin_window_number_position "left"
            set -g @catppuccin_window_flags "none" # none, icon, or text
            set -g @catppuccin_window_flags_icon_last " 󰖰" # -
            set -g @catppuccin_window_flags_icon_current " 󰖯" # *
            set -g @catppuccin_window_flags_icon_zoom " 󰁌" # Z
            set -g @catppuccin_window_flags_icon_mark " 󰃀" # M
            set -g @catppuccin_window_flags_icon_silent " 󰂛" # ~
            set -g @catppuccin_window_flags_icon_activity " 󱅫" # #
            set -g @catppuccin_window_flags_icon_bell " 󰂞" # !
            # Matches icon order when using `#F` (`#!~[*-]MZ`)
            set -g @catppuccin_window_flags_icon_format "##{?window_activity_flag,#{E:@catppuccin_window_flags_icon_activity},}##{?window_bell_flag,#{E:@catppuccin_window_flags_icon_bell},}##{?window_silence_flag,#{E:@catppuccin_window_flags_icon_silent},}##{?window_active,#{E:@catppuccin_window_flags_icon_current},}##{?window_last_flag,#{E:@catppuccin_window_flags_icon_last},}##{?window_marked_flag,#{E:@catppuccin_window_flags_icon_mark},}##{?window_zoomed_flag,#{E:@catppuccin_window_flags_icon_zoom},}"

            # Status line options
            set -g @catppuccin_window_left_separator ''
            set -g @catppuccin_window_middle_separator ' █'
            set -g @catppuccin_window_right_separator ' '
            set -g @catppuccin_window_number_position 'right'
            set -g @catppuccin_window_default_fill 'number'
            set -g @catppuccin_window_default_text '#W'
            set -g @catppuccin_window_current_fill 'number'
            set -g @catppuccin_window_current_text '#W#{?window_zoomed_flag,(),}'
            set -g @catppuccin_status_modules_right 'directory session'
            set -g @catppuccin_status_left_separator  ' '
            set -g @catppuccin_status_right_separator ''
            set -g @catppuccin_status_connect_separator "no"
            set -g @catppuccin_status_fill "icon"
            set -g @catppuccin_status_module_bg_color "#{@thm_surface_0}"
          '';
        }
        yank
      ];
      catppuccin = {
        enable = false;
      };
    };
  };
}
