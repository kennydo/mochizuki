import re

import mock
import pytest
import trollius
from trollius import From

from mochizuki.servers import IRCServer


#: The host the IRC server will listen on when testing
TEST_HOST = 'localhost'
#: The port the IRC server will listen on when testing
TEST_PORT = 6667
#: The number of seconds to sleep when a client waits for input to expect
SLEEP_TIME_FOR_EXPECT = 0.2


class TestClientProtocol(trollius.Protocol):
    line_split_regex = re.compile(b'\r\n')

    def __init__(self):
        self.lines = []
        self.read_buffer = bytearray()
        self.transport = None
        self.socket_file = None

    def connection_made(self, transport):
        self.transport = transport
        socket = transport.get_extra_info('socket')
        self.socket_file = socket.makefile('w')

    def connection_lost(self, exc):
        self.transport.close()
        self.socket_file = None

    def data_received(self, data):
        self.read_buffer += data
        print(self.read_buffer)
        lines = [line.decode('utf8') for line in
                 self.line_split_regex.split(self.read_buffer)]
        if len(lines) == 1:
            # The data received is not a complete command yet
            return
        self.read_buffer = bytearray(lines.pop().encode())
        self.lines.extend(lines)
        for line in lines:
            print(line)

    def send(self, message):
        data = u'{0}\r\n'.format(message)
        self.socket_file.write(data)
        self.socket_file.flush()

    @trollius.coroutine
    def expect(self, regex):
        yield From(trollius.sleep(SLEEP_TIME_FOR_EXPECT))
        assert len(self.lines), 'There we no lines in the buffer'
        line = self.lines.pop(0)
        match = re.match(regex, line)
        assert match is not None, '%r did not match %r' % (line, regex)
        raise trollius.Return(match)


@pytest.fixture(scope='function')
def event_loop():
    """Create an event loop for each test"""
    loop = trollius.new_event_loop()
    trollius.set_event_loop(loop)
    return loop


@pytest.fixture(scope='function')
def irc_server(event_loop):
    """Instantiate a new `IRCServer` for each test"""
    server = IRCServer('local')

    # Disable PINGs to the user
    server.continually_ping_user = trollius.coroutine(mock.MagicMock())

    # Disable timing out at the registration stage
    server.wait_for_user_registration_timeout = trollius.coroutine(
        mock.MagicMock())

    server_coro = event_loop.create_server(
        server.get_client_protocol_factory(),
        TEST_HOST, TEST_PORT
    )
    server_task = event_loop.run_until_complete(server_coro)
    return server_task

@pytest.fixture(scope='function')
def new_irc_user():
    """Helper function to create a new connection to the IRC server"""

    @trollius.coroutine
    def inner(nickname):
        loop = trollius.get_event_loop()
        coro = loop.create_connection(TestClientProtocol,
                                      host=TEST_HOST,
                                      port=TEST_PORT)
        task = trollius.async(coro)
        _, protocol = yield From(task)

        protocol.send('NICK {0}'.format(nickname))
        protocol.send('USER {0} {0} 127.0.0.1 :realname'.format(nickname))
        yield From(protocol.expect(r':\S+ 001 \S+'))
        yield From(protocol.expect(r':\S+ 002 \S+'))
        yield From(protocol.expect(r':\S+ 003 \S+'))
        yield From(protocol.expect(r':\S+ 004 \S+'))
        raise trollius.Return(protocol)

    return inner
