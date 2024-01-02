set IS_WSL (uname -r | grep "microsoft" > /dev/null; echo $status) 

# Check if fish is running in wsl
if test $IS_WSL != "0"
    exit
end

set SSH_AUTH_SOCK $HOME/.ssh/agent.sock
export SSH_AUTH_SOCK

set ALREADY_RUNNING (ps -auxww | grep -q "[n]piperelay.exe -ei -s //./pipe/openssh-ssh-agent"; echo $status)
if test $ALREADY_RUNNING != "0"
    if test -e $SSH_AUTH_SOCK
        echo "Removing previous socket..."
        rm $SSH_AUTH_SOCK
    end
    echo "Starting SSH-Agent relay..."
    setsid socat UNIX-LISTEN:$SSH_AUTH_SOCK,fork EXEC:"npiperelay.exe -ei -s //./pipe/openssh-ssh-agent",nofork &> /dev/null 2>&1
end

