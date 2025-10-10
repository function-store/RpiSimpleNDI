# Web Interface Integration Guide

## Overview

The NDI Receiver now includes a web interface for remote monitoring and control, adapted from the TouchDesigner NDINamedRouterExt architecture.

## Architecture

```
┌─────────────────────┐
│   Web Browser       │
│   (templates/)      │
│   - Modern UI       │
│   - Real-time       │
└──────┬──────────────┘
       │ WebSocket (8080)
       │ HTTP (80)
       ▼
┌─────────────────────┐
│  start_server.py    │
│  - HTTP Server      │
│  - Serves HTML/CSS  │
└─────────────────────┘
       
┌─────────────────────┐
│ websocket_server.py │
│  - WebSocket Server │
│  - Real-time msgs   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ ndi_receiver_ext.py │
│  - State management │
│  - Control handlers │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   ndi_receiver.py   │
│  - Main application │
│  - NDI + Display    │
└─────────────────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
pip3 install websockets
```

### 2. Start with Web Interface

```bash
python3 ndi_receiver.py --config config.led_screen.json --web-server
```

### 3. Access Web Interface

**Local access:**
```
http://localhost
```

**From another device on the network:**
```
http://[raspberry-pi-ip]
```

**Example:**
```
http://192.168.1.100
http://raspberrypi.local
```

## Features

### ✅ Real-Time Monitoring
- Current connected source
- Available NDI sources
- FPS (if enabled)
- Connection status
- Resolution
- Pattern configuration

### ✅ Remote Control
- Switch between sources
- Refresh source list
- View source history
- Connection health monitoring

### ✅ Auto-Updates
- State broadcasts every 10 seconds
- Instant source change notifications
- Connection status updates
- FPS monitoring

## WebSocket Protocol

The protocol is fully compatible with TouchDesigner's NDINamedRouter.

### Client → Server

**Request current state:**
```json
{"action": "request_state"}
```

**Change source:**
```json
{
  "action": "set_source",
  "source_name": "MACBOOK (output_led)"
}
```

**Refresh sources:**
```json
{"action": "refresh_sources"}
```

**Health check:**
```json
{"action": "ping"}
```

### Server → Client

**State update:**
```json
{
  "action": "state_update",
  "state": {
    "sources": ["MACBOOK (output_led)", "STUDIO (main_led)"],
    "current_source": "MACBOOK (output_led)",
    "connected": true,
    "fps": 60.0,
    "resolution": [1920, 1080],
    "pattern": ".*_led",
    "pattern_info": {
      "pattern": ".*_led",
      "case_sensitive": false,
      "plural_handling": false
    },
    "auto_switch_enabled": true,
    "last_update": 1699999999.123
  }
}
```

**Source changed:**
```json
{
  "action": "source_changed",
  "source_name": "STUDIO (main_led)"
}
```

**Error:**
```json
{
  "action": "error",
  "message": "Failed to connect to source"
}
```

**Pong response:**
```json
{
  "action": "pong",
  "timestamp": 1699999999.123
}
```

## Configuration

### Custom Ports

```bash
# Custom HTTP port
python3 ndi_receiver.py --web-server --web-port 8090

# Custom WebSocket port
python3 ndi_receiver.py --web-server --websocket-port 9000

# Both custom
python3 ndi_receiver.py --web-server --web-port 8090 --websocket-port 9000
```

### Config File

Add to your config.json:

```json
{
  "web": {
    "enabled": true,
    "http_port": 80,
    "websocket_port": 8080
  }
}
```

## Files

### Core Files (Adapted from TD_NDI_NamedRouter)

**`src/ndi_receiver_ext.py`**
- NDIReceiverExt class
- WebHandler class
- State management
- Message handling
- Adapted from `NDINamedRouterExt.py`

**`src/websocket_server.py`**
- WebSocket server implementation
- Client connection management
- Message routing

**`start_server.py`**
- HTTP server for web interface
- Serves templates/index.html
- Copied from TD_NDI_NamedRouter

**`templates/index.html`**
- Web interface UI
- Copied from TD_NDI_NamedRouter
- Will be adapted for single-source display

## Usage Examples

### Example 1: Studio Monitoring

```bash
# Start receiver with web interface
python3 ndi_receiver.py \
  --config config.led_screen.json \
  --web-server \
  --show-fps

# Access from phone/tablet
# http://raspberrypi.local
```

### Example 2: Remote Control

```bash
# Start headless with web interface
python3 ndi_receiver.py \
  --web-server \
  --no-display \
  --source-pattern ".*_led"

# Control from another computer
# http://192.168.1.100
```

### Example 3: Custom Ports

```bash
# Use non-privileged ports (no sudo)
python3 ndi_receiver.py \
  --web-server \
  --web-port 8080 \
  --websocket-port 8081
```

## Security Considerations

⚠️ **Important:**
- No authentication currently implemented
- Runs on all network interfaces (0.0.0.0)
- Anyone on network can access
- Suitable for trusted networks only

**Future enhancements:**
- Basic authentication
- API keys
- HTTPS support
- Access control lists

## Troubleshooting

### Port Already in Use

```bash
# Error: Port 80 is already in use
# Solution: Use custom port
python3 ndi_receiver.py --web-server --web-port 8080
```

### WebSocket Connection Failed

1. Check WebSocket port is open
2. Verify firewall settings
3. Check logs for errors
4. Try default ports (80, 8080)

### Can't Access from Network

1. Check Raspberry Pi IP: `hostname -I`
2. Verify same network
3. Check firewall: `sudo ufw status`
4. Try .local address: `raspberrypi.local`

## Performance

- **Minimal overhead**: WebSocket updates every 10s only
- **No impact on FPS**: Updates run in separate thread
- **Memory efficient**: Only broadcasts to active clients
- **Scalable**: Supports multiple simultaneous clients

## Next Steps

Planned enhancements:
1. Simplify UI for single source (remove multi-block layout)
2. Add FPS graph
3. Add source history log
4. Add configuration editor
5. Add authentication
6. Mobile-optimized layout

## Testing

```bash
# Test WebSocket connection
python3 -c "
import asyncio
import websockets
import json

async def test():
    uri = 'ws://localhost:8080'
    async with websockets.connect(uri) as websocket:
        # Request state
        await websocket.send(json.dumps({'action': 'request_state'}))
        response = await websocket.recv()
        print(json.dumps(json.loads(response), indent=2))

asyncio.run(test())
"
```

## Credits

Web interface architecture adapted from:
- **TD_NDI_NamedRouter** by Dan@DAN-4090
- WebSocket protocol compatible with TouchDesigner implementation
- UI templates reused from TouchDesigner project

