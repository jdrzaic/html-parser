import token_state
import token as t
import attributes


class Tokeniser(object):

    def __init__(self, reader, errors):
        self.reader = reader
        self.errors = errors
        self.state = token_state.DATA
        self.tag_pending = None
        self.comment_pending = t.CommentToken()
        self.doctype_pending = t.DoctypeToken()
        self.char_pending = t.CharacterToken()
        self.script_buffer = ''
        self.last_start_tag = None
        self.is_emit_pending = False
        self.emit_pending = None
        self.self_closing_acknow = True
        self.chars_string = ''
        self.code_point_holder = []
        self.multi_point_holder = []

    def read(self):
        self.self_closing_acknow = True
        while not self.is_emit_pending:
            self.state.read(self.reader, self)
            print self.state
        if self.chars_string:
            str = self.chars_string
            self.chars_string = ""
            self.char_pending.data = str
            return self.char_pending
        else:
            self.is_emit_pending = False
            return self.emit_pending

    def move_to_state(self, state):
        self.reader.advance()
        self.state = state

    def move(self, state):
        self.state = state

    def emit(self, consumed):
        self.chars_string += consumed

    def emit_token(self, token):
        # validate
        self.emit_pending = token
        self.is_emit_pending = True

        if token.type == t.TokenType.START_TAG:
            self.last_start_tag = token.tag_name
            if token.is_self_closing:
               self.self_closing_acknow = False
        elif token.type == t.TokenType.END_TAG:
            if len(token.attrs.attrs):
                self.error("No attributes allowed on end tag!")

    def emit_string(self, str):
        self.chars_string += str

    def error(self, state):
        print(state)
        self.errors.append(state)

    def eof_error(self, token):
        self.errors.append("EOF error: " + token)

    def emit_tag_pending(self):
        self.tag_pending.finalise_tag()
        self.emit_token(self.tag_pending)

    def emit_comment_pending(self):
        self.emit_token(self.comment_pending)

    def emit_doctype_pending(self):
        self.emit_token(self.doctype_pending)

    def consume_char_ref(self, additional_char, in_attr):
        if self.reader.empty():  # stopped here TODO
            return None
        if additional_char and additional_char == self.reader.current():
            return None
        if self.reader.current() in ['\t', '\n', '\r', '\f', ' ', '<', '&']:
            return None
        self.reader.mark = self.reader.current_pos
        code_ref = []
        if self.reader.match_seq_consume("#"):
            hex = self.reader.match_seq_ic("X")
            num_ref = self.reader.consume_hex() if hex else self.reader.consume_dig()
            if not num_ref:
                self.reader.current_pos = self.reader.mark
                return None
            if not self.reader.match_seq_consume(";"):
                self.errors.append("Missing semicolon")
            charval = -1
            try:
                base = 16 if hex else 10
                charval = int(num_ref, base)
            except:
                pass
            if charval == -1 or (
                    charval >= 0xD800 and charval <= 0xDFFF) or charval > 0x10FFFF:
                self.errors.append("character outside of valid range")
                code_ref[0] = token_state.REPLACE_CHAR
                return code_ref
            else:
                code_ref[0] = charval
                return code_ref
        else:
            name_ref = self.reader.consume_letter_and_digit_seq()
            legit = self.reader.match(';')
            found = True #(Entities.isBaseNamedEntity(nameRef) | | (Entities.isNamedEntity(nameRef) & & legit));

            if not found:
                self.reader.current_pos = self.reader.mark
                if legit:
                    self.errors.append("invalid named referenece {0}".format(name_ref))
                return None
            if in_attr and (
                self.reader.match_letter() or self.reader.match_digit() or self.reader.match_any_of('=', '-', '_')):
                self.reader.current_pos = self.reader.mark
                return None
            if not self.reader.match_seq_consume(";"):
                self.errors.append("Missing semicolon")
            num_chars = 1#Entities.codepointsForName(nameRef, multipointHolder);
            if num_chars == 1:
                code_ref[0] = self.multi_point_holder[0]
                return code_ref
            elif num_chars == 2:
                return self.multi_point_holder
            else:
                return self.multi_point_holder

    def create_tag_pending(self, start=False):
        self.tag_pending = t.StartTagToken("", attributes.Attributes()) if start else t.EndTagToken()
        return self.tag_pending

    def create_comment_pending(self):
        self.comment_pending = t.CommentToken()

    def create_doctype_pending(self):
        self.doctype_pending = t.DoctypeToken()

    def approptiate_end_tag_token(self):
        return self.last_start_tag is not None and self.tag_pending.name.lower() == self.last_start_tag.lower()

    def approptiate_end_tag_name(self):
        return self.last_start_tag

    def unescape_entities(self, in_attr):
        str = ''
        while not self.reader.empty():
            str += self.reader.consume_to("&")
            if self.reader.match("&"):
                self.reader.consume()
                c = self.consume_char_ref(None, in_attr)
                if not c:
                    str += "&"
                else:
                    str += c[0]
                    if len(c) == 2:
                        str += c[1]
        return str



