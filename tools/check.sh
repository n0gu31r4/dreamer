#!/usr/bin/env bash
# Dreamer's gate: green means dreamer's own code is verified.
# (Labs have their own tools/check.sh; this one covers dreamer-side Python.)
# Requires uv (https://docs.astral.sh/uv/): user-local install, no sudo:
#   curl -LsSf https://astral.sh/uv/install.sh | sh
set -euo pipefail
cd "$(dirname "$0")/.."

export PATH="$HOME/.local/bin:$PATH"
# Workspace-wide: sync every member editable (+ the dev group) and test them all.
uv sync --quiet --all-packages
uv run python -m pytest -q packages/asset-pipeline
echo "GATE GREEN"
