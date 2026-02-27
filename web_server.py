# web_server.py
"""
Complete Backend Server for Accident Detection System
Integrates with existing style.css, script.js, and 404.html
"""

from flask import Flask, render_template, jsonify, request, send_from_directory, abort
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
import json
import time
import threading
import os
import logging
from datetime import datetime
import random
from collections import deque

# ===== INITIALIZATION =====

app = Flask(__name__, 
            static_folder='.',  # Serve static files from current directory
            static_url_path='')  # Empty URL path for static files

app.config['SECRET_KEY'] = 'accident-detection-secret-2026'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max upload

# Enable CORS
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='threading',
                   ping_timeout=60,
                   ping_interval=25)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== DATA STORAGE =====

# Store connected clients
connected_clients = {}

# Store alert history
alert_history = deque(maxlen=100)

# Store detection statistics
stats = {
    'total_detections': 0,
    'accidents_detected': 0,
    'severity_counts': {'MINOR': 0, 'MAJOR': 0, 'CRITICAL': 0},
    'start_time': time.time(),
    'active_cameras': 0,
    'alerts_sent': 0
}

# Store recent detections for dashboard
recent_detections = deque(maxlen=50)

# ===== ACCIDENT DETECTION MODULE =====

class AccidentDetector:
    """Simulated accident detector for demo purposes"""
    
    def __init__(self):
        self.detection_history = deque(maxlen=10)
        self.confidence_threshold = 0.6
        
    def process_frame(self, frame_data=None):
        """
        Process frame and detect accidents
        Returns detection results
        """
        # Simulate detection (in real app, this would use ML models)
        accident_detected = random.random() > 0.7  # 30% chance
        
        if accident_detected:
            severity = random.choice(['MINOR', 'MAJOR', 'CRITICAL'])
            confidence = random.uniform(0.75, 0.98)
            
            # Severity-specific confidence
            if severity == 'MINOR':
                confidence = random.uniform(0.75, 0.85)
            elif severity == 'MAJOR':
                confidence = random.uniform(0.85, 0.92)
            else:
                confidence = random.uniform(0.92, 0.98)
            
            # Severity factors
            severity_factors = {
                'overlap': random.uniform(20, 100),
                'motion': random.uniform(30, 95),
                'debris': random.uniform(10, 90),
                'vehicle_count': random.randint(2, 5)
            }
            
            vehicle_count = random.randint(2, 4)
            
        else:
            severity = 'NONE'
            confidence = random.uniform(0.1, 0.3)
            severity_factors = {
                'overlap': random.uniform(0, 20),
                'motion': random.uniform(0, 30),
                'debris': random.uniform(0, 10),
                'vehicle_count': random.randint(0, 2)
            }
            vehicle_count = random.randint(0, 3)
        
        result = {
            'accident_detected': accident_detected,
            'severity': severity,
            'confidence': confidence,
            'severity_confidence': confidence * 100,
            'severity_score': random.uniform(20, 95) if accident_detected else random.uniform(0, 20),
            'severity_factors': severity_factors,
            'vehicle_count': vehicle_count,
            'timestamp': datetime.now().isoformat(),
            'detection_id': f"DET-{int(time.time())}-{random.randint(1000, 9999)}"
        }
        
        self.detection_history.append(result)
        return result
    
    def get_statistics(self):
        """Get detection statistics"""
        if not self.detection_history:
            return {'accuracy': 0, 'avg_confidence': 0}
        
        detections = list(self.detection_history)
        accidents = [d for d in detections if d['accident_detected']]
        
        return {
            'total_frames': len(detections),
            'accidents_detected': len(accidents),
            'avg_confidence': np.mean([d['confidence'] for d in detections]) * 100,
            'accuracy': random.uniform(94, 98)  # Simulated accuracy
        }

# Initialize detector
detector = AccidentDetector()

# ===== AUTHENTICATION MODULE =====

class AuthManager:
    """Simple authentication manager"""
    
    def __init__(self):
        self.users = {
            'admin': {
                'password': 'admin123',  # In production, use hashed passwords
                'role': 'admin',
                'name': 'Administrator'
            },
            'operator': {
                'password': 'operator123',
                'role': 'operator',
                'name': 'System Operator'
            }
        }
        self.sessions = {}
    
    def authenticate(self, username, password):
        """Authenticate user"""
        if username in self.users and self.users[username]['password'] == password:
            token = self.generate_token(username)
            self.sessions[token] = {
                'username': username,
                'role': self.users[username]['role'],
                'login_time': time.time()
            }
            return {
                'success': True,
                'token': token,
                'user': {
                    'name': self.users[username]['name'],
                    'role': self.users[username]['role']
                }
            }
        return {'success': False, 'message': 'Invalid credentials'}
    
    def generate_token(self, username):
        """Generate session token"""
        import hashlib
        token_string = f"{username}{time.time()}{random.random()}"
        return hashlib.md5(token_string.encode()).hexdigest()
    
    def verify_token(self, token):
        """Verify session token"""
        return token in self.sessions
    
    def logout(self, token):
        """Logout user"""
        if token in self.sessions:
            del self.sessions[token]
            return True
        return False

auth_manager = AuthManager()

# ===== API ROUTES =====

@app.route('/')
def index():
    """Serve main page"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    if os.path.exists(path):
        return send_from_directory('.', path)
    return render_template('404.html'), 404

# ===== API ENDPOINTS =====

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check endpoint"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'features': ['severity', 'confidence', 'heatmap', 'alerts', 'realtime'],
        'connections': len(connected_clients)
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics"""
    uptime_seconds = time.time() - stats['start_time']
    uptime = {
        'hours': int(uptime_seconds // 3600),
        'minutes': int((uptime_seconds % 3600) // 60),
        'seconds': int(uptime_seconds % 60)
    }
    
    detection_stats = detector.get_statistics()
    
    return jsonify({
        'total_detections': stats['total_detections'],
        'accidents_detected': stats['accidents_detected'],
        'severity_counts': stats['severity_counts'],
        'uptime': f"{uptime['hours']:02d}:{uptime['minutes']:02d}:{uptime['seconds']:02d}",
        'uptime_raw': uptime_seconds,
        'alerts_sent': stats['alerts_sent'],
        'active_cameras': stats['active_cameras'],
        'connected_clients': len(connected_clients),
        'detection_accuracy': detection_stats.get('accuracy', 0),
        'avg_confidence': detection_stats.get('avg_confidence', 0)
    })

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get alert history"""
    limit = request.args.get('limit', 20, type=int)
    severity = request.args.get('severity', None)
    
    alerts = list(alert_history)
    if severity:
        alerts = [a for a in alerts if a['severity'] == severity.upper()]
    
    return jsonify({
        'total': len(alerts),
        'alerts': alerts[-limit:]
    })

@app.route('/api/alerts/<alert_id>', methods=['GET'])
def get_alert(alert_id):
    """Get specific alert"""
    for alert in alert_history:
        if alert.get('id') == alert_id or alert.get('detection_id') == alert_id:
            return jsonify(alert)
    return jsonify({'error': 'Alert not found'}), 404

@app.route('/api/detect', methods=['POST'])
def detect():
    """Process image for accident detection"""
    try:
        data = request.json
        
        # Get image data
        image_data = data.get('image', '')
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Process image (simulated)
        result = detector.process_frame()
        
        # Update stats
        stats['total_detections'] += 1
        if result['accident_detected']:
            stats['accidents_detected'] += 1
            stats['severity_counts'][result['severity']] += 1
            
            # Add to alert history
            alert_entry = {
                'id': result['detection_id'],
                'timestamp': result['timestamp'],
                'severity': result['severity'],
                'confidence': result['confidence'],
                'vehicle_count': result['vehicle_count'],
                'location': f"Camera-{random.randint(1, 8)}"
            }
            alert_history.append(alert_entry)
            
            # Broadcast to all clients
            socketio.emit('accident_alert', alert_entry)
        
        # Add to recent detections
        recent_detections.append(result)
        
        # Broadcast detection update
        socketio.emit('new_detection', {
            'accident_detected': result['accident_detected'],
            'confidence': result['confidence'],
            'timestamp': result['timestamp']
        })
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Detection error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulate/<severity>', methods=['POST'])
def simulate_accident(severity):
    """Simulate accident for testing"""
    severity = severity.upper()
    
    if severity not in ['MINOR', 'MAJOR', 'CRITICAL']:
        return jsonify({'error': 'Invalid severity'}), 400
    
    # Create simulated accident data
    severity_data = {
        'MINOR': {
            'confidence': random.uniform(0.75, 0.85),
            'score': random.uniform(20, 35),
            'vehicles': random.randint(2, 3),
            'color': '#f59e0b'
        },
        'MAJOR': {
            'confidence': random.uniform(0.85, 0.92),
            'score': random.uniform(45, 65),
            'vehicles': random.randint(3, 4),
            'color': '#6366f1'
        },
        'CRITICAL': {
            'confidence': random.uniform(0.92, 0.98),
            'score': random.uniform(75, 95),
            'vehicles': random.randint(4, 6),
            'color': '#ef4444'
        }
    }
    
    data = severity_data[severity]
    
    accident_data = {
        'id': f"SIM-{int(time.time())}-{random.randint(1000, 9999)}",
        'timestamp': datetime.now().isoformat(),
        'severity': severity,
        'confidence': data['confidence'],
        'severity_score': data['score'],
        'vehicle_count': data['vehicles'],
        'location': f"Camera-{random.randint(1, 8)}",
        'simulated': True,
        'severity_factors': {
            'overlap': random.uniform(40, 95),
            'motion': random.uniform(50, 98),
            'debris': random.uniform(30, 90)
        }
    }
    
    # Add to alert history
    alert_history.append(accident_data)
    
    # Update stats
    stats['accidents_detected'] += 1
    stats['severity_counts'][severity] += 1
    
    # Broadcast to all clients
    socketio.emit('accident_alert', accident_data)
    
    # Trigger confetti for critical accidents
    if severity == 'CRITICAL':
        socketio.emit('celebration', {'type': 'confetti'})
    
    return jsonify({
        'success': True,
        'message': f'{severity} accident simulated',
        'data': accident_data
    })

@app.route('/api/clear-alerts', methods=['POST'])
def clear_alerts():
    """Clear alert history"""
    alert_history.clear()
    socketio.emit('alerts_cleared', {'timestamp': datetime.now().isoformat()})
    return jsonify({'success': True, 'message': 'Alert history cleared'})

@app.route('/api/login', methods=['POST'])
def login():
    """User login"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400
    
    result = auth_manager.authenticate(username, password)
    return jsonify(result)

@app.route('/api/logout', methods=['POST'])
def logout():
    """User logout"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if auth_manager.logout(token):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Invalid token'}), 401

@app.route('/api/verify-token', methods=['POST'])
def verify_token():
    """Verify session token"""
    token = request.json.get('token')
    if auth_manager.verify_token(token):
        return jsonify({'valid': True})
    return jsonify({'valid': False}), 401

@app.route('/api/camera/status', methods=['GET'])
def camera_status():
    """Get camera status"""
    return jsonify({
        'cameras': [
            {'id': 1, 'name': 'Highway Exit 24', 'status': 'active', 'type': 'highway'},
            {'id': 2, 'name': 'Downtown Intersection', 'status': 'active', 'type': 'intersection'},
            {'id': 3, 'name': 'School Zone', 'status': 'active', 'type': 'school'},
            {'id': 4, 'name': 'Bridge Crossing', 'status': 'maintenance', 'type': 'bridge'},
            {'id': 5, 'name': 'Tunnel Entry', 'status': 'active', 'type': 'tunnel'},
            {'id': 6, 'name': 'Parking Garage', 'status': 'inactive', 'type': 'parking'},
            {'id': 7, 'name': 'Roundabout', 'status': 'active', 'type': 'roundabout'},
            {'id': 8, 'name': 'Pedestrian Crossing', 'status': 'active', 'type': 'crosswalk'}
        ]
    })

@app.route('/api/camera/<int:camera_id>/stream', methods=['GET'])
def camera_stream(camera_id):
    """Get camera stream URL or data"""
    # Simulate stream URL
    return jsonify({
        'camera_id': camera_id,
        'stream_url': f'/static/streams/camera_{camera_id}.jpg',
        'status': 'online',
        'resolution': '1920x1080',
        'fps': 30
    })

@app.route('/api/export/alerts', methods=['GET'])
def export_alerts():
    """Export alerts as JSON"""
    format = request.args.get('format', 'json')
    
    if format == 'json':
        return jsonify({
            'exported_at': datetime.now().isoformat(),
            'total_alerts': len(alert_history),
            'alerts': list(alert_history)
        })
    elif format == 'csv':
        # Generate CSV
        csv_data = "timestamp,severity,confidence,vehicle_count,location\n"
        for alert in alert_history:
            csv_data += f"{alert['timestamp']},{alert['severity']},{alert['confidence']:.2f},{alert.get('vehicle_count',0)},{alert.get('location','unknown')}\n"
        
        return Response(
            csv_data,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=alerts.csv'}
        )
    
    return jsonify({'error': 'Unsupported format'}), 400

# ===== WEBSOCKET EVENTS =====

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid
    connected_clients[client_id] = {
        'connected_at': time.time(),
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    }
    logger.info(f"Client connected: {client_id}")
    
    # Send welcome message
    emit('connected', {
        'message': 'Connected to accident detection server',
        'timestamp': datetime.now().isoformat(),
        'client_id': client_id
    })
    
    # Update client count
    emit('client_count', {'count': len(connected_clients)}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid
    if client_id in connected_clients:
        del connected_clients[client_id]
    logger.info(f"Client disconnected: {client_id}")
    
    # Update client count
    emit('client_count', {'count': len(connected_clients)}, broadcast=True)

@socketio.on('subscribe')
def handle_subscribe(data):
    """Handle subscription to channels"""
    channels = data.get('channels', ['all'])
    client_id = request.sid
    
    if client_id in connected_clients:
        connected_clients[client_id]['channels'] = channels
    
    emit('subscribed', {
        'channels': channels,
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    """Handle unsubscription from channels"""
    channels = data.get('channels', [])
    client_id = request.sid
    
    if client_id in connected_clients and 'channels' in connected_clients[client_id]:
        current = set(connected_clients[client_id]['channels'])
        to_remove = set(channels)
        connected_clients[client_id]['channels'] = list(current - to_remove)
    
    emit('unsubscribed', {
        'channels': channels,
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('request_stats')
def handle_stats_request():
    """Send current stats to client"""
    stats_data = get_stats().json
    emit('stats_update', stats_data)

@socketio.on('request_alerts')
def handle_alerts_request():
    """Send recent alerts to client"""
    emit('alerts_update', {
        'alerts': list(alert_history)[-20:],
        'total': len(alert_history)
    })

@socketio.on('ping')
def handle_ping():
    """Handle ping for connection testing"""
    emit('pong', {'timestamp': time.time()})

@socketio.on('simulate_detection')
def handle_simulation(data):
    """Handle manual detection simulation from client"""
    severity = data.get('severity', 'MAJOR')
    
    # Create simulated detection
    detection = detector.process_frame()
    detection['manual'] = True
    detection['severity'] = severity
    
    # Broadcast to all clients
    emit('new_detection', detection, broadcast=True)
    
    if detection['accident_detected']:
        emit('accident_alert', detection, broadcast=True)

# ===== BACKGROUND TASKS =====

def stats_broadcaster():
    """Broadcast stats to all clients periodically"""
    while True:
        socketio.sleep(2)  # Update every 2 seconds
        stats_data = get_stats().json
        socketio.emit('stats_update', stats_data)

def random_detection_simulator():
    """Simulate random detections for demo"""
    while True:
        socketio.sleep(random.randint(10, 30))  # Random interval
        if random.random() > 0.5:  # 50% chance
            detection = detector.process_frame()
            socketio.emit('new_detection', detection)
            
            if detection['accident_detected']:
                # Add to alert history
                alert_entry = {
                    'id': detection['detection_id'],
                    'timestamp': detection['timestamp'],
                    'severity': detection['severity'],
                    'confidence': detection['confidence'],
                    'vehicle_count': detection['vehicle_count'],
                    'location': f"Camera-{random.randint(1, 8)}"
                }
                alert_history.append(alert_entry)
                
                socketio.emit('accident_alert', alert_entry)

# Start background tasks
socketio.start_background_task(stats_broadcaster)
socketio.start_background_task(random_detection_simulator)

# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return send_from_directory('.', '404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large_error(error):
    """Handle file too large errors"""
    return jsonify({'error': 'File too large'}), 413

# ===== MAIN ENTRY POINT =====

if __name__ == '__main__':
    print("="*60)
    print("🚗 PREMIUM ACCIDENT DETECTION SYSTEM")
    print("="*60)
    print("📡 Server: http://localhost:5000")
    print("🔌 WebSocket: ws://localhost:5000/socket.io")
    print("📊 API: http://localhost:5000/api/health")
    print("="*60)
    print("✅ Connected to frontend files:")
    print("   - style.css")
    print("   - script.js")
    print("   - 404.html")
    print("="*60)
    print("🎮 Demo Credentials:")
    print("   Admin: admin / admin123")
    print("   Operator: operator / operator123")
    print("="*60)
    
    # Run the server
    socketio.run(app, 
                host='0.0.0.0', 
                port=5000, 
                debug=True,
                allow_unsafe_werkzeug=True)
