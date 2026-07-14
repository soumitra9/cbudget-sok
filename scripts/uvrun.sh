#!/usr/bin/env bash
# Run cbudget commands inside the project uv environment (no global pip pollution).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
uv sync --all-extras
exec uv run "$@"
