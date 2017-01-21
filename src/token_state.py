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


class ScriptDataState(State):
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
        if reader.match("/"):
            tokeniser.script_buffer = ""
            tokeniser.move_to_state(RCDATA_END_TAG_OPEN)
        elif reader.match_letter() and tokeniser.approptiate_end_tag_name() and not reader.contains_ignore_case("</" + tokeniser.approptiate_end_tag_name()):
            tokeniser.tag_pending = tokeniser.create_tag_pending()
            tokeniser.tag_pending.name = tokeniser.approptiate_end_tag_name()
            tokeniser.emit_tag_pending()
            reader.unconsume()
            tokeniser.move(DATA)
        else:
            tokeniser.emit("<")
            tokeniser.move(RCDATA)


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
    def read(self, reader, tokeniser):
        if reader.match("/"):
            tokeniser.script_buffer = ''
            tokeniser.move_to_state(RAWTEXT_END_TAG_OPEN)
        else:
            tokeniser.emit("<")
            tokeniser.move(RAWTEXT)


class ScriptDataLessThanSignState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == "/":
            tokeniser.script_buffer = ''
            tokeniser.move(SCRIPT_DATA_END_TAG_OPEN)
        elif read_c == "!":
            tokeniser.emit("<!")
            tokeniser.move(SCRIPT_DATA_ESCAPE_START)
        else:
            tokeniser.emit("<")
            reader.unconsume()
            tokeniser.move(SCRIPT_DATA)


class MarkupDeclOpenState(State):
    pass


class BogusCommentState(State):
    pass


class TagNameState(State):
    def read(self, reader, tokeniser):
        tokeniser.tag_pending.append_tag_name(reader.consume_tag_name())
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " ":
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
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f'or read_c == " ":
            pass
        elif read_c == "/":
            tokeniser.move(SELF_CLOSING_START_TAG)
        elif read_c == ">":
            tokeniser.emit_tag_pending()
            tokeniser.move(DATA)
        elif read_c == NULL_CHAR:
            tokeniser.error("BeforeAttrNameState")
            tokeniser.tag_pending.new_attribute()
            reader.unconsume()
            tokeniser.move(ATTRIBUTE_NAME)
        elif read_c == reader.EOF:
            tokeniser.eof_error("BeforeAttrNameState")
            tokeniser.move(DATA)
        elif read_c == '"' or read_c == "'" or read_c == "<" or read_c == "=":
            tokeniser.error("BeforeAttrNameState")
            tokeniser.tag_pending.new_attribute()
            tokeniser.tag_pending.append_attr_name(read_c)
            tokeniser.move(ATTRIBUTE_NAME)
        else:
            tokeniser.tag_pending.new_attribute()
            reader.unconsume()
            tokeniser.move(ATTRIBUTE_NAME)


class AttributeNameState(State):
    pass


class SelfClosingStartTagState(State):
    pass


class RawTextEndTagOpenState(State):
    def read(self, reader, tokeniser):
        if reader.match_letter():
            tokeniser.create_tag_pending()
            tokeniser.move(RAWTEXT_END_TAG_NAME)
        else:
            tokeniser.emit("</")
            tokeniser.move(RAWTEXT)


class RcDataEndTagNameState(State):
    def read(self, reader, tokeniser):
        if reader.match_letter():
            name = reader.consume_word()
            tokeniser.tag_pending.append_tag_name(name)
            tokeniser.script_buffer += name
            return
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f'or read_c == " ":
            if tokeniser.approptiate_end_tag_token():
                tokeniser.move(BEFORE_ATTR_NAME)
            else:
                tokeniser.emit("</" + tokeniser.script_buffer)
                reader.unconsume()
                tokeniser.move(RCDATA)
        elif read_c == "/":
            if tokeniser.approptiate_end_tag_token():
                tokeniser.move(SELF_CLOSING_START_TAG)
            else:
                tokeniser.emit("</" + tokeniser.script_buffer)
                reader.unconsume()
                tokeniser.move(RCDATA)
        elif read_c == ">":
            if tokeniser.approptiate_end_tag_token():
                tokeniser.emit_tag_pending()
                tokeniser.move(DATA)
            else:
                tokeniser.emit("</" + tokeniser.script_buffer)
                reader.unconsume()
                tokeniser.move(RCDATA)
        else:
            tokeniser.emit("</" + tokeniser.script_buffer)
            reader.unconsume()
            tokeniser.move(RCDATA)


class RawtextEndTagNameState(State):
    def read(self, reader, tokeniser):
        if reader.match_letter():
            name = reader.consume_word()
            tokeniser.tag_pending.append_tag_name(name)
            tokeniser.script_buffer += name
            return
        needs_exit_tran = False
        if tokeniser.approptiate_end_tag_token() and not reader.empty():
            read_c = reader.consume()
            if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " ":
                tokeniser.move(BEFORE_ATTR_NAME)
            elif read_c == "/":
                tokeniser.move(SELF_CLOSING_START_TAG)
            elif read_c == ">":
                tokeniser.emit_tag_pending()
                tokeniser.move(DATA)
            else:
                tokeniser.script_buffer += read_c
                needs_exit_tran = True
        else:
            needs_exit_tran = True
        if needs_exit_tran:
            tokeniser.emit("</" + tokeniser.script_buffer)
            tokeniser.move(RAWTEXT)


class ScriptDataEndTagOpenState(State):
    def read(self, reader, tokeniser):
        if reader.match_letter():
            tokeniser.create_tag_pending()
            tokeniser.move(SCRIPT_DATA_END_TAG_NAME)
        else:
            tokeniser.emit("</")
            tokeniser.move(SCRIPT_DATA)


class ScriptDataEndTagNameState(State):
    def read(self, reader, tokeniser):
        if reader.match_letter():
            name = reader.consume_word()
            tokeniser.tag_pending.append_tag_name(name)
            tokeniser.script_buffer += name
        needs_exit_tran = False
        if tokeniser.approptiate_end_tag_token() and not reader.empty():
            read_c = reader.consume()
            if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " ":
                tokeniser.move(BEFORE_ATTR_NAME)
            elif read_c == "/":
                tokeniser.move(SELF_CLOSING_START_TAG)
            elif read_c == ">":
                tokeniser.emit_tag_pending()
                tokeniser.move(DATA)
            else:
                tokeniser.script_buffer += read_c
                needs_exit_tran = True
        else:
            needs_exit_tran = True
        if needs_exit_tran:
            tokeniser.emit("</" + tokeniser.script_buffer)
            tokeniser.move(SCRIPT_DATA)


class ScriptDataEscapeStartState(State):
    def read(self, reader, tokeniser):
        if reader.match("-"):
            tokeniser.emit("-")
            tokeniser.move_to_state(SCRIPT_DATA_ESCAPE_START_DASH)
        else:
            tokeniser.move(SCRIPT_DATA)


class ScriptDataEscapeStartDash(State):
    def read(self, reader, tokeniser):
        if reader.match("-"):
            tokeniser.emit("-")
            tokeniser.move_to_state(SCRIPT_DATA_ESCAPE_START_DASH)
        else:
            tokeniser.move(SCRIPT_DATA)


class ScriptDataEscapedState(State):
    def read(self, reader, tokeniser):
        if reader.empty():
            tokeniser.eof_error("ScriptDataEscapedState")
            tokeniser.move(DATA)
            return
        read_c = reader.current()
        if read_c == "-":
            tokeniser.emit("-")
            tokeniser.move_to_state(SCRIPT_DATA_ESCAPED_DASH)
        elif read_c == "<":
            tokeniser.move_to_state(SCRIPDATA_ESCAPED_LESS_THAN_SIGN)
        elif read_c == NULL_CHAR:
            tokeniser.error("ScriptDataEscapedState")
            reader.advance()
            tokeniser.emit(REPLACE_CHAR)
        else:
            data = reader.consume_to_any_of('-', '<', NULL_CHAR)
            tokeniser.emit(data)


class ScriptDataEscapedDashState(State):
    def read(self, reader, tokeniser):
        if reader.empty():
            tokeniser.eof_error("ScriptDataEscapedDashState")
            tokeniser.move(DATA)
            return
        read_c = reader.consume()
        if read_c == "-":
            tokeniser.emit("-")
            tokeniser.move_to_state(SCRIPT_DATA_ESCAPED_DASH_DASH)
        elif read_c == "<":
            tokeniser.move_to_state(SCRIPDATA_ESCAPED_LESS_THAN_SIGN)
        elif read_c == NULL_CHAR:
            tokeniser.error("ScriptDataEscapedState")
            reader.advance()
            tokeniser.emit(REPLACE_CHAR)
        else:
            data = reader.consume_to_any_of('-', '<', NULL_CHAR)
            tokeniser.emit(data)


class ScriptDataEscapedLessThanSignState(State):
    def read(self, reader, tokeniser):
        if reader.match_letter():
            tokeniser.script_buffer = ''
            tokeniser.script_buffer += reader.current()
            tokeniser.emit("<" + reader.current())
            tokeniser.move_to_state(SCRIPT_DATA_DOUBLE_ESCAPE_START)
        elif reader.match("/"):
            tokeniser.script_buffer = ''
            tokeniser.move_to_state(SCRIPT_DATA_ESCAPED_END_TAG_OPEN)
        else:
            tokeniser.emit("<")
            tokeniser.move(SCRIPT_DATA_ESCAPED)


class ScriptDataEscapedDashDashState(State):
    def read(self, reader, tokeniser):
        if reader.empty():
            tokeniser.eof_error("ScriptDataEscapedDashDashState")
            tokeniser.move(DATA)
            return
        read_c = reader.consume()
        if read_c == "-":
            tokeniser.emit("-")
        elif read_c == "<":
            tokeniser.move_to_state(SCRIPDATA_ESCAPED_LESS_THAN_SIGN)
        elif read_c == ">":
            tokeniser.emit(read_c)
            tokeniser.move(SCRIPT_DATA)
        elif read_c == NULL_CHAR:
            tokeniser.error("ScriptDataEscapedDashDashState")
            tokeniser.emit(REPLACE_CHAR)
            tokeniser.move(SCRIPT_DATA_ESCAPED)
        else:
            tokeniser.emit(read_c)
            tokeniser.move(SCRIPT_DATA_ESCAPED)


class ScriptDataEscapedEndTagOpenState(State):
    def read(self, reader, tokeniser):
        if reader.match_letter():
            tokeniser.create_tag_pending()
            tokeniser.tag_pending.append_tag_name(reader.current())
            tokeniser.script_buffer += reader.current()
            tokeniser.move_to_state(SCRIPT_DATA_ESCAPED_END_TAG_NAME)


class ScriptDataEscapedEndTagNameState(State):
    def read(self, reader, tokeniser):
        if reader.match_letter():
            name = reader.consume_word()
            tokeniser.tag_pending.append_tag_name(name)
            tokeniser.script_buffer += name
        needs_exit_tran = False
        if tokeniser.approptiate_end_tag_token() and not reader.empty():
            read_c = reader.consume()
            if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " ":
                tokeniser.move(BEFORE_ATTR_NAME)
            elif read_c == "/":
                tokeniser.move(SELF_CLOSING_START_TAG)
            elif read_c == ">":
                tokeniser.emit_tag_pending()
                tokeniser.move(DATA)
            else:
                tokeniser.script_buffer += read_c
                needs_exit_tran = True
        else:
            needs_exit_tran = True
        if needs_exit_tran:
            tokeniser.emit("</" + tokeniser.script_buffer)
            tokeniser.move(SCRIPT_DATA_ESCAPED)



class ScriptDataDoubleEscapeStartState(State):
    def read(self, reader, tokeniser):
        if reader.match_letter():
            name = reader.consume_word()
            tokeniser.script_buffer += name
            tokeniser.emit(name)
            return
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " " or read_c == "/" or read_c == ">":
            if tokeniser.script_buffer == "script":
                tokeniser.move(SCRIPT_DATA_DOUBLE_ESCAPED)
            else:
                tokeniser.move(SCRIPT_DATA_ESCAPED)
            tokeniser.emit(read_c)
        else:
            reader.unconsume()
            tokeniser.move(SCRIPT_DATA_ESCAPED)



class ScriptDataDoubleEscapedState(State):
    def read(self, reader, tokeniser):
        read_c = reader.current()
        if read_c == "-":
            tokeniser.emit("-")
            tokeniser.move_to_state(SCRIPT_DATA_DOUBLE_ESCAPED_DASH)
        elif read_c == "<":
            tokeniser.emit("<")
            tokeniser.move_to_state(SCRIPT_DATA_DOUBLE_ESCAPED_LESS_THAN_SIGN)
        elif read_c == NULL_CHAR:
            tokeniser.error("ScriptDataDoubleEscapedState")
            reader.advance()
            tokeniser.emit(REPLACE_CHAR)
        elif read_c == reader.EOF:
            tokeniser.eof_error("ScriptDataDoubleEscapedState")
            tokeniser.move(DATA)
        else:
            data = reader.consume_to_any_of('-', '<', NULL_CHAR)
            tokeniser.emit(data)


class ScriptDataDoubleEscapedLessThanSignState(State):
    def read(self, reader, tokeniser):
        if reader.match("/"):
            tokeniser.emit("/")
            tokeniser.script_buffer = ""
            tokeniser.move_to_state(SCRIPT_DATA_DOUBLE_ESCAPE_END)
        else:
            tokeniser.move(SCRIPT_DATA_DOUBLE_ESCAPED)


class ScriptDataDoubleEscapedDashState(State):
    def read(self, reader, tokeniser):
        read_c = reader.current()
        if read_c == "-":
            tokeniser.emit(read_c)
            tokeniser.move_to_state(SCRIPT_DATA_DOUBLE_ESCAPED_DASH_DASH)
        elif read_c == "<":
            tokeniser.emit(read_c)
            tokeniser.move_to_state(SCRIPT_DATA_DOUBLE_ESCAPED_LESS_THAN_SIGN)
        elif read_c == NULL_CHAR:
            tokeniser.error("ScriptDataDoubleEscapedDashState")
            tokeniser.emit(REPLACE_CHAR)
            tokeniser.emit(SCRIPT_DATA_DOUBLE_ESCAPED)
        elif read_c == reader.EOF:
            tokeniser.eof_error("ScriptDataDoubleEscapedDashState")
            tokeniser.move(DATA)
        else:
            tokeniser.emit(read_c)
            tokeniser.move(SCRIPT_DATA_DOUBLE_ESCAPED)


class ScriptDataDoubleEscapedState(State):
    def read(self, reader, tokeniser):
        read_c = reader.current()
        if read_c == "-":
            tokeniser.emit(read_c)
            tokeniser.move_to_state(SCRIPT_DATA_DOUBLE_ESCAPED_DASH)
        elif read_c == "<":
            tokeniser.emit(read_c)
            tokeniser.move_to_state(SCRIPT_DATA_DOUBLE_ESCAPED_LESS_THAN_SIGN)
        elif read_c == NULL_CHAR:
            tokeniser.error("ScriptDataDoubleEscapedState")
            reader.advance()
            tokeniser.emit(REPLACE_CHAR)
        elif read_c == reader.EOF:
            tokeniser.eof_error("ScriptDataDoubleEscapedState")
            tokeniser.move(DATA)
        else:
            data = reader.consume_to_any_of('-', '<', NULL_CHAR)
            tokeniser.emit(data)


class ScriptDataDoubleEscapedDashDashState(State):
    def read(self, reader, tokeniser):
        read_c = reader.current()
        if read_c == "-":
            tokeniser.emit("-")
        elif read_c == "<":
            tokeniser.emit("<")
            tokeniser.move_to_state(SCRIPT_DATA_DOUBLE_ESCAPED_LESS_THAN_SIGN)
        elif read_c == ">":
            tokeniser.emit(">")
            tokeniser.move(SCRIPT_DATA)
        elif read_c == NULL_CHAR:
            tokeniser.error("ScriptDataDoubleEscapedDashDashState")
            tokeniser.emit(REPLACE_CHAR)
            tokeniser.move(SCRIPT_DATA_DOUBLE_ESCAPED)
        elif read_c == reader.EOF:
            tokeniser.eof_error("ScriptDataDoubleEscapedDashDashState")
            tokeniser.move(DATA)
        else:
            tokeniser.emit(read_c)
            tokeniser.move(SCRIPT_DATA_DOUBLE_ESCAPED)


class ScriptDataDoubleEscapeEndState(State):
    def read(self, reader, tokeniser):
        if reader.match_letter():
            name = reader.consume_word()
            tokeniser.script_buffer += name
            tokeniser.emit(name)
            return
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " " or read_c == "/" or read_c == ">":
            if tokeniser.script_buffer == "script":
                tokeniser.move(SCRIPT_DATA_ESCAPED)
            else:
                tokeniser.move(SCRIPT_DATA_DOUBLE_ESCAPED)
            tokeniser.emit(read_c)
        else:
            reader.unconsume()
            tokeniser.move(SCRIPT_DATA_DOUBLE_ESCAPED)


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
RAWTEXT_END_TAG_OPEN = RawTextEndTagOpenState()
RAWTEXT = RawtextState()
RAWTEXT_END_TAG_NAME = RawtextEndTagNameState()
SCRIPT_DATA_END_TAG_OPEN = ScriptDataEndTagOpenState()
SCRIPT_DATA_ESCAPE_START = ScriptDataEscapeStartState()
SCRIPT_DATA = ScriptDataState()
SCRIPT_DATA_END_TAG_NAME = ScriptDataEndTagNameState()
SCRIPT_DATA_ESCAPE_START_DASH = ScriptDataEscapeStartDash()
SCRIPT_DATA_ESCAPED = ScriptDataEscapedState()
SCRIPT_DATA_ESCAPED_DASH = ScriptDataEscapedDashState()
SCRIPDATA_ESCAPED_LESS_THAN_SIGN = ScriptDataEscapedLessThanSignState()
SCRIPT_DATA_ESCAPED_DASH_DASH = ScriptDataEscapedDashDashState()
SCRIPT_DATA_DOUBLE_ESCAPE_START = ScriptDataDoubleEscapeStartState()
SCRIPT_DATA_ESCAPED_END_TAG_OPEN = ScriptDataEscapedEndTagOpenState()
SCRIPT_DATA_ESCAPED_END_TAG_NAME = ScriptDataEscapedEndTagNameState()
SCRIPT_DATA_DOUBLE_ESCAPED_DASH = ScriptDataDoubleEscapedDashState()
SCRIPT_DATA_DOUBLE_ESCAPED_LESS_THAN_SIGN = ScriptDataDoubleEscapedLessThanSignState()
SCRIPT_DATA_DOUBLE_ESCAPED = ScriptDataDoubleEscapedState()
SCRIPT_DATA_DOUBLE_ESCAPED_DASH_DASH = ScriptDataDoubleEscapedDashDashState()
SCRIPT_DATA_DOUBLE_ESCAPE_END = ScriptDataDoubleEscapeEndState()
ATTRIBUTE_NAME = AttributeNameState()
