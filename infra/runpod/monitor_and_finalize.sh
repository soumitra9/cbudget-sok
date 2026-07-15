#!/usr/bin/env bash
# Poll pod experiment progress; launch E1-sensitivity after E1b; sync + analyze when all done.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CONN_ENV="${REPO_ROOT}/results/runpod_connection.env"
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"

if [[ -f "$CONN_ENV" ]]; then
  # shellcheck disable=SC1090
  source "$CONN_ENV"
fi

POD_IP="${POD_IP:-${1:-}}"
if [[ -z "$POD_IP" ]]; then
  echo "ERROR: POD_IP required (set in runpod_connection.env or pass as arg)" >&2
  exit 2
fi

SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519_personal}"
SSH_OPTS=(-o StrictHostKeyChecking=no -o ConnectTimeout=15 -i "$SSH_KEY" -p "${RUNPOD_SSH_PORT:-22}")

pod_python() {
  runpod_ssh "root@${POD_IP}" "$@"
}

count_complete() {
  local exp="$1"
  pod_python "cd /workspace/cbudget && python3 -c \"
import glob
exp = '${exp}'
print(len([p for p in glob.glob(f'runs/{exp}/*/status.json') if '.attempt' not in p]))
\""
}

matrix_running() {
  pod_python "cd /workspace/cbudget && .venv/bin/python3 -c \"
import subprocess
out = subprocess.run(['ps','-eo','args='], capture_output=True, text=True, check=False)
running = any('python' in line and 'scripts.run_matrix' in line and 'ps -eo' not in line for line in out.stdout.splitlines())
print('yes' if running else 'no')
\""
}

launch_sensitivity() {
  echo "Launching E1-sensitivity matrix on pod..."
  pod_python bash -s <<'REMOTE'
set -euo pipefail
cd /workspace/cbudget
export CBUDGET_BACKEND=vllm
export VLLM_BASE_URL=http://127.0.0.1:8000
export CBUDGET_MODEL_CONFIG=qwen2.5_coder_7b_instruct
if ps -eo args= | grep -qE '^.*python.*scripts\.run_matrix'; then
  echo "run_matrix already running; skip launch"
  exit 0
fi
nohup uv run python -m scripts.run_matrix experiment=e1_sensitivity \
  preregistration=configs/hypotheses/e1_frozen.yaml --preflight \
  > /tmp/e1_sensitivity_matrix.log 2>&1 &
echo "PID=$!"
REMOTE
}

E1B_EXPECT=48
SENS_EXPECT=24

E1B_DONE="$(count_complete e1b_rtk_cod)"
SENS_DONE="$(count_complete e1_sensitivity)"
RUNNING="$(matrix_running)"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] pod=${POD_IP} e1b=${E1B_DONE}/${E1B_EXPECT} sensitivity=${SENS_DONE}/${SENS_EXPECT} matrix_running=${RUNNING}"

if [[ "$E1B_DONE" -lt "$E1B_EXPECT" ]]; then
  echo "WAIT: E1b not complete"
  exit 1
fi

if [[ "$SENS_DONE" -eq 0 && "$RUNNING" == "no" ]]; then
  launch_sensitivity
  echo "WAIT: E1-sensitivity just launched"
  exit 1
fi

if [[ "$SENS_DONE" -lt "$SENS_EXPECT" ]]; then
  echo "WAIT: E1-sensitivity not complete"
  exit 1
fi

if [[ "$RUNNING" == "yes" ]]; then
  echo "WAIT: matrix still running after counts met"
  exit 1
fi

echo "All experiments complete — syncing and running analysis pipeline..."
bash "${REPO_ROOT}/infra/runpod/sync_results.sh" "$POD_IP"

cd "$REPO_ROOT"
if [[ -d .venv ]]; then
  PY="${REPO_ROOT}/.venv/bin/python"
else
  PY=python3
fi

"$PY" -m scripts.run_analysis_pipeline
"$PY" -m scripts.validate_accounting --config configs/validation/accounting.yaml --runs runs/e1_rtk_compaction || true

echo "POD_EXPERIMENTS_COMPLETE e1b=${E1B_DONE} sensitivity=${SENS_DONE}"
