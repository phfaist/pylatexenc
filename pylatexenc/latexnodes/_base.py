
from __future__ import print_function, unicode_literals, absolute_imports


from ._nodescollectorbase import LatexNodesCollectorBase


# ------------------------------------------------------------------------------


class LatexNodesCollector(LatexNodesCollectorBase):

    def __init__(
            self,
            latex_walker,
            token_reader,
            parsing_state,
            make_child_parsing_state=None,
            stop_token_condition=None,
            stop_nodelist_condition=None,
    ):
        super(LatexNodesCollector, self).__init__(
            latex_walker=latex_walker,
            token_reader=token_reader,
            parsing_state=parsing_state,
            stop_token_condition=stop_token_condition,
            stop_nodelist_condition=stop_nodelist_condition
        )
        self.make_child_parsing_state = make_child_parsing_state


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


    def parse_latex_group(self, tok):

        groupnode = \
            latex_walker.parse_content(
                LatexDelimitedGroupParser(
                    require_brace_type=tok.arg,
                ),
                token_reader=token_reader,
                parsing_state=self.make_child_parsing_state(self.parsing_state),
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
            mspec = None


        node_class = LatexMacroNode
        what = 'macro ‘\\{}’'.format(macroname)

        return self.parse_invocable_token_type(tok, mspec, node_class, what)

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
            envspec = None

        node_class = LatexEnvironmentNode
        what = 'environment ‘{{{}}}’'.format(environmentname)

        return self.parse_invocable_token_type(tok, envspec, node_class, what)

    def parse_specials(self, tok):

        specials_spec = tok.arg

        node_class = LatexSpecialsNode
        what = 'specials ‘{}’'.format(specials_spec.specials_chars)

        return self.parse_invocable_token_type(tok, specials_spec, node_class, what)

    def parse_invocable_token_type(self, tok, spec, node_class, what):

        latex_walker = self.latex_walker
        token_reader = self.token_reader

        result_node, carryover_info = latex_walker.parse_content(
            LatexInvocableWithArgumentsParser(
                main_token=tok,
                spec=spec,
                node_class=node_class,
                what=what,
            ),
            token_reader=token_reader,
            parsing_state=self.make_child_parsing_state(self.parsing_state),
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


class LatexInvocableWithArgumentsParser(object):
    def __init__(self, main_token, spec, node_class, what):
        super(LatexInvocableWithArgumentsParser, self).__init__()
        self.main_token = main_token
        self.spec = spec

        self.node_class = node_class
        self.what = what


    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        if spec.instance_parser is not None:

            return latex_walker.parse_content(
                lambda *pargs, **pkwargs: \
                    .........
                    self.spec.get_instance_parser(*pargs,
                                              main_token=self.main_token,
                                              node_class=self.node_class,
                                              **pkwargs),
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





# ------------------------------------------------------------------------------
