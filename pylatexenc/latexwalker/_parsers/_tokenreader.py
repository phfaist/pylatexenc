
class LatexTokenReader(object):
    r"""
    Parse tokens from an input stream.  The `stream` is either a usual Python
    string, or it can be a file-like object.
    """
    def __init__(self, stream, parsing_state):
        super(LatexTokenReader, self).__init__()
        self.stream = stream
        self.parsing_state = parsing_state

    def next_token(self):

        if parsing_state is None:
            parsing_state = self.make_parsing_state() # get default parsing state

        brace_chars = [('{', '}')]

        if include_brace_chars:
            brace_chars += include_brace_chars

        if 'brackets_are_chars' in kwargs:
            if not kwargs.pop('brackets_are_chars'):
                brace_chars += [('[', ']')]

        s = self.s # shorthand

        space = '' # space that we gobble up before token

        #
        # In tolerant parsing mode, this method should not raise
        # LatexWalkerParseError.  Instead, it should return whatever token (at
        # the worst case, a placeholder chars token) it can to help the caller
        # recover from errors.
        #
        # This is because we want to recover from errors as soon as possible.
        # For instance a macro argument parser might rely on calls to
        # get_token() to parse its command arguments (say check for a starred
        # command); if an exception is raised then it will bubble up and make it
        # harder to keep the macro in some meaningful way.  We could have
        # required instead to guard each call to get_token with a try/except
        # block but it feels better to keep the same philosophy as internal
        # calls to get_latex_expression(), etc., which simply return whatever
        # they can instead of raising exceptions in tolerant parsing mode.
        #
        def _token_parse_error(msg, len, placeholder):
            e = LatexWalkerParseError(
                s=s,
                pos=pos,
                msg=msg,
                **self.pos_to_lineno_colno(pos, as_dict=True)
            )
            if self.tolerant_parsing:
                self._report_ignore_parse_error(e)
                return None, LatexToken(
                    tok='char',
                    arg=placeholder,
                    pos=pos,
                    len=len,
                    pre_space=space
                )
            return e, None

        while pos < len(s) and s[pos].isspace():
            space += s[pos]
            pos += 1
            if space.endswith('\n\n'):  # two \n's indicate new paragraph.
                space = space[:-2]
                pos = pos - 2
                try:
                    sspec = parsing_state.latex_context.get_specials_spec(
                        specials_chars='\n\n',
                        raise_if_not_found=True
                    )
                    return LatexToken(tok='specials', arg=sspec,
                                      pos=pos, len=2,
                                      pre_space=space)
                except KeyError:
                    return LatexToken(tok='char', arg='\n\n', pos=pos, len=2, pre_space=space)

        if pos >= len(s):
            raise LatexWalkerEndOfStream(final_space=space)

        if s[pos] == '\\':
            # escape sequence
            if pos+1 >= len(s):
                raise LatexWalkerEndOfStream()
            macro = s[pos+1] # next char is necessarily part of macro
            # following chars part of macro only if all are alphabetical
            isalphamacro = False
            i = 2
            if s[pos+1].isalpha():
                isalphamacro = True
                while pos+i<len(s) and s[pos+i].isalpha():
                    macro += s[pos+i]
                    i += 1

            # special treatment for \( ... \) and \[ ... \] -- "macros" for
            # inline/display math modes
            if macro in ['[', ']']:
                return LatexToken(tok='mathmode_display', arg='\\'+macro,
                                  pos=pos, len=i, pre_space=space)
            if macro in ['(', ')']:
                return LatexToken(tok='mathmode_inline', arg='\\'+macro,
                                  pos=pos, len=i, pre_space=space)

            # see if we have a begin/end environment
            if environments and macro in ['begin', 'end']:
                # \begin{environment} or \end{environment}
                envmatch = re.match(r'^\s*\{([\w* ._-]+)\}', s[pos+i:])
                if envmatch is None:
                    e, t = _token_parse_error(
                        msg=r"Bad \{} macro: expected {{environmentname}}".format(macro),
                        len=i,
                        placeholder='\\'+macro
                    )
                    if e:
                        raise e
                    return t

                return LatexToken(
                    tok=('begin_environment' if macro == 'begin' else 'end_environment'),
                    arg=envmatch.group(1),
                    pos=pos,
                    len=i+envmatch.end(), # !!: envmatch.end() counts from pos+i
                    pre_space=space
                    )

            # get the following whitespace, and store it in the macro's post_space
            post_space = ''
            if isalphamacro:
                # important, LaTeX does not consume space after non-alpha macros, like \&
                while pos+i<len(s) and s[pos+i].isspace():
                    post_space += s[pos+i]
                    i += 1
                    if post_space.endswith('\n\n'):
                        # if two \n's are encountered this signals a new
                        # paragraph, so do not include them as part of the
                        # macro's post_space.
                        post_space = post_space[:-2]
                        i -= 2
                        break

            return LatexToken(tok='macro', arg=macro, pos=pos, len=i,
                              pre_space=space, post_space=post_space)

        if s[pos] == '%':
            # latex comment
            m = re.compile(r'(\n|\r|\n\r)(?P<extraspace>\s*)').search(s, pos)
            mlen = None
            if m is not None:
                if m.group('extraspace').startswith( ('\n', '\r', '\n\r',) ):
                    # special case where there is a \n immediately following the
                    # first one -- this is a new paragraph
                    arglen = m.start()-pos
                    mlen = m.start()-pos
                    mspace = ''
                else:
                    arglen = m.start()-pos
                    mlen = m.end()-pos
                    mspace = m.group()
            else:
                arglen = len(s)-pos# [  ==len(s[pos:])  ]
                mlen = arglen
                mspace = ''
            return LatexToken(tok='comment', arg=s[pos+1:pos+arglen], pos=pos, len=mlen,
                              pre_space=space, post_space=mspace)

        # see https://stackoverflow.com/a/19343/1694896
        openbracechars, closebracechars = zip(*brace_chars)

        if s[pos] in openbracechars:
            return LatexToken(tok='brace_open', arg=s[pos], pos=pos, len=1, pre_space=space)

        if s[pos] in closebracechars:
            return LatexToken(tok='brace_close', arg=s[pos], pos=pos, len=1, pre_space=space)

        # check for math-mode dollar signs.  Using python syntax
        # "string.startswith(pattern, pos)"
        if s.startswith('$$', pos):
            # if we are in an open '$'-delimited math mode, we need to parse $$
            # as two single $'s (issue #43)
            if not (parsing_state.in_math_mode and parsing_state.math_mode_delimiter == '$'):
                return LatexToken(tok='mathmode_display', arg='$$',
                                  pos=pos, len=2, pre_space=space)
        if s.startswith('$', pos):
            return LatexToken(tok='mathmode_inline', arg='$', pos=pos, len=1, pre_space=space)

        sspec = parsing_state.latex_context.test_for_specials(
            s, pos, parsing_state=parsing_state
        )
        if sspec is not None:
            return LatexToken(tok='specials', arg=sspec,
                              pos=pos, len=len(sspec.specials_chars), pre_space=space)

        # otherwise, the token is a normal 'char' type.

        return LatexToken(tok='char', arg=s[pos], pos=pos, len=1, pre_space=space)
