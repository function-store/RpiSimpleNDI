#!/usr/bin/env python3
"""
NDI Receiver for Raspberry Pi LED Screen using FFmpeg
Receives 320x320 video from NDI sender "catatumbo_led" and displays on LED screen
"""

import pygame
import cv2
import numpy as np
import time
import os
import sys
import subprocess
import threading
from typing import Tuple, Optional

# Set environment variables for headless setup
# Try different video drivers in order of preference
video_drivers = ['kmsdrm', 'directfb', 'x11']
for driver in video_drivers:
    try:
        os.environ['SDL_VIDEODRIVER'] = driver
        # Test if this driver works
        pygame.init()
        pygame.quit()
        print(f"Using video driver: {driver}")
        break
    except:
        continue
else:
    # Fallback to default
    os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'
    print("Using default video driver: kmsdrm")

# Initialize pygame with error handling
try:
    pygame.init()
    print("Pygame initialized successfully")
except pygame.error as e:
    print(f"Pygame initialization failed: {e}")
    print("Try the troubleshooting steps in README.md")
    sys.exit(1)

# Screen dimensions - actual LED screen is 320x320
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 320
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)

# Display settings
DISPLAY_WIDTH = 800  # What the system reports
DISPLAY_HEIGHT = 800
DISPLAY_SIZE = (DISPLAY_WIDTH, DISPLAY_HEIGHT)

# Colors (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

class NDILEDReceiver:
    def __init__(self):
        # Initialize display at full resolution (800x800)
        try:
            self.screen = pygame.display.set_mode(DISPLAY_SIZE, pygame.FULLSCREEN)
            print(f"Display initialized at {DISPLAY_SIZE}")
        except pygame.error as e:
            print(f"Failed to initialize display: {e}")
            sys.exit(1)
        
        # Create a surface for the LED screen content (320x320)
        self.led_surface = pygame.Surface(SCREEN_SIZE)
        
        # LED screen position on the larger display
        self.led_positions = [
            (0, 0),  # Top-left
            (DISPLAY_WIDTH - SCREEN_WIDTH, 0),  # Top-right
            (0, DISPLAY_HEIGHT - SCREEN_HEIGHT),  # Bottom-left
            (DISPLAY_WIDTH - SCREEN_WIDTH, DISPLAY_HEIGHT - SCREEN_HEIGHT),  # Bottom-right
            ((DISPLAY_WIDTH - SCREEN_WIDTH) // 2, (DISPLAY_HEIGHT - SCREEN_HEIGHT) // 2),  # Center
        ]
        self.current_led_position = 0
        self.led_x, self.led_y = self.led_positions[self.current_led_position]
        
        # Rotation settings
        self.rotation_angles = [0, 90, 180, 270]
        self.current_rotation = 2  # Start with 180 degrees (upside down)
        
        pygame.display.set_caption("NDI LED Receiver - 320x320")
        
        # Hide the cursor for cleaner LED display
        pygame.mouse.set_visible(False)
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # NDI settings
        self.ndi_sender_name = "catatumbo_led"
        self.ffmpeg_process = None
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.last_frame_time = 0
        self.frame_timeout = 5.0  # seconds
        self.connection_status = "disconnected"
        
        print(f"LED screen positioned at ({self.led_x}, {self.led_y})")
        print("Press 'P' to cycle through LED screen positions")
        print("Press 'R' to cycle rotation angles")
        print(f"Looking for NDI sender: {self.ndi_sender_name}")
    
    def check_ndi_sources(self):
        """Check for available NDI sources using FFmpeg"""
        try:
            # Use FFmpeg to list NDI sources
            cmd = [
                'ffmpeg', '-f', 'libndi_newtek', '-list_sources', 'true', '-i', 'dummy', '-f', 'null', '-'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if self.ndi_sender_name in result.stderr:
                print(f"Found NDI source: {self.ndi_sender_name}")
                return True
            else:
                print(f"NDI source '{self.ndi_sender_name}' not found")
                print("Available sources:")
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("Timeout checking NDI sources")
            return False
        except Exception as e:
            print(f"Error checking NDI sources: {e}")
            return False
    
    def start_ffmpeg_capture(self):
        """Start FFmpeg process to capture NDI stream"""
        try:
            # FFmpeg command to receive NDI stream
            cmd = [
                'ffmpeg',
                '-f', 'libndi_newtek',
                '-i', self.ndi_sender_name,
                '-vf', f'scale={SCREEN_WIDTH}:{SCREEN_HEIGHT}',
                '-f', 'rawvideo',
                '-pix_fmt', 'bgr24',
                '-'
            ]
            
            print(f"Starting FFmpeg with command: {' '.join(cmd)}")
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            
            # Start frame reading thread
            self.frame_thread = threading.Thread(target=self.read_frames)
            self.frame_thread.daemon = True
            self.frame_thread.start()
            
            self.connection_status = "connecting"
            print("FFmpeg process started, waiting for frames...")
            return True
            
        except Exception as e:
            print(f"Failed to start FFmpeg: {e}")
            self.connection_status = "error"
            return False
    
    def read_frames(self):
        """Read frames from FFmpeg process"""
        frame_size = SCREEN_WIDTH * SCREEN_HEIGHT * 3  # BGR24
        
        while self.running and self.ffmpeg_process and self.ffmpeg_process.poll() is None:
            try:
                # Read raw frame data
                raw_frame = self.ffmpeg_process.stdout.read(frame_size)
                
                if len(raw_frame) == frame_size:
                    # Convert to numpy array
                    frame = np.frombuffer(raw_frame, dtype=np.uint8)
                    frame = frame.reshape((SCREEN_HEIGHT, SCREEN_WIDTH, 3))
                    
                    # Update current frame
                    with self.frame_lock:
                        self.current_frame = frame.copy()
                        self.last_frame_time = time.time()
                        self.connection_status = "connected"
                else:
                    print("Incomplete frame received")
                    
            except Exception as e:
                print(f"Error reading frame: {e}")
                break
        
        print("Frame reading thread ended")
        self.connection_status = "disconnected"
    
    def create_status_pattern(self):
        """Create status pattern showing connection state"""
        # Clear background
        self.led_surface.fill(BLACK)
        
        # Draw border
        border_color = GREEN if self.connection_status == "connected" else RED
        pygame.draw.rect(self.led_surface, border_color, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 3)
        
        # Status text
        font_large = pygame.font.Font(None, 32)
        font_medium = pygame.font.Font(None, 24)
        font_small = pygame.font.Font(None, 18)
        
        # Main title
        title_text = font_large.render("NDI Receiver", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 40))
        self.led_surface.blit(title_text, title_rect)
        
        # Status
        status_text = font_medium.render(f"Status: {self.connection_status.upper()}", True, border_color)
        status_rect = status_text.get_rect(center=(SCREEN_WIDTH//2, 80))
        self.led_surface.blit(status_text, status_rect)
        
        # Sender name
        sender_text = font_medium.render(f"Sender: {self.ndi_sender_name}", True, WHITE)
        sender_rect = sender_text.get_rect(center=(SCREEN_WIDTH//2, 110))
        self.led_surface.blit(sender_text, sender_rect)
        
        # Resolution
        res_text = font_small.render(f"Resolution: {SCREEN_WIDTH}x{SCREEN_HEIGHT}", True, WHITE)
        res_rect = res_text.get_rect(center=(SCREEN_WIDTH//2, 140))
        self.led_surface.blit(res_text, res_rect)
        
        # Connection indicator
        if self.connection_status == "connected":
            # Draw pulsing circle
            pulse_size = int(15 + 5 * np.sin(time.time() * 4))
            pygame.draw.circle(self.led_surface, GREEN, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40), pulse_size)
            
            # Frame info
            frame_time_text = font_small.render(f"Last frame: {time.time() - self.last_frame_time:.1f}s ago", True, GREEN)
            frame_time_rect = frame_time_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 40))
            self.led_surface.blit(frame_time_text, frame_time_rect)
        else:
            # Draw waiting animation
            wait_size = int(20 + 10 * np.sin(time.time() * 2))
            pygame.draw.circle(self.led_surface, YELLOW, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40), wait_size, 2)
            
            # Instructions
            if self.connection_status == "disconnected":
                inst_text = font_small.render("Waiting for NDI source...", True, YELLOW)
            else:
                inst_text = font_small.render("Connection error", True, RED)
            inst_rect = inst_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 40))
            self.led_surface.blit(inst_text, inst_rect)
        
        # Controls info
        controls_text = font_small.render("ESC:Exit P:Position R:Rotate", True, WHITE)
        controls_rect = controls_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 20))
        self.led_surface.blit(controls_text, controls_rect)
    
    def process_frame(self, frame):
        """Process incoming video frame"""
        if frame is None:
            return
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to pygame surface
        frame_surface = pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))
        
        # Update LED surface
        self.led_surface.blit(frame_surface, (0, 0))
    
    def draw_frame(self):
        """Draw the current frame to the display"""
        # Clear the main screen
        self.screen.fill(BLACK)
        
        # Get current frame if available
        with self.frame_lock:
            if self.current_frame is not None and self.connection_status == "connected":
                self.process_frame(self.current_frame)
            else:
                self.create_status_pattern()
        
        # Rotate the LED surface based on current rotation setting
        rotated_surface = pygame.transform.rotate(self.led_surface, self.rotation_angles[self.current_rotation])
        
        # Blit the LED content to the main screen at the LED position
        self.screen.blit(rotated_surface, (self.led_x, self.led_y))
    
    def cleanup(self):
        """Cleanup resources"""
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            try:
                self.ffmpeg_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ffmpeg_process.kill()
        pygame.quit()
    
    def run(self):
        """Main loop"""
        print("NDI LED Receiver Started")
        print("Controls:")
        print("  ESC - Exit")
        print("  P - Cycle LED screen positions")
        print("  R - Cycle rotation (0°, 90°, 180°, 270°)")
        
        # Check for NDI sources
        if self.check_ndi_sources():
            # Start FFmpeg capture
            if self.start_ffmpeg_capture():
                print("NDI capture started successfully")
            else:
                print("Failed to start NDI capture, showing status")
        else:
            print("NDI source not found, showing status")
        
        try:
            while self.running:
                current_time = time.time()
                
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                        elif event.key == pygame.K_p:
                            self.current_led_position = (self.current_led_position + 1) % len(self.led_positions)
                            self.led_x, self.led_y = self.led_positions[self.current_led_position]
                            print(f"LED position: {self.led_positions[self.current_led_position]}")
                        elif event.key == pygame.K_r:
                            self.current_rotation = (self.current_rotation + 1) % len(self.rotation_angles)
                            print(f"Rotation: {self.rotation_angles[self.current_rotation]}°")
                
                # Check for frame timeout
                if (self.connection_status == "connected" and 
                    current_time - self.last_frame_time > self.frame_timeout):
                    print("Frame timeout, switching to disconnected")
                    self.connection_status = "disconnected"
                
                # Draw current frame
                self.draw_frame()
                
                # Update display
                pygame.display.flip()
                self.clock.tick(60)  # 60 FPS
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            self.cleanup()

def main():
    """Main function"""
    try:
        receiver = NDILEDReceiver()
        receiver.run()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
