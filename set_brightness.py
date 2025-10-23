#!/usr/bin/env python3
"""
Brightness Control Script for NDI Receiver

This script allows you to control the display brightness of the NDI receiver
from the command line. It communicates with the running NDI receiver service
through a control file.

Usage:
    python3 set_brightness.py <brightness>
    python3 set_brightness.py --get
    python3 set_brightness.py --help

Examples:
    python3 set_brightness.py 0.5    # Set brightness to 50%
    python3 set_brightness.py 1.0    # Set brightness to 100%
    python3 set_brightness.py 0.0    # Set brightness to 0% (black)
    python3 set_brightness.py --get  # Get current brightness
"""

import sys
import os
import json
import time
import logging
import argparse
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BrightnessController:
    """Controls brightness through the NDI receiver's display handler"""
    
    def __init__(self):
        self.brightness_file = '/tmp/ndi_receiver_brightness'
        self.persistent_file = '/home/catatumbo/led_test/.brightness'  # Persistent storage
        self.current_brightness = 1.0
        
    def set_brightness(self, brightness: float) -> bool:
        """
        Set display brightness by writing to a control file
        
        Args:
            brightness: Brightness level (0.0 to 1.0)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clamp brightness value
            brightness = max(0.0, min(1.0, brightness))
            
            brightness_data = {
                'brightness': brightness,
                'timestamp': time.time()
            }
            
            # Write brightness to control file (for runtime)
            with open(self.brightness_file, 'w') as f:
                json.dump(brightness_data, f)
            
            # Write brightness to persistent file (for boot persistence)
            with open(self.persistent_file, 'w') as f:
                json.dump(brightness_data, f)
            
            self.current_brightness = brightness
            logger.info(f"Set display brightness to {brightness:.2f} (persistent)")
            return True
            
        except Exception as e:
            logger.error(f"Error setting brightness: {e}")
            return False
    
    def get_brightness(self) -> float:
        """Get current brightness level"""
        try:
            # First check runtime file
            if os.path.exists(self.brightness_file):
                with open(self.brightness_file, 'r') as f:
                    data = json.load(f)
                    return data.get('brightness', 1.0)
            
            # Fallback to persistent file
            if os.path.exists(self.persistent_file):
                with open(self.persistent_file, 'r') as f:
                    data = json.load(f)
                    return data.get('brightness', 1.0)
        except:
            pass
        return self.current_brightness


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Control NDI receiver display brightness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 0.5      # Set brightness to 50%%
  %(prog)s 1.0      # Set brightness to 100%%
  %(prog)s 0.0      # Set brightness to 0%% (black)
  %(prog)s --get    # Get current brightness
        """
    )
    
    parser.add_argument(
        'brightness',
        nargs='?',
        type=float,
        help='Brightness level (0.0 to 1.0)'
    )
    
    parser.add_argument(
        '--get',
        action='store_true',
        help='Get current brightness level'
    )
    
    args = parser.parse_args()
    
    controller = BrightnessController()
    
    if args.get:
        # Get current brightness
        current = controller.get_brightness()
        print(f"Current brightness: {current:.2f}")
        return 0
    
    if args.brightness is None:
        parser.error("Brightness value is required (use --get to get current value)")
    
    # Validate brightness value
    if not (0.0 <= args.brightness <= 1.0):
        logger.error("Brightness must be between 0.0 and 1.0")
        return 1
    
    # Set brightness
    if controller.set_brightness(args.brightness):
        print(f"✓ Brightness set to {args.brightness:.2f}")
        return 0
    else:
        print("✗ Failed to set brightness")
        return 1


if __name__ == '__main__':
    sys.exit(main())
