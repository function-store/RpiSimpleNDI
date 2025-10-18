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
- **🔒 Lock functionality**: Lock sources to prevent automatic switching (mirroring TD_NDI_NamedRouter API)
- **60 FPS performance**: Direct BGRA format for maximum throughput
- **Flexible configuration**: JSON-based config for display, content, and NDI settings

### 🌐 Web Interface
- **Remote control**: Select NDI sources from any device on the network
- **Real-time monitoring**: Live FPS, resolution, and connection status
- **Source management**: View available sources and switch between them instantly
- **🔒 Lock button**: Toggle lock state to prevent/allow automatic source switching
- **Smart override logic**: Manual selection respects new/reappearing sources
- **WebSocket updates**: Automatic state synchronization across all clients
- **Mobile-friendly**: Responsive design works on phones, tablets, and desktops

### 🌉 Bridge Server (Multi-Component)
- **Centralized control**: Manage multiple TD_NDI_NamedRouter and RPi receivers from one interface
- **Component aggregation**: Merge outputs from all connected components into unified view
- **Auto-discovery**: Components auto-register with unique IDs and display names
- **Command routing**: Browser commands automatically routed to correct component
- **Flexible deployment**: Run bridge on RPi or any machine, components connect as clients
- **Three modes**: Standalone (local only), bridge-only (no local web), or hybrid (both)

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

## Auto-Start Service (systemd)

To run the NDI receiver automatically on boot:

```bash
# Install the service
sudo cp ndi-receiver.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ndi-receiver.service

# Start the service immediately
sudo systemctl start ndi-receiver.service

# Check service status
sudo systemctl status ndi-receiver.service

# View live logs
sudo journalctl -u ndi-receiver.service -f

# Stop the service
sudo systemctl stop ndi-receiver.service

# Disable auto-start
sudo systemctl disable ndi-receiver.service
```

The service will:
- ✅ Start automatically on boot
- ✅ Restart automatically if it crashes
- ✅ Wait for network connectivity before starting
- ✅ Load configuration from `config.led_screen.json`
- ✅ **Auto-reconnect to display & NDI** if disconnected/reconnected (new!)

**Note:** By default, the service runs without a local web interface. Configure bridge connection in your config file, or edit the service file to add `--web-server` for standalone operation.

### Bridge Server Service (Optional)

To run the bridge server automatically on boot:

```bash
# Install the bridge service
sudo cp bridge-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bridge-server.service

# Start the service immediately
sudo systemctl start bridge-server.service

# Check service status
sudo systemctl status bridge-server.service

# View live logs
sudo journalctl -u bridge-server.service -f

# Stop the service
sudo systemctl stop bridge-server.service

# Disable auto-start
sudo systemctl disable bridge-server.service
```

The bridge service will:
- ✅ Start HTTP server on port 8000 for web interface
- ✅ Accept browser WebSocket connections on port 8080
- ✅ Accept component connections on port 8081
- ✅ Restart automatically if it crashes
- ✅ Wait for network connectivity before starting

### Service Configuration Scenarios

**Scenario 1: Standalone Receiver (Local Web Interface Only)**
```bash
# Edit ndi-receiver.service to add --web-server flag:
# ExecStart=.../python3 ndi_receiver.py --config config.led_screen.json --web-server

sudo systemctl enable ndi-receiver.service
# Access at http://raspberrypi.local:8000
```

**Scenario 2: RPi as Bridge Hub (Most Common)**
```bash
# Enable both services (no port conflict - receiver uses bridge)
sudo systemctl enable bridge-server.service
sudo systemctl enable ndi-receiver.service

# Configure bridge in config.led_screen.json:
# "bridge": {"enabled": true, "url": "ws://localhost:8081"}

# Access unified interface at http://raspberrypi.local:8000
```

**Scenario 3: Receiver Only (Connect to External Bridge)**
```bash
# Only enable receiver
sudo systemctl enable ndi-receiver.service

# Configure external bridge in config.led_screen.json:
# "bridge": {"enabled": true, "url": "ws://TD_MACHINE_IP:8081"}

# Control via TD_NDI_NamedRouter web interface
```

**Port Conflict Warning:** Don't run `ndi-receiver.service` with `--web-server` AND `bridge-server.service` together without changing ports - they both use 8000 and 8080 by default!

### Auto-Reconnection (Display & NDI)

The program now handles disconnections gracefully - both display and NDI sources:

#### Display Reconnection
- 🔌 **No display at startup?** Program starts anyway and retries every 5 seconds
- 📺 **Display unplugged?** Video reception continues, reconnects automatically when plugged back in
- 🔄 **Automatic recovery** No manual intervention needed - just plug the display back in

#### NDI Source Reconnection
- 📡 **No NDI sources at startup?** Program starts anyway and retries every 5 seconds
- 🔌 **NDI source disappeared?** Automatically detects and reconnects when available
- 🌐 **Web interface always works** Monitor and control via browser even without NDI or display
- 🎯 **Smart switching** Works with auto-switching and manual selection features

**How it works:**
- Program checks for display and NDI every 5 seconds when disconnected
- Web server continues running without interruption
- Display and NDI resume automatically when reconnected
- No crashes, no restarts needed!

**Note:** For production LED installations with permanent displays, consider using an HDMI locking cable to prevent accidental disconnection.

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

### Lock Functionality

The receiver includes a **Lock feature** (mirroring the TD_NDI_NamedRouter API) to prevent automatic source switching:

**Lock Modes:**
- 🔓 **Unlocked** (default): Automatic source switching is enabled based on regex patterns
- 🔒 **Locked**: Automatic source switching is disabled - current source remains fixed

**How to Lock:**

**Via CLI:**
```bash
# Start with lock enabled
python3 ndi_receiver.py --lock

# Combine with config and web server
python3 ndi_receiver.py --config config.led_screen.json --web-server --lock
```

**Via Web Interface:**
- Click the 🔓/🔒 button next to the output name
- 🔓 = Unlocked (auto-switching enabled)
- 🔒 = Locked (auto-switching disabled)
- Visual indicator: Locked outputs show 🔒 in title and orange border

**When to Use Lock:**
- ✅ **Production shows**: Lock to prevent unexpected source changes during performance
- ✅ **Testing specific sources**: Lock while debugging a particular NDI source
- ✅ **Manual control**: When you want complete control over source selection
- ✅ **Stable setups**: Lock after finding the right source to prevent auto-switching

**Lock Behavior:**
- When locked, the receiver will NOT automatically switch sources even if:
  - New matching sources appear on the network
  - Current source disappears and reappears
  - Regex patterns would normally trigger a switch
- Manual source selection via web interface still works when locked
- Can be toggled on/off at any time via CLI or web interface
- State is included in WebSocket updates for real-time synchronization

### Bridge Server (Multi-Component Control)

The bridge server allows you to control multiple NDI routing components (TouchDesigner instances, Raspberry Pi receivers) through a single unified web interface.

**Starting the Bridge Server:**

You have two options:

**Option 1: Use RPi Bridge Server (Included)**
```bash
# Start on default ports (HTTP: 8000, Browser WS: 8080, Component WS: 8081)
python3 bridge_server.py

# Don't auto-open browser
python3 bridge_server.py --no-browser

# Custom ports
python3 bridge_server.py --port 8090 -w 9000 -t 9001
```

**Option 2: Use TD_NDI_NamedRouter Bridge (External)**
```bash
# On your TouchDesigner/main computer, run the TD_NDI_NamedRouter bridge:
cd /path/to/TD_NDI_NamedRouter
python3 start_server.py

# Then connect your RPi receivers to it (see below)
```

**Architecture:**
- **Port 8000** (HTTP): Serves the web interface HTML page
- **Port 8080** (WebSocket): Browser JavaScript connects here for real-time updates
- **Port 8081** (WebSocket): Components (TD instances, RPi receivers) connect here as clients
- Bridge merges all component states and displays them in a unified interface
- Commands from browsers are routed to specific components by `component_id`

**Connecting RPi Receiver to Bridge:**

Via config file:
```json
{
  "name": "LED Screen",
  "bridge": {
    "enabled": true,
    "url": "ws://bridge-server-ip:8081",
    "component_id": "LED_Wall_Main",
    "component_name": "LED Wall - Stage Left"
  }
}
```

Via CLI:
```bash
# Connect to local RPi bridge
python3 ndi_receiver.py --config config.json --bridge-url ws://localhost:8081

# Connect to external TD_NDI_NamedRouter bridge
python3 ndi_receiver.py --config config.json --bridge-url ws://192.168.1.100:8081

# Bridge only (no local web server) - saves resources
python3 ndi_receiver.py --config config.json --bridge-url ws://192.168.1.100:8081 --bridge-only

# Hybrid mode (local web server + bridge connection)
python3 ndi_receiver.py --config config.json --web-server --bridge-url ws://192.168.1.100:8081
```

**Connecting TouchDesigner to Bridge:**

In TouchDesigner NDI_NamedRouter:
1. Set WebSocket DAT to CLIENT mode
2. Network Address: `bridge-server-ip`
3. Port: `8081`
4. Active: ✓
5. Callbacks: Point to `websocket1_callbacks`

**Features:**
- Unified control of all outputs from one interface
- Auto-discovery of connected components
- Component-specific lock states
- Real-time state synchronization
- Source lists aggregated from all components
- Per-component routing of commands

**Use Cases:**
- Control multiple LED walls from one interface
- Mix TouchDesigner and Raspberry Pi outputs
- Centralized monitoring of all NDI routing
- Remote control from any device on network

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
├── bridge_server.py                   # Bridge server for multi-component control
├── ndi-receiver.service               # Systemd service for NDI receiver
├── bridge-server.service              # Systemd service for bridge server
├── list_ndi_sources.py                # NDI source discovery utility
├── src/                               # Modular source code
│   ├── ndi_handler.py                 # NDI management (auto-switching, regex)
│   ├── display_handler.py             # Display/rendering
│   ├── config.py                      # Configuration management
│   ├── ndi_receiver_ext.py            # Web interface extension (WebSocket handling)
│   ├── server_handler.py              # Bridge client handler
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

**Service won't start / No display connected:**
- ✅ **Good news!** The service now works without a display connected
- Check service status: `sudo systemctl status ndi-receiver.service`
- View live logs: `sudo journalctl -u ndi-receiver.service -f`
- Look for "Display not available - will auto-reconnect" message
- Web interface will still work at `http://localhost:8000`
- Display will reconnect automatically when plugged in (checks every 5s)

## Support

For issues and questions:
- Create an issue in this repository
- Check the documentation in the `docs/` folder
- Review troubleshooting guides

## Changelog

### v3.3.0 - Bridge Server (Multi-Component Control)
- 🌉 **Bridge server**: Run centralized server to control multiple components (TD + RPi)
- 🔗 **Bridge client**: Connect RPi receiver to bridge server for unified control
- 🎯 **Component registration**: Auto-register with unique component ID and display name
- 📊 **State aggregation**: Bridge merges states from all connected components
- 🎛️ **Unified interface**: Control all outputs through single web interface
- 🔀 **Command routing**: Browser commands routed to specific components by ID
- 🔄 **Auto-reconnect**: Bridge client auto-reconnects on disconnection
- 📝 **Config support**: Bridge URL configurable via JSON config or CLI args
- 🚀 **Three modes**: Standalone, bridge-only, or hybrid (local + bridge)
- 🔧 **Flexible deployment**: Run bridge on RPi or any machine with Python
- 🔌 **External bridge support**: Can connect to TD_NDI_NamedRouter bridge server
- 🛠️ **Non-privileged ports**: Bridge HTTP server uses port 8000 (no sudo required)
- ⚙️ **Systemd service**: Auto-start bridge server on boot with `bridge-server.service`

### v3.2.0 - Lock Functionality (TD_NDI_NamedRouter API Compatibility)
- 🔒 **Lock functionality**: Prevent automatic source switching with lock/unlock toggle
- 🎛️ **Web UI lock button**: Visual lock control with 🔓/🔒 button next to output name
- 🔐 **CLI lock flag**: Start with `--lock` to begin with source locked
- 📡 **WebSocket lock command**: `set_lock` action for remote lock control
- 🎨 **Lock visual indicators**: Orange border and 🔒 icon when locked
- 🔄 **Lock state in updates**: Lock state included in all state updates
- 🎯 **API compatibility**: Mirrors TD_NDI_NamedRouter lock behavior and API

### v3.1.0 - Auto-Reconnection & Resilience
- 🔌 **Display auto-reconnection**: Automatically reconnects if display is disconnected/reconnected
- 📡 **NDI auto-reconnection**: Automatically reconnects to NDI sources when they appear/reappear
- 💪 **Headless operation**: Runs without display or NDI sources, auto-connects when available
- 🔄 **Graceful degradation**: Web server continues running even without display or NDI
- 🔁 **Periodic reconnection checks**: Attempts reconnection every 5 seconds for both display and NDI
- 🛡️ **Crash prevention**: No more exits due to missing/disconnected displays or NDI sources
- 📝 **Systemd service**: Auto-start on boot with proper restart handling

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