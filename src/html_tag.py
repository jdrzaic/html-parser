TAGS = dict()  # tags in HTML

BLOCK_TAGS = [
            "html", "head", "body", "frameset", "script", "noscript", "style", "meta", "link", "title", "frame",
            "noframes", "section", "nav", "aside", "hgroup", "header", "footer", "p", "h1", "h2", "h3", "h4", "h5", "h6",
            "ul", "ol", "pre", "div", "blockquote", "hr", "address", "figure", "figcaption", "form", "fieldset", "ins",
            "del", "dl", "dt", "dd", "li", "table", "caption", "thead", "tfoot", "tbody", "colgroup", "col", "tr", "th",
            "td", "video", "audio", "canvas", "details", "menu", "plaintext", "template", "article", "main",
            "svg", "math"
    ]
INLINE_TAGS = [
            "object", "base", "font", "tt", "i", "b", "u", "big", "small", "em", "strong", "dfn", "code", "samp", "kbd",
            "var", "cite", "abbr", "time", "acronym", "mark", "ruby", "rt", "rp", "a", "img", "br", "wbr", "map", "q",
            "sub", "sup", "bdo", "iframe", "embed", "span", "input", "select", "textarea", "label", "button", "optgroup",
            "option", "legend", "datalist", "keygen", "output", "progress", "meter", "area", "param", "source", "track",
            "summary", "command", "device", "area", "basefont", "bgsound", "menuitem", "param", "source", "track",
            "data", "bdi", "s"
    ]
EMPTY_TAGS = [
            "meta", "link", "base", "frame", "img", "br", "wbr", "embed", "hr", "input", "keygen", "col", "command",
            "device", "area", "basefont", "bgsound", "menuitem", "param", "source", "track"
    ]
FORMAT_AS_INLINE = [
            "title", "a", "p", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "address", "li", "th", "td", "script", "style",
            "ins", "del", "s"
    ]
PRESERVE_WHITESPACE_TAGS = [
            "pre", "plaintext", "title", "textarea"
    ]
FORM_LISTED_TAGS = [
            "button", "fieldset", "input", "keygen", "object", "output", "select", "textarea"
    ]
FORM_SUBMIT_TAGS = [
            "input", "keygen", "object", "select", "textarea"
    ]

SPECIAL_TAGS = ["address", "applet", "area", "article", "aside", "base", "basefont", "bgsound",
            "blockquote", "body", "br", "button", "caption", "center", "col", "colgroup", "command", "dd",
            "details", "dir", "div", "dl", "dt", "embed", "fieldset", "figcaption", "figure", "footer", "form",
            "frame", "frameset", "h1", "h2", "h3", "h4", "h5", "h6", "head", "header", "hgroup", "hr", "html",
            "iframe", "img", "input", "isindex", "li", "link", "listing", "marquee", "menu", "meta", "nav",
            "noembed", "noframes", "noscript", "object", "ol", "p", "param", "plaintext", "pre", "script",
            "section", "select", "style", "summary", "table", "tbody", "td", "textarea", "tfoot", "th", "thead",
            "title", "tr", "ul", "wbr", "xmp"]


class Tag(object):

    def __init__(self, tag_name):
        self.tag_name = tag_name
        self.block = False
        self.empty = False  #empty tags (img)
        self.self_closing = False
        self.form_list = False
        self.form_submit = False
        self.preserve_white = False

    @classmethod
    def value_of(cls, tag_name):
        if tag_name in TAGS:
            return TAGS[tag_name]
        tag = Tag(tag_name)
        tag.block = False
        return tag


def initialize_tags():
    for tag_name in BLOCK_TAGS:
        tag = Tag(tag_name)
        tag.block = True
        TAGS[tag_name] = tag
    for tag_name in INLINE_TAGS:
        tag = Tag(tag_name)
        tag.block = False
        TAGS[tag_name] = tag
    for tag_name in EMPTY_TAGS:
        tag = TAGS[tag_name]
        tag.can_contain_inline = True
        tag.empty = True
    for tag_name in PRESERVE_WHITESPACE_TAGS:
        tag = TAGS[tag_name]
        tag.preserve_white = True
    for tag_name in FORM_LISTED_TAGS:
        tag = TAGS[tag_name]
        tag.form_list = True
    for tag_name in FORM_SUBMIT_TAGS:
        tag = TAGS[tag_name]
        tag.form_submit = True

