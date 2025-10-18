#!/usr/bin/env bash
# Run the Hyperion Admin GUI
cd "$(dirname "$0")"
MY_PROJECT_DIR="$(pwd)"
HYPERION_DIR="$MY_PROJECT_DIR/hyperion"

# Activate virtual environment
source "$MY_PROJECT_DIR/.venv/bin/activate"

# Set PYTHONPATH to include Hyperion and project root
export PYTHONPATH="$HYPERION_DIR:$MY_PROJECT_DIR:$PYTHONPATH"

# Run the admin GUI
echo "[*] Starting Hyperion Admin GUI..."
cd "$MY_PROJECT_DIR"
python -m client.admin_gui

