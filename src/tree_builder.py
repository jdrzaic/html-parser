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
        self.state = ns.INITIAL
        self.head_elem = None
        self.form_elem = None
        self.formatting_elems = []
        self.original_state = None
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
            return self.insert_elem(token)
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
        tag_name = self.current_element().tag.tag_name
        if tag_name == "script" or tag_name == "style":
            n = node.Data(ch.data)
        else:
            n = node.Text(ch.data)
        self.current_element().append_child(n)

    def insert_start(self, token):
        new_start = node.Element(tag=html_tag.Tag.value_of(token))
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
        last = self.last_formatting_element()
        if not last or self.on_stack(last):
            return
        entry = last
        skip = False
        formatting_num = len(self.formatting_elems)
        pos = formatting_num - 1
        while True:
            if not pos:
                skip = True
                break
            pos -= 1
            entry = self.formatting_elems[pos]
            if not entry or self.on_stack(entry):
                break
        while True:
            if not skip:
                pos += 1
                entry = self.formatting_elems[pos]
            skip = False
            new_elem = self.insert_start(entry.node_name())
            new_elem.attributes.attrs = dict(
                new_elem.attributes.attrs.items() + entry.attributes.attrs.items())
            self.formatting_elems[pos] = new_elem
            if pos == formatting_num - 1:
                break

    def last_formatting_element(self):
        return self.formatting_elems[len(self.formatting_elems) - 1] if self.formatting_elems else None

    def active_formatting_elem(self, name):
        elems_size = len(self.formatting_elems)
        for i in range(elems_size):
            pos = elems_size - 1 - i
            next_elem = self.formatting_elems[pos]
            if not next_elem:
                break
            elif next_elem.node_name() == name:
                return next_elem
        return None

    def get_from_stack(self, name):
        for i in range(len(self.stack)):
            next_ = self.stack[len(self.stack) - 1 - i]
            if next_.tag.tag_lc_name == name:
                return next_
        return None

    def remove_from_active_formatting(self, el):
        size = len(self.formatting_elems)
        for i in range(size):
            next_el = self.formatting_elems[size - i - 1]
            if next_el == el:
                self.formatting_elems.pop(size - i - 1)
                break

    def mark_insertion(self):
        self.original_state = self.state

    def generate_implied_end(self, ex_tag=None):
        while ex_tag and not self.current_element().node_name() == ex_tag and \
            self.current_element().node_name() in [
                    "dd", "dt", "li", "option", "optgroup", "p", "rp", "rt"]:
            self.pop()

    def pop_stack_to_close(self, *args):
        size = len(self.stack)
        for i in range(size):
            pos = size - 1 - i
            next_el = self.stack[pos]
            self.stack.pop(pos)
            if next_el.node_name() in args:
                break

    def is_special(self, n):
        return n.name in html_tag.SPECIAL_TAGS

    def pop(self):
        self.stack.pop(len(self.stack) - 1)

    def push_active_formatting(self, obj):
        count = 0
        elems_size = len(self.formatting_elems)
        for i in elems_size:
            pos = elems_size - 1 - i
            elem = self.formatting_elems[pos]
            if not elem:
                break
            if obj.node_name() == elem.node_name() and \
                    set(obj.attributes.attrs) == set(elem.attributes.attrs):
                count += 1
            if count == 3:
                self.formatting_elems.pop(pos)
                break
        self.formatting_elems.append(obj)

    def in_button_scope(self, name):
        return self.in_scope_list([name], html_tag.IN_SCOPE_TAGS, html_tag.BUTTON_TAGS)

    def in_scope(self, name):
        return self.in_scope_list([name], html_tag.IN_SCOPE_TAGS)

    def in_scope_list(self, names, base_tags=html_tag.IN_SCOPE_TAGS, extra_tags=None):
        size = len(self.stack)
        for i in range(size):
            pos = size - i - 1
            elem = self.stack[pos]
            el_name = elem.node_name()
            if el_name in names:
                return True
            if el_name in base_tags:
                return False
            if extra_tags and el_name in extra_tags:
                return False
        return False

    def insert_form(self, token, on_stack=False):
        tag = html_tag.Tag.value_of(token.tag_lc_name)
        form_el = node.FormElement(tag, token.attributes)
        self.set_form_elem(form_el)
        self.insert_node(form_el)
        if on_stack:
            self.stack.append(form_el)
        return form_el

    def insert_marker_to_formatting(self):
        self.formatting_elems.append(None)

    def pop_stack_to_before(self, name):
        size = len(self.stack)
        for i in range(size):
            pos = size - 1 - i
            next_el = self.stack[pos]
            if next_el.node_name() == name:
                break
            else:
                self.stack.remove(pos)

    def get_active_formatting_el(self, name):
        elems_size = len(self.formatting_elems)
        for i in elems_size:
            pos = elems_size - 1 - i
            next_el = self.formatting_elems[pos]
            if not next_el:
                break
            elif next_el.node_name() == name:
                return next_el
        return None

    def on_stack(self, name):
        return name in self.stack

    def above_on_stack(self, n):
        size = len(self.stack)
        for i in range(size):
            next_el = self.stack[size - 1 - i]
            if n == next_el:
                return self.stack[size - 2 - i]
        return None

    def is_in_active_formatting(self, n):
        return n in self.formatting_elems

    def insert_in_foster_parents(self, n):
        last_table = self.get_from_stack("table")
        is_last_table_parent = False
        if last_table:
            if last_table.parent:
                foster_parent = last_table.parent
                is_last_table_parent = True
            else:
                foster_parent = self.above_on_stack(last_table)
        else:
            foster_parent = self.stack[0]
        if not is_last_table_parent:
            last_table.before(n)
        else:
            foster_parent.append_child(n)

    def insert_on_stack_after(self, first, second):
        size = len(self.stack)
        for i in range(size):
            if self.stack[size - 1 - i] == first:
                self.stack.insert(size - i, second)

    def in_list_item_scope(self, name):
        return self.in_scope_list([name], html_tag.IN_SCOPE_TAGS, html_tag.LIST_TAGS)

    def get_form_elem(self):
        return self.form_elem

    def set_form_elem(self, elem):
        self.form_elem = elem

    def clear_formatting_to_last_marker(self):
        while self.formatting_elems:
            elem = self.remove_last_formatting_element()
            if not elem:
                break

    def remove_last_formatting_element(self):
        if self.formatting_elems:
            elem = self.formatting_elems[len(self.formatting_elems) - 1]
            self.formatting_elems.pop()
            return elem
        return None

    def new_pending_table_chars(self):
        self.pending_table_chars = []

    def clear_stack_to_table_context(self):
        self.clear_stack_to_context("table")

    def in_table_scope(self, name):
        return self.in_scope_list([name], html_tag.IN_SCOPE_TAGS, html_tag.TABLE_TAGS)

    def set_foster_inserts(self, foster_inserts):
        self.foster_inserts = foster_inserts

    def clear_stack_to_table_row_context(self):
        self.clear_stack_to_context("tr")

    def in_select_scope(self, name):
        self.in_scope_list([name], html_tag.IN_SCOPE_TAGS, html_tag.SELECT_TAGS)

    def reset_insertion(self):
        last = False
        for i in range(len(self.stack)):
            pos = len(self.stack) - 1 - i
            n = self.stack[pos]
            name = n.node_name()
            if name == "select":
                self.move(ns.IN_SELECT)
                break
            elif not last and name == "th" or name == "td":
                self.move(ns.IN_CELL)
                break
            elif name == "tr":
                self.move(ns.IN_ROW)
                break
            elif name in ["tbody", "thead", "tfoot"]:
                self.move(ns.IN_TABLE_BODY)
                break
            elif name == "caption":
                self.move(ns.IN_CAPTION)
                break
            elif name == "colgroup":
                self.move(ns.IN_COLUMN_GROUP)
                break
            elif name == "table":
                self.move(ns.IN_TABLE)
                break
            elif name in ["head", "body"]:
                self.move(ns.IN_BODY)
                break
            elif name == "frameset":
                self.move(ns.IN_FRAMESET)
                break
            elif name == "html":
                self.move(ns.BEFORE_HEAD)
                break

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

    def __str__(self):
        return "current_token={0}\ncurrent_element={1}\nstate={2}".format(
            self.current_token, self.current_element(), self.state
        )



