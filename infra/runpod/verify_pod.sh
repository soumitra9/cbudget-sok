#!/usr/bin/env bash
# One-shot pod readiness check from local machine.
set -euo pipefail
POD_IP="${1:?pod ip required}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
# shellcheck source=pins.env
source "$(dirname "$0")/pins.env"

echo "Checking pod ${POD_IP}..."

runpod_ssh "root@${POD_IP}" bash -s <<REMOTE
set -euo pipefail
export PATH="/root/.local/bin:/root/.cargo/bin:\${PATH}"
fail=0
check() { if eval "\$2"; then echo "[ok] \$1"; else echo "[FAIL] \$1"; fail=1; fi; }

check "vllm env" "test -x ${VLLM_ENV}/bin/vllm"
check "vllm import + cuda" "${VLLM_ENV}/bin/python -c 'import vllm,torch; assert torch.cuda.is_available()'"
check "cbudget venv" "test -d ${CBUDGET_DIR}/.venv"
check "rtk binary" "test -x ${CBUDGET_DIR}/external/rtk/target/release/rtk"
check "vllm server" "curl -sf http://127.0.0.1:8000/v1/models >/dev/null"

exit \$fail
REMOTE

echo "Pod verification passed."
