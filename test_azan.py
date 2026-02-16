#!/usr/bin/env python3
"""Test Azan playback on Sonos"""

import json
from azan_scheduler import AzanScheduler

print("Testing Azan on Sonos...\n")

scheduler = AzanScheduler()

# Test Sonos connection
print("1. Connecting to Sonos...")
if scheduler.discover_sonos():
    print(f"   ✓ Connected to: {scheduler.sonos_device.player_name}\n")
else:
    print("   ✗ Failed to connect to Sonos")
    exit(1)

# Test prayer times fetch
print("2. Fetching prayer times...")
if scheduler.fetch_prayer_times():
    print("   ✓ Prayer times fetched successfully\n")
    for prayer, time in scheduler.prayer_times.items():
        print(f"   {prayer}: {time.strftime('%I:%M %p')}")
else:
    print("   ✗ Failed to fetch prayer times")
    exit(1)

# Test playing Azan
print("\n3. Playing Azan (Test)...")
input("   Press Enter to play the Azan track on your Sonos... ")
scheduler.play_azan("Fajr")  # Use actual prayer name
print("   ✓ Azan should be playing now!")
print("\nTest complete!")
