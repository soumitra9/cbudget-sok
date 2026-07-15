#!/usr/bin/env bash
# Pull runs/ and results/ from pod to local machine.
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

mkdir -p "${REPO_ROOT}/runs" "${REPO_ROOT}/results"
echo "Syncing runs/ and results/ from ${POD_IP}..."
runpod_rsync -az "root@${POD_IP}:/workspace/cbudget/runs/" "${REPO_ROOT}/runs/"
runpod_rsync -az "root@${POD_IP}:/workspace/cbudget/results/" "${REPO_ROOT}/results/"
echo "Sync complete."
