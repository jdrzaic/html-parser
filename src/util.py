class Reader(object):

    EOF = chr(-1)

    def __init__(self, input):
        self.input = input
        self.current_pos = 0

    def consume(self):
        return self.EOF if self.current_pos >= len(self.input) else input[self.current_pos]

    def consume_data(self):
        pass

    def consume_to(self, delimiter):
        pass

    def consume_to_any_of(self, delimiters):
        pass

    def consume_word(self):
        pass

    def current(self):
        return self.input[self.current_pos]

    def advance(self):
        pass

    def empty(self):
        pass

    def consume_tag_name(self):
        pass

    def unconsume(self):
        pass

    def match_letter(self):
        pass

    def match(self, char):
        pass