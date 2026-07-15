#!/usr/bin/env bash
# Pull a pinned Git SHA onto the pod without re-bootstrapping the full environment.
set -euo pipefail
POD_IP="${1:?pod ip required}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CONN_ENV="${REPO_ROOT}/results/runpod_connection.env"
if [[ -f "$CONN_ENV" && -z "${RUNPOD_SSH_PORT:-}" ]]; then
  RUNPOD_SSH_PORT="$(grep '^RUNPOD_SSH_PORT=' "$CONN_ENV" | cut -d= -f2)"
  export RUNPOD_SSH_PORT
fi
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
# shellcheck source=pins.env
source "$(dirname "$0")/pins.env"

REF="${CBUDGET_REPO_REF:-main}"
echo "Updating harness on ${POD_IP} to ref ${REF}"
runpod_ssh "root@${POD_IP}" bash -s <<REMOTE
set -euo pipefail
cd ${CBUDGET_DIR}
git fetch origin
git checkout main 2>/dev/null || git checkout -b main
git reset --hard "${REF}"
git clean -fd
echo "Harness updated to \$(git rev-parse --short HEAD)"
REMOTE
