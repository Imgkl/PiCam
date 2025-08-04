#!/bin/bash
set -e

echo "🚀 Setting up Professional Pi Camera Stream Server..."
echo "======================================================"

# Create project directory
PROJECT_DIR="$HOME/picamera-stream"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Check if camera is detected
echo "📹 Checking camera..."
if ! python3 -c "from picamera2 import Picamera2; Picamera2()" 2>/dev/null; then
    echo "❌ Camera not detected. Please check Camera Module 3 connection."
    exit 1
fi
echo "✅ Camera detected!"

# Get user preferences
echo ""
echo "🔧 Configuration Setup"
echo "======================"

read -p "Enter username for camera access [admin]: " username
username=${username:-admin}

read -s -p "Enter password for camera access [pogocam2025]: " password
echo ""
password=${password:-pogocam2025}

read -p "Enter port number [8080]: " port
port=${port:-8080}

# Create camera server script
cat > camera_server.py << 'EOF'
# [Content from the camera_server.py artifact above]
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
# [Content from the Dockerfile artifact above]
EOF

# Create docker-compose.yml with user settings
cat > docker-compose.yml << EOF
version: '3.8'

services:
  picamera-stream:
    build: .
    container_name: picamera-live
    restart: unless-stopped
    ports:
      - "${port}:8080"
    devices:
      - /dev/video0:/dev/video0
      - /dev/vchiq:/dev/vchiq
      - /dev/vcsm-cma:/dev/vcsm-cma
    privileged: true
    environment:
      - CAM_USER=${username}
      - CAM_PASS=${password}
      - CAM_PORT=8080
    volumes:
      - /opt/vc/lib:/opt/vc/lib:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "--basic", "--user", "${username}:${password}", "http://localhost:8080/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
EOF

# Create management scripts
cat > start.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Pi Camera Stream Server..."
docker-compose up -d
echo "✅ Server started!"
echo "🌐 Access your camera at: http://$(hostname -I | awk '{print $1}'):8080"
EOF

cat > stop.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping Pi Camera Stream Server..."
docker-compose down
echo "✅ Server stopped!"
EOF

cat > logs.sh << 'EOF'
#!/bin/bash
echo "📋 Camera Server Logs:"
docker-compose logs -f picamera-stream
EOF

cat > update.sh << 'EOF'
#!/bin/bash
echo "🔄 Updating Pi Camera Server..."
docker-compose down
docker-compose build --no-cache
docker-compose up -d
echo "✅ Update complete!"
EOF

# Make scripts executable
chmod +x start.sh stop.sh logs.sh update.sh

# Build and start the container
echo ""
echo "🔨 Building Docker container..."
docker-compose build

echo ""
echo "🚀 Starting camera server..."
docker-compose up -d

# Wait for server to be ready
echo "⏳ Waiting for server to start..."
sleep 10

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo "✅ Professional Pi Camera Server is running!"
echo ""
echo "📱 Access URLs:"
echo "   • Local:    http://localhost:${port}"
echo "   • Network:  http://${SERVER_IP}:${port}"
echo "   • Hostname: http://$(hostname).local:${port}"
echo ""
echo "🔐 Login Credentials:"
echo "   • Username: ${username}"
echo "   • Password: ${password}"
echo ""
echo "🛠️  Management Commands:"
echo "   • Start:    ./start.sh"
echo "   • Stop:     ./stop.sh"
echo "   • Logs:     ./logs.sh"
echo "   • Update:   ./update.sh"
echo ""
echo "📱 Features:"
echo "   • 🔄 Auto-restart on failure"
echo "   • 📱 Mobile-optimized interface"
echo "   • 🔒 Password protection"
echo "   • 🎥 Smooth MJPEG streaming"
echo "   • 🔧 180° rotation support"
echo ""
echo "🌐 Open http://${SERVER_IP}:${port} in your browser!"
EOF
