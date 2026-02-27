# video_handler.py
"""
Handle video capture from webcam or uploaded files
"""

import cv2
import os
import time
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import shutil
import numpy as np
import config

class VideoHandler:
    def __init__(self):
        self.cap = None
        self.source_type = None  # 'webcam', 'video', 'upload'
        self.current_fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        self.is_playing = False
        self.is_paused = False
        self.video_path = None
        self.total_frames = 0
        self.video_fps = 30
        
        # Recording
        self.is_recording = False
        self.recorder = None
        
        print("✅ Video Handler initialized")

    # ===== OPTION 1: WEBCAM =====
    def start_webcam(self, camera_id=0):
        """Start real-time webcam capture"""
        print(f"\n📷 Starting webcam {camera_id}...")
        
        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            print("❌ Failed to open webcam")
            return False
        
        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
        
        self.source_type = 'webcam'
        self.is_playing = True
        
        print(f"✅ Webcam running")
        return True

    # ===== OPTION 2: UPLOAD VIDEO =====
    def upload_video_gui(self):
        """Open file dialog to upload video"""
        print("\n📂 Opening file browser...")
        
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        file_path = filedialog.askopenfilename(
            title="Select Video for Accident Detection",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv"),
                ("All files", "*.*")
            ]
        )
        
        root.destroy()
        
        if file_path:
            return self.load_video(file_path)
        else:
            print("❌ No file selected")
            return False

    def upload_video_cli(self, file_path=None):
        """Upload video using command line"""
        if file_path is None:
            file_path = input("Enter video file path: ").strip()
        
        return self.load_video(file_path)

    def load_video(self, file_path):
        """Load video file"""
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        # Copy to uploads folder
        filename = os.path.basename(file_path)
        dest_path = os.path.join("uploads", f"upload_{int(time.time())}_{filename}")
        shutil.copy2(file_path, dest_path)
        
        # Open video
        self.cap = cv2.VideoCapture(dest_path)
        if not self.cap.isOpened():
            print("❌ Failed to open video file")
            return False
        
        # Get video info
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = self.total_frames / self.video_fps if self.video_fps > 0 else 0
        
        self.source_type = 'video'
        self.is_playing = True
        self.video_path = dest_path
        
        print(f"\n✅ Video loaded:")
        print(f"   Resolution: {width}x{height}")
        print(f"   FPS: {self.video_fps:.1f}")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Frames: {self.total_frames}")
        
        return True

    # ===== OPTION 3: CREATE SIMULATION =====
    def create_simulation(self, accident_type="major", duration=10):
        """Create simulated accident video"""
        print(f"\n🎬 Creating {accident_type} accident simulation...")
        
        output_path = f"uploads/simulated_{accident_type}_{int(time.time())}.mp4"
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, 30.0, (1280, 720))
        
        # Generate frames
        for i in range(duration * 30):
            frame = self._generate_accident_frame(i, accident_type)
            out.write(frame)
            
            if i % 30 == 0:
                print(f"   Generating: {i//30}/{duration}s", end='\r')
        
        out.release()
        print(f"\n✅ Simulation created: {output_path}")
        
        return self.load_video(output_path)

    def _generate_accident_frame(self, frame_num, accident_type):
        """Generate a single simulation frame"""
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        frame[:,:] = (100, 100, 100)  # Gray road
        
        # Add road
        cv2.line(frame, (0, 400), (1280, 400), (255, 255, 255), 2)
        
        # Add cars based on frame number
        if frame_num > 30:  # After 1 second
            if accident_type == "minor":
                cv2.rectangle(frame, (500, 350), (600, 400), (0, 0, 255), -1)
                cv2.rectangle(frame, (580, 340), (680, 390), (255, 0, 0), -1)
            elif accident_type == "major":
                cv2.rectangle(frame, (480, 340), (600, 400), (0, 0, 255), -1)
                cv2.rectangle(frame, (560, 330), (680, 390), (255, 0, 0), -1)
                cv2.rectangle(frame, (620, 350), (720, 410), (0, 255, 0), -1)
            else:  # critical
                cv2.rectangle(frame, (450, 320), (600, 400), (0, 0, 255), -1)
                cv2.rectangle(frame, (550, 310), (700, 390), (255, 0, 0), -1)
                cv2.rectangle(frame, (650, 340), (750, 420), (0, 255, 0), -1)
                # Add debris
                for _ in range(20):
                    x = np.random.randint(500, 750)
                    y = np.random.randint(320, 420)
                    cv2.circle(frame, (x, y), 3, (255, 255, 0), -1)
        
        return frame

    # ===== VIDEO PLAYBACK =====
    def read_frame(self):
        """Read next frame"""
        if not self.is_playing or self.is_paused or self.cap is None:
            return None, False
        
        ret, frame = self.cap.read()
        
        if ret:
            self.frame_count += 1
            
            # Calculate FPS
            elapsed = time.time() - self.start_time
            if elapsed >= 1.0:
                self.current_fps = self.frame_count / elapsed
                self.frame_count = 0
                self.start_time = time.time()
            
            # Auto-restart for videos
            if not ret and self.source_type == 'video':
                self.restart()
                ret, frame = self.cap.read()
        
        return frame, ret

    def pause(self):
        """Pause/resume playback"""
        self.is_paused = not self.is_paused
        status = "PAUSED" if self.is_paused else "PLAYING"
        print(f"⏯️ {status}")

    def restart(self):
        """Restart video"""
        if self.source_type == 'video' and self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            print("🔄 Video restarted")

    def seek(self, seconds):
        """Seek forward/backward"""
        if self.source_type == 'video' and self.cap:
            current = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            target = current + (seconds * self.video_fps)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, target))
            print(f"⏩ Seek {seconds:+d}s")

    def get_progress(self):
        """Get playback progress"""
        if self.source_type == 'video' and self.total_frames > 0:
            current = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            return (current / self.total_frames) * 100
        return 0

    # ===== RECORDING =====
    def start_recording(self):
        """Start recording"""
        if self.cap is None:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recordings/recording_{timestamp}.avi"
        
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.recorder = cv2.VideoWriter(filename, fourcc, 20.0, (width, height))
        self.is_recording = True
        print(f"🎥 Recording: {filename}")

    def stop_recording(self):
        """Stop recording"""
        if self.recorder:
            self.recorder.release()
            self.is_recording = False
            print("💾 Recording saved")

    def write_frame(self, frame):
        """Write frame to recording"""
        if self.is_recording and self.recorder:
            self.recorder.write(frame)

    # ===== SCREENSHOT =====
    def save_screenshot(self, frame):
        """Save screenshot"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        print(f"📸 Screenshot: {filename}")
        return filename

    # ===== CLEANUP =====
    def release(self):
        """Release resources"""
        if self.is_recording:
            self.stop_recording()
        
        if self.cap:
            self.cap.release()
        
        print("✅ Video handler released")
