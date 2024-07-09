
alias vim nvim
alias c clear
alias ls eza
alias ip "ip -c"
alias la "ls -la"

# If we're running in WSL, we need to use wsl-notify-send to show notifications
if cat /proc/version | grep "microsoft.*WSL"
    function notify-send
        wsl-notify-send.exe --category $WSL_DISTRO_NAME "$argv"
    end
end

if status is-interactive
    # Commands to run in interactive sessions can go here
    atuin init fish | source
end

function reload-config
    source ~/.config/fish/config.fish
end

starship init fish | source
thefuck --alias | source
zoxide init fish | source

# pnpm
set -gx PNPM_HOME "/home/hadronomy/.local/share/pnpm"
set -gx PATH "$PNPM_HOME" $PATH
# pnpm end
set -gx VOLTA_HOME "$HOME/.volta"
set -gx PATH "$VOLTA_HOME/bin" $PATH

# bun
set --export BUN_INSTALL "$HOME/.bun"
set --export PATH $BUN_INSTALL/bin $PATH

# Created by `pipx` on 2024-02-02 13:45:27
set PATH $PATH /home/hadronomy/.local/bin
