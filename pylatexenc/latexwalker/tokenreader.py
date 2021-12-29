import re

import logging

logger = logging.getLogger(__name__)



class LatexTokenReader(object):
    r"""
    Parse tokens from an input string.

    ...................

    .. versionadded:: 3.0

       The `LatexTokenReader` class was introduced in `pylatexenc` 3.
    """
    def __init__(self, s):
        super(LatexTokenReader, self).__init__()
        self.s = s

        self._pos = 0

        self._rx_environment_name = \
            re.compile(r'^\{(?P<environmentname>[\w* ._-]+)\}')


    def _advance_to_pos(self, pos):
        self._pos = pos


    def make_token(self, **kwargs):
        return LatexToken(**kwargs)



    def skip_space(self, parsing_state):
        r"""
        Move internal position to skip any whitespace.  The position pointer is left
        immediately after any encountered whitespace.  If the current pointed
        position is not whitespace, the position is not advanced.

        If `parsing_state.enable_double_newline_paragraphs` is set, then two
        consecutive newlines do not count as whitespace.

        Returns the string of whitespace characters that was skipped.
        """

        (space, space_pos, space_len) = \
            self.impl_peek_space(self.s, self._pos, self.parsing_state, self)

        self._advance_to_pos(space_pos + space_len)

        return (space, space_pos, space_len)

    def peek_space(self, parsing_state):
        return self.impl_peek_space(self.s, self._pos, parsing_state)


    def next_token(self, parsing_state):
        tok = self.peek_token(parsing_state=parsing_state)
        self._advance_to_pos(tok.pos+tok.len)
        return tok

    def rewind_last_token(self, tok, rewind_pre_space=True):
        if self._pos != (tok.pos+tok.len):
            raise ValueError(
                "rewind_last_token(): The given token is not the last token read"
            )
        if rewind_pre_space:
            new_pos = tok.pos - len(tok.pre_space)
        else:
            new_pos = tok.pos
        self._advance_to_pos(new_pos)

    def rewind_to_pos(self, pos):
        if pos > self._pos:
            raise ValueError("Internal error, rewind_to_pos() requires a position that is "
                             "*before* the current position, got %d > %d" % (pos, self._pos))
        self._advance_to_pos(pos)

    def jump_to_pos(self, pos):
        self._advance_to_pos(pos)


    def peek_token(self, parsing_state):

        # shorthands (& to avoid repeated lookups)
        s = self.s
        len_s = len(s)
        pos = self._pos

        pre_space, space_pos, space_len = self.impl_peek_space(s, pos, parsing_state)

        pos = space_pos + space_len
        if pos >= len_s:
            raise LatexWalkerEndOfStream(final_space=pre_space)

        # first, see if we have a new paragraph token
        if pos < len_s - 2  \
           and s[pos] == '\n' and s[pos+1] == '\n'  \
           and parsing_state.enable_double_newline_paragraphs:
            # two \n's indicate new paragraph.
            try:
                sspec = parsing_state.latex_context.get_specials_spec(
                    specials_chars='\n\n',
                    raise_if_not_found=True
                )
                return self.make_token(tok='specials', arg=sspec,
                                       pos=pos, len=2,
                                       pre_space=pre_space)
            except KeyError:
                return self.make_token(tok='char', arg='\n\n',
                                       pos=pos, len=2,
                                       pre_space=pre_space)

        c = s[pos]

        # check if we have a math mode delimiter
        if c in parsing_state._math_delims_info_startchars:
            t = self.impl_maybe_read_math_mode_delimiter(s, pos, parsing_state, pre_space)
            if t is not None:
                return t
            # continue, we have some other token ->

        # check if we have an environment
        if parsing_state.enable_environments \
           and s.startswith( ('\\begin', '\\end',) , pos ):
            # \begin{environment} or \end{environment}
            return self.impl_read_environment(s=s, pos=pos,
                                              parsing_state=parsing_state,
                                              pre_space=pre_space)

        # check if we have a macro
        if c == '\\':
            return self.impl_read_macro(s=s, pos=pos,
                                        parsing_state=parsing_state,
                                        pre_space=pre_space)

        # check if we have a latex comment
        if c == '%': 
            return self.impl_read_comment(s=s, pos=pos,
                                          parsing_state=parsing_state,
                                          pre_space=pre_space)


        if c in parsing_state._latex_group_delimchars_by_open:
            return self.make_token(tok='brace_open', arg=c, pos=pos, len=1,
                                   pre_space=pre_space)
        if c in parsing_state._latex_group_delimchars_close:
            return self.make_token(tok='brace_close', arg=c, pos=pos, len=1,
                                   pre_space=pre_space)

        sspec = parsing_state.latex_context.test_for_specials(
            s, pos, parsing_state=parsing_state
        )
        if sspec is not None:
            return self.make_token(tok='specials', arg=sspec,
                                   pos=pos, len=len(sspec.specials_chars),
                                   pre_space=pre_space)

        # otherwise, the token is a normal 'char' type.

        return self.make_token(tok='char', arg=c, pos=pos, len=1, pre_space=pre_space)




    def impl_peek_space(self, s, pos, parsing_state):
        r"""
        Look at the string `s`, and identify how many characters need to be skipped
        in order to skip whitespace.  Does not update the internal position
        pointer.

        Return a tuple `(space_string, pos, len)` where `space_string` is the
        string of whitespace characters that would be skipped at the current
        position pointer (reported in `pos`).  `len` is the length of the space
        string.

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
        return (space, pos, p2-pos)


    def maybe_read_math_mode(self, s, pos, parsing_state, pre_space):
        if parsing_state.in_math_mode:
            # looking for closing math mode
            expecting_close = parsing_state._math_expecting_close_delim_info
            expecting_close_delim = expecting_close['close_delim']
            expecting_close_tok = expecting_close['tok']
            if s.startswith(expecting_close_delim):
                return self.make_token(tok=expecting_close_tok, arg=expecting_close_delim,
                                       pos=pos, len=len(expecting_close_delim),
                                       pre_space=pre_space)
            return None

        # see if we have an opening math mode
        for delim in parsing_state._math_delims_by_len:
            if s.startswith(delim, pos):
                info = parsing_state._math_delims_info_by_open[delim]
                # found open math delimiter
                return self.make_token(tok=info['tok'], arg=delim,
                                       pos=pos, len=len(delim),
                                       pre_space=space)

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
                recovery_token_placeholder=LatexToken(
                    tok='char',
                    arg='',
                    pos=pos,
                    len=0,
                    pre_space=pre_space
                ),
                recovery_pos=len(s)
            )

        c = s[pos+1] # next char is necessarily part of macro
        macro = c

        # following chars part of macro only if all are alphabetical
        isalphamacro = (c in parsing_state.macro_alpha_chars)
        i = 2
        if isalphamacro:
            while pos + i < len(s) and (s[pos+i] in parsing_state.macro_alpha_chars):
                macro += s[pos+i]
                i += 1

        # get the following whitespace, and store it in the macro's post_space
        post_space = ''
        if isalphamacro:
            post_space, post_space_pos, post_space_len = \
                self.impl_peek_space(s, pos+i, parsing_state)
            i +=  post_space_pos + post_space_len - (pos + i)

        return self.make_token(tok='macro', arg=macro,
                               pos=pos, len=i,
                               pre_space=pre_space, post_space=post_space)


    def impl_read_environment(self, s, pos, parsing_state, pre_space):

        if s.startswith('\\begin', pos):
            beginend = 'begin'
        elif s.startswith('\\end', pos):
            beginend = 'end'
        else:
            raise ValueError(
                "Internal error, expected ‘\\begin’ or ‘\\end’ in read_environment"
            )

        envmatch = self._rx_environment_name.match(s, pos)
        if envmatch is None:
            tokarg = '\\'+beginend
            raise LatexWalkerTokenParseError(
                msg=r"Bad ‘\{}’ call: expected {{environmentname}}".format(beginend),
                len=i,
                recovery_token_placeholder=LatexToken(
                    tok='char',
                    arg=tokarg,
                    pos=pos,
                    len=len(tokarg),
                    pre_space=pre_space
                ),
                recovery_pos=pos+len(tokarg),
            )

        return self.make_token(
            tok=(beginend+'_environment'),
            arg=envmatch.group('environmentname'),
            pos=pos,
            len=envmatch.end()-pos,
            pre_space=pre_space,
        )
        

    def impl_read_comment(self, s, pos, parsing_state, pre_space):

        if s[pos] != '%':
            raise ValueError("Internal error, expected ‘%’ in read_comment()")

        sppos = s.find('\n', pos)
        if sppos == -1:
            # reached end of string
            comment_content_offset = len(s) - pos
            comment_with_whitespace_len = comment_content_len
            post_space = ''
        else:
            # skip whitespace, starting from the first \n that finishes the
            # comment
            post_space, post_space_pos, post_space_len = \
                self.impl_peek_space(s, sppos, parsing_state)
            comment_content_offset = sppos - pos
            comment_with_whitespace_len = post_space_pos + post_space_len - pos

        return self.make_token(
            tok='comment',
            arg=s[pos+1:pos+comment_content_offset],
            pos=pos,
            len=comment_with_whitespace_len,
            pre_space=pre_space,
            post_space=post_space
        )
    







