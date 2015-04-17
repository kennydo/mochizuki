class IRCUser(object):
    def __init__(self, nickname):
        """

        :param str nickname: the nick of the new user
        """
        self.nickname = nickname
        self.username = None
        self.hostname = None
        self.realname = None
