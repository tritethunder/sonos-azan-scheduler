#!/bin/bash
# Quick deployment script for Raspberry Pi 5

set -e

echo "🥧 Azan Scheduler - Raspberry Pi 5 Deployment Helper"
echo "======================================================"
echo ""

# Get Pi IP
read -p "Enter your Pi's IP address: " PI_IP

# Verify Pi is reachable
echo "📡 Testing connection to Pi..."
if ! ping -c 1 -W 2 $PI_IP > /dev/null 2>&1; then
    echo "❌ Cannot reach Pi at $PI_IP"
    echo "Please check:"
    echo "  - Pi is powered on"
    echo "  - IP address is correct"
    echo "  - Both devices on same network"
    exit 1
fi
echo "✅ Pi is reachable"
echo ""

# Create deployment package
echo "📦 Creating deployment package..."
cd "$(dirname "$0")"
tar -czf azan-pi-deployment.tar.gz \
    config.json \
    requirements.txt \
    azan_scheduler.py \
    web_control.py \
    control_azan.py \
    Dockerfile \
    docker-compose.yml \
    .dockerignore
echo "✅ Package created"
echo ""

# Transfer to Pi
echo "📤 Transferring files to Pi..."
scp azan-pi-deployment.tar.gz pi@$PI_IP:/home/pi/
echo "✅ Files transferred"
echo ""

# Extract and build on Pi
echo "🔧 Setting up on Pi (this will take a few minutes)..."
ssh pi@$PI_IP << 'ENDSSH'
    # Create directory
    mkdir -p ~/azan-scheduler
    cd ~/azan-scheduler

    # Extract
    tar -xzf ~/azan-pi-deployment.tar.gz

    # Build Docker image
    echo "🐳 Building Docker image..."
    docker build -t azan-scheduler:latest .

    echo ""
    echo "✅ Setup complete on Pi!"
ENDSSH

# Cleanup
rm azan-pi-deployment.tar.gz

echo ""
echo "======================================================"
echo "✅ Deployment Complete!"
echo "======================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Open Portainer: http://$PI_IP:9000"
echo "2. Go to Stacks → Add stack"
echo "3. Use docker-compose.yml content from the guide"
echo "4. Deploy the stack"
echo ""
echo "Or use Docker Compose directly:"
echo "  ssh pi@$PI_IP"
echo "  cd ~/azan-scheduler"
echo "  docker-compose up -d"
echo ""
echo "Web interface will be at: http://$PI_IP:8080"
echo ""
