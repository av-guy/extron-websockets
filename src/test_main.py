from main import WebSocketServer
from main import WebSocketClient
from main import Server
from main import Payload

import pprint
import pytest

pp = pprint.PrettyPrinter(indent=2)


def test_concat_hash():
    ws_server = WebSocketServer()
    hash = ws_server._create_hash('dGhlIHNhbXBsZSBub25jZQ==')
    expected = "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="
    assert hash == expected


def test_uri_verify_and_handshake():
    test_uri = "ws://localhost:8080/chat"
    ws_client = WebSocketClient(test_uri)
    handshake = ws_client.create_client_handshake().strip().split('\r\n')
    payload = Payload.decode(handshake)
    assert payload['Connection'] == 'Upgrade'
    assert payload['Host'] == 'localhost:8080'
    assert payload['Sec-WebSocket-Version'] == '13'
    assert payload['Upgrade'] == 'websocket'
    assert payload['method'][0] == 'GET'
    assert payload['method'][1] == '/chat'
    assert payload['method'][2] == 'HTTP/1.1'


def test_uri_path_replacement():
    test_uri = "ws://localhost/"
    ws_client = WebSocketClient(test_uri)
    handshake = ws_client.create_client_handshake().strip().split('\r\n')
    payload = Payload.decode(handshake)
    assert payload['Host'] == 'localhost'
    assert payload['method'][0] == 'GET'
    assert payload['method'][1] == '/'
    assert payload['method'][2] == 'HTTP/1.1'


def test_uri_no_host():
    test_uri = "ws://:9090/"
    with pytest.raises(ValueError):
        WebSocketClient(test_uri)


def test_fragment_identifier():
    test_uri = "ws://localhost:9090#cats"
    with pytest.raises(ValueError):
        WebSocketClient(test_uri)


def test_add_protocols():
    test_uri = 'ws://localhost:8080/chat'
    ws_client = WebSocketClient(test_uri)
    ws_client.add_protocol('cats')
    ws_client.add_protocol('meow')
    handshake = ws_client.create_client_handshake().strip().split('\r\n')
    payload = Payload.decode(handshake)
    assert payload['Sec-WebSocket-Protocols'] == 'cats, meow'


def test_add_extension():
    test_uri = 'ws://localhost:8080/chat'
    ws_client = WebSocketClient(test_uri)
    ws_client.add_extension('cats')
    ws_client.add_extension('meow')
    handshake = ws_client.create_client_handshake().strip().split('\r\n')
    payload = Payload.decode(handshake)
    assert payload['Sec-WebSocket-Extensions'] == 'cats, meow'


def test_add_custom():
    test_uri = 'ws://localhost:8080/chat'
    ws_client = WebSocketClient(test_uri)
    ws_client.add_custom('Authorization: Basic YWxhZGRpbjpvcGVuc2VzYW1l')
    handshake = ws_client.create_client_handshake().strip().split('\r\n')
    payload = Payload.decode(handshake)
    assert payload['Authorization'] == 'Basic YWxhZGRpbjpvcGVuc2VzYW1l'
