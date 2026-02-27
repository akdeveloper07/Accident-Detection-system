# severity_classifier.py
"""
Automatic severity classification for accidents
Classifies as: MINOR 🟡, MAJOR 🟠, or CRITICAL 🔴
"""

import cv2
import numpy as np
import math
from collections import deque
import config

class SeverityClassifier:
    """
    AUTOMATICALLY identifies accident severity based on:
    - Vehicle overlap area
    - Number of vehicles involved
    - Motion intensity
    - Debris detection
    - Speed change
    - Collision angle
    """
    
    def __init__(self):
        self.severity_levels = {
            'MINOR': {'color': config.COLORS['MINOR'], 'threshold': 30, 'emoji': '🟡'},
            'MAJOR': {'color': config.COLORS['MAJOR'], 'threshold': 60, 'emoji': '🟠'},
            'CRITICAL': {'color': config.COLORS['CRITICAL'], 'threshold': 90, 'emoji': '🔴'}
        }
        
        # Tracking variables
        self.severity_history = deque(maxlen=30)
        self.last_severity = 'NONE'
        self.vehicle_positions = {}  # Track vehicles across frames
        self.frame_count = 0
        
        print("✅ Severity Classifier initialized")

    def classify(self, vehicles, motion_data, frame=None):
        """
        AUTOMATICALLY classify accident severity
        
        Args:
            vehicles: List of detected vehicles with bbox
            motion_data: Average motion intensity
            frame: Current frame (for debris detection)
            
        Returns:
            severity: 'MINOR', 'MAJOR', or 'CRITICAL'
            score: 0-100 severity score
            confidence: 0-100 confidence in classification
            factors: Dictionary of individual factor scores
        """
        
        # Calculate all severity factors (0-100 each)
        factors = {}
        
        # FACTOR 1: Vehicle Overlap Area (0-100)
        factors['overlap'] = self._calculate_overlap_score(vehicles)
        
        # FACTOR 2: Number of Vehicles (0-100)
        factors['vehicle_count'] = self._calculate_vehicle_count_score(vehicles)
        
        # FACTOR 3: Motion Intensity (0-100)
        factors['motion'] = self._calculate_motion_score(motion_data)
        
        # FACTOR 4: Debris Detection (0-100)
        if frame is not None:
            factors['debris'] = self._detect_debris_score(frame, vehicles)
        else:
            factors['debris'] = 0
        
        # FACTOR 5: Speed Change (0-100)
        factors['speed_change'] = self._calculate_speed_change_score(vehicles)
        
        # FACTOR 6: Collision Angle (0-100)
        factors['angle'] = self._calculate_collision_angle_score(vehicles)
        
        # Weighted total score
        weights = {
            'overlap': 0.25,
            'vehicle_count': 0.20,
            'motion': 0.20,
            'debris': 0.15,
            'speed_change': 0.10,
            'angle': 0.10
        }
        
        total_score = 0
        for factor, score in factors.items():
            total_score += score * weights.get(factor, 0)
        
        # Determine severity level
        severity = self._get_severity_level(total_score)
        
        # Calculate confidence
        confidence = self._calculate_confidence(factors, total_score)
        
        # Store in history
        self.severity_history.append({
            'severity': severity,
            'score': total_score,
            'confidence': confidence,
            'frame': self.frame_count
        })
        
        self.last_severity = severity
        self.frame_count += 1
        
        return severity, total_score, confidence, factors

    def _calculate_overlap_score(self, vehicles):
        """Calculate severity based on vehicle overlap"""
        if len(vehicles) < 2:
            return 0
        
        total_overlap = 0
        overlap_count = 0
        
        for i in range(len(vehicles)):
            for j in range(i+1, len(vehicles)):
                overlap = self._bbox_overlap(
                    vehicles[i]['bbox'], 
                    vehicles[j]['bbox']
                )
                if overlap > 0:
                    total_overlap += overlap
                    overlap_count += 1
        
        if overlap_count == 0:
            return 0
        
        avg_overlap = total_overlap / overlap_count
        
        # Convert to score (0-100)
        if avg_overlap < 1000:
            return (avg_overlap / 1000) * 30  # 0-30
        elif avg_overlap < 5000:
            return 30 + ((avg_overlap - 1000) / 4000) * 40  # 30-70
        else:
            return 70 + min((avg_overlap - 5000) / 5000, 1) * 30  # 70-100

    def _bbox_overlap(self, bbox1, bbox2):
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

    def _calculate_vehicle_count_score(self, vehicles):
        """More vehicles = higher severity"""
        count = len(vehicles)
        
        if count <= 1:
            return 0
        elif count == 2:
            return 40
        elif count == 3:
            return 70
        else:
            return 100

    def _calculate_motion_score(self, motion_data):
        """Higher motion = higher severity"""
        if motion_data is None:
            return 50
        
        if motion_data < 10:
            return 20
        elif motion_data < 30:
            return 60
        else:
            return 95

    def _detect_debris_score(self, frame, vehicles):
        """Detect debris/spatter around accident"""
        if frame is None or len(vehicles) < 2:
            return 0
        
        # Get accident area
        accident_area = self._get_accident_area(frame, vehicles)
        if accident_area is None:
            return 0
        
        x1, y1, x2, y2 = accident_area
        
        # Convert to grayscale and detect edges
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Count edge pixels in accident area
        roi = edges[y1:y2, x1:x2]
        edge_pixels = np.sum(roi > 0)
        total_pixels = roi.size
        
        if total_pixels == 0:
            return 0
        
        edge_density = (edge_pixels / total_pixels) * 100
        
        # Convert to score
        if edge_density < 5:
            return 20
        elif edge_density < 15:
            return 60
        else:
            return 95

    def _get_accident_area(self, frame, vehicles):
        """Get bounding box covering all vehicles"""
        if not vehicles:
            return None
        
        h, w = frame.shape[:2]
        
        x1 = min(v['bbox'][0] for v in vehicles)
        y1 = min(v['bbox'][1] for v in vehicles)
        x2 = max(v['bbox'][2] for v in vehicles)
        y2 = max(v['bbox'][3] for v in vehicles)
        
        # Add padding
        padding = 50
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(w, x2 + padding)
        y2 = min(h, y2 + padding)
        
        return (x1, y1, x2, y2)

    def _calculate_speed_change_score(self, vehicles):
        """Detect sudden speed changes (simplified)"""
        # In real system, track vehicles across frames
        # For demo, return moderate score
        return 50

    def _calculate_collision_angle_score(self, vehicles):
        """Head-on collisions more severe (simplified)"""
        if len(vehicles) < 2:
            return 0
        return 60

    def _get_severity_level(self, score):
        """Convert score to severity level"""
        if score < config.SEVERITY_THRESHOLDS['MINOR']:
            return 'MINOR'
        elif score < config.SEVERITY_THRESHOLDS['MAJOR']:
            return 'MAJOR'
        else:
            return 'CRITICAL'

    def _calculate_confidence(self, factors, total_score):
        """Calculate confidence in classification"""
        scores = list(factors.values())
        if not scores:
            return 0
        
        # Lower standard deviation = higher confidence
        std_dev = np.std(scores)
        max_std = 50
        confidence = max(0, 100 - (std_dev / max_std) * 100)
        
        # Lower confidence near thresholds
        if 25 < total_score < 35 or 55 < total_score < 65:
            confidence *= 0.8
        
        return min(confidence, 100)

    def get_severity_color(self, severity):
        """Get color for severity level"""
        return self.severity_levels.get(severity, {'color': config.COLORS['WHITE']})['color']

    def get_severity_emoji(self, severity):
        """Get emoji for severity level"""
        return self.severity_levels.get(severity, {'emoji': '⚪'})['emoji']

    def get_statistics(self):
        """Get severity statistics"""
        if not self.severity_history:
            return "No accidents detected"
        
        recent = list(self.severity_history)[-10:]
        severities = [s['severity'] for s in recent]
        
        return {
            'current': self.last_severity,
            'minor': severities.count('MINOR'),
            'major': severities.count('MAJOR'),
            'critical': severities.count('CRITICAL'),
            'total': len(recent)
        }
