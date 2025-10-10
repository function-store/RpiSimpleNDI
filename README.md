# RpiSimpleNDI

A Raspberry Pi project for simple NDI (Network Device Interface) functionality with LED screen testing capabilities.

## Project Overview

This repository contains tools and utilities for Raspberry Pi projects, including:

- **LED Test Pattern Generator**: A comprehensive test pattern generator for 320x320 LED screens
- **NDI Integration**: Simple NDI functionality for network video streaming
- **Display Management**: Tools for handling various display configurations on Raspberry Pi

## Features

### 🎯 Smart NDI Receiver
- **Auto-discovery**: Automatically finds and connects to NDI sources ending with `_led`
- **Intelligent switching**: Switches to newly appeared sources automatically
- **Smart fallback**: Falls back to previous source when current source dies
- **Dead source detection**: Detects and recovers from non-responsive sources
- **60 FPS performance**: Direct BGRA format for maximum throughput
- **Flexible configuration**: JSON-based config for display, content, and NDI settings

### 📺 Advanced Display Management
- **Dual resolution support**: Separate display and content resolutions
- **Content positioning**: Pixel-perfect or named position placement
- **Rotation**: 0°, 90°, 180°, 270° rotation support
- **Scaling modes**: fit, fill, stretch, or none
- **FPS monitoring**: Real-time performance tracking

### 🧪 LED Test Patterns
- Multiple test patterns optimized for LED screens
- Automatic video driver detection (KMSDRM, DirectFB, X11)
- Position and rotation controls for display alignment
- Text-based orientation verification
- Real-time pattern cycling

## Requirements

- Raspberry Pi 5 (tested on Raspberry Pi OS Bookworm/Trixie)
- Python 3.13+
- Pygame library
- NDI SDK (installed at `/usr/local/lib/libndi.so.6`)
- FFmpeg with NDI support (optional, see [FFMPEG_NDI_BUILD.md](FFMPEG_NDI_BUILD.md))
- HDMI display or LED screen
- Network connectivity (for NDI features)

## Installation

### Quick Setup (NDI SDK Already Installed)

```bash
# Clone the repository
git clone <repository-url>
cd RpiSimpleNDI

# Install Python dependencies
pip3 install -r requirements.txt
```

### Full Setup (From Scratch)

```bash
# 1. Install system dependencies
sudo apt update
sudo apt install python3-pygame python3-pip python3-numpy

# 2. Install NDI SDK
# Download from: https://ndi.video/for-developers/ndi-sdk/download/
# Then:
sudo cp libndi.so.6.* /usr/local/lib/
sudo ldconfig

# 3. (Optional) Build FFmpeg with NDI support
# See FFMPEG_NDI_BUILD.md for complete instructions

# 4. Install Python dependencies
pip3 install -r requirements.txt
```

## Usage

🎯 **Quick Start**: See [CLI_GUIDE.md](CLI_GUIDE.md) for complete CLI documentation.  
📖 **Studio Setup**: See [STUDIO_SETUP.md](STUDIO_SETUP.md) for studio-specific instructions.

### Main Application (CLI)

```bash
# Quick start with auto-discovery
python3 ndi_receiver.py

# List available NDI sources
python3 list_ndi_sources.py

# Use a configuration file
python3 ndi_receiver.py --config config.led_screen.json

# Override config with CLI options
python3 ndi_receiver.py --config config.led_screen.json --show-fps --debug

# Test patterns only (no NDI)
python3 ndi_receiver.py --test-pattern
```

See `python3 ndi_receiver.py --help` for all options.

### Smart Auto-Switching

The receiver automatically manages NDI source connections:

**Automatic Source Discovery:**
- Scans for NDI sources ending with `_led` (configurable suffix)
- Example: `"MACBOOK (TouchDesigner_led)"` ✓ matches, `"MACBOOK (output)"` ✗ doesn't match

**Intelligent Switching:**
- 🆕 **New source appears** → Switches immediately to the new source
- ♻️ **Source reappears** → Switches back when a source comes back online
- ⚠️ **Current source dies** → Falls back to previous source if available
- 🔄 **Predictable fallback** → Always returns to the last working source

**Dead Source Detection:**
- Monitors frame reception in real-time
- After 2 seconds without frames → forces source check
- After 5 seconds without frames → marks source as dead
- Automatically finds and switches to working alternatives

**Disable auto-switching:**
```bash
python3 ndi_receiver.py --no-auto-switch
```

### Legacy Applications

**NDI Receiver** (Direct, 60 FPS):
```bash
python3 ndi_receiver_native_display.py
```

**LED Test Patterns**:
```bash
python3 led_test_pattern.py
```

**Controls:**
- **ESC**: Exit
- **SPACE**: Cycle patterns (test mode only)
- **P**: Cycle LED screen positions
- **R**: Cycle rotation angles

## Project Structure

```
RpiSimpleNDI/
├── ndi_receiver.py                    # Main NDI receiver CLI ⭐
├── list_ndi_sources.py                # NDI source discovery utility
├── src/                               # Modular source code
│   ├── ndi_handler.py                 # NDI management (auto-switching)
│   ├── display_handler.py             # Display/rendering
│   ├── config.py                      # Configuration management
│   ├── server_handler.py              # WebSocket (future)
│   └── test_patterns.py               # Test patterns
├── config.example.json                # Example configuration
├── config.led_screen.json             # LED screen config
├── config.adaptive.json               # Adaptive display config
├── README.md                          # This file
├── CLI_GUIDE.md                       # Complete CLI documentation
├── STUDIO_SETUP.md                    # Studio setup guide
├── PERFORMANCE_TIPS.md                # Optimization guide
├── FFMPEG_NDI_BUILD.md                # FFmpeg compilation guide
├── led_test_pattern.py                # Legacy test patterns
├── ndi_receiver_native_display.py     # Legacy receiver (60 FPS)
├── requirements.txt                   # Python dependencies
└── venv/                              # Virtual environment
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### NDI Source Discovery
```bash
# List available NDI sources
python3 list_ndi_sources.py

# Filter by suffix
python3 list_ndi_sources.py --suffix _led

# Wait longer for discovery
python3 list_ndi_sources.py --timeout 10
```

### Common Issues

**No NDI sources found:**
- Check network connectivity (both devices on same network)
- Verify avahi-daemon is running: `systemctl status avahi-daemon`
- Check firewall settings (NDI uses TCP port 5960 and UDP multicast)
- Ensure NDI sender is active

**Auto-switching not working:**
- Verify your NDI source name ends with `_led` (inside parentheses)
- NDI format: `"COMPUTERNAME (SourceName_led)"`
- Check logs with `--debug` flag

**Low FPS / Performance issues:**
- Use `--cpu-performance` flag to set CPU governor to performance mode
- Check PERFORMANCE_TIPS.md for optimization techniques
- Ensure you're using BGRA color format (default)

**Display issues:**
- Use test patterns to verify: `python3 ndi_receiver.py --test-pattern`
- Check config file display/content resolution settings
- Verify rotation and positioning in config

## Support

For issues and questions:
- Create an issue in this repository
- Check the documentation in the `docs/` folder
- Review troubleshooting guides

## Changelog

### v2.0.0 - Smart Auto-Switching
- 🎯 **Intelligent NDI source switching**: Automatically switches to new sources with `_led` suffix
- 🔙 **Smart fallback**: Falls back to previous source when current source dies
- 🔍 **Dead source detection**: Detects non-responsive sources and recovers automatically
- 📊 **Source discovery utility**: `list_ndi_sources.py` for quick NDI network diagnostics
- ⚙️ **Modular architecture**: Refactored into `src/` with separate handlers
- 📝 **JSON configuration**: Flexible config files for different display setups
- 🎨 **Dual resolution support**: Separate display and content resolution handling
- 📍 **Advanced positioning**: Named or pixel-based content positioning
- 🔄 **Multiple scaling modes**: fit, fill, stretch, or none
- 💾 **Config profiles**: Pre-made configs for LED screen, LCD, and adaptive setups

### v1.0.0 - Initial Release
- LED test pattern generator with orientation testing
- Basic NDI functionality with native SDK integration
- 60 FPS BGRA direct format reception
- Raspberry Pi optimized display handling