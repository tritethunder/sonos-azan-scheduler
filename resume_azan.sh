#!/bin/bash
# Resume Azan scheduler

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
source venv/bin/activate

echo "▶️  Resuming Azan scheduler..."
python control_azan.py resume
