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

import logging
logger = logging.getLogger(__name__)


# for Py3
_basestring = str
_unicode_from_str = lambda x: x
to_str = str

### BEGIN_PYTHON2_SUPPORT_CODE
import sys
if sys.version_info.major == 2:
    # Py2
    _basestring = basestring
    _unicode_from_str = lambda x: x.decode('utf-8')
    to_str = unicode
### END_PYTHON2_SUPPORT_CODE



# we'll be using "from _types import *" for convenience, so to avoid polluting
# the other modules' namespaces, we define __all__ here.


__all__ = [
    'LatexWalkerError',
    'LatexWalkerLocatedError',
    'LatexWalkerParseError',
    'LatexWalkerLocatedErrorFormatter',
    'LatexWalkerNodesParseError',
    'LatexWalkerTokenParseError',
    'LatexWalkerEndOfStream',
]



class LatexWalkerError(Exception):
    r"""
    Generic exception class raised while parsing LaTeX code.  Common subclass 
    to `LatexWalkerLocatedError` as well as `LatexWalkerEndOfStream`.
    """
    pass


class LatexWalkerLocatedError(LatexWalkerError):
    r"""
    Exception class raised to the user when there was an error dealing with
    LaTeX code.  The exception is accompanied by information about where the
    error occurred in the source LaTeX code.

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
       at 0.

    .. py:attribute:: input_source

       The name of the source (e.g. file name) from which the LaTeX code was
       obtained. (Optional.)

    .. py:attribute:: error_type_info

       Specify additional information about the error so that specific
       applications can interpret the error and provide more meaningful messages
       to the user.  For instance, the message "Character is forbidden: '%'"
       might be cryptic to a user, whereas an application might be able to parse
       the `error_type_info` to see that the error is of the type of a forbidden
       character, and issue a message like "LaTeX comments are not permitted
       ('%' char forbidden), use '\\%' for a literal percent sign."

       The `error_type_info` attribute is a dictionary with at least one key
       named `what`.  The `what` key should reflect the type of error that
       occurred, e.g., `token_forbidden_character`.  Other keys might give
       additional information about the error (e.g., which character was
       encountered and was forbidden).
    """
    def __init__(self, msg, s=None, pos=None, lineno=None, colno=None,
                 error_type_info=None, **kwargs):
        self.input_source = kwargs.pop('input_source', None)
        self.msg = msg
        self.s = s
        self.pos = pos
        self.lineno = lineno
        self.colno = colno
        self.error_type_info = error_type_info
        self.open_contexts = kwargs.pop('open_contexts', [])

        if len(kwargs):
            raise ValueError("Unexpected keyword argument(s) to LatexWalkerLocatedError(): "
                             + repr(kwargs))

        super(LatexWalkerLocatedError, self).__init__(
            LatexWalkerLocatedErrorFormatter(self).to_display_string()
        )

    def __str__(self):
        return LatexWalkerLocatedErrorFormatter(self).to_display_string()

    def set_pos_or_add_open_context_from_node(self, node, what=None):
        if node is None:
            return

        pos = node.pos

        if hasattr(node, 'latex_walker') and node.latex_walker \
           and hasattr(node.latex_walker, 'pos_to_lineno_colno'):
            lineno, colno = node.latex_walker.pos_to_lineno_colno(pos)
        else:
            lineno, colno = None, None

        if what is None:
            what = node.display_str()

        if self.pos is None:
            self.pos = pos
            self.lineno = lineno
            self.colno = colno
            return

        if self.open_contexts is None:
            self.open_contexts = []
        self.open_contexts.append(
            (what, pos, lineno, colno)
        )

    #
    # ### Problem: other_exception might have properties (e.g., from a
    # ### token-walker-parse-error) that are incompatible with the Cls class
    # ### (e.g. nodes-walker-parse-error)
    #
    # @classmethod
    # def new_from(Cls, other_exception, **kwargs):
    #     r"""
    #     Construct the exception from the properties in `other_exception`, which
    #     should also be of :py:class:`LatexWalkerParseError` type or subclass,
    #     with the additional attributes set via `kwargs`.  You can call this
    #     static method on subclasses, too, to construct subclass instances.
    #     """
    #     logger.debug("new_from(): Cls=%r, other_exception=%r, kwargs=%r",
    #                  Cls, other_exception, kwargs)
    #     d = dict([(k, v) for
    #               (k, v) in other_exception.__dict__.items()
    #               if not k.startswith('_')])
    #     d.update(kwargs)
    #     return Cls(**d)


class LatexWalkerParseError(LatexWalkerLocatedError):
    r"""
    Represents an error while LaTeX code, specifically while parsing the
    code into the nodes structure.
    """
    pass



class LatexWalkerLocatedErrorFormatter(object):
    r"""
    Format the 
    """

    def __init__(self, exc):
        super(LatexWalkerLocatedErrorFormatter, self).__init__()
        self.exc = exc
        
    def format_open_blocks(self):
        exc = self.exc
        if not exc.open_contexts:
            return None
        disp = ''
        for context in reversed(exc.open_contexts):
            what, pos, lineno, colno = context
            disp += '{empty:4}{loc:<18}  {what}\n'.format(
                empty='',
                loc=format_pos(pos,lineno,colno),
                what=what
            )
        return disp

    def format_pos(self):
        return format_pos(self.exc.pos, self.exc.lineno, self.exc.colno)

    def format_full_traceback(self):
        exc = self.exc
        msg = ''

        if exc.input_source:
            msg += '  in {}'.format(exc.input_source)

        msg += " {}".format(self.format_pos())

        if exc.open_contexts:
            msg += '\nOpen LaTeX blocks:\n'
            msg += self.format_open_blocks()

        return msg

    def to_display_string(self):
        exc = self.exc

        msg = to_str(exc.msg)
        msg += self.format_full_traceback()

        return msg


def format_pos(pos, lineno, colno):
    if lineno is not None:
        if colno is not None:
            return '@ (line {}, col {})'.format(lineno, colno)
        return '@ line {}'.format(lineno)
    if pos is not None:
        return '@ char pos {}'.format(pos)
    return '@ <unknown>'




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

    .. py:attribute:: recovery_parsing_state_delta

       Parsing state delta to use as if the parser call had returned
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
                 recovery_parsing_state_delta=None,
                 recovery_at_token=None,
                 recovery_past_token=None,
                 **kwargs):
        super(LatexWalkerNodesParseError, self).__init__(**kwargs)
        self.recovery_nodes = recovery_nodes
        self.recovery_parsing_state_delta = recovery_parsing_state_delta
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

