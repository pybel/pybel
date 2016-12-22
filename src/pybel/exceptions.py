class PyBelWarning(Exception):
    """PyBEL throws exceptions labeled PyBEL1xx for statements that cannot be fixed automatically"""
    #:
    code = 0

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'PyBEL1{:02} - {} - {}'.format(self.code, self.__class__.__name__, self.message)

