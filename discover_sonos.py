#!/usr/bin/env python3
"""Discover Sonos speakers on your network"""

import soco

print("Discovering Sonos speakers...")
speakers = soco.discover()

if speakers:
    print(f"\nFound {len(speakers)} Sonos speaker(s):\n")
    for speaker in speakers:
        print(f"  Name: {speaker.player_name}")
        print(f"  IP:   {speaker.ip_address}")
        try:
            info = speaker.get_speaker_info()
            print(f"  Model: {info.get('model_name', 'Unknown')}")
        except:
            print(f"  Model: Unknown")
        print()
else:
    print("No Sonos speakers found.")
    print("Make sure your Mac and Sonos are on the same WiFi network.")
