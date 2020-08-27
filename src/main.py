import socket
import pprint
import select
import queue
import os


pp = pprint.PrettyPrinter(indent=2)


class Router():
    routes = {
        'chat': True
    }


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


if __name__ == "__main__":
    server = Server()
    server.watch()
