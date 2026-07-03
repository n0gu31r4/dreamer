#!/usr/bin/env bash
# Dreamer's gate: green means dreamer's own code is verified.
# (Labs have their own tools/check.sh; this one covers dreamer-side Python.)
# Requires uv (https://docs.astral.sh/uv/): user-local install, no sudo:
#   curl -LsSf https://astral.sh/uv/install.sh | sh
set -euo pipefail
cd "$(dirname "$0")/.."

export PATH="$HOME/.local/bin:$PATH"
uv sync --quiet --extra dev
uv run python -m pytest -q
echo "GATE GREEN"
