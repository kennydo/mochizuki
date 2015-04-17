#!/usr/bin/env python

from mochizuki import Application
from mochizuki.servers import IRCServer


if __name__ == "__main__":
    application = Application(IRCServer(), host='127.0.0.1', port=6667)
    application.run()
