#!/usr/bin/env python
import logging

from mochizuki import Application
from mochizuki.servers import IRCServer


logging.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    application = Application(IRCServer, host='127.0.0.1', port=6667)
    application.run()
