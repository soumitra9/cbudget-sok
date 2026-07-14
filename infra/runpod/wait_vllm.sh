#!/usr/bin/env bash
# Poll vLLM /v1/models on the pod until ready or timeout.
set -euo pipefail
POD_IP="${1:?pod ip required}"
TIMEOUT_SEC="${2:-600}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"

runpod_ssh "root@${POD_IP}" bash -s <<REMOTE
set -euo pipefail
deadline=\$(( \$(date +%s) + ${TIMEOUT_SEC} ))
while [[ \$(date +%s) -lt \$deadline ]]; do
  if curl -sf http://127.0.0.1:8000/v1/models >/dev/null 2>&1; then
    echo "vLLM ready"
    curl -s http://127.0.0.1:8000/v1/models | head -c 400
    exit 0
  fi
  if ! pgrep -f "vllm serve" >/dev/null 2>&1; then
    echo "vLLM process exited"
    tail -30 /workspace/cbudget/vllm_server.log 2>/dev/null || true
    exit 1
  fi
  sleep 10
done
echo "vLLM timeout after ${TIMEOUT_SEC}s"
tail -20 /workspace/cbudget/vllm_server.log 2>/dev/null || true
exit 1
REMOTE
