import logging
import socket
from functools import partial

import trollius
from trollius import From

from mochizuki import replies
from mochizuki import utils

logger = logging.getLogger(__name__)
MAX_HOSTNAME_LENGTH = 63


class IRCClientProtocol(trollius.Protocol):
    def __init__(self, irc_server):
        """

        :param irc_server: a :class:`IRCServer` instance
        """

        self.irc_server = irc_server
        self.socket = None
        self.transport = None

    def connection_made(self, transport):
        self.socket = transport.get_extra_info('socket')
        self.transport = transport

        logger.info("self.irc_server: %r", self.irc_server)
        logger.info("Connection made to socket: %r", self.socket)

    def connection_lost(self, exc=None):
        logger.info("Connection lost to socket: %r", self.socket)
        self.transport.close()

    def data_received(self, data):
        """The callback for every chunk of data received from this client.
        Note that it isn't always one line per call.

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
            for line in unicode_data.splitlines():
                self.irc_server.handle(self.socket, line)


class IRCServer(object):
    def __init__(self, name):
        """

        :param str name: the name of the server
            (up to MAX_HOSTNAME_LENGTH chars long)
        """

        self.name = name[:MAX_HOSTNAME_LENGTH]

        #: Nickname queue maps :class:'socket.socket' objects to nickname
        self.nicks = {}

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

        # Normal messages end in "\r\n", which we don't care about.
        message = message.rstrip()
        command = utils.parse_command(message)

        logger.debug('Received message "%r"', message)

        command_handler = getattr(self, 'handle_{0}_command'.format(command.lower()), None)
        if not command_handler:
            self.handle_unkown_command(client_socket, command)
            return

        # Call the actual handler with the original message, COMMAND and all
        command_handler(client_socket, message)

    def reply(self, socket, number, message):
        """Reply to the user with a given reply number and message.

        :param socket: a :class:`socket.socket` to send the message to
        :param number: the numeric reply string from :mod:`mochizuki.replies`
        :param message: the string to send
        """

        data = u":{server_name} {number} {message}\r\n".format(
            server_name=self.name, number=number, message=message).encode()
        yield From(socket.send(data))
        logger.debug('Sent %r', data)

    # Below, define the handlers for IRC commands

    def handle_nick_command(self, client_socket, message):
        nick = utils.parse_message_params(message)

        logger.debug('Someone tried to register as nick %s', nick)

    def handle_user_command(self, client_socket, message):
        fragments = message.split(' ')
        # TODO(kennydo) handle improper input here
        username = fragments[1]
        realname = message.rsplit(':', 1)[-1]

        self.reply(
            client_socket,
            replies.RPL_WELCOME,
            "Welcome to the Internet Relay Network {nickname}!{username}@{host}".format(
                nickname="haha",
                username=username,
                host=client_socket.getpeername())
        )
        self.reply(
            client_socket,
            replies.RPL_YOURHOST,
            "Welcome to the Internet Relay Network {nickname}!{username}@{host}".format(
                nickname="haha",
                username=username,
                host=client_socket.getpeername())
        )
        self.reply(
            client_socket,
            replies.RPL_CREATED,
            "Welcome to the Internet Relay Network {nickname}!{username}@{host}".format(
                nickname="haha",
                username=username,
                host=client_socket.getpeername())
        )
        self.reply(
            client_socket,
            replies.RPL_MYINFO,
            "Welcome to the Internet Relay Network {nickname}!{username}@{host}".format(
                nickname="haha",
                username=username,
                host=client_socket.getpeername())
        )


    def handle_unkown_command(self, client_socket, command):
        """This handler is called when this :class:`IRCServer` instance
        doesn't have a handler defined for the given message.

        :param client_socket: the :class:`socket.socket` to the client
        :param unicode message: the message that the client sent
        """

        self.reply(
            client_socket,
            replies.ERR_UNKNOWNCOMMAND,
            "{nick} {command}: Unknown command".format(nick='haha', command=command))
