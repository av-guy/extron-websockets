import os

from base64 import b64encode
from src.dev.ws_base import (WebSocket, Payload)


class BadRequest(Exception):
    pass


class WebSocketClient(WebSocket):
    def __init__(
        self,
        uri=""
    ):
        super().__init__()
        self.fragments = self._verify_uri(uri)
        self.CONNECTING = False
        self.protocols = []
        self.extensions = []
        self.custom = []

    def add_extension(self, extension):
        self.extensions.append(extension)

    def add_protocol(self, protocol):
        self.protocols.append(protocol)

    def add_custom(self, custom):
        self.custom.append(custom)

    def create_header(self, key, values):
        return '{0}: {1}'.format(key, ", ".join(
            values
        ))

    def create_client_handshake(self):
        self.key = self.generate_random_key().decode('utf-8')
        handshake = ''
        headers = [
            '{0} {1} HTTP/1.1'.format(self.method, self.path),
            'Host: {0}'.format(self.host),
            'Upgrade: {0}'.format(self.upgrade),
            'Connection: {0}'.format(self.connection),
            'Sec-WebSocket-Key: {0}'.format(self.key),
            'Sec-WebSocket-Version: {0}'.format(self.version)
        ]
        if len(self.protocols) >= 1:
            headers.append(self.create_header(
                'Sec-WebSocket-Protocols',
                self.protocols
                )
            )
        if len(self.extensions) >= 1:
            headers.append(self.create_header(
                'Sec-WebSocket-Extensions',
                self.extensions
                )
            )
        if len(self.custom) >= 1:
            for header in self.custom:
                headers.append(header)
        for header in headers:
            handshake += "{0}\r\n".format(header)
        handshake += '\r\n'
        return handshake

    def establish_connection(self):
        self.CONNECTING = True
        pass

    def generate_random_key(self, bytes=16):
        rand = b64encode(os.urandom(bytes))
        return rand

    def validate_connection(self, payload):
        connection = payload['Connection']
        if connection is not None:
            connection = connection.lower()
        if connection != 'upgrade':
            self.CONNECTING = False
            raise ValueError('Connection does not match \'Upgrade\'')

    def validate_extensions(self, payload):
        extensions = payload['Sec-WebSocket-Extensions']
        if extensions is not None:
            extensions = [
                extension.strip().lower() for extension in
                extensions.split(",")
            ]
            for extension in extensions:
                if extension not in self.extensions:
                    self.CONNECTING = False
                    raise ValueError(
                        'Unexpected extension encountered: {0}'.format(
                            extension
                        )
                    )

    def validate_key(self, payload):
        _hash = payload['Sec-WebSocket-Accept']
        hash = self._create_hash(self.key)
        if _hash != hash:
            raise ValueError('Hash invalid')

    def validate_status(self, payload):
        status = payload['status'][0]
        if '101' not in status:
            self.CONNECTING = False
            raise BadRequest(status)

    def validate_upgrade(self, payload):
        upgrade = payload['Upgrade']
        if upgrade is not None:
            upgrade = upgrade.lower()
        if upgrade != 'websocket':
            self.CONNECTING = False
            raise ValueError('Upgrade value does not match \'websocket\'')

    def validate_response(self, response):
        response = response.decode('utf-8').strip().split('\r\n')
        payload = Payload.server(response)
        self.validate_status(payload)
        self.validate_upgrade(payload)
        self.validate_connection(payload)
        self.validate_key(payload)
        self.validate_extensions(payload)
