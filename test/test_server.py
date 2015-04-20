import functools
import trollius
from trollius import From


def coroutine_irc_test(func):
    """Helper decorator that marks the test function as a coroutine and
    closes the IRC server and event loop after the test is finished done.
    """
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        # pytest magic turns these positional arguments into kwargs
        event_loop = kwargs['event_loop']
        irc_server = kwargs['irc_server']

        coro = trollius.coroutine(func)
        task = trollius.async(coro(*args, **kwargs))
        try:
            event_loop.run_until_complete(task)
        finally:
            # Make sure that the IRC server and the event loop are closed
            # so that future tests don't all fail.
            irc_server.close()
            event_loop.close()
    return wrapped


@coroutine_irc_test
def test_unknown_command(event_loop, irc_server, new_irc_user):
    """Test that when the user sends an invalid command, the output is as
    expected.
    """
    alice = yield From(new_irc_user('alice'))
    alice.send('HELLO WORLD')
    yield From(alice.expect(r':\S+ 421 alice HELLO :Unknown command'))


@coroutine_irc_test
def test_change_nick(event_loop, irc_server, new_irc_user):
    """Test that when the user changes their nick, the server's response shows
    the old prefix, not  the new prefix.
    """
    alice = yield From(new_irc_user('alice'))
    alice.send('NICK bob')
    yield From(alice.expect(r':alice\S+ NICK :bob'))
