#!/usr/bin/env bash
set -euo pipefail
POD_IP="${1:?pod ip required}"
DEST="${2:-runs/_server_artifacts}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"

mkdir -p "${REPO_ROOT}/${DEST}"
echo "Fetch server artifacts from ${POD_IP} into ${DEST}"
runpod_ssh "root@${POD_IP}" "nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader" \
  > "${REPO_ROOT}/${DEST}/gpu_metadata.csv" 2>/dev/null \
  || echo "WARNING: gpu_metadata.csv not collected (pod unreachable?)" >&2
runpod_rsync -az "root@${POD_IP}:/workspace/cbudget/vllm_server.log" "${REPO_ROOT}/${DEST}/" \
  || echo "WARNING: vllm_server.log not collected (pod unreachable?)" >&2
