# visualizer.py
"""
Visualization module with all UI features
"""

import cv2
import numpy as np
import time
import config

class Visualizer:
    def __init__(self):
        self.colors = config.COLORS
        self.alert_flash = False
        self.last_flash_time = time.time()
        
        # For graphs
        self.confidence_history = []
        self.severity_history = []
        
        print("✅ Visualizer initialized")

    def create_dashboard(self, frame, data, fps, show_heatmap=True):
        """
        Create complete dashboard with all features
        """
        display = frame.copy()
        h, w = display.shape[:2]
        
        # 1. SEVERITY TOP BAR
        if data['accident_detected']:
            severity = data['severity']
            color = self._get_severity_color(severity)
            cv2.rectangle(display, (0, 0), (w, 30), color, -1)
            
            # Severity text
            text = f"{severity} ACCIDENT"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            text_x = (w - text_size[0]) // 2
            cv2.putText(display, text, (text_x, 22),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, config.COLORS['BLACK'], 2)
        
        # 2. SEVERITY METER (Top Left)
        self._draw_severity_meter(display, data, 10, 40)
        
        # 3. CONFIDENCE METER (Top Right)
        self._draw_confidence_meter(display, data, w - 210, 40)
        
        # 4. VEHICLE BOUNDING BOXES
        self._draw_vehicle_boxes(display, data)
        
        # 5. HEATMAP (if enabled)
        if show_heatmap and data['accident_detected']:
            display = self._draw_heatmap(display, data)
        
        # 6. ALERT OVERLAY (if accident)
        if data['accident_detected'] and data['should_alert']:
            display = self._draw_alert_overlay(display, data)
        
        # 7. BOTTOM INFO BAR
        self._draw_info_bar(display, data, fps, h, w)
        
        # 8. SEVERITY FACTORS (Bottom Left)
        if 'severity_factors' in data and data['severity_factors']:
            self._draw_severity_factors(display, data['severity_factors'], 10, h - 150)
        
        return display

    def _draw_severity_meter(self, frame, data, x, y):
        """Draw severity meter"""
        if 'severity_score' not in data:
            return
        
        score = data['severity_score']
        severity = data.get('severity', 'NONE')
        color = self._get_severity_color(severity)
        
        # Background
        cv2.rectangle(frame, (x, y), (x + 200, y + 30), (50, 50, 50), -1)
        
        # Fill
        fill_width = int(200 * score / 100)
        cv2.rectangle(frame, (x, y), (x + fill_width, y + 30), color, -1)
        
        # Border
        cv2.rectangle(frame, (x, y), (x + 200, y + 30), (255, 255, 255), 1)
        
        # Text
        cv2.putText(frame, f"Severity: {severity}", (x + 5, y + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, config.COLORS['WHITE'], 1)

    def _draw_confidence_meter(self, frame, data, x, y):
        """Draw confidence meter"""
        confidence = data.get('severity_confidence', data.get('confidence', 0) * 100)
        
        # Color based on confidence
        if confidence > 80:
            color = (0, 255, 0)  # Green
        elif confidence > 50:
            color = (0, 255, 255)  # Yellow
        else:
            color = (0, 0, 255)  # Red
        
        # Background
        cv2.rectangle(frame, (x, y), (x + 200, y + 30), (50, 50, 50), -1)
        
        # Fill
        fill_width = int(200 * confidence / 100)
        cv2.rectangle(frame, (x, y), (x + fill_width, y + 30), color, -1)
        
        # Border
        cv2.rectangle(frame, (x, y), (x + 200, y + 30), (255, 255, 255), 1)
        
        # Text
        cv2.putText(frame, f"Confidence: {confidence:.0f}%", (x + 5, y + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, config.COLORS['WHITE'], 1)

    def _draw_vehicle_boxes(self, frame, data):
        """Draw bounding boxes around vehicles"""
        if 'vehicles' not in data:
            return
        
        severity = data.get('severity', 'NONE')
        
        for vehicle in data['vehicles']:
            x1, y1, x2, y2 = vehicle['bbox']
            
            # Color based on accident status
            if data['accident_detected']:
                color = self._get_severity_color(severity)
            else:
                color = (0, 255, 0)  # Green for normal
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Confidence text
            conf = vehicle.get('confidence', 0)
            cv2.putText(frame, f"{conf:.1f}", (x1, y1-5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    def _draw_heatmap(self, frame, data):
        """Draw impact heatmap"""
        h, w = frame.shape[:2]
        overlay = np.zeros((h, w, 3), dtype=np.uint8)
        
        if 'vehicles' in data:
            for vehicle in data['vehicles']:
                x1, y1, x2, y2 = vehicle['bbox']
                center = ((x1+x2)//2, (y1+y2)//2)
                
                # Draw heat circles
                intensity = data.get('severity_score', 50) / 100
                
                # Inner circle (hottest)
                cv2.circle(overlay, center, 30, (0, 0, 255), -1)
                
                # Middle circle
                cv2.circle(overlay, center, 60, (0, 100, 255), -1)
                
                # Outer circle
                cv2.circle(overlay, center, 90, (0, 255, 255), -1)
        
        # Blend with original
        return cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)

    def _draw_alert_overlay(self, frame, data):
        """Draw flashing alert overlay"""
        current_time = time.time()
        
        # Flash every 0.5 seconds
        if current_time - self.last_flash_time > 0.5:
            self.alert_flash = not self.alert_flash
            self.last_flash_time = current_time
        
        if self.alert_flash:
            h, w = frame.shape[:2]
            
            # Red border
            cv2.rectangle(frame, (0, 0), (w, h), (0, 0, 255), 10)
            
            # Alert banner
            cv2.rectangle(frame, (0, 0), (w, 80), (0, 0, 150), -1)
            
            # Alert text
            severity = data['severity']
            text = f"🚨 {severity} ACCIDENT DETECTED! 🚨"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
            text_x = (w - text_size[0]) // 2
            cv2.putText(frame, text, (text_x, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, config.COLORS['WHITE'], 2)
        
        return frame

    def _draw_info_bar(self, frame, data, fps, h, w):
        """Draw bottom information bar"""
        # Background
        cv2.rectangle(frame, (0, h-30), (w, h), (30, 30, 30), -1)
        
        # FPS
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, h-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, config.COLORS['WHITE'], 1)
        
        # Vehicle count
        cv2.putText(frame, f"Vehicles: {data['vehicle_count']}", (150, h-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, config.COLORS['WHITE'], 1)
        
        # Time
        current_time = time.strftime("%H:%M:%S")
        time_size = cv2.getTextSize(current_time, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        cv2.putText(frame, current_time, (w - time_size[0] - 10, h-10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, config.COLORS['WHITE'], 1)
        
        # Controls hint
        cv2.putText(frame, "1:Minor 2:Major 3:Critical H:Heatmap Q:Quit", 
                   (w//2 - 200, h-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, config.COLORS['GRAY'], 1)

    def _draw_severity_factors(self, frame, factors, x, y):
        """Draw severity factor breakdown"""
        cv2.putText(frame, "Severity Factors:", (x, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, config.COLORS['WHITE'], 1)
        
        factor_names = {
            'overlap': 'Overlap',
            'vehicle_count': 'Vehicles',
            'motion': 'Motion',
            'debris': 'Debris'
        }
        
        y_offset = y + 20
        for key, value in list(factors.items())[:4]:
            name = factor_names.get(key, key)
            cv2.putText(frame, f"{name}: {value:.0f}", (x + 10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, config.COLORS['GRAY'], 1)
            y_offset += 15

    def _get_severity_color(self, severity):
        """Get color for severity level"""
        colors = {
            'MINOR': config.COLORS['MINOR'],
            'MAJOR': config.COLORS['MAJOR'],
            'CRITICAL': config.COLORS['CRITICAL'],
            'NONE': config.COLORS['NORMAL']
        }
        return colors.get(severity, config.COLORS['WHITE'])

    def draw_help_screen(self, frame):
        """Draw help screen"""
        h, w = frame.shape[:2]
        
        # Dark overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.3, overlay, 0.7, 0)
        
        # Help box
        cv2.rectangle(frame, (w//4, h//4), (3*w//4, 3*h//4), (50, 50, 50), -1)
        cv2.rectangle(frame, (w//4, h//4), (3*w//4, 3*h//4), (255, 255, 255), 2)
        
        # Title
        cv2.putText(frame, "CONTROLS", (w//2 - 80, h//4 + 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, config.COLORS['WHITE'], 2)
        
        # Controls
        controls = [
            ("1", "Simulate MINOR accident"),
            ("2", "Simulate MAJOR accident"),
            ("3", "Simulate CRITICAL accident"),
            ("H", "Toggle heatmap"),
            ("S", "Save screenshot"),
            ("SPACE", "Pause/Resume"),
            ("Q", "Quit")
        ]
        
        y_offset = h//4 + 80
        for key, desc in controls:
            cv2.putText(frame, f"{key}: {desc}", (w//4 + 40, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.COLORS['WHITE'], 1)
            y_offset += 30
        
        return frame
