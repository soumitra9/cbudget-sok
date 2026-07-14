#!/usr/bin/env bash
set -euo pipefail
POD_IP="${1:?pod ip required}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"

echo "Sync model config and launch scripts to ${POD_IP}"
runpod_rsync -az \
  "${REPO_ROOT}/configs/" "root@${POD_IP}:/workspace/cbudget/configs/" \
  "${REPO_ROOT}/infra/runpod/" "root@${POD_IP}:/workspace/cbudget/infra/runpod/"
