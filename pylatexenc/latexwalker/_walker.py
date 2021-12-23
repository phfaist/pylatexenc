# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2021 Philippe Faist
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

from .. import _util
from .. import macrospec
from ._types import *
from ._get_defaultspecs import get_default_latex_context_db
from ._parsingstate import ParsingState

import logging
logger = logging.getLogger(__name__)



def _maketuple(*args):
    # for use with Python 2, where we don't have *args expansion in tuples and
    # lists
    return tuple(args)



# ------------------------------------------------------------------------------


# class LatexParser(object):
#     def __init__(self, walker, pos, parsing_state, flags...):
#         ....
#         self.pos = 0

#     def seek(self, pos):
#         self.pos = pos

#     def take_token(self, ....):
#         ......
        
#     def peek_token(self, ....):
#         .......


    


# ------------------------------------------------------------------------------



class LatexWalker(object):
    r"""
    A parser which walks through an input stream, parsing it as LaTeX markup.

    Arguments:

      - `s`: the string to parse as LaTeX code

      - `latex_context`: a :py:class:`pylatexenc.macrospec.LatexContextDb`
        object that provides macro and environment specifications with
        instructions on how to parse arguments, etc.  If you don't specify this
        argument, or if you specify `None`, then the default database is used.
        The default database is obtained with
        :py:func:`get_default_latex_context_db()`.

        .. versionadded:: 2.0

           This `latex_context` argument was introduced in version 2.0.

    Additional keyword arguments are flags which influence the parsing.
    Accepted flags are:

      - `tolerant_parsing=True|False` If set to `True`, then the parser
        generally ignores syntax errors rather than raising an exception.

      - `strict_braces=True|False` This option refers specifically to reading a
        encountering a closing brace when an expression is needed.  You
        generally won't need to specify this flag, use `tolerant_parsing`
        instead.

    The methods provided in this class perform various parsing of the given
    string `s`.  These methods typically accept a `pos` parameter, which must be
    an integer, which defines the position in the string `s` to start parsing.

    These methods, unless otherwise documented, return a tuple `(node, pos,
    len)`, where node is a :py:class:`LatexNode` describing the parsed content,
    `pos` is the position at which the LaTeX element of iterest was encountered,
    and `len` is the length of the string that is considered to be part of the
    `node`.  That is, the position in the string that is immediately after the
    node is `pos+len`.

    The following obsolete flag is accepted by the constructor for backwards
    compatibility with `pylatexenc 1.x`:

      - `macro_dict`: This argument is kept for compatibility with `pylatexenc
        1.x`.  This is a dictionary of known LaTeX macro specifications.  If
        specified, this should be a dictionary where the keys are macro names
        and values are :py:class:`pylatexenc.macrospec.MacroSpec` instances, as
        returned for instance by the `pylatexenc 1.x`-emulating function
        :py:func:`MacrosDef`.  If you specify this argument, you cannot provide
        a custom `latex_context`.  This argument is superseded by the
        `latex_context` argument.  Furthermore, if you specify this argument, no
        specials are parsed so that the behavior closer to `pylatexenc 1.x`.

        .. deprecated:: 2.0
    
           The `macro_dict` argument has been replaced by the much more powerful
           `latex_context` argument which allows you to further provide
           environment specifications, etc.
    
      - `keep_inline_math=True|False`: Obsolete option.  In `pylatexenc 1.x`,
        this option triggered a weird behavior especially since there is a
        similarly named option in
        :py:class:`pylatexenc.latex2text.LatexNodes2Text` with a different
        meaning.  [See `Issue #14
        <https://github.com/phfaist/pylatexenc/issues/14>`_.]  You should now
        only use the option `math_mode=` in
        :py:class:`pylatexenc.latex2text.LatexNodes2Text`.

        .. deprecated:: 2.0

           This option is ignored starting from `pylatexenc 2`.  Instead, you
           should set the option `math_mode=` accordingly in
           :py:class:`pylatexenc.latex2text.LatexNodes2Text`.


    .. py:attribute:: s
    
       The string that is being parsed.

       Do NOT modify this attribute.
    """

    def __init__(self, s, latex_context=None, **kwargs):

        self.s = s

        # will be determined lazily automatically by pos_to_lineno_colno(...)
        self._line_no_calc = None

        self.debug_nodes = False

        if latex_context is None:
            if 'macro_dict' in kwargs:
                # LEGACY -- build a latex context using the given macro_dict
                _util.pylatexenc_deprecated_2(
                    "The `macro_dict=...` option in LatexWalker() is obsolete since "
                    "pylatexenc 2.  It'll still work, but please consider using instead "
                    "the more versatile option `latex_context=...`."
                )

                macro_dict = kwargs.pop('macro_dict', None)

                default_latex_context = get_default_latex_context_db()

                latex_context = default_latex_context.filter_context(
                    keep_which=['environments'], # no specials
                )
                latex_context.add_context_category(
                    'custom',
                    macro_dict.values(),
                    default_latex_context.iter_environment_specs()
                )

            else:
                # default -- use default
                latex_context = get_default_latex_context_db()

        else:
            # make sure the user didn't also provide a macro_dict= argument
            if 'macro_dict' in kwargs:
                raise TypeError(
                    "Cannot specify both `latex_context=` and `macro_dict=` arguments"
                )


        # We don't store the latex_context in an attribute, because we always
        # access it via the current parsing_state

        latex_context.freeze() # prevent future changes to the latex context db

        self.default_parsing_state = ParsingState(
            s=self.s,
            latex_context=latex_context,
        )


        #
        # now parsing flags:
        #
        self.tolerant_parsing = kwargs.pop('tolerant_parsing', True)
        self.strict_braces = kwargs.pop('strict_braces', False)

        if 'keep_inline_math' in kwargs:
            _util.pylatexenc_deprecated_2(
                "The keep_inline_math=... option in LatexWalker() has no effect "
                "in pylatexenc 2.  Please consider using the more versatile option "
                "math_mode=... in LatexNodes2Text() instead."
            )
            del kwargs['keep_inline_math']

        if kwargs:
            # any flags left which we haven't recognized
            logger.warning("LatexWalker(): Unknown flag(s) encountered: %r", kwargs.keys())

        super(LatexWalker, self).__init__()


    def make_parsing_state(self, **kwargs):
        r"""
        Return a new parsing state object that corresponds to the current string
        that we are parsing (`s` provided to the constructor) and the current
        latex context (`latex_context` provided to the constructor).

        If no arguments are provided, this returns the default parsing state.

        If keyword arguments are provided, then they can override fields from
        the default parsing state.  For instance, if we enter math mode, you
        might use::
        
          parsing_state_mathmode = \
              my_latex_walker.make_parsing_state(in_math_mode=True)
        """
        return self.default_parsing_state.sub_context(**kwargs)

    def parse_flags(self):
        """
        The parse flags currently set on this object.  Returns a dictionary with
        keys 'keep_inline_math', 'tolerant_parsing' and 'strict_braces'.

        .. deprecated:: 2.0

           The 'keep_inline_math' key is always set to `None` starting in
           `pylatexenc 2` and might be removed entirely in future versions.
        """
        return {
            'tolerant_parsing': self.tolerant_parsing,
            'strict_braces': self.strict_braces,
            # compatibility with pylatexenc 1.x
            'keep_inline_math': None,
        }

    def _report_ignore_parse_error(self, exc):
        logger.info("Ignoring parse error (tolerant parsing mode): %s", exc)
        
    def get_token(self, pos, include_brace_chars=None, environments=True,
                  keep_inline_math=None, parsing_state=None, **kwargs):
        r"""
        Parses the latex content given to the constructor (and stored in `self.s`),
        starting at position `pos`, to parse a single "token", as defined by
        :py:class:`LatexToken`.

        Parse the token in the stream pointed to at position `pos`.

        Returns a :py:class:`LatexToken`. Raises
        :py:exc:`LatexWalkerEndOfStream` if end of stream reached.

        For tokens of type 'char', usually a single character is returned.  The
        only exception is at paragraph boundaries, where a single 'char'-type
        token has argument '\\n\\n'.

        Normally whitespace cannot be part of a latex-specials.  As an
        exception, you can declare a `SpecialsSpec` in your `latex_context` with
        the chars ``"\n\n"``, and it will be reported at paragraph breaks caused
        by a double newline.

        The argument `include_brace_chars=` allows to specify additional pairs
        of single characters which should be considered as braces (i.e., of
        'brace_open' and 'brace_close' token types).  It should be a list of
        2-item tuples, for instance ``[('[', ']'), ('<', '>')]``.  The pair
        `('{', '}')` is always considered as braces.  The delimiters may not
        have more than one character each.

        If `environments=False`, then ``\begin`` and ``\end`` tokens count as
        regular 'macro' tokens (see :py:class:`LatexToken`); otherwise (the
        default) they are considered as the token types 'begin_environment' and
        'end_environment'.

        The parsing of the tokens might be influcenced by the `parsing_state` (a
        :py:class:`ParsingState` instance).  Currently, the only influence this
        has is that some latex specials are parsed differently if in math mode.
        See doc for :py:class:`ParsingState`.  If `parsing_state` is `None`, the
        default parsing state returned by :py:meth:`make_parsing_state()` is
        used.

        .. deprecated:: 2.0

           The flag `keep_inline_math` is only accepted for compatibiltiy with
           earlier versions of `pylatexenc`, but it has no effect starting in
           `pylatexenc 2`.  See the :py:class:`LatexWalker` class doc.

        .. deprecated:: 2.0

           If `brackets_are_chars=False`, then square bracket characters count
           as 'brace_open' and 'brace_close' token types (see
           :py:class:`LatexToken`); otherwise (the default) they are considered
           just like other normal characters.

        .. versionadded:: 2.0

           The `parsing_state` argument was introduced in version 2.0.
        """

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


    def make_node(self, node_class, **kwargs):
        r"""
        Create and return a node of type `node_class` which holds a representation
        of the latex code at position `pos` and of length `len` in the parsed
        string.

        The node class should be a :py:class:`LatexNode` subclass.  Keyword
        arguments are supplied directly to the constructor of the node class.

        Mandatory keyword-only arguments are 'pos', 'len', and 'parsing_state'.

        All nodes produced by :py:meth:`get_latex_nodes()` and friends use this
        method to create node classes.

        .. versionadded:: 2.0
        
           This method was introduced in `pylatexenc 2.0`.
        """
        # mandatory keyword-only arguments:
        pos, len, parsing_state = \
            kwargs.pop('pos'), kwargs.pop('len'), kwargs.pop('parsing_state')

        node = node_class(pos=pos, len=len, parsing_state=parsing_state, **kwargs)
        if self.debug_nodes:
            logger.debug("New node: %r", node)
        return node

    def _mknodeposlen(self, nclass, parsing_state, pos, len, **kwargs):
        return (
            self.make_node(nclass, parsing_state=parsing_state, pos=pos, len=len, **kwargs),
            pos,
            len
        )

    
    def pos_to_lineno_colno(self, pos, as_dict=False):
        r"""
        Return the line and column number corresponding to the given `pos` in our
        string `self.s`.

        The first time this function is called, line numbers are calculated for
        the entire string.  These are cached for future calls which are then
        fast.

        Return a tuple `(lineno, colno)` giving line number and column number.
        Line numbers start at 1 and column numbers start at zero, i.e., the
        beginning of the document (`pos=0`) has line and column number `(1,0)`.
        If `as_dict=True`, then a dictionary with keys 'lineno', 'colno' is
        returned instead of a tuple.
        """

        if self._line_no_calc is None:
            self._line_no_calc = _util.LineNumbersCalculator(self.s)

        return self._line_no_calc.pos_to_lineno_colno(pos, as_dict=as_dict)


    def get_latex_expression(self, pos, strict_braces=None, parsing_state=None):
        r"""
        Parses the latex content given to the constructor (and stored in `self.s`),
        starting at position `pos`, to parse a single LaTeX expression.

        Reads a latex expression, e.g. macro argument. This may be a single char, an escape
        sequence, or a expression placed in braces.  This is what TeX calls a "token" (and
        not what we call a token... anyway).

        Parsing might be influenced by the `parsing_state`.  See doc for
        :py:class:`ParsingState`.  If `parsing_state` is `None`, then the
        default parsing state is used.

        Returns a tuple `(node, pos, len)`, where `pos` is the position of the
        first char of the expression and `len` the length of the expression.

        .. versionadded:: 2.0

           The `parsing_state` argument was introduced in version 2.0.
        """

        if parsing_state is None:
            parsing_state = self.make_parsing_state() # get default parsing state

        with _util.PushPropOverride(self, 'strict_braces', strict_braces):

            tok = self.get_token(pos, environments=False, parsing_state=parsing_state)

            if tok.tok == 'macro':
                if tok.arg == 'end':
                    if not self.tolerant_parsing:
                        # error, we were expecting a single token
                        raise LatexWalkerParseError(
                            r"Expected expression, got \end",
                            self.s, pos,
                            **self.pos_to_lineno_colno(pos, as_dict=True)
                        )
                    else:
                        return self._mknodeposlen(LatexCharsNode,
                                                  parsing_state=parsing_state,
                                                  chars='',
                                                  pos=tok.pos,
                                                  len=0)
                return self._mknodeposlen(LatexMacroNode,
                                          parsing_state=parsing_state,
                                          macroname=tok.arg,
                                          nodeargd=None,
                                          macro_post_space=tok.post_space,
                                          nodeoptarg=None, nodeargs=None,
                                          pos=tok.pos, len=tok.len)
            if tok.tok == 'specials':
                return self._mknodeposlen(LatexSpecialsNode,
                                          parsing_state=parsing_state,
                                          specials_chars=tok.arg.specials_chars,
                                          nodeargd=None,
                                          pos=tok.pos, len=tok.len)
            if tok.tok == 'comment':
                return self.get_latex_expression(tok.pos+tok.len, parsing_state=parsing_state)
            if tok.tok == 'brace_open':
                return self.get_latex_braced_group(tok.pos, parsing_state=parsing_state)
            if tok.tok == 'brace_close':
                # don't worry, stray closing braces are still reported (in
                # get_latex_nodes()) if tolerant_parsing=False even if
                # strict_braces=False.  That's because we leave the brace in the
                # input and it will be picked up when we read the next token.
                if self.strict_braces and not self.tolerant_parsing:
                    raise LatexWalkerParseError(
                        "Expected expression, got closing brace '{}'".format(tok.arg),
                        self.s, pos,
                        **self.pos_to_lineno_colno(pos, as_dict=True)
                    )
                return self._mknodeposlen(LatexCharsNode,
                                          parsing_state=parsing_state,
                                          chars='',
                                          pos=tok.pos, len=0)
            if tok.tok == 'char':
                return self._mknodeposlen(LatexCharsNode,
                                          parsing_state=parsing_state,
                                          chars=tok.arg,
                                          pos=tok.pos,
                                          len=tok.len)
            if tok.tok in ('mathmode_inline', 'mathmode_display'):
                # don't report a math mode token, treat as char or macro
                if tok.arg.startswith('\\'):
                    return self._mknodeposlen(LatexMacroNode,
                                              parsing_state=parsing_state,
                                              macroname=tok.arg,
                                              nodeoptarg=None,
                                              nodeargs=None,
                                              macro_post_space=tok.post_space,
                                              pos=tok.pos,
                                              len=tok.len)
                else:
                    return self._mknodeposlen(LatexCharsNode,
                                              parsing_state=parsing_state,
                                              chars=tok.arg,
                                              pos=tok.pos,
                                              len=tok.len)

            raise LatexWalkerParseError(
                "Unknown token type: {}".format(tok.tok), self.s, pos,
                **self.pos_to_lineno_colno(pos, as_dict=True))


    def get_latex_maybe_optional_arg(self, pos, parsing_state=None):
        r"""
        Parses the latex content given to the constructor (and stored in `self.s`),
        starting at position `pos`, to attempt to parse an optional argument.

        Parsing might be influenced by the `parsing_state`. See doc for
        :py:class:`ParsingState`.  If `parsing_state` is `None`, the default
        parsing state is used.

        Attempts to parse an optional argument. If this is successful, we return
        a tuple `(node, pos, len)` if success where `node` is a
        :py:class:`LatexGroupNode`.  Otherwise, this method returns None.

        .. versionadded:: 2.0

           The `parsing_state` argument was introduced in version 2.0.
        """

        if parsing_state is None:
            parsing_state = self.make_parsing_state() # get default parsing state

        try:
            tok = self.get_token(pos, include_brace_chars=[('[', ']')], environments=False,
                                 parsing_state=parsing_state)
        except LatexWalkerEndOfStream:
            # we're at end of stream, simply report no optional arg and let
            # parents re-detect end of stream when they call again get_token().
            # Added exception handler to fix issue #57
            return None

        if tok.tok == 'brace_open' and tok.arg == '[':
            return self.get_latex_braced_group(pos, brace_type='[',
                                               parsing_state=parsing_state)

        return None


    def get_latex_braced_group(self, pos, brace_type='{', parsing_state=None):
        r"""
        Parses the latex content given to the constructor (and stored in `self.s`),
        starting at position `pos`, to read a latex group delimited by braces.

        Reads a latex expression enclosed in braces ``{ ... }``. The first token of
        `s[pos:]` must be an opening brace.

        Parsing might be influenced by the `parsing_state`.  See doc for
        :py:class:`ParsingState`.  If `parsing_state` is `None`, the default
        parsing state is used.

        Returns a tuple `(node, pos, len)`, where `node` is a
        :py:class:`LatexGroupNode` instance, `pos` is the position of the first
        char of the expression (which has to be an opening brace), and `len` is
        the length of the group, including the closing brace (relative to the
        starting position).

        The group must be delimited by the given `brace_type`.  `brace_type` may
        be one of ``{``, ``[``, ``(`` or ``<``, or a 2-item tuple of two
        distinct single characters providing the opening and closing brace
        chars (e.g., ``("<", ">")``).

        .. versionadded:: 2.0

           The `parsing_state` argument was introduced in version 2.0.
        """

        if parsing_state is None:
            parsing_state = self.make_parsing_state() # get default parsing state

        closing_brace = None
        if brace_type == '{':
            closing_brace = '}'
        elif brace_type == '[':
            closing_brace = ']'
        elif brace_type == '(':
            closing_brace = ')'
        elif brace_type == '<':
            closing_brace = '>'
        elif len(brace_type) == 2:
            brace_type, closing_brace = brace_type
        else:
            raise ValueError("Invalid brace type for get_latex_braced_group(): %s" %(brace_type))

        include_brace_chars = None
        if brace_type and brace_type != '{':
            include_brace_chars = [(brace_type, closing_brace)]

        firsttok = self.get_token(pos, include_brace_chars=include_brace_chars,
                                  parsing_state=parsing_state)
        if firsttok.tok != 'brace_open'  or  firsttok.arg != brace_type:
            raise LatexWalkerParseError(
                s=self.s,
                pos=pos,
                msg='get_latex_braced_group: not an opening brace/bracket: %s' %(
                    self.s[firsttok.pos:firsttok.pos+firsttok.len]
                ),
                **self.pos_to_lineno_colno(pos, as_dict=True)
            )

        (nodelist, npos, nlen) = self.get_latex_nodes(
            firsttok.pos + firsttok.len,
            stop_upon_closing_brace=(brace_type, closing_brace),
            parsing_state=parsing_state
        )

        return self._mknodeposlen(LatexGroupNode, nodelist=nodelist,
                                  parsing_state=parsing_state,
                                  delimiters=(brace_type, closing_brace),
                                  pos = firsttok.pos,
                                  len = npos + nlen - firsttok.pos)


    def get_latex_environment(self, pos, environmentname=None, parsing_state=None):
        r"""
        Parses the latex content given to the constructor (and stored in `self.s`),
        starting at position `pos`, to read a latex environment.

        Reads a latex expression enclosed in a
        ``\begin{environment}...\end{environment}``.  The first token in the
        stream must be the ``\begin{environment}``.

        If `environmentname` is given and nonempty, then additionally a
        :py:exc:`LatexWalkerParseError` is raised if the environment in the
        input stream does not match the provided environment name.

        Arguments to the begin environment command are parsed according to the
        corresponding specification in the given latex context `latex_context`
        provided to the constructor.  The environment name is looked up as a
        "macro name" in the macro spec.

        Parsing might be influenced by the `parsing_state`.  See doc for
        :py:class:`ParsingState`.  If `parsing_state` is `None`, the default
        parsing state is used.

        Returns a tuple (node, pos, len) where node is a
        :py:class:`LatexEnvironmentNode`.

        .. versionadded:: 2.0

           The `parsing_state` argument was introduced in version 2.0.
        """

        if parsing_state is None:
            parsing_state = self.make_parsing_state() # get default parsing state

        startpos = pos

        firsttok = self.get_token(pos, parsing_state=parsing_state)
        if firsttok.tok != 'begin_environment'  or  \
           (environmentname is not None and firsttok.arg != environmentname):
            raise LatexWalkerParseError(
                s=self.s,
                pos=pos,
                msg=r'get_latex_environment: expected \begin{%s}: %s' %(
                    environmentname if environmentname is not None else '<environment name>',
                    firsttok.arg
                ),
                **self.pos_to_lineno_colno(pos, as_dict=True)
            )
        if (environmentname is None):
            environmentname = firsttok.arg

        pos = firsttok.pos + firsttok.len

        env_spec = parsing_state.latex_context.get_environment_spec(environmentname)
        if env_spec is None:
            env_spec = macrospec.EnvironmentSpec('')

        # self = latex walker instance
        try:
            argsresult = env_spec.parse_args(w=self, pos=pos, parsing_state=parsing_state)
        except (LatexWalkerEndOfStream, LatexWalkerParseError) as e:
            e = self._exchandle_parse_subexpression(
                e,
                firsttok,
                "arguments of environment \"\\begin{{{}}}\"".format(environmentname),
            )
            if e is not None: raise e
            argsresult = (None, pos, 0, {})

        if len(argsresult) == 4:
            (argd, apos, alen, adic) = argsresult
        else:
            (argd, apos, alen) = argsresult
            adic = {}

        pos = apos + alen

        parsing_state_inner = adic.get('inner_parsing_state', parsing_state)
        #parsing_state_inner = parsing_state
        if env_spec.is_math_mode:
            parsing_state_inner = parsing_state.sub_context(
                in_math_mode=True,
                math_mode_delimiter='{'+environmentname+'}',
            )

        (nodelist, npos, nlen) = self.get_latex_nodes(pos,
                                                      stop_upon_end_environment=environmentname,
                                                      parsing_state=parsing_state_inner)

        if argd is not None and argd.legacy_nodeoptarg_nodeargs:
            legnodeoptarg = argd.legacy_nodeoptarg_nodeargs[0]
            legnodeargs = argd.legacy_nodeoptarg_nodeargs[1]
        else:
            legnodeoptarg, legnodeargs = None, []

        return self._mknodeposlen(LatexEnvironmentNode,
                                  parsing_state=parsing_state,
                                  environmentname=environmentname,
                                  nodelist=nodelist,
                                  nodeargd=argd,
                                  # legacy:
                                  optargs=[legnodeoptarg],
                                  args=legnodeargs,
                                  pos=startpos,
                                  len=npos+nlen-startpos)


    def _exchandle_parse_subexpression(self, e, tok, what):
        """
        (INTERNAL.) Handle an exception raised by a method that you called to parse
        a macro arguments or another "sub-expression".  Use as::

            except (LatexWalkerEndOfStream, LatexWalkerParseError) as e:
                e = self._exchandle_parse_subexpression(e, <tok>, "what this is about")
                if e is not None: raise e
                ... # do sth to recover from parse error in tolerant mode

        Use in an exception handler that captures both `LatexWalkerEndOfStream`
        and `LatexWalkerParseError`.  Returns what exception you should raise if
        you got one of these while parsing, e.g., macro arguments.
        """

        if isinstance(e, LatexWalkerEndOfStream):
            e = LatexWalkerParseError(
                s=self.s,
                pos=tok.pos,
                msg="End of input while parsing {}".format(what),
                **self.pos_to_lineno_colno(tok.pos, as_dict=True)
            )

        if getattr(e, 'pos', None) is not None and e.lineno is None and e.colno is None:
            e.lineno, e.colno = self.pos_to_lineno_colno(e.pos)

        e.open_contexts.append(
            _maketuple('{}'.format(what), tok.pos,
                       *self.pos_to_lineno_colno(tok.pos))
        )

        if self.tolerant_parsing:
            self._report_ignore_parse_error(e)
            return None
        return e
   

    def get_latex_nodes(self, pos=0, stop_upon_closing_brace=None,
                        stop_upon_end_environment=None,
                        stop_upon_closing_mathmode=None, read_max_nodes=None,
                        parsing_state=None):
        r"""
        Parses the latex content given to the constructor (and stored in `self.s`)
        into a list of nodes.

        Returns a tuple `(nodelist, pos, len)` where:

          - `nodelist` is a list of :py:class:`LatexNode`\ 's representing the
            parsed LaTeX code.

          - `pos` is the same as the `pos` given as argument; if there is
            leading whitespace it is reported in `nodelist` using a
            :py:class:`LatexCharsNode`.

          - `len` is the length of the parsed expression.  If one of the
            `stop_upon_...=` arguments are provided (cf below), then the `len`
            includes the length of the token/expression that stopped the
            parsing.
        
        If `stop_upon_closing_brace` is given and set to a character, then
        parsing stops once the given closing brace is encountered (but not
        inside a subgroup).  The brace is given as a character, ']', '}', ')',
        or '>'.  Alternatively you may specify a 2-item tuple of two single
        distinct characters representing the opening and closing brace chars.
        The returned `len` includes the closing brace, but the closing brace is
        not included in any of the nodes in the `nodelist`.

        If `stop_upon_end_environment` is provided, then parsing stops once the
        given environment was closed.  If there is an environment mismatch, then
        a `LatexWalkerParseError` is raised except in tolerant parsing mode (see
        :py:meth:`parse_flags()`).  Again, the closing environment is included
        in the length count but not the nodes.

        If `stop_upon_closing_mathmode` is specified, then the parsing stops
        once the corresponding math mode (assumed already open) is closed.  This
        argument may take the values `None` (no particular request to stop at
        any math mode token), or one of ``$``, ``$$``, ``\)`` or ``\]``
        indicating a closing math mode delimiter that we are expecting and at
        which point parsing should stop.

        If the token '$' (respectively '$$') is encountered, it is interpreted
        as the *beginning* of a new math mode chunk *unless* the argument
        `stop_upon_closing_mathmode=...` has been set to '$' (respectively
        '$$').

        If `read_max_nodes` is non-`None`, then it should be set to an integer
        specifying the maximum number of top-level nodes to read before
        returning.  (Top-level nodes means that macro arguments, environment or
        group contents, etc., do not count towards `read_max_nodes`.)  If
        `None`, the entire input string will be parsed.

        .. note::

           There are a few important differences between
           ``get_latex_nodes(read_max_nodes=1)`` and ``get_latex_expression()``:
           The former reads a logical node of the LaTeX document, which can be a
           sequence of characters, a macro invocation with arguments, or an
           entire environment, but the latter reads a single LaTeX "token" in
           a similar way to how LaTeX parses macro arguments.

           For instance, if a macro is encountered, then
           ``get_latex_nodes(read_max_nodes=1)`` will read and parse its
           arguments, and include it in the corresponding
           :py:class:`LatexMacroNode`, whereas ``get_latex_expression()`` will
           return a minimal :py:class:`LatexMacroNode` with no arguments
           regardless of the macro's argument specification.  The same holds for
           latex specials.  For environments,
           ``get_latex_nodes(read_max_nodes=1)`` will return the entire parsed
           environment into a :py:class:`LatexEnvironmentNode`, whereas
           ``get_latex_expression()`` will return a :py:class:`LatexMacroNode`
           named 'begin' with no arguments.

        Parsing might be influenced by the `parsing_state`.  See doc for
        :py:class:`ParsingState`.  If `parsing_state` is `None`, the default
        parsing state is used.

        .. versionadded:: 2.0

           The `parsing_state` argument was introduced in version 2.0.
        """

        if parsing_state is None:
            parsing_state = self.make_parsing_state() # get default parsing state

        nodelist = []
    
        include_brace_chars = None
        opening_brace_for_stop_upon_closing_brace = None
        if stop_upon_closing_brace:
            if stop_upon_closing_brace == '}':
                opening_brace_for_stop_upon_closing_brace = '{'
            elif stop_upon_closing_brace == ']':
                opening_brace_for_stop_upon_closing_brace = '['
            elif stop_upon_closing_brace == ')':
                opening_brace_for_stop_upon_closing_brace = '('
            elif stop_upon_closing_brace == '>':
                opening_brace_for_stop_upon_closing_brace = '<'
            elif len(stop_upon_closing_brace) == 2:
                opening_brace_for_stop_upon_closing_brace, stop_upon_closing_brace = \
                    stop_upon_closing_brace

            if stop_upon_closing_brace != '}':
                include_brace_chars = [
                    (opening_brace_for_stop_upon_closing_brace, stop_upon_closing_brace)
                ]

        # consistency check
        if stop_upon_closing_mathmode is not None and not parsing_state.in_math_mode:
            logger.warning(
                ("Call to LatexWalker.get_latex_nodes(stop_upon_closing_mathmode={!r}) "
                 "but parsing state has in_math_mode={!r}").format(
                     stop_upon_closing_mathmode,
                     parsing_state.in_math_mode,
                 )
            )

        #
        # Man, I really need to rewrite this function properly. This is some
        # pretty ugly sh*t.
        #

        origpos = pos

        class PosPointer:
            def __init__(self, pos, parsing_state, lastchars='', lastchars_pos=None):
                self.pos = pos
                self.parsing_state = parsing_state
                self.lastchars = lastchars
                self.lastchars_pos = lastchars_pos

            def push_lastchars(self, pos, chars):
                self.lastchars += chars
                if self.lastchars_pos is None:
                    self.lastchars_pos = pos
            
            def flush_lastchars(self):
                res = self.lastchars_pos, self.lastchars
                self.lastchars = ''
                self.lastchars_pos = None
                return res

        p = PosPointer(pos=pos, parsing_state=parsing_state)

        def do_read(nodelist, p):
            r"""
            Read a single token and process it, recursing into brace blocks and
            environments etc if needed, and appending stuff to nodelist.

            Return True whenever we should stop trying to read more. (e.g. upon
            reaching the a matched stop_upon_end_environment etc.)  Can return
            an exception instance to give more information than simply `True`.
            """

            try:
                tok = self.get_token(p.pos, include_brace_chars=include_brace_chars,
                                     parsing_state=p.parsing_state)
            except LatexWalkerEndOfStream as e:
                if self.tolerant_parsing:
                    return e
                raise # re-raise
            except LatexWalkerParseError as e:
                # get_token() should not raise parse errors in tolerant_parsing
                # mode, because this can lead to infinite loops (#37)
                assert(not self.tolerant_parsing)
                raise # exception will be handled in outer loop

            p.pos = tok.pos + tok.len

            #def tok_to_pos_and_chars_from_ppos(tok):
            #    return tok.pos, self.s[p.pos, tok.pos+tok.len]

            # if it's a char, just append it to the stream of last characters.
            if tok.tok == 'char':
                p.push_lastchars(pos=(tok.pos - len(tok.pre_space)),
                                 chars=(tok.pre_space + tok.arg))
                return False

            # if it's not a char, push the last `p.lastchars` into the node list
            # before we do anything else
            if len(p.lastchars):
                charspos, chars = p.flush_lastchars()
                strnode = self.make_node(LatexCharsNode,
                                         parsing_state=p.parsing_state,
                                         chars=chars+tok.pre_space,
                                         pos=charspos, len=tok.pos - charspos)
                nodelist.append(strnode)
                if read_max_nodes and len(nodelist) >= read_max_nodes:
                    # adjust p.pos for return value of get_latex_nodes()
                    p.pos = tok.pos
                    return True
            elif len(tok.pre_space):
                # If we have pre_space, add a separate chars node that contains
                # the spaces.  We do this seperately, so that latex2text can
                # ignore these groups by default to avoid too much space on the
                # output.  This allows latex2text to implement the
                # `strict_latex_spaces=True` flag correctly.
                spacestrnode = self.make_node(LatexCharsNode,
                                              parsing_state=p.parsing_state,
                                              chars=tok.pre_space,
                                              pos=tok.pos-len(tok.pre_space),
                                              len=len(tok.pre_space))
                nodelist.append(spacestrnode)
                if read_max_nodes and len(nodelist) >= read_max_nodes:
                    # adjust p.pos for return value of get_latex_nodes()
                    p.pos = tok.pos
                    return True

            # and see what the token is.

            if tok.tok == 'brace_close':
                # we've reached the end of the group. stop the parsing.
                if tok.arg != stop_upon_closing_brace:
                    #p.push_lastchars(tok_to_pos_and_chars_from_ppos(tok))
                    raise LatexWalkerParseError(
                        s=self.s,
                        pos=tok.pos,
                        msg="Unexpected mismatching closing brace: '%s'"%(tok.arg),
                        **self.pos_to_lineno_colno(tok.pos, as_dict=True)
                    )
                return True

            if tok.tok == 'end_environment':
                # we've reached the end of an environment.
                if not stop_upon_end_environment:
                    #p.push_lastchars(tok_to_pos_and_chars_from_ppos(tok))
                    raise LatexWalkerParseError(
                        s=self.s,
                        pos=tok.pos,
                        msg=("Unexpected closing environment: '{}'".format(tok.arg)),
                        **self.pos_to_lineno_colno(tok.pos, as_dict=True)
                    )
                elif tok.arg != stop_upon_end_environment:
                    #p.push_lastchars(tok_to_pos_and_chars_from_ppos(tok))
                    raise LatexWalkerParseError(
                        s=self.s,
                        pos=tok.pos,
                        msg=("Unexpected mismatching closing environment: '{}', "
                             "was expecting '{}'".format(tok.arg, stop_upon_end_environment)),
                        **self.pos_to_lineno_colno(tok.pos, as_dict=True)
                    )
                return True

            if tok.tok in ('mathmode_inline', 'mathmode_display'):
                # see if we need to stop at a math mode 
                if stop_upon_closing_mathmode is not None:
                    if tok.arg == stop_upon_closing_mathmode:
                        # all OK, found the closing mathmode.
                        return True
                    if tok.arg in [r'\)', r'\]']:
                        # this is definitely a closing math-mode delimiter, so
                        # not a new math mode block.  This is a parse error,
                        # because we need to match the given
                        # stop_upon_closing_mathmode mode.

                        #p.push_lastchars(tok_to_pos_and_chars_from_ppos(tok))
                        raise LatexWalkerParseError(
                            s=self.s,
                            pos=tok.pos,
                            msg="Mismatching closing math mode: '{}', expected '{}'".format(
                                tok.arg, stop_upon_closing_mathmode,
                            ),
                            **self.pos_to_lineno_colno(tok.pos, as_dict=True)
                        )
                    # all ok, this is a new math mode opening.  Keep an assert
                    # in case we forget to include some math-mode delimiters in
                    # the future.
                    assert tok.arg in ['$', '$$', r'\(', r'\[']
                elif tok.arg in [r'\)', r'\]']:
                    # unexpected close-math-mode delimiter, but no
                    # stop_upon_closing_mathmode was specified. Parse error.

                    #p.push_lastchars(tok_to_pos_and_chars_from_ppos(tok))
                    raise LatexWalkerParseError(
                        s=self.s,
                        pos=tok.pos,
                        msg="Unexpected closing math mode: '{}'".format(tok.arg),
                        **self.pos_to_lineno_colno(tok.pos, as_dict=True)
                    )

                # we have encountered a new math inline, parse the math expression

                corresponding_closing_mathmode = \
                    {r'\(': r'\)', r'\[': r'\]'}.get(tok.arg, tok.arg)
                displaytype = 'inline' if tok.arg in [r'\(', '$'] else 'display'

                parsing_state_inner = p.parsing_state.sub_context(
                    in_math_mode=True,
                    math_mode_delimiter=tok.arg
                )

                try:
                    (mathinline_nodelist, mpos, mlen) = self.get_latex_nodes(
                        p.pos,
                        stop_upon_closing_mathmode=corresponding_closing_mathmode,
                        parsing_state=parsing_state_inner
                    )
                except LatexWalkerParseError as e:
                    e.open_contexts.append( _maketuple('math mode "{}"'.format(tok.arg), tok.pos,
                                                       *self.pos_to_lineno_colno(tok.pos)) )
                    raise
                p.pos = mpos + mlen

                nodelist.append(self.make_node(
                    LatexMathNode,
                    parsing_state=p.parsing_state,
                    displaytype=displaytype,
                    nodelist=mathinline_nodelist,
                    delimiters=(tok.arg, corresponding_closing_mathmode),
                    pos=tok.pos, len=mpos+mlen-tok.pos
                ))
                if read_max_nodes and len(nodelist) >= read_max_nodes:
                    return True
                return

            if tok.tok == 'comment':
                commentnode = self.make_node(LatexCommentNode,
                                             parsing_state=p.parsing_state,
                                             comment=tok.arg,
                                             comment_post_space=tok.post_space,
                                             pos=tok.pos, len=tok.len)
                nodelist.append(commentnode)
                if read_max_nodes and len(nodelist) >= read_max_nodes:
                    return True
                return

            if tok.tok == 'brace_open':
                # another braced group to read.
                try:
                    (groupnode, bpos, blen) = self.get_latex_braced_group(
                        tok.pos,
                        brace_type=tok.arg,
                        parsing_state=p.parsing_state
                    )
                # except LatexWalkerEndOfStream as e:
                #     # shouldn't happen.
                except LatexWalkerParseError as e:
                    e.open_contexts.append( _maketuple('open brace', tok.pos,
                                                       *self.pos_to_lineno_colno(tok.pos)) )
                    raise

                p.pos = bpos + blen
                nodelist.append(groupnode)
                if read_max_nodes and len(nodelist) >= read_max_nodes:
                    return True
                return

            if tok.tok == 'begin_environment':
                # an environment to read.
                try:
                    (envnode, epos, elen) = self.get_latex_environment(
                        tok.pos,
                        environmentname=tok.arg,
                        parsing_state=p.parsing_state
                    )
                except LatexWalkerParseError as e:
                    e.open_contexts.append(
                        _maketuple('begin environment "{}"'.format(tok.arg), tok.pos,
                                   *self.pos_to_lineno_colno(tok.pos))
                    )
                    raise
                p.pos = epos + elen
                # add node and continue.
                nodelist.append(envnode)
                if read_max_nodes and len(nodelist) >= read_max_nodes:
                    return True
                return

            if tok.tok == 'macro':
                # read a macro. see if it has arguments.
                macroname = tok.arg
                mspec = p.parsing_state.latex_context.get_macro_spec(macroname)
                if mspec is None:
                    mspec = macrospec.MacroSpec('')

                try:
                    margsresult = \
                        mspec.parse_args(w=self, pos=tok.pos + tok.len,
                                         parsing_state=p.parsing_state)
                except (LatexWalkerEndOfStream, LatexWalkerParseError) as e:
                    e = self._exchandle_parse_subexpression(
                        e,
                        tok,
                        "arguments of macro \"{}\"".format(macroname)
                    )
                    if e is not None: raise e
                    margsresult = (None, tok.pos + tok.len, 0, {})

                if len(margsresult) == 4:
                    (nodeargd, mapos, malen, mdic) = margsresult
                else:
                    (nodeargd, mapos, malen) = margsresult
                    mdic = {}

                p.pos = mapos + malen

                if nodeargd is not None and nodeargd.legacy_nodeoptarg_nodeargs:
                    nodeoptarg = nodeargd.legacy_nodeoptarg_nodeargs[0]
                    nodeargs = nodeargd.legacy_nodeoptarg_nodeargs[1]
                else:
                    nodeoptarg, nodeargs = None, []
                node = self.make_node(LatexMacroNode,
                                      parsing_state=p.parsing_state,
                                      macroname=tok.arg,
                                      nodeargd=nodeargd,
                                      macro_post_space=tok.post_space,
                                      # legacy data:
                                      nodeoptarg=nodeoptarg,
                                      nodeargs=nodeargs,
                                      pos=tok.pos,
                                      len=p.pos-tok.pos)
                nodelist.append(node)

                if 'new_parsing_state' in mdic:
                    # modify current parsing state---
                    p.parsing_state = mdic['new_parsing_state']

                if read_max_nodes and len(nodelist) >= read_max_nodes:
                    return True
                return None

            if tok.tok == 'specials':
                # read the specials. see if it expects/has arguments.
                sspec = tok.arg

                p.pos = tok.pos + tok.len
                nodeargd = None

                try:
                    res = sspec.parse_args(w=self, pos=p.pos, parsing_state=p.parsing_state)
                except (LatexWalkerEndOfStream, LatexWalkerParseError) as e:
                    e = self._exchandle_parse_subexpression(
                        e,
                        tok,
                        "arguments of specials \"{}\"".format(sspec.specials_chars)
                    )
                    if e is not None: raise e
                    res = (None, p.pos, 0, {})

                if res is not None:
                    # specials expects arguments, read them
                    if len(res) == 4:
                        (nodeargd, mapos, malen, spdic) = res
                    else:
                        (nodeargd, mapos, malen) = res
                        spdic = {}

                    p.pos = mapos + malen

                else:
                    spdic = {}

                node = self.make_node(LatexSpecialsNode,
                                      parsing_state=p.parsing_state,
                                      specials_chars=sspec.specials_chars,
                                      nodeargd=nodeargd,
                                      pos=tok.pos,
                                      len=p.pos-tok.pos)
                nodelist.append(node)

                if 'new_parsing_state' in spdic:
                    # modify current parsing state---
                    p.parsing_state = spdic['new_parsing_state']

                if read_max_nodes and len(nodelist) >= read_max_nodes:
                    return True
                return None


            raise LatexWalkerParseError(
                s=self.s,
                pos=p.pos,
                msg="Unknown token: {!r}".format(tok),
                **self.pos_to_lineno_colno(p.pos, as_dict=True)
            )



        while True:
            try:
                # might return boolean or Exception object
                r_endnow = do_read(nodelist, p)
            except LatexWalkerEndOfStream as e:
                if stop_upon_closing_brace or stop_upon_end_environment \
                   or stop_upon_closing_mathmode:
                    # unexpected eof
                    if stop_upon_closing_brace:
                        expecting = "'"+stop_upon_closing_brace+"'"
                    elif stop_upon_end_environment:
                        expecting = r"\end{"+stop_upon_end_environment+"}"
                    elif stop_upon_closing_mathmode:
                        expecting = "'"+stop_upon_closing_mathmode+"'"
                    e = LatexWalkerParseError(
                        s=self.s,
                        pos=p.pos,
                        msg="Unexpected end of stream, was expecting {}"
                            .format(expecting),
                        **self.pos_to_lineno_colno(len(self.s), as_dict=True)
                    )
                    if self.tolerant_parsing:
                        self._report_ignore_parse_error(e)
                        r_endnow = True
                    else:
                        raise e
                else:
                    r_endnow = e
            except LatexWalkerParseError as e:
                if self.tolerant_parsing:
                    self._report_ignore_parse_error(e)
                    r_endnow = False
                else:
                    raise

            if r_endnow:

                # add last chars and last space
                if isinstance(r_endnow, LatexWalkerEndOfStream):
                    p.push_lastchars(pos=p.pos,
                                     chars=r_endnow.final_space)
                    p.pos += len(r_endnow.final_space)

                if p.lastchars:
                    charspos, chars = p.flush_lastchars()
                    strnode = self.make_node(LatexCharsNode,
                                             parsing_state=p.parsing_state,
                                             chars=chars,
                                             pos=charspos, len=len(chars))
                    nodelist.append(strnode)
                return (nodelist, origpos, p.pos - origpos)

        # code never reaches here

