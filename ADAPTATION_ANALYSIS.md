# NDINamedRouterExt Analysis - Feature Adaptation

## Overview
Analysis of NDINamedRouterExt.py from TouchDesigner to identify features adaptable to our Raspberry Pi NDI receiver.

## Current TouchDesigner Features

### 1. **Regex Pattern Matching** ✨ HIGHLY ADAPTABLE
```python
# Lines 57-76, 256-333
- Transforms patterns to handle plurals (projector/projectors)
- Case-insensitive regex matching
- Multiple output blocks with different regex patterns
- Keeps current source if it still matches pattern
```

**Adaptation for RPi:**
- Replace simple suffix matching with regex patterns
- Allow flexible source name matching (e.g., `.*_led`, `TouchDesigner.*`, etc.)
- Add pattern configuration to config.json
- Enable/disable case sensitivity

**Benefit:** Much more flexible than hardcoded `_led` suffix!

---

### 2. **WebSocket Communication** 🌐 VERY USEFUL
```python
# Lines 394-659 (WebHandler class)
- Real-time state broadcasting to web clients
- Bidirectional communication (control + monitoring)
- Actions: request_state, set_source, refresh_sources, save/recall config
- Automatic client management (add/remove)
- Ping/pong for connection health
```

**Adaptation for RPi:**
- Web interface to monitor/control receiver remotely
- Mobile-friendly dashboard showing:
  - Current connected source
  - Available sources
  - FPS/performance stats
  - Quick source switching
- Remote configuration changes
- Status monitoring from anywhere on network

**Benefit:** Remote control and monitoring! Perfect for installations.

---

### 3. **State Persistence** 💾 USEFUL
```python
# Lines 37-38, 133-148
- Save current configuration
- Auto-recall on startup
- StorageManager integration
```

**Adaptation for RPi:**
- Remember last connected source
- Auto-reconnect on restart
- Save/restore display settings
- Configuration profiles (studio, home, event, etc.)

**Benefit:** Seamless restarts, no manual reconfiguration!

---

### 4. **Source Appearance/Disappearance Callbacks** 📡 ALREADY IMPLEMENTED!
```python
# Lines 343-382
- onSourceAppeared: Update mapping when new source appears
- onSourceDisappeared: Clean up and remap when source dies
- Menu updates for available sources
```

**Current Status:** ✅ We already have similar functionality!
- Our auto-switching handles source appearance
- Smart fallback handles disappearance
- We track `previous_available_sources`

**Enhancement Opportunity:**
- Add callbacks/hooks for custom actions
- Trigger external scripts on source changes
- Log source availability history

---

### 5. **Multiple Output Management** 🔀 INTERESTING
```python
# Lines 79-131
- Multiple output blocks, each with own regex
- Independent source selection per output
- Resolution tracking per output
```

**Adaptation for RPi:**
Could support multiple virtual "outputs":
- Main display (LED screen)
- Recording to disk
- Re-streaming via NDI
- Preview on secondary display

**Benefit:** Multi-purpose receiver!

---

### 6. **Manual Refresh** 🔄 SIMPLE TO ADD
```python
# Lines 385-391
- Manual source refresh trigger
- Force update of source mapping
```

**Adaptation for RPi:**
- CLI command: `--refresh-sources`
- WebSocket action: "refresh_sources"
- Keyboard shortcut: F5

**Benefit:** User control when auto-discovery has issues.

---

## Recommended Adaptations (Priority Order)

### Priority 1: Regex Pattern Matching
**Effort:** Medium | **Value:** High

Add to `config.json`:
```json
{
  "ndi": {
    "source_pattern": ".*_led",
    "pattern_type": "regex",
    "case_sensitive": false,
    "enable_plural_handling": true
  }
}
```

Replace hardcoded `endswith('_led')` with regex matching.

---

### Priority 2: WebSocket Server
**Effort:** High | **Value:** Very High

Create `src/websocket_server.py`:
- WebSocket server using `websockets` library
- REST API for status queries
- Web dashboard (HTML/CSS/JS)
- Real-time updates using Socket.IO or raw WebSockets

Features:
- View current source, FPS, resolution
- Switch sources remotely
- Save/load configurations
- View logs
- Start/stop receiver

**Perfect for:** Studio installations, remote monitoring, mobile control

---

### Priority 3: Configuration Profiles
**Effort:** Low | **Value:** Medium

Add profile management:
```bash
# Save current state as profile
python3 ndi_receiver.py --save-profile studio

# Load profile
python3 ndi_receiver.py --load-profile studio

# List profiles
python3 ndi_receiver.py --list-profiles
```

Automatically save:
- Last connected source
- Display settings
- Performance settings

---

### Priority 4: Manual Refresh Command
**Effort:** Very Low | **Value:** Low

Add signal handler for SIGUSR1:
```bash
# Trigger source refresh without restart
kill -USR1 <pid>
```

Or keyboard shortcut when running with display.

---

### Priority 5: Source Change Hooks
**Effort:** Low | **Value:** Medium

Add callback system:
```json
{
  "hooks": {
    "on_source_connect": "/path/to/script.sh",
    "on_source_disconnect": "/path/to/script.sh",
    "on_source_change": "/path/to/script.sh"
  }
}
```

Pass source name, timestamp, etc. to scripts.

**Use cases:**
- Log to external system
- Trigger recording
- Update external displays
- Send notifications

---

## TouchDesigner-Specific Features (Not Applicable)

❌ **Multiple Output Blocks:** Too complex for single-display use case
❌ **StorageManager:** TouchDesigner-specific, use JSON/SQLite instead
❌ **CustomParHelper:** TouchDesigner parameter system
❌ **Menu Labels/Names:** GUI-specific, not needed for CLI

---

## Implementation Roadmap

### Phase 1: Enhanced Pattern Matching (1-2 hours)
- [ ] Add regex pattern support
- [ ] Replace `endswith()` with regex matching
- [ ] Add plural handling option
- [ ] Update config.json schema
- [ ] Update documentation

### Phase 2: WebSocket Server (4-6 hours)
- [ ] Install `websockets` library
- [ ] Create `src/websocket_server.py`
- [ ] Implement basic state broadcasting
- [ ] Add control actions (set_source, refresh, etc.)
- [ ] Create simple HTML dashboard
- [ ] Add authentication (optional)

### Phase 3: Profile Management (1-2 hours)
- [ ] Implement profile save/load
- [ ] Add CLI commands
- [ ] Auto-save last state
- [ ] Profile directory management

### Phase 4: Hooks System (1 hour)
- [ ] Implement callback mechanism
- [ ] Add config options
- [ ] Test with example scripts
- [ ] Document hook API

---

## Key Takeaways

✅ **Regex matching** would make source selection much more powerful
✅ **WebSocket server** would enable remote control/monitoring
✅ **Profile management** would improve UX for multi-environment setups
✅ **Hooks** would enable extensibility for custom workflows

The TouchDesigner code shows a mature approach to:
- Flexible source matching (regex vs hardcoded)
- Remote control (WebSocket API)
- State persistence (save/recall)
- Extensibility (callbacks, multiple outputs)

Our receiver could benefit greatly from these patterns!

