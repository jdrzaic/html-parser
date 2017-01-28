from abc import ABCMeta
import token
import node

NULL_CHAR = '\u0000'
REPLACE_CHAR = '\uFFFD'


class State(object):
    __metaclass__ = ABCMeta

    def read(self, reader, tokeniser):
        pass


class DataState(State):
    def read(self, reader, tokeniser):
        read_c = reader.current()
        if read_c == "&":
            tokeniser.move_to_state(CHAR_REF_IN_DATA)
        elif read_c == "<":
            tokeniser.move_to_state(TAG_OPEN)
        elif read_c == NULL_CHAR:
            tokeniser.error("DataState")
            tokeniser.emit(reader.consume())
        elif read_c == reader.EOF:
            tokeniser.emit_token(token.EOFToken())
        else:
            data = reader.consume_data()
            tokeniser.emit_string(data)


class CharRefInDataState(State):
    def read(self, reader, tokeniser):
        cs = tokeniser.consume_char_ref(None, False)
        if not cs:
            tokeniser.emit("&")  # TODO
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
            tokeniser.emit_token(token.EOFToken())
        else:
            data = reader.consume_to_any_of('&', '<', NULL_CHAR)
            tokeniser.emit_string(data)


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
            tokeniser.emit_string(data)


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
            tokeniser.emit_token(token.EOFToken())
        else:
            data = reader.consume_to_any_of('<', NULL_CHAR)
            tokeniser.emit_string(data)


class PlaintextState(State):
    def read(self, reader, tokeniser):
        read_c = reader.current()
        if read_c == NULL_CHAR:
            tokeniser.error("PlaintextState")
            reader.advance()
            tokeniser.emit(REPLACE_CHAR)
        elif read_c == reader.EOF:
            tokeniser.emit_token(token.EOFToken())
        else:
            data = reader.consume_to(NULL_CHAR)
            tokeniser.emit_string(data)


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
            tokeniser.emit_string("</")
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
        elif reader.match_letter() and tokeniser.approptiate_end_tag_name() and not reader.contains_ignore_case(
                        "</" + tokeniser.approptiate_end_tag_name()):
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
            tokeniser.emit_string("</")
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
            tokeniser.emit_string("<!")
            tokeniser.move(SCRIPT_DATA_ESCAPE_START)
        else:
            tokeniser.emit("<")
            reader.unconsume()
            tokeniser.move(SCRIPT_DATA)


class MarkupDeclOpenState(State):
    def read(self, reader, tokeniser):
        if reader.match_seq_consume("--"):
            tokeniser.create_comment_pending()
            tokeniser.move(COMMENT_START)
        elif reader.match_seq_ic("DOCTYPE"):
            tokeniser.move(DOCTYPE)
        # TODO
        #elif reader.match_seq("[CDATA["):
        #    tokeniser.move(CDATA_SECTION)
        else:
            tokeniser.error("MarkupDeclOpenState")
            tokeniser.move_to_state(BOGUS_COMMENT)


class BogusCommentState(State):
    def read(self, reader, tokeniser):
        reader.unconsume()
        comment_token = token.CommentToken()
        comment_token.data += reader.consume_to(">")
        comment_token.bogus = True
        tokeniser.emit_token(comment_token)
        tokeniser.move_to_state(DATA)


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
            return
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


class AttrNameState(State):
    def read(self, reader, tokeniser):
        name = reader.consume_to_any_of(
            '\t', '\n', '\r', '\f', ' ', '/', '=', '>', NULL_CHAR, '"', '\'', '<')
        tokeniser.tag_pending.append_attr_name(name)
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f'or read_c == " ":
            tokeniser.move(AFTER_ATTR_NAME)
        elif read_c == "/":
            tokeniser.move(SELF_CLOSING_START_TAG)
        elif read_c == "=":
            tokeniser.move(BEFORE_ATTR_VALUE)
        elif read_c == ">":
            tokeniser.emit_tag_pending()
            tokeniser.move(DATA)
        elif read_c == NULL_CHAR:
            tokeniser.error("AttrNameState")
            tokeniser.tag_pending.append_attr_name(REPLACE_CHAR)
        elif read_c == reader.EOF:
            tokeniser.eof_error("AttrNameState")
            tokeniser.move(DATA)
        elif read_c == '"' or read_c == "'" or read_c == "<":
            tokeniser.error("AttrNameState")
            tokeniser.tag_pending.append_attr_name(read_c)


class AfterAttrNameState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f'or read_c == " ":
            return
        elif read_c == "/":
            tokeniser.move(SELF_CLOSING_START_TAG)
        elif read_c == "=":
            tokeniser.move(BEFORE_ATTR_VALUE)
        elif read_c == ">":
            tokeniser.emit_tag_pending()
            tokeniser.move(DATA)
        elif read_c == NULL_CHAR:
            tokeniser.error("AfterAttrNameState")
            tokeniser.tag_pending.append_attr_name(REPLACE_CHAR)
            tokeniser.move(ATTRIBUTE_NAME)
        elif read_c == reader.EOF:
            tokeniser.eof_error("AfterAttrNameState")
            tokeniser.move(DATA)
        elif read_c == '"' or read_c == "'" or read_c == "<":
            tokeniser.error("AfterAttrNameState")
            tokeniser.tag_pending.new_attribute()
            tokeniser.tag_pending.append_attr_name(read_c)
            token.move(ATTRIBUTE_NAME)
        else:
            tokeniser.tag_pending.new_attribute()
            reader.unconsume()
            tokeniser.move(ATTRIBUTE_NAME)


class BeforeAttrValueState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " ":
            return
        elif read_c == '"':
            tokeniser.move(ATTRIBUTE_VALUE_DOUBLE_QUOTED)
        elif read_c == "&":
            reader.unconsume()
            tokeniser.move(ATTRIBUTE_VALUE_UNQUOTED)
        elif read_c == "'":
            tokeniser.move(ATTRIBUTE_VALUE_SINGLE_QUOTED)
        elif read_c == NULL_CHAR:
            tokeniser.error("BeforeAttributeValue")
            tokeniser.tag_pending.append_attr_value(REPLACE_CHAR)
            tokeniser.move(ATTRIBUTE_VALUE_UNQUOTED)
        elif read_c == reader.EOF:
            tokeniser.eof_error("BeforeAttributeValue")
            tokeniser.emit_tag_pending()
            tokeniser.move(DATA)
        elif read_c == ">":
            tokeniser.error("BeforeAttributeValue")
            tokeniser.emit_tag_pending()
            tokeniser.move(DATA)
        elif read_c == "<" or read_c == "=":
            tokeniser.error("BeforeAttributeValue")
            tokeniser.tag_pending.append_attr_value(read_c)
            tokeniser.move(ATTRIBUTE_VALUE_UNQUOTED)
        else:
            reader.unconsume()
            tokeniser.move(ATTRIBUTE_VALUE_UNQUOTED)


class AttrValueUnquotedState(State):
    def read(self, reader, tokeniser):
        data = reader.consume_to_any_of(
            '\t', '\n', '\r', '\f', ' ', '&', '>', NULL_CHAR, '"', '\'', '<', '=', '`')
        if data:
            tokeniser.tag_pending.append_attr_value(data)
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " ":
            tokeniser.move(BEFORE_ATTR_NAME)
        elif read_c == "&":
            ref = tokeniser.consume_char_ref(">", True)
            if ref:
                tokeniser.tag_pending.append_attr_value(ref)
            else:
                tokeniser.tag_pending.append_attr_value("&")
        elif read_c == ">":
            tokeniser.emit_tag_pending()
            tokeniser.move(DATA)
        elif read_c == NULL_CHAR:
            tokeniser.error("AttrValueUnqoutedState")
            tokeniser.tag_pending.append_attr_value(REPLACE_CHAR)
        elif read_c == reader.EOF:
            tokeniser.eof_error("AttrValueUnqoutedState")
            tokeniser.move(DATA)
        elif read_c == '"' or read_c == "'" or read_c == "<" or read_c == "=" or read_c == '`':
            tokeniser.error("AttrValueUnqoutedState")
            tokeniser.tag_pending.append_attr_value(read_c)



class AttrValueSingleQuotedState(State):
    def read(self, reader, tokeniser):
        data = reader.consume_to_any_of('\'', '&', NULL_CHAR)
        if data:
            tokeniser.tag_pending.append_attr_value(data)
        else:
            tokeniser.tag_pending.set_empty_attr_value()
        read_c = reader.consume()
        if read_c == "'":
            tokeniser.move(AFTER_ATTR_VALUE_QUOTED)
        elif read_c == "&":
            ref = tokeniser.consume_char_ref("'", True)
            if ref:
                tokeniser.tag_pending.append_attr_value(ref)
            else:
                tokeniser.tag_pending.append_attr_value("&")
        elif read_c == NULL_CHAR:
            tokeniser.error("AttrValueSingleQuotedState")
            tokeniser.tag_pending.append_attr_value(REPLACE_CHAR)
        elif reader.EOF:
            tokeniser.eof_error("AttrValueSingleQuotedState")
            tokeniser.move(DATA)


class AttrValueDoubleQuotedState(State):
    def read(self, reader, tokeniser):
        data = reader.consume_to_any_of('"', '&', NULL_CHAR)
        if data:
            tokeniser.tag_pending.append_attr_value(data)
        else:
            tokeniser.tag_pending.set_empty_attr_value()
        read_c = reader.consume()
        if read_c == '"':
            tokeniser.move(AFTER_ATTR_VALUE_QUOTED)
        elif read_c == "&":
            ref = tokeniser.consume_char_ref('"', True)
            if ref:
                tokeniser.tag_pending.append_attr_value(ref)
            else:
                tokeniser.tag_pending.append_attr_value("&")
        elif read_c == NULL_CHAR:
            tokeniser.error("AttrValueDoubleQuotedState")
            tokeniser.tag_pending.append_attr_value(REPLACE_CHAR)
        elif reader.EOF:
            tokeniser.eof_error("AttrValueDoubleQuotedState")
            tokeniser.move(DATA)


class AfterAttrValueQuotedState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " ":
            tokeniser.move(BEFORE_ATTR_NAME)
        elif read_c == "/":
            tokeniser.move(SELF_CLOSING_START_TAG)
        elif read_c == ">":
            tokeniser.emit_tag_pending()
            tokeniser.move(DATA)
        elif read_c == reader.EOF:
            tokeniser.eof_error("AfterAttrValueQuotedState")
            tokeniser.move(DATA)
        else:
            tokeniser.error("AfterAttrValueQuotedState")
            reader.unconsume()
            tokeniser.move(BEFORE_ATTR_NAME)



class SelfClosingStartTagState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == ">":
            tokeniser.tag_pending.is_self_closing = True
            tokeniser.emit_tag_pending()
            tokeniser.move(DATA)
        elif read_c == reader.EOF:
            tokeniser.eof_error("SelfClosingStartTagState")
            tokeniser.move(DATA)
        else:
            tokeniser.error("SelfClosingStartTagState")
            reader.unconsume()
            tokeniser.move(BEFORE_ATTR_NAME)


class RawTextEndTagOpenState(State):
    def read(self, reader, tokeniser):
        if reader.match_letter():
            tokeniser.create_tag_pending()
            tokeniser.move(RAWTEXT_END_TAG_NAME)
        else:
            tokeniser.emit_string("</")
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
                tokeniser.emit_string("</" + tokeniser.script_buffer)
                reader.unconsume()
                tokeniser.move(RCDATA)
        elif read_c == "/":
            if tokeniser.approptiate_end_tag_token():
                tokeniser.move(SELF_CLOSING_START_TAG)
            else:
                tokeniser.emit_string("</" + tokeniser.script_buffer)
                reader.unconsume()
                tokeniser.move(RCDATA)
        elif read_c == ">":
            if tokeniser.approptiate_end_tag_token():
                tokeniser.emit_tag_pending()
                tokeniser.move(DATA)
            else:
                tokeniser.emit_string("</" + tokeniser.script_buffer)
                reader.unconsume()
                tokeniser.move(RCDATA)
        else:
            tokeniser.emit_string("</" + tokeniser.script_buffer)
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
            tokeniser.emit_string("</" + tokeniser.script_buffer)
            tokeniser.move(RAWTEXT)


class ScriptDataEndTagOpenState(State):
    def read(self, reader, tokeniser):
        if reader.match_letter():
            tokeniser.create_tag_pending()
            tokeniser.move(SCRIPT_DATA_END_TAG_NAME)
        else:
            tokeniser.emit_string("</")
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
            tokeniser.emit_string("</" + tokeniser.script_buffer)
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
            tokeniser.emit_string(data)


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
            tokeniser.emit_string(data)


class ScriptDataEscapedLessThanSignState(State):
    def read(self, reader, tokeniser):
        if reader.match_letter():
            tokeniser.script_buffer = ''
            tokeniser.script_buffer += reader.current()
            tokeniser.emit_string("<" + reader.current())
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
            tokeniser.emit_string("</" + tokeniser.script_buffer)
            tokeniser.move(SCRIPT_DATA_ESCAPED)



class ScriptDataDoubleEscapeStartState(State):
    def read(self, reader, tokeniser):
        if reader.match_letter():
            name = reader.consume_word()
            tokeniser.script_buffer += name
            tokeniser.emit_string(name)
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
            tokeniser.emit_string(data)


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
            tokeniser.move(SCRIPT_DATA_DOUBLE_ESCAPED_DASH_DASH)
        elif read_c == "<":
            tokeniser.emit(read_c)
            tokeniser.move(SCRIPT_DATA_DOUBLE_ESCAPED_LESS_THAN_SIGN)
        elif read_c == NULL_CHAR:
            tokeniser.error("ScriptDataDoubleEscapedDashState")
            tokeniser.emit(REPLACE_CHAR)
            tokeniser.move(SCRIPT_DATA_DOUBLE_ESCAPED)
        elif read_c == reader.EOF:
            tokeniser.eof_error("ScriptDataDoubleEscapedDashState")
            tokeniser.move(DATA)
        else:
            tokeniser.emit(read_c)
            tokeniser.move(SCRIPT_DATA_DOUBLE_ESCAPED)


"""class ScriptDataDoubleEscapedState(State):
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
            tokeniser.emit(data)"""


class ScriptDataDoubleEscapedDashDashState(State):
    def read(self, reader, tokeniser):
        read_c = reader.current()
        if read_c == "-":
            tokeniser.emit("-")
        elif read_c == "<":
            tokeniser.emit("<")
            tokeniser.move(SCRIPT_DATA_DOUBLE_ESCAPED_LESS_THAN_SIGN)
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
            tokeniser.emit_string(name)
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


class CommentStartState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == "-":
            tokeniser.move(COMMENT_START_DASH)
        elif read_c == ">":
            tokeniser.error("CommentStartState")
            tokeniser.emit_comment_pending()
            tokeniser.move(DATA)
        elif read_c == NULL_CHAR:
            tokeniser.error("CommentStartState")
            tokeniser.comment_pending.data += REPLACE_CHAR
            tokeniser.move(COMMENT)
        elif read_c == reader.EOF:
            tokeniser.eof_error("CommentStartState")
            tokeniser.emit_comment_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.comment_pending.data += read_c
            tokeniser.move(COMMENT)


class DoctypeState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " ":
            tokeniser.move(BEFORE_DOCTYPE_NAME)
        elif read_c == reader.EOF:
            tokeniser.eof_error("DoctypeState")
        elif read_c == ">":
            tokeniser.error("DoctypeState")
            tokeniser.create_doctype_pending()
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.error("DoctypeState")
            tokeniser.move(BEFORE_DOCTYPE_NAME)


class CommentStartDashState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == "-":
            tokeniser.move(COMMENT_START_DASH)
        elif read_c == ">":
            tokeniser.error("CommentStartDashState")
            tokeniser.emit_comment_pending()
            tokeniser.move(DATA)
        elif read_c == NULL_CHAR:
            tokeniser.error("CommentStartState")
            tokeniser.comment_pending.data += REPLACE_CHAR
            tokeniser.move(COMMENT)
        elif read_c == reader.EOF:
            tokeniser.eof_error("CommentStartDashState")
            tokeniser.emit_comment_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.comment_pending.data += read_c
            tokeniser.move(COMMENT)


class CommentState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == "-":
            tokeniser.move(COMMENT_END_DASH)
        elif read_c == NULL_CHAR:
            tokeniser.error("CommentState")
            tokeniser.comment_pending.data += REPLACE_CHAR
            reader.advance()
        elif read_c == reader.EOF:
            tokeniser.eof_error("CommentState")
            tokeniser.emit_comment_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.comment_pending.data += read_c
            tokeniser.comment_pending.data += reader.consume_to_any_of('-', NULL_CHAR)


class CommentEndDashState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == "-":
            tokeniser.move(COMMENT_END)
        elif read_c == NULL_CHAR:
            tokeniser.error("CommentEndDashState")
            tokeniser.comment_pending.data += REPLACE_CHAR
            reader.advance()
        elif read_c == reader.EOF:
            tokeniser.eof_error("CommentEndDashState")
            tokeniser.emit_comment_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.comment_pending.data += '-' + read_c
            tokeniser.move(COMMENT)


class CommentEndState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == ">":
            tokeniser.emit_comment_pending()
            tokeniser.move(DATA)
        elif read_c == NULL_CHAR:
            tokeniser.error("CommentEndState")
            tokeniser.comment_pending.data += "--" + REPLACE_CHAR
            tokeniser.move(COMMENT)
        elif read_c == "!":
            tokeniser.error("CommentEndState")
            tokeniser.move(COMMENT_END_BANG)
        elif read_c == "-":
            tokeniser.error("CommentEndState")
            tokeniser.comment_pending.data += "-"
        elif read_c == reader.EOF:
            tokeniser.eof_error("CommentEndState")
            tokeniser.emit_comment_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.error("CommentEndState")
            tokeniser.comment_pending.data += "--" + read_c
            tokeniser.move(COMMENT)


class CommentEndBangState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == ">":
            tokeniser.emit_comment_pending()
            tokeniser.move(DATA)
        elif read_c == NULL_CHAR:
            tokeniser.error("CommentEndBangState")
            tokeniser.comment_pending.data += "--!" + REPLACE_CHAR
            tokeniser.move(COMMENT)
        elif read_c == "-":
            tokeniser.comment_pending.data += "--!"
            tokeniser.move(COMMENT_END_DASH)
        elif read_c == reader.EOF:
            tokeniser.eof_error("CommentEndBangState")
            tokeniser.emit_comment_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.error("CommentEndBangState")
            tokeniser.comment_pending.data += "--!" + read_c
            tokeniser.move(COMMENT)


class BeforeDoctypeNameState(State):
    def read(self, reader, tokeniser):
        if reader.match_letter():
            tokeniser.create_doctype_pending()
            tokeniser.move(DOCTYPE_NAME)
            return
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " ":
            pass
        elif read_c == NULL_CHAR:
            tokeniser.error("BeforeDoctypeState")
            tokeniser.create_doctype_pending()
            tokeniser.doctype_pending.name += REPLACE_CHAR
            tokeniser.move(DOCTYPE_NAME)
        elif read_c == reader.EOF:
            tokeniser.eof_error("BeforeDoctypeState")
            tokeniser.create_doctype_pending()
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.create_doctype_pending()
            tokeniser.doctype_pending.name += read_c


class DoctypeNameState(State):
    def read(self, reader, tokeniser):
        if reader.match_letter():
            name = reader.consume_word()
            tokeniser.doctype_pending.name += name
            return
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " ":
            tokeniser.move(AFTER_DOCTYPE_NAME)
        elif read_c == ">":
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        elif read_c == NULL_CHAR:
            tokeniser.error("DoctypeNameState")
            tokeniser.doctype_pending.name += REPLACE_CHAR
        elif read_c == reader.EOF:
            tokeniser.eof_error("DoctypeNameState")
            tokeniser.create_doctype_pending()
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.doctype_pending.name += read_c


class AfterDoctypeNameState(State):
    def read(self, reader, tokeniser):
        if reader.empty():
            tokeniser.eof_error("AfterDoctypeNameState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
            return
        if reader.match_any_of('\t', '\n', '\r', '\f', ' '):
            reader.advance()
        elif reader.match('>'):
            tokeniser.emit_doctype_pending()
            tokeniser.move_to_state(DATA)
        elif reader.match_seq_ic("PUBLIC"):
            tokeniser.doctype_pending.pub_sys = "PUBLIC"
            tokeniser.move(AFTER_DOCTYPE_PUBLIC_KEY)
        elif reader.match_seq_ic("SYSTEM"):
            tokeniser.doctype_pending.pub_sys = "SYSTEM"
            tokeniser.move(AFTER_DOCTYPE_SYSTEM_KEY)
        else:
            tokeniser.error("AfterDoctypeNameState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.move_to_state(BOGUS_DOCTYPE)


class AfterDoctypePublicKeyState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " ":
            tokeniser.move(BEFORE_DOCTYPE_PUBLIC_ID)
        elif read_c == '"':
            tokeniser.error("AfterDoctypePublicState")
            tokeniser.move(DOCTYPE_PUBLIC_ID_DOUBLE_QUOTED)
        elif read_c == "'":
            tokeniser.error("AfterDoctypePublicState")
            tokeniser.move(DOCTYPE_PUBLIC_ID_SINGLE_QUOTED)
        elif read_c == ">":
            tokeniser.error("AfterDoctypePublicState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        elif read_c == reader.EOF:
            tokeniser.eof_error("AfterDoctypePublicState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.error("AfterDoctypePublicState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(BOGUS_DOCTYPE)


class AfterDoctypeSystemKeyState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " ":
            tokeniser.move(BEFORE_DOCTYPE_SYSTEM_ID)
        elif read_c == ">":
            tokeniser.error("AfterDoctypeSystemKeyState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        elif read_c == '"':
            tokeniser.error("AfterDoctypeSystemKeyState")
            tokeniser.move(DOCTYPE_SYSTEM_ID_DOUBLE_QUOTED)
        elif read_c == "'":
            tokeniser.error("AfterDoctypeSystemKeyState")
            tokeniser.move(DOCTYPE_SYSTEM_ID_SINGLE_QUOTED)
        elif read_c == reader.EOF:
            tokeniser.eof_error("AfterDoctypeSystemKeyState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.eof_error("AfterDoctypeSystemKeyState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()


class BogusDoctypeState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == ">" or read_c == reader.EOF:
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)


class BeforeDoctypePublicIdState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " ":
            pass
        elif read_c == '"':
            tokeniser.move(DOCTYPE_PUBLIC_ID_DOUBLE_QUOTED)
        elif read_c == "'":
            tokeniser.move(DOCTYPE_PUBLIC_ID_SINGLE_QUOTED)
        elif read_c == ">":
            tokeniser.error("BeforeDoctypePublicIdState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        elif read_c == reader.EOF:
            tokeniser.eof_error("BeforeDoctypePublicIdState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.eof_error("BeforeDoctypePublicIdState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.move(BOGUS_DOCTYPE)


class DoctypePublicIdDoubleQuotedState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == '"':
            tokeniser.move(AFTER_DOCTYPE_PUBLIC_ID)
        elif read_c == NULL_CHAR:
            tokeniser.error("DoctypePublicIdDoubleQuotedState")
            tokeniser.doctype_pending.public_identifier += REPLACE_CHAR
        elif read_c == ">":
            tokeniser.error("DoctypePublicIdDoubleQuotedState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        elif read_c == reader.EOF:
            tokeniser.eof_error("DoctypePublicIdDoubleQuotedState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.doctype_pending.public_identifier += read_c


class DoctypePublicIdSingleQuotedState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == "'":
            tokeniser.move(AFTER_DOCTYPE_PUBLIC_ID)
        elif read_c == NULL_CHAR:
            tokeniser.error("DoctypePublicIdSingleQuotedState")
            tokeniser.doctype_pending.public_identifier += REPLACE_CHAR
        elif read_c == ">":
            tokeniser.error("DoctypePublicIdSingleQuotedState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        elif read_c == reader.EOF:
            tokeniser.eof_error("DoctypePublicIdDoubleQuoted")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.doctype_pending.public_identifier += read_c


class AfterDoctypePublicIdState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " ":
            tokeniser.move(BETWEEN_PUB_AND_SYS_IDS)
        elif read_c == ">":
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        elif read_c == '"':
            tokeniser.error("AfterDoctypePublicIdState")
            tokeniser.move(DOCTYPE_SYSTEM_ID_DOUBLE_QUOTED)
        elif read_c == "'":
            tokeniser.error("AfterDoctypePublicIdState")
            tokeniser.move(DOCTYPE_SYSTEM_ID_SINGLE_QUOTED)
        elif read_c == reader.EOF:
            tokeniser.eof_error("AfterDoctypePublicIdState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.error("AfterDoctypePublicIdState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.move(BOGUS_DOCTYPE)


class BetweenPubAndSysIdsState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " ":
            pass
        elif read_c == ">":
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        elif read_c == '"':
            tokeniser.error("BetweenPubAndSysIdsState")
            tokeniser.move(DOCTYPE_SYSTEM_ID_DOUBLE_QUOTED)
        elif read_c == "'":
            tokeniser.error("BetweenPubAndSysIdsState")
            tokeniser.move(DOCTYPE_SYSTEM_ID_SINGLE_QUOTED)
        elif read_c == reader.EOF:
            tokeniser.eof_error("BetweenPubAndSysIdsState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.error("BetweenPubAndSysIdsState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.move(BOGUS_DOCTYPE)


class DoctypeSystemIdSingleQuoted(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == "'":
            tokeniser.move(AFTER_DOCTYPE_SYSTEM_ID)
        elif read_c == NULL_CHAR:
            tokeniser.error("DoctypeSystemIdDoubleQuoted")
            tokeniser.doctype_pending.system_identifier += REPLACE_CHAR
        elif read_c == ">":
            tokeniser.error("DoctypeSystemIdDoubleQuoted")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        elif read_c == reader.EOF:
            tokeniser.eof_error("DoctypeSystemIdDoubleQuoted")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.doctype_pending.system_identifier += read_c


class DoctypeSystemIdDoubleQuoted(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == '"':
            tokeniser.move(AFTER_DOCTYPE_SYSTEM_ID)
        elif read_c == NULL_CHAR:
            tokeniser.error("DoctypeSystemIdDoubleQuoted")
            tokeniser.doctype_pending.system_identifier += REPLACE_CHAR
        elif read_c == ">":
            tokeniser.error("DoctypeSystemIdDoubleQuoted")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        elif read_c == reader.EOF:
            tokeniser.eof_error("DoctypeSystemIdDoubleQuoted")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.doctype_pending.system_identifier += read_c


class BeforeDoctypeSystemIdState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " ":
            pass
        elif read_c == '"':
            tokeniser.move(DOCTYPE_SYSTEM_ID_DOUBLE_QUOTED)
        elif read_c == "'":
            tokeniser.move(DOCTYPE_SYSTEM_ID_SINGLE_QUOTED)
        elif read_c == ">":
            tokeniser.error("BeforeDoctypeSystemIdState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        elif read_c == reader.EOF:
            tokeniser.eof_error("BeforeDoctypeSystemIdState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.error("BeforeDoctypeSystemIdState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.move(BOGUS_DOCTYPE)


class AfterDoctypeSystemIdState(State):
    def read(self, reader, tokeniser):
        read_c = reader.consume()
        if read_c == '\t' or read_c == '\n' or read_c == '\r' or read_c == '\f' or read_c == " ":
            pass
        elif read_c == ">":
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        elif read_c == reader.EOF:
            tokeniser.eof_error("AfterDoctypeSystemIdState")
            tokeniser.doctype_pending.force_quirks = True
            tokeniser.emit_doctype_pending()
            tokeniser.move(DATA)
        else:
            tokeniser.error("AfterDoctypeSystemIdState")
            tokeniser.move(BOGUS_DOCTYPE)


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
ATTRIBUTE_NAME = AttrNameState()
AFTER_ATTR_NAME = AfterAttrNameState()
BEFORE_ATTR_VALUE = BeforeAttrValueState()
ATTRIBUTE_VALUE_UNQUOTED = AttrValueUnquotedState()
ATTRIBUTE_VALUE_SINGLE_QUOTED = AttrValueSingleQuotedState()
ATTRIBUTE_VALUE_DOUBLE_QUOTED = AttrValueDoubleQuotedState()
AFTER_ATTR_VALUE_QUOTED = AfterAttrValueQuotedState()
COMMENT_START = CommentStartState()
DOCTYPE = DoctypeState()
COMMENT_START_DASH = CommentStartDashState()
COMMENT = CommentState()
COMMENT_END_DASH = CommentEndDashState()
COMMENT_END = CommentEndState()
COMMENT_END_BANG = CommentEndBangState()
BEFORE_DOCTYPE_NAME = BeforeDoctypeNameState()
DOCTYPE_NAME = DoctypeNameState()
AFTER_DOCTYPE_NAME = AfterDoctypeNameState()
AFTER_DOCTYPE_PUBLIC_KEY = AfterDoctypePublicKeyState()
AFTER_DOCTYPE_SYSTEM_KEY = AfterDoctypeSystemKeyState()
BOGUS_DOCTYPE = BogusDoctypeState()
BEFORE_DOCTYPE_PUBLIC_ID = BeforeDoctypePublicIdState()
DOCTYPE_PUBLIC_ID_DOUBLE_QUOTED = DoctypePublicIdDoubleQuotedState()
DOCTYPE_PUBLIC_ID_SINGLE_QUOTED = DoctypePublicIdSingleQuotedState()
AFTER_DOCTYPE_PUBLIC_ID = AfterDoctypePublicIdState()
BETWEEN_PUB_AND_SYS_IDS = BetweenPubAndSysIdsState()
DOCTYPE_SYSTEM_ID_DOUBLE_QUOTED = DoctypeSystemIdDoubleQuoted()
DOCTYPE_SYSTEM_ID_SINGLE_QUOTED = DoctypeSystemIdSingleQuoted()
BEFORE_DOCTYPE_SYSTEM_ID = BeforeDoctypeSystemIdState()
AFTER_DOCTYPE_SYSTEM_ID = AfterDoctypeSystemIdState()

