from abc import ABCMeta
import tokeniser


class State(object):
    __metaclass__ = ABCMeta

    def read(self, reader, tokeniser):
        pass


class DataState(State):

    def read(self, reader, tokeniser):
        read = reader.curr()
        if read == "&":
            tokeniser.move_to_state(CHAR_REF_IN_DATA)
        elif read == "<":
            tokeniser.move_to_state(TAG_OPEN)


class CharRefInDataState(State):
    pass


class TagOpenState(State):
    pass


DATA = DataState()
CHAR_REF_IN_DATA = CharRefInDataState()
TAG_OPEN = TagOpenState()