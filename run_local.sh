#!/usr/bin/env bash
# Run EngineLab locally at http://localhost:8501
# Usage: bash run_local.sh [--recompute]
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Prefer anaconda Python (3.12, has all deps); fall back to python3
PYTHON="${PYTHON:-}"
if [ -z "$PYTHON" ]; then
  for candidate in \
      /opt/anaconda3/bin/python3.12 \
      /opt/homebrew/bin/python3.12 \
      /usr/local/bin/python3.12 \
      python3.12 python3; do
    if command -v "$candidate" &>/dev/null; then
      PYTHON="$candidate"
      break
    fi
  done
fi

if [ -z "$PYTHON" ]; then
  echo "ERROR: Python 3.10+ not found. Install via anaconda or homebrew." >&2
  exit 1
fi

echo "Using Python: $($PYTHON --version 2>&1)"

# Install missing deps quietly
$PYTHON -m pip install -q streamlit chess tqdm pandas numpy plotly 2>/dev/null || true

# Optionally re-run pre-compute (adds ~3 min with parallelism)
if [[ "$1" == "--recompute" ]]; then
  echo ""
  echo "Running depth=2 tournament pre-compute (this takes ~3 min)..."
  $PYTHON scripts/precompute_tournaments.py
  echo ""
fi

echo ""
echo "Starting EngineLab at http://localhost:8501"
echo "Press Ctrl+C to stop."
echo ""

$PYTHON -m streamlit run ui/app.py --server.port 8501 --server.headless false
