#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
for script in fig1_taxonomy.py fig2_c4_amplification.py fig3_anatomy.py fig4_e1_cells.py fig5_e1b_cells.py fig6_sac.py; do
  python3 "$script"
done
