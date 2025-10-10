"""
WebSocket Server for NDI Receiver Web Interface
Provides real-time communication between web browser and NDI receiver

Adapted to work with the TouchDesigner web interface protocol
"""

import asyncio
import websockets
import json
import logging
from typing import Set, Optional

logger = logging.getLogger('ndi_receiver.websocket')


class WebSocketServer:
    """WebSocket server for real-time web interface communication"""
    
    def __init__(self, extension, port: int = 8080):
        """
        Initialize WebSocket server
        
        Args:
            extension: NDIReceiverExt instance
            port: WebSocket port (default: 8080)
        """
        self.extension = extension
        self.port = port
        self.clients: Set = set()
        self.server = None
        self.loop = None  # Will be set when server starts
        
        # Connect this server to the extension's WebHandler
        if hasattr(extension, 'webHandler'):
            extension.webHandler.setWebServer(self)
        
        logger.info(f'WebSocket server initialized on port {port}')
    
    def send_message(self, client, message: str):
        """Send message to a specific client
        
        Args:
            client: WebSocket client connection
            message: JSON message string
        """
        if not self.loop:
            logger.error('Event loop not available')
            return
            
        try:
            # Schedule the coroutine in the event loop from another thread
            asyncio.run_coroutine_threadsafe(client.send(message), self.loop)
        except Exception as e:
            logger.error(f'Error sending message to client: {e}')
    
    async def handler(self, websocket):
        """Handle WebSocket connections
        
        Args:
            websocket: WebSocket connection
        """
        client_id = id(websocket)
        logger.info(f'New WebSocket connection from {websocket.remote_address}')
        
        # Add client
        self.clients.add(websocket)
        if hasattr(self.extension, 'webHandler'):
            self.extension.webHandler.addClient(websocket)
        
        try:
            # Send initial state
            if hasattr(self.extension, 'webHandler'):
                self.extension.webHandler.sendInitialState(websocket)
            
            # Handle messages
            async for message in websocket:
                logger.debug(f'Received message from {websocket.remote_address}: {message[:100]}...')
                
                # Handle message through extension
                if hasattr(self.extension, 'webHandler'):
                    self.extension.webHandler.handleMessage(websocket, message)
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f'WebSocket connection closed: {websocket.remote_address}')
        
        except Exception as e:
            logger.error(f'Error in WebSocket handler: {e}')
        
        finally:
            # Remove client
            self.clients.discard(websocket)
            if hasattr(self.extension, 'webHandler'):
                self.extension.webHandler.removeClient(websocket)
            logger.info(f'Client disconnected (remaining: {len(self.clients)})')
    
    async def start(self):
        """Start the WebSocket server"""
        try:
            # Store the event loop for cross-thread communication
            self.loop = asyncio.get_running_loop()
            
            self.server = await websockets.serve(
                self.handler,
                "0.0.0.0",  # Listen on all interfaces
                self.port,
                ping_interval=20,
                ping_timeout=10
            )
            logger.info(f'WebSocket server started on ws://0.0.0.0:{self.port}')
            logger.info(f'Web interface will connect to this port')
            
            # Keep server running
            await asyncio.Future()  # Run forever
            
        except Exception as e:
            logger.error(f'Error starting WebSocket server: {e}')
            raise
    
    async def stop(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info('WebSocket server stopped')
    
    def run(self):
        """Run the WebSocket server (blocking)"""
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            logger.info('WebSocket server interrupted')
        except Exception as e:
            logger.error(f'WebSocket server error: {e}')


def start_websocket_server(extension, port: int = 8080):
    """Start WebSocket server in a separate thread
    
    Args:
        extension: NDIReceiverExt instance
        port: WebSocket port (default: 8080)
    
    Returns:
        WebSocketServer instance
    """
    import threading
    
    server = WebSocketServer(extension, port)
    
    # Run in separate thread
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    
    logger.info(f'WebSocket server thread started')
    
    return server

