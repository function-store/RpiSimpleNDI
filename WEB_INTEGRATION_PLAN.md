# Web Interface Integration Plan

## Goal
Reuse the TD_NDI_NamedRouter web interface and server for our Raspberry Pi NDI receiver with minimal changes.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Browser                             │
│                    (index.html)                             │
│                                                             │
│  - Modern UI with source selection                         │
│  - Real-time status updates                                │
│  - WebSocket client                                        │
└──────────────────┬──────────────────────────────────────────┘
                   │ WebSocket (port 8080)
                   │
┌──────────────────▼──────────────────────────────────────────┐
│              start_server.py                                │
│                                                             │
│  - Static HTTP server (templates/)                         │
│  - WebSocket server                                        │
│  - Forwards messages to NDIReceiverExt                     │
└──────────────────┬──────────────────────────────────────────┘
                   │ Python API
                   │
┌──────────────────▼──────────────────────────────────────────┐
│          src/ndi_receiver_ext.py                           │
│       (Adapted from NDINamedRouterExt.py)                  │
│                                                             │
│  - getCurrentState()                                       │
│  - handleSetSource()                                       │
│  - handleRefreshSources()                                  │
│  - broadcastStateUpdate()                                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│            ndi_receiver.py                                  │
│         (Main Application)                                  │
│                                                             │
│  Uses NDIHandler, DisplayHandler                           │
│  Now also creates NDIReceiverExt instance                  │
└─────────────────────────────────────────────────────────────┘
```

## Files to Create/Adapt

### 1. Copy Web Assets (NO CHANGES NEEDED)
```bash
# Copy the entire templates directory
cp -r ../namedrouter/TD_NDI_NamedRouter/templates ./

# Copy start_server.py
cp ../namedrouter/TD_NDI_NamedRouter/start_server.py ./
```

### 2. Create `src/ndi_receiver_ext.py`
Adapt NDINamedRouterExt.py to work with our NDI receiver:

**What to Keep:**
- WebHandler class (entire thing!)
- getCurrentState() pattern
- Message handling (request_state, set_source, etc.)
- Broadcast mechanisms

**What to Change:**
- Remove TouchDesigner-specific code (CustomParHelper, seqSwitch, etc.)
- Remove regex/plural handling (we'll add back later)
- Simplify to single source (not multiple outputs)
- Adapt to work with our NDIHandler

**New Structure:**
```python
class NDIReceiverExt:
    def __init__(self, ndi_handler, display_handler):
        self.ndi_handler = ndi_handler
        self.display_handler = display_handler
        self.webHandler = WebHandler(self)
    
    def getCurrentState(self):
        """Return current state for web interface"""
        return {
            'sources': self.ndi_handler.get_available_sources(),
            'current_source': self.ndi_handler.get_source_name(),
            'connected': self.ndi_handler.is_connected(),
            'fps': self.display_handler.get_fps(),
            'resolution': self.display_handler.get_resolution(),
            'last_update': time.time()
        }
    
    def handleSetSource(self, source_name):
        """Switch to a different source"""
        return self.ndi_handler.set_source(source_name)
    
    def handleRefreshSources(self):
        """Force refresh source list"""
        return self.ndi_handler.refresh_sources()
```

### 3. Adapt `start_server.py`
Minor changes:
- Update branding (NDI Receiver instead of NDI Router)
- WebSocket connects to Python backend instead of TouchDesigner
- Remove TouchDesigner-specific messaging

### 4. Update `index.html`
Minor UI changes:
- Single source selector (not multiple blocks)
- Add FPS display
- Add resolution display
- Remove multi-output UI elements
- Add "Raspberry Pi" branding

### 5. Integrate into `ndi_receiver.py`
```python
# Add web server option
parser.add_argument(
    '--web-server',
    action='store_true',
    help='Start web server for remote control'
)

# In main():
if args.web_server:
    from src.ndi_receiver_ext import NDIReceiverExt, start_web_server
    
    ext = NDIReceiverExt(ndi, display)
    start_web_server(ext, port=80, websocket_port=8080)
```

## Implementation Steps

### Phase 1: Basic Integration (2-3 hours)
1. ✅ Copy templates/ and start_server.py
2. ✅ Create src/ndi_receiver_ext.py with basic structure
3. ✅ Implement getCurrentState()
4. ✅ Test WebSocket connection
5. ✅ Verify state broadcasting

### Phase 2: Control Functions (1-2 hours)
1. Add handleSetSource() - manual source selection
2. Add handleRefreshSources() - force discovery
3. Test source switching from web UI
4. Add error handling

### Phase 3: UI Adaptation (1-2 hours)
1. Simplify index.html for single source
2. Add FPS/resolution display
3. Add connection health indicator
4. Update styling/branding

### Phase 4: Integration Testing (1 hour)
1. Test with actual NDI sources
2. Verify auto-switching still works
3. Test web control doesn't break auto-switching
4. Performance testing

## WebSocket Protocol (Already Defined!)

### Client → Server Messages:
```json
{"action": "request_state"}
{"action": "set_source", "source_name": "MACBOOK (output_led)"}
{"action": "refresh_sources"}
{"action": "ping"}
```

### Server → Client Messages:
```json
{
  "action": "state_update",
  "state": {
    "sources": ["source1", "source2"],
    "current_source": "source1",
    "connected": true,
    "fps": 60.0,
    "resolution": [1920, 1080],
    "last_update": 1234567890.123
  }
}

{
  "action": "source_changed",
  "source_name": "new_source"
}

{
  "action": "error",
  "message": "Error description"
}

{
  "action": "pong",
  "timestamp": 1234567890.123
}
```

## Benefits

✅ **Proven Architecture** - Already tested in TouchDesigner
✅ **Beautiful UI** - Modern, responsive design
✅ **No Dependencies** - Pure Python + vanilla JS
✅ **Real-time Updates** - WebSocket bidirectional communication
✅ **Mobile Friendly** - Works on phones/tablets
✅ **Zero Config** - Just run start_server.py

## Usage

```bash
# Terminal 1: Start NDI receiver with web server
python3 ndi_receiver.py --config config.led_screen.json --web-server

# Terminal 2 (or browser): Access web interface
# Opens automatically at http://localhost:80
# Or manually: http://[raspberry-pi-ip]:80

# Mobile device on same network:
# http://raspberrypi.local:80
```

