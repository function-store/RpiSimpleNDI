#!/usr/bin/env python3
"""
Simple test script to verify NDI receiver display functionality
"""

import pygame
import numpy as np
import time
import os
import sys

# Set environment variables for headless setup
os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'

# Initialize pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 320
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 800

# Create display
screen = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.FULLSCREEN)
led_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.mouse.set_visible(False)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

clock = pygame.time.Clock()
running = True

print("NDI Receiver Display Test")
print("This will show a test pattern on the LED screen")
print("Press ESC to exit")

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
    
    # Clear LED surface
    led_surface.fill(BLACK)
    
    # Draw test pattern
    current_time = time.time()
    
    # Animated circle
    center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    radius = int(50 + 30 * np.sin(current_time * 2))
    pygame.draw.circle(led_surface, GREEN, (center_x, center_y), radius, 3)
    
    # Text
    font = pygame.font.Font(None, 24)
    text = font.render("NDI Receiver Test", True, WHITE)
    text_rect = text.get_rect(center=(SCREEN_WIDTH//2, 50))
    led_surface.blit(text, text_rect)
    
    # Status
    status_text = font.render("Ready for NDI", True, BLUE)
    status_rect = status_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
    led_surface.blit(status_text, status_rect)
    
    # Rotate and display
    rotated_surface = pygame.transform.rotate(led_surface, 180)  # Upside down
    screen.fill(BLACK)
    screen.blit(rotated_surface, (0, 0))  # Top-left position
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
print("Test completed")
