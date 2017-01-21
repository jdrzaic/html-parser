import token_state
import token


class Tokeniser(object):

    def __init__(self, reader, errors):
        self.reader = reader
        self.errors = errors
        self.state = token_state.DATA
        self.tag_pending = token.Token()
        self.script_buffer = ''

    def move_to_state(self, state):
        self.reader.advance()
        self.state = state

    def move(self, state):
        self.state = state

    def emit(self, consumed):
        pass

    def error(self, state):
        pass

    def eof_error(self, token):
        pass

    def emit_tag_pending(self):
        pass

    def consume_char_ref(self, additional_char, in_attr):
        pass

    def create_tag_pending(self, bool=False):
        pass

    def approptiate_end_tag_token(self):
        pass

    def approptiate_end_tag_name(self):
        pass
