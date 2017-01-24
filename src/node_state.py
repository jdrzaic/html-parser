import node
from abc import ABCMeta
import token as t
import token_state
import html_tag as ht


class State(object):
    __metaclass__ = ABCMeta

    def process_token(self, token, tree_builder):
        pass

    def is_white(self, token):
        if token.type == t.TokenType.CHARACTER:
            for i in len(token.data):
                if token.data[i] not in ["\n", "\r", "\f", "\t", " "]:
                    return False
            return True
        return False

    def handle_rcdata(self, token, tree_builder):
        tree_builder.insert(token)
        tree_builder.tokeniser.move(token_state.RCDATA)
        tree_builder.mark_insertion()
        tree_builder.move(TEXT)

    def handle_rawtext(self, token, tree_builder):
        tree_builder.insert(token)
        tree_builder.tokeniser.move(token_state.RAWTEXT)
        tree_builder.mark_insertion()
        tree_builder.move(TEXT)


    def any_other_end_tag(self, token, tree_builder):
        name = token.tag_lc_name
        stack = tree_builder.stack
        for i in range(len(stack)):
            n = stack[len(stack) - 1 - i]
            if n.node_name() == name:
                tree_builder.generate_implied_end(name)
                tree_builder.pop_stack_to_close(name)
                break
            else:
                if tree_builder.is_special(n):
                    return False
        return True



class InitialState(State):
    def process_token(self, token, tree_builder):
        if self.is_white(token):
            return True
        elif token.type == t.TokenType.COMMENT:
            tree_builder.insert(token)
        elif token.type == t.TokenType.DOCTYPE:
            document_type = node.DocumentType(
                token.tag_name, token.public_identifier, token.system_identifier, token.sys_key)
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
            return IN_BODY.process_token(token, tree_builder)
        elif token.type == t.TokenType.START_TAG and token.tag_lc_name == "head":
            head = tree_builder.insert(token)
            tree_builder.set_head(head)
            tree_builder.move(IN_HEAD)
        elif token.type == t.TokenType.END_TAG and token.tag_lc_name in ["head", "html", "body", "br"]:
            tree_builder.process_start("head")
            return tree_builder.process_token(token)
        elif token.type == t.TokenType.END_TAG:
            tree_builder.error("BeforeHeadState")
            return False
        else:
            tree_builder.process_start("head")
            return tree_builder.process_token(token)
        return True


class InHeadState(State):

    def process_token(self, token, tree_builder):
        print token
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
                if tree_builder.active_formatting_elem("a"):
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
                    if el.node_name() == "li":
                        tree_builder.process_end("li")
                        break
                    if tree_builder.is_special(el) and not el.node_name() in ["address", "div", "p"]:
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
                if tree_builder.current_element().node_name() in ["h1", "h2", "h3", "h4", "h5", "h6"]:
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
                    if el.node_name in ["dd", "dt"]:
                        tree_builder.process_end(el.node_name())
                        break
                    if tree_builder.is_special(el) and not el.node_name() in ["address", "div", "p"]:
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
            elif name == "xmp":
                if tree_builder.in_button_scope("p"):
                    tree_builder.process_end("p")
                tree_builder.reconstruct_formatting()
                tree_builder.frameset(False)
                self.handle_rawtext(token, tree_builder)
            elif name == "iframe":
                tree_builder.frameset(False)
                self.handle_rawtext(token, tree_builder)
            elif name == "noembed":
                self.handle_rawtext(token, tree_builder)
            elif name == "select":
                tree_builder.reconstruct_formatting()
                tree_builder.insert(token)
                tree_builder.frameset(False)
                state = tree_builder.state
                if state == IN_TABLE or state == IN_CAPTION or state == IN_TABLE_BODY or state == IN_ROW or state == IN_CELL:
                    tree_builder.move(IN_SELECT_IN_TABLE)
                else:
                    tree_builder.move(IN_SELECT)
            elif name in ["optgroup", "option"]:
                if tree_builder.current_element().node_name() == "option":
                    tree_builder.process_end("option")
                tree_builder.reconstruct_formatting()
                tree_builder.insert(token)
            elif name in ["rp", "rt"]:
                if tree_builder.in_scope("ruby"):
                    tree_builder.generate_implied_end()
                    if tree_builder.current_element().node_name() == "ruby":
                        tree_builder.error("InBodyState")
                        tree_builder.pop_stack_to_before("ruby")
                    tree_builder.insert(token)
            elif name == "math":
                tree_builder.reconstruct_formatting()
                tree_builder.insert(token)
                tree_builder.acknowledge_self_closing()
            elif name == "svg":
                tree_builder.reconstruct_formatting()
                tree_builder.insert(token)
                tree_builder.acknowledge_self_closing()
            elif name in ["caption", "col", "colgroup", "frame", "head", "tbody", "td", "tfoot",
                          "th", "thead", "tr"]:
                tree_builder.error("InBodyState")
                return False
            else:
                tree_builder.reconstruct_formatting()
                tree_builder.insert(token)
        elif token.type == t.TokenType.END_TAG:
            name = token.tag_lc_name
            if name in ["a", "b", "big", "code", "em", "font", "i", "nobr", "s", "small", "strike",
                        "strong", "tt", "u"]:
                for i in range(8):
                    el = tree_builder.get_active_formatting_el(name)
                    if not el:
                        return self.any_other_end_tag(token, tree_builder)
                    elif tree_builder.on_stack(el):
                        tree_builder.error("InBodyState")
                        tree_builder.remove_from_active_formatting(el)
                        return True
                    elif tree_builder.in_scope(el.node_name()):
                        tree_builder.error("InBodyState")
                        return False
                    elif tree_builder.current_element() != el:
                        tree_builder.error("InBodyState")
                    furthest_block = None
                    common_anchestor = None
                    seen_formatting = False
                    stack = tree_builder.stack
                    for i in range(min(len(stack), 64)):
                        eel = stack[i]
                        if eel == el:
                            common_anchestor = stack[i - 1]
                            seen_formatting = True
                        elif seen_formatting and tree_builder.is_special(eel):
                            furthest_block = eel
                            break
                    if not furthest_block:
                        tree_builder.pop_stack_to_close(el.node_name())
                        tree_builder.remove_from_active_formatting(el)
                        return True
                    n = furthest_block
                    last = furthest_block
                    for i in range(3):
                        if tree_builder.on_stack(n):
                            n = tree_builder.above_on_stack(n)
                        if tree_builder.is_in_active_formatting(n):
                            tree_builder.remove_from_stack(n)
                            continue
                        elif n == el:
                            break
                        replacement = node.Element(ht.Tag.value_of(n.node_name()))
                        n = replacement
                        if last.parent:
                            last.remove()
                        n.append_child(last)
                        last = n
                    if common_anchestor.node_name() in ["table", "tbody", "tfoot", "thead", "tr"]:
                        if last.parent:
                            last.remove()
                        tree_builder.insert_in_foster_parent(last)
                    else:
                        if last.parent:
                            last.remove()
                        else:
                            common_anchestor.append_child(last)
                    adopter = node.Element(el.tag)
                    adopter.attributes.attrs += el.attributes.attrs
                    child_nodes = furthest_block.child_nodes
                    for child_node in child_nodes:
                        adopter.append_child(child_node)
                    furthest_block.append_child(adopter)
                    tree_builder.remove_from_active_formatting(el)
                    tree_builder.remove_from_stack(el)
                    tree_builder.insert_on_stack_after(furthest_block, adopter)
            elif name in ["address", "article", "aside", "blockquote", "button", "center", "details", "dir", "div",
                "dl", "fieldset", "figcaption", "figure", "footer", "header", "hgroup", "listing", "menu",
                "nav", "ol", "pre", "section", "summary", "ul"]:
                if not tree_builder.in_scope(name):
                    tree_builder.error("InBodyState")
                    return False
                else:
                    tree_builder.generate_implied_end()
                    if tree_builder.current_element().node_name() != name:
                        tree_builder.error("InBodyState")
                    tree_builder.pop_stack_to_close(name)
            elif name == "span":
                return self.any_other_end_tag(token, tree_builder)
            elif name == "li":
                if not tree_builder.in_list_item_scope(name):
                    tree_builder.error("InBodyState")
                    return False
                else:
                    tree_builder.generate_implied_end(name)
                    if tree_builder.current_element().node_name() == name:
                        tree_builder.error("InBodyState")
                    tree_builder.pop_stack_to_close(name)
            elif name == "body":
                if not tree_builder.in_scope("body"):
                    tree_builder.error("InBodyState")
                    return False
                else:
                    tree_builder.move(AFTER_BODY)
            elif name == "html":
                not_ignored = tree_builder.process_end("body")
                if not_ignored:
                    return tree_builder.process_end(token)
            elif name == "form":
                current_form = tree_builder.get_form_elem()
                tree_builder.set_form_elem(None)
                if not current_form or not tree_builder.in_scope(name):
                    tree_builder.error("InBodyState")
                    return False
                else:
                    tree_builder.generate_implied_end()
                    if tree_builder.current_element().node_name() == name:
                        tree_builder.error("InBodyState")
                    tree_builder.remove_from_stack(current_form)
            elif name == "p":
                if tree_builder.in_button_scope(name):
                    tree_builder.error("InBodyState")
                    tree_builder.process_start(name)
                    tree_builder.process_token(token)
                else:
                    tree_builder.generate_implied_end(name)
                    if not tree_builder.current_element().node_name() == name:
                        tree_builder.error("InBodyState")
                    tree_builder.pop_stack_to_close(name)
            elif name in ["dd", "dt"]:
                if not tree_builder.in_scope(name):
                    tree_builder.error("InBodyState")
                    return False
                else:
                    tree_builder.generate_implied_end(name)
                    if not tree_builder.current_element().node_name() == name:
                        tree_builder.error("InBodyState")
                    tree_builder.pop_stack_to_close(name)
            elif name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                if tree_builder.in_scope_list(["h1", "h2", "h3", "h4", "h5", "h6"]):
                    tree_builder.error("InBodyState")
                    return False
                else:
                    tree_builder.generate_implied_end(name)
                    if not tree_builder.current_element().node_name() == name:
                        tree_builder.error("InBodyState")
                    tree_builder.pop_stack_to_close(["h1", "h2", "h3", "h4", "h5", "h6"])
            elif name in ["applet", "marquee", "object"]:
                if not tree_builder.in_scope("name"):
                    if not tree_builder.in_scope(name):
                        tree_builder.error("InBodyState")
                        return False
                    tree_builder.generate_implied_end()
                    if not tree_builder.current_element().node_name() == name:
                        tree_builder.error("InBodyState")
                    tree_builder.pop_stack_to_close(name)
                    tree_builder.clear_formatting_to_last_marker()
            elif name == "br":
                tree_builder.error("InBodyState")
                tree_builder.process_start("br")
                return False
            else:
                return self.any_other_end_tag(token, tree_builder)
        return True


class InHeadNoScriptState(State):
    def process_token(self, token, tree_builder):
        if token.type == t.TokenType.DOCTYPE:
            tree_builder.error("BeforeHeadState")
        elif token.type == t.TokenType.START_TAG and token.tag_lc_name == "html":
            return tree_builder.process_token(token, IN_BODY)
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
    def process_token(self, token, tree_builder):
        if token.type == t.TokenType.CHARACTER:
            tree_builder.insert(token)
        elif token.type == t.TokenType.EOF:
            tree_builder.error("TextState")
            tree_builder.pop()
            tree_builder.move(tree_builder.original_state)
            return tree_builder.process_token(token)
        elif token.type == t.TokenType.END_TAG:
            tree_builder.pop()
            tree_builder.move(tree_builder.original_state)
        return True


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
    def process_token(self, token, tree_builder):
        if token.type == t.TokenType.CHARACTER:
            tree_builder.new_pending_table_chars()
            tree_builder.mark_insertion()
            tree_builder.move(IN_TABLE_TEXT)
            return tree_builder.process_token(token)
        elif token.type == t.TokenType.COMMENT:
            tree_builder.insert(token)
            return True
        elif token.type == t.TokenType.DOCTYPE:
            tree_builder.error("InTableState")
            return False
        elif token.type == t.TokenType.START_TAG:
            name = token.tag_lc_name
            if name == "caption":
                tree_builder.clear_stack_to_table_context()
                tree_builder.insert_marker_to_formatting()
                tree_builder.insert(token)
                tree_builder.move(IN_CAPTION)
            elif name == "colgroup":
                tree_builder.clear_stack_to_table_context()
                tree_builder.insert(token)
                tree_builder.move(IN_COLUMN_GROUP)
            elif name == "col":
                tree_builder.process_start("colgroup")
                return tree_builder.process_token(token)
            elif name in ["tbody", "tfoot", "thead"]:
                tree_builder.clear_stack_to_table_context()
                tree_builder.insert(token)
                tree_builder.move(IN_TABLE_BODY)
            elif name in ["tb", "th", "tr"]:
                tree_builder.process_start("tbody")
                return tree_builder.process_token(token)
            elif name == "table":
                tree_builder.error("InTableState")
                processed = tree_builder.process_end("table")
                if processed:
                    tree_builder.process_token(token)
            elif name in ["style", "script"]:
                return tree_builder.process(token, IN_HEAD)
        elif token.type == t.TokenType.END_TAG:
            name = token.tag_lc_name
            if name == "table":
                if not tree_builder.in_table_scope(name):
                    tree_builder.error("InTableState")
                    return False
                else:
                    tree_builder.pop_stack_to_close("table")
                tree_builder.reset_insertion()
            elif name in ["body", "caption", "col", "colgroup", "html", "tbody", "td", "tfoot", "th", "thead", "tr"]:
                tree_builder.error("InTableState")
                return False
            else:
                return self.anything_else(token, tree_builder)
            return True
        elif token.type == t.TokenType.EOF:
            if tree_builder.current_element().node_name() == "html":
                tree_builder.error("InTableState")
            return True
        return self.anything_else(token, tree_builder)

    def anything_else(self, token, tree_builder):
        if tree_builder.current_element().node_name() in ["table", "tbody", "tfoot", "thead", "tr"]:
            tree_builder.set_foster_inserts(True)
            processed = tree_builder.process_token(token, IN_BODY)
            tree_builder.set_foster_inserts(False)
        else:
            processed = tree_builder.process_token(token, IN_BODY)
        return processed


class InCaptionState(State):
    def process_token(self, token, tree_builder):
        if token.type == t.TokenType.END_TAG and token.tag_lc_name == "caption":
            name = token.tag_lc_name
            if tree_builder.in_table_scope(name):
                tree_builder.error("InCaptionState")
                return False
            else:
                tree_builder.generate_implied_end()
                if not tree_builder.current_element().node_name() == "caption":
                    tree_builder.error("InCaptionState")
                tree_builder.pop_stack_to_close("caption")
                tree_builder.clear_formatting_to_last_marker()
                tree_builder.move(IN_TABLE)
        elif token.type == t.TokenType.START_TAG and token.tag_lc_name in [
            "caption", "col", "colgroup", "tbody", "td", "tfoot", "th", "thead", "tr"] or (
            token.type == t.TokenType.END_TAG and token.tag_lc_name == "table"):
            tree_builder.error("InCaptionState")
            processed = tree_builder.process_end("caption")
            if processed:
                return tree_builder.process_token(token)
        elif token.type == t.TokenType.END_TAG and token.tag_lc_name == [
            "body", "col", "colgroup","html", "tbody", "td", "tfoot", "th", "thead", "tr"]:
            tree_builder.error("InCaptionState")
            return False
        else:
            return tree_builder.process_token(token, IN_BODY)


class InRowState(State):
    def process_token(self, token, tree_builder):
        if token.type == t.TokenType.START_TAG:
            name = token.tag_lc_name
            if name in ["th", "td"]:
                tree_builder.clear_stack_to_table_row_context()
                tree_builder.insert(token)
                tree_builder.move(IN_CELL)
                tree_builder.insert_marker_to_formatting()
            elif name in ["caption", "col", "colgroup", "tbody", "tfoot", "thead", "tr"]:
                processed = tree_builder.process_end("tr")
                if processed:
                    return tree_builder.process_token(token)
                return False
            else:
                return tree_builder.process_token(token, IN_TABLE)
        elif token.type == t.TokenType.END_TAG:
            name = token.tag_lc_name
            if name == "tr":
                if not tree_builder.in_table_scope("tr"):
                    tree_builder.error("InRowState")
                    return False
                tree_builder.clear_stack_to_table_row_context()
                tree_builder.pop()
                tree_builder.move(IN_TABLE_BODY)
            elif name == "table":
                processed = tree_builder.process_end("tr")
                if processed:
                    return tree_builder.process_token(token)
                return False
            elif name in ["tbody", "tfoot", "thead"]:
                if not tree_builder.in_table_scope(name):
                    tree_builder.error("InRowState")
                    return False
                tree_builder.process_end("tr")
                return tree_builder.process_token(token)
            elif name in ["body", "caption", "col", "colgroup", "html", "td", "th"]:
                tree_builder.error("InRowState")
                return False
            else:
                return tree_builder.process_token(token, IN_TABLE)
        else:
            return tree_builder.process_token(token, IN_TABLE)
        return True


class InCellState(State):
    def process_token(self, token, tree_builder):
        if token.type == t.TokenType.END_TAG:
            name = token.tag_lc_name
            if name in ["td", "th"]:
                if not tree_builder.in_table_scope(name):
                    tree_builder.error("InCellState")
                    tree_builder.move(IN_ROW)
                    return False
                tree_builder.generate_implied_end()
                if not tree_builder.current_element().node_name() == name:
                    tree_builder.error("InCellState")
                tree_builder.pop_stack_to_close(name)
                tree_builder.clear_formatting_to_last_marker()
                tree_builder.move(IN_ROW)
            elif name in ["body", "caption", "col", "colgroup", "html"]:
                tree_builder.error("InCellState")
                return False
            elif name in ["table", "tbody", "tfoot", "thead", "tr"]:
                if not tree_builder.in_table_scope(name):
                    tree_builder.error("InCellState")
                    return False
                if tree_builder.in_table_scope("td"):
                    tree_builder.process_end("td")
                else:
                    tree_builder.process_end("th")
                return tree_builder.process_token(token)
            else:
                return tree_builder.process_token(token, IN_BODY)
        elif token.type == t.TokenType.START_TAG and token.tag_lc_name in [
            "caption", "col", "colgroup", "tbody", "td", "tfoot", "th", "thead", "tr"]:
            if not tree_builder.in_table_scope("td") or tree_builder.in_table_scope("th"):
                tree_builder.error("InCellState")
                return False
            if tree_builder.in_table_scope("td"):
                tree_builder.process_end("td")
            else:
                tree_builder.process_end("th")
            return tree_builder.process_token(token)
        else:
            return tree_builder.process_token(token, IN_BODY)
        return True


class InFramesetState(State):
    def process_token(self, token, tree_builder):
        if self.is_white(token) or token.type == t.TokenType.COMMENT:
            tree_builder.insert(token)
        elif token.type == t.TokenType.START_TAG:
            name = token.tag_lc_name
            if name == "html":
                return tree_builder.process_token(token, IN_BODY)
            elif name == "frameset":
                tree_builder.insert(token)
            elif name == "noframes":
                return tree_builder.process_token(token, IN_HEAD)
            else:
                return False
        elif token.type == t.TokenType.END_TAG and token.tag_lc_name == "frameset":
            tree_builder.pop()
            tree_builder.move(AFTER_FRAMESET)
        elif token.type == t.TokenType.EOF:
            if not tree_builder.current_element().node_name() == "html":
                return True
        else:
            return False
        return True


class InSelectState(State):
    def process_token(self, token, tree_builder):
        if token.type == t.TokenType.CHARACTER:
            if not token.data:
                tree_builder.error("InSelectState")
                return False
            else:
                tree_builder.insert(token)
        elif token.type == t.TokenType.COMMENT:
            tree_builder.insert(token)
        elif token.type == t.TokenType.START_TAG:
            name = token.tag_lc_name
            if name == "html":
                return tree_builder.process_token(token, IN_BODY)
            elif name == "option":
                tree_builder.process_end("option")
                tree_builder.insert(token)
            elif name == "optgroup":
                if tree_builder.current_element().node_name() in ["optgroup", "option"]:
                    tree_builder.process_end(tree_builder.current_element().node_name())
                tree_builder.insert(token)
            elif name == "select":
                tree_builder.process_end("select")
            elif name in ["input", "textarea", "keygen"]:
                tree_builder.error("InSelectState")
                if not tree_builder.in_select_scope("select"):
                    return False
                tree_builder.process_end("select")
                return tree_builder.process_token(token)
            elif name == "script":
                return tree_builder.process_token(token, IN_HEAD)
            else:
                return False
        elif token.type == t.TokenType.END_TAG:
            name = token.tag_lc_name
            if name == "optgroup":
                if tree_builder.current_element().node_name() == "option" and tree_builder.above_on_stack(
                        tree_builder.current_element()) and tree_builder.above_on_stack(
                        tree_builder.current_element()).node_name() == "optgroup":
                    tree_builder.process_end("option")
                elif tree_builder.current_element().node_name() == "optgroup":
                    tree_builder.pop()
            elif name == "option":
                if tree_builder.current_element().node_name() == "option":
                    tree_builder.pop()
            elif name == "select":
                if not tree_builder.in_select_scope(name):
                    return False
                else:
                    tree_builder.pop_stack_to_close(name)
                    tree_builder.reset_insertion()
            else:
                return False
        else:
            return False
        return True


class InSelectInTableState(State):
    def process_token(self, token, tree_builder):
        if token.type == t.TokenType.START_TAG and token.tag_lc_name in [
            "caption", "table", "tbody", "tfoot", "thead", "tr", "td", "th"
        ]:
            tree_builder.error("InSelectInTableState")
            tree_builder.process_end("select")
            return tree_builder.process_token(token)
        elif token.type == t.TokenType.END_TAG and token.tag_lc_name in [
            "caption", "table", "tbody", "tfoot", "thead", "tr", "td", "th"]:
            if tree_builder.in_table_scope(token.tag_lc_name):
                tree_builder.process_end("select")
                return tree_builder.process_token(token)
            else:
                return False
        else:
            return tree_builder.process_token(token, IN_SELECT)


class InTableBodyState(State):
    def process_token(self, token, tree_builder):
        if token.type == t.TokenType.START_TAG:
            name = token.tag_lc_name
            if name == "tr":
                tree_builder.clear_stack_to_table_body_context()
                tree_builder.insert(token)
                tree_builder.move(IN_ROW)
            elif name in ["th", "td"]:
                tree_builder.error("InTableBodyState")
                tree_builder.process_start("tr")
                return tree_builder.process_token(token)
            elif name in ["caption", "col", "colgroup", "tbody", "tfoot", "thead"]:
                return self.exit_table_body(token, tree_builder)
            else:
                return tree_builder.process_token(token, IN_TABLE)
        elif token.type == t.TokenType.END_TAG:
            name = token.tag_lc_name
            if name in ["tbody", "tfoot", "thead"]:
                if not tree_builder.in_table_scope(name):
                    tree_builder.error("InTableBodyState")
                    return False
                else:
                    tree_builder.clear_stack_to_table_body_context()
                    tree_builder.pop()
                    tree_builder.move(IN_TABLE)
            elif name == "table":
                if not tree_builder.in_table_scope("tbody") or tree_builder.in_table_scope("thead") or tree_builder.in_table_scope("tfoot"):
                    return False
                tree_builder.clear_stack_to_table_body_context()
                tree_builder.process_end(tree_builder.current_element().node_name())
                return tree_builder.process_token(token)
            elif name in ["body", "caption", "col", "colgroup", "html", "td", "th", "tr"]:
                tree_builder.error("IntableBodyState")
                return False
            else:
                return tree_builder.process_token(token, IN_TABLE)
        return True

    def exit_table_body(self, token, tree_builder):
        if tree_builder.in_table_scope("tbody") or tree_builder.in_table_scope("thead") or tree_builder.in_table_scope("tfoot"):
            return False
        tree_builder.clear_stack_to_table_body_context()
        tree_builder.process_end(tree_builder.current_element().node_name())
        return tree_builder.process_token(token)


class InTableTextState(State):
    def process_token(self, token, tree_builder):
        if token.type == t.TokenType.CHARACTER and token.data:
            tree_builder.pending_table_chars += token.data
        else:
            if tree_builder.pending_table_chars:
                for char in tree_builder.pending_table_chars:
                    ch = t.CharacterToken()
                    ch.data = char
                    if self.is_white(token):
                        if tree_builder.current_element().node_name() in ["table", "tbody", "tfoot", "thead", "tr"]:
                            tree_builder.set_foster_inserts(True)
                            tree_builder.process_token(ch, IN_BODY)
                            tree_builder.set_foster_inserts(False)
                        else:
                            tree_builder.process_token(ch, IN_BODY)
                    else:
                        tree_builder.insert(ch)
                tree_builder.new_pending_table_chars()
            tree_builder.move(tree_builder.original_state)
            return tree_builder.process_token(token)
        return True


class InColumnGroupState(State):
    def process_token(self, token, tree_builder):
        if self.is_white(token):
            tree_builder.insert(token)
            return True
        if token.type == t.TokenType.COMMENT:
            tree_builder.insert(token)
        elif token.type == t.TokenType.DOCTYPE:
            return True
        elif token.type == t.TokenType.START_TAG:
            name = token.tag_lc_name
            if name == "html":
                return tree_builder.process_token(token, IN_BODY)
            elif name == "col":
                tree_builder.insert_empty(token)
            else:
                self.anything_else(token, tree_builder)
        elif token.type == t.TokenType.END_TAG:
            name = token.tag_lc_name
            if name == "colgroup":
                if tree_builder.current_element().node_name() == "html":
                    tree_builder.error("InColumnGroupState")
                    return False
                else:
                    tree_builder.pop()
                    tree_builder.move(IN_TABLE)
            else:
                return self.anything_else(token, tree_builder)
        elif token.type == t.TokenType.EOF:
            if tree_builder.current_element().node_name() == "html":
                return True
            return self.anything_else(token, tree_builder)
        else:
            return self.anything_else(token, tree_builder)
        return True

    def anything_else(self, token, tree_builder):
        processed = tree_builder.process_end("colgroup")
        if processed:
            return tree_builder.process_token(token)
        return True


class AfterBodyState(State):
    def process_token(self, token, tree_builder):
        if self.is_white(token):
            return tree_builder.process_token(token, IN_BODY)
        elif token.type == t.TokenType.COMMENT:
            tree_builder.insert(token)
        elif token.type == t.TokenType.DOCTYPE:
            tree_builder.error("AfterBodyState")
            return False
        elif token.type == t.TokenType.START_TAG and token.tag_lc_name == "html":
            return tree_builder.process_token(token, IN_BODY)
        elif token.type == t.TokenType.END_TAG and token.tag_lc_name == "html":
            tree_builder.move(AFTER_AFTER_BODY)
        else:
            tree_builder.move(IN_BODY)
            return tree_builder.process_token(token)
        return True


class AfterAfterBodyState(State):
    def process_token(self, token, tree_builder):
        if token.type == t.TokenType.COMMENT:
            tree_builder.insert(token)
        elif token.type == t.TokenType.DOCTYPE or self.is_white(token) or (
                        token.type == t.TokenType.START_TAG and token.tag_lc_name == "html"):
            return tree_builder.process_token(token, IN_BODY)
        else:
            tree_builder.error("AfterAfterBodyState")
            tree_builder.move(IN_BODY)
            return tree_builder.process_token(token)
        return True


class AfterFramesetState(State):
    def process_token(self, token, tree_builder):
        if self.is_white(token):
            tree_builder.insert(token)
        elif token.type == t.TokenType.COMMENT:
            tree_builder.insert(token)
        elif token.type == t.TokenType.START_TAG and token.tag_lc_name == "html":
            return tree_builder.process_token(token, IN_BODY)
        elif token.type == t.TokenType.END_TAG and token.tag_lc_name == "html":
            tree_builder.move(AFTER_AFTER_FRAMESET)
        elif token.type == t.TokenType.START_TAG and token.tag_lc_name == "noframes":
            return tree_builder.process_token(token, IN_HEAD)
        else:
            return False
        return True


class AfterAfterFramesetState(State):
    def process_token(self, token, tree_builder):
        if token.type == t.TokenType.COMMENT:
            tree_builder.insert(token)
            return True
        elif self.is_white(token) or (token.type == t.TokenType.START_TAG and token.tag_lc_name == "html"):
            return tree_builder.process_token(token, IN_BODY)
        elif token.type == t.TokenType.START_TAG and token.tag_lc_name == "noframes":
            return tree_builder.process_token(token, IN_HEAD)
        else:
            return False


INITIAL = InitialState()
BEFORE_HTML = BeforeHtmlState()
BEFORE_HEAD = BeforeHeadState()
IN_HEAD = InHeadState()
IN_BODY = InBodyState()
IN_HEAD_NOSCRIPT = InHeadNoScriptState()
TEXT = TextState()
AFTER_HEAD = AfterHeadState()
IN_TABLE = InTableState()
IN_CAPTION = InCaptionState()
IN_ROW = InRowState()
IN_CELL = InCellState()
IN_FRAMESET = InFramesetState()
IN_SELECT = InSelectState()
IN_SELECT_IN_TABLE = InSelectInTableState()
IN_TABLE_BODY = InTableBodyState()
IN_TABLE_TEXT = InTableTextState()
IN_COLUMN_GROUP = InColumnGroupState()
AFTER_BODY = AfterBodyState()
AFTER_AFTER_BODY = AfterAfterBodyState()
AFTER_FRAMESET = AfterFramesetState()
AFTER_AFTER_FRAMESET = AfterAfterFramesetState()