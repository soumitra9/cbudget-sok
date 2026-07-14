#!/usr/bin/env bash
set -euo pipefail
POD_IP="${1:?pod ip required}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"

echo "Bootstrapping pod ${POD_IP} with uv (SSH key: ${RUNPOD_SSH_KEY})..."

runpod_ssh "root@${POD_IP}" bash -s <<'REMOTE'
set -euo pipefail
apt-get update -qq && apt-get install -y -qq git curl rsync build-essential >/dev/null 2>&1 || true
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
REMOTE

runpod_rsync -az --exclude='runs/' --exclude='workspaces/' --exclude='.git/' --exclude='.venv/' \
  "${REPO_ROOT}/" "root@${POD_IP}:/workspace/cbudget/"

runpod_ssh "root@${POD_IP}" bash -s <<'REMOTE'
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
cd /workspace/cbudget
uv sync --all-extras
if [ -d external/rtk/Cargo.toml ]; then
  cd external/rtk
  cargo build --release
  cd /workspace/cbudget
fi
echo "Bootstrap complete (uv venv at .venv)."
REMOTE
