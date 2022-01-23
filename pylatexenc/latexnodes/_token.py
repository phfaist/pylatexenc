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

from ._parsedargsbase import ParsedMacroArgs


# for Py3
_unicode_from_str = lambda x: x

## Begin Py2 support code
import sys
if sys.version_info.major == 2:
    # Py2
    _unicode_from_str = lambda x: x.decode('utf-8')
## End Py2 support code



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
    which we treat in the same way (e.g. a text character, a comment, a macro,
    etc.)

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
    newlines.  The `pos` position is the position of the first character of the
    token itself, which immediately follows any leading whitespace.  Similarly,
    the `len` attribute does not include the leading whitespace's length,
    meaning that `pos+len` points to the character immediately after the present
    token.

    The `post_space` is only used for 'macro' and 'comment' tokens, and it
    stores any spaces encountered after a macro, or the newline with any
    following spaces that terminates a LaTeX comment.  When we encounter two
    consecutive newlines these are not included in `post_space`.  Contrary to
    `pre_space`, the length of the `post_space` is included in the attribute
    `len`.

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

