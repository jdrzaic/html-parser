import character_entities as ce


BOOLEAN_ATTRS = ["allowfullscreen", "async", "autofocus", "checked", "compact", "declare",
                 "default", "defer", "disabled", "formnovalidate", "hidden", "inert", "ismap",
                 "itemscope", "multiple", "muted", "nohref", "noresize", "noshade",
                 "novalidate", "nowrap", "open", "readonly", "required", "reversed", "seamless",
                 "selected", "sortable", "truespeed", "typemustmatch"]


DATA_PREFIX = 'data-'


class Attribute(object):

    def __init__(self, key, value):
        self.key = key.strip()
        self.value = value
        if not self.key or self.value is None:
            raise ValueError('attribute key or value empty')

    def get_html(self):
        # needs entity escaping
        return self.key + '="' + self.value + '"'

    def will_collapse(self):
        return (self.value == "" or self.value == self.key) \
               and self.key in BOOLEAN_ATTRS

    def value_lc(self):
        return self.value.lower()

    def key_lc(self):
        return self.key.lower()

    def is_data_attr(self):
        return self.key.startswith(DATA_PREFIX) and len(self.key) > len(DATA_PREFIX)

    def __str__(self):
        return self.get_html()

    def create_from_encoded(self, unencoded_key, encoded_value):
        val = ce.Entities.unescape(encoded_value)
        return Attribute(unencoded_key, val)

    def is_bool_attr(self):
        return self.key in BOOLEAN_ATTRS


class BoolAttribute(Attribute):

    def __init__(self, key):
        super(BoolAttribute, self).__init__(key, "")

    def get_html(self):
        return self.key

    def __str__(self):
        return self.key


class Attributes(object):

    def __init__(self):
        self.attrs = dict()

    def get_value(self, key):
        if key in self.attrs.keys():
            return self.attrs.get(key).value
        return None

    def get_value_ignore_key_case(self, key):
        for attr_key in self.attrs.keys():
            if key.lower() == attr_key.lower():
                return self.attrs.get(key).value
        return ""

    def has_key_ignore_key_case(self, key):
        for attr_key in self.attrs.keys():
            if key.lower() == attr_key.lower():
                return True
        return False

    def get_html(self):
        content = ''
        for attr_key in self.attrs:
            attr = self.attrs.get(attr_key)
            content += " "
            content += attr.get_html()
        return content

    def __str__(self):
        return self.get_html()