# web_server.py
"""
Premium Web Server for Accident Detection System
Real-time updates with WebSocket
"""

from flask import Flask, render_template, jsonify, request, Response, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
import json
import time
import threading
import os
from datetime import datetime
import queue

# Import your existing modules
from detector import AccidentDetector
from severity_classifier import SeverityClassifier
from alert_system import AlertSystem
import config

app = Flask(__name__)
app.config['SECRET_KEY'] = 'accident-detection-secret'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize components
detector = AccidentDetector()
severity_classifier = SeverityClassifier()
alert_system = AlertSystem()

# Store connected clients
connected_clients = {}
frame_queue = queue.Queue(maxsize=10)
alert_history = []
stats = {
    'total_detections': 0,
    'accidents_detected': 0,
    'severity_counts': {'MINOR': 0, 'MAJOR': 0, 'CRITICAL': 0},
    'start_time': time.time()
}

# ===== ROUTES =====

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0',
        'features': ['severity', 'confidence', 'heatmap', 'alerts']
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    uptime = time.time() - stats['start_time']
    return jsonify({
        'total_detections': stats['total_detections'],
        'accidents_detected': stats['accidents_detected'],
        'severity_counts': stats['severity_counts'],
        'uptime': format_uptime(uptime),
        'alerts_sent': alert_system.alerts_sent,
        'connected_clients': len(connected_clients)
    })

@app.route('/api/alert-history', methods=['GET'])
def get_alert_history():
    """Get recent alerts"""
    return jsonify({
        'alerts': alert_history[-20:]  # Last 20 alerts
    })

@app.route('/api/detect', methods=['POST'])
def detect():
    """Process uploaded image"""
    try:
        data = request.json
        if 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
        # Decode base64 image
        image_data = data['image'].split(',')[1]
        img_bytes = base64.b64decode(image_data)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        # Process frame
        result = detector.process_frame(frame)
        
        # Add to stats
        stats['total_detections'] += 1
        if result['accident_detected']:
            stats['accidents_detected'] += 1
            stats['severity_counts'][result['severity']] += 1
        
        # Broadcast to all clients
        socketio.emit('new_detection', result)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulate/<severity>', methods=['POST'])
def simulate_accident(severity):
    """Simulate accident for demo"""
    if severity.upper() in ['MINOR', 'MAJOR', 'CRITICAL']:
        # Create fake accident data
        accident_data = create_fake_accident(severity.upper())
        
        # Broadcast to all clients
        socketio.emit('accident_alert', accident_data)
        
        # Save to history
        alert_history.append({
            'timestamp': datetime.now().isoformat(),
            'severity': severity.upper(),
            'data': accident_data
        })
        
        return jsonify({
            'success': True,
            'message': f'{severity} accident simulated',
            'data': accident_data
        })
    
    return jsonify({'error': 'Invalid severity'}), 400

@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    """Clear alert history"""
    alert_history.clear()
    return jsonify({'success': True})

def create_fake_accident(severity):
    """Create fake accident data for simulation"""
    severity_data = {
        'MINOR': {'score': 25, 'confidence': 75, 'vehicles': 2},
        'MAJOR': {'score': 55, 'confidence': 85, 'vehicles': 3},
        'CRITICAL': {'score': 85, 'confidence': 95, 'vehicles': 4}
    }
    
    data = severity_data.get(severity, severity_data['MAJOR'])
    
    return {
        'accident_detected': True,
        'severity': severity,
        'severity_score': data['score'],
        'confidence': data['confidence'] / 100,
        'severity_confidence': data['confidence'],
        'vehicle_count': data['vehicles'],
        'timestamp': datetime.now().isoformat(),
        'location': {
            'camera_id': f'CAM-{np.random.randint(1, 10)}',
            'lat': 37.7749 + np.random.random() * 0.01,
            'lng': -122.4194 + np.random.random() * 0.01
        }
    }

# ===== WEBSOCKET EVENTS =====

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid
    connected_clients[client_id] = {
        'connected_at': time.time(),
        'ip': request.remote_addr
    }
    print(f"📱 Client connected: {client_id}")
    emit('connected', {'message': 'Connected to accident detection server'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid
    if client_id in connected_clients:
        del connected_clients[client_id]
    print(f"📱 Client disconnected: {client_id}")

@socketio.on('subscribe')
def handle_subscribe(data):
    """Subscribe to specific alerts"""
    client_id = request.sid
    channels = data.get('channels', ['all'])
    if client_id in connected_clients:
        connected_clients[client_id]['channels'] = channels
    emit('subscribed', {'channels': channels})

@socketio.on('request_stats')
def handle_stats_request():
    """Send current stats to client"""
    stats_data = get_stats().json
    emit('stats_update', stats_data)

# ===== UTILITY FUNCTIONS =====

def format_uptime(seconds):
    """Format uptime string"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def broadcast_accident(accident_data):
    """Broadcast accident to all clients"""
    socketio.emit('accident_alert', accident_data)
    
    # Add to history
    alert_history.append({
        'timestamp': datetime.now().isoformat(),
        'severity': accident_data['severity'],
        'data': accident_data
    })

# ===== BACKGROUND TASKS =====

def stats_updater():
    """Update and broadcast stats periodically"""
    while True:
        socketio.sleep(2)  # Update every 2 seconds
        stats_data = get_stats().json
        socketio.emit('stats_update', stats_data)

def alert_cleaner():
    """Clean old alerts periodically"""
    while True:
        socketio.sleep(300)  # Every 5 minutes
        # Keep only last 100 alerts
        while len(alert_history) > 100:
            alert_history.pop(0)

# Start background tasks
socketio.start_background_task(stats_updater)
socketio.start_background_task(alert_cleaner)

if __name__ == '__main__':
    print("="*60)
    print("🌐 PREMIUM WEB SERVER STARTING")
    print("="*60)
    print("📡 WebSocket enabled for real-time updates")
    print("📍 http://localhost:5000")
    print("="*60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
