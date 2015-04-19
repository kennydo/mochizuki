import logging

import trollius

logger = logging.getLogger(__name__)


class IRCUser(trollius.Protocol):
    def __init__(self, irc_server):
        """

        :param irc_server: a :class:`IRCServer` instance
        """

        # Low-level async connection variables
        self.irc_server = irc_server
        self.transport = None
        self.has_active_connection = False

        # High-level IRC variables
        self.nickname = None
        self.username = None
        self.hostname = None
        self.realname = None

        self.is_registered = False
        self.has_pending_ping = False

    @property
    def prefix(self):
        """The prefix send in PRIVMSG and other messages to indicate the
        origin of the message
        """

        return '{nickname}!{username}@{hostname}'.format(
            nickname=self.nickname,
            username=self.username,
            hostname=self.hostname,
        )

    def __repr__(self):
        return self.prefix

    def connection_made(self, transport):
        self.transport = transport
        self.hostname, _ = transport.get_extra_info('socket').getpeername()
        self.has_active_connection = True
        self.irc_server.on_user_connection_made(self)

    def connection_lost(self, exc=None):
        self.transport.close()
        self.has_active_connection = False
        self.irc_server.on_user_connection_lost(self)

    def data_received(self, data):
        """The callback for every chunk of data received from this client.
        Note that it isn't always one line per call.

        :param data: str or bytestring, depending on Python version
        """
        # Decode the data to unicode and then pass on to the server to handle.
        # TODO(kennydo) make a data buffer to handle messages split over 2
        #   calls to this function
        # TODO(kennydo) handle non-utf8 data
        try:
            unicode_data = data.decode('utf8')
        except UnicodeDecodeError:
            unicode_data = None
            logger.exception(
                'Could not decode data received from user: %r', data)

        if unicode_data:
            for line in unicode_data.splitlines():
                self.irc_server.handle(self, line)

    def reply(self, command, params, prefix=None, include_nick=True):
        """Send a reply to this user

        :param command: normally a string from :mod:`mochizuki.replies`
        :param unicode params: the message to send
        :param unicode prefix: `None` if you want to use the server's name
        :param boolean include_nick: include the nick in the data sent
        """
        if include_nick:
            # So many replies include the nick that this function defaults to
            # including it.
            template = u":{prefix} {command} {nickname} {params}\r\n"
        else:
            template = u":{prefix} {command} {params}\r\n"
        data = template.format(
            prefix=prefix if prefix else self.irc_server.name,
            command=command,
            params=params,
            nickname=self.nickname,
        ).encode()
        self.transport.write(data)
        logger.debug('Sent: %r', data)

    def send(self, message):
        """Send a raw message to the user

        :param unicode message: the entire raw message to send (without "\r\n")
        """
        data = u"{message}\r\n".format(message=message).encode()
        self.transport.write(data)
        logger.debug('Sent: %r', data)
