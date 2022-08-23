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





# ------------------------------------------------------------------------------

class LatexParserBase(object):
    r"""
    The base class for :py:mod:`pylatexenc.latexnodes.parsers` parsers.

    Parsers are objects that are designed to parse a specific type of latex
    construct, such as content enclosed in curly braces, into a node tree.

    When invoked, parse objects return a tuple `(nodes, parsing_state_delta)`.
    The first element, `nodes`, is the result nodes.  It is usually a
    :py:class:`~pylatexenc.latexnodes.LatexNodeList` instance, but it can also
    be a specific node instance, or another related object like a
    :py:class:`~pylatexenc.latexnodes.ParsedArguments` instance.  The second
    element, `parsing_state_delta`, encode any changes in the parsing state that
    should be caused by parsing the given construct.  The `parsing_state_delta`
    should be either `None` (no parsing state changes) or a
    :py:class:`~pylatexenc.latexnodes.ParsingStateDelta` instance.  For
    instance, if the parser encountered a ``\newcommand`` it can relay the
    corresponding state change through the `parsing_state_delta` object.

    The main functionality of the parser is implemented in the
    :py:meth:`parse()` method.

    Parser objects should be invoked via the latex walker instance, using
    `LatexWalker.parse_content()` (see :py:class:`LatexWalkerBase` and
    :py:class:`pylatexenc.latexwalker.LatexWalker`):

    .. code::

       my_latex_walker = LatexWalker(....)
       my_parser = .... # some LatexParserBase subclass

       token_reader = my_latex_walker.make_token_reader()
       parsing_state = my_latex_walker.make_parsing_state()
    
       # parse that specific construct:
       nodes, parsing_state_delta = my_latex_walker.parse_content(
           my_parser,
           token_reader,
           parsing_state
       )
    """
    def __init__(self):
        super(LatexParserBase, self).__init__()

    def parse(self, latex_walker, token_reader, parsing_state, **kwargs):
        r"""
        The main functionality of the parser is implemented in this method.

        Parser objects should not be called directly, but rather be invoked via
        the latex walker instance, using `LatexWalker.parse_content()`.  (See
        class doc above.)

        Subclasses should implement this method to construct the relevant node
        tree by reading tokens from the `token_reader` (use
        `token_reader.next_token()` and friends, see
        :py:class:`~pylatexenc.latexnodes.LatexTokenReaderBase`)

        Subclasses should return a tuple pair `(nodes, parsing_state_delta)`.

        The `nodes` is the node list, node, or object that resulted from the
        parsing.

        The `parsing_state_delta` encodes any parsing state changes that
        resulted during the parsing of this construct.  If there are no parsing
        state changes, `parsing_state_delta` can be set to `None`.
        """
        raise RuntimeError("LatexParserBase subclasses must reimplement parse()")


    def contents_can_be_empty(self):
        r"""
        If absorbing no tokens is a valid option for the thing this object is meant
        to parse, then we should return `True` here.  This would be the case,
        for instance, for group contents, for optional arguments, etc.  But a
        parser for a mandatory argument would return `False` here.

        This is used in certain special situations, for instance if a closing
        brace is immediately encountered after a macro that expected an argument
        (say ``\mymacro}`` --- it's an error if ``\mymacro`` requires a
        mandatory argument but it's ok if it accepts an optional argument).  In
        this case, we need to check all the macro arguments' parser to see if it
        is okay that they have no contents.
        """
        return True


    def __repr__(self):
        return "<{}>".format(self.__class__.__name__)
