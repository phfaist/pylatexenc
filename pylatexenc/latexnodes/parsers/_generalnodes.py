
from __future__ import print_function, unicode_literals


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
                 **kwargs):
        super(LatexGeneralNodesParser, self).__init__(**kwargs)
        self.stop_token_condition = stop_token_condition
        self.stop_nodelist_condition = stop_nodelist_condition
        # no effect if conditions are None:
        self.require_stop_condition_met = require_stop_condition_met
        self.stop_condition_message = stop_condition_message
        # parsing state for child nodes
        self.child_parsing_state = child_parsing_state

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
            stop_token_condition=self.stop_token_condition,
            stop_nodelist_condition=self.stop_nodelist_condition,
            make_child_parsing_state=make_child_parsing_state,
        )

        while True:

            try:

                self._read_and_process_one_token_handle_eos(collector)

            except (LatexNodesCollector.ReachedEndOfStream,
                    LatexNodesCollector.ReachedStoppingCondition) as e:
                # all good! Return the node list that we got.
                pos_start = collector.pos_start()
                nodelist = collector.get_final_nodelist()
                return LatexNodeList(
                    nodelist=nodelist,
                    parsing_state=parsing_state,
                    pos=pos_start,
                    len=e.pos_end - pos_start
                ), collector.get_parser_carryover_info()

            except LatexWalkerError as e:
                # we got an error! Add some info to help with recovery in case
                # we're in tolerant parsing mode, and then raise the issue
                # further up.
                collector.finalize()
                nodelist = collector.get_final_nodelist()
                pos_start = collector.pos_start()
                pos_end = collector.pos_end()
                len_ = \
                    None if (pos_start is None or pos_end is None) else (pos_end - pos_start)
                e.recovery_nodes = LatexNodeList(
                    nodelist=nodelist,
                    parsing_state=parsing_state,
                    pos=pos_start,
                    len=len_
                )
                e.carryover_info = collector.get_parser_carryover_info()
                raise


    def _read_and_process_one_token_handle_eos(self, collector):

        try:

            collector.read_and_process_one_token()

        except LatexWalkerEndOfStream as e:

            collector.finalize()

            if ( self.require_stop_condition_met and
                 ( ( self.stop_token_condition is not None
                     and not collector.stop_token_condition_met )
                   or ( self.stop_nodelist_condition is not None
                        and not collector.stop_nodelist_condition_met ) )
                ):
                #
                message = self.stop_condition_message
                if message is None:
                    message = (
                        'End of stream encountered while parsing nodes without '
                        'stop condition being met'
                    )
                exc = LatexWalkerParseError(msg=message, pos=collector.pos_start())
                exc.recovery_nodes = LatexNodeList(collector.nodelist)
                raise exc

            raise LatexNodesCollector.ReachedEndOfStream()


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


    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        if self.include_brace_chars:
            this_level_parsing_state = parsing_state.sub_context(
                latex_group_delimiters= \
                    parsing_state.latex_group_delimiters + [include_brace_chars]
            )

        firsttok = token_reader.next_token(pos, parsing_state=this_level_parsing_state)

        if firsttok.tok != 'brace_open'  \
           or (require_brace_type is not None and firsttok.arg != require_brace_type) \
           or (self.do_not_skip_space and firsttok.pre_space):

            if self.optional:
                # all ok, the argument was optional and was simply not specified.
                token_reader.move_to_token(firsttok)
                return None

            #
            if require_brace_type:
                acceptable_braces = '‘' + require_brace_type + '’'
            else:
                acceptable_braces = ", ".join([
                    '‘' + od + '’'
                    for (od, cd) in this_level_parsing_state.latex_group_delimiters
                ])
            what_we_got = latex_walker.s[firsttok.pos:firsttok.pos+firsttok.len]
            raise LatexWalkerParseError(
                msg='Expected an opening LaTeX delimiter (%s), got ‘%s’%s' %(
                    acceptable_braces,
                    what_we_got
                    ' with leading whitespace' if firsttok.pre_space else ''
                )
                recovery_nodes=LatexNodeList([]),
                recovery_at_token=firsttok
            )

        brace_type = firsttok.arg
        closing_brace = this_level_parsing_state._latex_group_delimchars_by_open[brace_type]

        def stop_token_condition(token):
            if token.tok == 'brace_close' and token.arg == closing_brace:
                return True
            return False

        nodelist = latex_walker.parse_content(
            LatexGeneralNodesParser(
                stop_token_condition=stop_token_condition,
                child_parsing_state=parsing_state,
            ),
            token_reader=token_reader,
            parsing_state=this_level_parsing_state,
            open_context=(
                'LaTeX delimited expression ‘{}…{}’'.format(brace_type, closing_brace),
                firsttok
            )
        )

        return latex_walker.make_node(LatexGroupNode,
                                      nodelist=nodelist,
                                      parsing_state=parsing_state,
                                      delimiters=(brace_type, closing_brace),
                                      pos = firsttok.pos,
                                      len = nodelist.pos + nodelist.len - firsttok.pos)



