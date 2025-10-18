"""
Test patterns for LED Receiver
Runs the original led_test_pattern.py functionality
"""

import logging
import sys

logger = logging.getLogger('ndi_receiver.test')


def run_test_patterns(args):
    """Run test pattern mode"""
    logger.info("Starting test pattern mode")
    
    # Import and run the original test pattern script
    try:
        import led_test_pattern
        
        # Override sys.argv to pass any relevant arguments
        original_argv = sys.argv
        sys.argv = ['led_test_pattern.py']
        
        # Run the test pattern
        led_test_pattern.main() if hasattr(led_test_pattern, 'main') else None
        
        # Restore argv
        sys.argv = original_argv
        
        return 0
    except ImportError:
        logger.error("Test pattern module not found")
        print("Error: led_test_pattern.py not found")
        return 1
    except Exception as e:
        logger.error(f"Test pattern error: {e}")
        return 1







