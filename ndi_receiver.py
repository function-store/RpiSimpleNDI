#!/usr/bin/env python3
"""
NDI Receiver for Raspberry Pi LED Screen
Receives 320x320 video from NDI sender "catatumbo_led" and displays on LED screen
"""

import pygame
import cv2
import numpy as np
import time
import os
import sys
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
        self.video_capture = None
        self.last_frame_time = 0
        self.frame_timeout = 5.0  # seconds
        
        print(f"LED screen positioned at ({self.led_x}, {self.led_y})")
        print("Press 'P' to cycle through LED screen positions")
        print("Press 'R' to cycle rotation angles")
        print(f"Looking for NDI sender: {self.ndi_sender_name}")
    
    def setup_ndi_capture(self):
        """Setup NDI video capture"""
        try:
            # Try to find the NDI sender
            print("Searching for NDI sources...")
            
            # For now, we'll use a placeholder approach
            # In a real implementation, you'd use the NDI SDK
            print(f"Looking for sender: {self.ndi_sender_name}")
            
            # Create a test pattern for now
            self.create_test_pattern()
            return True
            
        except Exception as e:
            print(f"Failed to setup NDI capture: {e}")
            return False
    
    def create_test_pattern(self):
        """Create a test pattern while waiting for NDI"""
        # Create a test pattern with sender name
        self.led_surface.fill(BLACK)
        
        # Draw a border
        pygame.draw.rect(self.led_surface, WHITE, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 2)
        
        # Draw text
        font = pygame.font.Font(None, 24)
        text1 = font.render("NDI Receiver", True, WHITE)
        text2 = font.render("Waiting for:", True, WHITE)
        text3 = font.render(self.ndi_sender_name, True, RED)
        
        # Center the text
        text1_rect = text1.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40))
        text2_rect = text2.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 10))
        text3_rect = text3.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
        
        self.led_surface.blit(text1, text1_rect)
        self.led_surface.blit(text2, text2_rect)
        self.led_surface.blit(text3, text3_rect)
        
        # Draw a pulsing circle
        pulse_size = int(20 + 10 * np.sin(time.time() * 3))
        pygame.draw.circle(self.led_surface, GREEN, (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 60), pulse_size, 2)
    
    def process_frame(self, frame):
        """Process incoming video frame"""
        if frame is None:
            return
        
        # Resize frame to 320x320 if needed
        if frame.shape[:2] != (SCREEN_HEIGHT, SCREEN_WIDTH):
            frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
        
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
        
        # Rotate the LED surface based on current rotation setting
        rotated_surface = pygame.transform.rotate(self.led_surface, self.rotation_angles[self.current_rotation])
        
        # Blit the LED content to the main screen at the LED position
        self.screen.blit(rotated_surface, (self.led_x, self.led_y))
    
    def run(self):
        """Main loop"""
        print("NDI LED Receiver Started")
        print("Controls:")
        print("  ESC - Exit")
        print("  P - Cycle LED screen positions")
        print("  R - Cycle rotation (0°, 90°, 180°, 270°)")
        
        # Setup NDI capture
        if not self.setup_ndi_capture():
            print("Failed to setup NDI capture, running with test pattern")
        
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
            
            # Update test pattern if no NDI source
            if self.video_capture is None:
                self.create_test_pattern()
            
            # Draw current frame
            self.draw_frame()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS
        
        # Cleanup
        if self.video_capture is not None:
            self.video_capture.release()
        pygame.quit()
        sys.exit()

def main():
    """Main function"""
    try:
        receiver = NDILEDReceiver()
        receiver.run()
    except KeyboardInterrupt:
        print("\nExiting...")
        pygame.quit()
        sys.exit()
    except Exception as e:
        print(f"Error: {e}")
        pygame.quit()
        sys.exit(1)

if __name__ == "__main__":
    main()
