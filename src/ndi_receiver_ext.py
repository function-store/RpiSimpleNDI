"""
NDI Receiver Extension for Web Interface
Adapted from TouchDesigner NDINamedRouterExt.py

Provides WebSocket communication and state management for web-based control.
"""

import json
import time
import logging
from typing import Optional

logger = logging.getLogger('ndi_receiver.extension')


def debug(message):
    """Debug logging helper"""
    logger.debug(message)


class NDIReceiverExt:
    """Extension class for NDI Receiver - provides web interface integration"""
    
    def __init__(self, ndi_handler, display_handler=None, receiver_name="NDI Receiver"):
        """
        Initialize the extension
        
        Args:
            ndi_handler: NDIHandler instance
            display_handler: DisplayHandler instance (optional)
            receiver_name: Display name for this receiver (default: "NDI Receiver")
        """
        self.ndi_handler = ndi_handler
        self.display_handler = display_handler
        self.receiver_name = receiver_name
        
        # Cache for available sources (to avoid blocking on every state request)
        self._cached_sources = []
        self._last_source_scan = 0
        self._source_cache_timeout = 15.0  # Refresh sources every 15 seconds (background only)
        
        # Initialize the WebSocket handler
        self.webHandler = WebHandler(self)
        
        debug(f'NDI Receiver Extension initialized: "{receiver_name}"')
        debug(f'Current source: {self.ndi_handler.get_source_name()}')
    
    def _get_cached_sources(self):
        """Get available sources from cache or refresh if needed
        
        Returns:
            List of available NDI source names
        """
        current_time = time.time()
        
        # Refresh cache if expired
        if current_time - self._last_source_scan > self._source_cache_timeout:
            try:
                debug('Refreshing source cache...')
                self._cached_sources = self.ndi_handler.list_sources() if hasattr(self.ndi_handler, 'list_sources') else []
                self._last_source_scan = current_time
                debug(f'Source cache updated: {len(self._cached_sources)} sources')
            except Exception as e:
                debug(f'Error refreshing source cache: {e}')
                logger.error(f'Error refreshing source cache: {e}')
        
        return self._cached_sources
    
    def getCurrentState(self):
        """Get current state for WebSocket communication
        
        Returns current receiver state including sources, connection status, etc.
        Adapted from NDINamedRouterExt.getCurrentState()
        """
        try:
            # Get all available sources (from cache to avoid blocking)
            sources = self._get_cached_sources()
            
            # Get current source
            current_source = self.ndi_handler.get_source_name()
            
            # Check connection status
            connected = current_source is not None and self.ndi_handler.ndi_recv is not None
            
            # Get FPS if display handler available
            fps = 0.0
            if self.display_handler and hasattr(self.display_handler, 'fps'):
                fps = self.display_handler.fps
            
            # Get resolution if available
            resolution = [0, 0]
            if self.display_handler and hasattr(self.display_handler, 'screen'):
                if self.display_handler.screen:
                    resolution = [
                        self.display_handler.screen.get_width(),
                        self.display_handler.screen.get_height()
                    ]
            
            # Build state dict
            # Note: We adapt to TouchDesigner's web UI format which expects arrays for multiple blocks
            # Since we're a single receiver, we create arrays with one element
            state = {
                'sources': sources,
                'current_source': current_source or '',
                'connected': connected,
                'fps': fps,
                'resolution': resolution,
                'pattern': self.ndi_handler.source_pattern,
                'pattern_info': {
                    'pattern': self.ndi_handler.source_pattern,
                    'case_sensitive': self.ndi_handler.case_sensitive,
                    'plural_handling': self.ndi_handler.enable_plural_handling
                },
                'auto_switch_enabled': self.ndi_handler.auto_switch,
                'last_update': time.time(),
                # TouchDesigner web UI compatibility: expects arrays for multiple blocks
                'output_names': [self.receiver_name],
                'regex_patterns': [self.ndi_handler.source_pattern or '.*'],
                'current_sources': [current_source or ''],
                'output_resolutions': [resolution],
                'output_sources': {
                    self.receiver_name: current_source or ''
                }
            }
            
            debug(f'Current state: {len(sources)} sources, connected={connected}, current={current_source}')
            return state
            
        except Exception as e:
            debug(f'Error getting current state: {e}')
            logger.error(f'Error getting current state: {e}')
            return {
                'sources': [],
                'current_source': '',
                'connected': False,
                'error': str(e),
                'last_update': time.time(),
                'output_names': [self.receiver_name],
                'regex_patterns': ['.*'],
                'current_sources': [''],
                'output_resolutions': [[0, 0]],
                'output_sources': {self.receiver_name: ''}
            }
    
    def handleSetSource(self, source_name):
        """Handle source selection from web interface
        
        Args:
            source_name: Name of the NDI source to connect to
            
        Returns:
            True if successful, False otherwise
            
        Adapted from NDINamedRouterExt.handleSetSource()
        """
        try:
            debug(f'Set source request: {source_name}')
            logger.info(f'Web interface requesting source change to: {source_name}')
            
            # Disconnect current source
            if self.ndi_handler.ndi_recv:
                self.ndi_handler.ndi_lib.NDIlib_recv_destroy(self.ndi_handler.ndi_recv)
                self.ndi_handler.ndi_recv = None
            
            # Find the source
            from ctypes import c_uint32, byref
            num_sources = c_uint32(0)
            sources_ptr = self.ndi_handler.ndi_lib.NDIlib_find_get_current_sources(
                self.ndi_handler.ndi_find, 
                byref(num_sources)
            )
            
            if num_sources.value == 0:
                logger.error('No NDI sources available')
                return False
            
            # Cast pointer to array
            from ctypes import cast, POINTER
            from src.ndi_handler import NDIlib_source_t
            sources = cast(sources_ptr, POINTER(NDIlib_source_t))
            
            # Find matching source
            target_source = None
            for i in range(num_sources.value):
                source = sources[i]
                name = source.p_ndi_name.decode('utf-8') if source.p_ndi_name else ""
                if name == source_name:
                    target_source = source
                    break
            
            if not target_source:
                logger.error(f'Source not found: {source_name}')
                return False
            
            # Connect to new source
            from src.ndi_handler import NDIlib_recv_create_v3_t
            
            recv_settings = NDIlib_recv_create_v3_t()
            recv_settings.source_to_connect_to = target_source
            recv_settings.color_format = self.ndi_handler.color_format
            recv_settings.bandwidth = 100
            recv_settings.allow_video_fields = False
            recv_settings.p_ndi_recv_name = b"NDI Receiver"
            
            self.ndi_handler.ndi_recv = self.ndi_handler.ndi_lib.NDIlib_recv_create_v3(byref(recv_settings))
            
            if self.ndi_handler.ndi_recv:
                # Update connected source
                old_source = self.ndi_handler.connected_source
                self.ndi_handler.connected_source = source_name
                
                # Set manual override flag to prevent auto-switching away from this source
                self.ndi_handler.manual_override = True
                logger.info(f'✓ Switched from "{old_source}" to "{source_name}" via web interface (manual override enabled)')
                
                # Broadcast the change to all connected clients
                if hasattr(self, 'webHandler'):
                    self.webHandler.broadcastSourceChange(source_name)
                
                return True
            else:
                logger.error(f'Failed to connect to source: {source_name}')
                return False
                
        except Exception as e:
            debug(f'Error setting source: {e}')
            logger.error(f'Error setting source: {e}')
            return False
    
    def handleRefreshSources(self):
        """Handle refresh sources request from web interface
        
        Returns:
            True if successful, False otherwise
            
        Adapted from NDINamedRouterExt.handleRefreshSources()
        """
        try:
            debug('Refreshing sources from web interface')
            logger.info('Web interface requesting source refresh')
            
            # Force a source list refresh by invalidating cache
            self._last_source_scan = 0  # Force cache refresh
            sources = self._get_cached_sources()
            logger.info(f'Refreshed sources: found {len(sources)} sources')
            
            # Broadcast updated state
            if hasattr(self, 'webHandler'):
                self.webHandler.broadcastStateUpdate()
            
            return True
            
        except Exception as e:
            debug(f'Error refreshing sources: {e}')
            logger.error(f'Error refreshing sources: {e}')
            return False


class WebHandler:
    """Handler class for WebSocket communication with web clients
    
    Adapted from NDINamedRouterExt.WebHandler
    """
    
    def __init__(self, extension):
        self.extension = extension
        self.webServerDAT = None  # Will be set by the WebSocket server
        self.connected_clients = set()  # Track connected clients
        debug('WebHandler initialized')
    
    def setWebServer(self, webserver):
        """Set the WebSocket server instance"""
        self.webServerDAT = webserver
        debug(f'WebSocket server connected')
    
    def addClient(self, client):
        """Add a client to the connected clients set"""
        self.connected_clients.add(client)
        debug(f'Client added. Total clients: {len(self.connected_clients)}')
        logger.info(f'Web client connected (total: {len(self.connected_clients)})')
    
    def removeClient(self, client):
        """Remove a client from the connected clients set"""
        self.connected_clients.discard(client)
        debug(f'Client removed. Total clients: {len(self.connected_clients)}')
        logger.info(f'Web client disconnected (remaining: {len(self.connected_clients)})')
    
    def broadcastToAll(self, message):
        """Send message to all connected clients"""
        if not self.webServerDAT:
            debug('No WebSocket server available for broadcasting')
            return
        
        # Send to all clients
        clients_to_remove = []
        for client in list(self.connected_clients):
            try:
                self.webServerDAT.send_message(client, message)
            except Exception as e:
                debug(f'Failed to send to client {client}: {e}')
                clients_to_remove.append(client)
        
        # Clean up invalid clients
        for client in clients_to_remove:
            self.connected_clients.discard(client)
        
        debug(f'Message sent to {len(self.connected_clients)} clients')
    
    def broadcastStateUpdate(self):
        """Broadcast current state to all connected WebSocket clients
        
        Adapted from NDINamedRouterExt.WebHandler.broadcastStateUpdate()
        """
        if not self.connected_clients:
            debug('No connected clients to broadcast to')
            return
        
        debug('Broadcasting state update to all connected clients')
        
        if self.extension:
            state = self.extension.getCurrentState()
            debug(f'Current state for broadcast: {len(state)} keys')
            response = {
                'action': 'state_update',
                'state': state
            }
            message = json.dumps(response)
            self.broadcastToAll(message)
            debug('State broadcast completed')
        else:
            debug('WARNING: Extension not found for broadcast')
    
    def broadcastSourceChange(self, source_name):
        """Broadcast source change to all connected WebSocket clients
        
        Args:
            source_name: Name of the new source
            
        Adapted from NDINamedRouterExt.WebHandler.broadcastSourceChange()
        """
        if not self.connected_clients:
            debug('No connected clients to broadcast to')
            return
        
        debug(f'Broadcasting source change: {source_name}')
        
        response = {
            'action': 'source_changed',
            'source_name': source_name
        }
        message = json.dumps(response)
        self.broadcastToAll(message)
        debug('Source change broadcast completed')
    
    def sendInitialState(self, client):
        """Send initial state to a newly connected client
        
        Args:
            client: WebSocket client identifier
            
        Adapted from NDINamedRouterExt.WebHandler.sendInitialState()
        """
        debug('Sending initial state to newly connected client')
        
        if not self.webServerDAT:
            debug('No WebSocket server available')
            return
        
        if self.extension:
            debug('Extension found, getting current state...')
            state = self.extension.getCurrentState()
            debug(f'Current state retrieved: {len(state)} keys')
            response = {
                'action': 'state_update',
                'state': state
            }
            message = json.dumps(response)
            try:
                self.webServerDAT.send_message(client, message)
                debug('Initial state sent to connected client')
            except Exception as e:
                debug(f'Error sending initial state: {e}')
        else:
            debug('WARNING: Extension not found, cannot send initial state')
    
    def handleMessage(self, client, message):
        """Handle incoming WebSocket messages
        
        Args:
            client: WebSocket client identifier
            message: JSON message string
            
        Adapted from NDINamedRouterExt.WebHandler.handleMessage()
        """
        try:
            data = json.loads(message)
            action = data.get('action')
            
            if not self.extension:
                debug('ERROR: Extension not found, sending error response')
                error_response = {
                    'action': 'error',
                    'message': 'NDI Receiver extension not found'
                }
                self.webServerDAT.send_message(client, json.dumps(error_response))
                return
            
            if action == 'request_state':
                debug('Processing request_state action')
                state = self.extension.getCurrentState()
                response = {
                    'action': 'state_update',
                    'state': state
                }
                self.webServerDAT.send_message(client, json.dumps(response))
                debug('State response sent successfully')
            
            elif action == 'set_source':
                debug('Processing set_source action')
                source_name = data.get('source_name')
                debug(f'Set source parameters: source_name={source_name}')
                
                if source_name is not None:
                    debug('Valid set_source parameters, calling extension handler')
                    success = self.extension.handleSetSource(source_name)
                    debug(f'Extension handleSetSource result: {success}')
                    
                    if success:
                        debug('Set source successful, getting updated state')
                        state = self.extension.getCurrentState()
                        response = {
                            'action': 'state_update',
                            'state': state
                        }
                        self.webServerDAT.send_message(client, json.dumps(response))
                        debug('Updated state sent successfully')
                    else:
                        debug('Set source failed, sending error response')
                        error_response = {
                            'action': 'error',
                            'message': f'Failed to set source: {source_name}'
                        }
                        self.webServerDAT.send_message(client, json.dumps(error_response))
                else:
                    debug('Invalid set_source parameters, sending error response')
                    error_response = {
                        'action': 'error',
                        'message': 'Invalid set_source parameters'
                    }
                    self.webServerDAT.send_message(client, json.dumps(error_response))
            
            elif action == 'refresh_sources':
                debug('Processing refresh_sources action')
                success = self.extension.handleRefreshSources()
                debug(f'Extension handleRefreshSources result: {success}')
                
                if success:
                    debug('Refresh sources successful, getting updated state')
                    state = self.extension.getCurrentState()
                    response = {
                        'action': 'state_update',
                        'state': state
                    }
                    self.webServerDAT.send_message(client, json.dumps(response))
                    debug('Refreshed state sent successfully')
                else:
                    debug('Refresh sources failed, sending error response')
                    error_response = {
                        'action': 'error',
                        'message': 'Failed to refresh sources'
                    }
                    self.webServerDAT.send_message(client, json.dumps(error_response))
            
            elif action == 'ping':
                pong_response = {
                    'action': 'pong',
                    'timestamp': time.time()
                }
                self.webServerDAT.send_message(client, json.dumps(pong_response))
            
            else:
                debug(f'Unknown action received: {action}')
                error_response = {
                    'action': 'error',
                    'message': f'Unknown action: {action}'
                }
                self.webServerDAT.send_message(client, json.dumps(error_response))
        
        except Exception as e:
            debug(f'Exception in handleMessage: {e}')
            logger.error(f'Exception in handleMessage: {e}')
            error_response = {
                'action': 'error',
                'message': f'Error processing message: {str(e)}'
            }
            try:
                self.webServerDAT.send_message(client, json.dumps(error_response))
            except:
                pass

