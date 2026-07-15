#!/usr/bin/env bash
set -euo pipefail
MODEL_CONFIG="${1:?model config path required}"
POD_IP="${2:?pod ip required}"
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

REVISION=$(python3 -c "import yaml; from pathlib import Path; c=yaml.safe_load(Path('${REPO_ROOT}/${MODEL_CONFIG}').read_text()); print(c.get('revision') or '')")
REPO=$(python3 -c "import yaml; from pathlib import Path; c=yaml.safe_load(Path('${REPO_ROOT}/${MODEL_CONFIG}').read_text()); print(c['repository'])")

runpod_ssh "root@${POD_IP}" bash -s <<REMOTE
set -euo pipefail
VLLM_BIN="${VLLM_ENV}/bin/vllm"
if [[ ! -x "\$VLLM_BIN" ]]; then
  echo "Missing vllm at \$VLLM_BIN. Run bootstrap.sh first." >&2
  exit 1
fi
pkill -f "vllm serve" || true
sleep 2
nohup "\$VLLM_BIN" serve ${REPO} \\
  ${REVISION:+--revision ${REVISION} } \\
  --dtype bfloat16 \\
  --max-model-len 32768 \\
  --enable-prefix-caching \\
  --gpu-memory-utilization 0.85 \\
  --host 0.0.0.0 \\
  --port 8000 \\
  > /workspace/cbudget/vllm_server.log 2>&1 &
echo "vLLM starting on port 8000 (log: /workspace/cbudget/vllm_server.log)"
REMOTE

bash "$(dirname "$0")/wait_vllm.sh" "${POD_IP}" 600
