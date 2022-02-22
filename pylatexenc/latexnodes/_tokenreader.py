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

from __future__ import print_function, unicode_literals


import re
import logging
logger = logging.getLogger(__name__)

from ._exctypes import LatexWalkerTokenParseError, LatexWalkerEndOfStream

from ._token import LatexToken
from ._tokenreaderbase import LatexTokenReaderBase


class LatexTokenReader(LatexTokenReaderBase):
    r"""
    Parse tokens from an input string.

    ...................

    .. versionadded:: 3.0

       The `LatexTokenReader` class was introduced in `pylatexenc` 3.
    """
    def __init__(self, s, **kwargs):
        super(LatexTokenReader, self).__init__()
        self.s = s
        
        self.tolerant_parsing = kwargs.pop('tolerant_parsing', False)
        
        if kwargs:
            raise ValueError("Invalid argument(s) to LatexTokenReader: {!r}"
                             .format(kwargs))

        self._pos = 0

        # don't use '\w' for alphanumeric char, can get surprises especially if
        # we try to run our code on other platforms (eg brython) where the
        # environment name might otherwise not be matched correctly
        self._rx_environment_name = \
            re.compile(r'\s*\{(?P<environmentname>[A-Za-z0-9* ._-]+)\}')

    def move_to_token(self, tok, rewind_pre_space=True):
        if rewind_pre_space:
            new_pos = tok.pos - len(tok.pre_space)
        else:
            new_pos = tok.pos
        self._advance_to_pos(new_pos)

    def move_past_token(self, tok, fastforward_post_space=True):
        new_pos = tok.pos_end

        # note tok.pos_end already points past post_space (in contrast to pre_space)
        if not fastforward_post_space:
            post_space = getattr(tok, 'post_space', None)
            if post_space:
                new_pos -= len(post_space)

        self._advance_to_pos(new_pos)


    def peek_chars(self, num_chars, parsing_state):
        if self._pos >= len(self.s):
            raise LatexWalkerEndOfStream()
        return self.s[self._pos:self._pos+num_chars]

    def next_chars(self, num_chars, parsing_state):
        chars = self.peek_chars(num_chars, parsing_state)
        self._pos += num_chars
        if self._pos > len(self.s):
            self._pos = len(self.s)
        return chars

    def cur_pos(self):
        return self._pos

    def final_pos(self):
        return len(self.s)

    def move_to_pos_chars(self, pos):
        self._advance_to_pos(pos)


    def _advance_to_pos(self, pos):
        self._pos = pos

    def rewind_to_pos(self, pos):
        if pos > self._pos:
            raise ValueError("Internal error, rewind_to_pos() requires a position that is "
                             "*before* the current position, got {} > {}"
                             .format(pos, self._pos))
        self._advance_to_pos(pos)


    def skip_space_chars(self, parsing_state):
        r"""
        Move internal position to skip any whitespace.  The position pointer is left
        immediately after any encountered whitespace.  If the current pointed
        position is not whitespace, the position is not advanced.

        If `parsing_state.enable_double_newline_paragraphs` is set, then two
        consecutive newlines do not count as whitespace.

        Returns the string of whitespace characters that was skipped.
        """

        (space, space_pos, space_pos_end) = \
            self.impl_peek_space_chars(self.s, self._pos, parsing_state)

        self._advance_to_pos(space_pos_end)

        return (space, space_pos, space_pos_end)

    def peek_space_chars(self, parsing_state):
        return self.impl_peek_space_chars(self.s, self._pos, parsing_state)


    def peek_token(self, parsing_state):

        try:
            
            return self.impl_peek_token(parsing_state)

        except LatexWalkerTokenParseError as exc:
            if self.tolerant_parsing:
                # return recovery token if we're in tolerant parsing mode
                self.move_to_pos_chars(exc.recovery_token_at_pos)
                return exc.recovery_token_placeholder
            else:
                # raise it up the chain
                raise

    def impl_peek_token(self, parsing_state):

        logger.debug("impl_peek_token(): parsing_state = %r", parsing_state);

        # shorthands (& to avoid repeated lookups)
        s = self.s
        len_s = len(s)
        pos = self._pos

        pre_space, space_pos, space_pos_end = \
            self.impl_peek_space_chars(s, pos, parsing_state)

        pos = space_pos_end
        if pos >= len_s:
            raise LatexWalkerEndOfStream(final_space=pre_space)

        # first, see if we have a new paragraph token
        if (pos < len_s - 2
            and s[pos] == '\n' and s[pos+1] == '\n'
            and parsing_state.enable_double_newline_paragraphs):
            # two \n's indicate new paragraph.
            if parsing_state.latex_context is not None:
                try:
                    sspec = parsing_state.latex_context.get_specials_spec(
                        specials_chars='\n\n',
                    )
                except KeyError:
                    sspec = None
                if sspec is not None:
                    return self.make_token(tok='specials',
                                           arg=sspec,
                                           pos=pos,
                                           pos_end=pos+2,
                                           pre_space=pre_space)
            return self.make_token(tok='char', arg='\n\n',
                                   pos=pos, pos_end=pos+2,
                                   pre_space=pre_space)

        c = s[pos]

        logger.debug("Char at %d: %r", pos, c)

        # check if we have a math mode delimiter
        if c in parsing_state._math_delims_info_startchars and parsing_state.enable_math:
            t = self.impl_maybe_read_math_mode_delimiter(s, pos, parsing_state, pre_space)
            if t is not None:
                return t
            # continue, we have some other token ->

        if c == parsing_state.macro_escape_char:

            # check if we have an environment
            if parsing_state.enable_environments:
                if s.startswith('begin', pos+1):
                    beginend = 'begin'
                elif s.startswith('end', pos+1):
                    beginend = 'end'
                else:
                    beginend = None

                logger.debug("beginend=%r; s.startswith('begin',pos+1)=%r; s[pos+1:pos+7]=%r",
                             beginend, s.startswith('begin', pos+1), s[pos+1:pos+7])

                if beginend:
                    pastbeginendpos = pos+1+len(beginend)
                    if pastbeginendpos >= len(s) \
                       or s[pastbeginendpos] not in parsing_state.macro_alpha_chars:
                        # \begin{environment} and not e.g. \beginmetastate, or
                        # \end{environment} and not e.g. \endcsname
                        return self.impl_read_environment(s=s, pos=pos,
                                                          parsing_state=parsing_state,
                                                          beginend=beginend,
                                                          pre_space=pre_space)
                # otherwise we have a macro ->

            # we must have a macro
            if parsing_state.enable_macros:
                return self.impl_read_macro(s=s, pos=pos,
                                            parsing_state=parsing_state,
                                            pre_space=pre_space)

        # check if we have a latex comment
        if c == parsing_state.comment_char and parsing_state.enable_comments:
            return self.impl_read_comment(s=s, pos=pos,
                                          parsing_state=parsing_state,
                                          pre_space=pre_space)


        if parsing_state.enable_groups:
            if c in parsing_state._latex_group_delimchars_by_open:
                return self.make_token(tok='brace_open', arg=c, pos=pos, pos_end=pos+1,
                                       pre_space=pre_space)
            if c in parsing_state._latex_group_delimchars_close:
                return self.make_token(tok='brace_close', arg=c, pos=pos, pos_end=pos+1,
                                       pre_space=pre_space)

        if parsing_state.latex_context is not None and parsing_state.enable_specials:
            sspec = parsing_state.latex_context.test_for_specials(
                s, pos, parsing_state=parsing_state
            )
            if sspec is not None:
                return self.make_token(tok='specials', arg=sspec,
                                       pos=pos, pos_end=pos+len(sspec.specials_chars),
                                       pre_space=pre_space)

        # otherwise, the token is a normal 'char' type.

        return self.make_token(tok='char', arg=c, pos=pos, pos_end=pos+1, pre_space=pre_space)




    def impl_peek_space_chars(self, s, pos, parsing_state):
        r"""
        Look at the string `s`, and identify how many characters need to be skipped
        in order to skip whitespace.  Does not update the internal position
        pointer.

        Return a tuple `(space_string, pos, pos_end)` where `space_string` is
        the string of whitespace characters that would be skipped at the current
        position pointer (reported in `pos`).  The integer `pos_end` is the
        position immediately after the space characters.

        No exceptions is raised if we encounter the end of the stream, we simply
        stop looking for more spaces.
        """

        p2 = pos
        enable_double_newline_paragraphs = \
            parsing_state.enable_double_newline_paragraphs

        space = ''

        while True:
            if p2 >= len(s):
                break
            c = s[p2]
            if not c.isspace():
                break
            space += c
            p2 += 1

            if space.endswith('\n\n') and enable_double_newline_paragraphs:
                # two \n's indicate new paragraph.
                space = space[:-2]
                p2 = p2 - 2
                break

        # encountered end of space
        return (space, pos, p2)


    def impl_maybe_read_math_mode_delimiter(self, s, pos, parsing_state, pre_space):

        if parsing_state.in_math_mode:
            # looking for closing math mode
            expecting_close = parsing_state._math_expecting_close_delim_info
            # expecting_close can be None even in math mode, e.g., inside a math
            # environment \begin{align} ... \end{align}
            if expecting_close is not None:
                expecting_close_delim = expecting_close['close_delim']
                expecting_close_tok = expecting_close['tok']
                if s.startswith(expecting_close_delim, pos):
                    return self.make_token(tok=expecting_close_tok, arg=expecting_close_delim,
                                           pos=pos, pos_end=pos+len(expecting_close_delim),
                                           pre_space=pre_space)

        # see if we have a math mode delimiter; either an opening delimiter
        # while not in math mode or an unexpected open/close delimiter.  It's
        # not our job here to detect parse errors, we simply report the
        # delimiter and let the parsers report syntax errors.  We do need some
        # minimal logic to choose between different possible delimiters, though,
        # like matching the expected closing delimiter above.
        #

        #print(f"{parsing_state._math_all_delims_by_len=}")

        for delim, tok_type in parsing_state._math_all_delims_by_len:
            if s.startswith(delim, pos):
                return self.make_token(tok=tok_type, arg=delim,
                                       pos=pos, pos_end=pos+len(delim),
                                       pre_space=pre_space)

        return None


    def impl_read_macro(self, s, pos, parsing_state, pre_space):

        if s[pos] != '\\':
            raise ValueError("Internal error, expected '\\' in impl_read_macro()")

        # read information for an escape sequence

        if pos+1 >= len(s):
            raise LatexWalkerTokenParseError(
                s=s,
                pos=pos+1,
                msg="Expected macro name after ‘\\’ escape character",
                recovery_token_placeholder=self.make_token(
                    tok='char',
                    arg='',
                    pos=pos,
                    pos_end=pos,
                    pre_space=pre_space
                ),
                recovery_token_at_pos=len(s)
            )

        c = s[pos+1] # next char is necessarily part of macro
        macro = c

        # following chars part of macro only if all are alphabetical
        isalphamacro = (c in parsing_state.macro_alpha_chars)
        posi = pos + 2
        if isalphamacro:
            while posi < len(s) and (s[posi] in parsing_state.macro_alpha_chars):
                macro += s[posi]
                posi += 1

        # get the following whitespace, and store it in the macro's post_space
        post_space = ''
        if isalphamacro:
            post_space, post_space_pos, post_space_pos_end = \
                self.impl_peek_space_chars(s, posi, parsing_state)
            posi = post_space_pos_end

        return self.make_token(tok='macro', arg=macro,
                               pos=pos, pos_end=posi,
                               pre_space=pre_space, post_space=post_space)


    def impl_read_environment(self, s, pos, parsing_state, beginend, pre_space):

        if s[pos:pos+1+len(beginend)] != parsing_state.macro_escape_char + beginend:
            raise ValueError(
                "Internal error, expected ‘\\{}’ in read_environment()"
                .format(beginend)
            )

        pos_envname = pos + 1 + len(beginend)

        envmatch = self._rx_environment_name.match(s, pos_envname)

        logger.debug("Getting environment name (using %r) at %r -> %r, is {align}?=%r",
                     self._rx_environment_name.pattern,
                     '...'+s[pos_envname:pos_envname+20]+'?...',
                     envmatch,
                     (s[pos_envname:pos_envname+len('{align}')] == '{align}')
                     )

        if envmatch is None:
            tokarg = parsing_state.macro_escape_char + beginend
            raise LatexWalkerTokenParseError(
                msg=r"Bad ‘\{}’ call: expected {{environmentname}}".format(beginend),
                pos=pos,
                recovery_token_placeholder=LatexToken(
                    tok='char',
                    arg=tokarg,
                    pos=pos,
                    pos_end=pos+len(tokarg),
                    pre_space=pre_space
                ),
                recovery_token_at_pos=pos+len(tokarg),
            )

        env_token = self.make_token(
            tok=(beginend+'_environment'),
            arg=envmatch.group('environmentname'),
            pos=pos,
            pos_end=envmatch.end(),
            pre_space=pre_space,
        )
        logger.debug("read environment token %r", env_token)
        return env_token

    def impl_read_comment(self, s, pos, parsing_state, pre_space):

        if s[pos] != parsing_state.comment_char:
            raise ValueError("Internal error, expected comment char ‘{}’ in read_comment()"
                             .format(parsing_state.comment_char))

        sppos = s.find('\n', pos)
        if sppos == -1:
            # reached end of string
            comment_pos_end = len(s)
            comment_with_whitespace_pos_end = len(s)
            post_space = ''
        else:
            # skip whitespace, starting from the first \n that finishes the
            # comment
            post_space, post_space_pos, post_space_pos_end = \
                self.impl_peek_space_chars(s, sppos, parsing_state)
            comment_pos_end = sppos
            comment_with_whitespace_pos_end = post_space_pos_end

        return self.make_token(
            tok='comment',
            arg=s[pos+1:comment_pos_end],
            pos=pos,
            pos_end=comment_with_whitespace_pos_end,
            pre_space=pre_space,
            post_space=post_space
        )
    







