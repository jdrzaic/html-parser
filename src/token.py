from abc import ABCMeta
import attributes


class TokenType(object):
    NO_TYPE = "no_type"
    START_TAG = "start_tag"
    END_TAG = "end_tag"
    CHARACTER = "character_token"
    COMMENT = "comment_token"
    DOCTYPE = "doctype_token"
    EOF = "eof_token"


class Token(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.type = 0

    def get_type(self):
        return self.type


class DoctypeToken(Token):

    def __init__(self):
        super(DoctypeToken, self).__init__()
        self.public_identifier = ''
        self.system_identifier = ''
        self.name = ''
        self.sys_key = ''
        self.type = TokenType.DOCTYPE
        self.force_quirks = False

    def token_name(self):
        return self.name.lower()

    def __str__(self):
        doc_str = "<!DOCTYPE " + "PUBLIC \"{0}\"".format(self.public_identifier) if self.public_identifier else ""
        doc_str += " SYSTEM \"{0}\"".format(self.system_identifier) if self.system_identifier else ""
        return doc_str + ">" if doc_str else ""


class TagToken(Token):
    __metaclass__ = ABCMeta

    def __init__(self):
        super(TagToken, self).__init__()
        self.tag_name = ''
        self.tag_lc_name = ''
        self.pending_attr_name = ''
        self.pending_attr_value = ''
        self.is_empty_attr_name = False
        self.is_empty_attr_value = False
        self.is_self_closing = False
        self.attrs = attributes.Attributes()

    def token_name(self):
        return self.tag_lc_name

    def new_attribute(self):
        if self.pending_attr_name.strip():
            if self.pending_attr_value:
                attribute = attributes.Attribute(self.pending_attr_name,self.pending_attr_value)
            elif self.is_empty_attr_value:
                attribute = attributes.Attribute(self.pending_attr_name, "")
            else:
                attribute = attributes.BoolAttribute(self.pending_attr_name)
            self.attrs.attrs[self.pending_attr_name] = attribute
        self.pending_attr_name = ''
        self.pending_attr_value = ''
        self.is_empty_attr_value = False
        self.is_empty_attr_name = False

    def finalise_tag(self):
        if self.pending_attr_name:
            self.new_attribute()

    def set_name_lc(self):
        self.tag_lc_name = self.tag_name.lower()
        return self

    def append_tag_name(self, append):
        self.tag_name = "{0}{1}".format(self.tag_name, append)
        self.tag_lc_name = self.tag_name.lower()

    def append_attr_name(self, append):
        self.pending_attr_name = "{0}{1}".format(self.pending_attr_name, append)

    def append_attr_value(self, append):
        self.pending_attr_value = "{0}{1}".format(self.pending_attr_value, append)

    def set_empty_attr_value(self):
        self.is_empty_attr_value = True


class StartTagToken(TagToken):
    def __init__(self, name='', attrs=attributes.Attributes()):
        super(StartTagToken, self).__init__()
        self.type = TokenType.START_TAG
        self.attrs = attrs
        self.tag_name = name
        self.tag_lc_name = name.lower()

    def __str__(self):
        return "<" + self.tag_name + "" + self.attrs.__str__() + ">"


class EndTagToken(TagToken):
    def __init__(self, name=''):
        super(EndTagToken, self).__init__()
        self.type = TokenType.END_TAG
        self.tag_name = name
        self.tag_lc_name = name.lower()

    def __str__(self):
        return "</" + self.tag_name + ">"


class CommentToken(Token):
    def __init__(self):
        super(CommentToken, self).__init__()
        self.data = ''
        self.bogus = False
        self.type = TokenType.COMMENT

    def __str__(self):
        return "<!--" + self.data + "-->"


class CharacterToken(Token):

    def __init__(self):
        super(CharacterToken, self).__init__()
        self.type = TokenType.CHARACTER
        self.data = ''

    def __str__(self):
        return self.data


class EOFToken(Token):
    def __init__(self):
        super(EOFToken, self).__init__()
        self.type = TokenType.EOF

    def __str__(self):
        return "EOFToken"