# RpiSimpleNDI

A Raspberry Pi project for simple NDI (Network Device Interface) functionality with LED screen testing capabilities.

## Project Overview

This repository contains tools and utilities for Raspberry Pi projects, including:

- **LED Test Pattern Generator**: A comprehensive test pattern generator for 320x320 LED screens
- **NDI Integration**: Simple NDI functionality for network video streaming
- **Display Management**: Tools for handling various display configurations on Raspberry Pi

## Features

### 🎯 Smart NDI Receiver
- **Auto-discovery**: Automatically finds and connects to NDI sources matching regex patterns
- **Intelligent switching**: Switches to newly appeared sources automatically
- **Smart fallback**: Falls back to previous source when current source dies
- **Dead source detection**: Detects and recovers from non-responsive sources
- **Manual override**: Web interface for remote source selection and control
- **60 FPS performance**: Direct BGRA format for maximum throughput
- **Flexible configuration**: JSON-based config for display, content, and NDI settings

### 🌐 Web Interface
- **Remote control**: Select NDI sources from any device on the network
- **Real-time monitoring**: Live FPS, resolution, and connection status
- **Source management**: View available sources and switch between them instantly
- **Smart override logic**: Manual selection respects new/reappearing sources
- **WebSocket updates**: Automatic state synchronization across all clients
- **Mobile-friendly**: Responsive design works on phones, tablets, and desktops

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
- WebSockets library (`websockets>=10.0` for web interface)
- FFmpeg with NDI support (optional, see [FFMPEG_NDI_BUILD.md](FFMPEG_NDI_BUILD.md))
- HDMI display or LED screen
- Network connectivity (for NDI and web interface)

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

# With web interface for remote control
python3 ndi_receiver.py --config config.led_screen.json --web-server

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

### Web Interface

```bash
# Start with web interface enabled
python3 ndi_receiver.py --config config.led_screen.json --web-server

# Access from browser
http://localhost:8000          # Local access
http://raspberrypi.local:8000  # Network access (mDNS)
http://[raspberry-pi-ip]:8000  # Direct IP access

# Custom ports
python3 ndi_receiver.py --web-server --web-port 8090 --websocket-port 9000
```

**Features:**
- 🎛️ **Remote source selection**: Choose any NDI source from dropdown
- 📊 **Live monitoring**: Real-time FPS, resolution, connection status
- 🔄 **Auto-refresh**: Source list updates automatically
- 📱 **Mobile-friendly**: Works on phones and tablets
- 🌐 **Multi-client**: Multiple browsers can connect simultaneously

### Smart Auto-Switching

The receiver automatically manages NDI source connections:

**Automatic Source Discovery:**
- Scans for NDI sources matching regex patterns (e.g., `".*_led"`)
- Example: `"MACBOOK (TouchDesigner_led)"` ✓ matches, `"MACBOOK (output)"` ✗ doesn't match
- See [REGEX_PATTERN_GUIDE.md](REGEX_PATTERN_GUIDE.md) for pattern examples

**Intelligent Switching:**
- 🆕 **New source appears** → Switches immediately to the new source
- ♻️ **Source reappears** → Switches back when a source comes back online
- ⚠️ **Current source dies** → Falls back to previous source if available
- 🔄 **Predictable fallback** → Always returns to the last working source
- 🎛️ **Manual override** → Web interface selection takes priority, but respects new sources

**Manual Override Logic:**
- Manual source selection from web interface is "sticky"
- Prevents switching to existing sources
- Still switches to new/reappearing sources matching pattern
- Clears override if manually selected source dies/disappears

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
├── start_server.py                    # Web interface HTTP server
├── src/                               # Modular source code
│   ├── ndi_handler.py                 # NDI management (auto-switching, regex)
│   ├── display_handler.py             # Display/rendering
│   ├── config.py                      # Configuration management
│   ├── ndi_receiver_ext.py            # Web interface extension
│   ├── websocket_server.py            # WebSocket server
│   └── test_patterns.py               # Test patterns
├── templates/                         # Web interface files
│   └── index.html                     # Web UI (adapted from TouchDesigner)
├── config.example.json                # Example configuration
├── config.led_screen.json             # LED screen config
├── config.adaptive.json               # Adaptive display config
├── config.regex_example.json          # Regex pattern examples
├── README.md                          # This file
├── CLI_GUIDE.md                       # Complete CLI documentation
├── CONFIG_GUIDE.md                    # Configuration guide
├── REGEX_PATTERN_GUIDE.md             # Regex pattern examples
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
- Verify your NDI source name matches the regex pattern (default: `".*_led"`)
- NDI format: `"COMPUTERNAME (SourceName_led)"`
- Check pattern in config: `"source_pattern": ".*_led"`
- Check logs with `--debug` flag

**Web interface not loading:**
- Check if both HTTP and WebSocket servers started
- Verify ports are not in use: `sudo lsof -i :8000 -i :8080`
- Access via: `http://localhost:8000` or `http://raspberrypi.local:8000`
- Check browser console for WebSocket errors

**Manual source selection not working:**
- Verify source is available in the network
- Check WebSocket connection (should show "Connected" in UI)
- Look for errors in browser console (F12)
- Check terminal logs for connection errors

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

### v3.0.0 - Web Interface & Advanced Control
- 🌐 **Web interface**: Remote control and monitoring via browser
- 🎛️ **Manual source selection**: Override auto-switching from any device
- 📡 **WebSocket integration**: Real-time state synchronization
- 🔄 **Smart manual override**: Respects new/reappearing sources even with manual selection
- 🧮 **Regex pattern matching**: Flexible source filtering with full regex support
- ⚡ **Non-blocking architecture**: Background threads for state broadcasting
- 📊 **Live monitoring**: FPS, resolution, and connection status in browser
- 🎯 **Source caching**: Performance optimization for source discovery
- 🔧 **Signal handling**: Clean shutdown with Ctrl+C
- 📱 **Mobile-friendly UI**: Responsive design for all devices

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