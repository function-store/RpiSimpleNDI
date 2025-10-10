# LED Receiver CLI Guide

Professional CLI application for receiving NDI video streams and displaying them on LED screens.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Line Options](#command-line-options)
- [Configuration File](#configuration-file)
- [Usage Examples](#usage-examples)
- [Architecture](#architecture)
- [Future: Server Integration](#future-server-integration)

## Installation

```bash
# Install dependencies
pip3 install -r requirements.txt

# Make executable
chmod +x ndi_receiver.py
```

## Quick Start

### Auto-detect and connect
```bash
# Automatically finds sources ending with '_led'
python3 ndi_receiver.py
```

### List available sources
```bash
python3 ndi_receiver.py --list-sources
```

### Run with performance optimizations
```bash
# Enable CPU performance mode and run
python3 ndi_receiver.py --cpu-performance
```

## Command Line Options

### NDI Options

| Option | Default | Description |
|--------|---------|-------------|
| `-s, --source SOURCE` | Auto-detect | Specific NDI source name |
| `--source-suffix SUFFIX` | `_led` | Auto-detect sources ending with suffix |
| `--scan-timeout N` | `2` | Seconds to wait for source discovery |
| `--color-format FORMAT` | `bgra` | Color format (`bgra`, `uyvy`, `rgba`) |

**Note**: `bgra` format provides best performance (60 FPS) as it requires no conversion.

### Display Options

| Option | Default | Description |
|--------|---------|-------------|
| `-r, --resolution WxH` | `320x320` | Display resolution |
| `-f, --fullscreen` | Off | Run in fullscreen mode |
| `--rotation ANGLE` | `180` | Screen rotation (0, 90, 180, 270) |
| `--position POS` | `center` | Screen position (center, top-left, etc.) |
| `--show-fps` | Off | Show FPS counter on screen |
| `--video-driver DRIVER` | `auto` | SDL video driver |

### Performance Options

| Option | Description |
|--------|-------------|
| `--cpu-performance` | Set CPU to performance mode (requires sudo) |
| `--priority N` | Process priority (-20 to 19, negative = higher) |

### Other Options

| Option | Description |
|--------|-------------|
| `--test-pattern` | Run test pattern mode (no NDI) |
| `--list-sources` | List available NDI sources and exit |
| `--debug` | Enable debug logging |
| `--config FILE` | Load configuration from JSON file |
| `-v, --version` | Show version and exit |

## Configuration File

Create a `config.json` file for persistent settings:

```json
{
  "ndi": {
    "source_suffix": "_led",
    "scan_timeout": 2,
    "color_format": "bgra"
  },
  "display": {
    "resolution": "320x320",
    "fullscreen": false,
    "rotation": 180,
    "position": "center",
    "show_fps": false
  },
  "performance": {
    "cpu_performance_mode": true,
    "priority": -10
  }
}
```

Load configuration:
```bash
python3 ndi_receiver.py --config config.json
```

**Note**: Command line arguments override config file settings.

## Usage Examples

### Basic Usage

```bash
# Auto-detect source ending with '_led'
python3 ndi_receiver.py

# Connect to specific source
python3 ndi_receiver.py --source "MACBOOKAIR (catatumbo_led)"

# Different suffix for source detection
python3 ndi_receiver.py --source-suffix "_display"
```

### Display Configuration

```bash
# Full screen with FPS counter
python3 ndi_receiver.py --fullscreen --show-fps

# Different resolution and rotation
python3 ndi_receiver.py --resolution 640x480 --rotation 90

# Position in top-right corner
python3 ndi_receiver.py --position top-right
```

### Performance Tuning

```bash
# Maximum performance
python3 ndi_receiver.py --cpu-performance --priority -10

# Or use sudo to run with high priority
sudo python3 ndi_receiver.py --priority -10
```

### Testing

```bash
# List all NDI sources on network
python3 ndi_receiver.py --list-sources

# Run test patterns (no NDI required)
python3 ndi_receiver.py --test-pattern

# Debug mode for troubleshooting
python3 ndi_receiver.py --debug
```

### Studio Setup

```bash
# Recommended studio configuration
python3 ndi_receiver.py \
  --source-suffix "_led" \
  --resolution 320x320 \
  --rotation 180 \
  --position center \
  --cpu-performance
```

## Architecture

### Project Structure

```
led_test/
├── ndi_receiver.py              # Main CLI application
├── src/
│   ├── __init__.py
│   ├── ndi_handler.py          # NDI source management
│   ├── display_handler.py      # Display and rendering
│   ├── config.py               # Configuration management
│   ├── server_handler.py       # WebSocket (future)
│   └── test_patterns.py        # Test pattern mode
├── config.example.json          # Example configuration
├── led_test_pattern.py          # Original test patterns
├── ndi_receiver_native_display.py  # Legacy receiver (60 FPS)
└── docs/
```

### Module Overview

**`ndi_handler.py`**
- NDI source discovery
- Auto-detection with suffix matching
- Frame reception with configurable format
- Connection management

**`display_handler.py`**
- Pygame display initialization
- Frame rendering with rotation/positioning
- FPS tracking and display
- Event handling (ESC to exit)

**`config.py`**
- JSON configuration loading
- YAML support (optional, requires PyYAML)
- Hierarchical configuration merging

**`server_handler.py`**
- WebSocket communication (to be implemented)
- Command/control protocol
- Status reporting
- See [Future: Server Integration](#future-server-integration)

### Design Principles

1. **Modular**: Each component is independent and testable
2. **Extensible**: Easy to add new features (WebSocket, plugins, etc.)
3. **CLI-first**: All functionality accessible via command line
4. **Configuration**: Support both CLI args and config files
5. **Logging**: Comprehensive logging for debugging

## Future: Server Integration

The architecture supports future WebSocket server integration:

### Planned Features

- **Remote Control**: Change NDI source, resolution, rotation via WebSocket
- **Status Monitoring**: Real-time FPS, connection status, errors
- **Multi-device Management**: Control multiple LED receivers from one server
- **Configuration Sync**: Push config updates to all receivers

### Command Protocol (Draft)

**Commands from Server:**
```json
{"cmd": "set_source", "source": "name"}
{"cmd": "set_resolution", "width": 320, "height": 320}
{"cmd": "set_rotation", "angle": 180}
{"cmd": "reconnect"}
{"cmd": "shutdown"}
```

**Status Updates to Server:**
```json
{"type": "status", "fps": 60.0, "source": "name", "frames": 1000}
{"type": "heartbeat", "timestamp": 1234567890}
{"type": "error", "message": "Connection lost"}
```

### Implementation Notes

- Use `websockets` or `python-socketio` library
- Async event loop for non-blocking communication
- Thread-safe command queue for main loop
- Authentication via token
- Automatic reconnection with exponential backoff

## Logging

Logs are written to:
- **Console**: INFO and above
- **File**: `ndi_receiver.log` - all messages

Enable debug logging:
```bash
python3 ndi_receiver.py --debug
```

Log format:
```
2025-10-10 01:36:18,837 - ndi_receiver - INFO - LED Receiver v1.0.0 starting...
2025-10-10 01:36:19,032 - ndi_receiver.ndi - INFO - NDI initialized (format: bgra)
```

## Troubleshooting

### No NDI sources found
```bash
# List sources with debug info
python3 ndi_receiver.py --list-sources --debug

# Check network connectivity
ping <ndi-sender-ip>

# Verify NDI SDK is installed
ldconfig -p | grep ndi
```

### Display issues
```bash
# Try different video drivers
python3 ndi_receiver.py --video-driver kmsdrm
python3 ndi_receiver.py --video-driver directfb
python3 ndi_receiver.py --video-driver x11

# Run test patterns (no NDI)
python3 ndi_receiver.py --test-pattern
```

### Low FPS
```bash
# Enable performance mode
python3 ndi_receiver.py --cpu-performance

# Use BGRA format (fastest)
python3 ndi_receiver.py --color-format bgra

# Check actual source FPS
python3 ndi_receiver.py --show-fps --debug
```

### Permission denied
```bash
# Add user to video group
sudo usermod -a -G video $USER

# Then logout and login again
```

## Exit

Press **ESC** or **Ctrl+C** to exit the application gracefully.

---

**Version**: 1.0.0  
**Last Updated**: October 10, 2025  
**Performance**: 60 FPS with BGRA format


