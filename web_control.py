#!/usr/bin/env python3
"""Simple web interface to control Azan scheduler from phone"""

from flask import Flask, render_template_string, request, jsonify
import json
import os
from datetime import datetime, timedelta
import subprocess
import requests

app = Flask(__name__)

# Use script directory for config files (works on both Mac and LXC)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(SCRIPT_DIR, 'scheduler_state.json')
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'config.json')

def load_config():
    """Load configuration"""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def fetch_prayer_times():
    """Fetch today's prayer times from API"""
    try:
        config = load_config()
        city = config['location']['city']
        country = config['location']['country']
        method = config['location'].get('method', 1)

        today = datetime.now().strftime("%d-%m-%Y")
        url = f"http://api.aladhan.com/v1/timingsByCity/{today}"
        params = {"city": city, "country": country, "method": method}

        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if response.status_code == 200 and data['code'] == 200:
            timings = data['data']['timings']
            return {
                'Fajr': timings['Fajr'].split(' ')[0],
                'Dhuhr': timings['Dhuhr'].split(' ')[0],
                'Asr': timings['Asr'].split(' ')[0],
                'Maghrib': timings['Maghrib'].split(' ')[0],
                'Isha': timings['Isha'].split(' ')[0]
            }
    except Exception as e:
        print(f"Error fetching prayer times: {e}")
    return None

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Azan Control</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 30px;
            max-width: 400px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        .status {
            text-align: center;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            font-weight: bold;
            font-size: 18px;
        }
        .status.running { background: #d4edda; color: #155724; }
        .status.paused { background: #fff3cd; color: #856404; }
        .btn {
            display: block;
            width: 100%;
            padding: 15px;
            margin: 10px 0;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .btn:active { transform: scale(0.98); }
        .btn-stop { background: #dc3545; color: white; }
        .btn-pause { background: #ffc107; color: #333; }
        .btn-resume { background: #28a745; color: white; }
        .btn-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin: 10px 0;
        }
        .btn-small {
            padding: 12px;
            font-size: 14px;
        }
        .emoji { font-size: 24px; margin-right: 8px; }
        .info {
            background: #e7f3ff;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            font-size: 14px;
            color: #004085;
        }
        .prayer-times {
            margin: 20px 0;
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            overflow: hidden;
        }
        .prayer-times h2 {
            font-size: 18px;
            color: #333;
            margin-bottom: 15px;
            text-align: center;
        }
        .prayer-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 8px;
            width: 100%;
        }
        .prayer-card {
            background: white;
            border-radius: 8px;
            padding: 10px 5px;
            text-align: center;
            transition: all 0.3s;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 85px;
        }
        .prayer-card.upcoming {
            background: #d1ecf1;
            border: 3px solid #17a2b8;
        }
        .prayer-card.passed {
            opacity: 0.5;
        }
        .prayer-name {
            font-size: 12px;
            color: #666;
            margin-bottom: 6px;
            display: block;
        }
        .prayer-card.upcoming .prayer-name {
            color: #17a2b8;
            font-weight: bold;
        }
        .prayer-time {
            font-size: 16px;
            font-weight: bold;
            color: #667eea;
            display: block;
        }
        .prayer-emoji {
            font-size: 18px;
            display: block;
            margin-bottom: 4px;
            height: 22px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🕌 Azan Control</h1>
        <div id="status" class="status">Loading...</div>

        <div class="prayer-times" id="prayerTimes">
            <h2>📿 Today's Prayer Times</h2>
            <div id="prayerList">Loading...</div>
        </div>

        <button class="btn btn-stop" onclick="stopNow()">
            <span class="emoji">⏹️</span>Stop Playing Now
        </button>

        <div class="btn-group">
            <button class="btn btn-pause btn-small" onclick="pause(30)">
                <span class="emoji">📞</span>Call (30m)
            </button>
            <button class="btn btn-pause btn-small" onclick="pause(120)">
                <span class="emoji">👥</span>Guests (2h)
            </button>
        </div>

        <div class="btn-group">
            <button class="btn btn-pause btn-small" onclick="pause(60)">
                <span class="emoji">⏰</span>1 Hour
            </button>
            <button class="btn btn-pause btn-small" onclick="pause(null)">
                <span class="emoji">⏸️</span>Pause All
            </button>
        </div>

        <button class="btn btn-resume" onclick="resume()">
            <span class="emoji">▶️</span>Resume Azan
        </button>

        <div class="info" id="info">
            Tap any button to control the Azan scheduler
        </div>
    </div>

    <script>
        async function updatePrayerTimes() {
            try {
                const response = await fetch('/api/prayer-times');
                const data = await response.json();
                const prayerList = document.getElementById('prayerList');

                if (data.times) {
                    const now = new Date();
                    const prayers = data.times;
                    let html = '';
                    let nextPrayer = null;

                    // Define correct prayer order
                    const prayerOrder = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'];

                    for (const name of prayerOrder) {
                        if (!prayers[name]) continue;
                        const time = prayers[name];
                        const [hours, minutes] = time.split(':');
                        const prayerDate = new Date();
                        prayerDate.setHours(parseInt(hours), parseInt(minutes), 0);

                        const isPassed = prayerDate < now;
                        const isNext = !isPassed && !nextPrayer;

                        if (isNext) nextPrayer = name;

                        const cardClass = isNext ? 'upcoming' : (isPassed ? 'passed' : '');
                        const emoji = isNext ? '▶️' : (isPassed ? '✓' : '');

                        html += `
                            <div class="prayer-card ${cardClass}">
                                <span class="prayer-emoji">${emoji || ''}</span>
                                <span class="prayer-name">${name}</span>
                                <span class="prayer-time">${time}</span>
                            </div>
                        `;
                    }

                    prayerList.innerHTML = '<div class="prayer-grid">' + html + '</div>';
                    return nextPrayer;
                } else {
                    prayerList.innerHTML = '<div style="text-align:center;color:#999;">Unable to load prayer times</div>';
                    return null;
                }
            } catch (error) {
                console.error('Error fetching prayer times:', error);
                return null;
            }
        }

        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                const statusDiv = document.getElementById('status');
                const infoDiv = document.getElementById('info');

                // Update prayer times
                const nextPrayer = await updatePrayerTimes();

                if (data.paused) {
                    statusDiv.className = 'status paused';
                    if (data.pause_until) {
                        statusDiv.textContent = `⏸️ PAUSED until ${data.pause_until}`;
                        infoDiv.textContent = `Scheduler will auto-resume at ${data.pause_until}`;
                    } else {
                        statusDiv.textContent = '⏸️ PAUSED indefinitely';
                        infoDiv.textContent = 'Azan will not play until you resume';
                    }
                } else {
                    statusDiv.className = 'status running';
                    statusDiv.textContent = '▶️ RUNNING';
                    if (nextPrayer) {
                        infoDiv.textContent = `Next Azan: ${nextPrayer}`;
                    } else {
                        infoDiv.textContent = 'Azan scheduler is active';
                    }
                }
            } catch (error) {
                console.error('Error updating status:', error);
                document.getElementById('info').textContent = '❌ Connection error';
            }
        }

        async function stopNow() {
            const infoDiv = document.getElementById('info');
            infoDiv.textContent = '⏹️ Stopping playback...';
            try {
                await fetch('/api/stop', { method: 'POST' });
                infoDiv.textContent = '✅ Playback stopped';
                setTimeout(() => {
                    updateStatus();
                }, 2000);
            } catch (error) {
                infoDiv.textContent = '❌ Error stopping playback';
            }
        }

        async function pause(minutes) {
            const infoDiv = document.getElementById('info');
            infoDiv.textContent = '⏸️ Pausing scheduler...';
            try {
                const url = minutes ? `/api/pause?minutes=${minutes}` : '/api/pause';
                await fetch(url, { method: 'POST' });
                setTimeout(async () => {
                    await updateStatus();
                }, 500);
            } catch (error) {
                infoDiv.textContent = '❌ Error pausing';
            }
        }

        async function resume() {
            const infoDiv = document.getElementById('info');
            infoDiv.textContent = '▶️ Resuming scheduler...';
            try {
                await fetch('/api/resume', { method: 'POST' });
                setTimeout(async () => {
                    await updateStatus();
                }, 500);
            } catch (error) {
                infoDiv.textContent = '❌ Error resuming';
            }
        }

        // Update status every 3 seconds
        setInterval(updateStatus, 3000);
        updateStatus();
    </script>
</body>
</html>
'''

def read_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"paused": False, "pause_until": None}

def write_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/status')
def api_status():
    state = read_state()
    result = {
        "paused": state.get('paused', False),
        "pause_until": None,
        "next_prayer": None
    }

    if state.get('pause_until'):
        pause_time = datetime.fromisoformat(state['pause_until'])
        result['pause_until'] = pause_time.strftime('%I:%M %p')

    return jsonify(result)

@app.route('/api/pause', methods=['POST'])
def api_pause():
    minutes = request.args.get('minutes', type=int)
    state = read_state()
    state['paused'] = True

    if minutes:
        pause_until = datetime.now() + timedelta(minutes=minutes)
        state['pause_until'] = pause_until.isoformat()
    else:
        state['pause_until'] = None

    write_state(state)
    return jsonify({"status": "paused"})

@app.route('/api/resume', methods=['POST'])
def api_resume():
    state = read_state()
    state['paused'] = False
    state['pause_until'] = None
    write_state(state)
    return jsonify({"status": "resumed"})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    try:
        import soco
        config = load_config()
        speaker_ip = config.get('sonos', {}).get('speaker_ip', '10.75.30.94')
        speaker = soco.SoCo(speaker_ip)
        speaker.stop()
        return jsonify({"status": "stopped"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/prayer-times')
def api_prayer_times():
    times = fetch_prayer_times()
    if times:
        return jsonify({"times": times})
    else:
        return jsonify({"error": "Unable to fetch prayer times"}), 500

if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"\n{'='*60}")
    print(f"🕌 Azan Control Web Interface")
    print(f"{'='*60}")
    print(f"\nAccess from your phone:")
    print(f"  http://{local_ip}:8080")
    print(f"\nOr from this Mac:")
    print(f"  http://localhost:8080")
    print(f"\n{'='*60}\n")
    app.run(host='0.0.0.0', port=8080, debug=False)
