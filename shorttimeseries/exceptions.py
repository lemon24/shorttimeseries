

class InvalidTimestamp(Exception):

    def __init__(self, message, timestamp=None):
        super(InvalidTimestamp, self).__init__(message)
        self.timestamp = timestamp

    def __str__(self):
        message = super(InvalidTimestamp, self).__str__()
        if self.timestamp:
            message = "{}: {!r}".format(message, self.timestamp)
        return message
