#!/usr/bin/env python3
"""
Fetch prayer times for a specific date
Usage:
    python get_prayer_times.py                    # Today's times
    python get_prayer_times.py 15-02-2026         # Specific date (DD-MM-YYYY)
    python get_prayer_times.py --json             # JSON output
"""

import requests
import sys
import json
from datetime import datetime
import os

def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config['location']
    except FileNotFoundError:
        print(f"Warning: config.json not found, using defaults")
        return {"city": "Huddinge", "country": "Sweden", "method": 1}
    except Exception as e:
        print(f"Warning: Error reading config.json: {e}, using defaults")
        return {"city": "Huddinge", "country": "Sweden", "method": 1}

def get_prayer_times(date_str=None, city=None, country=None, method=None, json_output=False):
    """Fetch prayer times from Aladhan API"""

    # Load from config if not provided
    if city is None or country is None or method is None:
        config = load_config()
        city = city or config.get('city', 'Huddinge')
        country = country or config.get('country', 'Sweden')
        method = method or config.get('method', 1)

    # Use today's date if not provided
    if not date_str or date_str == "--json":
        date_str = datetime.now().strftime("%d-%m-%Y")

    url = f"http://api.aladhan.com/v1/timingsByCity/{date_str}"
    params = {
        "city": city,
        "country": country,
        "method": method
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if response.status_code == 200 and data['code'] == 200:
            timings = data['data']['timings']
            date_info = data['data']['date']

            if json_output or "--json" in sys.argv:
                # JSON output
                print(json.dumps({
                    "date": date_info['readable'],
                    "hijri": date_info['hijri']['date'],
                    "timings": {
                        "Fajr": timings['Fajr'],
                        "Sunrise": timings['Sunrise'],
                        "Dhuhr": timings['Dhuhr'],
                        "Asr": timings['Asr'],
                        "Maghrib": timings['Maghrib'],
                        "Isha": timings['Isha']
                    }
                }, indent=2))
            else:
                # Human-readable output
                print(f"\n🕌 Prayer Times for {city}, {country}")
                print(f"📅 Date: {date_info['readable']}")
                print(f"📆 Hijri: {date_info['hijri']['date']}")
                print("=" * 50)
                print(f"Fajr:    {timings['Fajr']}")
                print(f"Sunrise: {timings['Sunrise']}")
                print(f"Dhuhr:   {timings['Dhuhr']}")
                print(f"Asr:     {timings['Asr']}")
                print(f"Maghrib: {timings['Maghrib']}")
                print(f"Isha:    {timings['Isha']}")
                print("=" * 50)
        else:
            print(f"Error: {data.get('data', 'Unable to fetch prayer times')}")
            sys.exit(1)

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    get_prayer_times(date_arg)
