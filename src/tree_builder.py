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
        self.tokeniser = tokeniser.Tokeniser(self.reader, self.errors)

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

    def frameset(self, bool):
        pass

    def head(self):
        pass

    def push(self, elem):
        pass

    def remove_from_stack(self, elem):
        pass

    def reconstruct_formatting(self):
        pass
