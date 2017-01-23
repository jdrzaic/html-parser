import node
from abc import ABCMeta
import token as t
import token_state


class State(object):
    __metaclass__ = ABCMeta

    def process_token(self, token, tree_builder):
        pass

    def is_white(self, t):
        pass

    def handle_rcdata(self, token, tree_builder):
        pass

    def handle_rawtext(self, token, tree_builder):
        pass


class InitialState(State):
    def process_token(self, token, tree_builder):
        if self.is_white(token):
            return True
        elif token.type == t.TokenType.COMMENT:
            tree_builder.insert(token)
        elif token.type == t.TokenType.DOCTYPE:
            document_type = node.DocumentType(
                token.name, token.public_identifier, token.system_identifier, token.sys_key)
            tree_builder.doc.append_child(document_type)
            if token.force_quirks:
                tree_builder.doc.quirks_mode = node.QuirksMode.QUIRKS
            tree_builder.move(BEFORE_HTML)
        else:
            tree_builder.move(BEFORE_HTML)
            return tree_builder.process_token(token)
        return True


class BeforeHtmlState(State):
    def process_token(self, token, tree_builder):
        if token.type == t.TokenType.DOCTYPE:
            tree_builder.error("BeforeHtmlState")
            return False
        elif token.type == t.TokenType.COMMENT:
            tree_builder.insert(token)
        elif self.is_white(token):
            return True
        elif token.type == t.TokenType.START_TAG and token.tag_lc_name == "html":
            tree_builder.insert(token)
            tree_builder.move(BEFORE_HEAD)
        elif token.type == t.TokenType.END_TAG and token.tag_lc_name in ["head", "html", "body", "br"]:
            tree_builder.insert_start("html")
            tree_builder.move(BEFORE_HEAD)
            return tree_builder.process_token(token)
        elif token.type == t.TokenType.END_TAG:
            tree_builder.error("BeforeHtmlState")
            return False
        else:
            tree_builder.insert_start("html")
            tree_builder.move(BEFORE_HEAD)
            return tree_builder.process_token(token)
        return True


class BeforeHeadState(State):
    def process_token(self, token, tree_builder):
        if self.is_white(token):
            return True
        elif token.type == t.TokenType.COMMENT:
            tree_builder.insert(token)
        elif token.type == t.TokenType.DOCTYPE:
            tree_builder.error("BeforeHeadState")
            return False
        elif token.type == t.TokenType.START_TAG and token.tag_lc_name == "html":
            head = tree_builder.insert(token)
            tree_builder.set_head(head)
            tree_builder.move(IN_HEAD)
        elif token.type == t.TokenType.END_TAG and token.tag_lc_name in ["head", "html", "body", "br"]:
            tree_builder.process_start("head")
            tree_builder.process(token)
        elif token.type == t.TokenType.END_TAG:
            tree_builder.error("BeforeHeadState")
            return False
        else:
            tree_builder.process_start("head")
            return tree_builder.process(token)
        return True


class InHeadState(State):

    def process_token(self, token, tree_builder):
        if self.is_white(token):
            tree_builder.insert(token)
            return True
        if token.type == t.TokenType.COMMENT:
            tree_builder.insert(token)
        elif token.type == t.TokenType.DOCTYPE:
            tree_builder.error("InHeadState")
        elif token.type == t.TokenType.START_TAG:
            name = token.tag_lc_name
            if name == "html":
                return IN_BODY.process_token(token, tree_builder)
            elif name in ["base", "basefont", "bgsound", "command", "link"]:
                elem = tree_builder.insert_empty(token)
                if name == "base" and "href" in elem.attributes.attrs.keys():
                    tree_builder.set_base_url(elem)
            elif name == "meta":
                meta = tree_builder.insert_empty(token)
            elif name == "title":
                self.handle_rcdata(token, tree_builder)
            elif name in ["noframes", "style"]:
                self.handle_rawtext(token, tree_builder)
            elif name == "noscript":
                tree_builder.insert(token)
                tree_builder.move(IN_HEAD_NOSCRIPT)
            elif name == "script":
                tree_builder.tokeniser.move(token_state.SCRIPT_DATA)
                tree_builder.mark_insertion()
                tree_builder.move(TEXT)
                tree_builder.insert(token)
            elif name == "head":
                tree_builder.error("InHeadState")
                return False
            else:
                tree_builder.process_end("head")
                return tree_builder.process_token(token)
        elif token.type == t.TokenType.END_TAG:
            name = token.tag_lc_name
            if name == "head":
                tree_builder.pop()
                tree_builder.move(AFTER_HEAD)
            elif name in ["body", "html", "br"]:
                tree_builder.process_end("head")
                return tree_builder.process_token(token)
            else:
                tree_builder.error("InHeadState")
                return False
        else:
            tree_builder.process_end("head")
            return tree_builder.process_token(token)
        return True


class InBodyState(State):
    def process_token(self, token, tree_builder):
        if token.type == t.TokenType.CHARACTER:
            if not token.data:
                return False
            elif tree_builder.frameset() and self.is_white(token):
                tree_builder.reconstruct_formatting()
                tree_builder.insert(token)
            else:
                tree_builder.reconstruct_formatting()
                tree_builder.insert(token)
                tree_builder.frameset()
        elif token.type == t.TokenType.COMMENT:
            tree_builder.insert(token)
        elif token.type == t.TokenType.DOCTYPE:
            tree_builder.error("InBodyState")
            return False
        elif token.type == t.TokenType.START_TAG:
            name = token.tag_lc_name
            if name == "a":
                if tree_builder.active_formatting_elem():
                    tree_builder.error("InBodyState")
                    tree_builder.process_end("a")
                    remaining_a = tree_builder.get_from_stack("a")
                    if remaining_a:
                        tree_builder.remove_from_active_formatting(remaining_a)
                        tree_builder.remove_from_stack(remaining_a)
                tree_builder.reconstruct_formatting()
                a = tree_builder.insert(token)
                tree_builder.push_active_formatting(a)
            elif name in ["area", "br", "embed", "img", "keygen", "wbr"]:
                tree_builder.reconstruct_formatting()
                tree_builder.insert_empty(token)
                tree_builder.frameset(False)
            elif name in ["address", "article", "aside", "blockquote", "center", "details", "dir", "div", "dl",
                "fieldset", "figcaption", "figure", "footer", "header", "hgroup", "menu", "nav", "ol",
                "p", "section", "summary", "ul"]:
                if tree_builder.in_button_scope("p"):
                    tree_builder.process_end("p")
                tree_builder.insert(token)
            elif name == "span":
                tree_builder.reconstruct_formatting()
                tree_builder.insert(token)
            elif name == "li":
                tree_builder.frameset()
                stack = tree_builder.stack
                for i in range(len(stack)):
                    el = stack.get(len(stack) - 1 - i)
                    if el.name == "li":
                        tree_builder.process_end("li")
                        break
                    if tree_builder.is_special(el) and not el.name in ["address", "div", "p"]:
                        break
                if tree_builder.in_button_scope("p"):
                    tree_builder.process_end("p")
                tree_builder.insert(token)
            elif name == "html":
                return False
            elif name in ["base", "basefont", "bgsound", "command", "link", "meta", "noframes",
                          "script", "style", "title"]:
                return tree_builder.process_token(token, IN_HEAD)
            elif name == "body":
                return False
            elif name == "frameset":
                return False
            elif name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                if tree_builder.in_button_scope("p"):
                    tree_builder.process_end("p")
                if tree_builder.current_element().name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    tree_builder.pop()
                tree_builder.insert(token)
            elif name in ["pre", "listing"]:
                if tree_builder.in_button_scope("p"):
                    tree_builder.process_end("p")
                tree_builder.insert(token)
                tree_builder.frameset(False)
            elif name == "form":
                if tree_builder.in_button_scope("p"):
                    tree_builder.process_end("p")
                tree_builder.insert_form(token, True)
            elif name in ["dd", "dt"]:
                tree_builder.frameset(False)
                stack = tree_builder.stack
                for i in range(len(stack)):
                    el = stack.get(len(stack) - 1 - i)
                    if el.name in ["dd", "dt"]:
                        tree_builder.process_end(el.name)
                        break
                    if tree_builder.is_special(el) and not el.name in ["address", "div", "p"]:
                        break
                if tree_builder.in_button_scope("p"):
                    tree_builder.process_end("p")
                tree_builder.insert(token)
            elif name == "plaintext":
                if tree_builder.in_button_scope("p"):
                    tree_builder.process_end("p")
                tree_builder.insert(token)
                tree_builder.tokeniser.move(token_state.PlaintextState())
            elif name == "button":
                if tree_builder.in_button_scope("button"):
                    return False
                else:
                    tree_builder.reconstruct_formatting()
                    tree_builder.insert(token)
                    tree_builder.frameset(False)
            elif name in ["b", "big", "code", "em", "font", "i", "s", "small", "strike", "strong", "tt", "u"]:
                tree_builder.reconstruct_formatting()
                tree_builder.insert_empty(token)
                tree_builder.frameset(False)
            elif name in ["applet", "marquee", "object"]:
                tree_builder.reconstruct_formatting()
                tree_builder.insert(token)
                tree_builder.insert_marker_to_formatting()
                tree_builder.frameset()
            elif name == "table":
                if tree_builder.doc.quirks_mode != node.QuirksMode.QUIRKS and tree_builder.in_button_scope("p"):
                    tree_builder.process_end("p")
                tree_builder.insert(token)
                tree_builder.frameset(False)
                tree_builder.move(IN_TABLE)
            elif name == "input":
                tree_builder.reconstruct_formatting()
                el = tree_builder.insert_empty(token)
                if not el.attributes.attrs["type"].lower() == "hidden":
                    tree_builder.frameset(False)
            elif name in ["param", "source", "track"]:
                tree_builder.insert_empty(token)
            elif name == "hr":
                if tree_builder.in_button_scope("p"):
                    tree_builder.process_end("p")
                tree_builder.insert_empty(token)
                tree_builder.frameset(False)
            elif name == "image":
                if not tree_builder.get_from_stack("svg"):
                    token.tag_name = "img"
                    return tree_builder.process_token(token)
                else:
                    tree_builder.insert(token)
            elif name == "textarea":
                tree_builder.insert(token)
                tree_builder.tokeniser.move(token_state.RCDATA)
                tree_builder.mark_insertion()
                tree_builder.frameset(False)
                tree_builder.move(TEXT)
            else:
                tree_builder.reconstruct_formatting()
                tree_builder.insert(token)
        elif token.type == t.TokenType.END_TAG:
            











class InHeadNoScriptState(State):
    def process_token(self, token, tree_builder):
        if token.type == t.TokenType.DOCTYPE:
            tree_builder.error("BeforeHeadState")
        elif token.type == t.TokenType.START_TAG and token.tag_lc_name == "html":
            return tree_builder.process(token, IN_BODY)
        elif token.type == t.TokenType.END_TAG and token.tag_lc_name == "noscript":
            tree_builder.pop()
            tree_builder.move(IN_HEAD)
        elif self.is_white(token) or token.type == t.TokenType.COMMENT or (
                        token.type == t.TokenType.START_TAG and token.tag_lc_name in [
                    "basefont", "bgsound", "link", "meta", "noframes", "style"]):
            return tree_builder.process_token(token, IN_HEAD)
        elif token.type == t.TokenType.END_TAG and token.tag_lc_name == "br":
            tree_builder.error("InHeadNoScriptState")
            ch_token = t.CharacterToken()
            ch_token.data = token.__str__()
            tree_builder.insert(ch_token)
        elif token.type == t.TokenType.START_TAG and token.tag_lc_name in [
            "head", "noscript"] or token.type == t.TokenType.END_TAG:
            tree_builder.error("InHeadNoScriptState")
            return False
        else:
            tree_builder.error("InHeadNoScriptState")
            ch_token = t.CharacterToken()
            ch_token.data = token.__str__()
            tree_builder.insert(ch_token)
        return True


class TextState(State):
    pass


class AfterHeadState(State):
    def process_token(self, token, tree_builder):
        if self.is_white(token):
            tree_builder.insert(token)
        elif token.type == t.TokenType.COMMENT:
            tree_builder.insert(token)
        elif token.type == t.TokenType.DOCTYPE:
            tree_builder.error("AfterHeadState")
        elif token.type == t.TokenType.START_TAG:
            name = token.tag_lc_name
            if name == "html":
                return tree_builder.process_token(token, IN_BODY)
            elif name == "body":
                tree_builder.insert(token)
                tree_builder.frameset()
                tree_builder.move(IN_BODY)
            elif name == "frameset":
                tree_builder.insert(token)
                tree_builder.move(IN_FRAMESET)
            elif name in ["base", "basefont", "bgsound", "link", "meta",
                          "noframes", "script", "style", "title"]:
                tree_builder.error("AfterHeadState")
                head = tree_builder.head()
                tree_builder.push(head)
                tree_builder.process_token(token, IN_HEAD)
                tree_builder.remove_from_stack(head)
            elif name == "head":
                tree_builder.error("AfterHeadState")
                return False
            else:
                tree_builder.process_start("body")
                tree_builder.frameset(True)
                return tree_builder.process_token(token)
        elif token.type == t.TokenType.END_TAG:
            if token.tag_lc_name in ["body", "html"]:
                tree_builder.process_start("body")
                tree_builder.frameset(True)
                return tree_builder.process_token(token)
            else:
                tree_builder.error("AfterHeadState")
                return False
        else:
            tree_builder.process_start("body")
            tree_builder.frameset(True)
            return tree_builder.process_token(token)
        return True


class InTableState(State):
    pass


INITIAL = InitialState()
BEFORE_HTML = BeforeHtmlState()
BEFORE_HEAD = BeforeHeadState()
IN_HEAD = InHeadState()
IN_BODY = InBodyState()
IN_HEAD_NOSCRIPT = InHeadNoScriptState()
TEXT = TextState()
AFTER_HEAD = AfterHeadState()
IN_TABLE = InTableState()