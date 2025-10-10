#!/usr/bin/env python3
"""
LED Screen Test Pattern Generator for Raspberry Pi
Creates a colorful test pattern for 800x800 LED screen connected via HDMI
"""

import pygame
import sys
import math
import time
import os
from typing import Tuple

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
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
GRAY = (128, 128, 128)

class LEDTestPattern:
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
        # Try different corners to find the right one
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
        
        pygame.display.set_caption("LED Test Pattern - 320x320 on 800x800")
        
        # Initialize font for text patterns
        try:
            self.font_large = pygame.font.Font(None, 48)
            self.font_medium = pygame.font.Font(None, 32)
            self.font_small = pygame.font.Font(None, 24)
        except:
            self.font_large = pygame.font.SysFont('Arial', 48)
            self.font_medium = pygame.font.SysFont('Arial', 32)
            self.font_small = pygame.font.SysFont('Arial', 24)
        
        # Hide the cursor for cleaner LED display
        pygame.mouse.set_visible(False)
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        print(f"LED screen positioned at ({self.led_x}, {self.led_y})")
        print("Press 'P' to cycle through LED screen positions")
        
    def draw_color_bars(self):
        """Draw horizontal color bars"""
        bar_height = SCREEN_HEIGHT // 8
        colors = [RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA, WHITE, BLACK]
        
        for i, color in enumerate(colors):
            y_start = i * bar_height
            pygame.draw.rect(self.led_surface, color, (0, y_start, SCREEN_WIDTH, bar_height))
    
    def draw_grid_pattern(self):
        """Draw a grid pattern"""
        grid_size = 20  # 16x16 grid for 320x320
        for x in range(0, SCREEN_WIDTH, grid_size):
            pygame.draw.line(self.led_surface, WHITE, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, grid_size):
            pygame.draw.line(self.led_surface, WHITE, (0, y), (SCREEN_WIDTH, y), 1)
    
    def draw_gradient_circle(self):
        """Draw a radial gradient circle"""
        center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        max_radius = min(SCREEN_WIDTH, SCREEN_HEIGHT) // 2
        
        for radius in range(max_radius, 0, -2):
            # Create gradient from red to blue
            intensity = int(255 * (1 - radius / max_radius))
            color = (intensity, 0, 255 - intensity)
            pygame.draw.circle(self.led_surface, color, (center_x, center_y), radius)
    
    def draw_checkerboard(self):
        """Draw a checkerboard pattern"""
        square_size = 20  # Smaller squares for 320x320
        for x in range(0, SCREEN_WIDTH, square_size):
            for y in range(0, SCREEN_HEIGHT, square_size):
                if (x // square_size + y // square_size) % 2 == 0:
                    pygame.draw.rect(self.led_surface, WHITE, (x, y, square_size, square_size))
                else:
                    pygame.draw.rect(self.led_surface, BLACK, (x, y, square_size, square_size))
    
    def draw_concentric_circles(self):
        """Draw concentric circles"""
        center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        colors = [RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA]
        
        for i in range(6):
            radius = (i + 1) * 25  # Smaller circles for 320x320
            color = colors[i % len(colors)]
            pygame.draw.circle(self.led_surface, color, (center_x, center_y), radius, 3)
    
    def draw_text_orientation(self):
        """Draw text patterns to show orientation"""
        # Clear background
        self.led_surface.fill(BLACK)
        
        # Top text
        top_text = self.font_large.render("TOP", True, WHITE)
        top_rect = top_text.get_rect(center=(SCREEN_WIDTH//2, 30))
        self.led_surface.blit(top_text, top_rect)
        
        # Bottom text
        bottom_text = self.font_large.render("BOTTOM", True, WHITE)
        bottom_rect = bottom_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT-30))
        self.led_surface.blit(bottom_text, bottom_rect)
        
        # Left text
        left_text = self.font_medium.render("LEFT", True, WHITE)
        left_text = pygame.transform.rotate(left_text, 90)
        left_rect = left_text.get_rect(center=(30, SCREEN_HEIGHT//2))
        self.led_surface.blit(left_text, left_rect)
        
        # Right text
        right_text = self.font_medium.render("RIGHT", True, WHITE)
        right_text = pygame.transform.rotate(right_text, 90)
        right_rect = right_text.get_rect(center=(SCREEN_WIDTH-30, SCREEN_HEIGHT//2))
        self.led_surface.blit(right_text, right_rect)
        
        # Center text with rotation info
        center_text = self.font_small.render(f"ROT: {self.rotation_angles[self.current_rotation]}°", True, YELLOW)
        center_rect = center_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.led_surface.blit(center_text, center_rect)
    
    def draw_arrow_pattern(self):
        """Draw arrows pointing in different directions"""
        self.led_surface.fill(BLACK)
        
        # Draw arrows pointing in cardinal directions
        arrow_size = 20
        
        # Up arrow (top)
        pygame.draw.polygon(self.led_surface, RED, [
            (SCREEN_WIDTH//2, 50),
            (SCREEN_WIDTH//2 - arrow_size, 50 + arrow_size),
            (SCREEN_WIDTH//2 + arrow_size, 50 + arrow_size)
        ])
        
        # Down arrow (bottom)
        pygame.draw.polygon(self.led_surface, GREEN, [
            (SCREEN_WIDTH//2, SCREEN_HEIGHT - 50),
            (SCREEN_WIDTH//2 - arrow_size, SCREEN_HEIGHT - 50 - arrow_size),
            (SCREEN_WIDTH//2 + arrow_size, SCREEN_HEIGHT - 50 - arrow_size)
        ])
        
        # Left arrow
        pygame.draw.polygon(self.led_surface, BLUE, [
            (50, SCREEN_HEIGHT//2),
            (50 + arrow_size, SCREEN_HEIGHT//2 - arrow_size),
            (50 + arrow_size, SCREEN_HEIGHT//2 + arrow_size)
        ])
        
        # Right arrow
        pygame.draw.polygon(self.led_surface, YELLOW, [
            (SCREEN_WIDTH - 50, SCREEN_HEIGHT//2),
            (SCREEN_WIDTH - 50 - arrow_size, SCREEN_HEIGHT//2 - arrow_size),
            (SCREEN_WIDTH - 50 - arrow_size, SCREEN_HEIGHT//2 + arrow_size)
        ])
        
        # Center text
        center_text = self.font_small.render("ARROWS", True, WHITE)
        center_rect = center_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.led_surface.blit(center_text, center_rect)
    
    def draw_test_pattern(self, pattern_type: str):
        """Draw the specified test pattern"""
        # Clear the LED surface
        self.led_surface.fill(BLACK)
        
        if pattern_type == "color_bars":
            self.draw_color_bars()
        elif pattern_type == "grid":
            self.draw_grid_pattern()
        elif pattern_type == "gradient":
            self.draw_gradient_circle()
        elif pattern_type == "checkerboard":
            self.draw_checkerboard()
        elif pattern_type == "circles":
            self.draw_concentric_circles()
        elif pattern_type == "text_orientation":
            self.draw_text_orientation()
        elif pattern_type == "arrows":
            self.draw_arrow_pattern()
        elif pattern_type == "all":
            # Draw multiple patterns in quadrants
            # Top-left: Color bars
            bar_height = SCREEN_HEIGHT // 4
            bar_width = SCREEN_WIDTH // 4
            colors = [RED, GREEN, BLUE, YELLOW]
            for i, color in enumerate(colors):
                y_start = i * (bar_height // 4)
                pygame.draw.rect(self.led_surface, color, (0, y_start, bar_width, bar_height // 4))
            
            # Top-right: Grid
            grid_size = 10
            for x in range(SCREEN_WIDTH // 4, SCREEN_WIDTH, grid_size):
                pygame.draw.line(self.led_surface, WHITE, (x, 0), (x, SCREEN_HEIGHT // 4), 1)
            for y in range(0, SCREEN_HEIGHT // 4, grid_size):
                pygame.draw.line(self.led_surface, WHITE, (SCREEN_WIDTH // 4, y), (SCREEN_WIDTH, y), 1)
            
            # Bottom-left: Checkerboard
            square_size = 12
            for x in range(0, SCREEN_WIDTH // 4, square_size):
                for y in range(SCREEN_HEIGHT // 4, SCREEN_HEIGHT // 2, square_size):
                    if (x // square_size + y // square_size) % 2 == 0:
                        pygame.draw.rect(self.led_surface, WHITE, (x, y, square_size, square_size))
                    else:
                        pygame.draw.rect(self.led_surface, BLACK, (x, y, square_size, square_size))
            
            # Bottom-right: Gradient circle
            center_x = SCREEN_WIDTH - SCREEN_WIDTH // 8
            center_y = SCREEN_HEIGHT - SCREEN_HEIGHT // 8
            max_radius = SCREEN_WIDTH // 8
            for radius in range(max_radius, 0, -2):
                intensity = int(255 * (1 - radius / max_radius))
                color = (intensity, 0, 255 - intensity)
                pygame.draw.circle(self.led_surface, color, (center_x, center_y), radius)
        
        # Clear the main screen
        self.screen.fill(BLACK)
        
        # Rotate the LED surface based on current rotation setting
        rotated_surface = pygame.transform.rotate(self.led_surface, self.rotation_angles[self.current_rotation])
        
        # Blit the LED content to the main screen at the LED position
        self.screen.blit(rotated_surface, (self.led_x, self.led_y))
    
    def run(self):
        """Main loop"""
        patterns = ["text_orientation", "arrows", "color_bars", "grid", "gradient", "checkerboard", "circles", "all"]
        pattern_index = 0
        last_pattern_change = time.time()
        pattern_duration = 5  # seconds per pattern
        
        print("LED Test Pattern Generator - 320x320 LED Screen")
        print("Controls:")
        print("  ESC - Exit")
        print("  SPACE - Cycle patterns")
        print("  P - Cycle LED screen positions")
        print("  R - Cycle rotation (0°, 90°, 180°, 270°)")
        print("Patterns: text_orientation, arrows, color_bars, grid, gradient, checkerboard, circles, all")
        print(f"Current pattern: {patterns[pattern_index]}")
        print(f"LED position: {self.led_positions[self.current_led_position]}")
        print(f"Current rotation: {self.rotation_angles[self.current_rotation]}°")
        
        while self.running:
            current_time = time.time()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_SPACE:
                        pattern_index = (pattern_index + 1) % len(patterns)
                        print(f"Switched to pattern: {patterns[pattern_index]}")
                    elif event.key == pygame.K_p:
                        self.current_led_position = (self.current_led_position + 1) % len(self.led_positions)
                        self.led_x, self.led_y = self.led_positions[self.current_led_position]
                        print(f"LED position: {self.led_positions[self.current_led_position]}")
                    elif event.key == pygame.K_r:
                        self.current_rotation = (self.current_rotation + 1) % len(self.rotation_angles)
                        print(f"Rotation: {self.rotation_angles[self.current_rotation]}°")
            
            # Auto-cycle patterns
            if current_time - last_pattern_change >= pattern_duration:
                pattern_index = (pattern_index + 1) % len(patterns)
                last_pattern_change = current_time
                print(f"Auto-switched to pattern: {patterns[pattern_index]}")
            
            # Draw current pattern
            self.draw_test_pattern(patterns[pattern_index])
            
            # Update display
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS
        
        pygame.quit()
        sys.exit()

def main():
    """Main function"""
    try:
        test_pattern = LEDTestPattern()
        test_pattern.run()
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
