#!/usr/bin/env bash
# Personal SSH key for RunPod (not Autodesk/corporate git keys).
RUNPOD_SSH_KEY="${RUNPOD_SSH_KEY:-$HOME/.ssh/id_ed25519_personal}"
RUNPOD_SSH_PUB="${RUNPOD_SSH_PUB:-$HOME/.ssh/id_ed25519_personal.pub}"
RUNPOD_SSH_PORT="${RUNPOD_SSH_PORT:-22}"
export RUNPOD_SSH_OPTS=(
  -i "$RUNPOD_SSH_KEY"
  -p "$RUNPOD_SSH_PORT"
  -o StrictHostKeyChecking=no
  -o IdentitiesOnly=yes
  -o ServerAliveInterval=30
  -o ServerAliveCountMax=10
)

runpod_ssh() {
  ssh "${RUNPOD_SSH_OPTS[@]}" "$@"
}

runpod_rsync() {
  rsync -e "ssh -i ${RUNPOD_SSH_KEY} -p ${RUNPOD_SSH_PORT} -o StrictHostKeyChecking=no -o IdentitiesOnly=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=10" "$@"
}
