
# Alises
alias vim nvim
alias c clear
alias ls eza
alias ip 'ip -c'
alias la 'ls -la'

# If we're running in WSL, we need to use wsl-notify-send to show notifications
if cat /proc/version | grep 'microsoft.*WSL'
    # function notify-send
    #     wsl-notify-send.exe --category $WSL_DISTRO_NAME '$argv'
    # end
end

# Disable fish_greeting
function fish_greating
end

if status is-interactive
    # Commands to run in interactive sessions can go here
    atuin init fish | source
end

function reload-config
    source ~/.config/fish/config.fish
end

function z --wraps z --description 'use fzf and zoxide to jump'
    set dir $(
    zoxide query --list --score |
    fzf --height 40% --layout reverse --info inline \
        --nth 2.. --tac --no-sort --query '$argv' \
        --bind 'enter:become:echo {2..}'
  ) && cd '$dir'
end

set -e fish_user_paths

# Editor
set -gx EDITOR nvim

# pnpm
set -gx PNPM_HOME '/home/hadronomy/.local/share/pnpm'
set -gx PATH '$PNPM_HOME'/bin $PATH
# pnpm end

# Go
set -gx GOPATH $HOME/.go
set -gx PATH $PATH $GOPATH/bin

# Rust
set -g fish_user_paths $HOME/.cargo/bin $fish_user_paths

# bun
set --export BUN_INSTALL '$HOME/.bun'
set --export PATH $BUN_INSTALL/bin $PATH

# Created by `pipx` on 2024-02-02 13:45:27
set PATH $PATH /home/hadronomy/.local/bin


# rvm
rvm default

# Shell integrations

function starship_transient_prompt_func
    starship module character
end
starship init fish | source
enable_transience

thefuck --alias | source
zoxide init fish | source
fnm env --use-on-cd | source
