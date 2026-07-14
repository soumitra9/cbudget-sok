#!/usr/bin/env bash
set -euo pipefail
MODEL_CONFIG="${1:?model config path required}"
POD_IP="${2:?pod ip required}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"

REVISION=$(python3 -c "import yaml; from pathlib import Path; c=yaml.safe_load(Path('${REPO_ROOT}/${MODEL_CONFIG}').read_text()); print(c.get('revision') or '')")
REPO=$(python3 -c "import yaml; from pathlib import Path; c=yaml.safe_load(Path('${REPO_ROOT}/${MODEL_CONFIG}').read_text()); print(c['repository'])")

runpod_ssh "root@${POD_IP}" bash -s <<REMOTE
set -euo pipefail
export PATH="\$HOME/.local/bin:\$PATH"
pkill -f "vllm serve" || true
sleep 2
nohup vllm serve ${REPO} \\
  ${REVISION:+--revision ${REVISION} } \\
  --dtype bfloat16 \\
  --max-model-len 32768 \\
  --enable-prefix-caching \\
  --gpu-memory-utilization 0.85 \\
  --host 0.0.0.0 \\
  --port 8000 \\
  > /workspace/cbudget/vllm_server.log 2>&1 &
echo "vLLM starting on port 8000"
REMOTE
