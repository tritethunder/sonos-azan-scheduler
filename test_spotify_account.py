#!/usr/bin/env python3
"""Get Spotify account info from Sonos"""

import soco

speaker = soco.SoCo('10.75.30.94')
print(f"Connected to: {speaker.player_name}\n")

# Try to get Spotify account from system
print("Checking for Spotify accounts on Sonos...")
try:
    # Get all available music services
    from soco.music_services import MusicService
    import soco.music_services.music_service as ms

    # Try to find Spotify service
    services = list(ms.MusicService.get_all_music_services_names())
    print(f"Available services: {services}\n")

    # Get Spotify
    if 'Spotify' in services:
        spotify_service = MusicService('Spotify')
        print(f"Spotify Service Type: {spotify_service.service_type}")
        print(f"Spotify Service ID: {spotify_service.service_id}")

        # Get account - try different methods
        try:
            accounts = list(spotify_service.available_accounts)
            if accounts:
                account = accounts[0]
                print(f"Account Serial: {account.serial_number}")
                print(f"Account Metadata: {account.metadata if hasattr(account, 'metadata') else 'N/A'}")
            else:
                print("No accounts found, trying without account...")
                account = None
        except:
            print("Using service without specific account...")
            account = None

        if True:  # Try even without account

            # Now try to play with the account info
            print("\n" + "="*50)
            print("Trying to play with account info...")
            print("="*50 + "\n")

            track_id = '2bZ8wwkkPw6m22ZxbFl137'

            # Build URI with account info
            if account:
                uri = f'x-sonos-spotify:spotify%3atrack%3a{track_id}?sid={spotify_service.service_id}&flags=8224&sn={account.serial_number}'
            else:
                # Try without serial number
                uri = f'x-sonos-spotify:spotify%3atrack%3a{track_id}?sid={spotify_service.service_id}&flags=8224'

            print(f"URI: {uri}")

            speaker.clear_queue()
            speaker.avTransport.SetAVTransportURI([
                ('InstanceID', 0),
                ('CurrentURI', uri),
                ('CurrentURIMetaData', '')
            ])

            speaker.play()
            print("✓ Playing!")
        else:
            print("No Spotify account found")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
