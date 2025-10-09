#!/usr/bin/env python3
"""
NDI Receiver using Native SDK + Pygame Display
Combines working NDI reception from test_ndi_headless.py
with working display init from led_test_pattern.py
"""

import ctypes
from ctypes import *
import pygame
import sys
import os
import time

# Display configuration
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 320
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)

# Try different video drivers automatically
def init_video_driver():
    video_drivers = ['kmsdrm', 'directfb', 'x11']
    for driver in video_drivers:
        try:
            os.environ['SDL_VIDEODRIVER'] = driver
            pygame.init()
            pygame.quit()
            print(f"Using video driver: {driver}")
            return driver
        except:
            continue
    print("Using default video driver: kmsdrm")
    os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'
    return 'kmsdrm'

# Load NDI library
try:
    ndi_lib = CDLL("/usr/local/lib/libndi.so.6")
except OSError as e:
    print(f"Failed to load NDI library: {e}")
    sys.exit(1)

# NDI Structures
class NDIlib_source_t(Structure):
    _fields_ = [("p_ndi_name", c_char_p), ("p_url_address", c_char_p)]

class NDIlib_video_frame_v2_t(Structure):
    _fields_ = [
        ("xres", c_int), ("yres", c_int), ("FourCC", c_int),
        ("frame_rate_N", c_int), ("frame_rate_D", c_int),
        ("picture_aspect_ratio", c_float), ("frame_format_type", c_int),
        ("timecode", c_longlong), ("p_data", POINTER(c_uint8)),
        ("line_stride_in_bytes", c_int), ("p_metadata", c_char_p),
        ("timestamp", c_longlong)
    ]

class NDIlib_recv_create_v3_t(Structure):
    _fields_ = [
        ("source_to_connect_to", NDIlib_source_t),
        ("color_format", c_int), ("bandwidth", c_int),
        ("allow_video_fields", c_bool), ("p_ndi_recv_name", c_char_p)
    ]

# Function definitions
ndi_lib.NDIlib_initialize.restype = c_bool
ndi_lib.NDIlib_find_create_v2.restype = c_void_p
ndi_lib.NDIlib_find_create_v2.argtypes = [c_void_p]
ndi_lib.NDIlib_find_get_current_sources.restype = POINTER(NDIlib_source_t)
ndi_lib.NDIlib_find_get_current_sources.argtypes = [c_void_p, POINTER(c_uint32)]
ndi_lib.NDIlib_recv_create_v3.restype = c_void_p
ndi_lib.NDIlib_recv_create_v3.argtypes = [POINTER(NDIlib_recv_create_v3_t)]
ndi_lib.NDIlib_recv_capture_v2.restype = c_int
ndi_lib.NDIlib_recv_capture_v2.argtypes = [c_void_p, POINTER(NDIlib_video_frame_v2_t), c_void_p, c_void_p, c_uint32]
ndi_lib.NDIlib_recv_free_video_v2.argtypes = [c_void_p, POINTER(NDIlib_video_frame_v2_t)]
ndi_lib.NDIlib_recv_destroy.argtypes = [c_void_p]
ndi_lib.NDIlib_find_destroy.argtypes = [c_void_p]

def uyvy_to_rgb_fast(uyvy_data, width, height, stride):
    """Convert UYVY to RGB - FAST version using numpy"""
    import numpy as np
    
    # Reshape UYVY data
    uyvy = np.frombuffer(uyvy_data, dtype=np.uint8)
    
    # Create output array
    rgb = np.empty((height, width, 3), dtype=np.uint8)
    
    for y in range(height):
        row_start = y * stride
        row_data = uyvy[row_start:row_start + width * 2]
        
        # Extract U, Y0, V, Y1 components
        u = row_data[0::4].astype(np.int32)
        y0 = row_data[1::4].astype(np.int32)
        v = row_data[2::4].astype(np.int32)
        y1 = row_data[3::4].astype(np.int32)
        
        # YUV to RGB conversion (BT.601)
        c0 = y0 - 16
        c1 = y1 - 16
        d = u - 128
        e = v - 128
        
        # Pixel 0 (even pixels)
        r0 = np.clip((298 * c0 + 409 * e + 128) >> 8, 0, 255).astype(np.uint8)
        g0 = np.clip((298 * c0 - 100 * d - 208 * e + 128) >> 8, 0, 255).astype(np.uint8)
        b0 = np.clip((298 * c0 + 516 * d + 128) >> 8, 0, 255).astype(np.uint8)
        
        # Pixel 1 (odd pixels)
        r1 = np.clip((298 * c1 + 409 * e + 128) >> 8, 0, 255).astype(np.uint8)
        g1 = np.clip((298 * c1 - 100 * d - 208 * e + 128) >> 8, 0, 255).astype(np.uint8)
        b1 = np.clip((298 * c1 + 516 * d + 128) >> 8, 0, 255).astype(np.uint8)
        
        # Interleave pixels
        rgb[y, 0::2, 0] = r0
        rgb[y, 0::2, 1] = g0
        rgb[y, 0::2, 2] = b0
        rgb[y, 1::2, 0] = r1
        rgb[y, 1::2, 1] = g1
        rgb[y, 1::2, 2] = b1
    
    return rgb.tobytes()

print("="*60)
print("NDI Native Receiver with Display")
print("="*60)

# Initialize video driver
init_video_driver()
pygame.init()

# Initialize display with fallback modes
display_modes = [
    (SCREEN_SIZE, pygame.FULLSCREEN),
    (SCREEN_SIZE, 0),  # Windowed mode
    ((640, 480), pygame.FULLSCREEN),
    ((640, 480), 0),
]

screen = None
for mode_size, mode_flags in display_modes:
    try:
        screen = pygame.display.set_mode(mode_size, mode_flags)
        print(f"Display initialized: {mode_size[0]}x{mode_size[1]}")
        break
    except pygame.error as e:
        print(f"Failed {mode_size}: {e}")
        continue

if not screen:
    print("Failed to initialize any display mode")
    sys.exit(1)

pygame.display.set_caption("NDI Receiver")
pygame.mouse.set_visible(False)
clock = pygame.time.Clock()

# Initialize NDI
print("\nInitializing NDI...")
if not ndi_lib.NDIlib_initialize():
    print("Failed to initialize NDI")
    pygame.quit()
    sys.exit(1)

ndi_find = ndi_lib.NDIlib_find_create_v2(None)
print("Searching for NDI sources...")
time.sleep(2)

num_sources = c_uint32(0)
sources = ndi_lib.NDIlib_find_get_current_sources(ndi_find, byref(num_sources))

print(f"\nFound {num_sources.value} NDI sources:")
target_source = None

for i in range(num_sources.value):
    source = sources[i]
    name = source.p_ndi_name.decode('utf-8') if source.p_ndi_name else ""
    print(f"  [{i}] {name}")
    if "catatumbo_led" in name.lower():
        target_source = source
        print(f"      ^ Selected!")

if not target_source and num_sources.value > 0:
    target_source = sources[0]
    print(f"  -> Using first source")

if not target_source:
    print("\n❌ No NDI sources found!")
    print("Make sure:")
    print("  1. NDI sender is running")
    print("  2. Both devices are on same network")
    print("  3. Firewall allows NDI (port 5960)")
    
    # Show waiting screen
    font = pygame.font.Font(None, 36)
    text = font.render("No NDI sources found", True, (255, 255, 255))
    screen.fill((0, 0, 0))
    screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2, 
                      screen.get_height() // 2 - text.get_height() // 2))
    pygame.display.flip()
    time.sleep(3)
    
    ndi_lib.NDIlib_find_destroy(ndi_find)
    ndi_lib.NDIlib_destroy()
    pygame.quit()
    sys.exit(1)

# Create receiver
print("\nConnecting to NDI source...")
recv_settings = NDIlib_recv_create_v3_t()
recv_settings.source_to_connect_to = target_source
recv_settings.color_format = 1  # UYVY
recv_settings.bandwidth = 100
recv_settings.allow_video_fields = False
recv_settings.p_ndi_recv_name = b"Native Display Receiver"

ndi_recv = ndi_lib.NDIlib_recv_create_v3(byref(recv_settings))

if not ndi_recv:
    print("Failed to create receiver")
    pygame.quit()
    sys.exit(1)

print("✓ Connected!")
print("\n" + "="*60)
print("Receiving video... Press Ctrl+C to stop")
print("="*60)

video_frame = NDIlib_video_frame_v2_t()
frame_count = 0
start_time = time.time()
last_fps_time = start_time
last_fps_count = 0
last_print_time = start_time

# Status font
font = pygame.font.Font(None, 24)

try:
    running = True
    while running:
        # Check for quit events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    running = False
        
        # Capture NDI frame
        frame_type = ndi_lib.NDIlib_recv_capture_v2(ndi_recv, byref(video_frame), None, None, 100)
        
        if frame_type == 1:  # Video frame
            frame_count += 1
            
            # Calculate FPS
            now = time.time()
            if now - last_fps_time >= 1.0:
                fps = (frame_count - last_fps_count) / (now - last_fps_time)
                
                # Print to console every second
                if now - last_print_time >= 1.0:
                    print(f"  Frame {frame_count} | {fps:.1f} fps")
                    last_print_time = now
                
                last_fps_time = now
                last_fps_count = frame_count
            
            # Convert frame
            width = video_frame.xres
            height = video_frame.yres
            stride = video_frame.line_stride_in_bytes
            
            uyvy_data = ctypes.string_at(video_frame.p_data, stride * height)
            rgb_data = uyvy_to_rgb_fast(uyvy_data, width, height, stride)
            
            # Create pygame surface
            ndi_surface = pygame.image.frombuffer(rgb_data, (width, height), 'RGB')
            
            # Scale to fit screen (use smoothscale for better quality, or no scale for max speed)
            screen_size = screen.get_size()
            scale = min(screen_size[0] / width, screen_size[1] / height)
            new_size = (int(width * scale), int(height * scale))
            
            # Use transform.scale (fast) instead of smoothscale for max FPS
            if scale > 1.5:
                scaled = pygame.transform.scale(ndi_surface, new_size)
            else:
                scaled = ndi_surface  # No scaling needed for similar sizes
                new_size = (width, height)
            
            # Center and draw
            x = (screen_size[0] - new_size[0]) // 2
            y = (screen_size[1] - new_size[1]) // 2
            
            screen.fill((0, 0, 0))
            screen.blit(scaled, (x, y))
            
            # Draw status overlay
            elapsed = now - start_time
            fps_display = (frame_count - last_fps_count) / (now - last_fps_time) if (now - last_fps_time) > 0 else 0
            status_text = f"Frame {frame_count} | {fps_display:.1f} fps | {width}x{height}"
            text_surface = font.render(status_text, True, (0, 255, 0))
            screen.blit(text_surface, (10, 10))
            
            pygame.display.flip()
            
            ndi_lib.NDIlib_recv_free_video_v2(ndi_recv, byref(video_frame))
        
        clock.tick(60)

except KeyboardInterrupt:
    print("\n\n⏹ Stopped by user")

# Cleanup
print("\nCleaning up...")
ndi_lib.NDIlib_recv_destroy(ndi_recv)
ndi_lib.NDIlib_find_destroy(ndi_find)
ndi_lib.NDIlib_destroy()
pygame.quit()

elapsed = time.time() - start_time
avg_fps = frame_count / elapsed if elapsed > 0 else 0

print("="*60)
print("Session complete!")
print(f"  Frames received: {frame_count}")
print(f"  Average FPS: {avg_fps:.1f}")
print(f"  Duration: {elapsed:.1f}s")
print("="*60)

