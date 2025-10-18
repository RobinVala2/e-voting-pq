#!/usr/bin/env bash
cd "$(dirname "$0")"
MY_PROJECT_DIR="$(pwd)"
HYPERION_DIR="$MY_PROJECT_DIR/hyperion"

# Activate virtual environment
source "$MY_PROJECT_DIR/.venv/bin/activate"

# Set PYTHONPATH to include Hyperion and project root
export PYTHONPATH="$HYPERION_DIR:$MY_PROJECT_DIR:$PYTHONPATH"

# Run the server as a module (to handle relative imports)
echo "[*] Starting Hyperion e-voting server..."
cd "$MY_PROJECT_DIR"
python -m server.app

