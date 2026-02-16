#!/bin/bash
# Quick pause scripts for common scenarios

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
source venv/bin/activate

case "${1:-pause}" in
    "call")
        # Pause for 30 minutes (typical call duration)
        echo "📞 Pausing Azan for phone call (30 minutes)..."
        python control_azan.py pause -m 30
        ;;
    "guests")
        # Pause for 2 hours (typical guest visit)
        echo "👥 Pausing Azan for guests (2 hours)..."
        python control_azan.py pause -m 120
        ;;
    "1h")
        # Pause for 1 hour
        echo "⏰ Pausing Azan for 1 hour..."
        python control_azan.py pause -m 60
        ;;
    "stop")
        # Stop current playback immediately
        echo "⏹️  Stopping current Azan..."
        python control_azan.py stop
        ;;
    *)
        # Pause indefinitely
        echo "⏸️  Pausing Azan indefinitely..."
        python control_azan.py pause
        ;;
esac
