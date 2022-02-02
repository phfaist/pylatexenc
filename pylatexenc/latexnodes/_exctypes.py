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



# we'll be using "from _types import *" for convenience, so to avoid polluting
# the other modules' namespaces, we define __all__ here.


__all__ = [
    'LatexWalkerError',
    'LatexWalkerParseError',
    'LatexWalkerNodesParseError',
    'LatexWalkerTokenParseError',
    'LatexWalkerEndOfStream',
]



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
        if pos is not None:
            return '@ char %d'%(pos)
        return '@ <unknown>'

    def __str__(self):
        return self._dispstr()


class LatexWalkerTokenParseError(LatexWalkerParseError):
    """
    Represents an error while parsing a single token of LaTeX code.  See
    :py:class:`LatexTokenReader`.

    In addition to the attributes inherited by
    :py:class:`LatexWalkerParseError`, we have:

    .. py:attribute:: recovery_token_placeholder

       A :py:class:`LatexToken` instance to use in place of a token that we
       tried, but failed, to parse.

    .. py:attribute:: recovery_token_at_pos

       The position at which to reset the token_reader's internal state to
       attempt to recover from this error.


    .. versionadded:: 3.0

       The :py:class:`LatexWalkerTokenParseError` class was introduced in
       `pylatexenc 3`.
    """
    def __init__(self, recovery_token_placeholder, recovery_token_at_pos, **kwargs):
        super(LatexWalkerTokenParseError, self).__init__(**kwargs)
        self.recovery_token_placeholder = recovery_token_placeholder
        self.recovery_token_at_pos = recovery_token_at_pos


class LatexWalkerNodesParseError(LatexWalkerParseError):
    """
    Represents an error while parsing content nodes, typically as a consequence
    of LatexWalker.parse_content().  This class carries some additional
    information about how best to recover from this parse error if we are
    operating in tolerant parsing mode.  E.g., we can already report a list of
    nodes parsed so far.

    In addition to the attributes inherited by
    :py:class:`LatexWalkerParseError`, we have:

    .. py:attribute:: recovery_nodes

       Nodes result (a :py:class:`LatexNode` or :py:class:`LatexNodeList`
       instance) to use as if the parser call had returned successfully.

    .. py:attribute:: recovery_carryoverinfo

       Carry-over `info` dictionary to use as if the parser call had returned
       successfully.

    .. py:attribute:: recovery_at_token

       If non-`None`, then we should reset the token reader's internal position
       to try to continue parsing at the given token's position.

    .. py:attribute:: recovery_past_token

       If non-`None`, then we should reset the token reader's internal position
       to try to continue parsing immediately after the given token's position.

       This attribute is not to be set if `recovery_at_token` is already
       non-`None`.


    .. versionadded:: 3.0

       The :py:class:`LatexWalkerNodesParseError` class was introduced in
       `pylatexenc 3`.
    """
    def __init__(self,
                 recovery_nodes=None,
                 recovery_carryoverinfo=None,
                 recovery_at_token=None,
                 recovery_past_token=None,
                 **kwargs):
        super(LatexWalkerNodesParseError, self).__init__(**kwargs)
        self.recovery_nodes = recovery_nodes
        self.recovery_carryoverinfo = recovery_carryoverinfo
        self.recovery_at_token = recovery_at_token
        self.recovery_past_token = recovery_past_token




class LatexWalkerEndOfStream(LatexWalkerError):
    """
    We reached end of the input string.

    .. py:attribute:: final_space

       Any trailing space at the end of the input string that might need to be
       included in a character node.

       .. versionadded:: 2.0

          The attribute `final_space` was added in `pylatexenc 2`.
    """
    def __init__(self, final_space=''):
        super(LatexWalkerEndOfStream, self).__init__()
        self.final_space = final_space



# ------------------------------------------------------------------------------

