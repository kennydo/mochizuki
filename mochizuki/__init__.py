import logging
import socket

import trollius


logger = logging.getLogger(__name__)


class Application(object):
    def __init__(self, irc_server_factory, host='127.0.0.1', port=6667):
        server_name = socket.getfqdn()
        self.irc_server = irc_server_factory(server_name)

        self.host = host
        self.port = port

        self.loop = trollius.get_event_loop()

        self._server_coro = self.loop.create_server(
            self.irc_server.get_client_protocol_factory(),
            self.host, self.port
        )
        self._server = self.loop.run_until_complete(self._server_coro)

    def run(self):
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt. Stopping server.")

        # let the server clean up before closing everything
        self._server.close()
        self.loop.run_until_complete(self._server.wait_closed())
        self.loop.close()
        logger.info("Server stopped.")
