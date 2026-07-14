#!/usr/bin/env bash
set -euo pipefail
POD_IP="${1:?pod ip required}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"

# shellcheck source=pins.env
source "$(dirname "$0")/pins.env"
export CBUDGET_REPO_REF

echo "Bootstrapping pod ${POD_IP}:${RUNPOD_SSH_PORT} (repo ref: ${CBUDGET_REPO_REF})..."

# Clone or update repo first so pod_setup.sh is available on the pod.
runpod_ssh "root@${POD_IP}" bash -s <<REMOTE
set -euo pipefail
export PATH="/root/.local/bin:\${PATH}"
REF="${CBUDGET_REPO_REF:-main}"
if [[ -d /workspace/cbudget/.git ]]; then
  cd /workspace/cbudget
  git fetch origin main
  git checkout "$REF"
else
  rm -rf /workspace/cbudget
  git clone https://github.com/soumitra9/cbudget-sok.git /workspace/cbudget
  cd /workspace/cbudget
  git checkout "$REF"
fi
REMOTE

# Idempotent setup: vllm env on /root (overlay), tiny cbudget venv, rtk build.
runpod_ssh "root@${POD_IP}" "bash /workspace/cbudget/infra/runpod/pod_setup.sh"

echo "Bootstrap complete. Launch vLLM with:"
echo "  bash infra/runpod/launch_vllm.sh configs/models/qwen2.5_7b_instruct.yaml ${POD_IP}"
