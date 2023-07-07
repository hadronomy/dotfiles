
alias vim nvim
alias c clear
alias ls exa
alias ip "ip -c"
alias la "ls -la"

function notify-send
    wsl-notify-send.exe --category $WSL_DISTRO_NAME "$argv"
end

if status is-interactive
    # Commands to run in interactive sessions can go here
end

function reload-config
    source ~/.config/fish/config.fish
end

starship init fish | source
zoxide init fish | source

# pnpm
set -gx PNPM_HOME "/home/hadronomy/.local/share/pnpm"
set -gx PATH "$PNPM_HOME" $PATH
# pnpm end
set -gx VOLTA_HOME "$HOME/.volta"
set -gx PATH "$VOLTA_HOME/bin" $PATH
