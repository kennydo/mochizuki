import pytest
import trollius
from trollius import From

def test_unknown_command(event_loop, irc_server, new_irc_user):
    """Test that when the user sends an invalid command, the output is as
    expected.
    """
    @trollius.coroutine
    def run():
        alice = yield From(new_irc_user('alice'))
        alice.send('HELLO WORLD')
        yield From(alice.expect(r':\S+ 421 alice HELLO :Unknown command'))

    t = trollius.async(run())
    event_loop.run_until_complete(t)
    irc_server.close()
    event_loop.close()


def test_change_nick(event_loop, irc_server, new_irc_user):
    """Test that when the user changes their nick, the server's response shows
    the old prefix, not  the new prefix.
    """
    @trollius.coroutine
    def run():
        alice = yield From(new_irc_user('alice'))
        alice.send('NICK bob')
        yield From(alice.expect(r':alice\S+ NICK :bob'))

    t = trollius.async(run())
    event_loop.run_until_complete(t)
    irc_server.close()
    event_loop.close()
