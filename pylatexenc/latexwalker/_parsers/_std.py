
from __future__ import print_function, unicode_literals, absolute_imports

from ...macrospec._specclasses import MacroSpec, EnvironmentSpec, SpecialsSpec

from ._nodescollectorbase import LatexNodesCollectorBase


# ------------------------------------------------------------------------------


class LatexNodesCollector(LatexNodesCollectorBase):

    def __init__(
            self,
            latex_walker,
            token_reader,
            parsing_state,
            stop_token_condition=None,
            stop_nodelist_condition=None
    ):
        super(LatexNodesCollector, self).__init__(
            latex_walker=latex_walker,
            token_reader=token_reader,
            parsing_state=parsing_state,
            stop_token_condition=stop_token_condition,
            stop_nodelist_condition=stop_nodelist_condition
        )


    def parse_latex_group(self, tok):
        groupnode = \
            latex_walker.parse_content(
                LatexDelimitedGroupParser(
                    require_brace_type=tok.arg,
                ),
                token_reader=token_reader,
                parsing_state=self.parsing_state,
        )

        stop_exc = self.push_to_nodelist(groupnode)
        if stop_exc is not None:
            stop_exc.pos_end = groupnode.pos + groupnode.len
            raise stop_exc


    def parse_macro(self, tok):

        macroname = tok.arg
        mspec = tok.spec
        if mspec is None:
            mspec = self.parsing_state.latex_context.get_macro_spec(macroname)
        if mspec is None:
            exc = latex_walker.check_tolerant_parsing_ignore_error(
                LatexWalkerParseError(
                    msg=r"Encountered unknown macro ‘\{}’".format(macroname),
                    pos=tok.pos
                )
            )
            if exc is not None:
                raise exc
            mspec = MacroSpec('')

        return self.parse_invocable_token_type(tok, mspec)


    def parse_environment(self, tok):

        environmentname = tok.arg
        envspec = tok.spec
        if envspec is None:
            envspec = \
                self.parsing_state.latex_context.get_environment_spec(environmentname)

        if envspec is None:
            exc = latex_walker.check_tolerant_parsing_ignore_error(
                LatexWalkerParseError(
                    msg=r"Encountered unknown environment ‘{{{}}}’".format(environmentname),
                    pos=tok.pos
                )
            )
            if exc is not None:
                raise exc
            envspec = EnvironmentSpec('')

        return self.parse_invocable_token_type(tok, envspec)


    def parse_specials(self, tok):
        specials_spec = tok.arg
        return self.parse_invocable_token_type(tok, specials_spec)


    def parse_comment_node(self, tok):

        commentnode = latex_walker.make_node(
                LatexCommentNode,
                parsing_state=self.parsing_state,
                comment=tok.arg,
                comment_post_space=tok.post_space,
                pos=tok.pos,
                len=tok.len
        )

        stop_exc = self.push_to_nodelist( commentnode )
        if stop_exc is not None:
            stop_exc.pos_end = tok.pos + tok.len
            raise stop_exc




    def parse_invocable_token_type(self, tok, spec):

        latex_walker = self.latex_walker
        token_reader = self.token_reader

        result_node, carryover_info = latex_walker.parse_content(
            LatexInvocableWithArgumentsParser(
                main_token=tok,
                spec=spec,
            ),
            token_reader=token_reader,
            parsing_state=self.parsing_state,
        )

        self.update_state_from_carryover_info(carryover_info)

        if result_node is None:
            return

        exc = self.push_to_nodelist(result_node)
        if exc is not None:
            exc.pos_end = result_node.pos + result_node.len
            raise exc


    



# ------------------------------------------------------------------------------


class LatexGeneralNodesParser(object):
    def __init__(self,
                 stop_token_condition=None,
                 stop_nodelist_condition=None,
                 require_stop_condition_met=True,
                 stop_condition_message=None
                 **kwargs):
        super(LatexGeneralNodesParser, self).__init__(**kwargs)
        self.stop_token_condition = stop_token_condition
        self.stop_nodelist_condition = stop_nodelist_condition
        # no effect if conditions are None:
        self.require_stop_condition_met = require_stop_condition_met
        self.stop_condition_message = stop_condition_message

    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        collector = LatexNodesCollector(
            latex_walker=latex_walker,
            token_reader=token_reader,
            parsing_state=parsing_state,
            stop_token_condition=self.stop_token_condition,
            stop_nodelist_condition=self.stop_nodelist_condition,
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


class LatexInvocableWithArgumentsParser(object):
    def __init__(self, main_token, spec):
        super(LatexInvocableWithArgumentsParser, self).__init__()
        self.main_token = main_token
        self.spec = spec

        if isinstance(self.spec, MacroSpec):
            self.node_class = LatexMacroNode
            self.what = 'macro ‘\\{}’'.format(self.main_token.arg)
        elif isinstance(self.spec, EnvironmentSpec):
            self.node_class = LatexEnvironmentNode
            self.what = 'environment ‘{{{}}}’'.format(self.main_token.arg)
        elif isinstance(self.spec, SpecialsSpec):
            self.node_class = LatexSpecialsNode
            self.what = 'specials ‘{}’'.format(self.main_token.arg.specials_chars)
        else:
            raise TypeError("Invalid/unknown spec class {!r}".format(self.spec))

    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        if spec.instance_parser is not None:

            return latex_walker.parse_content(
                lambda *args, **kwargs: \
                    spec.instance_parser(*args, instance_token=tok, **kwargs),
                latex_walker=latex_walker,
                token_reader=token_reader,
                parsing_state=self.parsing_state,
                open_context=( self.what, self.main_token )
                **kwargs,
            )

        else:

            with latex_walker.new_parser_open_context( ('arguments of ' + self.what,
                                                        self.main_token) ) as pc:

                return self._legacy_args_parse(latex_walker, token_reader,
                                               parsing_state, **kwargs)

            if pc.recovery_from_exception is not None:
                return pc.perform_recovery_nodes_info(token_reader)


    def _legacy_args_parse(self, latex_walker, token_reader, parsing_state, **kwargs):

        # we are immediately after `self.main_token`, which expects
        # arguments as specified in the specification instance `spec` (either a
        # MacroSpec, EnvironmentSpec, or SpecialsSpec)
        #
        # Note that this parser is not called for specs that have the
        # `instance_parser` attribute.

        tok = self.main_token

        # FIXME: this is still the legacy call, we might want to update this at
        # some point for some updated macro arguments parser.

        argsresult = \
            spec.parse_args(w=latex_walker, pos=tok.pos + tok.len,
                            parsing_state=p.parsing_state)

        if len(argsresult) == 4:
            (nodeargd, apos, alen, adic) = argsresult
        else:
            (nodeargd, apos, alen) = argsresult
            adic = {}

        pos_end = apos + alen
        token_reader.jump_to_pos(pos_end)

        if nodeargd is not None and nodeargd.legacy_nodeoptarg_nodeargs:
            legnodeoptarg = nodeargd.legacy_nodeoptarg_nodeargs[0]
            legnodeargs = nodeargd.legacy_nodeoptarg_nodeargs[1]
        else:
            legnodeoptarg, legnodeargs = None, []


        new_parsing_state = adic.get('new_parsing_state', None)
        inner_parsing_state = adic.get('inner_parsing_state', None)

        nodekwargs = {}

        if self.node_class is LatexEnvironmentNode:
            if inner_parsing_state is None:
                inner_parsing_state = parsing_state
            if spec.is_math_mode:
                inner_parsing_state = inner_parsing_state.sub_context(
                    in_math_mode=True,
                    math_mode_delimiter='{'+environmentname+'}',
                )
            nodelist, npos, nlen = \
                self.read_environment_body(latex_walker, token_reader, inner_parsing_state)

            nodekwargs['nodelist'] = nodelist
            pos_end = npos + nlen

        node = latex_walker.make_node(
            self.node_class,
            parsing_state=p.parsing_state,
            macroname=tok.arg,
            nodeargd=nodeargd,
            macro_post_space=tok.post_space,
            # legacy data:
            nodeoptarg=legnodeoptarg,
            nodeargs=legnodeargs,
            # pos/len:
            pos=tok.pos,
            len=pos_end-tok.pos,
            # per-node-type stuff:
            **nodekwargs
        )

        if new_parsing_state is not None:
            carryover_info['set_parsing_state'] = new_parsing_state

        return node, carryover_info


    def read_environment_body(self, latex_walker, token_reader, parsing_state):

        environmentname = self.main_token.arg

        def stop_token_condition(token, environmentname=environmentname):
            if token.tok == 'end_environment' and token.arg == environmentname:
                return True
            return False

        nodes = latex_walker.parse_content(
            LatexGeneralNodesParser(
                stop_token_condition=stop_token_condition,
            ),
            token_reader=token_reader,
            parsing_state=parsing_state,
            open_context=(
                'body of ‘{'+environmentname+'}’',
                self.main_token
            )
        )

        return nodes


# ------------------------------------------------------------------------------



class LatexDelimitedGroupParser(object):
    def __init__(self, require_brace_type, optional=False, **kwargs):
        super(LatexDelimitedGroupParser, self).__init__(**kwargs)
        self.require_brace_type = require_brace_type
        self.optional = optional


    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        firsttok = token_reader.next_token(pos, parsing_state=parsing_state)

        if firsttok.tok != 'brace_open'  \
           or (require_brace_type is not None and firsttok.arg != require_brace_type):

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
                    for (od, cd) in parsing_state.latex_group_delimiters
                ])
            raise LatexWalkerParseError(
                msg='Expected an opening LaTeX delimiter (%s), got ‘%s’' %(
                    acceptable_braces,
                    latex_walker.s[firsttok.pos:firsttok.pos+firsttok.len]
                )
                recovery_nodes=LatexNodeList([]),
                recovery_at_token=tok
            )

        brace_type = firsttok.arg
        closing_brace = parsing_state._latex_group_delimchars_by_open[brace_type]

        def stop_token_condition(token):
            if token.tok == 'brace_close' and token.arg == closing_brace:
                return True
            return False

        nodelist = latex_walker.parse_content(
            LatexGeneralNodesParser(
                stop_token_condition=stop_token_condition,
            ),
            token_reader=token_reader,
            parsing_state=parsing_state,
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





# ------------------------------------------------------------------------------
