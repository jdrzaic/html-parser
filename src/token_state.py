from abc import ABCMeta
import token


NULL_CHAR = '\u0000'
REPLACE_CHAR = '\uFFFD'


class State(object):
    __metaclass__ = ABCMeta

    def read(self, reader, tokeniser):
        pass


class DataState(State):
    def read(self, reader, tokeniser):
        read_c = reader.curr()
        if read_c == "&":
            tokeniser.move_to_state(CHAR_REF_IN_DATA)
        elif read_c == "<":
            tokeniser.move_to_state(TAG_OPEN)
        elif read_c == NULL_CHAR:
            tokeniser.error("DataState")
            tokeniser.emit(reader.consume())
        elif read_c == reader.EOF:
            tokeniser.emit(token.EOFToken())
        else:
            data = reader.consume_data()
            tokeniser.emit(data)


class CharRefInDataState(State):
    def read(self, reader, tokeniser):
        cs = tokeniser.consume_char_ref(None, False)
        if not cs:
            tokeniser.emit("&")
        else:
            tokeniser.emit(cs)
        tokeniser.move_to_state(DATA)


class RcDataState(State):
    def read(self, reader, tokeniser):
        read_c = reader.curr()
        if read_c == "&":
            tokeniser.move_to_state(CHAR_REF_IN_RCDATA)
        elif read_c == "<":
            tokeniser.move_to_state(RCDATA_LESS_THAN_SIGN)
        elif read_c == NULL_CHAR:
            tokeniser.error("RcDataState")
            reader.advance()
            tokeniser.emit(REPLACE_CHAR)
        elif read_c == reader.EOF:
            tokeniser.emit(token.EOFToken())
        else:
            data = reader.consume_to_any_of('&', '<', NULL_CHAR)
            tokeniser.emit(data)


class CharRefInRcDataState(State):
    def read(self, reader, tokeniser):
        cs = tokeniser.consume_char_ref(None, False)
        if not cs:
            tokeniser.emit("&")
        else:
            tokeniser.emit(cs)
        tokeniser.move_to_state(RCDATA)


class RawtextState(State):
    def read(self, reader, tokeniser):
        read_c = reader.current()
        if read_c == "<":
            tokeniser.move_to_state(RAWTEXT_LESS_THAN_SIGN)
        elif read_c == NULL_CHAR:
            tokeniser.error("RawtextState")
            reader.advance()
            tokeniser.emit(REPLACE_CHAR)

        elif read_c == reader.EOF:
            tokeniser.emit(token.EOFToken())
        else:
            data = reader.consume_to_any_of('<', NULL_CHAR)
            tokeniser.emit(data)


class ScriptData(State):
    def read(self, reader, tokeniser):
        read_c = reader.current()
        if read_c == "<":
            tokeniser.move_to_state(SCRIPT_DATA_LESS_THAN_SIGN)
        elif read_c == NULL_CHAR:
            tokeniser.error("ScriptData")
            reader.advance()
            tokeniser.emit(REPLACE_CHAR)

        elif read_c == reader.EOF:
            tokeniser.emit(token.EOFToken())
        else:
            data = reader.consume_to_any_of('<', NULL_CHAR)
            tokeniser.emit(data)


class PlaintextState(State):
    def read(self, reader, tokeniser):
        read_c = reader.current()
        if read_c == NULL_CHAR:
            tokeniser.error("PlaintextState")
            reader.advance()
            tokeniser.emit(REPLACE_CHAR)
        elif read_c == reader.EOF:
            tokeniser.emit(token.EOFToken())
        else:
            data = reader.consume_to(NULL_CHAR)
            tokeniser.emit(data)


class TagOpenState(State):
    def read(self, reader, tokeniser):
        read_c = reader.current()
        if read_c == "!":
            tokeniser.move_to_state(MARKUP_DECL_OPEN)
        elif read_c == "/":
            tokeniser.move_to_state(END_TAG_OPEN)
        elif  read_c == "?":
            tokeniser.move_to_state(BOGUS_COMMENT)
        else:
            if reader.match_letter():
                tokeniser.create_tag_pending(True)
                tokeniser.move(TAG_NAME)
            else:
                tokeniser.error("TagOpenState")
                tokeniser.emit("<")
                tokeniser.move(DATA)


class EndTagOpenState(State):
    def read(self, reader, tokeniser):
        if reader.empty():
            tokeniser.eof_error("EndTagOpenState")
            tokeniser.emit("</")
            tokeniser.move(DATA)
        elif reader.match_letter():
            tokeniser.create_tag_pending()
            tokeniser.move(TAG_NAME)
        elif reader.match('>'):
            tokeniser.error("EndTagOpenState")
            tokeniser.move_to_state(DATA)
        else:
            tokeniser.error("EndTagOpenState")
            tokeniser.move_to_state(BOGUS_COMMENT)


class RcDataLessThanSignState(State):
    def read(self, reader, tokeniser):
        pass


class RcDataEndTagOpenState(State):
    def read(self, reader, tokeniser):
        if reader.match_letter():
            tokeniser.create_tag_pending()
            tokeniser.tag_pending.append_tag_name(reader.current())
            tokeniser.script_buffer += reader.current()
            tokeniser.move_to_state(RCDATA_END_TAG_NAME)
        else:
            tokeniser.emit("</")
            tokeniser.move(RCDATA)


class RawtextLessThanSignState(State):
    pass


class ScriptDataLessThanSignState(State):
    pass


class MarkupDeclOpenState(State):
    pass


class BogusCommentState(State):
    pass


class TagNameState(State):
    def read(self, reader, tokeniser):
        tokeniser.tag_pending.append_tag_name(reader.consume_tag_name())
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f':
            return
        if read_c == " ":
            tokeniser.move(BEFORE_ATTR_NAME)
        elif read_c == "/":
            tokeniser.move(SELF_CLOSING_START_TAG)
        elif read_c == ">":
            tokeniser.emit_tag_pending()
            tokeniser.move(DATA)
        elif read_c == NULL_CHAR:
            tokeniser.tag_pending.append_tag_name(REPLACE_CHAR)
        elif read_c == reader.EOF:
            tokeniser.eof_error("TagNameState")
            tokeniser.move(DATA)


class BeforeAttrNameState(State):
    pass


class SelfClosingStartTagState(State):
    pass


class RcDataEndTagNameState(State):
    def read(self, reader, tokeniser):
        if reader.match_letter():
            name = reader.consume_word()
            tokeniser.tag_pending.append_tag_name(name)
            tokeniser.script_buffer += name
            return
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f':
            return
        if read_c == " ":
            if tokeniser.approptiate_end_tag_token():
                tokeniser.move(BEFORE_ATTR_NAME)
            else:
                tokeniser.emit("</" + tokeniser.script_buffer)
                reader.unconsume()
                tokeniser.move(RCDATA)


DATA = DataState()
CHAR_REF_IN_DATA = CharRefInDataState()
CHAR_REF_IN_RCDATA = CharRefInRcDataState()
RCDATA = RcDataState()
TAG_OPEN = TagOpenState()
END_TAG_OPEN = EndTagOpenState()
RCDATA_LESS_THAN_SIGN = RcDataLessThanSignState()
RAWTEXT_LESS_THAN_SIGN = RawtextLessThanSignState()
SCRIPT_DATA_LESS_THAN_SIGN = ScriptDataLessThanSignState()
MARKUP_DECL_OPEN = MarkupDeclOpenState()
BOGUS_COMMENT = BogusCommentState()
TAG_NAME = TagNameState()
BEFORE_ATTR_NAME = BeforeAttrNameState()
SELF_CLOSING_START_TAG = SelfClosingStartTagState()
RCDATA_END_TAG_OPEN = RcDataEndTagOpenState()
RCDATA_END_TAG_NAME = RcDataEndTagNameState()