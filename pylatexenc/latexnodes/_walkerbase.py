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
        r"""
        Called when the parser enters math mode.  Return the parsing state delta
        (see :py:class:`ParsingStateDelta`) that should be applied to the
        parsing state for the math mode contents.

        The `math_mode_delimiter` is the delimiter string that opened math mode,
        and `trigger_token` is the corresponding token instance (either can be
        `None`, e.g. if math mode was entered because of an environment such as
        ``\begin{align}``).

        The default implementation returns a delta that sets the parsing state
        fields `in_math_mode=True` and
        `math_mode_delimiter=math_mode_delimiter`.  Reimplement this method if
        entering math mode should cause further changes to the parsing state,
        e.g., if a different set of macro definitions applies in math mode.
        """
        return ParsingStateDelta(
            set_attributes=dict(
                in_math_mode=True,
                math_mode_delimiter=math_mode_delimiter
            )
        )

    def leave_math_mode(self, trigger_token=None):
        r"""
        Called when the parser leaves math mode.  Return the parsing state delta
        (see :py:class:`ParsingStateDelta`) that should be applied to the
        parsing state for the text mode contents that follow.

        The `trigger_token` is the token instance that caused math mode to be
        left, if applicable, and `None` otherwise.

        The default implementation returns a delta that sets the parsing state
        fields `in_math_mode=False` and `math_mode_delimiter=None`.  See also
        :py:meth:`enter_math_mode()`.
        """
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

    See also :py:class:`pylatexenc.latexwalker.LatexWalker`.

    .. versionadded:: 3.0
    
       The :py:class:`LatexWalkerBase` class was added in `pylatexenc 3.0`.
    """

    def parsing_state_event_handler(self):
        r"""
        Return the parsing state event handler associated with this latex walker.

        The returned object is queried whenever a parsing state delta of type
        :py:class:`ParsingStateDeltaWalkerEvent` (e.g.,
        :py:class:`ParsingStateDeltaEnterMathMode`) needs to be resolved into
        actual parsing state changes.

        The default implementation returns a shared, default instance of
        :py:class:`LatexWalkerParsingStateEventHandler`.  Reimplement this
        method to return your own handler instance if you'd like to customize
        how the parsing state changes upon such events.
        """
        return _default_parsing_state_event_handler

    def parse_content(self, parser, token_reader=None, parsing_state=None,
                      open_context=None, **kwargs):
        r"""
        Run the given `parser` on the latex code represented by this latex walker,
        and return its result.

        Arguments:

        - `parser` is a callable object (see
          :py:mod:`pylatexenc.latexnodes.parsers`) that will be invoked with the
          keyword arguments `latex_walker`, `token_reader` and `parsing_state`.

        - `token_reader` is the token reader to read tokens from.  If `None`,
          the subclass is expected to provide a suitable token reader for the
          latex code it is walking through.

        - `parsing_state` is the :py:class:`ParsingState` instance to parse the
          content with.  If `None`, the subclass is expected to provide a
          suitable default parsing state.

        - `open_context`, if non-`None`, is a tuple `(open_context_name,
          open_context_token)` describing the construct that is being parsed
          (e.g. ``r"Argument of \mymacro"``) along with the token that
          introduced it.  This information is used to provide more helpful error
          messages.

        Return a tuple `(result, parsing_state_delta)`, where `result` is
        whatever the parser returned (typically a :py:class:`LatexNode` or a
        :py:class:`LatexNodeList` instance) and where `parsing_state_delta`, if
        non-`None`, is a :py:class:`ParsingStateDelta` instance describing how
        the parsing state should change for the content that follows.

        This method is expected to catch parse errors and to attempt recovery
        from them if the latex walker is operating in tolerant parsing mode.

        Subclasses must reimplement this method.  See
        :py:meth:`pylatexenc.latexwalker.LatexWalker.parse_content()` for the
        reference implementation.
        """
        raise RuntimeError("LatexWalkerBase subclasses must reimplement parse_content()")

    def make_node(self, node_class, **kwargs):
        r"""
        Create and return an instance of the node class `node_class` (a
        :py:class:`LatexNode` subclass), with the given keyword arguments passed
        on to the node constructor.

        Callers always provide at least the keyword arguments `pos`, `pos_end`
        and `parsing_state`.  Implementations are expected to also set the
        node's `latex_walker` attribute to this latex walker instance.

        All node instances created while parsing are created with this method,
        so reimplementing it in a subclass is a convenient way of customizing
        the node objects (e.g. to attach additional information to them).

        Subclasses must reimplement this method.
        """
        raise RuntimeError("LatexWalkerBase subclasses must reimplement make_node()")

    def make_nodelist(self, nodelist, **kwargs):
        r"""
        Create and return a :py:class:`LatexNodeList` instance that contains the
        nodes in the list `nodelist`.  Additional keyword arguments are passed
        on to the node list constructor; callers always provide at least the
        keyword argument `parsing_state`.

        As with :py:meth:`make_node()`, implementations are expected to set the
        node list's `latex_walker` attribute to this latex walker instance, and
        reimplementing this method is a convenient way of customizing the node
        list objects that are created while parsing.

        Subclasses must reimplement this method.
        """
        raise RuntimeError("LatexWalkerBase subclasses must reimplement make_nodelist()")

    def make_nodes_collector(self,
                             token_reader,
                             parsing_state,
                             **kwargs):
        r"""
        Create and return a :py:class:`LatexNodesCollector` instance that reads
        tokens from `token_reader` with the parsing state `parsing_state`.  Any
        further keyword arguments are passed on to the nodes collector
        constructor.

        Reimplement this method in a subclass if you'd like the parsers to use a
        custom subclass of :py:class:`LatexNodesCollector`.

        Subclasses must reimplement this method.
        """
        raise RuntimeError(
            "LatexWalkerBase subclasses must reimplement make_nodes_collector()")

    def make_latex_group_parser(self, delimiters):
        r"""
        Create and return a parser instance that will parse a LaTeX group (e.g.
        ``{...}``) delimited by the given `delimiters`.

        The `delimiters` argument is what will be given to the parser's
        `delimiters=` argument; see
        :py:class:`pylatexenc.latexnodes.parsers.LatexDelimitedGroupParser`.

        This method is used by :py:class:`LatexNodesCollector` when it
        encounters a group opening token.  Reimplement it in a subclass if you'd
        like groups to be parsed by a custom parser class.

        Subclasses must reimplement this method.
        """
        raise RuntimeError(
            "LatexWalkerBase subclasses must reimplement make_latex_group_parser()")

    def make_latex_math_parser(self, math_mode_delimiters):
        r"""
        Create and return a parser instance that will parse a math mode block (e.g.
        ``$...$``) delimited by the given `math_mode_delimiters`.

        The `math_mode_delimiters` argument is what will be given to the
        parser's `math_mode_delimiters=` argument; see
        :py:class:`pylatexenc.latexnodes.parsers.LatexMathParser`.

        This method is used by :py:class:`LatexNodesCollector` when it
        encounters a math mode opening token.  Reimplement it in a subclass if
        you'd like math mode to be parsed by a custom parser class.

        Subclasses must reimplement this method.
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
        Return a human-readable string that describes where the given `node` is
        located in the latex code, for use in error and warning messages.

        The default implementation reports the node's `pos` attribute as a
        character offset.  Reimplement this method if you can provide a more
        helpful description, e.g., a line and column number (see
        :py:meth:`pylatexenc.latexwalker.LatexWalker.pos_to_lineno_colno()`) or
        the name of the file the code was read from.
        """
        return 'character position '+repr(node.pos)
