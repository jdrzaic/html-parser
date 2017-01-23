import node
import util
import tokeniser
import token as t
import token_state as ts
import node_state as ns
import attributes as at
import html_tag


class TreeBuilder(object):
    def __init__(self, url, input_str):
        self.doc = node.Document(url)
        self.reader = util.Reader(input_str)
        self.errors = []
        self.state = ns.INITIAL
        self.head_elem = None
        self.form_elem = None
        self.formatting_elems = []
        self.original_state = None #what?
        self.stack = []
        self.tokeniser = tokeniser.Tokeniser(self.reader, self.errors)
        self.pending_table_chars = []
        self.empty_end = t.EndTagToken()
        self.frameset_good = False
        self.current_token = None
        self.foster_inserts = False
        self.start = t.StartTagToken("", at.Attributes())
        self.end = t.EndTagToken()
        self.specific_scope_tar = [None]

    def parse(self):
        while True:
            curr_token = self.tokeniser.read()
            print curr_token
            self.process_token(curr_token)
            finished = False
            if curr_token.type == t.TokenType.EOF:
                finished = True
            curr_token = None
            if finished:
                break

    def process_token(self, curr_token, state=None):
        self.current_token = curr_token
        if not state:
            return self.state.process_token(self.current_token, self)
        return state.process_token(self.current_token, self)

    def process_start(self, name, attrs=at.Attributes()):
        if self.current_token == self.start:
            new_start = t.StartTagToken(name, attrs)
            return self.process_token(new_start)
        self.start = t.StartTagToken(name, attrs)
        return self.process_token(self.start)

    def process_end(self, name):
        if self.current_token == self.end:
            new_end = t.EndTagToken(name)
            return self.process_token(new_end)
        self.end = t.EndTagToken(name)
        return self.process_token(self.end)

    def insert_elem(self, elem):
        self.insert_node(elem)
        self.stack.append(elem)

    def insert(self, token):
        if isinstance(token, node.Element):
            self.insert_elem(token)
        if token.type == t.TokenType.START_TAG:
            self.insert_start_tag(token)
        elif token.type == t.TokenType.COMMENT:
            self.insert_comment_token(token)
        elif token.type == t.TokenType.CHARACTER:
            self.insert_char_token(token)

    def insert_start_tag(self, tag):
        if tag.is_self_closing:
            elem = self.insert_empty(tag)
            self.stack.append(elem)
            self.tokeniser.move(ts.DATA)
            self.empty_end = t.EndTagToken()
            self.empty_end.name = tag.tag_lc_name
            self.tokeniser.emit(self.empty_end)
            return elem
        elem = node.Element(tag=html_tag.Tag.value_of(tag.tag_lc_name))
        self.insert(elem)
        return elem

    def insert_comment_token(self, comment):
        comm = node.Comment(comment.data)
        self.insert_node(comment)

    def insert_node(self, n):
        if not self.stack:
            self.doc.append_child(n)
        elif self.foster_inserts:
            self.insert_in_foster_parents(n)
        else:
            self.current_element().append_child(n)
        if isinstance(n, node.Element) and n.tag.form_list and self.form_elem:
            self.form_elem.add_element(n)

    def insert_char_token(self, ch):
        tag_name = self.current_element().tag.tag_lc_name
        if tag_name == "script" or tag_name == "style":
            n = node.Data(ch.data)
        else:
            n = node.Text(ch.data)
        self.current_element().append_child(n)

    def insert_start(self, token):
        new_start = node.Element(tag=html_tag.Tag.value_of(token.tag_lc_name))
        self.insert(new_start)
        return new_start

    def insert_empty(self, token):
        a_tag = html_tag.Tag.value_of(token.tag_lc_name)
        elem = node.Element(tag=a_tag, attributes=token.attributes)
        self.insert_node(elem)
        if token.is_self_closing:
            if token.tag_lc_name in html_tag.TAGS:
                if token.is_self_closing:
                    self.tokeniser.self_closing_acknow = True
                else:
                    a_tag.self_closing = True
                    self.tokeniser.self_closing_acknow = True
        return elem

    def move(self, state):
        self.state = state

    def error(self, token):
        print(token)
        self.errors.append(token)

    def set_head(self, head):
        self.head_elem = head

    def set_base_url(self, node_el):
        pass

    def frameset(self, ok=False):
        self.frameset_good = ok

    def head(self):
        return self.head_elem

    def push(self, elem):
        self.stack.append(elem)

    def remove_from_stack(self, elem):
        for i in range(len(self.stack)):
            next_ = self.stack[len(self.stack) - 1 - i]
            if next_ == elem:
                self.stack.remove(next_)
                return True
        return False

    def reconstruct_formatting(self):
        pass

    def active_formatting_elem(self):
        pass

    def get_from_stack(self, name):
        for i in range(len(self.stack)):
            next_ = self.stack[len(self.stack) - 1 - i]
            if next_.tag.tag_lc_name == name:
                return next_
        return None

    def remove_from_active_formatting(self, obj):
        pass

    def mark_insertion(self):
        self.original_state = self.state

    def generate_implied_end(self, name):
        pass

    def pop_stack_to_close(self, name):
        pass

    def is_special(self, n):
        return n.name in html_tag.SPECIAL_TAGS

    def pop(self):
        self.stack.pop(len(self.stack) - 1)

    def push_active_formatting(self, obj):
        pass

    def in_button_scope(self, name):
        pass

    def in_scope(self, name):
        pass

    def insert_form(self, token):
        pass

    def insert_marker_to_formatting(self):
        self.formatting_elems.append(None)

    def pop_stack_to_before(self):
        pass

    def acknowledge_self_closing(self):
        pass

    def get_active_formatting_el(self, name):
        pass

    def on_stack(self, name):
        pass

    def above_on_stack(self, n):
        pass

    def is_in_active_formatting(self, n):
        pass

    def insert_in_foster_parents(self, n):
        pass

    def insert_on_stack_after(self, first, second):
        pass

    def in_list_item_scope(self, name):
        pass

    def get_form_elem(self):
        return self.form_elem

    def set_form_elem(self, elem):
        self.form_elem = elem

    def clear_formatting_to_last_marker(self):
        pass

    def new_pending_table_chars(self):
        pass

    def clear_stack_to_table_context(self):
        self.clear_stack_to_context("table")

    def in_table_scope(self, name):
        pass

    def set_foster_inserts(self, bool):
        pass

    def clear_stack_to_table_row_context(self):
        self.clear_stack_to_context("tr")

    def in_select_scope(self, name):
        pass

    def reset_insertion(self):
        pass

    def clear_stack_to_table_body_context(self):
        self.clear_stack_to_context("tbody", "tfoot", "thead")

    def clear_stack_to_context(self, *args):
        for i in range(len(self.stack)):
            next_ = self.stack[len(self.stack) - 1 - i]
            if next_.node_name() in args or next_.node_name() in ["html"]:
                break
            else:
                self.stack.pop(len(self.stack) - i - 1)


    def current_element(self):
        return self.stack[len(self.stack) - 1] if self.stack else None



