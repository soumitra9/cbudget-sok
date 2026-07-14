#!/usr/bin/env bash
# Idempotent pod setup. Safe to re-run; skips completed steps.
# Intended image: runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=pins.env
source "${SCRIPT_DIR}/pins.env"

export PATH="/root/.local/bin:/root/.cargo/bin:${PATH}"

log() { echo "[pod_setup] $*"; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || return 1
}

install_base_tools() {
  if need_cmd uv && need_cmd git; then
    log "base tools already present"
    return 0
  fi
  log "installing base tools (git, curl, uv)..."
  apt-get update -qq
  apt-get install -y -qq git curl rsync build-essential >/dev/null
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="/root/.local/bin:${PATH}"
}

install_rust() {
  if need_cmd cargo; then
    log "rust already present: $(cargo --version)"
    return 0
  fi
  log "installing rust..."
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
  # shellcheck source=/dev/null
  source /root/.cargo/env
  export PATH="/root/.cargo/bin:${PATH}"
}

vllm_ready() {
  [[ -x "${VLLM_ENV}/bin/vllm" ]] || return 1
  "${VLLM_ENV}/bin/python" -c "import vllm, torch; assert torch.cuda.is_available()" >/dev/null 2>&1
}

install_vllm_env() {
  if vllm_ready; then
    log "vllm env ready: $("${VLLM_ENV}/bin/python" -c "import vllm,torch; print('vllm', vllm.__version__, 'torch', torch.__version__)")"
    return 0
  fi
  log "creating vllm env at ${VLLM_ENV} (inherits system torch cu128)..."
  rm -rf "${VLLM_ENV}"
  python3 -m venv "${VLLM_ENV}" --system-site-packages
  "${VLLM_ENV}/bin/pip" install \
    "vllm==${VLLM_VERSION}" \
    "transformers${TRANSFORMERS_SPEC}" \
    --no-cache-dir -q
  vllm_ready || { log "ERROR: vllm env failed verification"; exit 1; }
  log "vllm env installed: $("${VLLM_ENV}/bin/python" -c "import vllm,torch; print('vllm', vllm.__version__, 'torch', torch.__version__)")"
}

sync_cbudget() {
  log "syncing cbudget harness (no vllm/torch in this venv)..."
  cd "${CBUDGET_DIR}"
  uv sync --all-extras
  log "cbudget venv size: $(du -sh .venv | cut -f1)"
}

rtk_ready() {
  [[ -x "${CBUDGET_DIR}/external/rtk/target/release/rtk" ]]
}

install_rtk() {
  if rtk_ready; then
    log "rtk already built"
    return 0
  fi
  cd "${CBUDGET_DIR}"
  mkdir -p external/rtk
  # Pre-baked image path (see infra/runpod/Dockerfile)
  if [[ -x /opt/rtk/target/release/rtk ]]; then
    log "using pre-baked rtk from /opt/rtk"
    rm -rf external/rtk
    ln -sf /opt/rtk external/rtk
    rtk_ready && return 0
  fi
  install_rust
  if [[ ! -f external/rtk/Cargo.toml ]]; then
    log "cloning rtk at ${RTK_PINNED_COMMIT}..."
    git clone https://github.com/rtk-ai/rtk.git external/rtk
    git -C external/rtk checkout "${RTK_PINNED_COMMIT}"
  fi
  log "building rtk..."
  cd external/rtk && cargo build --release
  rtk_ready || { log "ERROR: rtk build failed"; exit 1; }
  log "rtk ready: ${CBUDGET_DIR}/external/rtk/target/release/rtk"
}

write_marker() {
  local marker="${CBUDGET_DIR}/.pod_setup_done"
  {
    echo "POD_IMAGE=${POD_IMAGE}"
    echo "VLLM_VERSION=${VLLM_VERSION}"
    echo "TRANSFORMERS_SPEC=${TRANSFORMERS_SPEC}"
    echo "RTK_PINNED_COMMIT=${RTK_PINNED_COMMIT}"
    date -u +"%Y-%m-%dT%H:%M:%SZ"
  } > "${marker}"
  log "marker written: ${marker}"
}

main() {
  install_base_tools
  install_vllm_env
  sync_cbudget
  install_rtk
  write_marker
  log "pod setup complete"
}

main "$@"
