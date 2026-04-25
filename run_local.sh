#!/usr/bin/env bash
# Run EngineLab locally at http://localhost:8501
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create venv if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt -q

echo ""
echo "Starting EngineLab at http://localhost:8501"
echo "Press Ctrl+C to stop."
echo ""

streamlit run ui/app.py --server.port 8501 --server.headless false
