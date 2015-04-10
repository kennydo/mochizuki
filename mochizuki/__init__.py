import asyncio
import logging
import socket


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class IRCClientProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self._socket = transport.get_extra_info('socket')
        logger.info("Connection made to socket: %r", self._socket)

    def connection_lost(self, exc=None):
        logger.info("Connection lost to socket: %r", self._socket)

    def data_received(self, data):
        print(type(data))
        print(repr(data))
        try:
            self._socket.send(data)
        except socket.error:
            logger.exception("Unable to send data to socket %r", self._socket)


class Mochizuki(object):
    client_protocol_factory = IRCClientProtocol

    def __init__(self, host='127.0.0.1', port=6667):
        self.host = host
        self.port = port

        # handle the async magic
        self._loop = asyncio.get_event_loop()
        self._server_coro = self._loop.create_server(
            self.client_protocol_factory, self.host, self.port)
        self._server = self._loop.run_until_complete(self._server_coro)

    def run(self):
        try:
            self._loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt. Stopping server.")

        # let the server clean up before closing everything
        self._server.close()
        self._loop.run_until_complete(self._server.wait_closed())
        self._loop.close()
        logger.info("Server stopped.")


if __name__ == "__main__":
    mochi = Mochizuki()
    mochi.run()
