# Worktrunk (wt): git worktree management for parallel agent workflows.
{ flakePkgs, ... }:
{
  home.packages = [ flakePkgs.worktrunk ];

  # User config applies to every repo. post-start runs in the background when
  # a worktree is created; copy-ignored brings gitignored files (target/,
  # node_modules/, .env) over from the primary worktree with per-file reflink,
  # so blocks are shared until modified and the copy costs almost no disk.
  # --require-include makes it opt-in per repo via a .worktreeinclude file,
  # matching Claude Code desktop; a repo without the file copies nothing.
  xdg.configFile."worktrunk/config.toml".text = ''
    post-start = "wt step copy-ignored --require-include"
  '';
}
