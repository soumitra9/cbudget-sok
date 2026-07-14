#!/usr/bin/env bash
set -euo pipefail
POD_IP="${1:?pod ip required}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"

echo "Bootstrapping pod ${POD_IP}:${RUNPOD_SSH_PORT}..."

# Clone or update repo first so pod_setup.sh is available on the pod.
runpod_ssh "root@${POD_IP}" bash -s <<'REMOTE'
set -euo pipefail
export PATH="/root/.local/bin:${PATH}"
if [[ -d /workspace/cbudget/.git ]]; then
  cd /workspace/cbudget && git pull --ff-only origin main
else
  rm -rf /workspace/cbudget
  git clone https://github.com/soumitra9/cbudget-sok.git /workspace/cbudget
fi
REMOTE

# Idempotent setup: vllm env on /root (overlay), tiny cbudget venv, rtk build.
runpod_ssh "root@${POD_IP}" "bash /workspace/cbudget/infra/runpod/pod_setup.sh"

echo "Bootstrap complete. Launch vLLM with:"
echo "  bash infra/runpod/launch_vllm.sh configs/models/qwen2.5_7b_instruct.yaml ${POD_IP}"
