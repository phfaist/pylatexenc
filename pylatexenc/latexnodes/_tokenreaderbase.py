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

import logging
logger = logging.getLogger(__name__)


from ._exctypes import LatexWalkerEndOfStream
from ._token import LatexToken


class LatexTokenReaderBase(object):
    r"""
    Base class for token readers.

    A token reader is able to transform input characters (usually given as a
    single string) into *tokens*. Tokens are instances of
    :py:class:`LatexToken`.

    A token reader also has an internal position pointer that remembers where in
    the string we should continue to read more tokens.  A call to
    :py:meth:`next_token()` will both parse a new token and advance the internal
    position pointer past the token that was just read, such that future calls
    to :py:meth:`next_token()` continue parsing tokens as they appear in the
    string.

    A token reader should at minimum provide implementations to
    :py:meth:`peek_token()`, :py:meth:`move_to_token()`,
    :py:meth:`move_past_token()`, and :py:meth:`cur_pos()`.

    A token reader can (but does not have to) also provide character-level
    access to the input.  This can be used by some special parsers like verbatim
    parsers.  In this case, the token reader should implement
    :py:class:`peek_chars()`, :py:class:`next_chars()`, and
    :py:meth:`move_to_pos_chars()`.

    .. versionadded:: 3.0

       The :py:class:`LatexTokenReaderBase` class was introduced in `pylatexenc 3.0`.
    """

    def __init__(self, **kwargs):
        super(LatexTokenReaderBase, self).__init__(**kwargs)

    def make_token(self, **kwargs):
        r"""
        Return a new :py:class:`LatexToken` instance with the given parameters.  Can
        be reimplemented if you want to use a custom token class, although I'm
        not sure why you'd want to do that.
        """
        return LatexToken(**kwargs)

    def move_to_token(self, tok, rewind_pre_space=True):
        r"""
        Move the internal position pointer of this token reader to point to the
        position of the given token `tok`. That is, a subsequent call to
        :py:meth:`peek_token()` or :py:meth:`next_token()` should read the given
        token again.

        For token readers that can worry about whitespace, if
        `rewind_pre_space=True`, then the internal position is set to point on
        the whitespace that precedes the token `tok` (as specified in the
        instance `tok`); if `rewind_pre_space=False` the internal position
        pointer is set to point on the actual token after the preceding
        whitespace.
        """
        raise RuntimeError(
            "LatexTokenReaderBase subclasses must reimplement rewind_to_token()"
        )

    def move_past_token(self, tok, fastforward_post_space=True):
        r"""
        Move the internal position pointer of this token reader to point immediately
        past the given token `tok`.  That is, a subsequent call to
        :py:meth:`peek_token()` or :py:meth:`next_token()` should return the
        token that follows `tok` in the input stream.

        For token readers that can worry about whitespace, if
        `fastforward_post_space=True`, then whitespace that follows the given
        `tok` (for macro and comment nodes) is also skipped.
        """
        raise RuntimeError(
            "LatexTokenReaderBase subclasses must reimplement move_past_token()"
        )

    def peek_token(self, parsing_state):
        r"""
        Parse a single token at the current position in the input stream.  Parsing
        is influenced by the given `parsing_state`. (See
        :py:class:`ParsingState`.)

        The internal position pointer is not updated.  I.e., a subsequent call
        to `peek_token()` with the same parsing state should return the same
        token.

        If the end of stream is reached, i.e., if there are no remaining tokens
        at the current internal position, then :py:exc:`LatexWalkerEndOfStream`
        is raised.
        """
        raise RuntimeError(
            "LatexTokenReaderBase subclasses must reimplement peek_token()"
        )

    def peek_token_or_none(self, parsing_state):
        r"""
        A convenience method that calls :py:class:`peek_token()`, but that returns
        `None` instead of raising :py:exc:`LatexWalkerEndOfStream`.
        """
        try:
            return self.peek_token(parsing_state=parsing_state)
        except LatexWalkerEndOfStream:
            return None

    def next_token(self, parsing_state):
        r"""
        Same as :py:meth:`peek_token()`, but then also updates the internal position
        pointer of this token reader to advance past the token that was read.
        """
        tok = self.peek_token(parsing_state=parsing_state)
        self.move_past_token(tok)
        return tok

    def cur_pos(self):
        r"""
        Return the current internal position pointer's state.
        """
        raise RuntimeError("LatexTokenReaderBase subclasses must reimplement cur_pos()")

    def peek_space_chars(self, parsing_state):
        r"""
        Read a sequence of whitespace characters and return them.  Whitespace
        characters should be read until a nonwhitespace character is found.

        The current internal position pointer should remain as it is.
        """
        raise RuntimeError("This token reader does not support character-level access")

    def skip_space_chars(self, parsing_state):
        r"""
        Read a sequence of whitespace characters and return them.  Whitespace
        characters should be read until a nonwhitespace character is found.

        Advance internal position as whitespace characters are read.  The
        position pointer should be left immediately after any encountered
        whitespace.  If the current pointed position is not whitespace, the
        position should not be advanced.
        """
        raise RuntimeError("This token reader does not support character-level access")

    def peek_chars(self, num_chars, parsing_state):
        r"""
        Reads at most `num_chars` of characters at the current position and returns
        them.  The internal position pointer is not changed.

        If the pointer is already at the end of the string and there are no
        chars we can read, then :py:exc:`LatexWalkerEndOfStream` is raised.
        """
        raise RuntimeError("This token reader does not support character-level access")

    def next_chars(self, num_chars, parsing_state):
        r"""
        Reads at most `num_chars` of characters at the current position and returns
        them.  The internal position pointer is advanced to point immediately
        after the characters read.

        If the pointer is already at the end of the string and there are no
        chars we can read, then :py:exc:`LatexWalkerEndOfStream` is raised.
        """
        raise RuntimeError("This token reader does not support character-level access")

    def move_to_pos_chars(self, pos):
        r"""
        Move the internal position pointer to a specific character-level position in
        the input string/stream.
        """
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
        super(LatexTokenListTokenReader, self).__init__()
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




