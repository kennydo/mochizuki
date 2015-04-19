def parse_command(message):
    """Parse the command (or possible command) from a user's message
    to the server.

    :param unicode message: a line of data from the user
    :return: the command (first word in the message)
    """
    return message.split(' ', 1)[0]

def parse_message_params(message):
    """Parse the non-command part of the string out from a user's message
    to the server.

    :param unicode: message: a line of data from the user
    :return: the rest of the message after the command
    """
    return message.split(' ', 1)[1]
