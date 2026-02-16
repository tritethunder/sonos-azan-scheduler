#!/usr/bin/env python3
"""
Azan Scheduler for Sonos
Fetches prayer times from Aladhan API and plays Azan on Sonos at scheduled times
"""

import json
import logging
import time
import os
from datetime import datetime, timedelta
import requests
import soco
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.date import DateTrigger

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use script directory for state file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, 'scheduler_state.json')


class AzanScheduler:
    def __init__(self, config_file='config.json'):
        """Initialize the Azan Scheduler"""
        with open(config_file, 'r') as f:
            self.config = json.load(f)

        self.scheduler = BlockingScheduler()
        self.sonos_device = None
        self.prayer_times = {}

    def discover_sonos(self):
        """Discover and connect to Sonos speaker"""
        try:
            # Try to connect to specific IP if provided
            if self.config['sonos'].get('speaker_ip'):
                logger.info(f"Connecting to Sonos at {self.config['sonos']['speaker_ip']}")
                self.sonos_device = soco.SoCo(self.config['sonos']['speaker_ip'])
            else:
                # Auto-discover
                logger.info("Discovering Sonos speakers...")
                devices = list(soco.discover())
                if not devices:
                    raise Exception("No Sonos speakers found on network")

                # Find by name or use first device
                speaker_name = self.config['sonos'].get('speaker_name')
                if speaker_name:
                    for device in devices:
                        if device.player_name == speaker_name:
                            self.sonos_device = device
                            break

                if not self.sonos_device:
                    self.sonos_device = devices[0]

            logger.info(f"Connected to Sonos: {self.sonos_device.player_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Sonos: {e}")
            return False

    def fetch_prayer_times(self):
        """Fetch prayer times from Aladhan API"""
        try:
            city = self.config['location']['city']
            country = self.config['location']['country']
            method = self.config['location'].get('method', 2)

            # Get today's date
            today = datetime.now()

            # Build API URL
            url = f"http://api.aladhan.com/v1/timingsByCity"
            params = {
                'city': city,
                'country': country,
                'method': method
            }

            logger.info(f"Fetching prayer times for {city}, {country}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            timings = data['data']['timings']

            # Parse prayer times
            self.prayer_times = {}
            for prayer in ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']:
                time_str = timings[prayer].split(' ')[0]  # Remove timezone
                prayer_time = datetime.strptime(f"{today.strftime('%Y-%m-%d')} {time_str}",
                                               '%Y-%m-%d %H:%M')
                self.prayer_times[prayer] = prayer_time

            logger.info("Prayer times fetched successfully:")
            for prayer, time in self.prayer_times.items():
                logger.info(f"  {prayer}: {time.strftime('%I:%M %p')}")

            return True

        except Exception as e:
            logger.error(f"Failed to fetch prayer times: {e}")
            return False

    def is_paused(self):
        """Check if scheduler is paused"""
        if not os.path.exists(STATE_FILE):
            return False

        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)

            if not state.get('paused', False):
                return False

            # Check if pause has expired
            pause_until = state.get('pause_until')
            if pause_until:
                pause_time = datetime.fromisoformat(pause_until)
                if datetime.now() >= pause_time:
                    # Auto-resume
                    state['paused'] = False
                    state['pause_until'] = None
                    with open(STATE_FILE, 'w') as f:
                        json.dump(state, f)
                    return False

            return True
        except Exception as e:
            logger.error(f"Error checking pause state: {e}")
            return False

    def play_azan(self, prayer_name):
        """Play Azan track on Sonos"""
        try:
            # Check if paused
            if self.is_paused():
                logger.info(f"Skipping {prayer_name} - Scheduler is paused")
                return

            if not self.sonos_device:
                logger.error("Sonos device not connected")
                return

            logger.info(f"Playing Azan for {prayer_name}")

            # Set volume
            volume = self.config['sonos'].get('volume', 30)
            self.sonos_device.volume = volume

            # Get Spotify URI for this specific prayer
            prayer_config = self.config['azan']['prayers'].get(prayer_name, {})
            spotify_uri = prayer_config.get('spotify_uri')

            if not spotify_uri:
                logger.error(f"No Spotify URI configured for {prayer_name}")
                return

            # For Spotify URIs, use direct SOAP calls
            if spotify_uri.startswith('spotify:track:'):
                # Extract track ID
                track_id = spotify_uri.replace('spotify:track:', '')

                # Build Sonos-compatible Spotify URI (sid=9 is Spotify's service ID)
                uri = f'x-sonos-spotify:spotify%3atrack%3a{track_id}?sid=9&flags=8224'

                # Clear queue first
                self.sonos_device.clear_queue()

                # Use SetAVTransportURI action
                self.sonos_device.avTransport.SetAVTransportURI([
                    ('InstanceID', 0),
                    ('CurrentURI', uri),
                    ('CurrentURIMetaData', '')
                ])

                # Play
                self.sonos_device.play()

            else:
                logger.error(f"Invalid Spotify URI: {spotify_uri}")

            logger.info(f"Azan playing for {prayer_name}")

        except Exception as e:
            logger.error(f"Failed to play Azan: {e}")

    def schedule_prayers(self):
        """Schedule Azan for prayer times"""
        try:
            # Remove existing jobs
            self.scheduler.remove_all_jobs()

            prayers_config = self.config['azan']['prayers']
            now = datetime.now()

            for prayer, prayer_time in self.prayer_times.items():
                # Check if this prayer is enabled
                prayer_settings = prayers_config.get(prayer, {})
                if not prayer_settings.get('enabled', False):
                    logger.info(f"Skipped {prayer} (disabled in config)")
                    continue

                # Only schedule if time is in the future
                if prayer_time > now:
                    self.scheduler.add_job(
                        self.play_azan,
                        DateTrigger(run_date=prayer_time),
                        args=[prayer],
                        id=f'azan_{prayer}'
                    )
                    logger.info(f"Scheduled {prayer} at {prayer_time.strftime('%I:%M %p')}")
                else:
                    logger.info(f"Skipped {prayer} (time has passed)")

            # Schedule daily prayer time refresh at midnight
            tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=1, second=0)
            self.scheduler.add_job(
                self.refresh_schedule,
                DateTrigger(run_date=tomorrow),
                id='daily_refresh'
            )
            logger.info(f"Scheduled daily refresh at {tomorrow.strftime('%I:%M %p')}")

        except Exception as e:
            logger.error(f"Failed to schedule prayers: {e}")

    def refresh_schedule(self):
        """Refresh prayer times and reschedule"""
        logger.info("Refreshing prayer schedule...")
        if self.fetch_prayer_times():
            self.schedule_prayers()

    def run(self):
        """Main run loop"""
        logger.info("Starting Azan Scheduler...")

        # Connect to Sonos
        if not self.discover_sonos():
            logger.error("Cannot start without Sonos connection")
            return

        # Fetch initial prayer times
        if not self.fetch_prayer_times():
            logger.error("Cannot start without prayer times")
            return

        # Schedule prayers
        self.schedule_prayers()

        # Start scheduler
        logger.info("Scheduler started. Press Ctrl+C to exit.")
        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped.")


if __name__ == "__main__":
    scheduler = AzanScheduler()
    scheduler.run()
