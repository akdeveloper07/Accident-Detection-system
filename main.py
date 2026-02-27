# main.py
"""
Main application for Accident Detection System
"""

import cv2
import time
import argparse
import numpy as np
import sys

# Import all modules
from video_handler import VideoHandler
from detector import AccidentDetector
from visualizer import Visualizer
from alert_system import AlertSystem
import config

class AccidentDetectionApp:
    def __init__(self):
        # Initialize all components
        self.video = VideoHandler()
        self.detector = AccidentDetector()
        self.visualizer = Visualizer()
        self.alert_system = AlertSystem()
        
        # State
        self.running = True
        self.show_heatmap = config.DEFAULT_HEATMAP
        self.show_help = False
        self.last_frame = None
        
        print("\n" + "="*60)
        print("🚗 ACCIDENT DETECTION SYSTEM")
        print("="*60)

    def show_menu(self):
        """Show main menu"""
        print("\n📋 SELECT INPUT SOURCE:")
        print("   [1] Real-time Webcam")
        print("   [2] Upload Video File (Browse)")
        print("   [3] Enter Video File Path")
        print("   [4] Create Simulation Video")
        print("   [Q] Quit")
        
        choice = input("\nEnter choice: ").strip().lower()
        return choice

    def run_webcam(self):
        """Run with webcam"""
        camera_id = input("Enter camera ID (0 for default): ").strip()
        if not camera_id:
            camera_id = 0
        else:
            camera_id = int(camera_id)
        
        if self.video.start_webcam(camera_id):
            self._process_loop()

    def run_upload_gui(self):
        """Run with uploaded video (GUI)"""
        if self.video.upload_video_gui():
            self._process_loop()

    def run_upload_cli(self):
        """Run with video file path"""
        file_path = input("Enter video file path: ").strip()
        if self.video.upload_video_cli(file_path):
            self._process_loop()

    def run_simulation(self):
        """Create and run simulation"""
        print("\n🎬 Select Accident Type:")
        print("   [1] Minor Accident")
        print("   [2] Major Accident")
        print("   [3] Critical Accident")
        
        choice = input("Choice: ").strip()
        
        accident_type = {
            '1': 'minor',
            '2': 'major',
            '3': 'critical'
        }.get(choice, 'major')
        
        duration = input("Duration in seconds (default 10): ").strip()
        if not duration:
            duration = 10
        else:
            duration = int(duration)
        
        if self.video.create_simulation(accident_type, duration):
            self._process_loop()

    def _process_loop(self):
        """Main processing loop"""
        print("\n🚀 Starting detection...")
        print("Controls: [Q]uit [H]elp [1-3]Demo [Space]Pause\n")
        
        while self.running:
            # Read frame
            frame, ret = self.video.read_frame()
            if not ret:
                continue
            
            # Process frame
            accident_data = self.detector.process_frame(frame)
            
            # Get current FPS
            fps = self.video.current_fps
            
            # Visualize
            display = self.visualizer.create_dashboard(
                frame, accident_data, fps, self.show_heatmap
            )
            
            # Add progress bar for videos
            if self.video.source_type == 'video':
                progress = self.video.get_progress()
                self._draw_progress(display, progress)
            
            # Add source info
            self._draw_source_info(display)
            
            # Show recording indicator
            if self.video.is_recording:
                cv2.putText(display, "🔴 REC", (10, 100),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Show help screen if requested
            if self.show_help:
                display = self.visualizer.draw_help_screen(display)
            
            # Trigger alert if needed
            if accident_data['accident_detected'] and accident_data['should_alert']:
                self.alert_system.trigger_alert(frame, accident_data)
                
                # Save screenshot automatically
                self.video.save_screenshot(display)
            
            # Store last frame for screenshot
            self.last_frame = display
            
            # Display
            cv2.imshow("Accident Detection System", display)
            
            # Handle keys
            key = cv2.waitKey(1) & 0xFF
            self._handle_key(key)
    
    def _handle_key(self, key):
        """Handle keyboard input"""
        if key == ord('q'):
            self.running = False
        
        elif key == ord('h'):
            self.show_help = not self.show_help
        
        elif key == ord(' '):
            self.video.pause()
        
        elif key == ord('s'):
            if self.last_frame is not None:
                self.video.save_screenshot(self.last_frame)
        
        elif key == ord('r'):
            if not self.video.is_recording:
                self.video.start_recording()
            else:
                self.video.stop_recording()
        
        elif key == ord('h'):
            self.show_heatmap = not self.show_heatmap
            print(f"Heatmap: {'ON' if self.show_heatmap else 'OFF'}")
        
        # Demo accident simulation
        elif key == ord('1'):
            self.detector.force_accident("MINOR")
        elif key == ord('2'):
            self.detector.force_accident("MAJOR")
        elif key == ord('3'):
            self.detector.force_accident("CRITICAL")
        
        # Video controls
        elif key == 83:  # Right arrow
            self.video.seek(5)
        elif key == 81:  # Left arrow
            self.video.seek(-5)
        elif key == ord('r'):
            self.video.restart()

    def _draw_progress(self, frame, progress):
        """Draw video progress bar"""
        h, w = frame.shape[:2]
        
        # Progress bar
        bar_x = 10
        bar_y = h - 50
        bar_w = w - 20
        bar_h = 10
        
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), 
                     (50, 50, 50), -1)
        
        fill_w = int(bar_w * progress / 100)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h),
                     (0, 255, 0), -1)

    def _draw_source_info(self, frame):
        """Draw source information"""
        source_text = {
            'webcam': '📷 LIVE WEBCAM',
            'video': '🎬 VIDEO FILE'
        }.get(self.video.source_type, '')
        
        if source_text:
            cv2.putText(frame, source_text, (frame.shape[1] - 200, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.COLORS['WHITE'], 1)

    def run(self):
        """Main application entry point"""
        while True:
            choice = self.show_menu()
            
            if choice == '1':
                self.run_webcam()
            elif choice == '2':
                self.run_upload_gui()
            elif choice == '3':
                self.run_upload_cli()
            elif choice == '4':
                self.run_simulation()
            elif choice == 'q':
                break
            else:
                print("❌ Invalid choice")
            
            # Ask to continue
            cont = input("\n🔄 Process another video? (y/n): ").strip().lower()
            if cont != 'y':
                break
            
            # Reset for next run
            self.running = True
        
        # Cleanup
        self.video.release()
        cv2.destroyAllWindows()
        print("\n✅ System shutdown complete")

def main():
    app = AccidentDetectionApp()
    app.run()

if __name__ == "__main__":
    main()
