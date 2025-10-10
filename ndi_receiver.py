#!/usr/bin/env python3
"""
LED Receiver - Professional NDI to LED Screen Display
A modular CLI application for receiving NDI video streams
"""

import argparse
import sys
import logging
import time
import signal
from pathlib import Path

# Version
__version__ = "1.0.0"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ndi_receiver.log')
    ]
)
logger = logging.getLogger('ndi_receiver')


def main():
    """Main entry point for the LED Receiver application"""
    
    # Setup signal handlers for clean exit
    def signal_handler(signum, frame):
        logger.info("Shutdown signal received")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    parser = argparse.ArgumentParser(
        description='LED Receiver - NDI to LED Screen Display',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect NDI source ending with '_led'
  %(prog)s
  
  # Specify a custom NDI source
  %(prog)s --source "MySource (192.168.1.100)"
  
  # Set custom source suffix
  %(prog)s --source-suffix "_display"
  
  # Enable debug logging
  %(prog)s --debug
  
  # Run in test mode (pattern display)
  %(prog)s --test-pattern
  
  # Set resolution
  %(prog)s --resolution 320x320
  
  # Full screen mode
  %(prog)s --fullscreen
        """
    )
    
    # NDI Source options
    ndi_group = parser.add_argument_group('NDI Options')
    ndi_group.add_argument(
        '-s', '--source',
        type=str,
        default=None,
        help='Specific NDI source name to connect to'
    )
    ndi_group.add_argument(
        '--source-suffix',
        type=str,
        default='_led',
        help='Auto-detect sources ending with this suffix (default: _led)'
    )
    ndi_group.add_argument(
        '--scan-timeout',
        type=int,
        default=2,
        help='Seconds to wait for NDI source discovery (default: 2)'
    )
    ndi_group.add_argument(
        '--color-format',
        type=str,
        choices=['bgra', 'uyvy', 'rgba'],
        default='bgra',
        help='NDI color format (default: bgra - fastest)'
    )
    ndi_group.add_argument(
        '--no-auto-switch',
        action='store_true',
        help='Disable automatic switching to new sources with matching suffix'
    )
    
    # Web server options
    web_group = parser.add_argument_group('Web Interface Options')
    web_group.add_argument(
        '--web-server',
        action='store_true',
        help='Start web server for remote control and monitoring'
    )
    web_group.add_argument(
        '--web-port',
        type=int,
        default=8000,
        help='HTTP server port (default: 8000, use 80 for standard but requires sudo)'
    )
    web_group.add_argument(
        '--websocket-port',
        type=int,
        default=8080,
        help='WebSocket server port (default: 8080)'
    )
    
    # Display options
    display_group = parser.add_argument_group('Display Options')
    display_group.add_argument(
        '-r', '--resolution',
        type=str,
        default='320x320',
        help='Display resolution WxH (default: 320x320)'
    )
    display_group.add_argument(
        '-f', '--fullscreen',
        action='store_true',
        help='Run in fullscreen mode'
    )
    display_group.add_argument(
        '--rotation',
        type=int,
        choices=[0, 90, 180, 270],
        default=180,
        help='Screen rotation in degrees (default: 180)'
    )
    display_group.add_argument(
        '--position',
        type=str,
        choices=['center', 'top-left', 'top-right', 'bottom-left', 'bottom-right'],
        default='center',
        help='LED screen position on display (default: center)'
    )
    display_group.add_argument(
        '--show-fps',
        action='store_true',
        help='Show FPS counter on screen'
    )
    display_group.add_argument(
        '--video-driver',
        type=str,
        choices=['kmsdrm', 'directfb', 'x11', 'auto'],
        default='auto',
        help='SDL video driver (default: auto)'
    )
    
    # Performance options
    perf_group = parser.add_argument_group('Performance Options')
    perf_group.add_argument(
        '--cpu-performance',
        action='store_true',
        help='Set CPU governor to performance mode (requires sudo)'
    )
    perf_group.add_argument(
        '--priority',
        type=int,
        default=0,
        help='Process priority (-20 to 19, negative = higher priority, requires sudo)'
    )
    
    # Server options (for future use)
    server_group = parser.add_argument_group('Server Options (Future)')
    server_group.add_argument(
        '--server',
        type=str,
        default=None,
        help='WebSocket server URL (e.g., ws://server:8080)'
    )
    server_group.add_argument(
        '--server-token',
        type=str,
        default=None,
        help='Authentication token for server'
    )
    
    # General options
    parser.add_argument(
        '--test-pattern',
        action='store_true',
        help='Run in test pattern mode (no NDI)'
    )
    parser.add_argument(
        '--list-sources',
        action='store_true',
        help='List available NDI sources and exit'
    )
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Load configuration from file'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Log startup
    logger.info(f"LED Receiver v{__version__} starting...")
    logger.debug(f"Arguments: {vars(args)}")
    
    # Import modules here to avoid import overhead for --help
    from src.ndi_handler import NDIHandler
    from src.display_handler import DisplayHandler
    from src.config import Config
    
    # Load config if specified
    config = None
    if args.config:
        config = Config.load(args.config)
        logger.info(f"Loaded configuration from {args.config}")
    
    # List sources mode
    if args.list_sources:
        logger.info("Scanning for NDI sources...")
        # Convert CLI suffix to regex pattern
        source_pattern = f'.*{args.source_suffix}' if args.source_suffix else '.*_led'
        ndi = NDIHandler(
            source_pattern=source_pattern,
            scan_timeout=args.scan_timeout
        )
        sources = ndi.list_sources()
        
        if sources:
            print("\nAvailable NDI sources:")
            for i, source in enumerate(sources, 1):
                # Check if matches pattern
                matches = ndi._matches_pattern(source)
                suffix = " ✓" if matches else ""
                print(f"  [{i}] {source}{suffix}")
        else:
            print("\nNo NDI sources found.")
        
        return 0
    
    # Test pattern mode
    if args.test_pattern:
        logger.info("Running in test pattern mode")
        from src.test_patterns import run_test_patterns
        return run_test_patterns(args)
    
    # Set CPU performance mode
    if args.cpu_performance:
        try:
            import os
            os.system('echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null')
            logger.info("CPU governor set to performance mode")
        except Exception as e:
            logger.warning(f"Failed to set CPU performance mode: {e}")
    
    # Get configuration values (config file or args)
    if config:
        # Load from config file
        display_res = config.get('display', {}).get('resolution')
        content_res = config.get('content', {}).get('resolution')
        content_pos = config.get('content', {}).get('position')
        rotation = config.get('content', {}).get('rotation', args.rotation)
        scaling = config.get('content', {}).get('scaling', 'fit')
        fullscreen = config.get('display', {}).get('fullscreen', args.fullscreen)
        show_fps = config.get('display', {}).get('show_fps', args.show_fps)
        video_driver = config.get('display', {}).get('video_driver', args.video_driver)
    else:
        # Use command line args
        display_res = args.resolution
        content_res = None
        content_pos = args.position
        rotation = args.rotation
        scaling = 'fit'
        fullscreen = args.fullscreen
        show_fps = args.show_fps
        video_driver = args.video_driver
    
    # Parse display resolution
    display_resolution = None
    if display_res:
        try:
            width, height = map(int, display_res.split('x'))
            display_resolution = (width, height)
        except (ValueError, AttributeError):
            logger.error(f"Invalid display resolution format: {display_res}")
            return 1
    
    # Parse content resolution
    content_resolution = None
    if content_res:
        try:
            width, height = map(int, content_res.split('x'))
            content_resolution = (width, height)
        except (ValueError, AttributeError):
            logger.error(f"Invalid content resolution format: {content_res}")
            return 1
    
    # Parse content position
    content_position = None
    if content_pos and ',' in str(content_pos):
        try:
            x, y = map(int, content_pos.split(','))
            content_position = (x, y)
            content_pos_name = None
        except (ValueError, AttributeError):
            logger.error(f"Invalid content position format: {content_pos}")
            return 1
    else:
        content_pos_name = content_pos if isinstance(content_pos, str) else None
    
    # Initialize display handler
    try:
        display = DisplayHandler(
            display_resolution=display_resolution,
            content_resolution=content_resolution,
            content_position=content_position,
            position=content_pos_name,
            fullscreen=fullscreen,
            rotation=rotation,
            scaling=scaling,
            show_fps=show_fps,
            video_driver=video_driver
        )
        logger.info(f"Display initialized")
    except Exception as e:
        logger.error(f"Failed to initialize display: {e}")
        return 1
    
    # Initialize NDI handler
    try:
        # Get NDI config with defaults
        ndi_config = config.get('ndi', {}) if config else {}
        
        # Use source_pattern from config, or convert CLI suffix to regex pattern
        source_pattern = ndi_config.get('source_pattern')
        if not source_pattern and args.source_suffix:
            # Convert CLI suffix to regex pattern (e.g., '_led' -> '.*_led')
            source_pattern = f'.*{args.source_suffix}'
        if not source_pattern:
            source_pattern = '.*_led'  # Default
        
        ndi = NDIHandler(
            source_name=args.source,
            source_pattern=source_pattern,
            enable_plural_handling=ndi_config.get('enable_plural_handling', False),
            case_sensitive=ndi_config.get('case_sensitive', False),
            scan_timeout=args.scan_timeout,
            color_format=args.color_format,
            auto_switch=not args.no_auto_switch
        )
    except Exception as e:
        logger.error(f"Failed to initialize NDI: {e}")
        display.cleanup()
        return 1
    
    # Find and connect to NDI source
    try:
        logger.info("Searching for NDI sources...")
        if not ndi.connect():
            logger.error("Failed to connect to NDI source")
            display.cleanup()
            return 1
        
        logger.info(f"Connected to: {ndi.get_source_name()}")
    except Exception as e:
        logger.error(f"NDI connection error: {e}")
        display.cleanup()
        return 1
    
    # Initialize web server if requested
    web_extension = None
    websocket_server = None
    http_server_thread = None
    
    if args.web_server:
        try:
            from src.ndi_receiver_ext import NDIReceiverExt
            from src.websocket_server import start_websocket_server
            import subprocess
            import threading
            import os
            
            logger.info("Initializing web interface...")
            
            # Determine receiver name
            receiver_name = "NDI Receiver"  # Default
            if config and config.get('name'):
                receiver_name = config.get('name')
            elif args.config:
                # Use config filename without extension as fallback
                base_name = os.path.splitext(os.path.basename(args.config))[0]
                # Convert config.led_screen -> LED Screen
                receiver_name = base_name.replace('config.', '').replace('_', ' ').title()
            
            # Create extension
            web_extension = NDIReceiverExt(ndi, display, receiver_name=receiver_name)
            logger.info(f"✓ Web extension initialized (name: '{receiver_name}')")
            
            # Start WebSocket server
            websocket_server = start_websocket_server(web_extension, port=args.websocket_port)
            logger.info(f"✓ WebSocket server started on port {args.websocket_port}")
            
            # Start HTTP server for web interface
            def run_http_server():
                try:
                    cmd = [
                        'python3', 'start_server.py',
                        '--port', str(args.web_port),
                        '--websocket-port', str(args.websocket_port),
                        '--no-browser'
                    ]
                    subprocess.run(cmd, cwd='/home/catatumbo/led_test')
                except Exception as e:
                    logger.error(f"HTTP server error: {e}")
            
            http_server_thread = threading.Thread(target=run_http_server, daemon=True)
            http_server_thread.start()
            logger.info(f"✓ HTTP server started on port {args.web_port}")
            
            # Start background state broadcaster (non-blocking)
            def broadcast_state_updates():
                import time
                while True:
                    time.sleep(10)  # Broadcast every 10 seconds
                    try:
                        if web_extension and hasattr(web_extension, 'webHandler'):
                            web_extension.webHandler.broadcastStateUpdate()
                    except Exception as e:
                        logger.debug(f"Error broadcasting state: {e}")
            
            broadcast_thread = threading.Thread(target=broadcast_state_updates, daemon=True)
            broadcast_thread.start()
            logger.info(f"✓ State broadcast thread started")
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("🌐 WEB INTERFACE READY")
            logger.info("=" * 60)
            logger.info(f"  Local:    http://localhost:{args.web_port}")
            logger.info(f"  Network:  http://[raspberry-pi-ip]:{args.web_port}")
            logger.info(f"  WebSocket: ws://localhost:{args.websocket_port}")
            logger.info("=" * 60)
            logger.info("")
            
        except ImportError as e:
            logger.error(f"Failed to load web server dependencies: {e}")
            logger.error("Install with: pip3 install websockets")
        except Exception as e:
            logger.error(f"Failed to initialize web interface: {e}")
            logger.exception(e)
    
    # Main loop
    logger.info("Starting video reception...")
    try:
        frame_count = 0
        start_time = time.time()
        last_fps_report = start_time
        fps_report_interval = 10  # Report FPS every 10 seconds
        
        while True:
            # Get NDI frame
            frame = ndi.receive_frame()
            
            if frame is not None:
                frame_count += 1
                
                # Display frame
                display.update(frame)
                
                # Report FPS every 10 seconds
                now = time.time()
                if now - last_fps_report >= fps_report_interval:
                    elapsed = now - start_time
                    avg_fps = frame_count / elapsed if elapsed > 0 else 0
                    _, (width, height), source_fps = frame
                    logger.info(f"FPS Report: {avg_fps:.1f} fps (source: {source_fps:.1f} fps) | Frames: {frame_count} | Resolution: {width}x{height}")
                    last_fps_report = now
                
                # Check for exit
                if display.should_exit():
                    logger.info("Exit requested")
                    break
        
        # Final stats
        elapsed = time.time() - start_time
        avg_fps = frame_count / elapsed if elapsed > 0 else 0
        logger.info(f"Session complete: {frame_count} frames in {elapsed:.1f}s (avg: {avg_fps:.1f} fps)")
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Runtime error: {e}", exc_info=True)
        return 1
    finally:
        # Cleanup
        logger.info("Cleaning up...")
        ndi.disconnect()
        display.cleanup()
    
    logger.info("Shutdown complete")
    return 0


if __name__ == '__main__':
    sys.exit(main())

