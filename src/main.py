import socket
import pprint
import select
import queue
import os
import re

from hashlib import sha1
from base64 import b64encode


pp = pprint.PrettyPrinter(indent=2)


class Router():
    routes = {
        'chat': True
    }


class WebSocket():
    def __init__(self):
        self.GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
        self.upgrade = 'websocket'
        self.connection = 'Upgrade'
        self.regex = r"(ws|wss)://|([a-zA-Z]*):?(\d*)?/?(\w*)?\??(.*)?"
        self.uri_format = "ws://host[:port]/path[?query]"
        self.method = 'GET'
        self.version = '13'

    def recieve(self, payload):
        pass

    def _assign_fragments(self, host, port, path, query):
        self.host = host
        self.port = port
        self.path = path
        self.query = query

    def _concatenate_key(self, key):
        return '{0}{1}'.format(key, self.GUID).encode('utf-8')

    def _create_hash(self, key):
        concatenation = self._concatenate_key(key)
        return b64encode(sha1(concatenation).digest()).decode('utf-8')

    def _split_uri(self, uri):
        secure, host, port, path, query, end = re.split(
            self.regex, uri
        )
        return (secure, host, port, path, query, end)

    def _verify_fragments(self, host, port, path, query):
        if len(host) <= 0:
            raise ValueError('Host cannot be blank')
        if len(port) > 0:
            host = '{0}:{1}'.format(host, port)
        path = '/{0}'.format(path)
        return (host, path)

    def _verify_uri(self, uri):
        if '#' in uri:
            raise ValueError('Fragment identifiers MUST NOT be used')
        match = re.search(self.regex, uri)
        if match.group() is not None:
            start, host, port, path, query, end = self._split_uri(uri)
            host, path = self._verify_fragments(host, port, path, query)
            self._assign_fragments(host, port, path, query)
        else:
            raise ValueError('''URI is not in correct format: {0}'''.format(
                self.uri_format
            ))


class WebSocketClient(WebSocket):
    def __init__(
        self,
        uri=""
    ):
        super().__init__()
        self.fragments = self._verify_uri(uri)

    def verify(self, uri):
        return True

    def generate_random_key(self, bytes=16):
        rand = b64encode(os.urandom(bytes))
        return rand

    def create_client_handshake(self):
        return '''{0} {1} HTTP/1.1\r\nHost: {2}\r\nUpgrade: {3}\r\nConnection: {4}\r\nSec-WebSocket-Key: {5}\r\nSec-WebSocket-Version: {6}\r\nUser-Agent: python\r\nPragma: no-cache\r\n Cache-Control: no-cache\r\n\r\n'''.format( # noqa
            self.method,
            self.path,
            self.host,
            self.upgrade,
            self.connection,
            self.generate_random_key().decode('utf-8'),
            self.version
        ).strip()


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


class Server(socket.socket):
    def __init__(self, port=8080):
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(('localhost', port))
        self.listen(5)
        self.setblocking(0)
        self.inputs = [self]
        self.outputs = []
        self.message_queues = {}

    def watch(self):
        while self.inputs:
            readable, writable, exceptional = select.select(
                self.inputs, self.outputs, self.inputs
            )
            self._readable(readable)
            self._writable(writable)
            self._exceptional(exceptional)

    def _handle_data(self, _socket):
        data = _socket.recv(1024)
        try:
            if data:
                data = data.decode('utf-8').strip()
                split = data.split('\r\n')
                payload = Payload.decode(split)
                print(payload)
                ws = Payload.validate_ws(payload)
                if ws:
                    web_socket_server = WebSocketServer()
                    web_socket_server.receive(payload)
                    res = web_socket_server.create_server_handshake()
                    self.message_queues[_socket].put(res)
                    if _socket not in self.outputs:
                        self.outputs.append(_socket)
        except Exception:
            message = 'Hello, World!'
            self.message_queues[_socket].put(message)
            if _socket not in self.outputs:
                self.outputs.append(_socket)

    def _handle_server(self, _socket):
        connection, address = _socket.accept()
        connection.setblocking(0)
        self.inputs.append(connection)
        self.message_queues[connection] = queue.Queue()

    def _readable(self, readable):
        for _socket in readable:
            if _socket is self:
                self._handle_server(_socket)
            else:
                self._handle_data(_socket)

    def _writable(self, writable):
        for _socket in writable:
            try:
                next_msg = self.message_queues[_socket].get_nowait()
            except queue.Empty:
                self.outputs.remove(_socket)
            else:
                _socket.send(next_msg.encode())

    def _exceptional(self, exceptional):
        for _socket in exceptional:
            print('exception condition on {0}'.format(_socket.getpeername()))
            self.inputs.remove(_socket)
            if _socket in self.outputs:
                self.outputs.remove(_socket)
            _socket.close()
            del self.message_queues[_socket]


class Payload():
    @staticmethod
    def decode(payload):
        payload_dict = {}
        for item in payload:
            item = item.split(': ')
            if 'HTTP/1.1' in item[0]:
                method, path, version = item[0].split(' ')
                payload_dict['method'] = [method, path, version]
            else:
                key, value = item
                payload_dict[key] = value
        return payload_dict

    @staticmethod
    def decode_server(payload):
        payload_dict = {}
        for item in payload:
            item = item.split(': ')
            if 'HTTP/1.1' in item[0]:
                payload_dict['method'] = item
            else:
                key, value = item
                payload_dict[key] = value
        return payload_dict

    @staticmethod
    def validate_ws(payload):
        try:
            upgrade = payload['Upgrade']
            connection = payload['Connection']
            if upgrade == 'websocket' and connection == 'Upgrade':
                return True
            else:
                return False
        except KeyError:
            return False


if __name__ == "__main__":
    server = Server()
    server.watch()
