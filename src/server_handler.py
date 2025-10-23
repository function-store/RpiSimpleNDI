"""
Bridge Client Handler - WebSocket client for connecting to bridge server

This module handles connection to the NDI Named Router bridge server,
allowing the Raspberry Pi receiver to be controlled alongside TouchDesigner
instances through a unified web interface.

Protocol:
- Connects to bridge server as WebSocket client
- Sends initial state on connection
- Sends state updates when sources/locks change
- Receives commands from bridge (routed from web browsers)
- Executes commands locally (set_source, set_lock, etc.)
"""

import asyncio
import websockets
import json
import logging
import threading
import time
from typing import Optional

logger = logging.getLogger('ndi_receiver.bridge_client')


class BridgeClientHandler:
    """WebSocket client for connecting to bridge server"""
    
    def __init__(self, bridge_url: str, extension):
        """
        Initialize bridge client
        
        Args:
            bridge_url: WebSocket bridge URL (e.g., ws://server:8081)
            extension: NDIReceiverExt instance for state and commands
        """
        self.bridge_url = bridge_url
        self.extension = extension
        self.websocket = None
        self.connected = False
        self.running = False
        self.reconnect_delay = 5  # seconds
        self.thread = None
        self.loop = None
        
        logger.info(f"Bridge client initialized (URL: {bridge_url})")
    
    def start(self):
        """Start bridge client in background thread"""
        if self.running:
            logger.warning("Bridge client already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_client, daemon=True)
        self.thread.start()
        logger.info("Bridge client thread started")
    
    def stop(self):
        """Stop bridge client"""
        logger.info("Stopping bridge client...")
        self.running = False
        
        if self.loop and self.websocket:
            # Schedule close in the event loop
            asyncio.run_coroutine_threadsafe(self.websocket.close(), self.loop)
        
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info("Bridge client stopped")
    
    def _run_client(self):
        """Run client event loop (runs in separate thread)"""
        try:
            asyncio.run(self._client_loop())
        except Exception as e:
            logger.error(f"Bridge client error: {e}")
    
    async def _client_loop(self):
        """Main client loop with auto-reconnect"""
        self.loop = asyncio.get_running_loop()
        
        while self.running:
            try:
                logger.info(f"Connecting to bridge: {self.bridge_url}")
                async with websockets.connect(
                    self.bridge_url,
                    ping_interval=20,
                    ping_timeout=10
                ) as websocket:
                    self.websocket = websocket
                    self.connected = True
                    logger.info("Connected to bridge server")
                    
                    # Send initial state
                    await self._send_initial_state()
                    
                    # Handle messages
                    async for message in websocket:
                        await self._handle_message(message)
                        
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Bridge connection closed")
                self.connected = False
            except Exception as e:
                logger.error(f"Bridge connection error: {e}")
                self.connected = False
            
            # Reconnect after delay
            if self.running:
                logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
                await asyncio.sleep(self.reconnect_delay)
        
        self.connected = False
    
    async def _send_initial_state(self):
        """Send initial state to bridge on connection"""
        try:
            if not self.extension:
                logger.error("No extension available")
                return
            
            state = self.extension.getCurrentState()
            message = {
                'action': 'state_update',
                'state': state
            }
            await self.websocket.send(json.dumps(message))
            logger.info("Sent initial state to bridge")
        except Exception as e:
            logger.error(f"Failed to send initial state: {e}")
    
    async def _handle_message(self, message: str):
        """Handle incoming message from bridge
        
        Args:
            message: JSON message string
        """
        try:
            data = json.loads(message)
            action = data.get('action')
            
            logger.debug(f"Received from bridge: {action}")
            
            # Check if this message is for this specific component
            # Commands from the bridge should have component_id set
            message_component_id = data.get('component_id')
            if message_component_id and message_component_id != self.extension.component_id:
                # Message is for another component, ignore it
                logger.debug(f'Ignoring message for component {message_component_id} (we are {self.extension.component_id})')
                return
            
            # Handle commands by delegating to webHandler
            if hasattr(self.extension, 'webHandler'):
                # Process in main thread context (webHandler expects this)
                self.extension.webHandler.handleMessage(None, message)
            else:
                logger.error("No webHandler available to process bridge command")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from bridge: {e}")
        except Exception as e:
            logger.error(f"Error handling bridge message: {e}")
    
    def broadcast_state_update(self):
        """Send state update to bridge (called when state changes locally)"""
        if not self.connected or not self.websocket or not self.loop:
            return
        
        try:
            state = self.extension.getCurrentState()
            message = json.dumps({
                'action': 'state_update',
                'state': state
            })
            
            # Schedule send in event loop
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(message),
                self.loop
            )
            logger.debug("Sent state update to bridge")
        except Exception as e:
            logger.error(f"Failed to send state update to bridge: {e}")
    
    def broadcast_source_change(self, block_idx: int, source_name: str):
        """Send source change notification to bridge
        
        Args:
            block_idx: Output block index
            source_name: New source name
        """
        if not self.connected or not self.websocket or not self.loop:
            return
        
        try:
            message = json.dumps({
                'action': 'source_changed',
                'block_idx': block_idx,
                'source_name': source_name
            })
            
            # Schedule send in event loop
            asyncio.run_coroutine_threadsafe(
                self.websocket.send(message),
                self.loop
            )
            logger.debug(f"Sent source change to bridge: {source_name}")
        except Exception as e:
            logger.error(f"Failed to send source change to bridge: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to bridge
        
        Returns:
            bool: True if connected
        """
        return self.connected







