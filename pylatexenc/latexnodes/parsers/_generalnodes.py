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
    r"""
    Parse general nodes, either until a stopping condition is met, or until the
    end of stream is reached.

    This is the general-purpose parser that parses the bulk of LaTeX content.
    It will parse content, using a nodes collector instance, where the latter
    will instantiate specialized parsers whenever specific constructs (such as
    macros, environments, arguments, etc.) are identified.

    Nodes are parsed with a `LatexNodesCollector` instance provided by the latex
    walker instance (see `LatexWalker.make_nodes_collector()`).  This class can
    be seen as a thin wrapper around a `LatexNodesCollector` instance to provide
    a `LatexParserBase` interface.

    Arguments:

      - `stop_token_condition`, `stop_nodelist_condition`,
        `make_child_parsing_state`, `include_stop_token_pre_space_chars` are
        passed on directly to create a nodes collector instance (see also
        :py:meth:`parse()`)

      - If `require_stop_condition_met` is `True` (the default), then any
        stopping condition must be eventually met; a parse error is raised if
        the end of stream is reached.  This option has no effect if no stopping
        conditions are specified.

      - The `stop_condition_message` argument can be used to specify a more
        human-friendly error message to report in case a specified stopping
        condition is not met. E.g., "expected ‘}’ after ..." is probably more
        illuminating than the default message "stopping condition not met...".

      - The `handle_stop_condition_token` argument accepts a callable.  When a
        token stopping condition is met, the given callable is invoked as
        `handle_stop_condition_token(token, latex_walker=latex_walker,
        token_reader=token_reader, parsing_state=parsing_state)`, where `token`
        is the token that caused the token stop condition to fire.  This
        callback is typically used to set the `tokenreader`'s position
        appropriately (e.g., past the token that ends a group).

      - The `handle_stop_data` argument accepts a callable.  After a stopping
        condition is met (whether token or nodelist), this callable is invoked
        with the return value of the stop callback function (`stop_data`) as
        argument.  This enables the stop condition callback to specify more
        detailed information about what caused the processing to stop.  The
        callback is invoked with the syntax `handle_stop_data(stop_data,
        latex_walker=latex_walker, token_reader=token_reader,
        parsing_state=parsing_state)`.
    """
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


    def make_nodes_collector(self, latex_walker, token_reader, parsing_state):
        r"""
        Create the nodes collector instance that will do the main parsing.
        """
        return latex_walker.make_nodes_collector(
            token_reader=token_reader,
            parsing_state=parsing_state,
            stop_token_condition=self.stop_token_condition,
            stop_nodelist_condition=self.stop_nodelist_condition,
            make_child_parsing_state=self.make_child_parsing_state,
            include_stop_token_pre_space_chars=self.include_stop_token_pre_space_chars,
        )

    def parse(self, latex_walker, token_reader, parsing_state, **kwargs):
        r"""
        The main parsing routine.  The nodes collector instance is created using
        `self.make_nodes_collector()`.

        We check that stop conditions are met, if applicable, and call the
        relevant handlers.
        """

        pos_start = token_reader.cur_pos()

        collector = self.make_nodes_collector(latex_walker, token_reader, parsing_state)

        try:

            collector.process_tokens()

        except LatexWalkerParseError as e:

            # we got an error! Add some info to help with recovery in case
            # we're in tolerant parsing mode, and then raise the issue
            # further up.
            #
            
            logger.debug("Got parse error while reading general nodes: %r", e)

            thenodelist = collector.get_final_nodelist()
            if thenodelist.pos is None:
                thenodelist.pos = pos_start
            if thenodelist.pos_end is None:
                thenodelist.pos_end = pos_start

            raise LatexWalkerNodesParseError(
                msg=e.msg,
                pos=e.pos,
                open_contexts=e.open_contexts,
                error_type_info=e.error_type_info,
                recovery_nodes=thenodelist,
                recovery_parsing_state_delta=collector.get_parser_parsing_state_delta(),
            )

        collected_nodelist = collector.get_final_nodelist()
        if collected_nodelist.pos is None:
            collected_nodelist.pos = pos_start
        if collected_nodelist.pos_end is None:
            collected_nodelist.pos_end = pos_start


        # check that any required stop condition was met

        stop_token_condition_met = collector.stop_token_condition_met()
        stop_nodelist_condition_met = collector.stop_nodelist_condition_met()

        if not self.require_stop_condition_met:
            # no condition to meet
            met_a_required_stop_condition = True
        else:
            met_a_required_stop_condition = False
            if self.stop_token_condition is not None:
                if stop_token_condition_met:
                    met_a_required_stop_condition = True
            elif self.stop_nodelist_condition is not None:
                if stop_nodelist_condition_met:
                    met_a_required_stop_condition = True
            else:
                # there were no stopping conditions set
                met_a_required_stop_condition = True

        logger.debug("finished parsing general nodes; "
                     "self.require_stop_condition_met=%r, "
                     "stop_token_condition=%r, stop_token_condition_met=%r, "
                     "stop_nodelist_condition=%r, stop_nodelist_condition_met=%r;"
                     "met_a_required_stop_condition=%r",
                     self.require_stop_condition_met,
                     self.stop_token_condition, stop_token_condition_met,
                     self.stop_nodelist_condition, stop_nodelist_condition_met,
                     met_a_required_stop_condition)

        if not met_a_required_stop_condition:
            #
            message = self.stop_condition_message
            if message is None:
                message = (
                    'End of stream encountered while parsing nodes without '
                    'stop condition being met [reporting starting position]'
                )
            exc = LatexWalkerNodesParseError(
                msg=message,
                pos=collector.pos_start(),
                recovery_nodes=collected_nodelist,
                recovery_parsing_state_delta=collector.get_parser_parsing_state_delta(),
                error_type_info={
                    'what': 'nodes_generalnodes_required_stop_condition_not_met',
                    'stop_condition_message': self.stop_condition_message
                },
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

        nodelist = collected_nodelist
        parsing_state_delta = collector.get_parser_parsing_state_delta()

        logger.debug("parser - we got final nodelist - %r", nodelist)

        return nodelist, parsing_state_delta



# ------------------------------------------------------------------------------


class LatexSingleNodeParser(LatexGeneralNodesParser):
    r"""
    A parser that collects a single logical node.

    Inherits :py:class:`LatexGeneralNodesParser`.  Additional keyword arguments
    are provided to the :py:class:`LatexGeneralNodesParser` constructor.

    This class is a simple `LatexGeneralNodesParser` where the stopping
    condition is set to whenever the node list reaches one node.  (If
    `stop_on_comment` is `False`, then we don't count comment nodes).

    The parser always returns a node list, and never a single node instance.

    If the end of stream is reached, an empty node list is returned.

    Arguments:
    
      - `stop_on_comment`: If `True`, then a single comment node will count as a
        single node read.  If `False`, then processing will continue until a
        non-comment node is reached.
    """
    def __init__(self, stop_on_comment=True, **kwargs):
        super(LatexSingleNodeParser, self).__init__(
            stop_nodelist_condition=self._stop_nodelist_condition,
            require_stop_condition_met=False,
            **kwargs
        )
        self.stop_on_comment = stop_on_comment
        
    def _stop_nodelist_condition(self, nodelist):
        nl = nodelist
        if not self.stop_on_comment:
            nl = [n for n in nl if not n.isNodeType(nodes.LatexCommentNode)]
        if len(nl) >= 1:
            return True
        return False

    def contents_can_be_empty(self):
        r"""
        Return `False`, because no content would not satisfy the requirements of
        this parser.
        """
        return False





