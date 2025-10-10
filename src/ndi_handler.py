"""
NDI Handler - Manages NDI source discovery and frame reception
"""

import ctypes
from ctypes import *
import time
import logging
from typing import Optional, List, Tuple
import numpy as np

logger = logging.getLogger('ndi_receiver.ndi')


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


class NDIHandler:
    """Handles NDI source discovery and frame reception"""
    
    # Color format constants
    COLOR_FORMATS = {
        'uyvy': 1,
        'bgra': 2,
        'rgba': 3
    }
    
    def __init__(
        self,
        source_name: Optional[str] = None,
        source_suffix: str = '_led',
        scan_timeout: int = 2,
        color_format: str = 'bgra',
        auto_switch: bool = True
    ):
        """
        Initialize NDI handler
        
        Args:
            source_name: Specific NDI source to connect to (or None for auto-detect)
            source_suffix: Auto-detect sources ending with this suffix
            scan_timeout: Seconds to wait for source discovery
            color_format: Color format ('bgra', 'uyvy', 'rgba')
            auto_switch: Automatically switch to new sources with matching suffix
        """
        self.source_name = source_name
        self.source_suffix = source_suffix
        self.scan_timeout = scan_timeout
        self.color_format_name = color_format
        self.color_format = self.COLOR_FORMATS.get(color_format, 2)
        self.auto_switch = auto_switch
        
        self.ndi_lib = None
        self.ndi_find = None
        self.ndi_recv = None
        self.connected_source = None
        self.previous_source = None  # Track the source we were on before current
        self.video_frame = NDIlib_video_frame_v2_t()
        self.last_source_check = 0
        self.source_check_interval = 2.0  # Check for new sources every 2 seconds
        self.last_frame_time = 0
        self.no_frame_timeout = 5.0  # Consider source dead after 5 seconds without frames
        self.previous_available_sources = set()  # Track what was available in last check
        
        # Load NDI library
        try:
            self.ndi_lib = CDLL("/usr/local/lib/libndi.so.6")
            self._setup_functions()
            logger.info("NDI library loaded successfully")
        except OSError as e:
            logger.error(f"Failed to load NDI library: {e}")
            raise
        
        # Initialize NDI
        if not self.ndi_lib.NDIlib_initialize():
            raise RuntimeError("Failed to initialize NDI")
        
        logger.info(f"NDI initialized (format: {color_format})")
    
    def _setup_functions(self):
        """Setup NDI library function signatures"""
        self.ndi_lib.NDIlib_initialize.restype = c_bool
        self.ndi_lib.NDIlib_find_create_v2.restype = c_void_p
        self.ndi_lib.NDIlib_find_create_v2.argtypes = [c_void_p]
        self.ndi_lib.NDIlib_find_get_current_sources.restype = POINTER(NDIlib_source_t)
        self.ndi_lib.NDIlib_find_get_current_sources.argtypes = [c_void_p, POINTER(c_uint32)]
        self.ndi_lib.NDIlib_recv_create_v3.restype = c_void_p
        self.ndi_lib.NDIlib_recv_create_v3.argtypes = [POINTER(NDIlib_recv_create_v3_t)]
        self.ndi_lib.NDIlib_recv_capture_v2.restype = c_int
        self.ndi_lib.NDIlib_recv_capture_v2.argtypes = [c_void_p, POINTER(NDIlib_video_frame_v2_t), c_void_p, c_void_p, c_uint32]
        self.ndi_lib.NDIlib_recv_free_video_v2.argtypes = [c_void_p, POINTER(NDIlib_video_frame_v2_t)]
        self.ndi_lib.NDIlib_recv_destroy.argtypes = [c_void_p]
        self.ndi_lib.NDIlib_find_destroy.argtypes = [c_void_p]
    
    def list_sources(self) -> List[str]:
        """List all available NDI sources"""
        self.ndi_find = self.ndi_lib.NDIlib_find_create_v2(None)
        time.sleep(self.scan_timeout)
        
        num_sources = c_uint32(0)
        sources = self.ndi_lib.NDIlib_find_get_current_sources(self.ndi_find, byref(num_sources))
        
        source_names = []
        for i in range(num_sources.value):
            source = sources[i]
            name = source.p_ndi_name.decode('utf-8') if source.p_ndi_name else ""
            source_names.append(name)
        
        return source_names
    
    def connect(self) -> bool:
        """
        Connect to NDI source
        
        Returns:
            True if connected successfully
        """
        # Create finder
        self.ndi_find = self.ndi_lib.NDIlib_find_create_v2(None)
        logger.info(f"Scanning for NDI sources (timeout: {self.scan_timeout}s)...")
        time.sleep(self.scan_timeout)
        
        # Get sources
        num_sources = c_uint32(0)
        sources = self.ndi_lib.NDIlib_find_get_current_sources(self.ndi_find, byref(num_sources))
        
        logger.info(f"Found {num_sources.value} NDI sources")
        
        # Select source
        target_source = None
        
        for i in range(num_sources.value):
            source = sources[i]
            name = source.p_ndi_name.decode('utf-8') if source.p_ndi_name else ""
            logger.debug(f"  Source {i}: {name}")
            
            # Exact match
            if self.source_name and name == self.source_name:
                target_source = source
                logger.info(f"Found exact match: {name}")
                break
            
            # Suffix match (priority)
            # NDI sources are formatted as "COMPUTERNAME (SourceName)"
            matches_suffix = False
            if '(' in name and ')' in name:
                source_part = name.split('(')[1].split(')')[0]
                matches_suffix = source_part.endswith(self.source_suffix)
            else:
                matches_suffix = name.endswith(self.source_suffix)
            
            if matches_suffix:
                target_source = source
                logger.info(f"Found source with suffix '{self.source_suffix}': {name}")
                break
        
        # Fallback to first source
        if not target_source and num_sources.value > 0:
            target_source = sources[0]
            name = target_source.p_ndi_name.decode('utf-8') if target_source.p_ndi_name else ""
            logger.warning(f"No source with suffix '{self.source_suffix}' found, using first: {name}")
        
        if not target_source:
            logger.error("No NDI sources available")
            return False
        
        # Create receiver
        recv_settings = NDIlib_recv_create_v3_t()
        recv_settings.source_to_connect_to = target_source
        recv_settings.color_format = self.color_format
        recv_settings.bandwidth = 100
        recv_settings.allow_video_fields = False
        recv_settings.p_ndi_recv_name = b"LED Receiver"
        
        self.ndi_recv = self.ndi_lib.NDIlib_recv_create_v3(byref(recv_settings))
        
        if not self.ndi_recv:
            logger.error("Failed to create NDI receiver")
            return False
        
        self.connected_source = target_source.p_ndi_name.decode('utf-8')
        logger.info(f"Connected to: {self.connected_source}")
        return True
    
    def check_and_switch_sources(self) -> bool:
        """
        Check for new NDI sources and switch if a better one is available
        
        Returns:
            True if switched to a new source
        """
        if not self.auto_switch or not self.ndi_find:
            return False
        
        import time
        now = time.time()
        
        # Check if we're connected but not receiving frames (dead source)
        is_source_dead = False
        if self.ndi_recv and self.last_frame_time > 0:
            time_since_last_frame = now - self.last_frame_time
            if time_since_last_frame > self.no_frame_timeout:
                logger.warning(f"No frames received for {time_since_last_frame:.1f}s - source may be dead")
                is_source_dead = True
        
        # Only check periodically (but always check if source is dead)
        if not is_source_dead and (now - self.last_source_check < self.source_check_interval):
            return False
        
        self.last_source_check = now
        
        # Get current sources
        num_sources = c_uint32(0)
        sources_ptr = self.ndi_lib.NDIlib_find_get_current_sources(self.ndi_find, byref(num_sources))
        
        if num_sources.value == 0:
            return False
        
        # Cast pointer to array
        sources = cast(sources_ptr, POINTER(NDIlib_source_t))
        
        # Check if current source still exists and find all matching sources
        current_source_exists = False
        available_sources = []
        
        for i in range(num_sources.value):
            source = sources[i]
            name = source.p_ndi_name.decode('utf-8') if source.p_ndi_name else ""
            
            # NDI sources are formatted as "COMPUTERNAME (SourceName)"
            # Check if the source name (part in parentheses) ends with suffix
            matches_suffix = False
            if '(' in name and ')' in name:
                # Extract source name from parentheses
                source_part = name.split('(')[1].split(')')[0]
                matches_suffix = source_part.endswith(self.source_suffix)
            else:
                # Fallback to full name check
                matches_suffix = name.endswith(self.source_suffix)
            
            if matches_suffix:
                available_sources.append((name, source))
                if name == self.connected_source:
                    current_source_exists = True
        
        if len(available_sources) == 0:
            return False
        
        # Get current available source names
        current_available = set(name for name, _ in available_sources)
        
        # Find sources that just appeared (weren't available in last check)
        newly_appeared = current_available - self.previous_available_sources
        newly_appeared_with_suffix = [(name, source) for name, source in available_sources 
                                      if name in newly_appeared and name != self.connected_source]
        
        # Update previous available sources for next check
        self.previous_available_sources = current_available.copy()
        
        # Determine if we should switch
        should_switch = False
        switch_reason = ""
        new_sources = []
        
        if not current_source_exists:
            # Current source disappeared - try to fall back to previous source first
            logger.warning(f"Current source '{self.connected_source}' is no longer available")
            
            # Check if previous source is available
            if self.previous_source and any(name == self.previous_source for name, _ in available_sources):
                logger.info(f"Falling back to previous source: {self.previous_source}")
                new_sources = [(name, source) for name, source in available_sources if name == self.previous_source]
                switch_reason = "current source disappeared, falling back to previous"
            else:
                # Previous not available, pick any other source
                logger.info(f"Previous source not available, picking from available sources")
                new_sources = [(name, source) for name, source in available_sources if name != self.connected_source]
                switch_reason = "current source disappeared"
            should_switch = True
            
        elif is_source_dead:
            # Current source is dead - try to fall back to previous source first
            logger.warning(f"Current source '{self.connected_source}' appears to be dead (no frames)")
            
            # Check if previous source is available
            if self.previous_source and any(name == self.previous_source for name, _ in available_sources):
                logger.info(f"Falling back to previous source: {self.previous_source}")
                new_sources = [(name, source) for name, source in available_sources if name == self.previous_source]
                switch_reason = "current source dead, falling back to previous"
            else:
                # Previous not available, pick any other source
                logger.info(f"Previous source not available, picking from available sources")
                new_sources = [(name, source) for name, source in available_sources if name != self.connected_source]
                switch_reason = "current source not sending frames"
            should_switch = True
            
        elif newly_appeared_with_suffix:
            # A source appeared (or reappeared) that wasn't available in the last check
            new_sources = newly_appeared_with_suffix
            should_switch = True
            switch_reason = "source (re)appeared"
        
        if should_switch and new_sources:
            # Pick the first new source (they're in discovery order, newest typically last)
            # But we'll take the last one to prefer the most recent
            name, source = new_sources[-1]  # Use last = most recent
            
            logger.info(f"Switching from '{self.connected_source}' to '{name}' ({switch_reason})")
            
            # Disconnect from current source
            if self.ndi_recv:
                self.ndi_lib.NDIlib_recv_destroy(self.ndi_recv)
                self.ndi_recv = None
            
            # Connect to new source
            recv_settings = NDIlib_recv_create_v3_t()
            recv_settings.source_to_connect_to = source
            recv_settings.color_format = self.color_format
            recv_settings.bandwidth = 100
            recv_settings.allow_video_fields = False
            recv_settings.p_ndi_recv_name = b"LED Receiver"
            
            self.ndi_recv = self.ndi_lib.NDIlib_recv_create_v3(byref(recv_settings))
            
            if self.ndi_recv:
                # Track the previous source before switching
                self.previous_source = self.connected_source
                self.connected_source = name
                logger.info(f"✓ Connected to: {name}")
                return True
            else:
                logger.error(f"Failed to connect to new source: {name}")
        
        return False
    
    def receive_frame(self, timeout_ms: int = 100) -> Optional[Tuple[np.ndarray, Tuple[int, int], float]]:
        """
        Receive a video frame from NDI
        
        Args:
            timeout_ms: Timeout in milliseconds
        
        Returns:
            Tuple of (frame_data, resolution, fps) or None if no frame
        """
        if not self.ndi_recv:
            return None
        
        # Check for new sources to switch to
        self.check_and_switch_sources()
        
        frame_type = self.ndi_lib.NDIlib_recv_capture_v2(
            self.ndi_recv,
            byref(self.video_frame),
            None,
            None,
            timeout_ms
        )
        
        if frame_type == 1:  # Video frame
            # Update last frame time
            import time
            self.last_frame_time = time.time()
            
            width = self.video_frame.xres
            height = self.video_frame.yres
            stride = self.video_frame.line_stride_in_bytes
            
            # Calculate FPS
            fps = 0.0
            if self.video_frame.frame_rate_D > 0:
                fps = self.video_frame.frame_rate_N / self.video_frame.frame_rate_D
            
            # Get frame data
            frame_data = ctypes.string_at(self.video_frame.p_data, stride * height)
            
            # Free the frame
            self.ndi_lib.NDIlib_recv_free_video_v2(self.ndi_recv, byref(self.video_frame))
            
            return (frame_data, (width, height), fps)
        
        # No frame received - if we've been getting frames but now stopped, force a check
        import time
        if self.last_frame_time > 0:
            time_since_last = time.time() - self.last_frame_time
            if time_since_last > 2.0:  # Been 2+ seconds without frames
                # Force immediate source check
                self.last_source_check = 0
        
        return None
    
    def get_source_name(self) -> Optional[str]:
        """Get the name of the connected source"""
        return self.connected_source
    
    def get_color_format(self) -> str:
        """Get the current color format"""
        return self.color_format_name
    
    def disconnect(self):
        """Disconnect from NDI source and cleanup"""
        if self.ndi_recv:
            self.ndi_lib.NDIlib_recv_destroy(self.ndi_recv)
            self.ndi_recv = None
            logger.info("NDI receiver destroyed")
        
        if self.ndi_find:
            self.ndi_lib.NDIlib_find_destroy(self.ndi_find)
            self.ndi_find = None
        
        if self.ndi_lib:
            self.ndi_lib.NDIlib_destroy()
            logger.info("NDI library shutdown")

