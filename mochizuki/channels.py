class IRCCHannel(object):
    """Represents an IRC channel and all of the state associated with it."""

    def __init__(self, name):
        """

        :param str name: the name of the new channel
        """
        self.name = name
        self.users = set()
