# Azan Scheduler - Quick Reference

## 📱 Control from Your Phone (EASIEST!)

### Start the web interface:
```bash
./start_web_control.sh
```

Then open the URL shown on your phone's browser. You'll get a beautiful interface to:
- ⏹️ Stop playing Azan immediately
- 📞 Pause for phone calls (30 min)
- 👥 Pause for guests (2 hours)
- ⏰ Pause for 1 hour
- ⏸️ Pause indefinitely
- ▶️ Resume when ready

**No need to come to your Mac!** Just bookmark the URL on your phone.

## 💻 Control from Mac Terminal

### Starting the Scheduler
```bash
cd ~/sonos
./start_azan.sh
```

### Stopping/Pausing Azan

| Situation | Command |
|-----------|---------|
| 📞 **Phone call** | `./pause_azan.sh call` |
| 👥 **Guests visiting** | `./pause_azan.sh guests` |
| ⏹️  **Stop playing now** | `./pause_azan.sh stop` |
| ⏸️  **Pause indefinitely** | `./pause_azan.sh` |
| ⏰ **Pause for 1 hour** | `./pause_azan.sh 1h` |

### Resume
```bash
./resume_azan.sh
```

### Check Status
```bash
python control_azan.py status
```

## Configuration

Edit `config.json` to:

### Disable a prayer
```json
"Fajr": {
  "enabled": false,    // ← Set to false
  "spotify_uri": "..."
}
```

### Change Azan track
Replace the `spotify_uri` with a different track:
```json
"Fajr": {
  "enabled": true,
  "spotify_uri": "spotify:track:NEW_TRACK_ID_HERE"
}
```

### Adjust volume
```json
"sonos": {
  "volume": 40    // 0-100
}
```

## Prayer Times

Today's times are automatically fetched daily for **Stockholm, Sweden**.

To change location, edit `config.json`:
```json
"location": {
  "city": "Your City",
  "country": "Your Country"
}
```

## Troubleshooting

### Azan not playing?
1. Check if paused: `python control_azan.py status`
2. Resume if needed: `./resume_azan.sh`
3. Test playback: `./test_azan.py`

### Wrong prayer times?
Check your city/country in `config.json`

### Sonos not found?
```bash
./discover_sonos.py
```
Then update IP in `config.json`
