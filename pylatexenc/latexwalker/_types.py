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

from ..macrospec import _parsedargs as macrospec_parsedargs


# for Py3
_basestring = str
_unicode_from_str = lambda x: x

## Begin Py2 support code
import sys
if sys.version_info.major == 2:
    # Py2
    _basestring = basestring
    _unicode_from_str = lambda x: x.decode('utf-8')
## End Py2 support code





class LatexWalkerError(Exception):
    """
    Generic exception class raised by this module.
    """
    pass


class LatexWalkerParseError(LatexWalkerError):
    """
    Represents an error while parsing LaTeX code.

    The following attributes are available if they were provided to the class
    constructor:

    .. py:attribute:: msg

       The error message

    .. py:attribute:: s

       The string that was currently being parsed

    .. py:attribute:: pos
    
       The index in the string where the error occurred, starting at zero.

    .. py:attribute:: lineno

       The line number where the error occurred, starting at 1.

    .. py:attribute:: colno

       The column number where the error occurred in the line `lineno`, starting
       at 1.
    """
    def __init__(self, msg, s=None, pos=None, lineno=None, colno=None):
        self.input_source = None # attribute can be set to add to error msg display
        self.msg = msg
        self.s = s
        self.pos = pos
        self.lineno = lineno
        self.colno = colno
        self.open_contexts = []

        super(LatexWalkerParseError, self).__init__(self._dispstr())

    def _dispstr(self):
        msg = self.msg
        if self.input_source:
            msg += '  in {}'.format(self.input_source)
        disp = msg + " %s"%(self._fmt_pos(self.pos, self.lineno, self.colno))
        if self.open_contexts:
            disp += '\nOpen LaTeX blocks:\n'
            for context in reversed(self.open_contexts):
                what, pos, lineno, colno = context
                disp += '{empty:8}{loc:>10}  {what}\n'.format(empty='',
                                                        loc=self._fmt_pos(pos,lineno,colno),
                                                        what=what)
        return disp

    def _fmt_pos(self, pos, lineno, colno):
        if lineno is not None:
            if colno is not None:
                return '@(%d,%d)'%(lineno, colno)
            return '@%d'%(lineno)
        return '@ char %d'%(pos)

    def __str__(self):
        return self._dispstr()




class LatexWalkerEndOfStream(LatexWalkerError):
    """
    Reached end of input stream (e.g., end of file).
    """
    def __init__(self, final_space=''):
        super(LatexWalkerEndOfStream, self).__init__()
        self.final_space = final_space



# ------------------------------------------------------------------------------




class LatexToken(object):
    r"""
    Represents a token read from the LaTeX input.

    This is used internally by :py:class:`LatexWalker`'s methods.  You probably
    don't need to worry about individual tokens.  Rather, you should use the
    high-level functions provided by :py:class:`LatexWalker` (e.g.,
    :py:meth:`~LatexWalker.get_latex_nodes()`).  So most likely, you can ignore
    this class entirely.

    Instances of this class are what the method
    :py:meth:`LatexWalker.get_token()` returns.  See the doc of that function
    for more information on how tokens are parsed.

    This is not the same thing as a LaTeX token, it's just a part of the input
    which we treat in the same way (e.g. a bunch of content characters, a
    comment, a macro, etc.)

    Information about the object is stored into the fields `tok` and `arg`. The
    `tok` field is a string which identifies the type of the token. The `arg`
    depends on what `tok` is, and describes the actual input.

    Additionally, this class stores information about the position of the token
    in the input stream in the field `pos`.  This `pos` is an integer which
    corresponds to the index in the input string.  The field `len` stores the
    length of the token in the input string.  This means that this token spans
    in the input string from `pos` to `pos+len`.

    Leading whitespace before the token is not returned as a separate
    'char'-type token, but it is given in the `pre_space` field of the token
    which follows.  Pre-space may contain a newline, but not two consecutive
    newlines.

    The `post_space` is only used for 'macro' and 'comment' tokens, and it
    stores any spaces encountered after a macro, or the newline with any
    following spaces that terminates a LaTeX comment.  When we encounter two
    consecutive newlines these are not included in `post_space`.

    The `tok` field may be one of:

      - 'char': raw character(s) which have no special LaTeX meaning and which
        are part of the text content.
        
        The `arg` field contains the characters themselves.

      - 'macro': a macro invocation, but not ``\begin`` or ``\end``
        
        The `arg` field contains the name of the macro, without the leading
        backslash.

      - 'begin_environment': an invocation of ``\begin{environment}``.
        
        The `arg` field contains the name of the environment inside the braces.

      - 'end_environment': an invocation of ``\end{environment}``.
        
        The `arg` field contains the name of the environment inside the braces.

      - 'comment': a LaTeX comment delimited by a percent sign up to the end of
        the line.
        
        The `arg` field contains the text in the comment line, not including the
        percent sign nor the newline.

      - 'brace_open': an opening brace.  This is usually a curly brace, and
        sometimes also a square bracket.  What is parsed as a brace depends on
        the arguments to :py:meth:`~LatexWalker.get_token()`.
        
        The `arg` is a string which contains the relevant brace character.
        
      - 'brace_close': a closing brace.  This is usually a curly brace, and
        sometimes also a square bracket.  What is parsed as a brace depends on
        the arguments to :py:meth:`~LatexWalker.get_token()`.
        
        The `arg` is a string which contains the relevant brace character.

      - 'mathmode_inline': a delimiter which starts/ends inline math.  This is
        (e.g.) a single '$' character which is not part of a double '$$'
        display environment delimiter.

        The `arg` is the string value of the delimiter in question ('$')

      - 'mathmode_display': a delimiter which starts/ends display math, e.g.,
        ``\[``.

        The `arg` is the string value of the delimiter in question (e.g.,
        ``\[`` or ``$$``)

      - 'specials': a character or character sequence that has a special
        meaning in LaTeX.  E.g., '~', '&', etc.

        The `arg` field is then the corresponding
        :py:class:`~pylatexenc.macrospec.SpecialsSpec` instance.  [The rationale
        for setting `arg` to a `SpecialsSpec` instance, in contrast to the
        behavior for macros and envrionments, is that macros and environments
        are delimited directly by LaTeX syntax and are determined unambiguously
        without any lookup in the latex context database.  This is not the case
        for specials.]
    """
    def __init__(self, tok, arg, pos, len, pre_space, post_space=''):
        self.tok = tok
        self.arg = arg
        self.pos = pos
        self.len = len
        self.pre_space = pre_space
        self.post_space = post_space
        self._fields = ['tok', 'arg', 'pos', 'len', 'pre_space']
        if self.tok in ('macro', 'comment'):
            self._fields.append('post_space')
        super(LatexToken, self).__init__()


    def __unicode__(self):
        return _unicode_from_str(self.__str__())

    def __repr__(self):
        return (
            "LatexToken(" +
            ", ".join([ "%s=%r"%(k,getattr(self,k))
                        for k in self._fields ]) +
            ")"
            )

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return all( ( getattr(self, f) == getattr(other, f)  for f in self._fields ) )

    # see https://docs.python.org/3/library/constants.html#NotImplemented
    def __ne__(self, other): return NotImplemented

    __hash__ = None





# ------------------------------------------------------------------------------



class LatexNode(object):
    """
    Represents an abstract 'node' of the latex document.

    Use :py:meth:`nodeType()` to figure out what type of node this is, and
    :py:meth:`isNodeType()` to test whether it is of a given type.

    You should use :py:meth:`LatexWalker.make_node()` to create nodes, so that
    the latex walker has the opportunity to do some additional setting up.

    All nodes have the following attributes:

    .. py:attribute:: parsing_state

       The parsing state at the time this node was created.  This object stores
       additional context information for this node, such as whether or not this
       node was parsed in a math mode block of LaTeX code.

       See also the :py:meth:`LatexWalker.make_parsing_state()` and the
       `parsing_state` argument of :py:meth:`LatexWalker.get_latex_nodes()`.

    .. py:attribute:: pos

       The position in the parsed string that this node represents.  The parsed
       string can be recovered as `parsing_state.s`, see
       :py:attr:`ParsingState.s`.

    .. py:attribute:: len

       How many characters in the parsed string this node represents, starting
       at position `pos`.  The parsed string can be recovered as
       `parsing_state.s`, see :py:attr:`ParsingState.s`.

    .. versionadded:: 2.0
       
       The attributes `parsing_state`, `pos` and `len` were added in
       `pylatexenc 2.0`.
    """
    def __init__(self, _fields, _redundant_fields=None,
                 parsing_state=None, pos=None, len=None, **kwargs):

        # Important: subclasses must specify a list of fields they set in the
        # `_fields` argument.  They should only specify base (non-redundant)
        # fields; if they have "redundant" fields, specify the additional fields
        # in _redundant_fields=...
        super(LatexNode, self).__init__(**kwargs)

        self.parsing_state = parsing_state
        self.pos = pos
        self.len = len

        self._fields = tuple(['pos', 'len'] + list(_fields))
        if _redundant_fields is not None:
            self._redundant_fields = tuple(list(self._fields) + list(_redundant_fields))
        else:
            self._redundant_fields = self._fields

    def nodeType(self):
        """
        Returns the class which corresponds to the type of this node.  This is a
        Python class object, that is one of
        :py:class:`~pylatexenc.latexwalker.LatexCharsNode`,
        :py:class:`~pylatexenc.latexwalker.LatexGroupNode`, etc.
        """
        return LatexNode

    def isNodeType(self, t):
        """
        Returns `True` if the current node is of the given type.  The argument `t`
        must be a Python class such as,
        e.g. :py:class:`~pylatexenc.latexwalker.LatexGroupNode`.
        """
        return isinstance(self, t)

    def latex_verbatim(self):
        r"""
        Return the chunk of LaTeX code that this node represents.

        This is a shorthand for ``node.parsing_state.s[node.pos:node.pos+node.len]``.
        """
        if self.parsing_state is None:
            raise TypeError("Can't use latex_verbatim() on node because we don't "
                            "have any parsing_state set")
        return self.parsing_state.s[self.pos : self.pos+self.len]

    def __eq__(self, other):
        return other is not None  and  \
            self.nodeType() == other.nodeType()  and  \
            other.parsing_state is self.parsing_state and \
            other.pos == self.pos and \
            other.len == self.len and \
            all(
                ( getattr(self, f) == getattr(other, f)  for f in self._fields )
            )

    # see https://docs.python.org/3/library/constants.html#NotImplemented
    def __ne__(self, other): return NotImplemented

    __hash__ = None

    def __unicode__(self):
        return _unicode_from_str(self.__str__())
    def __str__(self):
        return self.__repr__()
    def __repr__(self):
        return (
            self.nodeType().__name__ + "(" +
            "parsing_state=<parsing state {}>, ".format(id(self.parsing_state)) +
            ", ".join([ "%s=%r"%(k,getattr(self,k))  for k in self._fields ]) +
            ")"
            )


class LatexCharsNode(LatexNode):
    """
    A string of characters in the LaTeX document, without any special LaTeX
    code.

    .. py:attribute:: chars

       The string of characters represented by this node.
    """
    def __init__(self, chars, **kwargs):
        super(LatexCharsNode, self).__init__(
            _fields = ('chars',),
            **kwargs
        )
        self.chars = chars

    def nodeType(self):
        return LatexCharsNode


class LatexGroupNode(LatexNode):
    r"""
    A LaTeX group delimited by braces, ``{like this}``.

    Note: in the case of an optional macro or environment argument, this node is
    also used to represents a group delimited by square braces instead of curly
    braces.

    .. py:attribute:: nodelist

       A list of nodes describing the contents of the LaTeX braced group.  Each
       item of the list is a :py:class:`LatexNode`.

    .. py:attribute:: delimiters

       A 2-item tuple that stores the delimiters for this group node.  Usually
       this is `('{', '}')`, except for optional macro arguments where this
       might be for instance `('[', ']')`.

       .. versionadded:: 2.0

          The `delimiters` field was added in `pylatexenc 2.0`.
    """
    def __init__(self, nodelist, **kwargs):
        delimiters = kwargs.pop('delimiters', ('{', '}'))
        super(LatexGroupNode, self).__init__(
            _fields=('nodelist','delimiters',),
            **kwargs
        )
        self.nodelist = nodelist
        self.delimiters = delimiters

    def nodeType(self):
        return LatexGroupNode


class LatexCommentNode(LatexNode):
    r"""
    A LaTeX comment, delimited by a percent sign until the end of line.

    .. py:attribute:: comment

       The comment string, not including the '%' sign nor the following newline

    .. py:attribute:: comment_post_space

       The newline that terminated the comment possibly followed by spaces
       (e.g., indentation spaces of the next line)

    """
    def __init__(self, comment, **kwargs):
        comment_post_space = kwargs.pop('comment_post_space', '')

        super(LatexCommentNode, self).__init__(
            _fields = ('comment', 'comment_post_space', ),
            **kwargs
        )

        self.comment = comment
        self.comment_post_space = comment_post_space

    def nodeType(self):
        return LatexCommentNode


class LatexMacroNode(LatexNode):
    r"""
    Represents a macro type node, e.g. ``\textbf``

    .. py:attribute:: macroname

       The name of the macro (string), *without* the leading backslash.

    .. py:attribute:: nodeargd

       The :py:class:`pylatexenc.macrospec.ParsedMacroArgs` object that
       represents the macro arguments.

       For macros that do not accept any argument, this is an empty
       :py:class:`~pylatexenc.macrospec.ParsedMacroArgs` instance.  The
       attribute `nodeargd` can be `None` even for macros that accept arguments,
       in the situation where :py:meth:`LatexWalker.get_latex_expression()`
       encounters the macro when reading a single expression.

       Arguments must be declared in the latex context passed to the
       :py:class:`LatexWalker` constructor, using a suitable
       :py:class:`pylatexenc.macrospec.MacroSpec` object.  Some known macros are
       already declared in the default latex context.

       .. versionadded:: 2.0

          The `nodeargd` attribute was introduced in `pylatexenc 2`.

    .. py:attribute:: macro_post_space

       Any spaces that were encountered immediately after the macro.

    The following attributes are obsolete since `pylatexenc 2.0`.

    .. py:attribute:: nodeoptarg

       .. deprecated:: 2.0

          Macro arguments are stored in `nodeargd` in `pylatexenc 2`.  Accessing
          the argument `nodeoptarg` will still give a first optional argument
          for standard latex macros, for backwards compatibility.

       If non-`None`, this corresponds to the optional argument of the macro.

    .. py:attribute:: nodeargs

       .. deprecated:: 2.0

          Macro arguments are stored in `nodeargd` in pylatexenc 2.  Accessing
          the argument `nodeargs` will still provide a list of argument nodes
          for standard latex macros, for backwards compatibility.

       A list of arguments to the macro. Each item in the list is a
       :py:class:`LatexNode`.
    """
    def __init__(self, macroname, **kwargs):
        nodeargd=kwargs.pop('nodeargd', macrospec_parsedargs.ParsedMacroArgs())
        macro_post_space=kwargs.pop('macro_post_space', '')
        # legacy:
        nodeoptarg=kwargs.pop('nodeoptarg', None)
        nodeargs=kwargs.pop('nodeargs', [])

        super(LatexMacroNode, self).__init__(
            _fields = ('macroname','nodeargd','macro_post_space'),
            _redundant_fields = ('nodeoptarg','nodeargs'),
            **kwargs)

        self.macroname = macroname
        self.nodeargd = nodeargd
        self.macro_post_space = macro_post_space
        # legacy:
        self.nodeoptarg = nodeoptarg
        self.nodeargs = nodeargs

    def nodeType(self):
        return LatexMacroNode


class LatexEnvironmentNode(LatexNode):
    r"""
    A LaTeX Environment Node, i.e. ``\begin{something} ... \end{something}``.

    .. py:attribute:: environmentname

       The name of the environment ('itemize', 'equation', ...)

    .. py:attribute:: nodelist

       A list of :py:class:`LatexNode`'s that represent all the contents between
       the ``\begin{...}`` instruction and the ``\end{...}`` instruction.

    .. py:attribute:: nodeargd

       The :py:class:`pylatexenc.macrospec.ParsedMacroArgs` object that
       represents the arguments passed to the environment.  These are arguments
       that are present after the ``\begin{xxxxxx}`` command, as in
       ``\begin{tabular}{ccc}`` or ``\begin{figure}[H]``.  Arguments must be
       declared in the latex context passed to the :py:class:`LatexWalker`
       constructor, using a suitable
       :py:class:`pylatexenc.macrospec.EnvironmentSpec` object.  Some known
       environments are already declared in the default latex context.

       .. versionadded:: 2.0

          The `nodeargd` attribute was introduced in `pylatexenc 2`.

    The following attributes are available, but they are obsolete since
    `pylatexenc 2.0`.

    .. py:attribute:: envname

       .. deprecated:: 2.0

          This attribute was renamed `environmentname` for consistency with the
          rest of the package.

    .. py:attribute:: optargs

       .. deprecated:: 2.0

          Macro arguments are stored in `nodeargd` in `pylatexenc 2`.  Accessing
          the argument `optargs` will still give a list of initial optional
          arguments for standard latex macros, for backwards compatibility.

    .. py:attribute:: args

       .. deprecated:: 2.0

          Macro arguments are stored in `nodeargd` in `pylatexenc 2`.  Accessing
          the argument `args` will still give a list of curly-brace-delimited
          arguments for standard latex macros, for backwards compatibility.
    """
    
    def __init__(self, environmentname, nodelist, **kwargs):
        nodeargd = kwargs.pop('nodeargd', macrospec_parsedargs.ParsedMacroArgs())
        # legacy:
        optargs = kwargs.pop('optargs', [])
        args = kwargs.pop('args', [])

        super(LatexEnvironmentNode, self).__init__(
            _fields = ('environmentname','nodelist','nodeargd',),
            _redundant_fields = ('envname', 'optargs','args',),
            **kwargs)

        self.environmentname = environmentname
        self.nodelist = nodelist
        self.nodeargd = nodeargd
        # legacy:
        self.envname = environmentname
        self.optargs = optargs
        self.args = args

    def nodeType(self):
        return LatexEnvironmentNode


class LatexSpecialsNode(LatexNode):
    r"""
    Represents a specials type node, e.g. ``&`` or ``~``

    .. py:attribute:: specials_chars

       The name of the specials (string), *without* the leading backslash.

    .. py:attribute:: nodeargd

       If the specials spec (cf. :py:class:`~pylatexenc.macrospec.SpecialsSpec`)
       has `args_parser=None` then the attribute `nodeargd` is set to `None`.
       If `args_parser` is specified in the spec, then the attribute `nodeargd`
       is a :py:class:`pylatexenc.macrospec.ParsedMacroArgs` instance that 
       represents the arguments to the specials.

       The `nodeargd` attribute can also be `None` even if the specials expects
       arguments, in the special situation where
       :py:meth:`LatexWalker.get_latex_expression()` encounters this specials.

       Arguments must be declared in the latex context passed to the
       :py:class:`LatexWalker` constructor, using a suitable
       :py:class:`pylatexenc.macrospec.SpecialsSpec` object.  Some known latex
       specials are already declared in the default latex context.

    .. versionadded:: 2.0

       Latex specials were introduced in `pylatexenc 2.0`.
    """
    def __init__(self, specials_chars, **kwargs):
        nodeargd=kwargs.pop('nodeargd', None)

        super(LatexSpecialsNode, self).__init__(
            _fields = ('specials_chars','nodeargd'),
            **kwargs)

        self.specials_chars = specials_chars
        self.nodeargd = nodeargd

    def nodeType(self):
        return LatexSpecialsNode


class LatexMathNode(LatexNode):
    r"""
    A Math node type.

    .. py:attribute:: displaytype

       Either 'inline' or 'display', to indicate an inline math block or a
       display math block. (Note that math environments such as
       ``\begin{equation}...\end{equation}``, are reported as
       :py:class:`LatexEnvironmentNode`'s, and not as
       :py:class:`LatexMathNode`'s.)

    .. py:attribute:: delimiters

       A 2-item tuple containing the begin and end delimiters used to delimit
       this math mode section.

       .. versionadded:: 2.0

          The `delimiters` attribute was introduced in `pylatexenc 2`.

    .. py:attribute:: nodelist
    
       The contents of the environment, given as a list of
       :py:class:`LatexNode`'s.
    """
    def __init__(self, displaytype, nodelist=[], **kwargs):
        delimiters = kwargs.pop('delimiters', (None, None))

        super(LatexMathNode, self).__init__(
            _fields = ('displaytype','nodelist','delimiters'),
            **kwargs
        )

        self.displaytype = displaytype
        self.nodelist = nodelist
        self.delimiters = delimiters

    def nodeType(self):
        return LatexMathNode



# ------------------------------------------------------------------------------
