import datetime
import logging
import time
from functools import partial

import trollius

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
        :param unicode name: the name of the server
            (up to MAX_HOSTNAME_LENGTH chars long)
        """
        self.creation_time = datetime.datetime.utcnow()

        self.name = name[:MAX_HOSTNAME_LENGTH]

        # Maps `str` nicknames to :class:`users.IRCUser` objects
        self.users = {}

        # Maps `str` channel names to :class:`channels.IRCChannel` objects
        self.channels = {}

        self.loop = trollius.get_event_loop()

    def get_client_protocol_factory(self):
        """Return the factory for the :class:`Protocol` instances that will be
        created by the event loop whenever a new client connects.

        :return: a :class:`Protocol` that gets instantiated
        """

        return partial(self.user_class, irc_server=self)

    def handle(self, user, message):
        """Delegate each line of user input to the respective handler method.
        If not method exists, calls the :method:`handle_unknown_command`.

        :type user: mochizuki.users.IRCUser
        :param unicode message: a single line of input from the `user`
        """

        # Normal messages end in "\r\n", which we don't care about.
        message = message.rstrip()
        command = utils.parse_command(message)

        command_handler = getattr(
            self,
            'handle_{0}_command'.format(command.lower()),
            None)
        if not command_handler:
            self.handle_unkown_command(user, message)
            return

        # Call the actual handler with the original message, COMMAND and all
        command_handler(user, message)

    def on_user_connection_made(self, user):
        """Callback called when a user first connects

        :type user: mochizuki.users.IRCUser
        """
        logger.info('User (%r) connection made', user)
        self.loop.create_task(self.wait_for_user_registration_timeout(user))

    def on_user_connection_lost(self, user):
        """ Callback called when a user's connection is lost.
        This could be us terminating the user's transport, or it could be
        the user terminating the connection.

        :type user: mochizuki.users.IRCUser
        """
        logger.info('User (%r) connection lost', user)

    @trollius.coroutine
    def wait_for_user_registration_timeout(self, user, timeout=60):
        """Timeout the user if they don't finish registration before the
        timeout expires.

        :type user: mochizuki.users.IRCUser
        :param int timeout: timeout in seconds
        """
        yield trollius.From(trollius.sleep(timeout))
        if not user.is_registered and user.has_active_connection:
            user.send('ERROR :Registration timed out')
            user.transport.close()

    @trollius.coroutine
    def continually_ping_user(self, user, period=180, timeout=60):
        """A coroutine that continuously PINGs the user. If the user doesn't
        PONG within the timeout window, the user's connection is killed.

        The timeout should always be less than the period, or else this
        coroutine will still be waiting for the timeout when its next PING
        is supposed to be sent.

        :type user: mochizuki.users.IRCUser
        :param int period: the time in seconds between PINGs send to the user
        :param int timeout: the seconds before we terminate the connection
            if the user doesn't PONG in time
        """
        while user.has_active_connection:
            user.send('PING :{server_name}'.format(server_name=self.name))
            latest_ping = time.time()
            user.has_pending_ping = True
            yield trollius.From(trollius.sleep(timeout))
            if user.has_pending_ping:
                logger.info(
                    'User %r did not respond to PING within %d seconds',
                    user,
                    timeout
                )
                # the user has not responded to this ping
                user.send('ERROR :Ping timeout ({0} seconds)'.format(timeout))
                user.transport.close()
                break
            time_since_ping = time.time() - latest_ping
            time_to_sleep = max(period - time_since_ping, 0)
            yield trollius.From(trollius.sleep(time_to_sleep))

    # Below, define the handlers for IRC commands

    def handle_nick_command(self, user, message):
        """Handle the NICK command.

        :param user: the user who sent the command
        :type user: mochizuki.users.IRCUser
        :param unicode message: the received message
        """

        new_nick = utils.parse_message_params(message).split(' ', 1)[0]
        # TODO(kennydo) verify that no one else is using this nick

        # If the user has not successfully sent a USER command,
        # then they are sending NICK for the first time.
        # First time NICK commands don't have a response.
        old_nick = user.nickname
        if not user.is_registered:
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
        """Handle the USER command.

        :param user: the user who sent the command
        :type user: mochizuki.users.IRCUser
        :param unicode message: the received message
        """

        if user.is_registered:
            user.reply(
                replies.ERR_ALREADYREGISTRED,
                ':Unauthorized command (already registered)')
            return

        user.realname = message.rsplit(':', 1)[-1]

        user.reply(
            replies.RPL_WELCOME,
            ':Welcome to the Internet Relay Network {user}'
            .format(user=user.prefix))
        user.reply(
            replies.RPL_YOURHOST,
            ':Your host is {server_name}'.format(server_name=self.name))
        user.reply(
            replies.RPL_CREATED,
            ':This server was created {date}'
            .format(date=self.creation_time.strftime("%b %d %Y at %H:%M:%S")))
        user.reply(
            replies.RPL_MYINFO,
            ':{server_name} {version} {user_modes} {channel_modes}'
            .format(
                server_name=self.name,
                version='0.0.1',
                user_modes='o',
                channel_modes='o',
            ))

        user.is_registered = True
        self.loop.create_task(self.continually_ping_user(user))

    def handle_pong_command(self, user, message):
        """Handle the PONG command.

        :param user: the user who sent the command
        :type user: mochizuki.users.IRCUser
        :param unicode message: the received message
        """

        user.has_pending_ping = False

    def handle_ping_command(self, user, message):
        """Handle the PING command.

        :param user: the user who sent the command
        :type user: mochizuki.users.IRCUser
        :param unicode message: the received message
        """

        # This should split the fragment into PING and whatever else is after
        fragments = message.split(' ', 1)

        if len(fragments) < 2:
            # The user only sent PING, without any params
            self.user.reply(
                replies.ERR_NEEDMOREPARAMS,
                'PING :Not enough parameters')
            return

        self.user.send('PONG {server_name} :{response}'.format(
            server_name=self.name,
            response=fragments[1],
        ))

    def handle_unkown_command(self, user, message):
        """This handler is called when this :class:`IRCServer` instance
        doesn't have a handler defined for the given message.

        :param user: the user who sent the command
        :type user: mochizuki.users.IRCUser
        :param unicode message: the received message
        """

        command = utils.parse_command(message)

        user.reply(
            replies.ERR_UNKNOWNCOMMAND,
            "{0} :Unknown command".format(command))
