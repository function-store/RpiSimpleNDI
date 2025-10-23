"""
Display Handler - Manages pygame display and rendering
"""

import pygame
import os
import logging
import time
from typing import Tuple, Optional

logger = logging.getLogger('ndi_receiver.display')


class DisplayHandler:
    """Handles display initialization and frame rendering with auto-reconnection"""
    
    POSITIONS = {
        'center': lambda w, h, sw, sh: ((sw - w) // 2, (sh - h) // 2),
        'top-left': lambda w, h, sw, sh: (0, 0),
        'top-right': lambda w, h, sw, sh: (sw - w, 0),
        'bottom-left': lambda w, h, sw, sh: (0, sh - h),
        'bottom-right': lambda w, h, sw, sh: (sw - w, sh - h),
    }
    
    def __init__(
        self,
        display_resolution: Optional[Tuple[int, int]] = None,
        content_resolution: Optional[Tuple[int, int]] = None,
        content_position: Optional[Tuple[int, int]] = None,
        fullscreen: bool = False,
        rotation: int = 0,
        scaling: str = 'fit',
        show_fps: bool = False,
        video_driver: str = 'auto',
        brightness: float = 1.0,
        # Legacy parameters for backwards compatibility
        resolution: Optional[Tuple[int, int]] = None,
        position: Optional[str] = None,
        # Reconnection settings
        retry_interval: int = 5,
        max_retries: int = -1  # -1 = infinite retries
    ):
        """
        Initialize display handler
        
        Args:
            display_resolution: Physical display resolution (None = auto-detect)
            content_resolution: Content/NDI stream resolution (None = adaptive)
            content_position: Content position in pixels (x,y) or None for auto
            fullscreen: Run in fullscreen mode
            rotation: Content rotation (0, 90, 180, 270)
            scaling: Scaling mode ('fit', 'fill', 'none', 'stretch')
            show_fps: Show FPS counter
            video_driver: SDL video driver to use
            brightness: Display brightness (0.0 to 1.0, default: 1.0)
            retry_interval: Seconds between reconnection attempts
            max_retries: Maximum reconnection attempts (-1 = infinite)
        """
        # Handle legacy parameters
        if resolution and not display_resolution:
            display_resolution = resolution
        
        # Store all parameters for reconnection
        self.display_resolution = display_resolution
        self.content_resolution = content_resolution
        self.content_position = content_position
        self.content_position_name = position  # For legacy string positions
        self.fullscreen = fullscreen
        self.rotation = rotation
        self.scaling = scaling
        self.show_fps = show_fps
        self.video_driver = video_driver
        # Load persistent brightness setting if available
        try:
            persistent_brightness = self._load_persistent_brightness()
            if persistent_brightness is not None:
                self.brightness = persistent_brightness
                logger.info(f"Loaded persistent brightness: {self.brightness:.2f}")
            else:
                self.brightness = max(0.0, min(1.0, brightness))  # Clamp brightness
        except Exception as e:
            logger.warning(f"Error loading persistent brightness: {e}")
            self.brightness = max(0.0, min(1.0, brightness))  # Clamp brightness
        self.retry_interval = retry_interval
        self.max_retries = max_retries
        
        # Display state tracking
        self.screen = None
        self.screen_size = None
        self.display_available = False
        self.last_retry_time = 0
        self.retry_count = 0
        
        # Initialize video driver
        if video_driver != 'auto':
            os.environ['SDL_VIDEODRIVER'] = video_driver
            logger.info(f"Using video driver: {video_driver}")
        else:
            self._detect_video_driver()
        
        # FPS tracking - initialize before display
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
        self.source_fps = 0.0
        
        # Font for FPS display - initialize to None before display init
        self.font = None
        
        # Pre-calculate fixed position if possible (optimization)
        self._fixed_position = None
        if content_position is not None:
            self._fixed_position = content_position
        
        # Cache whether we need transformations
        self._needs_rotation = rotation != 0
        # Only mark as needing scaling if we force a specific size or use stretch
        # 'fit' will be checked dynamically (only scale if needed)
        self._needs_scaling = (content_resolution is not None and scaling != 'none') or (scaling in ['fill', 'stretch'])
        self._dynamic_fit = (scaling == 'fit')
        
        # Try to initialize display
        self._initialize_display()
        
        # Initialize font after display (if display available)
        if show_fps and self.display_available:
            try:
                self.font = pygame.font.Font(None, 36)
            except:
                pass
        
        logger.info(f"Configuration: display={self.screen_size}, content_res={content_resolution}, position={content_position}, rotation={rotation}°, scaling={scaling}")
        
        if self.display_available:
            logger.info(f"Display initialized (rotation: {rotation}°, scaling: {scaling}, optimized: {not self._needs_rotation and not self._needs_scaling})")
        else:
            logger.warning(f"Display not available - will retry every {retry_interval}s")
    
    def _initialize_display(self) -> bool:
        """
        Initialize or reinitialize the display
        Returns True if successful, False otherwise
        """
        try:
            # Initialize pygame if not already done
            if not pygame.get_init():
                pygame.init()
            
            # Create display
            flags = pygame.FULLSCREEN if self.fullscreen else 0
            
            if self.display_resolution:
                self.screen = pygame.display.set_mode(self.display_resolution, flags)
                logger.info(f"Display created: {self.display_resolution[0]}x{self.display_resolution[1]}")
            else:
                # Auto-detect display size
                self.screen = pygame.display.set_mode((0, 0), flags)
                detected_size = self.screen.get_size()
                logger.info(f"Display auto-detected: {detected_size[0]}x{detected_size[1]}")
            
            pygame.display.set_caption("LED Receiver")
            pygame.mouse.set_visible(False)
            
            self.clock = pygame.time.Clock()
            self.screen_size = self.screen.get_size()
            self.display_available = True
            self.retry_count = 0
            
            # Reinitialize font if needed
            if self.show_fps and not self.font:
                try:
                    self.font = pygame.font.Font(None, 36)
                except:
                    pass
            
            return True
            
        except pygame.error as e:
            self.display_available = False
            self.screen = None
            self.screen_size = None
            
            # Only log full error on first failure or every 10th retry
            if self.retry_count == 0 or self.retry_count % 10 == 0:
                logger.warning(f"Display not available (attempt {self.retry_count + 1}): {e}")
            
            return False
    
    def _try_reconnect_display(self):
        """Try to reconnect to display if enough time has passed"""
        now = time.time()
        
        # Check if it's time to retry
        if now - self.last_retry_time < self.retry_interval:
            return
        
        # Check retry limit
        if self.max_retries > 0 and self.retry_count >= self.max_retries:
            return
        
        self.last_retry_time = now
        self.retry_count += 1
        
        logger.debug(f"Attempting display reconnection (attempt {self.retry_count})...")
        
        if self._initialize_display():
            logger.info(f"✓ Display reconnected successfully after {self.retry_count} attempts")
        
    def is_display_available(self) -> bool:
        """Check if display is currently available"""
        return self.display_available
    
    def _detect_video_driver(self):
        """Auto-detect best video driver"""
        drivers = ['kmsdrm', 'directfb', 'x11']
        
        for driver in drivers:
            try:
                os.environ['SDL_VIDEODRIVER'] = driver
                pygame.init()
                pygame.quit()
                logger.info(f"Auto-detected video driver: {driver}")
                return
            except:
                continue
        
        # Fallback
        os.environ['SDL_VIDEODRIVER'] = 'kmsdrm'
        logger.warning("Using fallback video driver: kmsdrm")
    
    def update(self, frame_data: Tuple[bytes, Tuple[int, int], float]):
        """
        Update display with new frame
        
        Args:
            frame_data: Tuple of (raw_data, resolution, source_fps)
        """
        raw_data, (width, height), source_fps = frame_data
        
        self.source_fps = source_fps
        
        # If display is not available, try to reconnect
        if not self.display_available:
            self._try_reconnect_display()
            # If still not available, skip rendering but still process FPS
            if not self.display_available:
                self._update_fps_counter()
                return
        
        # Wrap display operations in try/except to catch disconnection
        try:
            self._render_frame(raw_data, width, height)
        except pygame.error as e:
            logger.warning(f"Display error (disconnected?): {e}")
            self.display_available = False
            self.last_retry_time = time.time()
            return
    
    def _render_frame(self, raw_data: bytes, width: int, height: int):
        """
        Internal method to render a frame to the display
        
        Args:
            raw_data: Frame pixel data
            width: Frame width
            height: Frame height
        """
        # Calculate expected buffer size for RGBA (4 bytes per pixel)
        expected_size = width * height * 4
        actual_size = len(raw_data)
        
        if actual_size != expected_size:
            logger.warning(f"Buffer size mismatch: expected {expected_size}, got {actual_size} for {width}x{height}")
            # Try to handle stride/padding
            # If buffer is larger, it might have stride padding
            if actual_size > expected_size:
                # Extract only the needed data (simple approach)
                import numpy as np
                data_array = np.frombuffer(raw_data, dtype=np.uint8)
                # Reshape considering stride
                stride = actual_size // height
                if stride >= width * 4:
                    # Has padding, extract clean rows
                    clean_data = bytearray()
                    for y in range(height):
                        row_start = y * stride
                        row_end = row_start + (width * 4)
                        clean_data.extend(data_array[row_start:row_end])
                    raw_data = bytes(clean_data)
                else:
                    logger.error(f"Cannot handle buffer size mismatch")
                    return
            else:
                logger.error(f"Buffer too small for resolution")
                return
        
        try:
            surface = pygame.image.frombuffer(raw_data, (width, height), 'RGBA')
        except ValueError as e:
            logger.error(f"Failed to create surface: {e}")
            return
        
        # Fast path: no transformations needed (or fit but already perfect size)
        if not self._needs_rotation and not self._needs_scaling:
            # Check if dynamic fit and already perfect size
            if self._dynamic_fit and (width != self.screen_size[0] or height != self.screen_size[1]):
                # Need to scale, fall through to slow path
                pass
            else:
                # Fast path: blit directly
                pos = self._fixed_position if self._fixed_position else ((self.screen_size[0] - width) // 2, (self.screen_size[1] - height) // 2)
                self.screen.fill((0, 0, 0))
                # Apply brightness adjustment
                adjusted_surface = self._apply_brightness(surface)
                self.screen.blit(adjusted_surface, pos)
                if self.show_fps:
                    self._draw_fps()
                pygame.display.flip()
                self._update_fps_counter()
                self._process_events()
                return
        
        # Slow path: apply transformations
        # Apply rotation
        if self._needs_rotation:
            surface = pygame.transform.rotate(surface, self.rotation)
            # Update dimensions after rotation
            if self.rotation in [90, 270]:
                width, height = height, width
        
        # Handle content resolution and scaling
        if self.content_resolution:
            # Scale to specified content resolution
            target_size = self.content_resolution
            if self.scaling != 'none':
                surface = pygame.transform.scale(surface, target_size)
            width, height = target_size
        elif self.scaling == 'fit':
            # Scale to fit display while maintaining aspect ratio
            scale = min(self.screen_size[0] / width, self.screen_size[1] / height)
            target_size = (int(width * scale), int(height * scale))
            surface = pygame.transform.scale(surface, target_size)
            width, height = target_size
        elif self.scaling == 'fill':
            # Scale to fill display, may crop
            scale = max(self.screen_size[0] / width, self.screen_size[1] / height)
            target_size = (int(width * scale), int(height * scale))
            surface = pygame.transform.scale(surface, target_size)
            width, height = target_size
        elif self.scaling == 'stretch':
            # Stretch to fill display exactly
            surface = pygame.transform.scale(surface, self.screen_size)
            width, height = self.screen_size
        # else: scaling == 'none', use original size
        
        # Calculate position
        if self.content_position is not None:
            # Explicit position in pixels
            pos = self.content_position
        elif self.content_position_name and self.content_position_name in self.POSITIONS:
            # Named position (center, top-left, etc.)
            pos_func = self.POSITIONS[self.content_position_name]
            pos = pos_func(width, height, self.screen_size[0], self.screen_size[1])
        else:
            # Default: center
            pos = ((self.screen_size[0] - width) // 2, (self.screen_size[1] - height) // 2)
        
        # Clear and blit
        self.screen.fill((0, 0, 0))
        # Apply brightness adjustment
        adjusted_surface = self._apply_brightness(surface)
        self.screen.blit(adjusted_surface, pos)
        
        # Draw FPS if enabled
        if self.show_fps:
            self._draw_fps()
        
        # Update display
        pygame.display.flip()
        
        # Update FPS counter
        self._update_fps_counter()
        
        # Process events
        self._process_events()
    
    def _update_fps_counter(self):
        """Update FPS counter (separated for optimization)"""
        self.frame_count += 1
        now = time.time()
        if now - self.last_fps_time >= 1.0:
            self.current_fps = self.frame_count / (now - self.last_fps_time)
            logger.debug(f"FPS: {self.current_fps:.1f} (source: {self.source_fps:.1f})")
            self.frame_count = 0
            self.last_fps_time = now
    
    def _draw_fps(self):
        """Draw FPS counter on screen"""
        if self.font:
            fps_text = f"{self.current_fps:.1f} FPS"
            text_surface = self.font.render(fps_text, True, (0, 255, 0))
            self.screen.blit(text_surface, (10, 10))
    
    def _process_events(self):
        """Process pygame events"""
        if not self.display_available:
            return
        
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._exit_requested = True
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        self._exit_requested = True
        except pygame.error:
            # Display disconnected during event processing
            self.display_available = False
    
    def should_exit(self) -> bool:
        """Check if exit was requested"""
        return getattr(self, '_exit_requested', False)
    
    def set_brightness(self, brightness: float):
        """
        Set display brightness
        
        Args:
            brightness: Brightness level (0.0 to 1.0)
        """
        self.brightness = max(0.0, min(1.0, brightness))  # Clamp value
        logger.info(f"Display brightness set to {self.brightness:.2f}")
    
    def get_brightness(self) -> float:
        """Get current brightness level"""
        return self.brightness
    
    def _load_persistent_brightness(self) -> Optional[float]:
        """Load brightness setting from persistent file"""
        try:
            persistent_file = '/home/catatumbo/led_test/.brightness'
            if os.path.exists(persistent_file):
                import json
                with open(persistent_file, 'r') as f:
                    data = json.load(f)
                    brightness = data.get('brightness', 1.0)
                    return max(0.0, min(1.0, brightness))  # Clamp value
        except Exception as e:
            logger.debug(f"Could not load persistent brightness: {e}")
        return None
    
    def _apply_brightness(self, surface):
        """
        Apply brightness adjustment to a pygame surface
        
        Args:
            surface: pygame.Surface to adjust
            
        Returns:
            Adjusted pygame.Surface
        """
        if self.brightness >= 1.0:
            return surface  # No adjustment needed
        
        # Create a copy to avoid modifying the original
        adjusted_surface = surface.copy()
        
        # Use a simple but effective method: create a dark overlay
        try:
            # Create a semi-transparent black overlay
            overlay = pygame.Surface(adjusted_surface.get_size(), pygame.SRCALPHA)
            alpha_value = int(255 * (1.0 - self.brightness))
            overlay.fill((0, 0, 0, alpha_value))
            
            # Blend the overlay onto the surface
            adjusted_surface.blit(overlay, (0, 0))
            
            logger.debug(f"Applied brightness {self.brightness:.2f} (alpha: {alpha_value})")
            return adjusted_surface
            
        except Exception as e:
            logger.error(f"Brightness adjustment failed: {e}")
            return surface  # Return original if method fails
    
    def cleanup(self):
        """Cleanup display resources"""
        try:
            if pygame.get_init():
                pygame.quit()
                logger.info("Display cleaned up")
        except:
            # Ignore cleanup errors
            pass

