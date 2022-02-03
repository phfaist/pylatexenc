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
from .._nodetypes import *

from .._nodescollector import LatexNodesCollector


from ._base import LatexParserBase


# ------------------------------------------------------------------------------

class LatexGeneralNodesParser(LatexParserBase):
    def __init__(self,
                 stop_token_condition=None,
                 stop_nodelist_condition=None,
                 require_stop_condition_met=True,
                 stop_condition_message=None,
                 child_parsing_state=None,
                 handle_stop_condition_token=None,
                 **kwargs):
        super(LatexGeneralNodesParser, self).__init__(**kwargs)
        self.stop_token_condition = stop_token_condition
        self.stop_nodelist_condition = stop_nodelist_condition
        # no effect if conditions are None:
        self.require_stop_condition_met = require_stop_condition_met
        self.stop_condition_message = stop_condition_message
        # parsing state for child nodes
        self.child_parsing_state = child_parsing_state
        # 
        self.handle_stop_condition_token = handle_stop_condition_token


    def _make_child_parsing_state(self, parsing_state, node_class):
        return self.child_parsing_state


    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        if self.child_parsing_state is not None:
            make_child_parsing_state = self._make_child_parsing_state
        else:
            make_child_parsing_state = None

        collector = latex_walker.make_nodes_collector(
            latex_walker=latex_walker,
            token_reader=token_reader,
            parsing_state=parsing_state,
            make_group_parser=LatexDelimitedGroupParser,
            make_math_parser=LatexMathParser,
            stop_token_condition=self.stop_token_condition,
            stop_nodelist_condition=self.stop_nodelist_condition,
            make_child_parsing_state=make_child_parsing_state,
        )

        try:
            collector.process_tokens()

        except LatexWalkerParseError as e:
            # we got an error! Add some info to help with recovery in case
            # we're in tolerant parsing mode, and then raise the issue
            # further up.
            raise LatexWalkerNodesParseError.new_from(
                e,
                recovery_nodes=collector.get_final_nodelist(),
                recovery_carryover_info=collector.get_parser_carryover_info(),
            )

        # check that any required stop condition was met

        if ( self.require_stop_condition_met and
             ( ( self.stop_token_condition is not None
                 and not collector.stop_token_condition_met() )
               or ( self.stop_nodelist_condition is not None
                    and not collector.stop_nodelist_condition_met() ) )
            ):
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

        if self.stop_token_condition is not None \
           and self.handle_stop_condition_token is not None:
            # do something with the token that caused the stop condition to fire
            self.handle_stop_condition_token(
                collector.stop_token_condition_met_token()
            )
            # and 

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
    def __init__(self,
                 require_brace_type,
                 include_brace_chars=None,
                 optional=False,
                 do_not_skip_space=False,
                 **kwargs):
        super(LatexDelimitedGroupParser, self).__init__(**kwargs)
        self.require_brace_type = require_brace_type
        self.include_brace_chars = include_brace_chars
        self.optional = optional
        self.do_not_skip_space = do_not_skip_space


    def contents_can_be_empty(self):
        return self.optional


    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        if self.include_brace_chars:
            this_level_parsing_state = parsing_state.sub_context(
                latex_group_delimiters= \
                    parsing_state.latex_group_delimiters + list(self.include_brace_chars)
            )
        else:
            this_level_parsing_state = parsing_state

        firsttok = token_reader.next_token(parsing_state=this_level_parsing_state)

        require_brace_type = self.require_brace_type

        if require_brace_type not in this_level_parsing_state._latex_group_delimchars_by_open:
            logger.warning("Required opening brace ‘%s’ is not a valid brace type; "
                           "delimiters = %s",
                           require_brace_type,
                           this_level_parsing_state.latex_group_delimiters)

        if firsttok.tok != 'brace_open'  \
           or (require_brace_type is not None and firsttok.arg != require_brace_type) \
           or (self.do_not_skip_space and firsttok.pre_space):

            if self.optional:
                # all ok, the argument was optional and was simply not specified.
                token_reader.move_to_token(firsttok)
                return None, None

            #
            if require_brace_type:
                acceptable_braces = '‘' + require_brace_type + '’'
            else:
                acceptable_braces = ", ".join([
                    '‘' + od + '’'
                    for (od, cd) in this_level_parsing_state.latex_group_delimiters
                ])
            raise LatexWalkerNodesParseError(
                msg='Expected an opening LaTeX delimiter (%s), got %s/‘%s’%s' %(
                    acceptable_braces,
                    firsttok.tok, firsttok.arg,
                    ' with leading whitespace' if firsttok.pre_space else ''
                ),
                recovery_nodes=LatexNodeList([]),
                recovery_at_token=firsttok
            )

        brace_type = firsttok.arg
        closing_brace = this_level_parsing_state._latex_group_delimchars_by_open[brace_type]

        def stop_token_condition(token):
            if token.tok == 'brace_close' and token.arg == closing_brace:
                return True
            return False

        def handle_stop_condition_token(token):
            assert token.tok == 'brace_close'            
            token_reader.move_past_token(token)


        nodelist, carryover_info = latex_walker.parse_content(
            LatexGeneralNodesParser(
                stop_token_condition=stop_token_condition,
                child_parsing_state=parsing_state,
                require_stop_condition_met=True,
                handle_stop_condition_token=handle_stop_condition_token,
            ),
            token_reader=token_reader,
            parsing_state=this_level_parsing_state,
            open_context=(
                'LaTeX delimited expression ‘{}…{}’'.format(brace_type, closing_brace),
                firsttok
            )
        )

        # can discard the carryover_info since the parsing state gets reset at
        # the end of the group.

        groupnode = \
            latex_walker.make_node(LatexGroupNode,
                                   nodelist=nodelist,
                                   parsing_state=this_level_parsing_state,
                                   delimiters=(brace_type, closing_brace),
                                   pos = firsttok.pos,
                                   # use cur_pos() to include the closing brace
                                   len = token_reader.cur_pos() - firsttok.pos)

        return groupnode, None







# ------------------------------------------------------------------------------




class LatexMathParser(LatexParserBase):
    def __init__(self,
                 require_math_mode_delimiter=None,
                 do_not_skip_space=False,
                 optional=False,
                 already_read_firsttok=None,
                 **kwargs):
        super(LatexMathParser, self).__init__(**kwargs)
        self.require_math_mode_delimiter = require_math_mode_delimiter
        self.do_not_skip_space = do_not_skip_space
        self.optional = optional
        self.already_read_firsttok = already_read_firsttok


    def contents_can_be_empty(self):
        return self.optional


    def get_math_parsing_state(self, parsing_state, math_mode_delimiter):
        return parsing_state.sub_context(in_math_mode=True,
                                         math_mode_delimiter=math_mode_delimiter)


    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        if self.already_read_firsttok is not None:
            firsttok = self.already_read_firsttok
        else:
            firsttok = token_reader.next_token(parsing_state=parsing_state)

        require_math_mode_delimiter = self.require_math_mode_delimiter

        if firsttok.tok not in ('mathmode_inline', 'mathmode_display')  \
           or (require_math_mode_delimiter is not None
               and firsttok.arg != require_math_mode_delimiter) \
           or (self.do_not_skip_space and firsttok.pre_space):

            if self.optional:
                # all ok, the argument was optional and was simply not specified.
                token_reader.move_to_token(firsttok)
                return None, None

            #
            if require_math_mode_delimiter:
                acceptable_mm = '‘' + require_math_mode_delimiter + '’'
            else:
                acceptable_mm = ", ".join([
                    '‘' + od + '’'
                    for (od, cd) in (
                            parsing_state.latex_inline_math_mode_delimiters
                            + parsing_state.latex_display_math_mode_delimiters
                    )
                ])
            raise LatexWalkerNodesParseError(
                msg='Expected a LaTeX math mode opening delimiter (%s), got %s/‘%s’%s' %(
                    acceptable_mm,
                    firsttok.tok,
                    firsttok.arg,
                    ' with leading whitespace' if firsttok.pre_space else ''
                ),
                recovery_nodes=LatexNodeList([]),
                recovery_at_token=firsttok
            )

        math_mode_delimiter = firsttok.arg
        math_mode_type = firsttok.tok

        math_parsing_state = self.get_math_parsing_state(parsing_state, math_mode_delimiter)

        closing_math_mode_delim = \
            math_parsing_state._math_expecting_close_delim_info['close_delim']
        
        def stop_token_condition(token):
            if token.tok == math_mode_type and token.arg == closing_math_mode_delim:
                return True
            return False

        nodelist, carryover_info = latex_walker.parse_content(
            LatexGeneralNodesParser(
                stop_token_condition=stop_token_condition,
                #child_parsing_state=parsing_state, # ??? why ???
            ),
            token_reader=token_reader,
            parsing_state=math_parsing_state,
            open_context=(
                'LaTeX math ‘{}…{}’'.format(math_mode_delimiter, closing_math_mode_delim),
                firsttok
            )
        )

        if math_mode_type == 'mathmode_inline':
            displaytype = 'inline'
        elif math_mode_type == 'mathmode_display':
            displaytype = 'display'
        else:
            displaytype = '<unknown>'

        len_ = None
        if nodelist is not None and nodelist.pos is not None and nodelist.len is not None:
            len_ = nodelist.pos + nodelist.len - firsttok.pos

        node = latex_walker.make_node(
            LatexMathNode,
            displaytype=displaytype,
            nodelist=nodelist,
            parsing_state=parsing_state,
            delimiters=(math_mode_delimiter, closing_math_mode_delim),
            pos = firsttok.pos,
            len = len_
        )

        return node, carryover_info


