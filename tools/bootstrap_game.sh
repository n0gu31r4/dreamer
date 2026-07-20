#!/usr/bin/env bash
# Start a new game lab: install the dreamer starter kit into a target directory.
#
# Copies:
#   skills/     — snapshot of the skill library (isolation for cold tests,
#                 provenance for grading; lessons fold back into dreamer's
#                 copies after the run)
#   .claude/    — the /kickstart command (single entry point, state-detecting)
#                 + lab settings (model: sonnet)
#
# Usage: tools/bootstrap_game.sh <target-dir>
#   e.g. tools/bootstrap_game.sh ../element-bending-arena

set -euo pipefail

DREAMER_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:?usage: bootstrap_game.sh <target-dir>}"

if [ -e "$TARGET/skills" ]; then
  echo "error: $TARGET/skills already exists — refusing to overwrite the snapshot" >&2
  exit 1
fi

mkdir -p "$TARGET/.claude"
cp -r "$DREAMER_DIR/skills" "$TARGET/skills"
cp -r "$DREAMER_DIR/lab-template/.claude/." "$TARGET/.claude/"

echo "Lab starter kit installed in $TARGET:"
echo "  skills/    skill snapshot: $(ls "$DREAMER_DIR/skills" | tr '\n' ' ')"
echo "  .claude/   /kickstart command + lab settings (model: sonnet)"
echo
echo "Next: cd $TARGET && claude    then type /kickstart"
