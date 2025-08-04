#!/usr/bin/env python3
"""
Professional Pi Camera Stream Server
- Smooth MJPEG streaming
- Password authentication  
- Mobile-optimized UI
- Docker-ready
"""

import io
import time
import base64
from threading import Condition, Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
from libcamera import Transform
import os

# Configuration
USERNAME = os.getenv('CAM_USER', 'admin')
PASSWORD = os.getenv('CAM_PASS', 'pogocam2025')
PORT = int(os.getenv('CAM_PORT', '8080'))

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

class AuthHandler(BaseHTTPRequestHandler):
    def check_auth(self):
        auth_header = self.headers.get('Authorization')
        if not auth_header:
            return False
        
        try:
            auth_type, credentials = auth_header.split(' ', 1)
            if auth_type.lower() != 'basic':
                return False
            
            decoded = base64.b64decode(credentials).decode('utf-8')
            username, password = decoded.split(':', 1)
            return username == USERNAME and password == PASSWORD
        except:
            return False

    def send_auth_request(self):
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Pi Camera"')
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>401 - Authentication Required</h1>')

    def do_GET(self):
        if not self.check_auth():
            self.send_auth_request()
            return

        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Pi Camera Live</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: white;
            overflow-x: hidden;
        }
        .header {
            background: rgba(0,0,0,0.3);
            padding: 15px 20px;
            text-align: center;
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .header h1 {
            font-size: 1.8rem;
            font-weight: 300;
            margin: 0;
        }
        .status {
            font-size: 0.9rem;
            opacity: 0.8;
            margin-top: 5px;
        }
        .stream-container {
            position: relative;
            margin: 20px;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            background: #000;
        }
        #stream {
            width: 100%;
            height: auto;
            display: block;
            max-height: 70vh;
            object-fit: contain;
        }
        .controls {
            background: rgba(0,0,0,0.5);
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .btn {
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }
        .btn:hover {
            background: rgba(255,255,255,0.3);
            transform: translateY(-1px);
        }
        .quality-indicator {
            font-size: 0.8rem;
            opacity: 0.7;
        }
        .fullscreen-btn {
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(0,0,0,0.7);
            border: none;
            color: white;
            padding: 10px;
            border-radius: 50%;
            cursor: pointer;
            z-index: 10;
        }
        @media (max-width: 768px) {
            .header h1 { font-size: 1.5rem; }
            .stream-container { margin: 10px; }
            .controls { 
                flex-direction: column; 
                gap: 10px; 
                text-align: center;
            }
            #stream { max-height: 60vh; }
        }
        @media (orientation: landscape) and (max-height: 500px) {
            .header { padding: 10px; }
            .header h1 { font-size: 1.3rem; }
            #stream { max-height: 80vh; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📹 Pi Camera Live</h1>
        <div class="status" id="status">● Live</div>
    </div>
    
    <div class="stream-container">
        <button class="fullscreen-btn" onclick="toggleFullscreen()" title="Fullscreen">⛶</button>
        <img id="stream" src="/stream.mjpg" alt="Live Camera Feed">
        <div class="controls">
            <button class="btn" onclick="refreshStream()">🔄 Refresh</button>
            <div class="quality-indicator">HD Quality</div>
            <button class="btn" onclick="toggleInfo()">ℹ Info</button>
        </div>
    </div>

    <script>
        function refreshStream() {
            const stream = document.getElementById('stream');
            const timestamp = Date.now();
            stream.src = '/stream.mjpg?' + timestamp;
        }

        function toggleFullscreen() {
            const stream = document.getElementById('stream');
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else {
                stream.requestFullscreen().catch(console.error);
            }
        }

        function toggleInfo() {
            alert('Pi Camera Module 3\\nResolution: 1920x1080\\nStatus: Connected');
        }

        // Auto-refresh if stream fails
        document.getElementById('stream').onerror = function() {
            document.getElementById('status').innerHTML = '⚠ Reconnecting...';
            setTimeout(() => {
                refreshStream();
                document.getElementById('status').innerHTML = '● Live';
            }, 2000);
        };

        // Prevent zoom on double tap
        let lastTouchEnd = 0;
        document.addEventListener('touchend', function (event) {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);
    </script>
</body>
</html>'''
            self.wfile.write(html.encode())

        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', str(len(frame)))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                print(f'Client disconnected: {self.client_address}')

        else:
            self.send_error(404)

class StreamingServer(HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == '__main__':
    # Initialize camera with 180° rotation
    picam2 = Picamera2()
    config = picam2.create_video_configuration(
        main={'size': (1920, 1080)},
        transform=Transform(hflip=True, vflip=True)
    )
    picam2.configure(config)
    
    output = StreamingOutput()
    picam2.start_recording(JpegEncoder(), FileOutput(output))
    
    try:
        server = StreamingServer(('0.0.0.0', PORT), AuthHandler)
        print(f'🚀 Pi Camera Server starting on port {PORT}')
        print(f'🔐 Username: {USERNAME} | Password: {PASSWORD}')
        print(f'🌐 Access: http://your-pi-ip:{PORT}')
        print('📱 Mobile optimized | 🔄 Auto-reconnect | 🔒 Password protected')
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n🛑 Shutting down camera server...')
    finally:
        picam2.stop_recording()
        picam2.stop()
