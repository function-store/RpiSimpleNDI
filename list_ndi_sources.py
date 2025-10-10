#!/usr/bin/env python3
"""
Simple utility to list available NDI sources on the network
"""

import sys
import time
from ctypes import *

# NDI structures
class NDIlib_source_t(Structure):
    _fields_ = [
        ("p_ndi_name", c_char_p),
        ("p_url_address", c_char_p),
    ]

class NDIlib_find_create_t(Structure):
    _fields_ = [
        ("show_local_sources", c_bool),
        ("p_groups", c_char_p),
        ("p_extra_ips", c_char_p),
    ]

def list_ndi_sources(timeout=5, filter_suffix=None):
    """
    List all available NDI sources
    
    Args:
        timeout: Seconds to wait for discovery
        filter_suffix: Only show sources ending with this string
    """
    try:
        # Load NDI library
        ndi_lib = CDLL("/usr/local/lib/libndi.so.6")
        
        # Initialize NDI
        if not ndi_lib.NDIlib_initialize():
            print("❌ Failed to initialize NDI library")
            return 1
        
        print("✅ NDI library initialized")
        print(f"⏳ Scanning for NDI sources (waiting {timeout}s)...\n")
        
        # Create finder
        find_settings = NDIlib_find_create_t()
        find_settings.show_local_sources = True
        find_settings.p_groups = None
        find_settings.p_extra_ips = None
        
        ndi_find = ndi_lib.NDIlib_find_create_v2(byref(find_settings))
        if not ndi_find:
            print("❌ Failed to create NDI finder")
            ndi_lib.NDIlib_destroy()
            return 1
        
        # Wait for sources
        time.sleep(timeout)
        
        # Get sources
        num_sources = c_uint32(0)
        sources_ptr = ndi_lib.NDIlib_find_get_current_sources(ndi_find, byref(num_sources))
        
        if num_sources.value == 0:
            print("❌ No NDI sources found on the network")
            print("\nTroubleshooting:")
            print("  • Make sure your NDI sender is running")
            print("  • Check that both devices are on the same network")
            print("  • Verify firewall settings allow NDI traffic")
            print("  • Check if avahi-daemon is running: systemctl status avahi-daemon")
        else:
            print(f"📡 Found {num_sources.value} NDI source(s):\n")
            print("─" * 70)
            
            # Cast pointer to array
            sources = cast(sources_ptr, POINTER(NDIlib_source_t))
            
            filtered_count = 0
            for i in range(num_sources.value):
                source = sources[i]
                name = source.p_ndi_name.decode('utf-8') if source.p_ndi_name else "Unknown"
                url = source.p_url_address.decode('utf-8') if source.p_url_address else "Unknown"
                
                # NDI sources are formatted as "COMPUTERNAME (SourceName)"
                # Extract source name for suffix matching
                source_name = name
                if '(' in name and ')' in name:
                    source_name = name.split('(')[1].split(')')[0]
                
                # Apply filter if specified
                if filter_suffix and not source_name.endswith(filter_suffix):
                    continue
                
                filtered_count += 1
                
                # Check if name matches common suffix
                suffix_match = ""
                if source_name.endswith("_led"):
                    suffix_match = " ✨ (matches _led)"
                elif source_name.endswith("_LED"):
                    suffix_match = " ✨ (matches _LED)"
                
                print(f"{filtered_count}. {name}{suffix_match}")
                print(f"   URL: {url}")
                print("─" * 70)
            
            if filter_suffix and filtered_count == 0:
                print(f"\n⚠️  No sources found with suffix '{filter_suffix}'")
                print(f"    Total sources available: {num_sources.value}")
        
        # Cleanup
        ndi_lib.NDIlib_find_destroy(ndi_find)
        ndi_lib.NDIlib_destroy()
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="List available NDI sources on the network",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # List all sources
  %(prog)s --timeout 10       # Wait 10 seconds for discovery
  %(prog)s --suffix _led      # Only show sources ending with '_led'
        """
    )
    
    parser.add_argument(
        '-t', '--timeout',
        type=int,
        default=5,
        help='Seconds to wait for NDI source discovery (default: 5)'
    )
    
    parser.add_argument(
        '-s', '--suffix',
        type=str,
        help='Only show sources ending with this suffix (e.g., _led)'
    )
    
    args = parser.parse_args()
    
    sys.exit(list_ndi_sources(timeout=args.timeout, filter_suffix=args.suffix))

