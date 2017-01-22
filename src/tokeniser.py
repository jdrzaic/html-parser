import token_state
import token


class Tokeniser(object):

    def __init__(self, reader, errors):
        self.reader = reader
        self.errors = errors
        self.state = token_state.DATA
        self.tag_pending = token.Token()
        self.comment_pending = token.CommentToken()
        self.doctype_pending = token.DoctypeToken()
        self.script_buffer = ''
        self.last_start_tag = None

    def move_to_state(self, state):
        self.reader.advance()
        self.state = state

    def move(self, state):
        self.state = state

    def emit(self, consumed):
        pass

    def emit_token(self, token):
        pass

    def emit_string(self, string):
        pass

    def error(self, state):
        self.errors.append(state)

    def eof_error(self, token):
        self.errors.append("EOF error: " + token)

    def emit_tag_pending(self):
        self.tag_pending.finalise_tag()
        self.emit(self.tag_pending)

    def emit_comment_pending(self):
        self.emit(self.comment_pending)

    def emit_doctype_pending(self):
        self.emit(self.doctype_pending)

    def consume_char_ref(self, additional_char, in_attr):
        pass

    def create_tag_pending(self, start=False):
        tag_pending = token.StartTagToken() if start else token.EndTagToken()
        return tag_pending

    def create_comment_pending(self):
        self.comment_pending = token.CommentToken()

    def create_doctype_pending(self):
        self.doctype_pending = token.DoctypeToken()

    def approptiate_end_tag_token(self):
        return self.last_start_tag is not None and self.tag_pending.name.lower() == self.last_start_tag.lower()

    def approptiate_end_tag_name(self):
        return self.last_start_tag

