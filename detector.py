# detector.py
"""
Main accident detection logic with YOLO integration
"""

import cv2
import numpy as np
from collections import deque
import config
from severity_classifier import SeverityClassifier

class AccidentDetector:
    def __init__(self):
        # Initialize components
        self.severity_classifier = SeverityClassifier()
        
        # Buffers for temporal analysis
        self.frame_buffer = deque(maxlen=10)
        self.motion_history = deque(maxlen=5)
        self.vehicle_history = deque(maxlen=10)
        
        # Try to load YOLO
        self.use_yolo = False
        try:
            from ultralytics import YOLO
            self.yolo = YOLO('yolov8n.pt')
            self.use_yolo = True
            print("✅ YOLO loaded for vehicle detection")
        except:
            print("⚠️ Using simple vehicle detection (YOLO not available)")
        
        # For demo mode
        self.demo_accident = None
        
        print("✅ Accident Detector initialized")

    def process_frame(self, frame):
        """
        Process a single frame and detect accidents
        
        Returns:
            Dictionary with detection results
        """
        
        # Check for demo forced accident first
        if self.demo_accident:
            result = self._create_demo_accident(frame, self.demo_accident)
            self.demo_accident = None
            return result
        
        # Detect vehicles
        vehicles = self.detect_vehicles(frame)
        self.vehicle_history.append(vehicles)
        
        # Calculate motion
        motion = self.calculate_motion(frame)
        self.motion_history.append(motion)
        avg_motion = np.mean(self.motion_history) if self.motion_history else 0
        
        # Check for accident
        accident_detected = False
        confidence = 0.0
        severity = 'NONE'
        severity_score = 0
        severity_confidence = 0
        severity_factors = {}
        
        # Basic accident detection logic
        if len(vehicles) >= config.MIN_VEHICLES_FOR_ACCIDENT:
            # Calculate maximum overlap
            max_overlap = 0
            for i in range(len(vehicles)):
                for j in range(i+1, len(vehicles)):
                    overlap = self._calculate_overlap(
                        vehicles[i]['bbox'],
                        vehicles[j]['bbox']
                    )
                    max_overlap = max(max_overlap, overlap)
            
            # Check if overlap exceeds threshold
            if max_overlap > config.OVERLAP_THRESHOLD:
                accident_detected = True
                confidence = min(max_overlap / 2000, 0.95)
                
                # AUTO SEVERITY CLASSIFICATION
                severity, severity_score, severity_confidence, severity_factors = \
                    self.severity_classifier.classify(vehicles, avg_motion, frame)
        
        return {
            'accident_detected': accident_detected,
            'confidence': confidence,
            'severity': severity,
            'severity_score': severity_score,
            'severity_confidence': severity_confidence,
            'severity_factors': severity_factors,
            'vehicle_count': len(vehicles),
            'vehicles': vehicles,
            'should_alert': accident_detected and severity_confidence > 60,
            'motion': avg_motion,
            'frame_shape': frame.shape
        }

    def detect_vehicles(self, frame):
        """Detect vehicles in frame using YOLO or simple method"""
        
        if self.use_yolo:
            return self._detect_vehicles_yolo(frame)
        else:
            return self._detect_vehicles_simple(frame)

    def _detect_vehicles_yolo(self, frame):
        """Use YOLO for vehicle detection"""
        vehicles = []
        
        try:
            results = self.yolo(frame, verbose=False)
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        cls = int(box.cls[0])
                        # Vehicle classes: car(2), motorcycle(3), bus(5), truck(7)
                        if cls in [2, 3, 5, 7]:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            conf = float(box.conf[0])
                            
                            vehicles.append({
                                'bbox': (x1, y1, x2, y2),
                                'confidence': conf,
                                'class': cls,
                                'center': ((x1+x2)//2, (y1+y2)//2)
                            })
        except Exception as e:
            print(f"YOLO error: {e}")
        
        return vehicles

    def _detect_vehicles_simple(self, frame):
        """Simple color-based vehicle detection for demo"""
        vehicles = []
        h, w = frame.shape[:2]
        
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Common car color ranges
        color_ranges = [
            (np.array([0, 50, 50]), np.array([10, 255, 255])),    # Red
            (np.array([90, 50, 50]), np.array([130, 255, 255])),  # Blue
            (np.array([40, 50, 50]), np.array([80, 255, 255])),   # Green
            (np.array([0, 0, 200]), np.array([180, 30, 255])),    # White
            (np.array([0, 0, 0]), np.array([180, 255, 50]))       # Black
        ]
        
        combined_mask = np.zeros((h, w), dtype=np.uint8)
        
        for lower, upper in color_ranges:
            mask = cv2.inRange(hsv, lower, upper)
            combined_mask = cv2.bitwise_or(combined_mask, mask)
        
        # Find contours
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if 500 < area < 50000:  # Filter by size
                x, y, w_box, h_box = cv2.boundingRect(contour)
                vehicles.append({
                    'bbox': (x, y, x + w_box, y + h_box),
                    'confidence': min(area / 10000, 1.0),
                    'center': (x + w_box//2, y + h_box//2)
                })
        
        return vehicles[:4]  # Limit for demo

    def calculate_motion(self, frame):
        """Calculate motion intensity using optical flow"""
        self.frame_buffer.append(frame)
        
        if len(self.frame_buffer) < 2:
            return 0
        
        # Convert to grayscale
        prev = cv2.cvtColor(self.frame_buffer[-2], cv2.COLOR_BGR2GRAY)
        curr = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate optical flow
        try:
            flow = cv2.calcOpticalFlowFarneback(prev, curr, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            return np.mean(mag)
        except:
            # Fallback to simple difference
            diff = cv2.absdiff(prev, curr)
            return np.mean(diff) / 10

    def _calculate_overlap(self, bbox1, bbox2):
        """Calculate overlap area between two bounding boxes"""
        x1, y1, x2, y2 = bbox1
        x3, y3, x4, y4 = bbox2
        
        x_left = max(x1, x3)
        y_top = max(y1, y3)
        x_right = min(x2, x4)
        y_bottom = min(y2, y4)
        
        if x_right > x_left and y_bottom > y_top:
            return (x_right - x_left) * (y_bottom - y_top)
        return 0

    def force_accident(self, severity):
        """Force accident for demo mode"""
        self.demo_accident = severity
        print(f"🎮 Demo: Forcing {severity} accident")

    def _create_demo_accident(self, frame, severity):
        """Create fake accident data for demo"""
        h, w = frame.shape[:2]
        
        # Create demo vehicles based on severity
        if severity == 'MINOR':
            vehicles = [
                {'bbox': (200, 150, 300, 250), 'confidence': 0.85},
                {'bbox': (250, 140, 350, 240), 'confidence': 0.80}
            ]
            score = 25
        elif severity == 'MAJOR':
            vehicles = [
                {'bbox': (180, 130, 320, 270), 'confidence': 0.90},
                {'bbox': (240, 120, 380, 260), 'confidence': 0.85},
                {'bbox': (300, 150, 400, 280), 'confidence': 0.75}
            ]
            score = 55
        else:  # CRITICAL
            vehicles = [
                {'bbox': (150, 100, 350, 300), 'confidence': 0.95},
                {'bbox': (200, 80, 400, 280), 'confidence': 0.92},
                {'bbox': (280, 120, 450, 320), 'confidence': 0.88},
                {'bbox': (320, 90, 480, 310), 'confidence': 0.85}
            ]
            score = 85
        
        return {
            'accident_detected': True,
            'confidence': 0.9,
            'severity': severity,
            'severity_score': score,
            'severity_confidence': 85,
            'severity_factors': {
                'overlap': score,
                'vehicle_count': len(vehicles) * 25,
                'motion': score - 10,
                'debris': score - 5
            },
            'vehicle_count': len(vehicles),
            'vehicles': vehicles,
            'should_alert': True,
            'motion': score / 2,
            'frame_shape': frame.shape
        }
