# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2022 Philippe Faist
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

#from ._parsedargs import ParsedArguments


# for Py3
_unicode_from_str = lambda x: x

### BEGIN_PYTHON2_SUPPORT_CODE
import sys
if sys.version_info.major == 2:
    _unicode_from_str = lambda x: x.decode('utf-8')
### END_PYTHON2_SUPPORT_CODE



class LatexToken(object):
    r"""
    Represents a token read from the LaTeX input.  Instances of this class are
    return by token readers such as :py:class:`LatexTokenReader`.

    This is not the same thing as a LaTeX token, it's just a part of the input
    which we treat in the same way (e.g. a text character, a comment, a macro,
    etc.)

    Information about the object is stored into the fields `tok` and `arg`. The
    `tok` field is a string which identifies the type of the token. The `arg`
    depends on what `tok` is, and describes the actual input.

    Additionally, this class stores information about the position of the token
    in the input stream in the field `pos`.  This `pos` is an integer which
    corresponds to the index in the input string.  The field `pos_end` stores
    the position immediately past the token in the input string.  This means
    that the string length spanned by this token is `pos_end - pos` (without
    leading whitespace).

    Leading whitespace before the token is not returned as a separate
    'char'-type token, but it is given in the `pre_space` field of the token
    which follows.  Pre-space may contain a newline, but not two consecutive
    newlines.  The `pos` position is the position of the first character of the
    token itself, which immediately follows any leading whitespace.

    The `post_space` is only used for 'macro' and 'comment' tokens, and it
    stores any spaces encountered after a macro, or the newline with any
    following spaces that terminates a LaTeX comment.  When we encounter two
    consecutive newlines these are not included in `post_space`.  Contrary to
    `pre_space`, the `post_space` is accounted for in the attribute `pos_end`,
    i.e., `pos_end` points immediately after any trailing whitespace.

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
        :py:class:`~pylatexenc.macrospec.SpecialsSpec` instance.

        The rationale for setting `arg` to a `SpecialsSpec` instance, in
        contrast to the behavior for macros and envrionments, is that macros and
        environments are delimited directly by LaTeX syntax and are determined
        unambiguously without any lookup in the latex context database.  This is
        not the case for specials, where successfully parsing a specials already
        requires a lookup in the context database, and so the spec object is
        readily available.

    .. versionchanged:: 3.0

       Starting in `pylatexenc 3`, the `len` argument was replaced by `pos_end`.
       For backwards compatibility, `kwargs` arguments are inspected for a `len`
       argument.  If a `len` argument is provided and `pos_end` was left `None`,
       then `pos_end` is set to `pos+len`.

    .. versionadded:: 3.0

       This class was moved to :py:class:`pylatexenc.latexnodes.LatexToken`
       starting in `pylatexenc 3.0`.  In earlier versions, this class was
       located in the :py:mod:`~pylatexenc.latexwalker` module, see
       :py:class:`~pylatexenc.latexwalker.LatexToken`.
    """
    def __init__(self, tok, arg, pos, pos_end=None, pre_space='', post_space='', **kwargs):

        len_ = kwargs.pop('len', None)

        self.tok = tok
        self.arg = arg
        self.pos = pos
        self.pos_end = pos_end
        self.pre_space = pre_space
        self.post_space = post_space
        
        if pos_end is None and len_ is not None and pos is not None:
            self.pos_end = pos + len_
            
        if kwargs:
            raise ValueError("Unexpected arguments to LatexToken(): " + repr(kwargs))

        self._fields = ['tok', 'arg', 'pos', 'pos_end', 'pre_space']
        if self.tok in ('macro', 'comment'):
            self._fields.append('post_space')
        super(LatexToken, self).__init__()

    @property
    def len(self):
        if self.pos is None or self.pos_end is None:
            return None
        return self.pos_end - self.pos

    def __unicode__(self):
        return _unicode_from_str(self.__str__())

    def __repr__(self):
        return (
            "LatexToken(" +
            ", ".join([ "{}={!r}".format(k,getattr(self,k))
                        for k in self._fields ]) +
            ")"
            )

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return all(
            (
                ( (getattr(self, f) is None and getattr(other, f) is None)
                  or getattr(self, f) == getattr(other, f) )
                for f in self._fields
            )
        )

    #__pragma__('skip')
    # see https://docs.python.org/3/library/constants.html#NotImplemented
    def __ne__(self, other): return NotImplemented
    #__pragma__('noskip')

    __hash__ = None

