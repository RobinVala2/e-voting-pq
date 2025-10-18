#!/usr/bin/env bash
set -e

# --- Variables ---
REPO_URL="https://github.com/hyperion-voting/hyperion.git"
MY_PROJECT_DIR="$(pwd)"    
HYPERION_DIR="$MY_PROJECT_DIR/hyperion"  

# --- Ensure git is installed ---
if ! command -v git &> /dev/null; then
  echo "[*] Git not found, installing..."
  if [ -f /etc/debian_version ]; then
    sudo apt update && sudo apt install -y git
  elif [ -f /etc/redhat-release ]; then
    sudo dnf install -y git || sudo yum install -y git
  else
    echo "[!] Please install git manually and rerun."
    exit 1
  fi
fi

# --- Clone Hyperion repo ---
if [ ! -d "$HYPERION_DIR" ]; then
  echo "[*] Cloning Hyperion into $HYPERION_DIR ..."
  git clone "$REPO_URL" "$HYPERION_DIR"
fi

cd "$MY_PROJECT_DIR"

# --- Create virtual environment ---
if [ ! -d "$MY_PROJECT_DIR/.venv" ]; then
  echo "[*] Creating virtualenv in $MY_PROJECT_DIR/.venv..."

  if command -v python3 &> /dev/null; then
    PYTHON_BIN=$(command -v python3)
  else
    PYTHON_BIN=$(ls /usr/bin/python3.* | sort -V | tail -n 1)
  fi

  echo "[*] Using $PYTHON_BIN"
  "$PYTHON_BIN" -m venv "$MY_PROJECT_DIR/.venv"
fi

source "$MY_PROJECT_DIR/.venv/bin/activate"

# --- Install dependencies ---
echo "[*] Installing dependencies..."
pip install --upgrade pip

# e-voting-pq-main project requirements
if [ -f "$MY_PROJECT_DIR/requirements.txt" ]; then
  echo "  - Installing project requirements..."
  pip install -r "$MY_PROJECT_DIR/requirements.txt"
fi

# Hyperion requirements
if [ -f "$HYPERION_DIR/requirements.txt" ]; then
  echo "  - Installing Hyperion requirements..."
  pip install -r "$HYPERION_DIR/requirements.txt"
fi

# Hyperion dependencies
echo "  - Installing Hyperion dependencies..."
if [ ! -d "$HYPERION_DIR/threshold-crypto" ]; then
  echo "  - Cloning threshold-crypto..."
  git clone --branch v0.2.0 --depth 1 https://github.com/tompetersen/threshold-crypto.git "$HYPERION_DIR/threshold-crypto"
  cd "$HYPERION_DIR/threshold-crypto"
  pip install .
  cd "$MY_PROJECT_DIR"
fi
# --- Add Hyperion repo to PYTHONPATH ---
export PYTHONPATH="$HYPERION_DIR:$PYTHONPATH"

echo
echo "[*] Setup complete."
echo "Activate env with: source $MY_PROJECT_DIR/.venv/bin/activate"
