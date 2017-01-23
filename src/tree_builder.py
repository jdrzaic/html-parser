import node
import util
import tokeniser
import token as t
import node_state as ns


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
        self.stack = [] # stack build_in?
        self.tokeniser = tokeniser.Tokeniser(self.reader, self.errors)
        self.pending_table_chars = []
        self.empty_end = t.EndTagToken()
        self.frameset_good = False
        self.foster_inserts = False

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

    def process_token(self, curr_token):
        pass

    def process_start(self, start_token):
        pass

    def process_end(self, end_token):
        pass

    def insert(self, token):
        pass

    def insert_start(self, token):
        pass

    def insert_empty(self, token):
        pass

    def move(self, state):
        pass

    def error(self, token):
        print(token)
        self.errors.append(token)

    def set_head(self, head):
        pass

    def set_base_url(self, node_el):
        pass

    def frameset(self, bool=False):
        pass

    def head(self):
        pass

    def push(self, elem):
        pass

    def remove_from_stack(self, elem):
        pass

    def reconstruct_formatting(self):
        pass

    def active_formatting_elem(self):
        pass

    def get_from_stack(self, name):
        pass

    def remove_from_active_formatting(self, obj):
        pass

    def mark_insertion(self):
        pass

    def generate_implied_end(self, name):
        pass

    def pop_stack_to_close(self, name):
        pass

    def is_special(self, n):
        pass

    def pop(self):
        pass

    def push_active_formatting(self, obj):
        pass

    def in_button_scope(self, name):
        pass

    def in_scope(self, name):
        pass

    def insert_form(self, token):
        pass

    def insert_marker_to_formatting(self):
        pass

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
        pass

    def set_form_elem(self, elem):
        pass

    def clear_formatting_to_last_marker(self):
        pass

    def new_pending_table_chars(self):
        pass

    def clear_stack_to_table_context(self):
        pass

    def in_table_scope(self, name):
        pass

    def set_foster_inserts(self, bool):
        pass

    def clear_stack_to_table_row_context(self):
        pass

    def in_select_scope(self, name):
        pass

    def reset_insertion(self):
        pass

    def clear_stack_to_table_body_context(self):
        pass



