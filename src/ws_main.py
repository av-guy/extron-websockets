from main import WebSocketClient

if __name__ == "__main__":
    ws_client = WebSocketClient(path='chat', host='localhost', port=8080)
    ws_client.watch()
