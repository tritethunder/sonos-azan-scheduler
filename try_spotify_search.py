#!/usr/bin/env python3
"""Try to play Spotify via search"""

import soco
from soco.music_services import MusicService

speaker = soco.SoCo('10.75.30.94')
print(f"Connected to: {speaker.player_name}\n")

try:
    # Get Spotify music service
    spotify = MusicService('Spotify')
    print(f"Spotify service found: {spotify.service_type}")

    # Search for the Azan track
    print("\nSearching for track...")
    # URL decode the Spotify track ID
    track_url = 'https://open.spotify.com/track/2bZ8wwkkPw6m22ZxbFl137'

    # Try to add to queue using add_to_queue
    print("Adding to queue and playing...")
    speaker.clear_queue()

    # Create a proper Spotify URI for SoCo
    from soco.data_structures import DidlMusicTrack, DidlResource

    track_id = '2bZ8wwkkPw6m22ZxbFl137'
    res = DidlResource(uri=f'x-sonos-spotify:spotify:track:{track_id}', protocol_info='sonos.com-spotify:*:audio/x-spotify:*')

    track = DidlMusicTrack(
        title='Azan',
        parent_id='',
        item_id=f'00030020spotify:track:{track_id}',
        resources=[res]
    )

    speaker.add_to_queue(track)
    speaker.play_from_queue(0)

    print("✓ Playing!")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
