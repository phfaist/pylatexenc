# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2019 Philippe Faist
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#


# Internal module. Internal API may move, disappear or otherwise change at any
# time and without notice.

import re
import logging
logger = logging.getLogger(__name__)


from ._exctypes import LatexWalkerEndOfStream
from ._token import LatexToken


class LatexTokenReaderBase(object):
    def __init__(self, **kwargs):
        super(LatexTokenReaderBase, self).__init__(**kwargs)


    def make_token(self, **kwargs):
        return LatexToken(**kwargs)

    def move_to_token(self, tok, rewind_pre_space=True):
        raise RuntimeError(
            "LatexTokenReaderBase subclasses must reimplement rewind_to_token()"
        )

    def move_past_token(self, tok, fastforward_post_space=True):
        raise RuntimeError(
            "LatexTokenReaderBase subclasses must reimplement move_past_token()"
        )

    def peek_token(self, parsing_state):
        raise RuntimeError(
            "LatexTokenReaderBase subclasses must reimplement peek_token()"
        )

    def peek_token_or_none(self, parsing_state):
        try:
            self.peek_token(parsing_state=parsing_state)
        except LatexWalkerEndOfStream:
            return None

    def next_token(self, parsing_state):
        tok = self.peek_token(parsing_state=parsing_state)
        self.move_past_token(tok)
        return tok

    def cur_pos(self):
        raise RuntimeError("LatexTokenReaderBase subclasses must reimplement cur_pos()")

    def final_pos(self):
        raise RuntimeError("LatexTokenReaderBase subclasses must reimplement final_pos()")

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
        try:
            # transcrypt doesn't seem to support default value in next(iter, default)
            i = next( (j for j, t in enumerate(self.token_list) if t is tok) )
        except StopIteration:
            raise IndexError("{}({!r}): no such token in list".format(methname, tok))
        return i

    def move_to_token(self, tok, rewind_pre_space=True):
        self._idx = self._find_tok_idx(tok, 'move_to_token')

    def move_past_token(self, tok, fastforward_post_space=True):
        self._idx = self._find_tok_idx(tok, 'move_past_token') + 1

    def cur_pos(self):
        return self.peek_token(None).pos

    def final_pos(self):
        return self.token_list[len(self.token_list)-1].pos_end




