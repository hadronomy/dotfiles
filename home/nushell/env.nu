# pnpm
$env.PNPM_HOME = $"($env.HOME)/.local/share/pnpm"

# cargo
$env.CARGO_HOME = $"($env.HOME)/.cargo"

# android
$env.ANDROID_HOME = $"($env.HOME)/android-sdk"

# go
$env.GOPATH = $"($env.HOME)/.go"

$env.FZF_DEFAULT_COMMAND = "fd --hidden --strip-cwd-prefix --exclude .git"
$env.FZF_CTRL_T_COMMAND = $env.FZF_DEFAULT_COMMAND

$env.PATH = ( 
  $env.PATH 
    | split row (char esep)
    | append /usr/local/bin
    | append ($env.CARGO_HOME | path join bin)
    | prepend ($env.PNPM_HOME)
    | append ($env.HOME | path join .go bin)
    | append ($env.HOME | path join .surrealdb)
    | append ($env.HOME | path join .local bin)
    | append ($env.HOME | path join .rvm bin)
    | append ($env.HOME | path join android-sdk cmdline-tools bin)
    | uniq
)