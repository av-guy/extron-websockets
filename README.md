# WebSocketServer And WebSocketClient

## In Progress

### Summary

An Extron based WebSocketServer and WebSocketClient per RFC 6455

> Create a pull request

> Write some tests

> Implement functionality

> Make sure tests pass

I really could use your help on this.

The Server class uses the Python select module and is intended ONLY for local
testing.

Please DO NOT have WebSocketServer or WebSocketClient handle their own
connections. These are meant to be public API's for the ServerInterface
and ClientInterface to use for speaking to each other ONLY.

> Current: https://tools.ietf.org/html/rfc6455#section-3

> Next: https://tools.ietf.org/html/rfc6455#section-4.1

- **[MIT license](http://opensource.org/licenses/mit-license.php)**
