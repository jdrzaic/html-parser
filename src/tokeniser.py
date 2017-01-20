import token_state


class Tokeniser(object):

    def __init__(self, reader, errors):
        self.reader = reader
        self.errors = errors
        self.state = token_state.DATA

    def move_to_state(self, state):
        self.state = state