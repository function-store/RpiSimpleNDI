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
    ndi_group.add_argument(
        '--lock',
        action='store_true',
        help='Start with source locked (prevents automatic source switching)'
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
    web_group.add_argument(
        '--component-id',
        type=str,
        default=None,
        help='Unique component ID for bridge mode (default: auto-generated from hostname)'
    )
    web_group.add_argument(
        '--component-name',
        type=str,
        default=None,
        help='Human-readable component name for bridge mode (default: derived from config name)'
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
    
    # Bridge options
    bridge_group = parser.add_argument_group('Bridge Options')
    bridge_group.add_argument(
        '--bridge-url',
        type=str,
        default=None,
        help='Bridge server URL for multi-component setup (e.g., ws://bridge-server:8081)'
    )
    bridge_group.add_argument(
        '--bridge-only',
        action='store_true',
        help='Connect only to bridge (no local web server)'
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
    
    # Initialize display handler (with auto-reconnection)
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
            video_driver=video_driver,
            retry_interval=5,  # Retry every 5 seconds
            max_retries=-1  # Infinite retries
        )
        if display.is_display_available():
            logger.info(f"Display initialized successfully")
        else:
            logger.warning(f"Display not available - will auto-reconnect when available")
            logger.info(f"Web server and NDI reception will continue to work")
    except Exception as e:
        logger.error(f"Failed to initialize display handler: {e}")
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
        
        # Apply lock flag if specified
        if args.lock:
            ndi.set_locked(True)
            logger.info("Source switching locked via --lock flag")
    except Exception as e:
        logger.error(f"Failed to initialize NDI: {e}")
        display.cleanup()
        return 1
    
    # Find and connect to NDI source
    ndi_connected = False
    try:
        logger.info("Searching for NDI sources...")
        if ndi.connect():
            logger.info(f"Connected to: {ndi.get_source_name()}")
            ndi_connected = True
        else:
            logger.warning("No NDI sources available - will retry during operation")
            logger.info("Web server will still work for monitoring")
    except Exception as e:
        logger.warning(f"NDI connection error: {e} - will retry during operation")
        ndi_connected = False
    
    # Initialize web extension and/or bridge client if requested
    web_extension = None
    websocket_server = None
    http_server_thread = None
    bridge_client = None
    
    if args.web_server or args.bridge_url:
        try:
            from src.ndi_receiver_ext import NDIReceiverExt
            import subprocess
            import threading
            import os
            
            logger.info("Initializing web extension...")
            
            # Determine receiver name
            receiver_name = "NDI Receiver"  # Default
            if config and config.get('name'):
                receiver_name = config.get('name')
            elif args.config:
                # Use config filename without extension as fallback
                base_name = os.path.splitext(os.path.basename(args.config))[0]
                # Convert config.led_screen -> LED Screen
                receiver_name = base_name.replace('config.', '').replace('_', ' ').title()
            
            # Get bridge settings
            # Priority: CLI args > config > defaults
            bridge_config = config.get('bridge', {}) if config else {}
            
            # Bridge URL: CLI arg > config > None
            bridge_url = args.bridge_url or (bridge_config.get('url') if bridge_config.get('enabled') else None)
            
            component_id = args.component_id or bridge_config.get('component_id')  # None = auto-generate in extension
            component_name = args.component_name or bridge_config.get('component_name') or receiver_name
            
            # Create extension
            web_extension = NDIReceiverExt(
                ndi, 
                display, 
                receiver_name=receiver_name,
                component_id=component_id,
                component_name=component_name
            )
            logger.info(f"✓ Web extension initialized (name: '{receiver_name}', component_id: '{web_extension.component_id}')")
            
            # Start local web server (unless bridge-only mode)
            if args.web_server and not args.bridge_only:
                from src.websocket_server import start_websocket_server
                
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
                
                # Start background state broadcaster for local clients
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
            
            # Connect to bridge server if URL provided
            if bridge_url:
                from src.server_handler import BridgeClientHandler
                
                bridge_client = BridgeClientHandler(bridge_url, web_extension)
                bridge_client.start()
                logger.info(f"✓ Bridge client connecting to {bridge_url}")
                
                # Attach bridge client to web extension for state updates
                if hasattr(web_extension, 'webHandler'):
                    web_extension.webHandler.bridge_client = bridge_client
            
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
        last_ndi_retry = 0
        fps_report_interval = 10  # Report FPS every 10 seconds
        ndi_retry_interval = 5  # Retry NDI connection every 5 seconds
        brightness_file = '/tmp/ndi_receiver_brightness'  # Brightness control file
        last_brightness_check = 0
        brightness_check_interval = 1.0  # Check brightness file every second
        
        while True:
            # Check for brightness changes
            now = time.time()
            if now - last_brightness_check >= brightness_check_interval:
                last_brightness_check = now
                try:
                    if os.path.exists(brightness_file):
                        with open(brightness_file, 'r') as f:
                            import json
                            data = json.load(f)
                            new_brightness = data.get('brightness', 1.0)
                            # Clamp brightness value
                            new_brightness = max(0.0, min(1.0, new_brightness))
                            if abs(new_brightness - display.get_brightness()) > 0.01:  # Only update if changed
                                display.set_brightness(new_brightness)
                except Exception as e:
                    logger.debug(f"Error reading brightness file: {e}")
                    # Continue execution even if brightness check fails
            # Try to connect to NDI if not connected
            if not ndi_connected:
                now = time.time()
                if now - last_ndi_retry >= ndi_retry_interval:
                    last_ndi_retry = now
                    logger.debug("Attempting NDI reconnection...")
                    try:
                        if ndi.connect():
                            logger.info(f"✓ NDI connected to: {ndi.get_source_name()}")
                            ndi_connected = True
                    except Exception as e:
                        logger.debug(f"NDI reconnection failed: {e}")
                
                # Sleep a bit if not connected to avoid busy loop
                if not ndi_connected:
                    time.sleep(0.1)
                    # Still check for exit even without NDI
                    if display.should_exit():
                        logger.info("Exit requested")
                        break
                    continue
            
            # Get NDI frame (only if connected)
            try:
                frame = ndi.receive_frame()
            except Exception as e:
                logger.warning(f"Error receiving frame: {e}")
                ndi_connected = False
                last_ndi_retry = time.time()
                continue
            
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
        try:
            ndi.disconnect()
        except:
            pass
        display.cleanup()
    
    logger.info("Shutdown complete")
    return 0


if __name__ == '__main__':
    sys.exit(main())

