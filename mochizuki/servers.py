import logging
from functools import partial

from . import replies
from . import utils
from .users import IRCUser

logger = logging.getLogger(__name__)
MAX_HOSTNAME_LENGTH = 63


# noinspection PyMethodMayBeStatic
class IRCServer(object):
    user_class = IRCUser

    def __init__(self, name):
        """

        :param str name: the name of the server
            (up to MAX_HOSTNAME_LENGTH chars long)
        """

        self.name = name[:MAX_HOSTNAME_LENGTH]

        # Maps `str` nicknames to :class:`users.IRCUser` objects
        self.users = {}

        # Maps `str` channel names to :class:`channels.IRCChannel` objects
        self.channels = {}

    def get_client_protocol_factory(self):
        """Return the factory for the :class:`Protocol` instances that will be
        created by the event loop whenever a new client connects.

        :return: a :class:`Protocol` that gets instantiated
        """
        return partial(self.user_class, irc_server=self)

    def handle(self, user, message):
        """

        :param user: the :class:`IRCUser` of the client
        :param unicode message: a single message from the `user`
        :return:
        """

        # Normal messages end in "\r\n", which we don't care about.
        message = message.rstrip()
        command = utils.parse_command(message)

        logger.debug('Received message: "%r"', message)

        command_handler = getattr(
            self,
            'handle_{0}_command'.format(command.lower()),
            None)
        if not command_handler:
            self.handle_unkown_command(user, command)
            return

        # Call the actual handler with the original message, COMMAND and all
        command_handler(user, message)

    # Below, define the handlers for IRC commands

    def handle_nick_command(self, user, message):
        new_nick = utils.parse_message_params(message).split(' ', 1)[0]
        # TODO(kennydo) verify that no one else is using this nick

        # If the user has not successfully sent a USER command,
        # then they are sending NICK for the first time.
        # First time NICK commands don't have a response.
        old_nick = user.nickname
        if not user.realname:
            user.nickname = new_nick
            return

        # If the user is changing their nickname, then we have to reply
        logger.info("{old} is changing nick to {new}"
                    .format(old=old_nick, new=new_nick))
        user.reply('NICK',
                   ':{0}'.format(new_nick),
                   include_nick=False,
                   prefix=user.prefix)
        # Change the nick after sending the reply so that the prefix
        # shows the old nick.
        user.nickname = new_nick

    def handle_user_command(self, user, message):
        fragments = message.split(' ')
        # TODO(kennydo) handle improper input here
        username = fragments[1]
        realname = message.rsplit(':', 1)[-1]

        user.username = username
        user.realname = realname

        user.reply(
            replies.RPL_WELCOME,
            "Welcome to the Internet Relay Network {user}"
            .format(user=user.prefix))
        user.reply(
            replies.RPL_YOURHOST,
            "Welcome to the Internet Relay Network {user}"
            .format(user=user.prefix))
        user.reply(
            replies.RPL_CREATED,
            "Welcome to the Internet Relay Network {user}"
            .format(user=user.prefix))
        user.reply(
            replies.RPL_MYINFO,
            "Welcome to the Internet Relay Network {user}"
            .format(user=user.prefix))

    def handle_unkown_command(self, user, command):
        """This handler is called when this :class:`IRCServer` instance
        doesn't have a handler defined for the given message.
        """

        user.reply(
            replies.ERR_UNKNOWNCOMMAND,
            "{command}: Unknown command"
            .format(command=command))
