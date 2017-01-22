from abc import ABCMeta
from cStringIO import StringIO

import attributes


class TokenType(object):
    NO_TYPE = 0
    START_TAG = 1
    END_TAG = 2
    CHARACTER = 3
    COMMENT = 4
    DOCTYPE = 5
    EOF = 6


class Token(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.type = 0

    def get_type(self):
        return self.type


class DoctypeToken(Token):

    def __init__(self):
        Token.__init__()
        self.public_identifier = StringIO()
        self.system_identifier = StringIO()
        self.name = StringIO()
        self.sys_key = ''
        self.type = TokenType.DOCTYPE
        self.force_quirks = False


class TagToken(Token):
    __metaclass__ = ABCMeta

    def __init__(self):
        Token.__init__()
        self.tag_name = ''
        self.tag_lc_name = ''
        self.pending_attr_name = ''
        self.pending_attr_value = StringIO()
        self.is_empty_attr_name = False
        self.is_empty_attr_value = False
        self.is_self_closing = False
        self.attrs = attributes.Attributes()

    def new_attribute(self):
        if self.pending_attr_name.strip():
            if self.pending_attr_value:
                attribute = attributes.Attribute(self.pending_attr_name,self.pending_attr_value)
            elif self.is_empty_attr_value:
                attribute = attributes.Attribute(self.pending_attr_name, "")
            else:
                attribute = attributes.BoolAttribute(self.pending_attr_name)
            attributes[self.pending_attr_name] = attribute
        self.pending_attr_name = ''
        self.pending_attr_value = StringIO()
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
    def __init__(self, name, attrs):
        TagToken.__init__()
        self.type = TokenType.START_TAG
        self.attrs = attrs
        self.name = name
        self.tag_lc_name = name.lower()

    def __str__(self):
        return "<" + self.name + " " + self.attrs + ">"


class EndTagToken(TagToken):
    def __init__(self):
        TagToken.__init__()
        self.type == TokenType.END_TAG

    def __str__(self):
        return "</" + self.name + ">"


class CommentToken(Token):
    def __init__(self):
        self.data = ''
        self.bogus = False

    def __str__(self):
        return "<!--" + self.data + "-->"


class CharacterToken(Token):

    def __init__(self):
        Token.__init__()
        self.type = TokenType.CHARACTER
        self.data = ''

    def __str__(self):
        return self.data


class EOFToken(Token):
    def __init__(self):
        self.type = TokenType.EOF