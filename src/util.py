import token_state


class Reader(object):

    EOF = chr(-1)

    def __init__(self, input):
        self.input = input
        self.current_pos = 0

    def consume(self):
        self.current_pos += 1
        return self.EOF if self.current_pos - 1 >= len(self.input) else input[self.current_pos - 1]

    def consume_data(self):
        start = self.current_pos
        while self.current_pos < len(self.input):
            curr = self.input[self.current_pos]
            if curr in ['&', '<', token_state.NULL_CHAR]:
                return self.input[start, self.current_pos]
            self.current_pos += 1
        return self.input[start:]

    def consume_to(self, delimiter):
        old_pos = self.current_pos
        index = self.input.find(delimiter, start=self.current_pos + 1, end=len(self.input))
        if index < 0:
            self.current_pos = len(self.input)
            return self.input[old_pos:]
        self.current_pos = index
        return self.input[old_pos:self.current_pos]

    def consume_to_any_of(self, *args):
        start = self.current_pos
        while self.current_pos < len(self.input):
            for delimiter in args:
                if self.input[self.current_pos] == delimiter:
                    return self.input[start:self.current_pos]
            self.current_pos += 1
        return self.input[start:]

    def consume_word(self):
        start = self.current_pos
        while self.current_pos < len(self.input):
            curr = self.input[self.current_pos]
            if curr >= 'A' and curr <= 'Z' or curr >= 'a' and curr <= 'z' or curr.isalpha():
                self.current_pos += 1
            else:
                return self.input[start:self.current_pos]
        return self.input[start:]

    def current(self):
        return self.EOF if self.current_pos >= len(self.input) else input[self.current_pos]

    def advance(self):
        self.current_pos += 1

    def empty(self):
        return self.current_pos >= len(self.input)

    def consume_tag_name(self):
        start = self.current_pos
        while self.current_pos < len(self.input):
            curr = self.input[self.current_pos]
            if curr in ['\t', '\n', '\r', '\f', ' ', '/', token_state.NULL_CHAR]:
                return self.input[start:self.current_pos]
            self.current_pos += 1
        return self.input[start:]

    def unconsume(self):
        self.current_pos -= 1

    def match_letter(self):
        curr = self.input[self.current_pos]
        return not self.empty() and (
            (curr >= 'A' and curr <= 'Z') or (curr >= 'a' and curr <= 'z') or curr.isalpha())

    def match(self, *args):
        return self.input[self.current_pos] in args

    def match_seq_consume(self, seq):
        for i in range(len(seq)):
            if seq[i] != self.input[self.current_pos + i]:
                return False
        self.current_pos += len(seq)
        return True

    def match_seq_ic(self, seq):
        input_lc = self.input.lower()
        seq_lc = seq.lower
        for i in range(len(seq)):
            if seq[i] != input_lc[self.current_pos + i]:
                return False
        self.current_pos += len(seq)
        return True
