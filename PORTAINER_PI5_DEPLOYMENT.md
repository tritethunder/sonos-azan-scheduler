# Deploy Azan Scheduler to Raspberry Pi 5 with Portainer

## 🎯 Overview

Deploy your Azan automation to Raspberry Pi 5 using Portainer for easy Docker management.

### Why Raspberry Pi 5?
- ✅ Low power consumption (~5W)
- ✅ Runs 24/7 reliably
- ✅ ARM64 architecture (modern)
- ✅ Powerful enough for multiple containers
- ✅ Portainer makes management easy

---

## 📋 Prerequisites

### On Raspberry Pi 5:
1. **Raspberry Pi OS (64-bit)** installed
2. **Docker** installed
3. **Portainer** installed and running
4. Pi connected to **same network** as Sonos

### If not already set up:

```bash
# SSH to your Pi
ssh pi@raspberrypi.local

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Portainer
docker volume create portainer_data
docker run -d \
  -p 9000:9000 \
  -p 9443:9443 \
  --name=portainer \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce:latest

# Reboot to apply docker group
sudo reboot
```

Access Portainer: `http://raspberrypi.local:9000`

---

## 📦 Method 1: Using Portainer Stacks (Recommended)

### Step 1: Prepare Files on Mac

```bash
cd ~/azan-scheduler

# Create deployment package
tar -czf azan-pi-deployment.tar.gz \
  config.json \
  requirements.txt \
  azan_scheduler.py \
  web_control.py \
  control_azan.py \
  Dockerfile \
  docker-compose.yml
```

### Step 2: Transfer to Raspberry Pi

```bash
# Replace with your Pi's IP
PI_IP="192.168.1.xxx"

scp azan-pi-deployment.tar.gz pi@$PI_IP:/home/pi/
```

### Step 3: Extract on Pi

```bash
# SSH to Pi
ssh pi@$PI_IP

# Extract files
mkdir -p ~/azan-scheduler
cd ~/azan-scheduler
tar -xzf ~/azan-pi-deployment.tar.gz

# Update config if needed
nano config.json
# Verify Sonos IP and settings
```

### Step 4: Build Docker Image on Pi

```bash
cd ~/azan-scheduler

# Build the image
docker build -t azan-scheduler:latest .

# Verify image
docker images | grep azan
```

### Step 5: Deploy via Portainer UI

1. **Open Portainer** in browser: `http://raspberrypi.local:9000`
2. Click **Stacks** → **+ Add stack**
3. **Name**: `azan-scheduler`
4. **Build method**: Web editor
5. **Paste this stack configuration:**

```yaml
version: '3.8'

services:
  azan-scheduler:
    image: azan-scheduler:latest
    container_name: azan-scheduler
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./config.json:/app/config.json
      - ./scheduler_state.json:/app/scheduler_state.json
    environment:
      - TZ=Europe/Stockholm

  azan-web:
    image: azan-scheduler:latest
    container_name: azan-web
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./config.json:/app/config.json
      - ./scheduler_state.json:/app/scheduler_state.json
    environment:
      - TZ=Europe/Stockholm
    command: python web_control.py
```

6. **Scroll down** to **Environment variables** (optional)
7. Click **Deploy the stack**

### Step 6: Verify Deployment

In Portainer:
1. Go to **Containers**
2. You should see:
   - `azan-scheduler` - Status: Running
   - `azan-web` - Status: Running
3. Click on each container to view logs

---

## 📦 Method 2: Manual Container Deployment

If you prefer individual containers instead of a stack:

### Deploy Scheduler Container

1. **Portainer** → **Containers** → **+ Add container**
2. **Name**: `azan-scheduler`
3. **Image**: `azan-scheduler:latest`
4. **Network**: Check "host" under Network tab
5. **Restart policy**: Unless stopped
6. **Volumes**:
   - `/home/pi/azan-scheduler/config.json` → `/app/config.json`
   - `/home/pi/azan-scheduler/scheduler_state.json` → `/app/scheduler_state.json`
7. **Env variables**:
   - `TZ` = `Europe/Stockholm`
8. Click **Deploy container**

### Deploy Web Container

Repeat above with:
- **Name**: `azan-web`
- **Command override**: `python web_control.py`

---

## 📦 Method 3: Docker Compose CLI (Alternative)

If you prefer command line:

```bash
cd ~/azan-scheduler

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart
```

---

## 🔧 Configuration

### Update Config Without Rebuilding

```bash
# SSH to Pi
ssh pi@raspberrypi.local

# Edit config
cd ~/azan-scheduler
nano config.json

# Restart containers in Portainer UI
# OR via CLI:
docker restart azan-scheduler azan-web
```

### Change Sonos IP

If your Sonos IP changes:

```bash
nano ~/azan-scheduler/config.json
# Update speaker_ip

# Restart containers
docker restart azan-scheduler azan-web
```

---

## 📱 Access Web Interface

From any device on your network:
```
http://raspberrypi.local:8080
```

Or use Pi's IP:
```
http://192.168.1.xxx:8080
```

Bookmark on your phone for easy access!

---

## 🔍 Monitoring & Logs

### View Logs in Portainer

1. **Containers** → Click container name
2. **Logs** tab → View real-time logs
3. **Stats** tab → See resource usage

### View Logs via CLI

```bash
# Scheduler logs
docker logs -f azan-scheduler

# Web logs
docker logs -f azan-web

# Last 50 lines
docker logs --tail 50 azan-scheduler
```

### Check Container Status

```bash
docker ps

# Expected output:
# CONTAINER ID   IMAGE                  STATUS
# xxxxx          azan-scheduler:latest  Up X hours
# yyyyy          azan-scheduler:latest  Up X hours
```

---

## 🔄 Updates & Maintenance

### Update Code

```bash
# On Mac - make changes to code
cd ~/azan-scheduler

# Transfer updated files
scp azan_scheduler.py web_control.py pi@$PI_IP:~/azan-scheduler/

# On Pi - rebuild image
ssh pi@$PI_IP
cd ~/azan-scheduler
docker build -t azan-scheduler:latest .

# Restart via Portainer or CLI:
docker-compose down
docker-compose up -d
```

### Update Config

```bash
# On Pi
nano ~/azan-scheduler/config.json

# Restart in Portainer UI
# OR
docker restart azan-scheduler azan-web
```

---

## 🐛 Troubleshooting

### Containers Won't Start

```bash
# Check logs
docker logs azan-scheduler

# Common issues:
# 1. Port already in use
sudo netstat -tlnp | grep 8080

# 2. Config file missing
ls -la ~/azan-scheduler/config.json

# 3. Network issues
docker network ls
```

### Sonos Not Found

```bash
# Test from container
docker exec -it azan-scheduler python -c "import soco; print(list(soco.discover()))"

# Check if Pi can reach Sonos
ping 10.75.30.94  # Your Sonos IP

# Verify network mode is 'host'
docker inspect azan-scheduler | grep NetworkMode
```

### Web Interface Not Accessible

```bash
# Check if container is running
docker ps | grep azan-web

# Check port
docker port azan-web

# Test locally on Pi
curl http://localhost:8080

# Check Pi firewall
sudo ufw status
```

### High CPU Usage

```bash
# Check resource usage
docker stats

# Restart containers
docker restart azan-scheduler azan-web
```

---

## 💾 Backup Configuration

```bash
# Backup config and state
ssh pi@$PI_IP
cd ~/azan-scheduler
tar -czf azan-backup-$(date +%Y%m%d).tar.gz \
  config.json \
  scheduler_state.json

# Copy backup to Mac
scp pi@$PI_IP:~/azan-scheduler/azan-backup-*.tar.gz ~/Downloads/
```

---

## 🔐 Security Tips

### 1. Change Default Pi Password
```bash
passwd
```

### 2. Enable UFW Firewall
```bash
sudo apt install ufw
sudo ufw allow 22    # SSH
sudo ufw allow 8080  # Web interface
sudo ufw enable
```

### 3. Restrict Web Interface Access
```bash
# Only allow from your local network
sudo ufw delete allow 8080
sudo ufw allow from 192.168.1.0/24 to any port 8080
```

---

## ⚡ Performance Notes

### Raspberry Pi 5 Resources

**Expected Usage:**
- RAM: ~100-150 MB total
- CPU: <5% average
- Storage: ~200 MB

**Recommended Pi 5 Specs:**
- Minimum: 2 GB RAM
- Recommended: 4 GB RAM
- Storage: 16 GB SD card minimum

### Power Consumption

- Idle: ~3-5W
- With containers: ~5-8W
- Annual cost: ~$5-10 (depending on electricity rates)

---

## 🎯 Complete Deployment Checklist

- [ ] Pi 5 running with Docker installed
- [ ] Portainer accessible at `:9000`
- [ ] Files transferred to Pi
- [ ] `config.json` updated with correct IPs
- [ ] Docker image built successfully
- [ ] Stack deployed in Portainer
- [ ] Both containers running
- [ ] Sonos discovered successfully
- [ ] Web interface accessible
- [ ] Test Azan playback works
- [ ] Prayer times fetched correctly
- [ ] Containers set to auto-restart
- [ ] Bookmarked web interface on phone

---

## 📊 Portainer UI Quick Guide

### Container Actions
- **Start/Stop**: Click icons next to container
- **Restart**: Three dots → Restart
- **Logs**: Container name → Logs tab
- **Shell**: Container name → Console → Connect

### Stack Actions
- **View**: Stacks → Click stack name
- **Update**: Stacks → Stack → Editor → Update
- **Remove**: Stacks → Stack → Delete

### Resource Monitoring
- **Dashboard**: Overview of all containers
- **Containers** → Container → Stats: Real-time graphs

---

## 🚀 Next Steps

1. **Test thoroughly** - Play Azan at different times
2. **Monitor for a day** - Check logs for errors
3. **Set up backups** - Schedule config backups
4. **Add monitoring** (optional) - Use Portainer alerts
5. **Document custom changes** - Keep notes of modifications

Your Azan scheduler is now running 24/7 on your Pi! 🎉
