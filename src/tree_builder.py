import node
import util
import tokeniser
import token


class TreeBuilder(object):
    def __init__(self, url, input_str):
        self.doc = node.Document(url)
        self.reader = util.Reader(input_str)
        self.errors = []
        self.tokeniser = tokeniser.Tokeniser(self.reader, self.errors)

    def parse(self):
        while True:
            curr_token = self.tokeniser.read()
            print curr_token
            self.process_token(curr_token)
            finished = False
            if curr_token.type == token.TokenType.EOF:
                finished = True
            curr_token = None
            if finished:
                break

    def process_token(self, curr_token):
        pass




