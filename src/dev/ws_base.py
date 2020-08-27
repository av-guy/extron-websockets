import re

from hashlib import sha1
from base64 import b64encode


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
    def server(payload):
        payload_dict = {}
        for item in payload:
            item = item.split(': ')
            if 'HTTP/1.1' in item[0]:
                payload_dict['status'] = item
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


class WebSocket():
    def __init__(self):
        self.GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
        self.upgrade = 'websocket'
        self.connection = 'Upgrade'
        self.regex = r"(ws|wss)://([a-zA-Z]*):?(\d*)?/?(\w*)?\??(.*)?"
        self.uri_format = "ws://host[:port]/path[?query]"
        self.method = 'GET'
        self.version = '13'
        self.secure = False

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
        start, secure, host, port, path, query, end = re.split(
            self.regex, uri
        )
        return (secure, host, port, path, query)

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
            secure, host, port, path, query = self._split_uri(uri)
            if secure == 'wss':
                self.secure = True
            host, path = self._verify_fragments(host, port, path, query)
            self._assign_fragments(host, port, path, query)
        else:
            raise ValueError('''URI is not in correct format: {0}'''.format(
                self.uri_format
            ))
