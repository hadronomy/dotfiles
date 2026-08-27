# Global agent instructions, shared by every harness.
#
# Claude Code reads ~/.claude/CLAUDE.md. Codex reads ~/.codex/AGENTS.md and
# OpenCode reads ~/.config/opencode/AGENTS.md. All three get the same file, so
# there is one document to edit rather than three to keep in sync.
#
# mkOutOfStoreSymlink rather than a plain .source: these are edited constantly,
# often by an agent mid-session, and a nix store path is read-only. This links
# to the working copy, so an edit lands in the repo as an ordinary diff. Same
# reasoning as home/neovim.
{ config, ... }:
let
  inherit (config.lib.file) mkOutOfStoreSymlink;
  agents = "${config.home.homeDirectory}/.dotfiles/home/agents";
in
{
  home.file = {
    ".claude/CLAUDE.md".source = mkOutOfStoreSymlink "${agents}/CLAUDE.md";

    # Referenced from CLAUDE.md by absolute path, so it has to sit beside it.
    ".claude/forbidden.md".source = mkOutOfStoreSymlink "${agents}/forbidden.md";

    ".codex/AGENTS.md".source = mkOutOfStoreSymlink "${agents}/CLAUDE.md";
    ".config/opencode/AGENTS.md".source = mkOutOfStoreSymlink "${agents}/CLAUDE.md";
  };

  # ~/.claude/settings.json is deliberately absent. Claude Code writes to it at
  # runtime -- installing a plugin, switching theme or model all rewrite the
  # file -- so managing it here would either lose those writes on the next
  # switch or fail outright against a read-only path. settings.local.json is
  # machine-local by design and stays unmanaged for the same reason.
}
