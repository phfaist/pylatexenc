import re
import logging
logger = logging.getLogger(__name__)



class LatexTokenReaderBase(object):
    def __init__(self, **kwargs):
        super(LatexTokenReaderBase, self).__init__(**kwargs)


    def make_token(self, **kwargs):
        return LatexToken(**kwargs)

    def move_to_token(self, tok):
        raise RuntimeError(
            "LatexTokenReaderBase subclasses must reimplement rewind_to_token()"
        )

    def move_past_token(self, tok):
        raise RuntimeError(
            "LatexTokenReaderBase subclasses must reimplement fastforward_past_token()"
        )

    def peek_token(self, parsing_state):
        raise RuntimeError(
            "LatexTokenReaderBase subclasses must reimplement peek_token()"
        )

    def next_token(self, parsing_state):
        tok = self.peek_token(parsing_state=parsing_state)
        self.fastforward_past_token(tok)
        return tok

    def cur_pos(self):
        raise RuntimeError("LatexTokenReaderBase subclasses must reimplement cur_pos()")

    def skip_space_chars(self, parsing_state):
        raise RuntimeError("This token reader does not support character-level access")

    def peek_chars(self, num_chars, parsing_state):
        raise RuntimeError("This token reader does not support character-level access")

    def next_chars(self, num_chars, parsing_state):
        raise RuntimeError("This token reader does not support character-level access")

    def move_to_pos_chars(self, pos):
        raise RuntimeError("This token reader does not support character-level access")




# ----------------------------


class LatexTokenListTokenReader(LatexTokenReaderBase):
    r"""
    A token reader object that simply yields tokens from a list of
    already-parsed tokens.

    This object doesn't parse any LaTeX code.  Use `LatexTokenReader`
    for that.
    """
    def __init__(self, token_list):
        self.token_list = token_list
        self._idx = 0

    def peek_token(self, parsing_state):
        if self._idx >= len(self.token_list):
            raise LatexWalkerEndOfStream()
        return self.token_list[self._idx]

    def next_token(self, parsing_state):
        # optimize implementation because the base class calls
        # fastforward_after_token(), which needs to look up the token in the
        # token_list again
        tok = self.peek_token(parsing_state)
        self._idx += 1
        return tok

    def _find_tok_idx(self, tok, methname):
        i = next([j for j, t in enumerate(self.token_list) if t is tok], None)
        if i is None:
            raise IndexError("{}({!r}): no such token in list".format(methname, tok))
        return i

    def move_to_token(self, tok):
        self._idx = self._find_tok_idx(tok, 'move_to_token')

    def move_past_token(self, tok):
        self._idx = self._find_tok_idx(tok, 'move_past_token') + 1

    def cur_pos(self):
        return peek_token(None).pos




