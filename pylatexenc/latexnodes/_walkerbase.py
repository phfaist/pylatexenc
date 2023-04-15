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

from ._parsingstatedelta import ParsingStateDelta



class LatexWalkerParsingStateEventHandler(object):
    r"""
    A LatexWalker parsing state event handler.

    The LatexWalker instance will call methods on this object to determine how
    to update the parsing state upon certain events, such as entering or exiting
    math mode.

    Events:

    - enter math mode

    - exit math mode

    .. versionadded:: 3.0
    
       The :py:class:`LatexWalkerParsingStateEventHandler` class was added in
       `pylatexenc 3.0`.
    """

    def enter_math_mode(self, math_mode_delimiter=None, trigger_token=None):
        return ParsingStateDelta(
            set_attributes=dict(
                in_math_mode=True,
                math_mode_delimiter=math_mode_delimiter
            )
        )

    def leave_math_mode(self, trigger_token=None):
        return ParsingStateDelta(
            set_attributes=dict(
                in_math_mode=False,
                math_mode_delimiter=None
            )
        )


_default_parsing_state_event_handler = LatexWalkerParsingStateEventHandler()


class LatexWalkerBase(object):
    r"""
    Base class for a latex-walker.  Essentially, this is all that the
    classes and methods in the :py:mod:`latexnodes` module need to know about
    what a LatexWalker does.

    See also :py:class:`latexwalker.LatexWalker`.

    .. versionadded:: 3.0
    
       The :py:class:`LatexWalkerBase` class was added in `pylatexenc 3.0`.
    """

    def parsing_state_event_handler(self):
        r"""
        Doc......
        """
        return _default_parsing_state_event_handler

    def parse_content(self, parser, token_reader=None, parsing_state=None,
                      open_context=None, **kwargs):
        r"""
        Doc......
        """
        raise RuntimeError("LatexWalkerBase subclasses must reimplement parse_content()")

    def make_node(self, node_class, **kwargs):
        r"""
        Doc......
        """
        raise RuntimeError("LatexWalkerBase subclasses must reimplement make_node()")

    def make_nodelist(self, nodelist, **kwargs):
        r"""
        Doc......
        """
        raise RuntimeError("LatexWalkerBase subclasses must reimplement make_nodelist()")

    def make_nodes_collector(self,
                             token_reader,
                             parsing_state,
                             **kwargs):
        r"""
        Doc......
        """
        raise RuntimeError(
            "LatexWalkerBase subclasses must reimplement make_nodes_collector()")

    def make_latex_group_parser(self, delimiters):
        r"""
        Doc......
        """
        raise RuntimeError(
            "LatexWalkerBase subclasses must reimplement make_latex_group_parser()")
        
    def make_latex_math_parser(self, math_mode_delimiters):
        r"""
        Doc......
        """
        raise RuntimeError(
            "LatexWalkerBase subclasses must reimplement make_latex_math_parser()")


    def check_tolerant_parsing_ignore_error(self, exc):
        r"""
        You can inspect the exception object `exc` and decide whether or not to
        attempt to recover from the exception (if you want to be tolerant to
        parsing errors).

        Return the exception object if it should be raised, or return None if
        recovery should be attempted.
        """
        return exc

    def format_node_pos(self, node):
        r"""
        Doc......
        """
        return 'character position '+repr(node.pos)
