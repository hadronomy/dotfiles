#!/bin/bash
# Deny Bash commands that point Cargo at a hand-picked cache or target directory.
#
# mbx owns those paths. It reads them from its own config and reflinks build
# output between the store and target/, which only works while both stay on the
# volume it chose. A command that sets CARGO_HOME or CARGO_TARGET_DIR moves one
# side of that pair and silently turns every build into a full copy -- or a full
# rebuild, because the cache key no longer matches.
#
# This is a hook and not a line of CLAUDE.md because an instruction lowers the
# odds of the mistake and a hook removes it. The reason text below is what the
# model reads after the block, so it names the command to run instead.
set -euo pipefail

command=$(jq -r '.tool_input.command // ""')

# Assignment only. A command that reads $CARGO_HOME is fine, and `unset` is the
# correction this hook asks for, so neither may match.
pattern='(^|[;&|(]|[[:space:]])(export[[:space:]]+|env[[:space:]]+)?(CARGO_HOME|CARGO_TARGET_DIR|CARGO_BUILD_TARGET_DIR)='

if [[ ! $command =~ $pattern ]]; then
  exit 0
fi

jq -n '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "deny",
    permissionDecisionReason: "Blocked. mbx already keeps the Cargo cache and the build output off the internal disk, and it reads those paths from its own configuration. A manual CARGO_HOME or CARGO_TARGET_DIR moves one of them and breaks the cache. Send the command again with no environment variables in front of it, and write `mbx` where you wrote `cargo`. `mbx doctor` checks the setup."
  }
}'
