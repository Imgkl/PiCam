#!/bin/bash
set -e

echo "🚀 Setting up Professional Pi Camera Stream Server..."
echo "======================================================"

# Check if camera is detected
echo "📹 Checking camera..."
if ! python3 -c "from picamera2 import Picamera2; Picamera2()" 2>/dev/null; then
    echo "❌ Camera not detected. Please check Camera Module 3 connection."
    exit 1
fi
echo "✅ Camera detected!"

# Load environment variables from .env if it exists
if [ -f .env ]; then
    echo "📝 Loading configuration from .env file..."
    export $(cat .env | xargs)
fi

# Get user preferences (with defaults from .env or fallback)
echo ""
echo "🔧 Configuration Setup"
echo "======================"

read -p "Enter username for camera access [${CAM_USER:-admin}]: " username
username=${username:-${CAM_USER:-admin}}

read -s -p "Enter password for camera access [${CAM_PASS:-pogocam2025}]: " password
echo ""
password=${password:-${CAM_PASS:-pogocam2025}}

read -p "Enter port number [${CAM_PORT:-8080}]: " port
port=${port:-${CAM_PORT:-8080}}

# Update .env file with user input
cat > .env << EOF
CAM_USER=${username}
CAM_PASS=${password}
CAM_PORT=${port}
EOF

# Create management scripts
cat > start.sh << 'SCRIPT_EOF'
#!/bin/bash
echo "🚀 Starting Pi Camera Stream Server..."
docker compose up -d
echo "✅ Server started!"
echo "🌐 Access your camera at: http://$(hostname -I | awk '{print $1}'):$(grep CAM_PORT .env | cut -d'=' -f2)"
SCRIPT_EOF

cat > stop.sh << 'SCRIPT_EOF'
#!/bin/bash
echo "🛑 Stopping Pi Camera Stream Server..."
docker compose down
echo "✅ Server stopped!"
SCRIPT_EOF

cat > logs.sh << 'SCRIPT_EOF'
#!/bin/bash
echo "📋 Camera Server Logs:"
docker compose logs -f picamera-stream
SCRIPT_EOF

cat > update.sh << 'SCRIPT_EOF'
#!/bin/bash
echo "🔄 Updating Pi Camera Server..."
docker compose down
docker compose build --no-cache
docker compose up -d
echo "✅ Update complete!"
SCRIPT_EOF

# Make scripts executable
chmod +x start.sh stop.sh logs.sh update.sh

# Build and start the container
echo ""
echo "🔨 Building Docker container..."
docker compose build

echo ""
echo "🚀 Starting camera server..."
docker compose up -d

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
