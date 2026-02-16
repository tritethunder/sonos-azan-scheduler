# Deployment Guide - Proxmox LXC vs Docker

## 🎯 Recommendation: **LXC Container** (Better for this use case)

### Why LXC?
- ✅ **Lightweight** - Uses less resources than Docker
- ✅ **Simple Setup** - No virtual env needed for dedicated containers
- ✅ **Simple Management** - Easy to manage in Proxmox UI
- ✅ **Full System Access** - Behaves like a mini VM
- ✅ **Better for Always-On Services** - Perfect for home automation
- ✅ **Direct IP Support** - Works even across network subnets

### Why NOT Docker (for this)?
- ⚠️ Network mode complexity for Sonos discovery
- ⚠️ More overhead for a simple Python app
- ⚠️ Harder to debug networking issues
- ⚠️ Overkill for this simple use case

### ⚠️ Important: Network Subnets
**Sonos Discovery across subnets:** If your LXC and Sonos are on different subnets (e.g., LXC on 10.75.1.x, Sonos on 10.75.30.x), auto-discovery won't work due to multicast limitations. **Solution:** Use direct IP in config.json - the scheduler will work perfectly!

---

## 📦 Option 1: LXC Container on Proxmox (RECOMMENDED)

### Step 1: Create LXC Container

1. **In Proxmox UI:**
   - Click **Create CT**
   - **CT ID**: Choose (e.g., 100)
   - **Hostname**: `azan-scheduler`
   - **Unprivileged container**: ✅ Yes
   - **Template**: `ubuntu-22.04-standard` (or Debian 12)
   - **Storage**: 8 GB (plenty)
   - **CPU**: 1 core
   - **Memory**: 512 MB (256 MB works too)
   - **Network**: Bridge to same network as Sonos
     - **IPv4**: DHCP or static
   - **DNS**: Use host settings
   - ✅ **Start at boot**

2. **Start the container**

### Step 2: Setup Inside LXC

```bash
# Access the container
pct enter 100

# Update system
apt update && apt upgrade -y

# Install Python and dependencies
apt install -y python3 python3-pip python3-venv git

# Create user for the service
useradd -m -s /bin/bash azan
su - azan

# Create project directory
mkdir ~/azan-scheduler
cd ~/azan-scheduler
```

### Step 3: Transfer Files

**From your Mac:**
```bash
# Get LXC IP (from Proxmox UI or container)
LXC_IP="10.75.30.xxx"  # Replace with actual IP

# Copy all files
scp -r ~/azan-scheduler/* azan@$LXC_IP:~/azan-scheduler/
```

**Or manually copy each file using the Proxmox UI**

### Step 4: Install and Setup

**Inside LXC:**
```bash
cd /home/azan/azan-scheduler

# Install Python packages system-wide (no venv needed for dedicated container)
sudo pip3 install -r requirements.txt

# Fix shebang in all Python files for system Python
sudo sed -i '1s|^#!.*python.*|#!/usr/bin/python3|' *.py

# Make scripts executable
sudo chmod +x *.py *.sh

# Update config.json with correct Sonos IP
nano config.json
# Make sure speaker_ip is set (e.g., "speaker_ip": "10.75.30.94")
# This is REQUIRED if LXC and Sonos are on different subnets
```

**Why no virtual environment?**
Since this LXC is dedicated to the Azan scheduler, installing packages system-wide is simpler and has no conflicts. This reduces overhead and simplifies the systemd service configuration.

### Step 5: Test

```bash
# Test network connectivity to Sonos
ping -c 3 10.75.30.94  # Replace with your Sonos IP

# Test direct Sonos connection (works across subnets)
python3 -c "
import soco
speaker = soco.SoCo('10.75.30.94')  # Replace with your Sonos IP
print(f'Connected to: {speaker.player_name}')
print(f'Volume: {speaker.volume}')
"

# Test Sonos discovery (may fail if on different subnet - that's OK!)
python3 discover_sonos.py

# Test prayer times
python3 -c "from azan_scheduler import AzanScheduler; s=AzanScheduler(); s.fetch_prayer_times()"
```

**Note:** If discovery fails but direct connection works, that's normal for different subnets. The scheduler uses the IP from config.json, so it will work fine!

### Step 6: Create Systemd Services

**Create scheduler service:**
```bash
sudo nano /etc/systemd/system/azan-scheduler.service
```

```ini
[Unit]
Description=Azan Scheduler
After=network.target

[Service]
Type=simple
User=azan
WorkingDirectory=/home/azan/azan-scheduler
ExecStart=/usr/bin/python3 /home/azan/azan-scheduler/azan_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Create web control service:**
```bash
sudo nano /etc/systemd/system/azan-web.service
```

```ini
[Unit]
Description=Azan Web Control
After=network.target

[Service]
Type=simple
User=azan
WorkingDirectory=/home/azan/azan-scheduler
ExecStart=/usr/bin/python3 /home/azan/azan-scheduler/web_control.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start services:**
```bash
sudo systemctl daemon-reloads
sudo systemctl enable azan-scheduler
sudo systemctl enable azan-web
sudo systemctl start azan-scheduler
sudo systemctl start azan-web

# Check status
sudo systemctl status azan-scheduler
sudo systemctl status azan-web
```

### Step 7: Access Web Interface

From your phone or any device on the network:
```
http://LXC_IP:8080
```

### Managing the Services

```bash
# View logs
sudo journalctl -u azan-scheduler -f
sudo journalctl -u azan-web -f

# Restart services
sudo systemctl restart azan-scheduler
sudo systemctl restart azan-web

# Stop services
sudo systemctl stop azan-scheduler
sudo systemctl stop azan-web
```

---

## 🐳 Option 2: Docker Container (Advanced)

### Docker Compose File

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  azan-scheduler:
    build: .
    container_name: azan-scheduler
    restart: unless-stopped
    network_mode: host  # Required for Sonos discovery
    volumes:
      - ./config.json:/app/config.json
      - ./scheduler_state.json:/app/scheduler_state.json
    environment:
      - TZ=Europe/Stockholm

  azan-web:
    build: .
    container_name: azan-web
    restart: unless-stopped
    network_mode: host  # Required for Sonos control
    volumes:
      - ./config.json:/app/config.json
      - ./scheduler_state.json:/app/scheduler_state.json
    environment:
      - TZ=Europe/Stockholm
    command: python web_control.py
```

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py .
COPY *.sh .
COPY config.json .

# Make scripts executable
RUN chmod +x *.py *.sh

# Default command
CMD ["python", "azan_scheduler.py"]
```

### Build and Run

```bash
# Build
docker-compose build

# Run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### ⚠️ Docker Limitations

1. **Network Mode**: Must use `host` mode for Sonos discovery
2. **Security**: Host mode bypasses Docker network isolation
3. **Complexity**: More moving parts than LXC
4. **Debugging**: Harder to troubleshoot network issues

---

## 🔄 Migration Steps from Mac to Proxmox

### 1. Prepare Files on Mac
```bash
cd ~/azan-scheduler

# Create deployment package
tar -czf azan-deployment.tar.gz \
  config.json \
  requirements.txt \
  *.py \
  *.sh \
  *.md
```

### 2. Transfer to Proxmox Host
```bash
# Upload to Proxmox host
scp azan-deployment.tar.gz root@proxmox-ip:/tmp/
```

### 3. Setup in LXC (see LXC guide above)

### 4. Update Config
- Update `speaker_ip` if needed
- Verify network connectivity

### 5. Test Everything
```bash
# In LXC
./discover_sonos.py
./test_azan.py
```

### 6. Stop Mac Services
```bash
# On Mac - stop the services
# Ctrl+C in both terminal windows
```

### 7. Enjoy!
Your Azan scheduler is now running 24/7 on Proxmox! 🎉

---

## 📊 Comparison Table

| Feature | LXC | Docker |
|---------|-----|--------|
| **Resource Usage** | Very Low | Low-Medium |
| **Setup Complexity** | Simple | Medium |
| **Network Discovery** | Easy | Complex |
| **Management** | Proxmox UI | Docker CLI |
| **Debugging** | Easy | Medium |
| **Portability** | Proxmox only | Any Docker host |
| **Recommendation** | ✅ **Best Choice** | Use if needed |

---

## 🔧 Troubleshooting

### Sonos Not Found in LXC

1. **Check if it's a subnet issue:**
   ```bash
   # Check LXC IP
   ip addr show

   # Check if you can reach Sonos
   ping 10.75.30.94  # Replace with your Sonos IP
   ```

2. **Different subnets? Use direct IP:**
   - If LXC is on `10.75.1.x` and Sonos on `10.75.30.x`, discovery won't work
   - This is **normal** - multicast doesn't cross subnets
   - **Solution:** Ensure `speaker_ip` is set in config.json
   - The scheduler will use direct IP and work perfectly!

3. **Test direct connection:**
   ```bash
   python3 -c "
   import soco
   speaker = soco.SoCo('10.75.30.94')  # Your Sonos IP
   print(f'Connected: {speaker.player_name}')
   "
   ```
   If this works, you're good to go!

4. **Optional: Same subnet (if needed):**
   - Move LXC to same network as Sonos in Proxmox
   - Or enable multicast routing in your network (complex)

### Service Won't Start

```bash
# Check logs
sudo journalctl -u azan-scheduler -n 50

# Check Python path
which python3
/home/azan/azan-scheduler/venv/bin/python --version

# Check permissions
ls -la /home/azan/azan-scheduler/
```

### Web Interface Not Accessible

```bash
# Check if service is running
sudo systemctl status azan-web

# Check if port is listening
sudo netstat -tlnp | grep 8080

# Check firewall (if enabled)
sudo ufw status
sudo ufw allow 8080
```

---

## 🎯 Final Recommendation

**Use LXC Container on Proxmox** for:
- ✅ Simpler setup and maintenance
- ✅ Better network compatibility with Sonos
- ✅ Lower resource usage
- ✅ Easier debugging
- ✅ Perfect for home automation

Docker is great for microservices and complex deployments, but for this single-purpose automation, LXC is the clear winner.
