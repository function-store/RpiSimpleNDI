#!/usr/bin/env python3
"""A TDXMediaServe hub that runs without TouchDesigner.

Serves the TDXMediaServe web page and relays JSON between browsers and nodes
(TouchDesigner components and Raspberry Pi receivers), all on one port.
Browsers connect at /browser, nodes at any other path.

TouchDesigner hubs find it the same way they find each other: they ask the port
for /hub-id, and when a hub answers they connect to it instead of serving. Point
every TouchDesigner component's Network Address (or Url) and Port at this machine.

The relay follows the TouchDesigner hub's rules (protocol 2); a protocol change
there needs the same change here. The page is not part of this repository:
copy it into templates/hub.html with update_hub_page.py.
"""

import argparse
import asyncio
import json
import logging
import os
import re
import socket
import sys
import time
from http import HTTPStatus
from typing import Callable, Optional

try:
    # websockets >= 13
    from websockets.asyncio.server import serve as _serve
    from websockets.datastructures import Headers
    from websockets.http11 import Response
    _IS_NEW_API = True
except ImportError:
    # websockets 10 to 12
    from websockets import serve as _serve
    _IS_NEW_API = False

PROTOCOL_VERSION = 2
BROWSER_PATH = '/browser'
HUB_ID_PATH = '/hub-id'
IDENTITY_FIELDS = ('component_id', 'component_name', 'machine_id')
DEFAULT_PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'hub.html')

logger = logging.getLogger('tdxms_hub')


def nodeStateFrom(state: dict) -> dict:
    """A node's state in the current form. A client still sending flat routing fields is treated as a routing node."""
    if 'capabilities' in state:
        return state
    identity = {field: state[field] for field in IDENTITY_FIELDS if field in state}
    routing = {field: value for field, value in state.items() if field not in IDENTITY_FIELDS}
    return {**identity, 'capabilities': {'routing': routing}}


class NodeRelay:
    """Relays messages between browsers and nodes. Pure logic: the server owns the sockets and passes `send` in."""

    def __init__(self, send: Callable[[object, str], None]) -> None:
        self._send = send
        self.clients: dict = {}
        self.nodes: dict = {}

    def onOpen(self, client: object, path: str) -> None:
        role = 'browser' if path.startswith(BROWSER_PATH) else 'node'
        self.clients[client] = {'role': role, 'key': None, 'wantsUpdates': True}
        if role == 'browser':
            for node in self._nodeClients():
                self._send(node, json.dumps({'action': 'request_state'}))
            self._send(client, self.mergedStateMessage())

    def onClose(self, client: object) -> None:
        record = self.clients.pop(client, None)
        if record and record['key'] in self.nodes:
            del self.nodes[record['key']]
            self._sendToBrowsers(self.mergedStateMessage())

    def onText(self, client: object, text: str) -> None:
        record = self.clients.setdefault(client, {'role': 'node', 'key': None, 'wantsUpdates': True})
        try:
            message = json.loads(text)
        except ValueError:
            message = None
        if not isinstance(message, dict):
            message = {}
        if record['role'] == 'browser':
            self._handleBrowserMessage(client, text, message)
        else:
            self._handleNodeMessage(client, record, text, message)

    def _handleBrowserMessage(self, client: object, text: str, message: dict) -> None:
        if message.get('action') == 'error':
            return
        if message.get('component_id'):
            self._routeCommand(message, client)
            return
        nodes = self._nodeClients()
        if not nodes:
            self._send(client, json.dumps({'action': 'error', 'message': 'TouchDesigner not connected'}))
        for node in nodes:
            self._send(node, text)

    def _handleNodeMessage(self, client: object, record: dict, text: str, message: dict) -> None:
        action = message.get('action')
        if action == 'register_client':
            record['wantsUpdates'] = message.get('client_type', 'controller') != 'info' or message.get('auto_update', True)
            return
        if action == 'request_state':
            self._send(client, self.mergedStateMessage())
            return
        componentId = message.get('component_id')
        ownId = self.nodes.get(record['key'], {}).get('component_id')
        if componentId and componentId != ownId:
            self._routeCommand(message, client)
            return
        if action == 'state_update' and message.get('state', {}).get('component_id'):
            state = message['state']
            self.nodes[self._assignNodeKey(client, record, state['component_id'])] = nodeStateFrom(state)
            text = self.mergedStateMessage()
        elif componentId:
            # Browsers address nodes by hub key, which may differ from the node's own id
            message['component_id'] = record['key']
            text = json.dumps(message)
        self._sendToBrowsers(text)
        for other, otherRecord in self.clients.items():
            if other != client and otherRecord['role'] == 'node' and otherRecord['wantsUpdates']:
                self._send(other, text)

    def _routeCommand(self, message: dict, sender: object) -> None:
        """Deliver a command to the one node it names, telling the sender if that node is gone."""
        key = message['component_id']
        target = next((client for client, record in self.clients.items() if record['role'] == 'node' and record['key'] == key), None)
        if target is None:
            self._send(sender, json.dumps({'action': 'error', 'message': f'Component {key} not connected'}))
            return
        # The node only knows its own id, not a suffixed hub key
        message['component_id'] = self.nodes.get(key, {}).get('component_id', key)
        self._send(target, json.dumps(message))

    def _assignNodeKey(self, client: object, record: dict, nodeId: str) -> str:
        """Return this client's hub-unique key, suffixing an id another live client already holds."""
        current = record['key']
        if current and self.nodes.get(current, {}).get('component_id') == nodeId:
            return current
        if current:
            self.nodes.pop(current, None)
        taken = {other['key'] for peer, other in self.clients.items() if other['key'] and peer != client}
        key, suffix = nodeId, 2
        while key in taken:
            key, suffix = f'{nodeId}#{suffix}', suffix + 1
        if key != nodeId:
            logger.warning(f"Component id '{nodeId}' is already connected; listing this one as '{key}'. Give each component a unique Component ID.")
        record['key'] = key
        return key

    def _nodeClients(self) -> list:
        return [client for client, record in self.clients.items() if record['role'] == 'node']

    def _sendToBrowsers(self, text: str) -> None:
        for client, record in self.clients.items():
            if record['role'] == 'browser':
                self._send(client, text)

    def mergedStateMessage(self) -> str:
        """Every connected node under its hub key; readers interpret the capabilities they understand."""
        nodes = [{**state, 'component_id': key, 'component_name': state.get('component_name', key), 'machine_id': state.get('machine_id', 'unknown')}
            for key, state in self.nodes.items()]
        return json.dumps({'action': 'state_update', 'state': {'protocol': PROTOCOL_VERSION, 'last_update': time.time(), 'nodes': nodes}})


def lanAddress() -> str:
    """This machine's address on the network. Sends nothing."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(('8.8.8.8', 80))
            return probe.getsockname()[0]
    except OSError:
        return '127.0.0.1'


def pageSource(text: str) -> str:
    """The TDXMediaServe commit a page copy came from, as recorded by update_hub_page.py."""
    match = re.search(r'TDXMediaServe page copied from (\S+)', text)
    return match.group(1) if match else 'unknown source'


class HubServer:
    """Owns the sockets: serves the page and /hub-id over HTTP and feeds WebSocket traffic to the relay."""

    def __init__(self, pagePath: str) -> None:
        self.pagePath = pagePath
        self.hubId = f'python:{socket.gethostname()}:{os.getpid()}'
        self.relay = NodeRelay(self._enqueue)
        self._outboxes: dict = {}

    def _readPage(self) -> Optional[bytes]:
        # Read on every request so a refreshed page needs no restart
        try:
            with open(self.pagePath, 'rb') as file:
                return file.read()
        except OSError as e:
            logger.error(f'Cannot read the page {self.pagePath}: {e}')
            return None

    def httpResponse(self, path: str) -> tuple:
        """(status, content type, body) for a plain HTTP request."""
        route = path.split('?', 1)[0]
        if route in ('/', '/index.html'):
            page = self._readPage()
            if page is None:
                return HTTPStatus.INTERNAL_SERVER_ERROR, 'text/plain; charset=utf-8', b'The hub page is missing. Run update_hub_page.py.'
            return HTTPStatus.OK, 'text/html; charset=utf-8', page
        if route == HUB_ID_PATH:
            return HTTPStatus.OK, 'application/json', json.dumps({'hub': self.hubId}).encode()
        if route == '/favicon.ico':
            return HTTPStatus.NO_CONTENT, 'text/plain', b''
        return HTTPStatus.NOT_FOUND, 'text/plain; charset=utf-8', b'Not Found'

    def _enqueue(self, client: object, text: str) -> None:
        outbox = self._outboxes.get(client)
        if outbox is not None:
            outbox.put_nowait(text)

    async def _drain(self, client, outbox: asyncio.Queue) -> None:
        """Send one client's messages in order; a slow client never holds up the others."""
        while True:
            text = await outbox.get()
            try:
                await client.send(text)
            except Exception as e:
                logger.debug(f'Could not send to a client: {e}')
                return

    async def handleConnection(self, client, path: str) -> None:
        outbox = asyncio.Queue()
        self._outboxes[client] = outbox
        writer = asyncio.create_task(self._drain(client, outbox))
        self.relay.onOpen(client, path)
        role = self.relay.clients[client]['role']
        logger.info(f'{role} connected from {client.remote_address[0]} ({len(self.relay.clients)} connected)')
        try:
            async for text in client:
                if isinstance(text, str):
                    self.relay.onText(client, text)
        except Exception as e:
            logger.debug(f'Connection ended: {e}')
        finally:
            self.relay.onClose(client)
            self._outboxes.pop(client, None)
            writer.cancel()
            logger.info(f'{role} disconnected ({len(self.relay.clients)} connected)')


def isWebSocketRequest(headers) -> bool:
    return 'websocket' in headers.get('Upgrade', '').lower()


async def runHub(host: str, port: int, pagePath: str) -> None:
    hub = HubServer(pagePath)

    if _IS_NEW_API:
        async def handler(connection):
            await hub.handleConnection(connection, connection.request.path)

        def processRequest(connection, request):
            if isWebSocketRequest(request.headers):
                return None
            status, contentType, body = hub.httpResponse(request.path)
            headers = Headers([('Content-Type', contentType), ('Content-Length', str(len(body)))])
            return Response(status.value, status.phrase, headers, body)
    else:
        async def handler(websocket, path=None):
            await hub.handleConnection(websocket, path if path is not None else websocket.path)

        async def processRequest(path, requestHeaders):
            if isWebSocketRequest(requestHeaders):
                return None
            status, contentType, body = hub.httpResponse(path)
            return status, [('Content-Type', contentType), ('Content-Length', str(len(body)))], body

    page = hub._readPage()
    source = pageSource(page.decode('utf-8', 'replace')) if page else 'missing'
    async with _serve(handler, host, port, process_request=processRequest):
        logger.info(f'TDXMediaServe hub serving at http://{lanAddress()}:{port} (page: {source}, protocol {PROTOCOL_VERSION})')
        logger.info(f'Point TouchDesigner components and Raspberry Pi receivers at {lanAddress()}:{port}')
        await asyncio.Future()


def main() -> None:
    parser = argparse.ArgumentParser(description='TDXMediaServe hub without TouchDesigner: serves the web page and relays between nodes on one port.')
    parser.add_argument('--port', type=int, default=8081, help='The one port for the page, browsers and nodes (default: 8081, the TouchDesigner default)')
    parser.add_argument('--host', default='0.0.0.0', help='Address to listen on (default: all interfaces)')
    parser.add_argument('--page', default=DEFAULT_PAGE, help='The page to serve (default: templates/hub.html)')
    parser.add_argument('--debug', action='store_true', help='Log every connection detail')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    # websockets logs every open and close itself; the hub logs connections with their role
    logging.getLogger('websockets').setLevel(logging.DEBUG if args.debug else logging.WARNING)
    try:
        asyncio.run(runHub(args.host, args.port, args.page))
    except OSError as e:
        logger.error(f'Cannot serve on port {args.port}: {e}. Is another hub or program using it?')
        sys.exit(1)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
