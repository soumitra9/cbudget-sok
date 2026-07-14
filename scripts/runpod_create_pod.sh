#!/usr/bin/env bash
# Create RunPod A40 pod with personal SSH key (not Autodesk/corporate).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=../infra/runpod/common.sh
source "$ROOT/infra/runpod/common.sh"

if [[ ! -f "$RUNPOD_SSH_PUB" ]]; then
  echo "Missing personal SSH public key: $RUNPOD_SSH_PUB" >&2
  exit 1
fi

API_KEY="${RUNPOD_API_KEY:-}"
if [[ -z "$API_KEY" ]]; then
  API_KEY=$(python3 -c "import json; from pathlib import Path; print(json.load(Path('$ROOT/../.cursor/mcp.json').open())['mcpServers']['runpod']['env']['RUNPOD_API_KEY'])")
fi

PUBKEY=$(cat "$RUNPOD_SSH_PUB")
export PUBKEY
PAYLOAD=$(python3 -c "
import json, os
print(json.dumps({
  'name': 'cbudget-sok-a40',
  'imageName': 'runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404',
  'gpuTypeIds': ['NVIDIA A40'],
  'gpuCount': 1,
  'containerDiskInGb': 60,
  'volumeInGb': 20,
  'volumeMountPath': '/workspace',
  'ports': ['22/tcp', '8000/http'],
  'cloudType': 'SECURE',
  'env': {'PUBLIC_KEY': os.environ['PUBKEY']},
}))
")

echo "Creating pod cbudget-sok-a40 (A40, personal SSH: $RUNPOD_SSH_PUB)..."
RESP=$(curl -s -w "\nHTTP:%{http_code}" -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" -d "$PAYLOAD" "https://rest.runpod.io/v1/pods")
HTTP=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
echo "$HTTP"
if [[ "$HTTP" != *200* && "$HTTP" != *201* ]]; then
  exit 1
fi
POD_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
echo "Pod ID: $POD_ID"
echo "$POD_ID" > "$ROOT/results/runpod_pod_id.txt"
