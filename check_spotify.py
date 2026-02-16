#!/usr/bin/env python3
"""Check what's currently playing to understand the format"""

import soco

# Connect to Sonos
speaker = soco.SoCo('10.75.30.94')
print(f"Connected to: {speaker.player_name}\n")

# Try to get current track info
print("Current track info:")
try:
    track = speaker.get_current_track_info()
    print(f"  Title: {track.get('title')}")
    print(f"  URI: {track.get('uri')}")
    print(f"  Metadata: {track.get('metadata')}")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "="*50)
print("Let's try playing the Spotify track with a simpler method...")
print("="*50 + "\n")

# Try using Spotify Connect approach
track_id = '2bZ8wwkkPw6m22ZxbFl137'

# Method 1: Try with x-rincon-cpcontainer
print("Trying Spotify playback...")
try:
    # Clear queue first
    speaker.clear_queue()

    # Try adding via Spotify service
    uri = f'x-sonos-spotify:spotify%3atrack%3a{track_id}?sid=9&flags=8224&sn=7'

    speaker.avTransport.SetAVTransportURI([
        ('InstanceID', 0),
        ('CurrentURI', uri),
        ('CurrentURIMetaData', '')
    ])

    speaker.play()
    print("✓ Playback started!")

except Exception as e:
    print(f"✗ Error: {e}")
