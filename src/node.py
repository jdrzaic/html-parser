from abc import ABCMeta
import attributes as atr
import character_entities as ce
import util
import html_tag as ht


PUBLIC_KEY = "PUBLIC"
SYSTEM_KEY = "SYSTEM"
COMMENT_KEY = "comment"
DATA_KEY = "data"
PUB_SYS_KEY = "pub_sys"
PUBLIC_ID = "public_id"
SYSTEM_ID = "system_id"


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

    def remove(self):
        if not self.parent:
            return False
        self.parent.remove_child(self)

    def add__html_before(self, html):
        self.add_html_sibling(self.sibling_ind, html)

    def add_node_before(self, node):
        self.add_node_sibling(self.sibling_ind, node)

    def add_html_after(self, html):
        self.add_html_sibling(self.sibling_ind + 1, html)

    def add_node_after(self, node):
        self.add_node_sibling(self.sibling_ind + 1, node)

    def add_html_sibling(self, ind, html):
        pass

    def add_node_sibling(self, ind, node):
        pass

    def name(self):
        return "#node"


class Comment(Node):
    def __init__(self, data):
        super(Comment, self).__init__()
        self.attributes.attrs[COMMENT_KEY] = data
        self.data = data
        self.name = "#comment"

    def name(self):
        return "#comment"


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


class Element(Node):
    def __init__(self, tag_name=None, tag=None, attributes=None):
        self.name = "#element"
        if tag_name:
            tag = ht.Tag.value_of(tag_name)
            if tag:
                super(Element, self).__init__(atr.Attributes())
                self.tag = tag
        else:
            self.tag = tag
            self.attributes = attributes or atr.Attributes()

    def node_name(self):
        return self.tag.tag_lc_name

    def append_child(self, node):
        pass



class QuirksMode(object):
    NO_QUIRKS = 0
    QUIRKS = 1
    LIMITED_QUIRKS = 2


class Document(Element):

    def __init__(self, url):
        super(Document, self).__init__(tag=ht.Tag.value_of("#root"))
        self.force_quirks = QuirksMode.NO_QUIRKS
        self.location = url

    def append_child(self, node_to_add):
        pass


class FormElement(Element):
    def __init__(self, tag, attributes):
        super(FormElement, self).__init__(tag=tag, attributes=attributes)
        self.elements = []
