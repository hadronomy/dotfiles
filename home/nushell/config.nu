
# The default config record. This is where much of your global configuration is setup.
$env.config = {
    show_banner: false # true or false to enable or disable the welcome banner at startup
    use_kitty_protocol: true # true or false to enable or disable the kitty protocol
    ls: {
        use_ls_colors: true # use the LS_COLORS environment variable to colorize output
        clickable_links: true # enable or disable clickable links. Your terminal has to support links.
    }
    rm: {
        always_trash: false # always act as if -t was given. Can be overridden with -p
    }
    cursor_shape: {
        emacs: line # block, underscore, line, blink_block, blink_underscore, blink_line, inherit to skip setting cursor shape (line is the default)
        vi_insert: line # block, underscore, line, blink_block, blink_underscore, blink_line, inherit to skip setting cursor shape (block is the default)
        vi_normal: underscore # block, underscore, line, blink_block, blink_underscore, blink_line, inherit to skip setting cursor shape (underscore is the default)
    }
    keybindings: [
      {
        name: "reload_config"
        modifier: "none"
        keycode: "f5"
        mode: ["emacs", "vi_normal", "vi_insert"]
        event: {
            send: "executehostcommand"
            cmd: "clear;source '($nu.config-path)';print 'Config reloaded.\n'"
        }
      }
    ]
}

# Uses fzf to search for a file in the current directory or
# the directory passed as an argument
def se [
  path: path = "."
] {
  nvim (fzf -m --preview "bat --color=always {}" --walker-root $path)
}

# The `google` command searches Google via a Gemini AI prompt and summarizes results.
# It requires the 'gemini' command-line tool to be installed and configured.
def google [
    query: string # The search query to pass to Google.
] {
    let gemini_prompt = $"Search google for <query>($query)</query> and summarize the results"
    let search_results = (^gemini -p $"($gemini_prompt)") | lines | str join " "
    print $"Search results summary for: ($query)\n\n($search_results)"
}

# use bash-env as a module rather than plugin
# This is replaced by nix with the correct path
# use NIX_BASH_ENV_NU_MODULE

if ('/etc/profile.d/nix.sh' | path exists) {
  bash-env /etc/profile.d/nix.sh | load-env
}

$env.LS_COLORS = (vivid generate catppuccin-mocha | str trim)
