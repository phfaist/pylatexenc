#
# The MIT License (MIT)
# 
# Copyright (c) 2015 Philippe Faist
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

"""
The ``latexwalker`` module provides a simple API for parsing LaTeX snippets, and
representing the contents using a data structure based on nodes classes.

LatexWalker will understand the syntax of most common macros.  However, ``latexwalker`` is
NOT a replacement for a full LaTeX engine.  (Originally, ``latexwalker`` was desigend to
extract useful text for indexing for text database searches of LaTeX content.)
"""

from __future__ import print_function #, absolute_import

import re
from collections import namedtuple
import sys
import logging

if sys.version_info.major > 2:
    def unicode(string): return string
    basestring = str

logger = logging.getLogger(__name__)



class LatexWalkerError(Exception):
    """
    Generic exception class raised by this module.
    """
    pass

class LatexWalkerParseError(LatexWalkerError):
    """
    Parse error.  The following attributes are available: `msg` (the error message), `s`
    (the parsed string), `pos` (the position of the error in the string, 0-based index).
    """
    def __init__(self, msg, s=None, pos=None):
        self.msg = msg
        self.s = s
        self.pos = pos
        disp = '...'+s[max(pos-25,0):pos]
        disp = '\n%s\n'%(disp)  +  (' '*len(disp)) + s[pos:pos+25]+'...'
        LatexWalkerError.__init__(self, msg + (
            " @ %d:\n%s" %(pos, disp)
            ))

class LatexWalkerEndOfStream(LatexWalkerError):
    """
    Reached end of input stream (e.g., end of file).
    """
    pass



MacrosDef = namedtuple('MacrosDef', ['macname', 'optarg', 'numargs'])
"""
Class which stores a Macro syntax.

- `macname` stores the name of the macro, without the leading backslash.

- `optarg` may be one of `True`, `False`, or `None`.

  + if `True`, the macro expects as first argument an optional argument in square
    brackets. Then, `numargs` specifies the number of additional mandatory arguments to
    the command, given in usual curly braces (or simply as one TeX token)

  + if `False`, the macro only expects a number of mandatory arguments given by
    `numargs`. The mandatory arguments are given in usual curly braces (or simply as one
    TeX token)

  + if `None`, then `numargs` is a string of either characters "{" or "[", in which each
    curly brace specifies a mandatory argument and each square bracket specifies an
    optional argument in square brackets.  For example, "{{[{" expects two mandatory
    arguments, then an optional argument in square brackets, and then another mandatory
    argument.
"""


_default_macro_list = (
    MacrosDef('documentclass', True, 1),
    MacrosDef('usepackage', True, 1),
    MacrosDef('selectlanguage', True, 1),
    MacrosDef('setlength', True, 2),
    MacrosDef('addlength', True, 2),
    MacrosDef('setcounter', True, 2),
    MacrosDef('addcounter', True, 2),
    MacrosDef('newcommand', None, "{[{"),
    MacrosDef('renewcommand', None, "{[{"),
    MacrosDef('DeclareMathOperator', False, 2),
    MacrosDef('input', False, 1),

    MacrosDef('hspace', False, 1),
    MacrosDef('vspace', False, 1),

    MacrosDef('\\', True, 0), # (Note: single backslash) end of line with optional spacing, e.g.  \\[2mm]
    MacrosDef('item', True, 0),

    # \input{someotherfile}
    MacrosDef('input', False, 1),
    MacrosDef('include', False, 1),

    MacrosDef('includegraphics', True, 1),

    MacrosDef('textit', False, 1),
    MacrosDef('textbf', False, 1),
    MacrosDef('textsc', False, 1),
    MacrosDef('textsl', False, 1),
    MacrosDef('text', False, 1),
    MacrosDef('mathrm', False, 1),

    MacrosDef('label', False, 1),
    MacrosDef('ref', False, 1),
    MacrosDef('eqref', False, 1),
    MacrosDef('url', False, 1),
    MacrosDef('hypersetup', False, 1),
    MacrosDef('footnote', True, 1),

    MacrosDef('keywords', False, 1),

    MacrosDef('hphantom', True, 1),
    MacrosDef('vphantom', True, 1),

    MacrosDef("'", False, 1),
    MacrosDef("`", False, 1),
    MacrosDef('"', False, 1),
    MacrosDef("c", False, 1),
    MacrosDef("^", False, 1),
    MacrosDef("~", False, 1),
    MacrosDef("H", False, 1),
    MacrosDef("k", False, 1),
    MacrosDef("=", False, 1),
    MacrosDef("b", False, 1),
    MacrosDef(".", False, 1),
    MacrosDef("d", False, 1),
    MacrosDef("r", False, 1),
    MacrosDef("u", False, 1),
    MacrosDef("v", False, 1),

    MacrosDef("vec", False, 1),
    MacrosDef("dot", False, 1),
    MacrosDef("hat", False, 1),
    MacrosDef("check", False, 1),
    MacrosDef("breve", False, 1),
    MacrosDef("acute", False, 1),
    MacrosDef("grave", False, 1),
    MacrosDef("tilde", False, 1),
    MacrosDef("bar", False, 1),
    MacrosDef("ddot", False, 1),


    MacrosDef('frac', False, 2),
    MacrosDef('nicefrac', False, 2),

    MacrosDef('sqrt', True, 1),

    MacrosDef('ket', False, 1),
    MacrosDef('bra', False, 1),
    MacrosDef('braket', False, 2),
    MacrosDef('ketbra', False, 2),

    MacrosDef('texorpdfstring', False, 2),

    # ethuebung
    MacrosDef('UebungLoesungFont', False, 1),
    MacrosDef('UebungHinweisFont', False, 1),
    MacrosDef('UebungExTitleFont', False, 1),
    MacrosDef('UebungSubExTitleFont', False, 1),
    MacrosDef('UebungTipsFont', False, 1),
    MacrosDef('UebungLabel', False, 1),
    MacrosDef('UebungSubLabel', False, 1),
    MacrosDef('UebungLabelEnum', False, 1),
    MacrosDef('UebungLabelEnumSub', False, 1),
    MacrosDef('UebungSolLabel', False, 1),
    MacrosDef('UebungHinweisLabel', False, 1),
    MacrosDef('UebungHinweiseLabel', False, 1),
    MacrosDef('UebungSolEquationLabel', False, 1),
    MacrosDef('UebungTipsLabel', False, 1),
    MacrosDef('UebungTipsEquationLabel', False, 1),
    MacrosDef('UebungsblattTitleSeries', False, 1),
    MacrosDef('UebungsblattTitleSolutions', False, 1),
    MacrosDef('UebungsblattTitleTips', False, 1),
    MacrosDef('UebungsblattNumber', False, 1),
    MacrosDef('UebungsblattTitleFont', False, 1),
    MacrosDef('UebungTitleCenterVSpacing', False, 1),
    MacrosDef('UebungAttachedSolutionTitleTop', False, 1),
    MacrosDef('UebungAttachedSolutionTitleFont', False, 1),
    MacrosDef('UebungAttachedSolutionTitle', False, 1),
    MacrosDef('UebungTextAttachedSolution', False, 1),
    MacrosDef('UebungDueByLabel', False, 1),
    MacrosDef('UebungDueBy', False, 1),
    MacrosDef('UebungLecture', False, 1),
    MacrosDef('UebungProf', False, 1),
    MacrosDef('UebungLecturer', False, 1),
    MacrosDef('UebungSemester', False, 1),
    MacrosDef('UebungLogoFile', False, 1),
    MacrosDef('UebungLanguage', False, 1),
    MacrosDef('UebungStyle', False, 1),
    #
    MacrosDef('uebung', False, '{['),
    MacrosDef('exercise', False, '{['),
    MacrosDef('keywords', False, 1),
    MacrosDef('subuebung', False, 1),
    MacrosDef('subexercise', False, 1),
    MacrosDef('pdfloesung', True, 1),
    MacrosDef('pdfsolution', True, 1),
    MacrosDef('exenumfulllabel', False, 1),
    MacrosDef('hint', False, 1),
    MacrosDef('hints', False, 1),
    MacrosDef('hinweis', False, 1),
    MacrosDef('hinweise', False, 1),

    )

default_macro_dict = dict([(m.macname, m) for m in _default_macro_list])
"""
The default context dictionary of known LaTeX macros.  The keys are the macro names
(:py:class:`MacrosDef.macname <MacrosDef>`) and the values are :py:class:`MacrosDef`
instances.
"""


# ------------------------------------------------


class LatexToken(object):
    r"""
    Represents a token read from the LaTeX input.

    This is not the same thing as a LaTeX token, it's just a part of the input which we
    treat in the same way (e.g. a bunch of content characters, a comment, a macro, etc.)

    Information about the object is stored into the fields `tok` and `arg`. The `tok`
    field is a string which identifies the type of the token. The `arg` depends on what
    `tok` is, and describes the actual input.

    Additionally, this class stores information about the position of the token in the
    input stream in the field `pos`.  This `pos` is an integer which corresponds to the
    index in the input string.  The field `len` stores the length of the token in the
    input string.  This means that this token spans in the input string from `pos` to
    `pos+len`.

    Leading whitespace before the token is not returned as a separate 'char'-type token,
    but it is given in the `pre_space` field of the token which follows.  Pre-space may
    contain a newline, but not two consecutive newlines.

    The `tok` field may be one of:

      - 'char': raw characters which have no special LaTeX meaning; they are part of the
        text content.
        
        The `arg` field contains the characters themselves.

      - 'macro': a macro invokation, but not '\begin' or '\end'
        
        The `arg` field contains the name of the macro, without the leading backslash.

      - 'begin_environment': an invokation of '\begin{environment}'.
        
        The `arg` field contains the name of the environment inside the braces.

      - 'end_environment': an invokation of '\end{environment}'.
        
        The `arg` field contains the name of the environment inside the braces.

      - 'comment': a LaTeX comment delimited by a percent sign up to the end of the line.
        
        The `arg` field contains the text in the comment line, not including the percent
        sign nor the newline.

      - 'brace_open': an opening brace.  This is usually a curly brace, and sometimes also
        a square bracket.  What is parsed as a brace depends on the arguments to
        :py:func:`get_token()`.
        
        The `arg` is a string which contains the relevant brace character.
        
      - 'brace_close': a closing brace.  This is usually a curly brace, and sometimes also
        a square bracket.  What is parsed as a brace depends on the arguments to
        :py:func:`get_token()`.
        
        The `arg` is a string which contains the relevant brace character.

      - 'mathmode_inline': a delimiter which starts inline math.  This is (e.g.) a single
        '$' character which is not part of a double '$$' display environment delimiter.

        The `arg` is the string value of the delimiter in question ('$')
    """
    def __init__(self, tok, arg, pos, len, pre_space):
        self.tok = tok
        self.arg = arg
        self.pos = pos
        self.len = len
        self.pre_space = pre_space
        self._fields = ['tok', 'arg', 'pos', 'len', 'pre_space']
        super(LatexToken, self).__init__()


    def __unicode__(self):
        return self.__repr__()

    def __repr__(self):
        return (
            u"LatexToken(" +
            u", ".join([ u"%s=%r"%(k,getattr(self,k))
                        for k in self._fields ]) +
            u")"
            )

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def __eq__(self, other):
        return all( ( getattr(self, f) == getattr(other, f)  for f in self._fields ) )

# ------------------------------------------------




class LatexNode(object):
    """
    Represents an abstract 'node' of the latex document.

    Use :py:meth:`nodeType()` to figure out what type of node this is.
    """
    def __init__(self, **kwargs):
        """
        Important: subclasses must set `self._fields` to a list (or tuple or iterable) of the
        fields stored in this object.
        """
        super(LatexNode, self).__init__(**kwargs)

    def nodeType(self):
        """
        Returns the class which corresponds to the type of this node.  This is a Python class
        object, that is one of :py:class:`~pylatexenc.latexwalker.LatexCharsNode`,
        :py:class:`~pylatexenc.latexwalker.LatexGroupNode`, etc.
        """
        return LatexNode

    def isNodeType(self, t):
        """
        Returns `True` if the current node is of the given type.  The argument `t` must be a
        Python class such as, e.g. :py:class:`~pylatexenc.latexwalker.LatexGroupNode`.
        """
        return isinstance(self, t)

    def __eq__(self, other):
        return other is not None  and  self.nodeType() == other.nodeType()  and  all(
            ( getattr(self, f) == getattr(other, f)  for f in self._fields )
        )
    def __unicode__(self):
        return self.__repr__()
    def __str__(self):
        return self.__unicode__().encode('utf-8')
    def __repr__(self):
        return (
            self.nodeType().__name__ + u"(" +
            u", ".join([ u"%s=%r"%(k,getattr(self,k))  for k in self._fields ]) +
            u")"
            )


class LatexCharsNode(LatexNode):
    """
    A string of characters in the LaTeX document, without any special meaning.
    """
    def __init__(self, chars, **kwargs):
        r"""
        Arguments:
            - `chars`: the actual characters.
        """
        super(LatexCharsNode, self).__init__(**kwargs)
        self._fields = ('chars',)
        self.chars = chars

    def nodeType(self):
        return LatexCharsNode

class LatexGroupNode(LatexNode):
    r"""
    A LaTeX group, i.e. `{...}`.
    """
    def __init__(self, nodelist, **kwargs):
        """
        Arguments:
            - `nodelist`: a list of nodes which comprise the group.
        """
        super(LatexNode, self).__init__(**kwargs)
        self._fields = ('nodelist',)
        self.nodelist = nodelist

    def nodeType(self):
        return LatexGroupNode

class LatexCommentNode(LatexNode):
    """
    A LaTeX comment, delimited by a percent sign until the end of line.
    """
    def __init__(self, comment, **kwargs):
        super(LatexCommentNode, self).__init__(**kwargs)
        self._fields = ('comment',)
        self.comment = comment

    def nodeType(self):
        return LatexCommentNode

class LatexMacroNode(LatexNode):
    r"""
    Represents a 'macro' type node, e.g. '\textbf'
    """
    def __init__(self, macroname, nodeoptarg=None, nodeargs=[], **kwargs):
        r"""
        Represents a 'macro' type node, e.g. '\textbf'

        Arguments:
            - `macroname`: the name of the macro (string), *without* the leading
              backslash
            - `nodeoptarg`: if non-`None`, this corresponds to the optional argument
              of the macro
            - `nodeargs`: a list of arguments to the macro. Each item in the list
              should be a LatexNode.
        """
        super(LatexMacroNode, self).__init__(**kwargs)
        self._fields = ('macroname','nodeoptarg','nodeargs',)
        self.macroname = macroname
        self.nodeoptarg = nodeoptarg
        self.nodeargs = nodeargs

    def nodeType(self):
        return LatexMacroNode

class LatexEnvironmentNode(LatexNode):
    r"""
    A LaTeX Environment Node, i.e. `\begin{something} ... \end{something}`.

    Arguments:
        - `envname`: the name of the environment ('itemize', 'equation', ...)
        - `nodelist`: a list of :py:class:`LatexNode`'s that represent all the
          contents between the `\begin{...}` instruction and the `\end{...}`
          instruction.
        - `optargs`: any possible optional argument passed to the `\begin{...}`
          instruction, for example in `\begin{enumerate}[label=\roman*)]
          (Currently, only a single optional argument is parsed, but this argument
          still accepts anyway a list of :py:class:`LatexNode`'s.)
        - `args`: any possible regular arguments passed to the `\begin{...}`
          instruction, for example in `\begin{tabular}{clr}`. Currently, only a
          single regular argument is parsed at maximum, but this is anyway a
          list of :py:class:`LatexNode`'s.
    """
    
    def __init__(self, envname, nodelist, optargs=[], args=[], **kwargs):
        super(LatexEnvironmentNode, self).__init__(**kwargs)
        self._fields = ('envname','nodelist','optargs','args',)
        self.envname = envname
        self.nodelist = nodelist
        self.optargs = optargs
        self.args = args

    def nodeType(self):
        return LatexEnvironmentNode

class LatexMathNode(LatexNode):
    r"""
    A Math node type.

    Note that currently only 'inline' math environments are detected.

    Arguments:
        - `displaytype`: either 'inline' or 'display'
    """
    def __init__(self, displaytype, nodelist=[], **kwargs):
        super(LatexMathNode, self).__init__(**kwargs)
        self._fields = ('displaytype','nodelist',)
        self.displaytype = displaytype
        self.nodelist = nodelist

    def nodeType(self):
        return LatexMathNode


# ------------------------------------------------------------------------------


class _PushPropOverride(object):
    def __init__(self, obj, propname, new_value):
        super(_PushPropOverride, self).__init__()
        self.obj = obj
        self.propname = propname
        self.new_value = new_value


    def __enter__(self):
        if self.new_value is not None:
            self.initval = getattr(self.obj, self.propname)
            setattr(self.obj, self.propname, self.new_value)
        return self

    def __exit__(self, type, value, traceback):
        # clean-up
        if self.new_value is not None:
            setattr(self.obj, self.propname, self.initval)



# ------------------------------------------------------------------------------

class LatexWalker(object):
    r"""
    A parser which walks through an input stream, parsing it as LaTeX markup.

    Arguments:

      - `s`: the string to parse as LaTeX code

      - `macro_dict`: a context dictionary of known LaTeX macros.  By default, the default
        global macro dictionary `default_macro_dict` is used.  This should be a dictionary
        where the keys are macro names (see :py:class:`MacrosDef.macname <MacrosDef>`) and
        values are :py:class:`MacrosDef` instances.

    Additional keyword arguments are flags which influence the parsing.  Accepted flags are:

      - `keep_inline_math=True|False` If this option is set to `True`, then inline math is
        parsed and stored using :py:class:`LatexMathNode` instances.  Otherwise, inline
        math is not treated differently and is simply kept as text.

      - `tolerant_parsing=True|False` If set to `True`, then the parser generally ignores
        syntax errors rather than raising an exception.

      - `strict_braces=True|False` This option refers specifically to reading a
        encountering a closing brace when an expression is needed.  You generally won't
        need to specify this flag, use `tolerant_parsing` instead.
    """

    def __init__(self, s, macro_dict=None, **flags):
        self.s = s
        if macro_dict is not None:
            self.macro_dict = macro_dict
        else:
            self.macro_dict = default_macro_dict
        #
        # now parsing flags:
        #
        self.keep_inline_math = flags.pop('keep_inline_math', False)
        self.tolerant_parsing = flags.pop('tolerant_parsing', True)
        self.strict_braces = flags.pop('strict_braces', False)
        if flags:
            # any flags left which we haven't recognized
            logger.warning("LatexWalker(): Unknown flag(s) encountered: %r", flags.keys())

    def parse_flags(self):
        """
        The parse flags currently set on this object.  Returns a dictionary with keys
        'keep_inline_math', 'tolerant_parsing' and 'strict_braces'.
        """
        return {
            'keep_inline_math': self.keep_inline_math,
            'tolerant_parsing': self.tolerant_parsing,
            'strict_braces': self.strict_braces,
        }
        
    def get_token(self, pos, brackets_are_chars=True, environments=True, keep_inline_math=None):
        """
        Parse the token in the stream pointed to at position `pos`.

        Returns a :py:class:`LatexToken`. Raises :py:exc:`LatexWalkerEndOfStream` if end
        of stream reached.

        If `brackets_are_chars=False`, then square bracket characters count as
        'brace_open' and 'brace_close' token types (see :py:class:`LatexToken`); otherwise
        (the default) they are considered just like other normal characters.

        If `environments=False`, then '\\begin' and '\\end' tokens count as regular
        'macro' tokens (see :py:class:`LatexToken`); otherwise (the default) they are
        considered as the token types 'begin_environment' and 'end_environment'.

        If `keep_inline_math` is not `None`, then that value overrides that of
        `self.keep_inline_math` for the duration of this method call.
        """

        s = self.s # shorthand

        with _PushPropOverride(self, 'keep_inline_math', keep_inline_math):

            space = ''
            while (pos < len(s) and s[pos].isspace()):
                space += s[pos]
                pos += 1
                if (space.endswith('\n\n')):  # two \n's indicate new paragraph.
                    # pre-space is overkill here I think.
                    return LatexToken(tok='char', arg='\n\n', pos=pos-2, len=2, pre_space='')


            if (pos >= len(s)):
                raise LatexWalkerEndOfStream()

            if (s[pos] == '\\'):
                # escape sequence
                i = 2
                macro = s[pos+1] # next char is necessarily part of macro
                # following chars part of macro only if all are alphabetical
                if (s[pos+1].isalpha()):
                    while pos+i<len(s) and s[pos+i].isalpha():
                        macro += s[pos+i]
                        i += 1
                # possibly followed by a star
                if (pos+i<len(s) and s[pos+i] == '*'):
                    macro += '*'
                    i += 1

                # see if we have a begin/end environment
                if (environments and (macro == 'begin' or macro == 'end')):
                    # \begin{environment} or \end{environment}
                    envmatch = re.match(r'^\s*\{([\w*]+)\}', s[pos+i:])
                    if (envmatch is None):
                        raise LatexWalkerParseError(s=s, pos=pos,
                                                    msg="Bad \\%s macro: expected {environment}" %(macro))

                    return LatexToken(
                        tok=('begin_environment' if macro == 'begin' else  'end_environment'),
                        arg=envmatch.group(1),
                        pos=pos,
                        len=i+envmatch.end(), # !!envmatch.end() counts from pos+i
                        pre_space=space
                        )

                # # possibly eat one following whitespace
                # if (s[pos+i].isspace()):
                #     i += 1

                return LatexToken(tok='macro', arg=macro, pos=pos, len=i, pre_space=space)

            if (s[pos] == '%'):
                # latex comment
                m = re.search(r'(\n|\r|\n\r)\s*', s[pos:])
                mlen = None
                if (m is not None):
                    mlen = m.start() # relative to pos already
                else:
                    mlen = len(s)-pos# [  ==len(s[pos:])  ]
                return LatexToken(tok='comment', arg=s[pos+1:pos+mlen], pos=pos, len=mlen, pre_space=space)

            openbracechars = '{'
            closebracechars = '}'
            if (not brackets_are_chars):
                openbracechars += '['
                closebracechars += ']'

            if (s[pos] in openbracechars):
                return LatexToken(tok='brace_open', arg=s[pos], pos=pos, len=1, pre_space=space)

            if (s[pos] in closebracechars):
                return LatexToken(tok='brace_close', arg=s[pos], pos=pos, len=1, pre_space=space)

            # check if it is an inline math char, if we care about inline math.
            if (s[pos] == '$' and self.keep_inline_math):
                # check that we don't have double-$$, which would be a display environment.
                if not (pos+1 < len(s) and s[pos+1] == '$'):
                    return LatexToken(tok='mathmode_inline', arg=s[pos], pos=pos, len=1, pre_space=space)
                # otherwise, proceed to 'char' type.

            return LatexToken(tok='char', arg=s[pos], pos=pos, len=1, pre_space=space)


    def get_latex_expression(self, pos, strict_braces=None):
        """
        Reads a latex expression, e.g. macro argument. This may be a single char, an escape
        sequence, or a expression placed in braces.  This is what TeX calls a "token" (and
        not what we call a token... anyway).

        Returns a tuple `(<LatexNode instance>, pos, len)`. `pos` is the first char of the
        expression, and `len` is its length.
        """

        with _PushPropOverride(self, 'strict_braces', strict_braces):

            tok = self.get_token(pos, environments=False, keep_inline_math=False)

            if (tok.tok == 'macro'):
                if (tok.arg == 'end'):
                    if (not self.tolerant_parsing):
                        # error, this should be an \end{environment}, not an argument in itself
                        raise LatexWalkerParseError("Expected expression, got \end", self.s, pos)
                    else:
                        return (LatexCharsNode(chars=''), tok.pos, 0)
                return (LatexMacroNode(macroname=tok.arg, nodeoptarg=None, nodeargs=[]),
                        tok.pos, tok.len)
            if (tok.tok == 'comment'):
                return self.get_latex_expression(pos+tok.len)
            if (tok.tok == 'brace_open'):
                return self.get_latex_braced_group(tok.pos)
            if (tok.tok == 'brace_close'):
                if (self.strict_braces and not self.tolerant_parsing):
                    raise LatexWalkerParseError("Expected expression, got closing brace!", self.s, pos)
                return (LatexCharsNode(chars=''), tok.pos, 0)
            if (tok.tok == 'char'):
                return (LatexCharsNode(chars=tok.arg), tok.pos, tok.len)

            raise LatexWalkerParseError("Unknown token type: %s" %(tok.tok), self.s, pos)


    def get_latex_maybe_optional_arg(self, pos):
        """
        Attempts to parse an optional argument. Returns a tuple `(groupnode, pos, len)` if
        success, otherwise returns None.
        """

        tok = self.get_token(pos, brackets_are_chars=False, environments=False)
        if (tok.tok == 'brace_open' and tok.arg == '['):
            return self.get_latex_braced_group(pos, brace_type='[')

        return None


    def get_latex_braced_group(self, pos, brace_type='{'):
        """
        Reads a latex expression enclosed in braces ``{ ... }``. The first token of `s[pos:]`
        must be an opening brace.

        Returns a tuple `(node, pos, len)`, where `node` is a :py:class:`LatexGroupNode`
        instance, `pos` is the first char of the expression (which has to be an opening
        brace), and `len` is its length, including the closing brace.
        """

        closing_brace = None
        if (brace_type == '{'):
            closing_brace = '}'
        elif (brace_type == '['):
            closing_brace = ']'
        else:
            raise LatexWalkerParseError(s=self.s, pos=pos, msg="Uknown brace type: %s" %(brace_type))
        brackets_are_chars = (brace_type != '[')

        firsttok = self.get_token(pos, brackets_are_chars=brackets_are_chars)
        if (firsttok.tok != 'brace_open'  or  firsttok.arg != brace_type):
            raise LatexWalkerParseError(s=self.s, pos=pos,
                                        msg='get_latex_braced_group: not an opening brace/bracket: %s' %(self.s[pos]))

        #pos = firsttok.pos + firsttok.len

        (nodelist, npos, nlen) = self.get_latex_nodes(firsttok.pos + firsttok.len,
                                                      stop_upon_closing_brace=closing_brace)

        return (LatexGroupNode(nodelist=nodelist), firsttok.pos, npos + nlen - firsttok.pos)


    def get_latex_environment(self, pos, environmentname=None):
        """
        Reads a latex expression enclosed in a ``\\begin{environment}...\\end{environment}``.
        The first token in the stream must be the ``\\begin{environment}``.

        If `environmentname` is given and nonempty, then additionally a
        :py:exc:`LatexWalkerParseError` is raised if the environment in the input stream
        does not match the provided name.

        This function will attempt to heuristically parse an optional argument, and
        possibly a mandatory argument given to the environment.  No space is allowed
        between ``\begin{environment}`` and an opening square bracket or opening brace.

        Returns a tuple (node, pos, len) with node being a :py:class:`LatexEnvironmentNode`.
        """

        startpos = pos

        firsttok = self.get_token(pos)
        if (firsttok.tok != 'begin_environment'  or
            (environmentname is not None and firsttok.arg != environmentname)):
            raise LatexWalkerParseError(s=self.s, pos=pos,
                                        msg=r'get_latex_environment: expected \begin{%s}: %s' %(
                environmentname if environmentname is not None else '<environment name>',
                firsttok.arg
                ))
        if (environmentname is None):
            environmentname = firsttok.arg

        pos = firsttok.pos + firsttok.len


        optargs = []
        args = []

        # see if the \begin{environment} is immediately followed by some options.
        # BUG: Don't eat the brace of a commutator!! impose no space.
        optargtuple = None
        if (self.s[pos] == '['):
            optargtuple = self.get_latex_maybe_optional_arg(pos)

        if (optargtuple is not None):
            optargs.append(optargtuple[0])
            pos = optargtuple[1]+optargtuple[2]
        else:
            # try to see if we have a mandatory argument
            # don't use get_token as we don't want to skip any space.
            if self.s[pos] == '{':
                (argnode, apos, alen) = self.get_latex_braced_group(pos)
                args.append(argnode)
                pos = apos+alen

        (nodelist, npos, nlen) = self.get_latex_nodes(pos, stop_upon_end_environment=environmentname)

        return (LatexEnvironmentNode(envname=environmentname,
                                     nodelist=nodelist,
                                     optargs=optargs,
                                     args=args),
                startpos, npos+nlen-startpos)


    

    def get_latex_nodes(self, pos=0, stop_upon_closing_brace=None, stop_upon_end_environment=None,
                        stop_upon_closing_mathmode=None):
        """
        Parses latex content stored in `self.s` into a list of nodes.

        Returns a tuple `(nodelist, pos, len)` where nodelist is a list of
        :py:class:`LatexNode`\ 's.
        
        If `stop_upon_closing_brace` is given and set to a character, then parsing stops
        once the given closing brace is encountered (but not inside a subgroup).  The
        brace is given as a character, ']' or '}'.  The returned `len` includes the
        closing brace, but the closing brace is not included in any of the nodes in the
        `nodelist`.

        If `stop_upon_end_environment` is provided, then parsing stops once the given
        environment was closed.  If there is an environment mismatch, then a
        `LatexWalkerParseError` is raised except in tolerant parsing mode (see
        py:meth:`parse_flags()`).  Again, the closing environment is included in the
        length count but not the nodes.
        """

        nodelist = []
    
        brackets_are_chars = True
        if (stop_upon_closing_brace == ']'):
            brackets_are_chars = False

        origpos = pos

        class PosPointer:
            def __init__(self, pos=0, lastchars=''):
                self.pos = pos
                self.lastchars = lastchars

        p = PosPointer(pos)

        def do_read(nodelist, p):
            """
            Read a single token and process it, recursing into brace blocks and environments etc if
            needed, and appending stuff to nodelist.

            Return True whenever we should stop trying to read more. (e.g. upon reaching the a matched
            stop_upon_end_environment etc.)
            """

            try:
                tok = self.get_token(p.pos, brackets_are_chars=brackets_are_chars)
            except LatexWalkerEndOfStream:
                if self.tolerant_parsing:
                    return True
                raise # re-raise

            p.pos = tok.pos + tok.len

            # if it's a char, just append it to the stream of last characters.
            if (tok.tok == 'char'):
                p.lastchars += tok.pre_space + tok.arg
                return False

            # maybe add the pre_space of the new token to lastchars, if applicable.
            #if (len(tok.pre_space)):
            #    p.lastchars += tok.pre_space # yields wayyy tooo much space in output!!

            # if it's not a char, push the last `p.lastchars` into the node list before anything else
            if (len(p.lastchars)):
                strnode = LatexCharsNode(chars=p.lastchars+tok.pre_space)
                nodelist.append(strnode)
                p.lastchars = '' # reset lastchars.

            # and see what the token is.

            if (tok.tok == 'brace_close'):
                # we've reached the end of the group. stop the parsing.
                if (tok.arg != stop_upon_closing_brace):
                    if (not self.tolerant_parsing):
                        raise LatexWalkerParseError(s=self.s, pos=tok.pos,
                                                    msg='Unexpected mismatching closing brace: `%s\'' %(tok.arg))
                    return False
                return True

            if (tok.tok == 'end_environment'):
                # we've reached the end of an environment.
                if (tok.arg != stop_upon_end_environment):
                    if (not self.tolerant_parsing):
                        raise LatexWalkerParseError(s=self.s, pos=tok.pos,
                                                    msg=('Unexpected mismatching closing environment: `%s\', '
                                                         'expecting `%s\'' %(tok.arg, stop_upon_end_environment))
                                                    )
                    return False
                return True

            if (tok.tok == 'mathmode_inline'):
                # if we care about keeping math mode inlines verbatim, gulp all of the expression.
                if (stop_upon_closing_mathmode is not None):
                    if (stop_upon_closing_mathmode != '$'):
                        raise LatexWalkerParseError(s=self.s, pos=tok.pos,
                                                    msg='Unexpected mismatching closing math mode: `$\'')
                    return True

                # we have encountered a new math inline, so gulp all of the math expression
                (mathinline_nodelist, mpos, mlen) = self.get_latex_nodes(p.pos, stop_upon_closing_mathmode='$')
                p.pos = mpos + mlen

                nodelist.append(LatexMathNode(displaytype='inline', nodelist=mathinline_nodelist))
                return

            if (tok.tok == 'comment'):
                commentnode = LatexCommentNode(comment=tok.arg)
                nodelist.append(commentnode)
                return

            if (tok.tok == 'brace_open'):
                # another braced group to read.
                (groupnode, bpos, blen) = self.get_latex_braced_group(tok.pos)
                p.pos = bpos + blen
                nodelist.append(groupnode)
                return

            if (tok.tok == 'begin_environment'):
                # an environment to read.
                (envnode, epos, elen) = self.get_latex_environment(tok.pos, environmentname=tok.arg)
                p.pos = epos + elen
                # add node and continue.
                nodelist.append(envnode)
                return

            if (tok.tok == 'macro'):
                # read a macro. see if it has arguments.
                nodeoptarg = None
                nodeargs = []
                macname = tok.arg.rstrip('*')
                if (macname in self.macro_dict):
                    mac = self.macro_dict[macname]

                    def getoptarg(pos):
                        """Gets a possibly optional argument. returns (argnode, new-pos) where argnode might
                        be `None` if the argument was not specified."""
                        optarginfotuple = self.get_latex_maybe_optional_arg(pos)
                        if (optarginfotuple is not None):
                            (nodeoptarg, optargpos, optarglen) = optarginfotuple
                            return (nodeoptarg, optargpos+optarglen)
                        return (None, pos)

                    def getarg(pos):
                        """Gets a mandatory argument. returns (argnode, new-pos)"""
                        (nodearg, npos, nlen) = self.get_latex_expression(pos, strict_braces=False)
                        return (nodearg, npos + nlen)

                    if (mac.optarg):
                        (nodeoptarg, p.pos) = getoptarg(p.pos)

                    if (isinstance(mac.numargs, basestring)):
                        # specific argument specification
                        for arg in mac.numargs:
                            if (arg == '{'):
                                (node, p.pos) = getarg(p.pos)
                                nodeargs.append(node)
                            elif (arg == '['):
                                (node, p.pos) = getoptarg(p.pos)
                                nodeargs.append(node)
                            else:
                                raise LatexWalkerError("Unknown macro argument kind for macro %s: %s"
                                                       % (mac.macroname, arg))
                    else:
                        for n in range(mac.numargs):
                            (nodearg, p.pos) = getarg(p.pos)
                            nodeargs.append(nodearg)

                nodelist.append(LatexMacroNode(macroname=tok.arg,
                                               nodeoptarg=nodeoptarg,
                                               nodeargs=nodeargs))
                return None

            raise LatexWalkerParseError(s=self.s, pos=p.pos, msg="Unknown token: %r" %(tok))



        while True:
            try:
                r_endnow = do_read(nodelist, p)
            except LatexWalkerEndOfStream:
                if (stop_upon_closing_brace or stop_upon_end_environment):
                    # unexpected eof
                    if (not self.tolerant_parsing):
                        raise LatexWalkerError("Unexpected end of stream!")
                    else:
                        r_endnow = False
                else:
                    r_endnow = True

            if (r_endnow):
                # add last chars
                if (p.lastchars):
                    strnode = LatexCharsNode(chars=p.lastchars)
                    nodelist.append(strnode)
                return (nodelist, origpos, p.pos - origpos)

        raise LatexWalkerError("CONGRATULATIONS !! "
                               "You are the first human to telepathically break an infinite loop !!!!!!!")
































    
    
# ------------------------------------------------------------------------------

def get_token(s, pos, brackets_are_chars=True, environments=True, **parse_flags):
    """
    Parse the next token in the stream.

    Returns a `LatexToken`. Raises `LatexWalkerEndOfStream` if end of stream reached.

    .. deprecated:: 1.0
       Please use :py:meth:`LatexWalker.get_token()` instead.
    """
    return LatexWalker(s, **parse_flags).get_token(pos=pos,
                                                   brackets_are_chars=brackets_are_chars,
                                                   environments=environments)


def get_latex_expression(s, pos, **parse_flags):
    """
    Reads a latex expression, e.g. macro argument. This may be a single char, an escape
    sequence, or a expression placed in braces.

    Returns a tuple `(<LatexNode instance>, pos, len)`. `pos` is the first char of the
    expression, and `len` is its length.

    .. deprecated:: 1.0
       Please use :py:meth:`LatexWalker.get_latex_expression()` instead.
    """

    return LatexWalker(s, **parse_flags).get_latex_expression(pos=pos)


def get_latex_maybe_optional_arg(s, pos, **parse_flags):
    """
    Attempts to parse an optional argument. Returns a tuple `(groupnode, pos, len)` if
    success, otherwise returns None.

    .. deprecated:: 1.0
       Please use :py:meth:`LatexWalker.get_latex_maybe_optional_arg()` instead.
    """

    return LatexWalker(s, **parse_flags).get_latex_maybe_optional_arg(pos=pos)

    
def get_latex_braced_group(s, pos, brace_type='{', **parse_flags):
    """
    Reads a latex expression enclosed in braces {...}. The first token of `s[pos:]` must
    be an opening brace.

    Returns a tuple `(node, pos, len)`. `pos` is the first char of the
    expression (which has to be an opening brace), and `len` is its length,
    including the closing brace.

    .. deprecated:: 1.0
       Please use :py:meth:`LatexWalker.get_latex_braced_group()` instead.
    """

    return LatexWalker(s, **parse_flags).get_latex_braced_group(pos=pos, brace_type=brace_type)


def get_latex_environment(s, pos, environmentname=None, **parse_flags):
    """
    Reads a latex expression enclosed in a \\begin{environment}...\\end{environment}. The first
    token in the stream must be the \\begin{environment}.

    Returns a tuple (node, pos, len) with node being a :py:class:`LatexEnvironmentNode`.

    .. deprecated:: 1.0
       Please use :py:meth:`LatexWalker.get_latex_environment()` instead.
    """

    return LatexWalker(s, **parse_flags).get_latex_environment(pos=pos, environmentname=environmentname)

def get_latex_nodes(s, pos=0, stop_upon_closing_brace=None, stop_upon_end_environment=None,
                    stop_upon_closing_mathmode=None, **parse_flags):
    """
    Parses latex content `s`.

    Returns a tuple `(nodelist, pos, len)` where nodelist is a list of `LatexNode` 's.

    If `stop_upon_closing_brace` is given, then `len` includes the closing brace, but the
    closing brace is not included in any of the nodes in the `nodelist`.

    .. deprecated:: 1.0
       Please use :py:meth:`LatexWalker.get_latex_nodes()` instead.
    """

    return LatexWalker(s, **parse_flags).get_latex_nodes(stop_upon_closing_brace=stop_upon_closing_brace,
                                                         stop_upon_end_environment=stop_upon_end_environment,
                                                         stop_upon_closing_mathmode=stop_upon_closing_mathmode)










# ------------------------------------------------------------------------------

#
# small utilities for displaying & debugging
#


def put_in_braces(brace_char, thestring):
    if (brace_char == '{'):
        return '{%s}' %(thestring)
    if (brace_char == '['):
        return '[%s]' %(thestring)
    if (brace_char == '('):
        return '(%s)' %(thestring)
    if (brace_char == '<'):
        return '<%s>' %(thestring)

    return brace_char + thestring + brace_char


def nodelist_to_latex(nodelist):
    latex = ''
    for n in nodelist:
        if n is None:
            continue
        if n.isNodeType(LatexCharsNode):
            latex += n.chars
            continue
        if n.isNodeType(LatexMacroNode):
            latex += r'\%s' %(n.macroname)

            mac = None
            if (n.macroname in default_macro_dict):
                mac = default_macro_dict[n.macroname]
            
            if (n.nodeoptarg is not None):
                latex += '[%s]' %(nodelist_to_latex([n.nodeoptarg]))

            if mac is not None:
                macbraces = (mac.numargs if isinstance(mac.numargs, basestring) else '{'*mac.numargs)
            else:
                macbraces = '{'*len(n.nodeargs)
                
            i = 0
            if (len(n.nodeargs) != len(macbraces)):
                raise LatexWalkerError("Error: number of arguments (%d) provided to macro `\\%s' does not "
                                       "match its specification of `%s'"
                                       %(len(n.nodeargs), n.macroname, macbraces))
            for i in range(len(n.nodeargs)):
                nodearg = n.nodeargs[i]
                if nodearg is not None:
                    latex += put_in_braces(macbraces[i], nodelist_to_latex([nodearg]))

            continue
        
        if n.isNodeType(LatexCommentNode):
            latex += '%'+n.comment+'\n'
            continue
        
        if n.isNodeType(LatexGroupNode):
            latex += put_in_braces('{', nodelist_to_latex(n.nodelist))
            continue
        
        if n.isNodeType(LatexEnvironmentNode):
            latex += r'\begin{%s}' %(n.envname)
            for optarg in n.optargs:
                latex += put_in_braces('[', nodelist_to_latex([optarg]))
            for arg in n.args:
                latex += put_in_braces('{', nodelist_to_latex([arg]))
            latex += nodelist_to_latex(n.nodelist)
            latex += r'\end{%s}' %(n.envname)
            continue
        
        latex += '<[UNKNOWN LATEX NODE: `%s\']>' %(n.nodeType().__name__)

    return latex



def math_node_to_latex(node):

    if (not node.isNodeType(LatexMathNode)):
        raise LatexWalkerError("Expected math node, got `%s'" %(node.nodeType().__name__))

    if (node.displaytype == 'inline'):
        return '$%s$' %(nodelist_to_latex(node.nodelist))
    if (node.displaytype == 'display'):
        return r'\[%s\]' %(nodelist_to_latex(node.nodelist))

    raise LatexWalkerError("Unkonwn displaytype: `%s'" %(node.displaytype))



def disp_node(n, indent=0, context='* ', skip_group=False):
    title = ''
    comment = ''
    iterchildren = []
    if n is None:
        title = '<None>'
    elif n.isNodeType(LatexCharsNode):
        title = "'%s'" %(n.chars.strip())
    elif n.isNodeType(LatexMacroNode):
        title = '\\'+n.macroname
        #comment = 'opt arg?: %d; %d args' % (n.arg.nodeoptarg is not None, len(n.arg.nodeargs))
        if (n.nodeoptarg):
            iterchildren.append(('[...]: ', [n.nodeoptarg], False))
        if (len(n.nodeargs)):
            iterchildren.append(('{...}: ', n.nodeargs, False))
    elif n.isNodeType(LatexCommentNode):
        title = '%' + n.comment.strip()
    elif n.isNodeType(LatexGroupNode):
        if (skip_group):
            for nn in n.arg:
                disp_node(nn, indent=indent, context=context)
            return
        title = 'Group: '
        iterchildren.append(('* ', n.nodelist, False))

    elif n.isNodeType(LatexEnvironmentNode):
        title = '\\begin{%s}' %(n.envname)
        iterchildren.append(('* ', n.nodelist, False))
    else:
        print("UNKNOWN NODE TYPE: %s"%(n.nodeType().__name__))

    print(' '*indent + context + title + '  '+comment)

    for context, nodelist, skip in iterchildren:
        for nn in nodelist:
            disp_node(nn, indent=indent+4, context=context, skip_group=skip)




if __name__ == '__main__':


    try:

        #latex = '\\textit{hi there!} This is {\em an equation}: \\begin{equation}\n a + bi = 0\n\\end{equation}\n\nwhere $i$ is the imaginary unit.\n'
        #nodelist = get_latex_nodes_debug(latex)
        #print repr(nodelist)


        import fileinput

        latex = ''
        for line in fileinput.input():
            latex += line

        (nodes, pos, llen) = get_latex_nodes(latex)

        print('\n--- NODES ---\n')
        print(repr(nodes))
        print('\n-------------\n')

        print('\n--- NODES ---\n')
        for n in nodes:
            disp_node(n)
        print('\n-------------\n')

    except:
        import pdb
        import sys
        print("\nEXCEPTION: " + unicode(sys.exc_info()[1]) + "\n")
        pdb.post_mortem()

