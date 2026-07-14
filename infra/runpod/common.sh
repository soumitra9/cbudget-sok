#!/usr/bin/env bash
# Personal SSH key for RunPod (not Autodesk/corporate git keys).
RUNPOD_SSH_KEY="${RUNPOD_SSH_KEY:-$HOME/.ssh/id_ed25519_personal}"
RUNPOD_SSH_PUB="${RUNPOD_SSH_PUB:-$HOME/.ssh/id_ed25519_personal.pub}"
export RUNPOD_SSH_OPTS=(
  -i "$RUNPOD_SSH_KEY"
  -o StrictHostKeyChecking=no
  -o IdentitiesOnly=yes
)

runpod_ssh() {
  ssh "${RUNPOD_SSH_OPTS[@]}" "$@"
}

runpod_rsync() {
  rsync -e "ssh ${RUNPOD_SSH_OPTS[*]}" "$@"
}
