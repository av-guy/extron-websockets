from src.dev.ws_base import WebSocket


class WebSocketServer(WebSocket):
    def __init__(self):
        super().__init__()
        self.header = 'HTTP/1.1 101 Switching Protocols'
        self.hash = None

    def create_server_handshake(self):
        return '''{0}\r\nUpgrade: {1}\r\nConnection: {2}\r\nSec-WebSocket-Accept: {3}\r\n\r\n'''.format( # noqa
            self.header,
            self.upgrade,
            self.connection,
            self.hash
        )

    def receive(self, payload):
        sec_websocket_key = payload['Sec-WebSocket-Key']
        hash = self._create_hash(sec_websocket_key)
        self.hash = hash
