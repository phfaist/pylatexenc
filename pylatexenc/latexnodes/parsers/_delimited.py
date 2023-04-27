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

import logging
logger = logging.getLogger(__name__)

from .._exctypes import *
from .. import nodes
from .._parsingstatedelta import get_updated_parsing_state_from_delta

from ._base import LatexParserBase
from ._generalnodes import LatexGeneralNodesParser



# for Py3
_basestring = str

### BEGIN_PYTHON2_SUPPORT_CODE
import sys
if sys.version_info.major == 2:
    _basestring = basestring
### END_PYTHON2_SUPPORT_CODE





# ------------------------------------------------------------------------------



class LatexDelimitedExpressionParserOpeningDelimiterNotFound(Exception):
    r"""
    Exception class used by a :py:class:`LatexDelimitedExpressionParserInfo`
    object to communicate to the associated `LatexDelimitedExpressionParser`
    instance that the initial delimiter was not found.

    You won't need to worry about handling this exception unless you are writing
    a very customized subclass of
    :py:class:`LatexDelimitedExpressionParserInfo`, see doc there.
    """
    def __init__(self, first_tokens, msg, **kwargs):
        super(LatexDelimitedExpressionParserOpeningDelimiterNotFound, self).__init__(**kwargs)
        self.first_tokens = first_tokens
        self.msg = msg


# LatexDelimitedGroupContentsParserInfo


class LatexDelimitedExpressionParserInfo(object):
    r"""
    Class that specifies how to parse a LaTeX chunk of code that is
    delimited by specific delimiters (a "delimited group").  Helper class for
    :py:class:`LatexDelimitedExpressionParser`.

    This class determines specific aspects of what type of delimited LaTeX code
    we should be reading, such as whether the delimiters are actual LaTeX group
    delimiters, or if they are math mode delimiters, or if they are verbatim
    delimiters, etc.

    Some static/class methods are crucial for determining how the beginning of
    the delimited expression is read.  E.g., determine the parsing state to use
    for the group itself, as well as if a token is an acceptable opening
    delimiter.  After reading the token that we determined corresponds to the
    opening delimiter, an instance of the class is created to handle the rest of
    the group processing.

    Important class methods, called when beginning to parse a delimited
    expression and before an instance of this class is created, are:

    - `get_group_parsing_state()` — Create the parsing state used for the group
      node itself.  One reason it might differ from the surrounding parsing
      state is for instance if the group is a LaTeX group with delimiters that
      are not '{', '}' and which need to be added to the list of LaTeX group
      delimiters.

    - `is_opening_delimiter()` — Determine whether a token that was read is
      indeed an opening delimiter that the current delimited expression parser
      is meant to handle.

    - `get_acceptable_open_delimiter_list()` — This class method is called only
      to generate friendlier error messages.

    The important class instance properties, that should be set by
    :py:meth:`initialize()`, are:

    - `group_parsing_state` — The group's parsing state (e.g., that
      associated with the LatexGroupNode, this might be the same parsing
      state as surrounding code, but it might also be modified if it is to
      include special delimiters, etc.).

      NOTE: the `group_parsing_state` is determined by the
      `LatexDelimitedGroupParser` object before this
      `LatexDelimitedExpressionParserInfo` is constructed.  See the
      :py:meth:`get_group_parsing_state()` static method.

    - `contents_parsing_state` — The group content's parsing state, which
      might differ from surrounding parsing state.  E.g., the group's
      contents might be in math mode.

    - `child_parsing_state_delta` - Any state changes to set when recursing down
      to children of the contents of this delimited content.  By default, the
      delta is applied with respect to the `group_parsing_state`, not the
      `contents_parsing_state`.  [Rationale: this attribute is usually used to
      "undo" some effects in the contents parsing state, so it's more useful to
      have the reference parsing state be the `group_parsing_state`.]

    - `parsed_delimiters` — This object is also responsible for actually
      determining which delimiters were used (if they weren't predetermined
      exactly).  Subclasses can use `get_parsed_delimiters()`, along with a
      custom implementation of `get_matching_delimiter()` if necessary.

      The `parsed_delimiters` is assumed to always be a 2-item tuple.  The
      values can be placeholders, if necessary.  They are only used in user
      messages until the final call to the
      `make_group_node_and_parsing_state_delta()` method.  In that method, the
      value of the `parsed_delimiters` is used to set the final group node's
      delimiters attribute.

    Further responsibilities of this object include:

    - Implement the stopping condition to detect the end delimiter (you
      might need to reimplement :py:meth:`stop_token_condition()`).  Also
      handle the final token that caused the stop (the default
      implementation of :py:meth:`handle_stop_condition_token()`, which is
      to place the token reader past that token, should be sufficient in
      most cases).

    - Create a relevant parser to parse the contents of the delimited
      expression.  See :py:meth:`make_content_parser()`.  The default
      implementation should suffice in most cases.

    - :py:meth:`make_group_node_and_parsing_state_delta()` — prepare the parsing
      state changes information that will be left over after the group is fully
      parsed.


    .. note::

       When subclasses reimplement the methods in this class, they must ensure
       that they accept ``**kwargs`` to accommodate any additional arguments
       that I might think of adding in the future.


    Here are some attributes that are set on the object instance:

    .. py:attribute:: delimited_expression_parser

       A pointer to the main parser instance class, provided for convenience.
       E.g., methods can use this object pointer to look up any custom
       attributes that were set on the main parser instance.

    .. py:attribute:: opening_delimiter_tokens

       The tokens associated with the opening delimiter.  This is the list
       returned by :py:meth:`parse_initial()`.

    .. py:attribute:: first_token

       This attribute holds the first token in `opening_delimiter_tokens`.  The
       first token is used at a couple places, such as for determining the
       initial position of the final group node, or for reporting the token
       associated with the open parser context representing this delimited
       expression.  (Subclasses may choose to set this attribute to something
       else in their `initialize()` method, but I wouldn't see why that is
       necessary.)

    .. py::attribute:: delimiters

       Mirrors the `delimiters` argument of the main parser object.  Recall that
       this is a constraint on what type of delimiters we are required to
       encounter.  This value may either be `None` (no constraint), a single
       string (constraint on the opening delimiter, closing delimiter to be
       deduced automatically), or a 2-item tuple (specify opening and closing
       delimiter).  See also :py:attr:`parsed_delimiters`.

    .. py:attribute:: parsed_delimiters

       A 2-item tuple of the actual delimiters that are applicable to this
       particular delimited expression that we are parsing.  Normally this
       attribute is set in `initialize()`, possibly using the help of
       `get_parsed_delimiters()`, because once we know the opening delimiter we
       also know what closing delimiter to expect.  See doc for
       :py:meth:`get_parsed_delimiters()`, :py:meth:`initialize()`, and
       :py:meth:`make_group_node_and_parsing_state_delta()` for more info on if the
       closing delimiter can't be deduced from the opening delimiter.

       This attribute is set in the constructor to the placeholder tuple `(None,
       None)`, and should be set to an appropriate value in `initialize()`.

    .. py:attribute:: group_parsing_state

       The parsing state returned by :py:meth:`get_group_parsing_state()`

    .. py:attribute:: contents_parsing_state

       The parsing state to use for parsing the contents of the delimited
       expression.  Defaults to `group_parsing_state`; can be set by subclasses
       in their `initialize()` reimplementation.

    .. py:attribute:: child_parsing_state_delta

       Any state changes to set when calling parsers for children of the
       contents of this delimited expression.  This can be left to `None` to
       keep the same parsing state as the contents.  It should be set to a
       :py:class:`~pylatexenc.latexnodes.ParsingStateDelta` instance to specify
       parsing state changes if applicable.

    .. py:attribute:: parsing_state

       The original parsing_state in which the delimited expression main parser
       instance was asked to operate in.  This is the parsing state that was
       provided as an argument to :py:meth:`get_group_parsing_state()`.
    """


    @classmethod
    def get_group_parsing_state(cls, parsing_state, delimiters,
                                delimited_expression_parser, latex_walker):
        r"""
        Return the parsing state object to use for the overall group.  This is the
        parsing state that will be attached to the resulting
        :py:class:`LatexGroupNode`.  (The group contents might have a different
        parsing state.)

        This default implementation simply returns `parsing_state` as is.
        """
        return parsing_state


    @classmethod
    def get_acceptable_open_delimiter_list(cls, delimiters, group_parsing_state,
                                           delimited_expression_parser, latex_walker):
        r"""
        Return a list of strings representing acceptable opening delimiters.

        The result is only used for error messages; this method's return value
        does not influence parsing behavior or the final node structure.
        """
        return []


    @classmethod
    def parse_initial(cls, delimiters, allow_pre_space,
                      latex_walker, token_reader, group_parsing_state,
                      delimited_expression_parser):
        r"""
        Attempt to parse the beginning of the delimited group.

        This method is responsible for inspecting new tokens using
        `token_reader` to to ensure that the first token (or first few tokens)
        indeed correspond to an opening delimiter of the type of expression this
        parser info is meant to handle.

        If an opening delimiter is successfully encountered, then this method
        should return a list of tokens that are associated with the opening
        delimiter that was read.  (Generally this is a single token, like a '{'
        char.)  The returned list will serve as argument to the constructor's
        `opening_delimiter_tokens` argument.  The token reader's position should
        be left *after* the initial delimiter tokens, so that the contents can
        immediately be read without having to move the token reader's position.

        If an opening delimiter is not successfully encountered, or the opening
        delimiter has space and `allow_pre_space` is not set, then the
        :py:exc:`LatexDelimitedExpressionParserOpeningDelimiterNotFound` should
        be raised, with relevant information for error messages and recovery.
        (The exception should be raised regardless of whether or not the
        delimited expression is optional.)  It is not necessary to reset the
        token reader's position, but it is important to set the `first_tokens`
        argument of that exception class to those tokens that were read so far,
        because it is used to reset the token reader correctly if the delimited
        expression was in fact optional or if we are trying to recover from a
        parse error.

        The default implementation of `parse_initial()` provided here inspects a
        single token and uses the `is_opening_delimiter()` class function to
        determine whether or not the token that was read is a valid opening
        delimiter.  You may reimplement this function to customize this
        behavior, e.g., if you need to inspect multiple tokens.  The default
        implementation uses :py:meth:`get_acceptable_open_delimiter_list()` to
        help generate a human-friendly error message in case an opening
        delimiter is not successfully parsed.
        """

        first_token = token_reader.next_token(parsing_state=group_parsing_state)
        
        ok = True
        if not allow_pre_space and first_token.pre_space:
            ok = False
        elif not cls.is_opening_delimiter(
                delimiters=delimiters,
                first_token=first_token,
                group_parsing_state=group_parsing_state,
                delimited_expression_parser=delimited_expression_parser,
                latex_walker=latex_walker
        ):
            ok = False

        if not ok:

            # prepare a human-friendly error message and raise it

            acceptable_opening_delimiters = \
                cls.get_acceptable_open_delimiter_list(
                    delimiters=delimiters,
                    group_parsing_state=group_parsing_state,
                    delimited_expression_parser=delimited_expression_parser,
                    latex_walker=latex_walker
                )
            if not acceptable_opening_delimiters:
                acceptable_delimiters_msg = '??'
            else:
                acceptable_delimiters_msg = ", ".join([
                    "‘{}’".format(od)
                    for od in acceptable_opening_delimiters
                ])

            raise LatexDelimitedExpressionParserOpeningDelimiterNotFound(
                msg='Expected an opening LaTeX delimiter ({}), got {}/‘{}’{}'.format(
                    acceptable_delimiters_msg,
                    first_token.tok,
                    first_token.arg,
                    (' with leading whitespace' if first_token.pre_space else '')
                ),
                first_tokens=[first_token],
            )
            
        return [first_token]


    @classmethod
    def is_opening_delimiter(cls, delimiters, first_token, group_parsing_state,
                             delimited_expression_parser, latex_walker):
        r"""
        Return `True` if the token `first_token` that was just read does indeed
        correspond to an opening delimiter that this parser is intended to read,
        including any constraints provided by the `delimiters` argument to the
        parser instance (provided here as the `delimiters` argument).
        """
        raise RuntimeError("Subclasses must reimplement is_opening_delimiter()")


    @classmethod
    def check_opening_delimiter(cls, delimiters, parsed_opening_delimiter,
                                latex_walker):
        r"""
        A helper convenience function for subclasses' optional use in their
        `is_opening_delimiter()` method reimplementations.  Returns `True` or
        `False` according to whether or not the parsed opening delimiter
        (`parsed_opening_delimiter`, a string) matches with the given
        `delimiters` argument, which was the delimiters constraint specified to
        the main parser instance.

        I.e., if the `delimiters` is None, `True` is returned because there was
        no delimiters constraint.  If the `delimiters` is a single string, it is
        compared to the parsed delimiter and returns `True` only if the strings
        are equal.  Similarly, if `delimiters` is a 2-item tuple, the first item
        is compared to the parsed delimiter.
        """
        if delimiters is None:
            return True

        if isinstance(delimiters, _basestring):
            open_delim = delimiters
        else:
            open_delim = delimiters[0]
        if parsed_opening_delimiter != open_delim:
            return False
        return True

    # ---

    def __init__(self, delimited_expression_parser, opening_delimiter_tokens,
                 group_parsing_state, parsing_state, delimiters, latex_walker):
        super(LatexDelimitedExpressionParserInfo, self).__init__()

        # save args
        self.delimited_expression_parser = delimited_expression_parser
        self.opening_delimiter_tokens = opening_delimiter_tokens
        if opening_delimiter_tokens:
            self.first_token = opening_delimiter_tokens[0]
        else:
            self.first_token = None
        self.group_parsing_state = group_parsing_state
        self.parsing_state = parsing_state
        self.delimiters = delimiters
        self.latex_walker = latex_walker
        # simple defaults so the attributes are there, can be overwritten in initialize()
        self.contents_parsing_state = self.group_parsing_state
        self.child_parsing_state_delta = None
        self.parsed_delimiters = (None, None)

    def initialize(self):
        r"""
        This method is called after the instance is created, so that subclasses can
        initialize the important relevant attributes for this class.

        By default, this method initializes the `parsed_delimiters` attribute
        using the `get_parsed_delimiters()` method.
        """
        self.contents_parsing_state = self.group_parsing_state
        self.child_parsing_state_delta = None
        self.parsed_delimiters = self.get_parsed_delimiters()

    def stop_token_condition(self, token):
        r"""
        This method must be reimplemented so that the parser knows when a closing
        delimiter was encountered.
        """
        raise RuntimeError("Subclasses must reimplement stop_token_condition()")

    def handle_stop_condition_token(self, token,
                                    latex_walker, token_reader, parsing_state):
        r"""
        Called to take action after the `token` was read and determined to satisfy
        the stopping condition.  By default, the `token_reader` is positioned
        immediately after the stopping token.
        """
        token_reader.move_past_token(token)
        logger.debug(
            "LatexDelimitedExpressionParser moved token reader past token %r",
            token
        )

    def make_child_parsing_state(self, parsing_state, node_class):
        r"""
        When parsing the delimited expression's contents, we might need to recurse
        into child groups etc.; in such cases, this method is used to create a
        relevant parsing state for child nodes.  It is directly used as the
        expression's internal node collector's `make_child_parsing_state()`
        handler.

        You may reimplement this method if you need a more detailed mechanism
        for determining what parsing state the child parser should be initiated
        with, e.g., if the parsing state should vary according to what type of
        child is encountered.
        """

        if self.child_parsing_state_delta is not None:
            logger.debug("Requested child parsing state, applying delta %r",
                         self.child_parsing_state_delta)
            return get_updated_parsing_state_from_delta(
                self.group_parsing_state,
                self.child_parsing_state_delta,
                self.latex_walker,
            )

        logger.debug("Requested child parsing state, keeping default %r", parsing_state)
        return parsing_state


    def get_matching_delimiter(self, opening_delimiter):
        r"""
        Subclasses can reimplement this method instead of reimplementing
        `get_parsed_delimiters()`.  This method will determine what delimiter
        should be used as closing delimiter for the given read
        opening_delimiter.  This can be used to match parentheses or braces, or
        LaTeX group delimiters, or math delimiters, etc.

        The default implementation returns `opening_delimiter` as is.
        """
        return opening_delimiter


    def get_parsed_delimiters(self):
        r"""
        Determine what the actual delimiters of this expression will be, based off
        the opening delimiter.  This method is usually called at the beginning
        of the delimited expression to help in information messages, etc.

        This function is called by the default `initialize()` method to set the
        `parsed_delimiters` attribute.

        The default implementation inspects the `delimiters` attribute.  Recall
        that `delimiters` is the argument that was provided to the
        `LatexDelimitedExpressionParser()` instance, specifying a requirement
        for what delimiters we want to accept.  If `delimiters` is already a
        pair, this method simply returns that pair.  If `delimiters` is a
        string, it attempts to find the matching closing delimiter by calling
        `get_matching_delimiter()`.  If `delimiters` is None, then the opening
        delimiter is set to the first token's `arg` attribute, and a matching
        delimiter is sought via the `get_matching_delimiter()` method.

        Usually there shouldn't be any need to reimplement this method.
        Instead, you should reimplement :py:meth:`get_matching_delimiter()` to
        instruct this method how to deducing the closing delimiter that is
        associated with a specific opening delimiter.

        In the event where there might be multiple acceptable closing
        delimiters, then the closing delimiter cannot be known in advance.  You
        need to handle this case manually.  I.e., return an empty closing
        delimiter here, or reimplement `initialize()` to assign a temporary
        placeholder value to the `parsed_delimiters` attribute.  This attribute
        is only used for information messages anyway before the final
        `make_group_node_and_parsing_state_delta()` anyways.  However, you need
        to either reimplement `make_group_node_and_parsing_state_delta()`, or to
        set the property `parsed_delimiters` correctly before that method gets
        called.
        """
        first_token = self.first_token
        delimiters = self.delimiters

        if delimiters is None:
            delimiters = first_token.arg

        if isinstance(delimiters, _basestring):
            opening_delimiter = delimiters
            closing_delimiter = self.get_matching_delimiter(opening_delimiter)
            return (opening_delimiter, closing_delimiter)

        return delimiters

    def make_content_parser(self, latex_walker, token_reader):
        r"""
        This method is responsible for creating a relevant parser to parse the
        contents of the delimited expression.

        The default implementation creates a `LatexGeneralNodesParser` instance
        that is properly initialized call the :py:meth:`stop_token_condition`,
        :py:meth:`handle_stop_condition_token`, and
        :py:meth:`make_child_parsing_state` callbacks on this instance object.

        You should only need to reimplement this method if you need more
        detailed control over the contents parser, e.g., if you need a stopping
        condition on the node list instead of the token only
        (`stop_nodelist_condition`).
        """
        if self.parsed_delimiters[1]:
            expected_matching = "matching ‘{}’".format(self.parsed_delimiters[1])
        else:
            expected_matching = "matching closing delimiter"
        return LatexGeneralNodesParser(
            make_child_parsing_state=self.make_child_parsing_state,
            stop_token_condition=self.stop_token_condition,
            require_stop_condition_met=True,
            handle_stop_condition_token=self.handle_stop_condition_token,
            stop_condition_message=
            "Expected {} after ‘{}’".format(expected_matching, self.parsed_delimiters[0])
        )

    def get_open_context_description(self):
        r"""
        Return a 2-item tuple `(msg, token)` or `None`.  The value must be suitable
        for passing as an argument to the `open_context` parameter of
        :py:meth:`LatexWalkerBase.parse_content()`.
        """
        return (
            'Delimited expression ‘{}…{}’'.format(*self.parsed_delimiters)
            ,
            self.first_token
        )

    def make_group_node_and_parsing_state_delta(self, latex_walker,
                                                token_reader, nodelist,
                                                parsing_state_delta):
        r"""
        Actually create the final node object and the associated parsing_state_delta
        that will be returned by the delimited expression parser.

        The default implementation creates a :py:class:`~nodes.LatexGroupNode`
        instance.  The `delimiters` field is set to the `parsed_delimiters`
        field that must have been set to an appropriate value by this point.
        """

        # use cur_pos() to include the closing delimiter
        pos_end = token_reader.cur_pos()

        group_node = latex_walker.make_node(
            nodes.LatexGroupNode,
            nodelist=nodelist,
            parsing_state=self.group_parsing_state,
            delimiters=self.parsed_delimiters,
            pos=self.first_token.pos,
            pos_end=pos_end
        )

        return group_node, parsing_state_delta




# ----------------------------




class LatexDelimitedExpressionParser(LatexParserBase):
    r"""
    A general-purpose parser / parser base class to handle LaTeX content that is
    enclosed by some form of delimiters.  This can include a standard TeX group
    (``{ ... }``), or math mode blocks (``$...$``), or environments
    (``\begin{xyz}...\end{xyz}``), etc.

    This class is a general base class that groups common functionality of
    various parsers.  Usually you shouldn't use `LatexDelimitedExpressionParser`
    parser instances directly.  Rather, you should use one of the more
    specialized parsers such as :py:class:`LatexDelimitedGroupParser` or
    :py:class:`LatexMathParser`, etc.

    Many specifics by which the delimited group is parsed is determined by a
    separate helper class, which must be a
    :py:class:`LatexDelimitedExpressionParserInfo` subclass.  That info class is
    given through the `delimited_expression_parser_info_class` constructor
    argument.  Specialized delimiter-based parsers, such as
    :py:class:`LatexDelimitedGroupParser`, provide their own info classes
    `delimited_expression_parser_info_class`; when using those specialized
    parsers, you don't have to worry about that argument.

    The main :py:meth:`parse()` method normally returns a
    :py:class:`LatexGroupNode` instance with the delimited LaTeX contents that
    was parsed according to the provided info class.  The exact object that is
    returned can be customized by the info class, see
    :py:meth:`LatexDelimitedExpressionParserInfo.make_group_node_and_parsing_state_delta()`.

    Constructor arguments:

    - `delimiters` can be either:

        * `None` to auto-detect delimiters.  If the first char token is one of the
          `auto_delimiters`, then the corresponding closing delimiter is
          determined from the parsing state.

        * A single `<char1>` indicating an opening delimiter.  The corresponding
          closing delimiter will be obtained by inspecting the parsing state.

        * A pair `(<char1>, <char2>)` of opening and closing delimiters.

    - If `optional` is `True`, then no error is raised if the expected opening
      delimiter is not present and a `None` node is returned by the parser.  By
      default, not encountering an expected opening delimiter causes a parse
      error.

    - If `allow_pre_space` is `True`, any space preceding the group is ignored
      (it's `False` by default). This can be useful for instance in certain edge
      cases where you'd want an optional argument to immediately follow a
      command, so that an opening bracket after whitespace doesn't get parsed as
      an optional argument.  For instance, IIRC AMS redefines the command ``\\``
      to require its optional argument (vertical spacing) to immediately follow
      the ``\\`` without any whitespace so that the code ``A+B=C \\ [A,B] = 0``
      doesn't parse ``[A,B]`` as an argument to ``\\``.

    - If `discard_parsing_state_delta` is `True`, any parsing state changes
      information from parsing the content of the group is discarded.  This is
      the default behavior and mirrors the behavior of (La)TeX that most
      definitions are local to a group

      .. todo: How could we think about implementing ``\global`` definitions then?
    """
    def __init__(self,
                 delimiters,
                 delimited_expression_parser_info_class,
                 optional=False,
                 allow_pre_space=False,
                 discard_parsing_state_delta=True,
                 **kwargs):
        super(LatexDelimitedExpressionParser, self).__init__(**kwargs)
        self.delimiters = delimiters
        self.optional = optional
        self.allow_pre_space = allow_pre_space
        # <-- allow_pre_space isn't a great interface here I think. (Where
        # should the space go in the node tree then?) -> use separate
        # LatexIgnoreSpaceAndCommentsPar() for callable arguments. (???)
        #
        # ### but then we might need to start parsing the group multiple times!
        # ### (to read the space, to read the opening delimiter, to enter the
        # ### group parser, ... ... )
        #
        self.discard_parsing_state_delta = discard_parsing_state_delta

        self.delimited_expression_parser_info_class = delimited_expression_parser_info_class


    def contents_can_be_empty(self):
        return self.optional


    def parse(self, latex_walker, token_reader, parsing_state, **kwargs):

        group_parsing_state = \
            self.delimited_expression_parser_info_class.get_group_parsing_state(
                parsing_state=parsing_state,
                delimiters=self.delimiters,
                delimited_expression_parser=self,
                latex_walker=latex_walker
            )

        opening_delimiter_tokens = None

        try:
            opening_delimiter_tokens = \
                self.delimited_expression_parser_info_class.parse_initial(
                    delimiters=self.delimiters,
                    allow_pre_space=self.allow_pre_space,
                    latex_walker=latex_walker,
                    token_reader=token_reader,
                    group_parsing_state=group_parsing_state,
                    delimited_expression_parser=self,
                )
        except LatexDelimitedExpressionParserOpeningDelimiterNotFound as e:
            
            recovery_token = None
            if e.first_tokens is not None and len(e.first_tokens):
                recovery_token = e.first_tokens[0]

            if self.optional:
                # all ok, the argument was optional and was simply not specified.
                if e.first_tokens is not None and len(e.first_tokens):
                    token_reader.move_to_token(recovery_token)
                return None, None

            pos = None
            if recovery_token is not None:
                pos = recovery_token.pos

            # raise a parse error
            raise LatexWalkerNodesParseError(
                msg=e.msg,
                pos=pos,
                recovery_nodes=latex_walker.make_nodelist(
                    [],
                    parsing_state=group_parsing_state,
                    pos=recovery_token.pos,
                    pos_end=recovery_token.pos, # w/o the token itself
                ),
                recovery_at_token=recovery_token,
                error_type_info={
                    'what': 'nodes_delimited_expected_opening_delimiter_not_found',
                    'first_tokens': e.first_tokens,
                },
            )

        # instantiate the contents parser info class now -->
        contents_parser_info = self.delimited_expression_parser_info_class(
            self,
            opening_delimiter_tokens=opening_delimiter_tokens,
            group_parsing_state=group_parsing_state,
            parsing_state=parsing_state,
            delimiters=self.delimiters,
            latex_walker=latex_walker
        )

        contents_parser_info.initialize()


        contents_parser = contents_parser_info.make_content_parser(
            latex_walker,
            token_reader
        )

        nodelist, parsing_state_delta = latex_walker.parse_content(
            contents_parser,
            token_reader=token_reader,
            parsing_state=contents_parser_info.contents_parsing_state,
            open_context=contents_parser_info.get_open_context_description()
        )

        # can discard the parsing_state_delta since the parsing state gets reset at
        # the end of the group.
        if self.discard_parsing_state_delta and parsing_state_delta is not None:
            logger.debug("Discarding parsing state changes after delimited expression: %r",
                         parsing_state_delta)
            parsing_state_delta = None

        groupnode, parsing_state_delta = \
            contents_parser_info.make_group_node_and_parsing_state_delta(
                latex_walker=latex_walker,
                token_reader=token_reader,
                nodelist=nodelist,
                parsing_state_delta=parsing_state_delta,
            )
        
        return groupnode, parsing_state_delta







# ------------------------------------------------

class LatexDelimitedGroupParserInfo(LatexDelimitedExpressionParserInfo):
    r"""
    Helper class for :py:class:`LatexDelimitedGroupParser`.  See also
    :py:class:`LatexDelimitedExpressionParserInfo`.
    """

    @classmethod
    def get_group_parsing_state(cls, parsing_state, delimiters, delimited_expression_parser,
                                latex_walker, **kwargs):
        r"""
        Return the parsing state object to use for the overall group.  This is the
        parsing state that will be attached to the resulting
        :py:class:`LatexGroupNode`.  (The group contents might have a different
        parsing state.)

        The default implementation inspects the `parsing_state` to ensure that
        the current delimiters are in the list of latex group delimiters.  It
        will add them if necessary and if it is able to (i.e., if the
        `delimiters` property specifies both opening and closing delimiters).
        If `delimiters` only contains the opening delimiter, and if it is not
        listed as a latex group delimiter, a parse error is raised.

        You should reimplement this method if the delimiters you want to capture
        are not latex group delimiters.  See :py:class:`LatexMathParser` for an
        example.

        .. note::
    
            This method assumes that the delimiters are latex group type (e.g.,
            curly brace chars), as specified in the parsing state's latex group
            delimiter list.  If not, then you need to reimplement this function
            in a subclass.
        """
        if delimiters is None:
            return parsing_state

        if isinstance(delimiters, _basestring):
            if delimiters not in parsing_state._latex_group_delimchars_by_open:
                raise ValueError(
                    "Delimiter ‘{}’ not a valid latex group delimiter ({!r})"
                    .format(delimiters, parsing_state.latex_group_delimiters)
                )
            return parsing_state
        
        delimiters_t = tuple(delimiters)
        ### doesn't work with transcrypt ... :/
        # if delimiters_te in parsing_state.latex_group_delimiters:
        #     # all ok, they are known group delimiters
        #     return parsing_state
        for odcd in parsing_state.latex_group_delimiters:
            if delimiters_t == odcd:
                # all ok, they are known group delimiters
                return parsing_state

        # otherwise, add the delimiters to the parsing state's group delimiter list
        return parsing_state.sub_context(
            latex_group_delimiters = \
                parsing_state.latex_group_delimiters + [ delimiters_t ]
        )


    @classmethod
    def get_acceptable_open_delimiter_list(cls, delimiters, group_parsing_state,
                                           delimited_expression_parser, latex_walker,
                                           **kwargs):
        r"""
        Only to be used for error messages.
        """
        if delimiters is not None:
            if isinstance(delimiters, _basestring):
                return [delimiters]
            else:
                return [delimiters[0]]
            
        return [
            od
            for (od, cd) in group_parsing_state.latex_group_delimiters
        ]

    @classmethod
    def is_opening_delimiter(cls, delimiters, first_token, group_parsing_state,
                             delimited_expression_parser, latex_walker, **kwargs):

        if first_token.tok != 'brace_open':
            return False

        if not cls.check_opening_delimiter(delimiters=delimiters,
                                           parsed_opening_delimiter=first_token.arg,
                                           latex_walker=latex_walker):
            return False

        return True
    

    # ---


    def stop_token_condition(self, token):
        if token.tok == 'brace_close' and token.arg == self.parsed_delimiters[1]:
            logger.debug(
                "LatexDelimitedGroupParser encountered the expected closing brace %r",
                token
            )
            return True
        return False


    def get_matching_delimiter(self, opening_delimiter):
        r"""
        Doc..............

        This method assumes that the delimiters are latex group type (e.g., curly
        brace chars).  If not, then you need to reimplement this function in a
        subclass.
        """
        return self.group_parsing_state._latex_group_delimchars_by_open[opening_delimiter]



class LatexDelimitedGroupParser(LatexDelimitedExpressionParser):
    r"""
    Doc.........................

    In all cases, the first token read (after possible whitespace) must be a
    'brace_open' type.  If `delimiters` is a pair of characters, the parsing
    state is inspected to ensure that these delimiters are recorded as latex
    group delimiters, and will add them if necessary for parsing the group
    contents (but not its parsed children).

          If the delimiters are not defined as LaTeX group delimiters in the
          parsing state, then a new parsing state is created that includes these
          delimiters.  The new parsing state is used to parse the group contents
          but not any child nodes.  This behavior ensures that expressions of
          the type ``\macro[A[B]]`` and ``\macro[{[}]`` are parsed correctly
          respectively as an optional argument ``A[B]`` to ``\macro`` and as a
          single opening bracket as an optional argument to ``\macro``.
    """

    def __init__(self,
                 delimiters,
                 delimited_expression_parser_info_class=LatexDelimitedGroupParserInfo,
                 **kwargs):
        super(LatexDelimitedGroupParser, self).__init__(
            delimiters=delimiters,
            delimited_expression_parser_info_class=delimited_expression_parser_info_class,
            **kwargs
        )
