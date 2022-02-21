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
from ..nodes import *

from .._nodescollector import LatexNodesCollector


from ._base import LatexParserBase

# for Py3
_basestring = str

### BEGIN_PYTHON2_SUPPORT_CODE
import sys
if sys.version_info.major == 2:
    _basestring = basestring
### END_PYTHON2_SUPPORT_CODE




# ------------------------------------------------------------------------------

class LatexGeneralNodesParser(LatexParserBase):
    def __init__(self,
                 stop_token_condition=None,
                 stop_nodelist_condition=None,
                 require_stop_condition_met=True,
                 stop_condition_message=None,
                 make_child_parsing_state=None,
                 handle_stop_condition_token=None,
                 include_stop_token_pre_space_chars=True,
                 handle_stop_data=None,
                 **kwargs):
        super(LatexGeneralNodesParser, self).__init__(**kwargs)
        self.stop_token_condition = stop_token_condition
        self.stop_nodelist_condition = stop_nodelist_condition
        # no effect if conditions are None:
        self.require_stop_condition_met = require_stop_condition_met
        self.stop_condition_message = stop_condition_message
        # parsing state for child nodes
        self.make_child_parsing_state = make_child_parsing_state
        # 
        self.handle_stop_condition_token = handle_stop_condition_token
        self.handle_stop_data = handle_stop_data

        self.include_stop_token_pre_space_chars = include_stop_token_pre_space_chars


    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        collector = latex_walker.make_nodes_collector(
            token_reader=token_reader,
            parsing_state=parsing_state,
            make_group_parser=LatexDelimitedGroupParser,
            make_math_parser=LatexMathParser,
            stop_token_condition=self.stop_token_condition,
            stop_nodelist_condition=self.stop_nodelist_condition,
            make_child_parsing_state=self.make_child_parsing_state,
            include_stop_token_pre_space_chars=self.include_stop_token_pre_space_chars,
        )

        try:

            collector.process_tokens()

        except LatexWalkerParseError as e:

            # we got an error! Add some info to help with recovery in case
            # we're in tolerant parsing mode, and then raise the issue
            # further up.
            #
            
            logger.debug("Got parse error while reading general nodes: %r", e)

            raise LatexWalkerNodesParseError(
                msg=e.msg,
                pos=e.pos,
                recovery_nodes=collector.get_final_nodelist(),
                recovery_carryover_info=collector.get_parser_carryover_info(),
            )

        # check that any required stop condition was met

        stop_token_condition_met = collector.stop_token_condition_met()
        stop_nodelist_condition_met = collector.stop_nodelist_condition_met()

        logger.debug("finished parsing general nodes; "
                     "self.require_stop_condition_met=%r, "
                     "stop_token_condition=%r, stop_token_condition_met=%r, "
                     "stop_nodelist_condition=%r, stop_nodelist_condition_met=%r",
                     self.require_stop_condition_met,
                     self.stop_token_condition, stop_token_condition_met,
                     self.stop_nodelist_condition, stop_nodelist_condition_met)

        met_a_required_stop_condition = False
        if not self.require_stop_condition_met:
            # no condition to meet
            met_a_required_stop_condition = True
        else:
            if self.stop_token_condition is not None:
                if stop_token_condition_met:
                    met_a_required_stop_condition = True
            elif self.stop_nodelist_condition is not None:
                if stop_nodelist_condition_met:
                    met_a_required_stop_condition = True
            else:
                # there were no stopping conditions set
                met_a_required_stop_condition = True

        if not met_a_required_stop_condition:
            #
            message = self.stop_condition_message
            if message is None:
                message = (
                    'End of stream encountered while parsing nodes without '
                    'stop condition being met'
                )
            exc = LatexWalkerNodesParseError(
                msg=message,
                pos=collector.pos_start(),
                recovery_nodes=collector.get_final_nodelist(),
                recovery_carryover_info=collector.get_parser_carryover_info(),
            )
            raise exc

        if stop_token_condition_met \
           and self.handle_stop_condition_token is not None:
            stoptoken = collector.stop_token_condition_met_token()
            # do something with the token that caused the stop condition to fire
            if stoptoken is not None:
                self.handle_stop_condition_token(
                    stoptoken,
                    latex_walker=latex_walker,
                    token_reader=token_reader,
                    parsing_state=parsing_state,
                )

        stop_data = collector.stop_condition_stop_data()
        if stop_data is not None and self.handle_stop_data is not None:
            self.handle_stop_data(stop_data,
                                  latex_walker=latex_walker,
                                  token_reader=token_reader,
                                  parsing_state=parsing_state)

        # put together the node list & carry on

        nodelist = collector.get_final_nodelist()
        carryover_info = collector.get_parser_carryover_info()

        return nodelist, carryover_info



# ------------------------------------------------------------------------------


class LatexSingleNodeParser(LatexGeneralNodesParser):
    def __init__(self, stop_after_comment=True, **kwargs):
        super(LatexSingleNodeParser, self).__init__(
            stop_nodelist_condition=self._stop_nodelist_condition,
            require_stop_condition_met=False,
            **kwargs
        )
        self.stop_after_comment = stop_after_comment
        
    def _stop_nodelist_condition(self, nodelist):
        nl = nodelist
        if not self.stop_after_comment:
            nl = [n for n in nl if not n.isNodeType(LatexCommentNode)]
        if len(nl) >= 1:
            return True
        return False


    def contents_can_be_empty(self):
        return False


# ------------------------------------------------------------------------------




class LatexDelimitedGroupParser(LatexParserBase):
    r"""
    ............

    In all cases, the first token read (after whitespace) must be a 'brace_open'
    type.  If `delimiters` is a pair of characters, the parsing state is
    inspected to ensure that these delimiters are recorded as latex group
    delimiters, and will add them if necessary for parsing the group contents
    (but not its parsed children).

    Arguments:

    - `delimiters` can be either:

        * `None` to auto-detect delimiters.  If the first char token is one of the
          `auto_delimiters`, then the corresponding closing delimiter is
          determined from the parsing state.

        * A single `<char1>` indicating an opening delimiter.  The corresponding
          closing delimiter will be obtained by inspecting the parsing state.

        * A pair `(<char1>, <char2>)` of opening and closing delimiters.

          If the delimiters are not defined as LaTeX group delimiters in the
          parsing state, then a new parsing state is created that includes these
          delimiters.  The new parsing state is used to parse the group contents
          but not any child nodes.  This behavior ensures that expressions of
          the type ``\macro[A[B]]`` and ``\macro[{[}]`` are parsed correctly
          respectively as an optional argument ``A[B]`` to ``\macro`` and as a
          single opening bracket as an optional argument to ``\macro``.

    - If `optional` is `True`, then no error is raised if the expected opening
      delimiter is not present and a `None` node is returned by the parser.  By
      default, not encountering the expected opening delimiter causes a parse
      error.

    - If `allow_pre_space` is `True` (by default), any space preceding the group
      is ignored.  Use `allow_pre_space=False` to inhibit this behavior.  This
      can be useful for instance in certain edge cases where you'd want an
      optional argument to immediately follow a command, so that an opening
      bracket after whitespace doesn't get parsed as an optional argument.  For
      instance, IIRC AMS redefines the command ``\\`` to require its optional
      argument (vertical spacing) to immediately follow the ``\\`` without any
      whitespace so that the code ``A+B=C \\ [A,B] = 0`` doesn't parse ``[A,B]``
      as an argument to ``\\``.

    - If `discard_carryover_info` is `True`, any carryover information from
      parsing the content of the group is discarded.  This is the default
      behavior and mirrors the behavior of (La)TeX that most definitions are
      local to a group

      .. todo: How do we implement ``\global`` definitions then?
    """
    def __init__(self,
                 delimiters,
                 optional=False,
                 allow_pre_space=True,
                 discard_carryover_info=True,
                 **kwargs):
        super(LatexDelimitedGroupParser, self).__init__(**kwargs)
        self.delimiters = delimiters
        self.optional = optional
        self.allow_pre_space = allow_pre_space
        self.discard_carryover_info = discard_carryover_info

        self.acceptable_opening_delimiter_token_types = ('brace_open', )
        self.make_group_contents_parser_info = \
            LatexDelimitedGroupParser.GroupContentsParserInfo

    def contents_can_be_empty(self):
        return self.optional


    def get_group_parsing_state(self, parsing_state):
        r"""
        ..............

        This method assumes that the delimiters are latex group type (e.g., curly
        brace chars).  If not, then you need to reimplement this function in a
        subclass.
        """
        if self.delimiters is None:
            return parsing_state

        if isinstance(self.delimiters, _basestring):
            if self.delimiters not in parsing_state._latex_group_delimchars_by_open:
                raise ValueError(
                    "Delimiter ‘{}’ not a valid latex group delimiter ({!r})"
                    .format(self.delimiters, parsing_state.latex_group_delimiters)
                )
            return parsing_state
        
        if self.delimiters in parsing_state.latex_group_delimiters:
            # all ok, they are known group delimiters
            return parsing_state

        # add the delimiters to the parsing state's group delimiter list
        return parsing_state.sub_context(
            latex_group_delimiters= \
                parsing_state.latex_group_delimiters + [ self.delimiters ]
        )

    def is_acceptable_opening_delimiter(self, first_token, group_parsing_state):
        if first_token.tok not in self.acceptable_opening_delimiter_token_types:
            return False

        if self.delimiters is not None:
            if isinstance(self.delimiters, _basestring):
                open_delim = self.delimiters
            else:
                open_delim = self.delimiters[0]

            if first_token.arg != open_delim:
                return False

        if not self.allow_pre_space and first_token.pre_space:
            return False

        return True

    def get_acceptable_open_delimiter_list(self, group_parsing_state):
        r"""
        ............

        Only used for error messages.
        """
        if self.delimiters is not None:
            if isinstance(self.delimiters, _basestring):
                return [self.delimiters]
            else:
                return [self.delimiters[0]]
            
        return [
            od
            for (od, cd) in group_parsing_state.latex_group_delimiters
        ]

    class GroupContentsParserInfo(object):

        def __init__(self, delimited_group_parser, first_token,
                     group_parsing_state, parsing_state, delimiters):
            super(LatexDelimitedGroupParser.GroupContentsParserInfo, self).__init__()

            # save args
            self.delimited_group_parser = delimited_group_parser
            self.first_token = first_token
            self.group_parsing_state = group_parsing_state
            self.parsing_state = parsing_state
            self.delimiters = delimiters

        def initialize(self):
            # default assignments, for latex groups; can be overridden by subclasses etc.
            self.contents_parsing_state = self.group_parsing_state
            self.child_parsing_state = self.parsing_state
            self.parsed_delimiters = self.get_parsed_delimiters()

        def stop_token_condition(self, token):
            if token.tok == 'brace_close' and token.arg == self.parsed_delimiters[1]:
                logger.debug(
                    "LatexDelimitedGroupParser encountered the expected closing brace %r",
                    token
                )
                return True
            return False
        
        def handle_stop_condition_token(self, token,
                                        latex_walker, token_reader, parsing_state):
            token_reader.move_past_token(token)
            logger.debug(
                "LatexDelimitedGroupParser moved token reader past token %r",
                token
            )

        def make_child_parsing_state(self, group_parsing_state, node_class):
            return self.child_parsing_state

        def get_matching_delimiter(self, opening_delimiter):
            r"""
            ..............

            This method assumes that the delimiters are latex group type (e.g., curly
            brace chars).  If not, then you need to reimplement this function in a
            subclass.
            """
            return self.group_parsing_state._latex_group_delimchars_by_open[opening_delimiter]

        def get_parsed_delimiters(self):
            r"""
            ..............
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

        def parse_content(self, latex_walker, token_reader):

            contents_parser = LatexGeneralNodesParser(
                stop_token_condition=self.stop_token_condition,
                make_child_parsing_state=self.make_child_parsing_state,
                require_stop_condition_met=True,
                handle_stop_condition_token=self.handle_stop_condition_token,
            )

            nodelist, carryover_info = latex_walker.parse_content(
                contents_parser,
                token_reader=token_reader,
                parsing_state=self.contents_parsing_state,
                open_context=(
                    'Delimited expression ‘{}…{}’'
                    .format(*self.parsed_delimiters),
                    self.first_token
                )
            )

            return nodelist, carryover_info

        def make_group_node_carryover_info(self, latex_walker, token_reader,
                                           nodelist, carryover_info):

            # use cur_pos() to include the closing delimiter
            pos_end = token_reader.cur_pos()

            group_node = latex_walker.make_node(
                LatexGroupNode,
                nodelist=nodelist,
                parsing_state=self.group_parsing_state,
                delimiters=self.parsed_delimiters,
                pos=self.first_token.pos,
                pos_end=pos_end
            )

            return group_node, carryover_info
        

    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        group_parsing_state = self.get_group_parsing_state(parsing_state)

        first_token = token_reader.next_token(parsing_state=group_parsing_state)
        
        if not self.is_acceptable_opening_delimiter(
                first_token=first_token,
                group_parsing_state=group_parsing_state
        ):

            if self.optional:
                # all ok, the argument was optional and was simply not specified.
                token_reader.move_to_token(first_token)
                return None, None

            acceptable_delimiters_msg = ", ".join([
                "‘{}’".format(od)
                for od in self.get_acceptable_open_delimiter_list(group_parsing_state)
            ])
            raise LatexWalkerNodesParseError(
                msg='Expected an opening LaTeX delimiter (%s), got %s/‘%s’%s' %(
                    acceptable_delimiters_msg,
                    first_token.tok,
                    first_token.arg,
                    (' with leading whitespace' if first_token.pre_space else '')
                ),
                recovery_nodes=LatexNodeList([]),
                recovery_at_token=first_token
            )

        if first_token is None:
            # All ok, an optional argument was not provided.  (In case
            # `self.optional=False`, an error was already raised by
            # get_opening_token().)
            return None, None

        # now delimiters is either None or a tuple of (open, close)

        contents_parser_info = self.make_group_contents_parser_info(
            self,
            first_token=first_token,
            group_parsing_state=group_parsing_state,
            parsing_state=parsing_state,
            delimiters=self.delimiters,
        )
        contents_parser_info.initialize()

        nodelist, carryover_info = contents_parser_info.parse_content(
            latex_walker=latex_walker,
            token_reader=token_reader
        )

        # can discard the carryover_info since the parsing state gets reset at
        # the end of the group.
        if self.discard_carryover_info and carryover_info is not None:
            logger.debug("Discarding carryover information %r after delimited group",
                         carryover_info)
            carryover_info = None

        groupnode, carryover_info = contents_parser_info.make_group_node_carryover_info(
            latex_walker=latex_walker,
            token_reader=token_reader,
            nodelist=nodelist,
            carryover_info=carryover_info,
        )
        
        return groupnode, carryover_info






# ------------------------------------------------------------------------------




class LatexMathParser(LatexDelimitedGroupParser):
    def __init__(self,
                 math_mode_delimiters,
                 **kwargs):
        super(LatexMathParser, self).__init__(
            delimiters=math_mode_delimiters,
            discard_carryover_info=False,
            **kwargs)

        self.acceptable_opening_delimiter_token_types = \
            ('mathmode_inline', 'mathmode_display')
        self.make_group_contents_parser_info = \
            LatexMathParser.MathContentsParserInfo

    def contents_can_be_empty(self):
        return False
        
    def get_group_parsing_state(self, parsing_state):
        return parsing_state

    def get_acceptable_open_delimiter_list(self, group_parsing_state):
        if self.delimiters is not None:
            if isinstance(self.delimiters, _basestring):
                return [self.delimiters]
            else:
                return [self.delimiters[0]]
            
        return [
            od
            for (od, cd) in (
                    group_parsing_state.latex_inline_math_delimiters
                    + group_parsing_state.latex_display_math_delimiters
            )
        ]


    class MathContentsParserInfo(LatexDelimitedGroupParser.GroupContentsParserInfo):

        def initialize(self):
            # set up all the relevant fields manually:

            self.math_mode_type = self.first_token.tok
            self.math_mode_delimiter = self.first_token.arg

            self.math_parsing_state = self.parsing_state.sub_context(
                in_math_mode=True,
                math_mode_delimiter=self.math_mode_delimiter
            )

            self.contents_parsing_state = self.math_parsing_state
            self.child_parsing_state = self.math_parsing_state
            self.parsed_delimiters = self.get_parsed_delimiters()

        def stop_token_condition(self, token):
            if token.tok == self.math_mode_type and token.arg == self.parsed_delimiters[1]:
                return True
            return False

        def get_matching_delimiter(self, opening_delimiter):
            return self.math_parsing_state._math_expecting_close_delim_info['close_delim']


        def make_group_node_carryover_info(self, latex_walker, token_reader,
                                           nodelist, carryover_info):

            # As for the delimited group parser, use cur_pos() so that it includes
            # the closing math mode delimiter.
            pos_end = token_reader.cur_pos()

            # note that nodelist can be None in case of a parse error

            if self.math_mode_type == 'mathmode_inline':
                displaytype = 'inline'
            elif self.math_mode_type == 'mathmode_display':
                displaytype = 'display'
            else:
                displaytype = '<unknown>'

            math_node = latex_walker.make_node(
                LatexMathNode,
                displaytype=displaytype,
                nodelist=nodelist,
                parsing_state=self.parsing_state,
                delimiters=self.parsed_delimiters,
                pos=self.first_token.pos,
                pos_end=pos_end,
            )

            return math_node, carryover_info
