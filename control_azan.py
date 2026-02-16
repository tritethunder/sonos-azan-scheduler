#!/usr/bin/env python3
"""Control Azan Scheduler - Pause, Resume, or Stop"""

import json
import os
import sys
from datetime import datetime, timedelta

# Use script directory for state file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, 'scheduler_state.json')

def read_state():
    """Read current scheduler state"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"paused": False, "pause_until": None}

def write_state(state):
    """Write scheduler state"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def pause_scheduler(duration_minutes=None):
    """Pause the scheduler"""
    state = read_state()
    state['paused'] = True

    if duration_minutes:
        pause_until = datetime.now() + timedelta(minutes=duration_minutes)
        state['pause_until'] = pause_until.isoformat()
        print(f"✓ Azan paused until {pause_until.strftime('%I:%M %p')}")
    else:
        state['pause_until'] = None
        print("✓ Azan paused indefinitely")

    write_state(state)

def resume_scheduler():
    """Resume the scheduler"""
    state = read_state()
    state['paused'] = False
    state['pause_until'] = None
    write_state(state)
    print("✓ Azan resumed")

def check_status():
    """Check current status"""
    state = read_state()

    if state['paused']:
        if state['pause_until']:
            pause_until = datetime.fromisoformat(state['pause_until'])
            if datetime.now() < pause_until:
                print(f"Status: PAUSED until {pause_until.strftime('%I:%M %p')}")
            else:
                print("Status: PAUSED (time expired, but not auto-resumed)")
        else:
            print("Status: PAUSED indefinitely")
    else:
        print("Status: RUNNING")

def stop_current_playback():
    """Stop any currently playing Azan"""
    try:
        import soco
        speaker = soco.SoCo('10.75.30.94')
        speaker.stop()
        print("✓ Stopped current playback")
    except Exception as e:
        print(f"✗ Error stopping playback: {e}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Control Azan Scheduler')
    parser.add_argument('action', choices=['pause', 'resume', 'status', 'stop'],
                        help='Action to perform')
    parser.add_argument('-m', '--minutes', type=int,
                        help='Pause duration in minutes (for pause action)')

    args = parser.parse_args()

    if args.action == 'pause':
        pause_scheduler(args.minutes)
    elif args.action == 'resume':
        resume_scheduler()
    elif args.action == 'status':
        check_status()
    elif args.action == 'stop':
        stop_current_playback()
