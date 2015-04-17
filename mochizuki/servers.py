import logging
import socket
import trollius
from functools import partial

logger = logging.getLogger(__name__)


class IRCClientProtocol(trollius.Protocol):
    def __init__(self, irc_server):
        """

        :param irc_server: a :class:`IRCServer` instance
        """

        self.irc_server = irc_server
        self.socket = None

    def connection_made(self, transport):
        self.socket = transport.get_extra_info('socket')
        logger.info("self.irc_server: %r", self.irc_server)
        logger.info("Connection made to socket: %r", self.socket)

    def connection_lost(self, exc=None):
        logger.info("Connection lost to socket: %r", self.socket)

    def data_received(self, data):
        """The callback for every line of data received from this client.

        :param data: str or bytestring, depending on Python version
        """
        # Decode the data to unicode and then pass on to the server to handle.
        # TODO(kennydo) handle non-utf8 data
        try:
            unicode_data = data.decode('utf8')
        except UnicodeDecodeError:
            unicode_data = None
            logger.exception(
                'Could not decode data received from user: %r', data)

        if unicode_data:
            self.irc_server.handle(self.socket, unicode_data)


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
        """Return the factory for the :class:`Protocol` instances that will be
        created by the event loop whenever a new client connects.

        :return: a :class:`Protocol` that gets instantiated
        """
        return partial(IRCClientProtocol, irc_server=self)

    def handle(self, client_socket, message):
        """

        :param client_socket: the :class:`socket.socket` to the client
        :param unicode message: the message that the client sent
        :return:
        """

        # Normal messages end in "\r\n", which we don't care about
        message = message.rstrip()

        logger.debug('Received message "%r"', message)


    # Below, define the handlers for IRC commands
