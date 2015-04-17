import logging
import socket
import trollius

logger = logging.getLogger(__name__)


class IRCClientProtocol(trollius.Protocol):
    def __init__(self, irc_server=None):
        """

        :param irc_server: a :class:`IRCServer` instance
        """

        self.irc_server = irc_server

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


class IRCServer(object):
    def __init__(self, host='127.0.0.1', port=6667):
        """

        :param str host: the host to listen on
        :param int port: a port number between 0 and 65535 to listen on
        :return:
        """

        self.host = host
        self.port = port

        #: Maps `str` nicknames to :class:`users.IRCUser` objects
        self.users = {}

        #: Maps `str` channel names to :class:`channels.IRCChannel` objects
        self.channels = {}

    def get_client_protocol_factory(self):
        """Return the factory for the :class:`Protocol` instances that gets called
        when a new connection to this server is initiated.

        :return: a :class:`Protocol` that gets instantiated
        """
        return IRCClientProtocol
