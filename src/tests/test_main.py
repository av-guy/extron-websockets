from src.dev.ws_server import WebSocketServer
from src.dev.ws_client import WebSocketClient
from src.dev.ws_base import Payload
from src.dev.ws_client import BadRequest

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


def test_not_101():
    test_uri = 'ws://localhost:8080/chat'
    ws_client = WebSocketClient(test_uri)
    mock_response = '''{0}\r\n\r\n'''.format(
        'HTTP/1.1 400 Internal Server Error',
    )
    mock_response = mock_response.encode()
    ws_client = WebSocketClient(test_uri)
    ws_client.CONNECTING = True
    with pytest.raises(BadRequest):
        ws_client.validate_response(mock_response)
        assert ws_client.CONNECTING is not True


def test_bad_upgrade():
    test_uri = 'ws://localhost:8080/chat'
    ws_client = WebSocketClient(test_uri)
    mock_response = '''{0}\r\nUpgrade: {1}\r\n\r\n'''.format(
        'HTTP/1.1 101 Switching Protocols',
        'WebSacket'
    )
    mock_response = mock_response.encode()
    ws_client = WebSocketClient(test_uri)
    ws_client.CONNECTING = True
    with pytest.raises(ValueError):
        ws_client.validate_response(mock_response)
        assert ws_client.CONNECTING is not True


def test_bad_connection():
    test_uri = 'ws://localhost:8080/chat'
    ws_client = WebSocketClient(test_uri)
    mock_response = '''{0}\r\nUpgrade: {1}\r\nConnection: {2}\r\n\r\n'''.format(
        'HTTP/1.1 101 Switching Protocols',
        'websocket',
        'upgra'
    )
    mock_response = mock_response.encode()
    ws_client = WebSocketClient(test_uri)
    ws_client.CONNECTING = True
    with pytest.raises(ValueError):
        ws_client.validate_response(mock_response)
        assert ws_client.CONNECTING is not True


def test_incorrect_key():
    test_uri = "ws://localhost:8080/chat"
    ws_client = WebSocketClient(test_uri)
    ws_client.key = ws_client.generate_random_key().decode('utf-8')
    mock_response = '''{0}\r\nUpgrade: {1}\r\nConnection: {2}\r\nSec-WebSocket-Accept: {3}\r\n\r\n'''.format(
        'HTTP/1.1 101 Switching Protocols',
        'websocket',
        'UpGrADe',
        'bad_key'
    )
    mock_response = mock_response.encode()
    ws_client.CONNECTING = True
    with pytest.raises(ValueError):
        ws_client.validate_response(mock_response)


def test_bad_extension():
    test_uri = "ws://localhost:8080/chat"
    ws_client = WebSocketClient(test_uri)
    ws_client.key = ws_client.generate_random_key()
    mock_response = '''{0}\r\nUpgrade: {1}\r\nConnection: {2}\r\nSec-WebSocket-Accept: {3}\r\nSec-WebSocket-Extensions: {4}\r\n\r\n'''.format(
        'HTTP/1.1 101 Switching Protocols',
        'websocket',
        'UpGrADe',
        ws_client._create_hash(ws_client.key),
        'not, here'
    )
    mock_response = mock_response.encode()
    ws_client.CONNECTING = True
    with pytest.raises(ValueError):
        assert ws_client.CONNECTING is not False
        ws_client.validate_response(mock_response)


def test_good_extension():
    test_uri = "ws://localhost:8080/chat"
    ws_client = WebSocketClient(test_uri)
    ws_client.add_extension('not')
    ws_client.add_extension('here')
    ws_client.key = ws_client.generate_random_key()
    mock_response = '''{0}\r\nUpgrade: {1}\r\nConnection: {2}\r\nSec-WebSocket-Accept: {3}\r\nSec-WebSocket-Extensions: {4}\r\n\r\n'''.format(
        'HTTP/1.1 101 Switching Protocols',
        'websocket',
        'UpGrADe',
        ws_client._create_hash(ws_client.key),
        'not, here'
    )
    mock_response = mock_response.encode()
    ws_client.validate_response(mock_response)


def test_correct_response():
    assert True is False
