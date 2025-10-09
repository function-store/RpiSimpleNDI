# Studio LED Screen Setup Guide

## What You Have

✅ **NDI Reception Working**: Confirmed receiving 320x320 video @ ~56 FPS from "catatumbo_led"  
✅ **Display Code Working**: `led_test_pattern.py` successfully displays on LED screen  
✅ **Optimized Performance**: Numpy-based color conversion for maximum FPS

## Files You Need

1. **`led_test_pattern.py`** - Test patterns for LED screen calibration
2. **`ndi_receiver_native_display.py`** - Main NDI receiver (uses native NDI SDK)

## At the Studio

### 1. Connect to Studio WiFi
The Pi should auto-connect to "catatumbo" network.

### 2. Test Display First
```bash
python3 led_test_pattern.py
```
- Press SPACE to cycle through patterns
- Press P to adjust position (if needed)
- Press R to rotate (currently set to 180°)
- Press ESC to exit

### 3. Run NDI Receiver

**Main Receiver** (60 FPS - optimized!):
```bash
# Set CPU to max speed (recommended)
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Run receiver
python3 ndi_receiver_native_display.py
```

Or with priority boost:
```bash
sudo nice -n -10 python3 ndi_receiver_native_display.py
```

**What it does:**
- Searches for NDI sources (looks for "catatumbo_led" first)
- Displays live video on the LED screen at 60 FPS
- Shows FPS in terminal and source framerate
- Uses BGRA format (no color conversion overhead)
- Press ESC or Ctrl+C to exit

💡 **Achieved 60 FPS** using BGRA direct format (no UYVY conversion)!

## LED Screen Configuration

The LED screen has these characteristics (already configured in code):
- Physical resolution: 800x800 (reported by display)
- Effective resolution: 320x320 (active LED area)
- Rotation: 180° (upside down by default)
- Position: Adjustable via 'P' key in `led_test_pattern.py`

## Troubleshooting

### No NDI Sources Found
- Verify NDI sender is running and sending to "catatumbo_led"
- Check both devices are on same network
- Firewall should allow NDI (port 5960)

### Display Issues
- Run `led_test_pattern.py` first to verify display works
- If display fails, try rebooting the Pi

### Low FPS
- Check network connection quality
- Verify no other processes using display: `ps aux | grep python`
- Kill other processes: `sudo pkill -9 -f ndi_receiver`

## Performance Notes

- Expected FPS: 50-60 FPS for 320x320 video
- Uses numpy for fast UYVY→RGB conversion
- Conditional scaling (only scales if needed)

## Network Info

**Studio WiFi**: catatumbo  
**Home WiFi**: FriedaBrenzlich (configured, auto-connects)

To switch networks manually:
```bash
nmcli device wifi connect "catatumbo"
```

## Quick Commands

```bash
# Kill any running receivers
sudo pkill -9 -f ndi_receiver

# Check running processes
ps aux | grep python

# Test NDI library
python3 -c "import ctypes; print(ctypes.CDLL('/usr/local/lib/libndi.so.6'))"

# Check display devices
ls -la /dev/dri/card*

# Test FFmpeg NDI support (if installed)
ffmpeg -f libndi_newtek -find_sources 1 -i dummy -t 1 -f null -
```

## Additional Documentation

- **[FFMPEG_NDI_BUILD.md](FFMPEG_NDI_BUILD.md)** - Complete guide for building FFmpeg with NDI support
- **[README.md](README.md)** - Full project documentation

---

**Last Updated**: October 10, 2025  
**Performance**: 60 FPS achieved using BGRA direct format (wired connection)  
**Tested**: NDI reception confirmed at 60 FPS on home setup

