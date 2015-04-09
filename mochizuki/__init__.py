import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class IRCClientProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self._transport = transport

    def connection_lost(self, exc=None):
        logger.info("Connection lost!")

    def data_received(self, data):
        print(type(data))
        print(repr(data))


class Mochizuki(object):
    client_protocol_factory = IRCClientProtocol

    def __init__(self, host='127.0.0.1', port=6667):
        self.host = host
        self.port = port
        self._loop = asyncio.get_event_loop()
        self._server_coro = self._loop.create_server(self.client_protocol_factory, self.host, self.port)
        self._server = self._loop.run_until_complete(self._server_coro)

    def log_sockets(self):
        logger.info(repr(self._server.sockets))

    def run(self):
        self._loop.call_later(4, self.log_sockets)
        try:
            self._loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt. Stopping server.")

        # let the server clean up before closing everything
        self._server.close()
        self._loop.run_until_complete(self._server.wait_closed())
        self._loop.close()


if __name__ == "__main__":
    mochi = Mochizuki()
    mochi.run()
