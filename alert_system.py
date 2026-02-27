# alert_system.py
"""
Emergency alert simulation system
"""

import cv2
import time
import os
from datetime import datetime
import config

class AlertSystem:
    def __init__(self):
        self.alerts_sent = 0
        self.last_alert_time = 0
        self.alert_cooldown = config.ALERT_COOLDOWN
        
        # Create evidence folder
        os.makedirs(config.EVIDENCE_FOLDER, exist_ok=True)
        
        print("✅ Alert System initialized")

    def trigger_alert(self, frame, accident_data):
        """
        Trigger emergency alert simulation
        """
        current_time = time.time()
        
        # Check cooldown
        if current_time - self.last_alert_time < self.alert_cooldown:
            return False
        
        severity = accident_data.get('severity', 'UNKNOWN')
        confidence = accident_data.get('severity_confidence', accident_data.get('confidence', 0) * 100)
        
        # Create timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save evidence
        if config.SAVE_EVIDENCE and frame is not None:
            evidence_path = os.path.join(
                config.EVIDENCE_FOLDER, 
                f"accident_{severity}_{file_timestamp}.jpg"
            )
            cv2.imwrite(evidence_path, frame)
        
        # Create alert message
        alert_message = f"""
╔══════════════════════════════════════════════════════════╗
║                    🚨 EMERGENCY ALERT                     ║
╠══════════════════════════════════════════════════════════╣
║  Time: {timestamp}                   
║  Severity: {severity} ({self._get_severity_emoji(severity)})                  
║  Confidence: {confidence:.1f}%                            
║  Vehicles Involved: {accident_data.get('vehicle_count', 0)}                      
║  Location: Camera Feed (Simulated)                       
╠══════════════════════════════════════════════════════════╣
║  🚑 AMBULANCE: Dispatched (ETA: 5 minutes)                ║
║  👮 POLICE: Dispatched (ETA: 7 minutes)                   ║
║  🔥 FIRE: {'Dispatched' if severity == 'CRITICAL' else 'Standby'}                     ║
╠══════════════════════════════════════════════════════════╣
║  Evidence: {evidence_path if config.SAVE_EVIDENCE else 'Not saved'}  
╚══════════════════════════════════════════════════════════╝
"""
        
        # Print alert
        print(alert_message)
        
        # Update counters
        self.alerts_sent += 1
        self.last_alert_time = current_time
        
        # Log to file
        self._log_alert(timestamp, severity, confidence, evidence_path if config.SAVE_EVIDENCE else None)
        
        return True

    def _get_severity_emoji(self, severity):
        """Get emoji for severity"""
        emojis = {
            'MINOR': '🟡',
            'MAJOR': '🟠',
            'CRITICAL': '🔴'
        }
        return emojis.get(severity, '⚪')

    def _log_alert(self, timestamp, severity, confidence, evidence_path):
        """Log alert to file"""
        log_path = os.path.join(config.EVIDENCE_FOLDER, "alerts.log")
        
        with open(log_path, 'a') as f:
            f.write(f"{timestamp} | {severity} | Confidence: {confidence:.1f}% | Evidence: {evidence_path}\n")

    def simulate_emergency_call(self):
        """Simulate emergency phone call (for demo)"""
        print("\n📞 SIMULATING EMERGENCY CALL...")
        time.sleep(1)
        print("   Dialing 911...")
        time.sleep(1)
        print("   Operator: What's your emergency?")
        time.sleep(1)
        print("   System: Automatic accident detection system reporting...")
        time.sleep(1)
        print("   ✅ Emergency services notified\n")

    def get_stats(self):
        """Get alert statistics"""
        return {
            'alerts_sent': self.alerts_sent,
            'last_alert': self.last_alert_time,
            'cooldown': self.alert_cooldown
        }
