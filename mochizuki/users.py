class IRCUser(object):
    def __init__(self, nickname):
        """

        :param str nickname: the nick of the new user
        """
        self.nickname = nickname
        self.username = None
        self.hostname = None
        self.realname = None

    @property
    def prefix(self):
        """The prefix send in PRIVMSG and other messages to indicate the
        origin of the message
        """

        return "{nickname}!{username}@{hostname}".format(
            nickname=self.nickname,
            username=self.username,
            hostname=self.hostname,
        )
