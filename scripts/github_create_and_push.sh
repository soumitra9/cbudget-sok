#!/usr/bin/env bash
# Create github.com/soumitra9/cbudget-sok and push via personal SSH key.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
REPO_NAME="${GITHUB_REPO_NAME:-cbudget-sok}"
GITHUB_USER="${GITHUB_USER:-soumitra9}"
SSH_KEY="${GITHUB_SSH_KEY:-$HOME/.ssh/id_ed25519_personal}"

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "Set GITHUB_TOKEN (PAT with repo scope) or create the repo manually:" >&2
  echo "  https://github.com/new?name=${REPO_NAME}&private=true" >&2
  echo "Then: GIT_SSH_COMMAND='ssh -i ${SSH_KEY} -o IdentitiesOnly=yes' git push -u origin main" >&2
  exit 1
fi

echo "Creating ${GITHUB_USER}/${REPO_NAME}..."
HTTP=$(curl -s -o /tmp/gh_create.json -w "%{http_code}" \
  -H "Authorization: Bearer ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  -d "{\"name\":\"${REPO_NAME}\",\"description\":\"SoK Context as a Budget experiment harness\",\"private\":true}" \
  "https://api.github.com/user/repos")

if [[ "$HTTP" != "201" && "$HTTP" != "422" ]]; then
  echo "GitHub API error HTTP ${HTTP}:" >&2
  cat /tmp/gh_create.json >&2
  exit 1
fi

git remote remove origin 2>/dev/null || true
git remote add origin "git@github.com:${GITHUB_USER}/${REPO_NAME}.git"
export GIT_SSH_COMMAND="ssh -i ${SSH_KEY} -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
git push -u origin main
echo "Pushed to https://github.com/${GITHUB_USER}/${REPO_NAME}"
