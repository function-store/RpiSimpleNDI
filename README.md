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
- **Auto Route**: on by default (a matching source takes the screen over); off, the receiver keeps its source (mirroring the TDXMediaServe router)
- **60 FPS performance**: Direct BGRA format for maximum throughput
- **Flexible configuration**: JSON-based config for display, content, and NDI settings

### 🌐 Web Interface
- **Remote control**: Select NDI sources from any device on the network
- **Real-time monitoring**: Live FPS, resolution, and connection status
- **Source management**: View available sources and switch between them instantly
- **AUTO button**: turn Auto Route on or off for the screen
- **Smart override logic**: Manual selection respects new/reappearing sources
- **WebSocket updates**: Automatic state synchronization across all clients
- **Mobile-friendly**: Responsive design works on phones, tablets, and desktops

### 🌉 TDXMediaServe Hub (Multi-Component)
- **Centralized control**: Control TouchDesigner TDXMediaServe components and RPi receivers from one web page
- **Runs without TouchDesigner**: `hub_server.py` keeps the page up on an always-on Pi; TouchDesigner hubs find it and connect instead of serving
- **One port**: page, browsers (`/browser`) and nodes share port 8081, the TouchDesigner default
- **Command routing**: Browser commands are delivered to the node they name by `component_id`
- **Three receiver modes**: Standalone (local only), hub-only (no local web), or hybrid (both)

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
- Pygame library with SDL 2.32.4+ (for HDMI display access via KMS/DRM)
- NDI SDK (installed at `/usr/local/lib/libndi.so.6`)
- WebSockets library (`websockets>=10.0` for web interface)
- FFmpeg with NDI support (optional, see [FFMPEG_NDI_BUILD.md](FFMPEG_NDI_BUILD.md))
- HDMI display or LED screen
- Network connectivity (for NDI and web interface)

> **⚠️ Important:** Use **system Python** (`/usr/bin/python3`) rather than a virtual environment. Older SDL versions (e.g., SDL 2.28.4 in some venv installations) cannot access the display via KMS/DRM. System Python typically has the newer SDL 2.32.4+ which works correctly.

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

### TDXMediaServe Hub Service (Optional)

To run the TDXMediaServe hub on this Pi at boot, so the web page is always up without a TouchDesigner hub:

```bash
# Install the hub service
sudo cp hub-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hub-server.service

# Start the service immediately
sudo systemctl start hub-server.service

# Check service status
sudo systemctl status hub-server.service

# View live logs
sudo journalctl -u hub-server.service -f
```

The hub service will:
- ✅ Serve the TDXMediaServe page at `http://<pi-ip>:8081`
- ✅ Accept browsers (path `/browser`) and nodes (TouchDesigner components, RPi receivers) on that same port
- ✅ Answer `/hub-id`, so TouchDesigner hubs pointed at this Pi connect to it instead of serving
- ✅ Restart automatically if it crashes
- ✅ Wait for network connectivity before starting

**Upgrading from the old bridge server:** `bridge_server.py` and `bridge-server.service` are gone; TouchDesigner's TDXMediaServe hubs no longer work with them. On the Pi:

```bash
sudo systemctl disable --now bridge-server.service
sudo rm /etc/systemd/system/bridge-server.service
sudo cp hub-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now hub-server.service
```

The page moves from `http://<pi-ip>/` (port 80) to `http://<pi-ip>:8081`.

### Service Configuration Scenarios

**Scenario 1: Standalone Receiver (Local Web Interface Only)**
```bash
# Edit ndi-receiver.service to add --web-server flag:
# ExecStart=.../python3 ndi_receiver.py --config config.led_screen.json --web-server

sudo systemctl enable ndi-receiver.service
# Access at http://raspberrypi.local:8000
```

**Scenario 2: RPi as the Hub (Studio, Most Common)**
```bash
# Enable both services; the receiver connects to the hub on the same Pi
sudo systemctl enable hub-server.service
sudo systemctl enable ndi-receiver.service

# ndi-receiver.service already passes --bridge-url ws://localhost:8081,
# or configure it in config.led_screen.json:
# "bridge": {"enabled": true, "url": "ws://localhost:8081"}

# Access the TDXMediaServe page at http://raspberrypi.local:8081
```

In TouchDesigner, set each TDXMediaServe component's **Network Address** (or **Url**) to the Pi's IP and **Port** to `8081`. Their status reads `Using the hub at <pi-ip>:8081`.

**Scenario 3: Receiver Only (Hub in TouchDesigner)**
```bash
# Only enable receiver
sudo systemctl enable ndi-receiver.service

# Point it at the TouchDesigner machine that serves:
# "bridge": {"enabled": true, "url": "ws://TD_MACHINE_IP:8081"}

# Control via the TDXMediaServe web page at http://TD_MACHINE_IP:8081
```

**Ports:** the hub uses only 8081. The receiver's own `--web-server` page uses 8000 and 8080, so the two can run together.

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

### Auto Route

**Auto Route** (it replaced Lock, its opposite, mirroring the TDXMediaServe router) decides whether a matching source may take the screen over:

- **Off**: the receiver keeps the source it has. A new matching source, or the current one going away, does not switch it. A receiver with no source yet (booted before any sender) still takes the first source matching its pattern, so a headless display never stays black.
- **On** (default): a source matching the pattern takes the screen over when it appears, and another matching source replaces the current one when it goes or stops sending frames.

Picking a source on the web page works either way.

**Starting with Auto Route off:**

```bash
python3 ndi_receiver.py --lock
```

or in the config:

```json
"ndi": { "source_pattern": ".*_led", "auto_route": false }
```

`--auto-route` turns it back on over a config that sets it off; `--lock` overrides both.

**On the web page:** the **AUTO** button next to the output name is lit while Auto Route is on.

The hub protocol still speaks of locks (`locks`, `set_lock`, `locked`): locked means Auto Route off. That keeps receivers and routers of every version talking to each other.

### TDXMediaServe Hub (Multi-Component Control)

The hub serves the TDXMediaServe web page and relays between every node: TouchDesigner TDXMediaServe components and Raspberry Pi receivers. TDXMediaServe components in TouchDesigner carry a hub of their own; `hub_server.py` is the same hub without TouchDesigner, for a machine that is always on.

**Starting the Hub:**
```bash
# One port for the page, browsers and nodes (default 8081)
python3 hub_server.py

# Another port: use the same Port on every TouchDesigner component and receiver
python3 hub_server.py --port 8090
```

**How TouchDesigner finds it:** a TouchDesigner hub asks its **Network Address** and **Port** for `/hub-id`. When this hub answers, the TouchDesigner hub does not serve and its component connects here (`Using the hub at <pi-ip>:8081`). A TouchDesigner hub only serves when its address names its own machine and the port is free, so with every component pointed at the Pi, the Pi is the only hub. If the Pi goes down, nothing takes over: components wait and reconnect when it is back.

**The page:** the web page comes with TDXMediaServe and is not part of this repository. Copy it onto the machine that runs the hub, from a TDXMediaServe checkout or from the page file itself; it lands in `templates/hub.html` (gitignored), stamped with where it came from, and the hub logs that at start. Copy it again after updating TDXMediaServe:

```bash
python3 update_hub_page.py --from /path/to/TDXMediaServe   # a checkout
python3 update_hub_page.py --from /path/to/index.html      # or the page file
```

Without the page the hub still relays, and `http://<pi-ip>:8081` says the page is missing.

The relay follows the TouchDesigner hub's rules (protocol 2); a protocol change there needs the same change in `hub_server.py`.

**Connecting RPi Receiver to the Hub:**

Via config file:
```json
{
  "name": "LED Screen",
  "bridge": {
    "enabled": true,
    "url": "ws://hub-ip:8081",
    "component_id": "LED_Wall_Main",
    "component_name": "LED Wall - Stage Left"
  }
}
```

Via CLI (`--hub-url` and `--bridge-url` are the same option):
```bash
# Hub on this Pi
python3 ndi_receiver.py --config config.json --hub-url ws://localhost:8081

# Hub in TouchDesigner or on another Pi
python3 ndi_receiver.py --config config.json --hub-url ws://192.168.1.100:8081

# Hub only (no local web server) - saves resources
python3 ndi_receiver.py --config config.json --hub-url ws://192.168.1.100:8081 --bridge-only

# Hybrid mode (local web server + hub connection)
python3 ndi_receiver.py --config config.json --web-server --hub-url ws://192.168.1.100:8081
```

The receiver publishes itself as a routing node: its `component_id`, `component_name`, `machine_id` (the hostname) and a `routing` capability with its one output. Give every Pi its own hostname or `component_id`: stock Pis are all called `raspberrypi`, and the page groups nodes by `machine_id`.

**Connecting TouchDesigner to the Hub:**

On each TDXMediaServe component, set **Network Address** (or **Url**) to the hub's IP, **Port** to `8081`, and **Active** on.

**Use Cases:**
- Control multiple LED walls from one interface
- Mix TouchDesigner and Raspberry Pi outputs
- Keep the control page up on an always-on Pi while TouchDesigner machines come and go
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
├── hub_server.py                      # TDXMediaServe hub without TouchDesigner
├── update_hub_page.py                 # Refreshes the hub's copy of the TDXMediaServe page
├── ndi-receiver.service               # Systemd service for NDI receiver
├── hub-server.service                 # Systemd service for the hub
├── list_ndi_sources.py                # NDI source discovery utility
├── src/                               # Modular source code
│   ├── ndi_handler.py                 # NDI management (auto-switching, regex)
│   ├── display_handler.py             # Display/rendering
│   ├── config.py                      # Configuration management
│   ├── ndi_receiver_ext.py            # Web interface extension (WebSocket handling)
│   ├── server_handler.py              # TDXMediaServe hub client
│   ├── websocket_server.py            # WebSocket server
│   └── test_patterns.py               # Test patterns
├── templates/                         # Web interface files
│   ├── index.html                     # Standalone receiver web UI
│   └── hub.html                       # TDXMediaServe page served by hub_server.py (a copy)
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
└── venv/                              # Virtual environment (not recommended, use system Python)
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

### v3.4.0 - TDXMediaServe Hub
- 🌉 **TDXMediaServe hub**: `hub_server.py` replaces `bridge_server.py`; one port (8081) for the page, browsers and nodes, and TouchDesigner hubs connect to it through `/hub-id`
- 📄 **Page from TDXMediaServe**: serves a local, gitignored copy of the TDXMediaServe page, made with `update_hub_page.py`
- 🔗 **Protocol 2 client**: the receiver publishes a `routing` capability, opts out of other nodes' state, ignores everything but commands, and names itself in `source_changed`
- ⚙️ **Systemd service**: `hub-server.service` replaces `bridge-server.service`
- 🏷️ **CLI**: `--hub-url` is an alias of `--bridge-url`

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