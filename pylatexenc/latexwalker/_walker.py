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
from .. import latexnodes
from .. import macrospec

from ..latexnodes._exctypes import *
from ..latexnodes._exctypes import format_pos
from ..latexnodes.nodes import *
from ..latexnodes import parsers


# fallback to empty context if PYLATEXENC_GET_DEFAULT_SPECS_FN block removed
get_default_latex_context_db = macrospec.LatexContextDb

### BEGIN_PYLATEXENC_GET_DEFAULT_SPECS_FN
from ._get_defaultspecs import get_default_latex_context_db
### END_PYLATEXENC_GET_DEFAULT_SPECS_FN

from ..latexnodes import ParsingState


import logging
logger = logging.getLogger(__name__)


_maketuple = lambda *args: tuple(args)



### BEGINPATCH_UNIQUE_OBJECT_ID
fn_unique_object_id = id
### ENDPATCH_UNIQUE_OBJECT_ID



_legacy_pyltxenc1_do = lambda *args: None



# ------------------------------------------------------------------------------



class LatexWalker(latexnodes.LatexWalkerBase):
    r"""
    A parser which walks through an input stream, parsing it as LaTeX markup.

    Arguments:

      - `s`: the string to parse as LaTeX code

      - `default_parsing_state`: The default parsing state to use to parse the
        content.  This should be a :py:class`pylatexenc.latexnodes.ParsingState`
        instance (or a subclass instance).  The parsing state also specifies the
        latex context, so if you specify `default_parsing_state=` you cannot
        also specify `latex_context=`.  If set to `None`, we'll pick a default
        parsing state.

        When parsing parts of the string you will still be able to provide
        custom parsing states; the parsing state specified here serves as the
        default for when you don't manually specify a parsing state to, e.g.,
        :py:meth:`parse_content()`.

        This object sets the default parsing state for the
        :py:meth:`make_parsing_state()` method.  That method returns a
        sub-context of the default parsing state with the specified attributes
        set.
    
        This argument is keyword-only.

        .. versionadded: 3.0

           The `default_parsing_state` argument was added in pylatexenc 3.

      - `latex_context`: Instead of providing a parsing state, you can provide
        the latex context only.  This should be a
        :py:class:`pylatexenc.macrospec.LatexContextDb` object that provides
        macro and environment specifications with instructions on how to parse
        arguments, etc.  If you don't specify this argument, or if you specify
        `None`, then the default database is used.  The default database is
        obtained with :py:func:`get_default_latex_context_db()`.

        It is strongly recommended to specify this argument as a keyword
        argument; we still accept a positional arg for backwards compatibility.

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

    .......... These methods, unless otherwise documented, return a tuple `(node, pos,
    len)`, where node is a :py:class:`LatexNode` describing the parsed content,
    `pos` is the position at which the LaTeX element of iterest was encountered,
    and `len` is the length of the string that is considered to be part of the
    `node`.  That is, the position in the string that is immediately after the
    node is `pos+len`. .......... changed in pylatexenc 3.......

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

        default_parsing_state = kwargs.pop('default_parsing_state', None)

        self.s = s

        # Shift reported line numbers by this amount.  Useful if you're parsing
        # a part of a file, so that line numbers are reported correctly.
        self.line_number_offset = kwargs.pop('line_number_offset', None) # first line = line # 1
        self.first_line_column_offset = kwargs.pop('first_line_column_offset', None)
        self.column_offset = kwargs.pop('column_offset', None)

        if self.line_number_offset is None:
            self.line_number_offset = 1
        if self.first_line_column_offset is None:
            self.first_line_column_offset = 0
        if self.column_offset is None:
            self.column_offset = 0

        # will be determined lazily automatically by pos_to_lineno_colno(...)
        self._line_no_calc = None

        self.debug_nodes = False

        if default_parsing_state is not None:
            self.default_parsing_state = default_parsing_state

            if latex_context is not None:
                raise ValueError("You cannot specify both the default_parsing_state= and "
                                 "the latex_context= arguments")
        else:
            if latex_context is None:

                latex_context = _legacy_pyltxenc1_do(
                    'LatexWalker_init_from_macro_dict', self, kwargs
                )

                if latex_context is None:
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

            if latex_context is not None:
                latex_context.freeze() # prevent future changes to the latex context db
                self.default_parsing_state = ParsingState(
                    s=self.s,
                    latex_context=latex_context,
                )

            else:
                # the user must promise to set a meaningful default_parsing_state !
                self.default_parsing_state = None


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


    make_latex_group_parser = parsers.LatexDelimitedGroupParser

    make_latex_math_parser = parsers.LatexMathParser


    def make_parsing_state(self, **kwargs):
        r"""
        Return a new parsing state object that corresponds to the current string
        that we are parsing (`s` provided to the constructor) and the current
        latex context (`latex_context` provided to the constructor).

        If no arguments are provided, this returns (a copy of) the default
        parsing state.

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
        
    
    def check_tolerant_parsing_ignore_error(self, exc):
        r"""
        Check if we should attempt to recover from the given error in tolerant
        parsing mode.

        If tolerant parsing mode is not enabled, or if `exc` is not an instance
        of :py:exc:`LatexWalkerError` (e.g., :py:exc:`LatexWalkerParseError` or
        :py:exc:`LatexWalkerEndOfStream`), then `exc` is returned unchanged.
        Otherwise, `None` is returned.

        Calling code should check the return value; if None was returned, then
        recovery from that error should be attempted, otherwise, the returned
        exception object should be raised.
        """

        if not self.tolerant_parsing or not isinstance(exc, LatexWalkerError):
            return exc

        # will recover from error ->
        self._report_ignore_parse_error(exc)

        return None


    class _ParsingContext(object):
        r"""
        Helper, use as context manager to capture parse errors and attempt recovery
        from parse errors in tolerant parsing mode.
        """
        def __init__(self, latex_walker, open_context):
            super(LatexWalker._ParsingContext, self).__init__()

            self.latex_walker = latex_walker
            self.open_context = open_context

            self.recovery_from_exception = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_traceback):
            if exc_value is not None and isinstance(exc_value, LatexWalkerParseError):
                e = exc_value
                if self.open_context:
                    what, tok = self.open_context
                    if what is not None:
                        if tok is not None:
                            e.open_contexts.append(
                                _maketuple(what, tok.pos,
                                           * self.latex_walker.pos_to_lineno_colno(tok.pos))
                            )
                        else:
                            e.open_contexts.append(
                                _maketuple(what, None, -1, -1)
                            )

                if hasattr(e, 'pos') and e.lineno is None and e.colno is None:
                    epos = getattr(e, 'pos', None)
                    e.lineno, e.colno = self.latex_walker.pos_to_lineno_colno(epos)
                e = self.latex_walker.check_tolerant_parsing_ignore_error(e)
                if e is None:
                    # we're trying to recover from this error (tolerant parsing mode)
                    self.recovery_from_exception = e
                    return True # error was handled

                return None # raise the same error further

        def perform_recovery_nodes_and_parsing_state_delta(self, token_reader):
            if self.recovery_from_exception is None:
                raise RuntimeError("No exception had happened to try to recover nodes from")

            nodes = None
            parsing_state_delta = None
            reset_at_tok = None

            # set nodes
            if hasattr(self.recovery_from_exception, 'recovery_nodes'):
                # remember, transcrypt doesn't like getattr(a, b, default) with default arg
                nodes = self.recovery_from_exception.recovery_nodes
            # parser state delta information?
            if hasattr(self.recovery_from_exception, 'recovery_parsing_state_delta'):
                parsing_state_delta = \
                    self.recovery_from_exception.recovery_parsing_state_delta

            # attempt to reset token_reader's position
            if hasattr(self.recovery_from_exception, 'recovery_at_token'):
                reset_at_tok = self.recovery_from_exception.recovery_at_token

            if reset_at_tok is not None:
                token_reader.move_to_token(reset_at_tok)
            else:
                reset_past_tok = None
                if hasattr(self.recovery_from_exception, 'recovery_past_token'):
                    reset_past_tok = self.recovery_from_exception.recovery_past_token
                if reset_past_tok is not None:
                    token_reader.move_past_token(reset_past_tok)

            return nodes, parsing_state_delta

    def new_parsing_open_context(self, open_context_name=None, open_context_token=None):
        r"""
        Create a context manager to capture parse errors and attempt recovery from
        them in tolerant parsing mode.

        Use as follows::

            tok = ... # token representing \mymacro
            with latex_walker.new_parsing_open_context(r"\mymacro invocation", tok) as pc:

                # parse stuff associated with \mymacro, perhaps custom
                # arguments
                ...

            if pc.recovery_from_exception is not None:
                # attempt recovery from the exception object stored in
                # the attribute `pc.recovery_from_exception`.  The method
                # `pc.perform_recovery_nodes_and_parsing_state_delta()` can be
                # useful.
                ...

        The context manager has a method
        `perform_recovery_nodes_and_parsing_state_delta(token_reader)` that will
        attempt to recover a nodes object from the parse error exception object
        and any parsing state changes information, which might have resulted
        from the parsing of a latex construct, and will attempt to reset the
        token reader's position in order to continue parsing.  The method
        returns a tuple `(nodes, parsing_state_delta)` with the hopefully
        recovered node list and parsing state changes information dictionary.

        The `open_context_name` is a textual description of the context to open,
        and the `open_context_token` is the token instance that is associated
        with the opening of this context.
        """
        return LatexWalker._ParsingContext(self, (open_context_name, open_context_token))

    def make_token_reader(self, pos=None):
        r"""
        Create an instance of :py:class:`LatexTokenReader` initialized to parse the
        string (`self.s`) of this LatexWalker object.  If `pos` is provided,
        then the token reader is initialized to start parsing at the position
        index `pos` in the string.
        """
        token_reader = latexnodes.LatexTokenReader(self.s,
                                                   tolerant_parsing=self.tolerant_parsing)
        if pos is not None:
            token_reader.move_to_pos_chars(pos)
        return token_reader

    def parse_content(self, parser, token_reader=None, parsing_state=None,
                      open_context=None):
        r"""
        The main entry point to parse the stored LaTeX code into a node structure.

        Arguments:
        
        - The `parser` must be a callable object that can be called with the
          keyword arguments `latex_walker`, `token_reader` and `parsing_state`.
          The return value of `parser(...)` should be a :py:class:`LatexNode` or
          :py:class:`LatexNodeList` instance.

        - `token_reader` is a :py:class:`LatexTokenReader` instance that is
          tasked with converting the raw string into tokens.  If `None`, then
          :py:meth:`make_token_reader()` is called to create a token reader
          instance.

        - `parsing_state` is a :py:class:`ParsingState` instance that represents
          the current parsing state.  If `None`, then
          :py:meth:`make_parsing_sttae()` is called to create a parsing state.

        - `open_context`, if non-`None`, is a tuple `( open_context_name,
          open_context_token )` with a textual description of the open context
          this construct represents (e.g., ``r"Argument of \mymacro"``) and the
          token that initiated this new context (e.g. the token representing the
          macro ``\mymacro``).  The information about open contexts is used in
          error messages.

        The return value is a tuple `(result, parser_parsing_state_delta)` where
        `result` is the return value of the parser, which is expected to be a
        :py:class:`LatexNode` or :py:class:`LatexNodeList` instance, and where
        `parser_parsing_state_delta`, if non-`None`, is a dictionary with
        information to carry over when parsing further content, for instance, on
        how to update the current parsing state.

        What keys can be set in the `parser_parsing_state_delta` dictionary is
        up to the parsers.  See :py:class:`LatexGeneralNodesParser` and
        :py:class:`LatexInvocableWithArgumentsParser` for examples.  An example
        where `parser_parsing_state_delta` is important is to implement the
        ``\newcommand`` macro which should update the current latex context to
        include the new macro definition.
        """

        the_token_reader = None
        the_parsing_state = None

        if token_reader is None:
            the_token_reader = self.make_token_reader()
        else:
            the_token_reader = token_reader

        if parsing_state is None:
            the_parsing_state = self.make_parsing_state()
        else:
            the_parsing_state = parsing_state

        nodes = None
        info = None

        open_context_name, open_context_tok = None, None
        if open_context:
            open_context_name, open_context_tok = open_context

        start_pos = the_token_reader.cur_pos()
        logger.debug(":: Parsing content (%s @ %r) - %r [%r]::",
                     open_context_name, start_pos, parser, the_parsing_state)

        with self.new_parsing_open_context(open_context_name, open_context_tok) as pc:

            try:

                nodes, info = parser.parse(
                    latex_walker=self,
                    token_reader=the_token_reader,
                    parsing_state=the_parsing_state,
                )

            except LatexWalkerEndOfStream:
                logger.warning("End of stream encountered when parsing content with %s (%s)",
                               parser.__class__.__name__, open_context_name)
                nodes, info = None, None

        if pc.recovery_from_exception is not None:
            nodes, info = pc.perform_recovery_nodes_info(the_token_reader)

        logger.debug(":: PARSED content (%s @ %r) - %r - result %r + %r DONE ::",
                     open_context_name, start_pos, parser, nodes, info)

        return nodes, info


    def make_nodes_collector(self,
                             token_reader,
                             parsing_state,
                             **kwargs):
        return latexnodes.LatexNodesCollector(
            self,
            token_reader,
            parsing_state,
            **kwargs
        )

    def make_node(self, node_class, **kwargs):
        r"""
        Create and return a node of type `node_class` which holds a representation
        of the latex code between positions `pos` and `pos_end` in the parsed
        string.

        The node class should be a :py:class:`LatexNode` subclass.  Keyword
        arguments are supplied directly to the constructor of the node class.

        Mandatory keyword-only arguments are 'pos', 'pos_end', and 'parsing_state'.

        For compatibility with `pylatexenc 2.0`, you can also specify `len=`
        instead of `pos_end=`.

        All nodes produced by :py:meth:`get_latex_nodes()` and friends use this
        method to create node classes.

        .. versionadded:: 2.0
        
           This method was introduced in `pylatexenc 2.0`.

        .. versionchanged:: 3.0
        
           The mandatory `len=` keyword argument was replaced by the mandatory
           keyword argument `pos_end=`.  For backwards compatibility, you can
           still specify `len=` instead of `pos_end=`.
        """
        # mandatory keyword-only arguments:
        pos, pos_end, parsing_state = \
            kwargs.pop('pos'), kwargs.pop('pos_end', None), kwargs.pop('parsing_state')

        if pos_end is None and pos is not None and 'len' in kwargs:
            _util.pylatexenc_deprecated_3(
                "make_node(..., len=..., ...); use ‘pos_end=’ instead of ‘len=’")
            len_ = kwargs['len']
            pos_end = pos + len_

        node = node_class(pos=pos, pos_end=pos_end, parsing_state=parsing_state,
                          latex_walker=self, **kwargs)
        if self.debug_nodes:
            logger.debug("New node: %r", node)
        return node

    def make_nodelist(self, nodelist, **kwargs):
        r"""
        Doc .............................

        .. versionadded:: 3.0
        
           This method was introduced in `pylatexenc 3.0`.

        """

        # mandatory keyword-only argument:
        parsing_state = kwargs.pop('parsing_state')

        return LatexNodeList(
            nodelist=nodelist,
            parsing_state=parsing_state,
            latex_walker=self,
            **kwargs
        )


    def format_pos(self, pos):
        if pos is None:
            return '(location unknown)'
        lineno, colno = self.pos_to_lineno_colno(pos)
        return format_pos(pos, lineno, colno)


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
            self._line_no_calc = _util.LineNumbersCalculator(
                self.s,
                line_number_offset=self.line_number_offset,
                first_line_column_offset=self.first_line_column_offset,
                column_offset=self.column_offset,
            )

        return self._line_no_calc.pos_to_lineno_colno(pos, as_dict=as_dict)


    def __repr__(self):
        return "<LatexWalker {}>".format(fn_unique_object_id(self))







### BEGIN_PYLATEXENC1_LEGACY_SUPPORT_CODE

_legacy_pyltxenc1_do = \
    lambda what, *args: globals()['_legacy_pyltxenc1_'+what](*args)

def _legacy_pyltxenc1_LatexWalker_init_from_macro_dict(walker, kwargs):

    if 'macro_dict' not in kwargs:
        return None

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

    return latex_context

### END_PYLATEXENC1_LEGACY_SUPPORT_CODE


### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE

def _pyltxenc2_LatexWalker_get_token(
        self, pos, include_brace_chars=None, environments=True,
        keep_inline_math=None, parsing_state=None, **kwargs
):
    r"""
    Parses the latex content given to the constructor (and stored in `self.s`),
    starting at position `pos`, to parse a single "token", as defined by
    :py:class:`LatexToken`.

    .. deprecated:: 3.0

       This method was deprecated as of `pylatexenc 3`.  Please use token
       readers instead, see :py:meth:`make_token_reader()` and
       :py:class:`LatexTokenReader`.

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

    _util.pylatexenc_deprecated_3("get_token(); use LatexTokenReader instances instead, "
                                  "see LatexWalker.make_token_reader()")


    if parsing_state is None:
        parsing_state = self.make_parsing_state() # get default parsing state

    parsing_state_setattrs = {}

    if 'brackets_are_chars' in kwargs:
        if not kwargs.pop('brackets_are_chars'):
            if not include_brace_chars:
                include_brace_chars = []
            else:
                include_brace_chars = list(include_brace_chars)
            include_brace_chars += [('[', ']')]

    if include_brace_chars:
        d = parsing_state.latex_group_delimiters + include_brace_chars
        parsing_state_setattrs['latex_group_delimiters'] = d
    if environments is not None and parsing_state.enable_environments != environments:
        parsing_state_setattrs['enable_environments'] = environments

    if parsing_state_setattrs:
        parsing_state = parsing_state.sub_context(**parsing_state_setattrs)

    return self.make_token_reader(pos=pos).peek_token(parsing_state=parsing_state)

LatexWalker.get_token = _pyltxenc2_LatexWalker_get_token



def _pyltxenc2_LatexWalker_get_latex_nodes(
        self,
        pos=0,
        stop_upon_closing_brace=None,
        stop_upon_end_environment=None,
        stop_upon_closing_mathmode=None,
        read_max_nodes=None,
        parsing_state=None
):
    r"""
    Parses the latex content given to the constructor (and stored in `self.s`)
    into a list of nodes.

    .. deprecated:: 3.0

       This method was deprecated as of `pylatexenc 3`.  Please use parser
       objects instead.  You probably want something like::

        # Deprecated since pylatexenc 3:
        
        #nodelist, npos, nlen = my_latex_walker.get_latex_nodes(
        #    parsing_state=parsing_state
        #)
        
        # New syntax since pylatexenc 3:
        
        nodelist, parsing_state_delta = my_latex_walker.parse_content(
            latexnodes.parsers.LatexGeneralNodesParser(),
            parsing_state=parsing_state
        )
        npos = nodelist.pos
        nlen = nodelist.len # or nodelist.pos_end - nodelist.pos

       See the documentation for
       :py:class:`~latexnodes.parsers.LatexGeneralNodesParser` for information
       on how to implement similar behavior as with the `stop_upon_*=`
       arguments, or by `read_max_nodes=`.  See also, for instance, the
       :py:class:`~latexnodes.parsers.LatexSingleNodeParser` parser class.

    Returns a tuple `(nodelist, pos, len)` where:

    - `nodelist` is a list of :py:class:`LatexNode`\ 's representing the parsed
      LaTeX code.

    - `pos` is the same as the `pos` given as argument; if there is leading
      whitespace it is reported in `nodelist` using a
      :py:class:`LatexCharsNode`.

    - `len` is the length of the parsed expression.  If one of the
      `stop_upon_...=` arguments are provided (cf below), then the `len`
      includes the length of the token/expression that stopped the parsing.

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

    _util.pylatexenc_deprecated_3(
        "get_latex_nodes(): "
        "use LatexWalker.parse_content(LatexGeneralNodesParser(), ...) instead."
    )

    if parsing_state is None:
        parsing_state = self.make_parsing_state()

    def stop_token_condition(tok):
        if stop_upon_closing_brace is not None:
            if tok.tok == 'brace_close' and tok.arg == stop_upon_closing_brace:
                # stop condition met
                logger.debug("Stop condition reached - closing brace - %r", tok)
                return True
        if stop_upon_end_environment is not None:
            if tok.tok == 'end_environment' and tok.arg == stop_upon_end_environment:
                # stop condition met
                logger.debug("Stop condition reached - end environ - %r", tok)
                return True
        if stop_upon_closing_mathmode is not None:
            if tok.tok in ('mathmode_inline', 'mathmode_display') \
               and tok.arg == stop_upon_closing_mathmode:
                # stop condition met
                logger.debug("Stop condition reached - closing math mode - %r", tok)
                return True
        return False

    def stop_nodelist_condition(nodelist):
        #print(f"**** nodelist stopping condition ? *** {nodelist=} ")
        if read_max_nodes is not None:
            if len(nodelist) >= read_max_nodes:
                # stop condition met
                logger.debug("Stop condition reached - nodes read (%d) >= read_max_nodes (%d)",
                             len(nodelist), read_max_nodes)
                return True
        return False

    if stop_upon_closing_brace is not None:
        # we need to include the corresponding open brace as brace character
        # in the parsing state.
        if len(stop_upon_closing_brace) == 2:
            opbr,clbr = stop_upon_closing_brace
            stop_upon_closing_brace = clbr
        else:
            clbr = stop_upon_closing_brace
            opbr = { '}': '{',
                     ']': '[', 
                     ')': '(',
                     '>': '<' }.get(clbr, None)
        if (opbr, clbr) not in parsing_state.latex_group_delimiters:
            parsing_state = parsing_state.sub_context(
                latex_group_delimiters= \
                    list(parsing_state.latex_group_delimiters) + [ (opbr, clbr) ]
            )

        require_stop_condition_met = True
        stop_condition_message = "Was expecting ‘{}’".format(stop_upon_closing_brace)

    elif stop_upon_end_environment is not None:
        require_stop_condition_met = True
        stop_condition_message = \
            "Was expecting ‘\\end{}{}{}’".format('{',stop_upon_end_environment,'}')

    elif stop_upon_closing_mathmode is not None:
        require_stop_condition_met = True
        stop_condition_message = \
            "Was expecting ‘{}’".format(stop_upon_closing_mathmode)

    else:
        stop_condition_message = None
        require_stop_condition_met = False

    # tokens that cause a stop should be absorbed in pos_end (e.g. closing
    # brace, closing math mode delimiter)
    def handle_stop_condition_token(token, latex_walker, token_reader, parsing_state):
        logger.debug("moving past token %r", token)
        token_reader.move_past_token(token)

    parser = parsers.LatexGeneralNodesParser(
        stop_token_condition=stop_token_condition,
        stop_nodelist_condition=stop_nodelist_condition,
        require_stop_condition_met=require_stop_condition_met,
        handle_stop_condition_token=handle_stop_condition_token,
        stop_condition_message=stop_condition_message,
    )

    token_reader = self.make_token_reader(pos=pos)

    logger.debug("token_reader.cur_pos() is initialized to %d", token_reader.cur_pos())

    nodes, info = self.parse_content(
        parser,
        token_reader=token_reader,
        parsing_state=parsing_state,
    )

    logger.debug("token_reader.cur_pos() is now %d", token_reader.cur_pos())

    # use cur_pos() to include any final stop condition token etc.
    pos_end = token_reader.cur_pos()

    if info is not None:
        logger.warning("Call to get_latex_nodes() ignores parsing state changes information "
                       "of parsing state")

    if nodes is not None:
        p = nodes.pos
        l = pos_end - p
    else:
        p = None
        l = None

    return (nodes, p, l)

LatexWalker.get_latex_nodes = _pyltxenc2_LatexWalker_get_latex_nodes



def _pyltxenc2_LatexWalker_get_latex_expression(
        self,
        pos,
        strict_braces=None,
        parsing_state=None
):
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

    _util.pylatexenc_deprecated_3(
        "get_latex_expression(): "
        "use LatexWalker.parse_content(LatexExpressionParser(), ...) instead."
    )

    logger.debug("get_latex_expression(): “%s...”",
                 self.s[pos:pos+50])

    parser = parsers.LatexExpressionParser(
        return_full_node_list=False,
        single_token_requiring_arg_is_error=not self.tolerant_parsing,
        allow_pre_space=True,
        allow_pre_comments=True,
    )

    token_reader = self.make_token_reader(pos=pos)

    try:
        nodes, info = self.parse_content(
            parser,
            token_reader=token_reader,
            parsing_state=parsing_state,
        )
        logger.debug("nodes = %r, info = %r", nodes, info)
    except LatexWalkerParseError as e:
        # only raise error if we have strict_braces; otherwise leave token in
        # the input stream and let the next call report an error.  (I don't know
        # why this is the best behavior, but it's needed because that's how
        # pylatexenc 2 worked.)
        if getattr(e, '_error_was_unexpected_closing_brace_in_expression', False) \
           and not strict_braces:
            logger.warning(
                "Ignoring parse error (strict_braces=False in "
                "LatexWalker.get_latex_expression)", exc_info=True)
            nodes, info = None, None
        else:
            raise

    if nodes is not None and (
            nodes.isNodeType(LatexMacroNode)
            or nodes.isNodeType(LatexEnvironmentNode)
            or nodes.isNodeType(LatexSpecialsNode)
    ):
        # match behavior of pylatexenc 2, where a macros' nodeargd attribute was
        # always None even if the macro didn't accept any arguments
        nodes.nodeargd = None

    if info is not None:
        logger.warning("Call to get_latex_expression() ignores parsing state changes information "
                       "of parsing state")

    if nodes is None and (self.tolerant_parsing or strict_braces is False):
        logger.warning(
            "get_latex_expression(): No expression found! creating a dummy chars node."
        )

        nodes = self.make_node(
            LatexCharsNode,
            parsing_state=parsing_state,
            chars='',
            pos=pos,
            pos_end=pos,
        )

    if nodes is not None:
        p, l = nodes.pos, nodes.len
    else:
        p, l = pos, 0

    return (nodes, p, l)


LatexWalker.get_latex_expression = _pyltxenc2_LatexWalker_get_latex_expression


def _pyltxenc2_LatexWalker_get_latex_braced_group(
        self,
        pos,
        brace_type='{',
        parsing_state=None
):
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

    _util.pylatexenc_deprecated_3(
        "get_latex_braced_group(): "
        "use LatexWalker.parse_content(LatexDelimitedGroupParser(), ...) instead."
    )

    if parsing_state is None:
        parsing_state = self.make_parsing_state() # get default parsing state

    if brace_type == '{':
        brace_type = ['{', '}']
    elif brace_type == '[':
        brace_type = ['[', ']']
    elif brace_type == '(':
        brace_type = ['(', ')']
    elif brace_type == '<':
        brace_type = ['<', '>']
    elif len(brace_type) == 2:
        pass
    else:
        raise ValueError("Invalid brace type for get_latex_braced_group(): {}"
                         .format(brace_type))
    
    brace_type = tuple(brace_type)

    #require_brace_type = brace_type[0] # the opening brace
    #
    # ### This is now done automatically by LatexDelimitedGroupParser
    #
    # include_brace_chars = None
    # if brace_type not in parsing_state.latex_group_delimiters:
    #     include_brace_chars = [ brace_type ]
    
    parser = parsers.LatexDelimitedGroupParser(
        delimiters=brace_type,
        allow_pre_space=True,
        #include_delimiter_chars=include_brace_chars,
    )

    nodes, info = self.parse_content(
        parser,
        token_reader=self.make_token_reader(pos=pos),
        parsing_state=parsing_state,
    )

    if info is not None:
        logger.warning("Call to get_latex_braced_group() ignores parsing state changes "
                       "information of parsing state")

    if nodes is not None:
        p, l = nodes.pos, nodes.len
    else:
        p, l = pos, 0

    return (nodes, p, l)

LatexWalker.get_latex_braced_group = _pyltxenc2_LatexWalker_get_latex_braced_group



def _pyltxenc2_LatexWalker_get_latex_environment(
        self,
        pos,
        environmentname=None,
        parsing_state=None
):
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

    .. deprecated:: 3.0
    
       This function was deprecated in pylatexenc 3.0.  Use
       `LatexWalker.parse_content(LatexSingleNodeParser(), ...)`
       at the beginning of the environment.

    .. versionadded:: 2.0

       The `parsing_state` argument was introduced in version 2.0.
    """

    _util.pylatexenc_deprecated_3(
        "get_latex_environment(): "
        "use LatexWalker.parse_content(LatexSingleNodeParser(), ...) instead."
    )

    if parsing_state is None:
        parsing_state = self.make_parsing_state() # get default parsing state


    # parse a single node and then we'll verify that it was the correct
    # environment node
    parser = parsers.LatexSingleNodeParser()

    nodes, info = self.parse_content(
        parser,
        token_reader=self.make_token_reader(pos=pos),
        parsing_state=parsing_state,
    )

    if info is not None:
        logger.warning("Call to get_latex_environment() ignores parsing state changes "
                       "information of parsing state")

    if not nodes or len(nodes) != 1 or not nodes[0].isNodeType(LatexEnvironmentNode):
        raise LatexWalkerParseError("Expected environment, got {}".format(nodes))

    envnode = nodes[0]

    if environmentname is not None and envnode.environmentname != environmentname:
        raise LatexWalkerParseError(
            "Expected environment {{{correct_envname}}}, got {{{got_envname}}}".format(
                correct_envname=environmentname,
                got_envname=envnode.environmentname
            )
        )

    p, l = envnode.pos, envnode.len

    return (envnode, p, l)
    
LatexWalker.get_latex_environment = _pyltxenc2_LatexWalker_get_latex_environment

def _pyltxenc2_LatexWalker_get_latex_maybe_optional_arg(self, pos, parsing_state=None):
    r"""
    Parses the latex content given to the constructor (and stored in `self.s`),
    starting at position `pos`, to attempt to parse an optional argument.

    Parsing might be influenced by the `parsing_state`. See doc for
    :py:class:`ParsingState`.  If `parsing_state` is `None`, the default
    parsing state is used.

    Attempts to parse an optional argument. If this is successful, we return
    a tuple `(node, pos, len)` if success where `node` is a
    :py:class:`LatexGroupNode`.  Otherwise, this method returns None.

    .. deprecated:: 3.0

       This method was deprecated in `pylatexenc 3.0`.  You should use the
       stronger and more flexible parsers mechanism instead, e.g.,
       ``LatexWalker.parse_content(LatexOptionalSquareBracketsParser(), ...)``

    .. versionadded:: 2.0

       The `parsing_state` argument was introduced in version 2.0.
    """

    _util.pylatexenc_deprecated_3(
        "get_latex_maybe_optional_arg(): "
        "use LatexWalker.parse_content(LatexOptionalSquareBracketsParser(), ...) instead."
    )


    if parsing_state is None:
        parsing_state = self.make_parsing_state() # get default parsing state


    # parse a single node and then we'll verify that it was the correct
    # environment node
    parser = parsers.LatexOptionalSquareBracketsParser()

    nodes, info = self.parse_content(
        parser,
        token_reader=self.make_token_reader(pos=pos),
        parsing_state=parsing_state,
    )

    if info is not None:
        logger.warning("Call to get_latex_maybe_optional_arg() ignores parsing state changes "
                       "information of parsing state")


    if nodes is None:
        return None

    p, l = nodes.pos, nodes.len

    return (nodes, p, l)


LatexWalker.get_latex_maybe_optional_arg = \
    _pyltxenc2_LatexWalker_get_latex_maybe_optional_arg


### END_PYLATEXENC2_LEGACY_SUPPORT_CODE
