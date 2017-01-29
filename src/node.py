from abc import ABCMeta
import attributes as atr
import character_entities as ce
import util
import html_tag as ht
import re

PUBLIC_KEY = "PUBLIC"
SYSTEM_KEY = "SYSTEM"
COMMENT_KEY = "comment"
DATA_KEY = "data"
PUB_SYS_KEY = "pub_sys"
PUBLIC_ID = "public_id"
SYSTEM_ID = "system_id"
# Whether to show whitespace nodes or not
SHOW_WHITESPACE_NODE = False

class Node(object):
    __metaclass__ = ABCMeta

    def __init__(self, attributes=None):
        self.children = []
        self.parent = None
        if attributes:
            self.attributes = attributes
        else:
            self.attributes = atr.Attributes()
        self.sibling_ind = None

    def root(self):
        curr = self
        while curr.parent:
            curr = curr.parent
        return curr

    def add_children(self, index, nodes):
        for child in nodes:
            self.reparent(child)
            self.children.insert(index, child)
            self.reindex(index)

    def remove_child(self, out):
        if not out.parent == self:
            return
        self.children.pop(out.sibling_ind)
        self.reindex(out.sibling_ind)
        out.parent = None

    def before(self, node):
        self.parent.add_children(self.sibling_ind, [node])
        return self

    def remove(self):
        if not self.parent:
            return False
        self.parent.remove_child(self)

    def name(self):
        return "#node"

    def reparent(self, node):
        if node.parent:
            node.parent.remove_child(node)
        node.parent = self

    def reindex(self, index):
        for i in range(index, len(self.children)):
            self.children[i].sibling_ind = i

    def indent(self, to_indend, depth=0):
        offset = depth * "\t"
        indeneted = to_indend.replace("\n", "\n" + offset)
        return indeneted

    def get_attributes(self):
        attrs = self.attributes.attrs.values()
        node_html = "\n"
        for attribute in attrs:
            node_html = "{0}\n{1}\nKey: {2}, Value: {3}\n".format(
                node_html, "Attribute:", attribute.key, attribute.value
            )
        return node_html


class Comment(Node):
    def __init__(self, data):
        super(Comment, self).__init__()
        self.attributes.attrs[COMMENT_KEY] = data
        self.data = data
        self.name = "#comment"

    def name(self):
        return "#comment"

    def get_html(self, depth=0):
        return "\nComment Node:\nData: {0}\n".format(self.data)


class Data(Node):
    def __init__(self, data):
        super(Data, self).__init__()
        self.attributes.attrs[DATA_KEY] = data
        self.name = "#data"

    @classmethod
    def create_from_encoded(cls, encoded_data):
        data = ce.Entities.unescape(encoded_data, False)
        return Data(data)

    def name(self):
        return "#data"

    def get_html(self, depth=0):
        return "\nData Node:\nData: {0}\n".format(self.attributes.attrs[DATA_KEY])


class DocumentType(Node):
    def __init__(self, name, public_id, system_id, pub_sys=None):
        super(DocumentType, self).__init__()
        self.name = "#documenttype"
        self.attributes.attrs["name"] = name
        self.attributes.attrs["public_id"] = public_id
        self.attributes.attrs["system_id"] = system_id
        if pub_sys:
            self.attributes.attrs["pub_sys"] = pub_sys
        elif public_id:
            self.attributes.attrs["pub_sys"] = "PUBLIC"

    def name(self):
        return "#documenttype"

    def get_html(self, depth=0):
        node_html = "\nDocumentType Node: {0}\n".format(self.attributes.attrs["name"])
        keys = []
        if self.attributes.attrs["public_id"]:
            node_html = "{0}\Attribute:\nKey: PUBLIC, Value: {1}\n".format(
                node_html, self.attributes.attrs["public_id"]
            )
        elif self.attributes.attrs["system_id"]:
            node_html = "{0}\Attribute:\nKey: SYSTEM, Value: {1}\n".format(
                node_html, self.attributes.attrs["system_id"]
            )
        return node_html


class Text(Node):
    def __init__(self, text):
        super(Text, self).__init__()
        self.text = text
        self.name = "#text"
        self.attributes.attrs["text"] = text

    def name(self):
        return "#text"

    def get_normalized(self):
        return util.OutputPrinter.normalize_whitespace(self.text)

    def create_with_text(self, text):
        self.text = text
        self.attributes.attrs["text"] = text
        return self

    def text(self):
        if "text" in self.attributes.attrs.keys():
            return self.attributes.attrs["text"]
        return self.text

    def split_text(self, offset):
        first = self.text[:offset]
        second = self.text[offset:]
        self.create_with_text(first)
        second_node = Text(second)
        if self.parent:
            self.add_node_after(second_node)
        return second_node

    @classmethod
    def create_from_encoded(cls, text):
        text = ce.Entities.unescape(text, False)
        return Text(text)

    def get_html(self):
        node_html = "\n"
        if not SHOW_WHITESPACE_NODE and self.get_normalized() == " ":
            return node_html
        node_html = "Text Node:\nData: {0}\n".format(self.text)
        return node_html


class Element(Node):
    def __init__(self, tag_name=None, tag=None, attributes=None):
        self.name = "#element"
        if tag_name:
            tag = ht.Tag.value_of(tag_name)
            if tag:
                super(Element, self).__init__(atr.Attributes())
                self.tag = tag
        else:
            super(Element, self).__init__(attributes or atr.Attributes())
            self.tag = tag

    def node_name(self):
        return self.tag.tag_name

    def append_child(self, node):
        self.reparent(node)
        self.children.append(node)
        node.sibling_ind = len(self.children) - 1

    def get_html(self, depth=0):
        node_html = "\nElement Node:\nName: {0}\n".format(self.tag.tag_name)
        node_html = "{0}{1}".format(node_html, self.get_attributes())
        for child in self.children:
            node_html = "{0}{1}".format(node_html, self.indent(child.get_html(), 1))
        return node_html


class QuirksMode(object):
    NO_QUIRKS = 0
    QUIRKS = 1
    LIMITED_QUIRKS = 2


class Document(Element):

    def __init__(self):
        super(Document, self).__init__(tag=ht.Tag.value_of("#root"))
        self.force_quirks = QuirksMode.NO_QUIRKS

    def get_html(self, depth=0):
        node_html = "\nDocument:\n"
        node_html = "{0}{1}".format(node_html, self.get_attributes())
        for child in self.children:
            node_html = "{0}{1}".format(node_html, self.indent(child.get_html(), 1))
        node_html = re.sub(r'\n\s*\n', '\n\n', node_html)
        return node_html


class FormElement(Element):
    def __init__(self, tag, attributes):
        super(FormElement, self).__init__(tag=tag, attributes=attributes)
        self.elements = []

    def add_element(self, node):
        self.elements.append(node)
        return self

    def get_html(self, depth=0):
        node_html = "\nFormElement Node:\n"
        node_html = "{0}{1}".format(node_html, self.get_attributes())
        for child in self.children:
            node_html = "{0}{1}".format(node_html, self.indent(child.get_html(), 1))
        for element in self.elements:
            node_html = "{0}{1}".format(node_html, self.indent(element.get_html(), 1))
        return node_html