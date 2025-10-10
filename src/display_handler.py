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
    """Handles display initialization and frame rendering"""
    
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
        # Legacy parameters for backwards compatibility
        resolution: Optional[Tuple[int, int]] = None,
        position: Optional[str] = None
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
        """
        # Handle legacy parameters
        if resolution and not display_resolution:
            display_resolution = resolution
        
        self.display_resolution = display_resolution
        self.content_resolution = content_resolution
        self.content_position = content_position
        self.content_position_name = position  # For legacy string positions
        self.fullscreen = fullscreen
        self.rotation = rotation
        self.scaling = scaling
        self.show_fps = show_fps
        
        # Initialize video driver
        if video_driver != 'auto':
            os.environ['SDL_VIDEODRIVER'] = video_driver
            logger.info(f"Using video driver: {video_driver}")
        else:
            self._detect_video_driver()
        
        # Initialize pygame
        pygame.init()
        
        # Create display
        flags = pygame.FULLSCREEN if fullscreen else 0
        
        try:
            if display_resolution:
                self.screen = pygame.display.set_mode(display_resolution, flags)
                logger.info(f"Display created: {display_resolution[0]}x{display_resolution[1]}")
            else:
                # Auto-detect display size
                self.screen = pygame.display.set_mode((0, 0), flags)
                detected_size = self.screen.get_size()
                logger.info(f"Display auto-detected: {detected_size[0]}x{detected_size[1]}")
        except pygame.error as e:
            logger.error(f"Failed to create display: {e}")
            raise
        
        pygame.display.set_caption("LED Receiver")
        pygame.mouse.set_visible(False)
        
        self.clock = pygame.time.Clock()
        self.screen_size = self.screen.get_size()
        
        logger.info(f"Configuration: display={self.screen_size}, content_res={content_resolution}, position={content_position}, rotation={rotation}°, scaling={scaling}")
        
        # FPS tracking
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
        self.source_fps = 0.0
        
        # Font for FPS display
        if show_fps:
            self.font = pygame.font.Font(None, 36)
        else:
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
        
        logger.info(f"Display initialized (rotation: {rotation}°, scaling: {scaling}, optimized: {not self._needs_rotation and not self._needs_scaling})")
    
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
        
        # Create surface from frame data
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
                self.screen.blit(surface, pos)
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
        self.screen.blit(surface, pos)
        
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
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._exit_requested = True
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    self._exit_requested = True
    
    def should_exit(self) -> bool:
        """Check if exit was requested"""
        return getattr(self, '_exit_requested', False)
    
    def cleanup(self):
        """Cleanup display resources"""
        if pygame.get_init():
            pygame.quit()
            logger.info("Display cleaned up")

