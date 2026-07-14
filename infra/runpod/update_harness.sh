#!/usr/bin/env bash
# Pull a pinned Git SHA onto the pod without re-bootstrapping the full environment.
set -euo pipefail
POD_IP="${1:?pod ip required}"
# shellcheck source=common.sh
source "$(dirname "$0")/common.sh"
# shellcheck source=pins.env
source "$(dirname "$0")/pins.env"

REF="${CBUDGET_REPO_REF:-main}"
echo "Updating harness on ${POD_IP} to ref ${REF}"
runpod_ssh "root@${POD_IP}" bash -s <<REMOTE
set -euo pipefail
cd /workspace/cbudget
git fetch origin
git checkout "${REF}"
echo "Harness updated to \$(git rev-parse --short HEAD)"
REMOTE
