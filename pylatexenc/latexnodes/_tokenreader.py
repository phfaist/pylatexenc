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
    LatexTokenReader(s, *, tolerant_parsing=False)

    Parse tokens from an input string to create :py:class:`LatexToken`
    instances.

    Inherits :py:class:`LatexTokenReaderBase`.  See also the methods there for
    the standard token reader interface (such as
    :py:meth:`LatexTokenReaderBase.peek_token()` and friends).

    The main functionality of this class is coded in the `impl_***()` methods.
    To extend this class with custom functionality, you should reimplement
    those.  The methods reimplemented from :py:class:`LatexTokenReaderBase` add
    layers of exception catching and recovery, etc., so be wary of
    reimplementing them manually.

    Attributes:

    .. py::attribute:  s

       The string that is being parsed.  Do NOT modify this attribute!

    .. py::attribute:  tolerant_parsing

       Whether or not we are in tolerant parsing mode.  In tolerant parsing
       mode, we go out of our way to recover from errors to produce some kind of
       useful tokens.  If not in tolerant parsing mode, then parsing is strict
       and errors are raised immediately so that they can be traced down and
       debugged more easily.


    .. versionadded:: 3.0

       The :py:class:`LatexTokenReader` class was introduced in `pylatexenc 3.0`.
    """
    def __init__(self, s, **kwargs):
        super(LatexTokenReader, self).__init__()
        self.s = s
        
        self.tolerant_parsing = kwargs.pop('tolerant_parsing', False)
        
        if kwargs:
            raise ValueError("Invalid argument(s) to LatexTokenReader: {!r}"
                             .format(kwargs))

        self._pos = 0

    def move_to_token(self, tok, rewind_pre_space=True):
        r"""
        Reimplemented from :py:meth:`LatexTokenReaderBase.move_to_token()`.
        """
        if rewind_pre_space:
            new_pos = tok.pos - len(tok.pre_space)
        else:
            new_pos = tok.pos
        self._advance_to_pos(new_pos)

    def move_past_token(self, tok, fastforward_post_space=True):
        r"""
        Reimplemented from :py:meth:`LatexTokenReaderBase.move_past_token()`.
        """
        new_pos = tok.pos_end

        # note tok.pos_end already points past post_space (in contrast to pre_space)
        if not fastforward_post_space:
            post_space = getattr(tok, 'post_space', None)
            if post_space:
                new_pos -= len(post_space)

        self._advance_to_pos(new_pos)


    def peek_chars(self, num_chars, parsing_state):
        r"""
        Reimplemented from :py:meth:`LatexTokenReaderBase.peek_chars()`.
        """
        if self._pos >= len(self.s):
            raise LatexWalkerEndOfStream()
        return self.s[self._pos:self._pos+num_chars]

    def next_chars(self, num_chars, parsing_state):
        r"""
        Reimplemented from :py:meth:`LatexTokenReaderBase.next_chars()`.
        """
        chars = self.peek_chars(num_chars, parsing_state)
        self._pos += num_chars
        if self._pos > len(self.s):
            self._pos = len(self.s)
        return chars

    def cur_pos(self):
        r"""
        Reimplemented from :py:meth:`LatexTokenReaderBase.cur_pos()`.
        """
        return self._pos

    # def final_pos(self):
    #     return len(self.s)

    def move_to_pos_chars(self, pos):
        r"""
        Reimplemented from :py:meth:`LatexTokenReaderBase.move_to_pos_chars()`.
        """
        self._advance_to_pos(pos)


    def _advance_to_pos(self, pos):
        self._pos = pos


    def skip_space_chars(self, parsing_state):
        r"""
        Move internal position to skip any whitespace.  The position pointer is left
        immediately after any encountered whitespace.  If the current pointed
        position is not whitespace, the position is not advanced.

        If `parsing_state.enable_double_newline_paragraphs` is set, then two
        consecutive newlines do not count as whitespace.

        Returns the string of whitespace characters that was skipped.

        Reimplemented from :py:meth:`LatexTokenReaderBase.skip_space_chars()`.
        """

        (space, space_pos, space_pos_end) = \
            self.impl_peek_space_chars(self.s, self._pos, parsing_state)

        self._advance_to_pos(space_pos_end)

        return (space, space_pos, space_pos_end)

    def peek_space_chars(self, parsing_state):
        r"""
        Reimplemented from :py:meth:`LatexTokenReaderBase.peek_space_chars()`.
        """
        return self.impl_peek_space_chars(self.s, self._pos, parsing_state)


    def peek_token(self, parsing_state):
        r"""
        Read a single token without updating the current position pointer.  Returns
        the token that was parsed.

        Parse errors while reading the token are handled differently whether or
        not we are in tolerant parsing mode.  (See :py:attr:`tolerant_parsing`
        attribute and constructor argument.)  If not in tolerant mode, the error
        is raised.  When in tolerant parsing mode, the error is translated into
        a "recovery token" provided by the error object.  The "recovery token"
        is returned as if no error had occurred, in order to continue parsing.

        Reimplemented from :py:meth:`LatexTokenReaderBase.peek_token()`.
        """

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

    # ---


    def impl_peek_token(self, parsing_state):
        r"""
        Read a single token and return it.

        If the end of stream is reached, raise :py:exc:`LatexWalkerEndOfStream`
        (regardless of whether or not we are in tolerant parsing mode).
        """

        logger.debug("impl_peek_token(): parsing_state = %r, pos=%r", parsing_state, self._pos)

        # shorthands (& to avoid repeated lookups to self.XXX)
        s = self.s
        len_s = len(s)
        pos = self._pos

        pre_space, space_pos, space_pos_end = \
            self.impl_peek_space_chars(s, pos, parsing_state)

        # first, see if we have a new paragraph token
        if parsing_state.enable_double_newline_paragraphs and pre_space.count('\n') >= 2:
            # the whitespace contained at least two newlines -- it's a new
            # paragraph token

            # identify where the first and last newline chars are
            newpar_rel_pos_start = pre_space.find('\n')
            newpar_rel_pos_end = pre_space.rfind('\n')+1 # include last newline
            # pre_space is the leading whitespace up to the first newline
            pre_space = pre_space[:newpar_rel_pos_start]
            newpar_pos_start = space_pos + newpar_rel_pos_start
            newpar_pos_end = space_pos + newpar_rel_pos_end

            if parsing_state.latex_context is not None:
                try:
                    sspec = parsing_state.latex_context.get_specials_spec(
                        specials_chars='\n\n',
                    )
                except KeyError:
                    sspec = None
                # make sure we got a spec specifically for the new paragraph
                # token and not a generic default spec object provided by
                # get_specials_spec() on failed lookup
                if sspec is not None and sspec.specials_chars == '\n\n':
                    return self.make_token(tok='specials',
                                           arg=sspec,
                                           pos=newpar_pos_start,
                                           pos_end=newpar_pos_end,
                                           pre_space=pre_space)

            par_space_tokens = s[newpar_pos_start:newpar_pos_end]
            return self.make_token(tok='char', arg=par_space_tokens, #'\n\n',
                                   pos=newpar_pos_start,
                                   pos_end=newpar_pos_end,
                                   pre_space=pre_space)

        # if all we could read is whitespsace (w/o 2+ newlines), and we're at
        # the end of the stream, we raise LatexWalkerEndOfStream.
        pos = space_pos_end
        if pos >= len_s:
            raise LatexWalkerEndOfStream(final_space=pre_space)

        # inspect the next character --

        c = s[pos]

        #logger.debug("Char at %d: %r", pos, c)

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

                #logger.debug("beginend=%r; s.startswith('begin',pos+1)=%r; s[pos+1:pos+7]=%r",
                #             beginend, s.startswith('begin', pos+1), s[pos+1:pos+7])

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
        if parsing_state.enable_comments \
           and c == parsing_state.comment_start[0] \
           and s.startswith(parsing_state.comment_start, pos):
            #
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
            #logger.debug("tested for specials at ‘%s’ -> %r", s[pos:pos+3]+'...', sspec)
            #logger.debug("get_specials_spec('&') -> %r", parsing_state.latex_context.get_specials_spec('&'))
            if sspec is not None:
                return self.make_token(tok='specials', arg=sspec,
                                       pos=pos, pos_end=pos+len(sspec.specials_chars),
                                       pre_space=pre_space)

        # otherwise, the token is a normal 'char' type.

        return self.impl_char_token(c, pos, pos+1, parsing_state, pre_space)


    def impl_peek_space_chars(self, s, pos, parsing_state):
        r"""
        Look at the string `s`, and identify how many characters need to be skipped
        in order to skip whitespace.  Does not update the internal position
        pointer.

        Return a tuple `(space_string, pos, pos_end)` where `space_string` is
        the string of whitespace characters that would be skipped at the current
        position pointer (reported in `pos`).  The integer `pos_end` is the
        position immediately after the space characters.

        No exception is raised if we encounter the end of the stream, we simply
        stop looking for more spaces.
        """

        p2 = pos
        # enable_double_newline_paragraphs = \
        #     parsing_state.enable_double_newline_paragraphs

        space = ''

        while True:
            if p2 >= len(s):
                break
            c = s[p2]
            if not c.isspace():
                break
            space += c
            p2 += 1

            # ### new paragraphs handled differently now -- parser will count
            # ### number of newlines in returned whitespace
            #
            # if space.endswith('\n\n') and enable_double_newline_paragraphs:
            #     # two \n's indicate new paragraph.
            #     space = space[:-2]
            #     p2 = p2 - 2
            #     break

        # encountered end of space
        return (space, pos, p2)


    def impl_char_token(self, c, pos, pos_end, parsing_state, pre_space):
        r"""
        Read a character token.

        This method checks that the given character is not a forbidden
        character, see :py:attr:`ParsingState.forbidden_characters`.
        """
        if c in parsing_state.forbidden_characters:
            raise LatexWalkerTokenParseError(
                s=self.s,
                pos=pos,
                msg="Character is forbidden here: ‘{}’ ({:#x})".format(c, ord(c)),
                error_type_info={
                    'what': 'token_forbidden_character',
                    'forbidden_character': c
                },
                recovery_token_placeholder=self.make_token(
                    tok='char',
                    arg=c,
                    pos=pos,
                    pos_end=pos_end,
                    pre_space=pre_space
                ),
                recovery_token_at_pos=pos_end,
            )
        return self.make_token(tok='char', arg=c, pos=pos, pos_end=pos_end, pre_space=pre_space)


    def impl_maybe_read_math_mode_delimiter(self, s, pos, parsing_state, pre_space):
        r"""
        See if we can read a math mode delimiter token.  This method is called only
        after a first check (math mode is enabled in parsing state, and the
        character is one of the first characters of known math mode delimiters).

        Return the math mode token, or `None` if we didn't encounter a math mode
        delimiter.
        """

        if parsing_state.in_math_mode:
            # looking for closing math mode
            expecting_close = parsing_state._math_expecting_close_delim_info
            # expecting_close can be None even in math mode, e.g., inside a math
            # environment \begin{align} ... \end{align}
            if expecting_close is not None:
                expecting_close_delim = expecting_close['close_delim']
                expecting_close_tok = expecting_close['tok']
                logger.debug("expecting close math mode delimiter: delim %r, tok %r",
                             expecting_close_delim, expecting_close_tok)
                if s.startswith(expecting_close_delim, pos):
                    logger.debug("we did encounter that expected delim & tok at pos = %r;"
                                 "we have s[pos:pos+10]=%r",
                                 pos, s[pos:pos+10])
                    return self.make_token(tok=expecting_close_tok,
                                           arg=expecting_close_delim,
                                           pos=pos,
                                           pos_end=pos+len(expecting_close_delim),
                                           pre_space=pre_space)

        # see if we have a math mode delimiter; either an opening delimiter
        # while not in math mode or an unexpected open/close delimiter.  It's
        # not our job here to detect parse errors, we simply report the
        # delimiter and let the parsers report syntax errors.  We do need some
        # minimal logic to choose between different possible delimiters, though,
        # like matching the expected closing delimiter above.

        #print(f"{parsing_state._math_all_delims_by_len=}")

        for delim, tok_type in parsing_state._math_all_delims_by_len:
            if s.startswith(delim, pos):
                logger.debug("Encountered opening math delim %r (tok %r) at pos = %r;"
                             "we have s[pos:pos+10]=%r",
                             delim, tok_type, pos, s[pos:pos+10])
                return self.make_token(tok=tok_type, arg=delim,
                                       pos=pos, pos_end=pos+len(delim),
                                       pre_space=pre_space)

        return None


    def impl_read_macro(self, s, pos, parsing_state, pre_space):
        r"""
        Read a macro call token.  Called when the character at the current position
        is a macro escape character (usually ``\``, see
        :py:attr:`ParsingState.macro_escape_char`).

        Macro characters that form long macro names are determined by the
        py:attr:`ParsingState.macro_alpha_chars` attribute.

        Return the macro token.
        """

        if s[pos] != parsing_state.macro_escape_char:
            raise ValueError("Internal error, expected '\\' in impl_read_macro()")

        # read information for an escape sequence

        if pos+1 >= len(s):
            raise LatexWalkerTokenParseError(
                s=s,
                pos=pos+1,
                msg=(
                    "Expected macro name after ‘{}’ escape character"
                    .format(parsing_state.macro_escape_char)
                ),
                error_type_info={
                    'what': 'token_end_of_stream_immediately_after_escape_character',
                },
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

            # but make sure we put back whitespace that breaks into a new paragraph:
            if post_space.count('\n') >= 2:
                # only keep whitespace up to the first newline character
                newline_rel_pos = post_space.find('\n')
                post_space_pos_end = post_space_pos + newline_rel_pos
                post_space = post_space[:newline_rel_pos]

            posi = post_space_pos_end

        return self.make_token(tok='macro', arg=macro,
                               pos=pos, pos_end=posi,
                               pre_space=pre_space, post_space=post_space)



    # don't use '\w' for alphanumeric char, can get surprises especially if
    # we try to run our code on other platforms (eg brython) where the
    # environment name might otherwise not be matched correctly
    rx_environment_name = \
        re.compile(r'''\s*\{(?P<environmentname>[A-Za-z0-9*._ :/!^()\[\]-]+)\}''')
    r"""
    A regular expression that will read the environment name after encountering
    the ``\begin`` or ``\end`` constructs.
    """

    def parse_latex_environment_name(self, pos, beginend, pos_envname):
        r"""
        Parse an environment name in curly braces after encountering ``\begin`` or
        ``\end``.

        We allow for whitespace, an opening brace, a macro name with normal
        ASCII alphanumeric characters and some standard punctuation, and a
        closing curly brace.

        We use the regular expression stored as the class attribute
        `rx_environment_name`.  To override it, you can simply set this
        attribute to your token reader object instance, e.g.,
        ``my_token_reader.rx_environment_name = .....``

        Return a tuple `(environmentname, environment_match_end_pos)`.  If the
        environment name could not be read because of a parse error, then return
        `(None, None)`.
        """

        # I might want to pass this code into transcrypt (->Javascript), where
        # rx.match(s, pos) is not supported ...
        envmatch = self.rx_environment_name.match(self.s[pos_envname:]) #self.s, pos_envname)
        if envmatch is None:
            return None, None

        envmatch_end_pos = pos_envname + envmatch.end()

        return envmatch.group('environmentname'), envmatch_end_pos


    def impl_read_environment(self, s, pos, parsing_state, beginend, pre_space):
        r"""
        Parse a ``\begin{environmentname}`` or ``\end{environmentname}`` token.

        This method is called after we have seen that at the position `pos` in
        the string we indeed have ``\begin`` or ``\end`` (or with the current
        escape character instead of ``\``).

        Return the parsed token.
        """

        if s[pos:pos+1+len(beginend)] != parsing_state.macro_escape_char + beginend:
            raise ValueError(
                "Internal error, expected ‘{}{}’ in read_environment()"
                .format(parsing_state.macro_escape_char, beginend)
            )

        pos_envname = pos + 1 + len(beginend)

        environment_name, environment_pos_end = \
            self.parse_latex_environment_name(pos, beginend, pos_envname)

        logger.debug("Getting environment name at %r -> %r, is {align}?=%r",
                     '...|'+s[pos_envname:pos_envname+35]+'|...',
                     environment_pos_end,
                     (s[pos_envname:pos_envname+len('{align}')] == '{align}')
                     )

        if environment_name is None:
            tokarg = parsing_state.macro_escape_char + beginend
            raise LatexWalkerTokenParseError(
                s=s,
                msg=r"Bad ‘\{}’ call: expected {{environmentname}}".format(beginend),
                pos=pos,
                error_type_info={
                    'what': 'token_error_parse_beginend_environment_name',
                    'beginend': beginend,
                    'macro_beginend': tokarg,
                },
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
            arg=environment_name,
            pos=pos,
            pos_end=environment_pos_end,
            pre_space=pre_space,
        )
        logger.debug("read environment token %r", env_token)
        return env_token

    def impl_read_comment(self, s, pos, parsing_state, pre_space):
        r"""
        Parse and return a comment token.

        We also parse the post-space and include it in the token object. New
        paragraph tokens are never included in the comment's post-space
        attribute.
        """

        if not s.startswith(parsing_state.comment_start, pos):
            raise ValueError("Internal error, expected comment start ‘{}’ in read_comment()"
                             .format(parsing_state.comment_start))

        pos_inner_start = pos+len(parsing_state.comment_start)

        sppos = s.find('\n', pos_inner_start)
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

            # but make sure we put back whitespace that breaks into a new paragraph:
            if post_space.count('\n') >= 2:
                # only keep whitespace up to the first newline character
                newline_rel_pos = post_space.find('\n')
                post_space_pos_end = post_space_pos + newline_rel_pos
                post_space = post_space[:newline_rel_pos]

            comment_pos_end = sppos
            comment_with_whitespace_pos_end = post_space_pos_end

        return self.make_token(
            tok='comment',
            arg=s[pos_inner_start:comment_pos_end],
            pos=pos,
            pos_end=comment_with_whitespace_pos_end,
            pre_space=pre_space,
            post_space=post_space
        )
    



