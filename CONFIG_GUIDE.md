# Configuration Guide

LED Receiver supports flexible configuration through JSON files, allowing you to define display and content settings independently.

## Quick Start

```bash
# Use LED screen configuration
python3 ndi_receiver.py --config config.led_screen.json

# Use adaptive configuration
python3 ndi_receiver.py --config config.adaptive.json

# Create custom config
cp config.example.json my_config.json
# Edit my_config.json
python3 ndi_receiver.py --config my_config.json
```

## Configuration Structure

### Display vs Content

The configuration distinguishes between:

- **Display**: The physical screen (e.g., 800x800 LED panel or 1920x1080 monitor)
- **Content**: The NDI video stream (e.g., 320x320 video)

This separation allows you to:
1. Handle LED screens with different physical/effective resolutions
2. Position content anywhere on the display
3. Scale content independently
4. Rotate content without affecting display

## Configuration Sections

### NDI Configuration

```json
"ndi": {
  "source_suffix": "_led",    // Auto-detect sources ending with this
  "scan_timeout": 2,           // Seconds to wait for discovery
  "color_format": "bgra"       // Format: bgra (fastest), uyvy, rgba
}
```

### Display Configuration

```json
"display": {
  "resolution": "800x800",   // Physical display resolution
                             // null = auto-detect
  "fullscreen": true,        // Run fullscreen
  "video_driver": "auto",    // SDL driver: auto, kmsdrm, x11, directfb
  "show_fps": false          // Show FPS counter
}
```

**Display Resolution Options:**
- `"800x800"` - Specific resolution
- `null` - Auto-detect (recommended for adaptive setups)

### Content Configuration

```json
"content": {
  "resolution": "320x320",   // Force content to this size
                             // null = use source resolution
  "position": "0,0",         // Position in pixels (x,y)
                             // or: "center", "top-left", etc.
                             // null = center
  "rotation": 180,           // Rotation in degrees (0, 90, 180, 270)
                             // null = 0
  "scaling": "fit"           // Scaling mode (see below)
}
```

**Position Options:**
- `"0,0"` - Top-left corner (x,y in pixels)
- `"100,50"` - Specific pixel position
- `"center"` - Center of display
- `"top-left"`, `"top-right"`, `"bottom-left"`, `"bottom-right"` - Named positions
- `null` - Auto-center

**Scaling Modes:** with `resolution` set, the content resolution is a box on the screen and every source is scaled into it, whatever size it arrives at; without it, the box is the whole display.
- `"fit"` - Whole frame, aspect ratio kept, centred with black bars (default)
- `"fill"` - Box covered, aspect ratio kept, centre cropped
- `"stretch"` - Box covered exactly, aspect ratio ignored
- `"none"` - Native size from the box corner, clipped to the box

**Rotation:**
- Rotates the content before positioning
- For 90° or 270°, width and height are swapped

### Hub Configuration (TDXMediaServe Integration)

```json
"bridge": {
  "enabled": false,              // Connect to a TDXMediaServe hub
  "url": null,                   // Hub URL (e.g., ws://studio-pi:8081)
  "component_id": null,          // Unique ID on the hub
                                 // null = auto-generated from hostname
  "component_name": "LED Wall"   // Human-readable name on the web page
                                 // null = uses "name" field
}
```

**Hub Mode:**
When connected to a TDXMediaServe hub (inside a TouchDesigner TDXMediaServe component, or `hub_server.py` on a Pi), this Raspberry Pi receiver appears on the TDXMediaServe web page alongside TouchDesigner outputs and other RPi receivers, grouped by its hostname. The section keeps the name `bridge` so existing configs keep working.

**Fields:**
- `enabled`: Set to `true` to connect to the hub (can be overridden with the `--hub-url` / `--bridge-url` CLI arg)
- `url`: WebSocket URL of the hub's one port (default: 8081)
- `component_id`: Unique identifier for this component. Stock Pis share the hostname `raspberrypi`, so set this (or a unique hostname) on each one
- `component_name`: Human-readable display name

**Configuration Priority:**
1. CLI arguments (`--hub-url` / `--bridge-url`, `--component-id`, `--component-name`)
2. Config file (`bridge` section)
3. Auto-generated defaults

**Default Values:**
- `component_id`: Auto-generated as `"RaspberryPi_<hostname>"`
- `component_name`: Uses the `"name"` field from config

**Example (Multi-RPi Setup with a Hub):**
```json
{
  "name": "LED Screen",
  "bridge": {
    "enabled": true,
    "url": "ws://192.168.1.100:8081",
    "component_id": "LED_Wall_Main",
    "component_name": "LED Wall - Stage Left"
  }
}
```

This connects to the hub at `192.168.1.100:8081` and appears in the interface as "LED Wall - Stage Left" with ID "LED_Wall_Main".

**Modes:**
- **Standalone**: `--web-server` (local web interface only)
- **Hub only**: `--hub-url ws://server:8081 --bridge-only` (no local web server)
- **Hybrid**: `--web-server --hub-url ws://server:8081` (both local and hub)

## Example Configurations

### 1. LED Screen (800x800 display, 320x320 content)

```json
{
  "description": "LED screen with specific content area",
  "display": {
    "resolution": "800x800",
    "fullscreen": true
  },
  "content": {
    "resolution": "320x320",
    "position": "0,0",
    "rotation": 180,
    "scaling": "none"
  }
}
```

**Use case**: LED panel that reports 800x800 but only has 320x320 active pixels in the corner, upside down.

### 2. Adaptive Fullscreen

```json
{
  "description": "Auto-detect everything",
  "display": {
    "resolution": null,
    "fullscreen": true
  },
  "content": {
    "resolution": null,
    "position": null,
    "rotation": 0,
    "scaling": "fit"
  }
}
```

**Use case**: Works on any display, scales NDI content to fit perfectly.

### 3. LCD Test Setup

```json
{
  "description": "Test on 1366x768 LCD",
  "display": {
    "resolution": "1366x768",
    "fullscreen": false
  },
  "content": {
    "resolution": null,
    "position": "center",
    "rotation": 0,
    "scaling": "fit"
  }
}
```

**Use case**: Testing on a laptop/monitor, scale content to fit.

### 4. Multiple Content Windows

```json
{
  "description": "Multiple small windows",
  "display": {
    "resolution": "1920x1080",
    "fullscreen": true
  },
  "content": {
    "resolution": "320x320",
    "position": "100,100",
    "rotation": 0,
    "scaling": "none"
  }
}
```

**Use case**: Display content at specific position (for multi-window setups in future).

### 5. Portrait Display

```json
{
  "description": "Portrait orientation",
  "display": {
    "resolution": "1080x1920",
    "fullscreen": true
  },
  "content": {
    "resolution": null,
    "position": "center",
    "rotation": 90,
    "scaling": "fit"
  }
}
```

**Use case**: Portrait display with rotated content.

## Configuration Precedence

Configuration sources in order of priority (highest to lowest):

1. Command line arguments
2. Configuration file
3. Default values

Example:
```bash
# Config file says rotation: 180, but CLI overrides to 0
python3 ndi_receiver.py --config config.json --rotation 0
```

## Common Scenarios

### Scenario 1: Your LED Screen Setup

**Problem**: LED panel shows as 800x800, but only 320x320 area is active at top-left, upside down.

**Solution**:
```json
{
  "display": {"resolution": "800x800", "fullscreen": true},
  "content": {
    "resolution": "320x320",
    "position": "0,0",
    "rotation": 180,
    "scaling": "none"
  }
}
```

**What it does**:
- Opens 800x800 display
- Receives NDI at native resolution
- Forces to 320x320 if different
- Positions at 0,0 (top-left)
- Rotates 180° to fix upside-down
- No scaling (pixel-perfect)

### Scenario 2: Testing at Home

**Problem**: Want to test on any display without manual configuration.

**Solution**:
```json
{
  "display": {"resolution": null, "fullscreen": true},
  "content": {
    "resolution": null,
    "position": null,
    "rotation": 0,
    "scaling": "fit"
  }
}
```

**What it does**:
- Auto-detects display size
- Uses NDI source resolution
- Centers content
- Scales to fit while maintaining aspect ratio

### Scenario 3: Different Rotation Per Location

**Studio** (`config.studio.json`):
```json
{"content": {"rotation": 180}}
```

**Home** (`config.home.json`):
```json
{"content": {"rotation": 0}}
```

Run:
```bash
# At studio
python3 ndi_receiver.py --config config.studio.json

# At home
python3 ndi_receiver.py --config config.home.json
```

## Validation

The application validates configurations:

- Display resolution must be `"WxH"` format or `null`
- Content resolution must be `"WxH"` format or `null`
- Position must be `"X,Y"` pixels or named position
- Rotation must be 0, 90, 180, or 270
- Scaling must be "none", "fit", "fill", or "stretch"

Invalid configurations will show an error and exit.

## Debugging

Enable debug logging to see configuration details:

```bash
python3 ndi_receiver.py --config config.json --debug
```

Look for log lines like:
```
Configuration: display=(800, 800), content_res=(320, 320), position=(0, 0), rotation=180°, scaling=none
```

## Tips

1. **Start with adaptive config** - Use `config.adaptive.json` first to verify everything works
2. **Test incrementally** - Add one setting at a time to isolate issues
3. **Use profiles** - Create different config files for different scenarios
4. **Log everything** - Use `--debug` when troubleshooting
5. **Pixel-perfect** - Use `scaling: "none"` when you want exact sizing

## Config File Locations

Recommended organization:

```
led_test/
├── config.adaptive.json      # Auto-detect everything
├── config.led_screen.json    # Your LED screen
├── config.studio.json        # Studio-specific
├── config.home.json          # Home-specific
└── config.example.json       # Template
```

Select with `--config`:
```bash
python3 ndi_receiver.py --config config.led_screen.json
```

---

**See Also**: 
- [CLI_GUIDE.md](CLI_GUIDE.md) - Command line options
- [STUDIO_SETUP.md](STUDIO_SETUP.md) - Studio setup guide





