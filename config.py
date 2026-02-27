# config.py
"""
Configuration settings for Accident Detection System
"""

# Camera/Video Settings
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FPS_TARGET = 30

# Detection Settings
ACCIDENT_THRESHOLD = 0.6
MIN_VEHICLES_FOR_ACCIDENT = 2
OVERLAP_THRESHOLD = 500  # pixels

# Severity Thresholds
SEVERITY_THRESHOLDS = {
    'MINOR': 30,      # 0-30
    'MAJOR': 60,      # 30-60
    'CRITICAL': 90    # 60-100
}

# Alert Settings
ALERT_COOLDOWN = 3  # seconds
SAVE_EVIDENCE = True
EVIDENCE_FOLDER = "evidence"

# Visualization
SHOW_FPS = True
SHOW_VEHICLE_COUNTS = True
DEFAULT_HEATMAP = True

# Colors (BGR format)
COLORS = {
    'MINOR': (0, 255, 255),     # Yellow
    'MAJOR': (0, 165, 255),     # Orange
    'CRITICAL': (0, 0, 255),    # Red
    'NORMAL': (0, 255, 0),      # Green
    'WHITE': (255, 255, 255),
    'BLACK': (0, 0, 0),
    'GRAY': (128, 128, 128)
}

# Create necessary folders
import os
os.makedirs(EVIDENCE_FOLDER, exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("recordings", exist_ok=True)
