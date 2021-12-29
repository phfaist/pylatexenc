


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

        helper = _LatexGeneralNodesParserHelper(self,
                                                latex_walker,
                                                token_reader,
                                                parsing_state)

        while True:

            try:

                self._read_and_process_one_token_handle_eos(helper)

            except (_WeSimplyReachedEndOfStream,_WeReachedAStoppingCondition) as e:
                # all good! Return the node list that we got.
                pos_start = helper.pos_start()
                return LatexNodeList(
                    nodelist=helper.nodelist,
                    parsing_state=parsing_state,
                    pos=pos_start,
                    len=e.pos_end - pos_start
                )

            except LatexWalkerError as e:
                # we got an error! Add some info to help with recovery in case
                # we're in tolerant parsing mode, and then raise the issue
                # further up.
                helper.finalize()
                pos_start = helper.pos_start()
                pos_end = helper.pos_end()
                len_ = \
                    None if (pos_start is None or pos_end is None) else (pos_end - pos_start)
                e.recovery_nodes = LatexNodeList(
                    nodelist=helper.nodelist,
                    parsing_state=parsing_state,
                    pos=pos_start,
                    len=len_
                )
                raise



    def _read_and_process_one_token_handle_eos(self, helper):

        try:

            helper.read_and_process_one_token()

        except LatexWalkerEndOfStream as e:

            helper.finalize()

            if ( self.require_stop_condition_met and
                 ( ( self.stop_token_condition is not None
                     and not helper.stop_token_condition_met )
                   or ( self.stop_nodelist_condition is not None
                        and not helper.stop_nodelist_condition_met ) )
                ):
                #
                message = self.stop_condition_message
                if message is None:
                    message = (
                        'End of stream encountered while parsing nodes without '
                        'stop condition being met'
                    )
                exc = LatexWalkerParseError(msg=message, pos=helper.pos_start())
                exc.recovery_nodes = LatexNodeList(helper.nodelist)
                raise exc

            raise _WeSimplyReachedEndOfStream()





class _WeSimplyReachedEndOfStream(Exception):
    pass

class _WeReachedAStoppingCondition(Exception):
    pass


class _LatexGeneralNodesParserHelper:

    def __init__(self, parserobj, latex_walker, token_reader, parsing_state):
        self.parserobj = parserobj
        self.latex_walker = latex_walker
        self.token_reader = token_reader

        self.stop_token_condition_met = False
        self.stop_nodelist_condition_met = False

        # current parsing state. This attribute might change as we parse tokens
        # and nodes.
        self.parsing_state = parsing_state

        # a node list that we are building
        self.nodelist = []

        # characters that we are accumulating
        self.pending_chars_pos = None
        self.pending_chars = ''


    def push_pending_chars(self, chars, pos):
        self.pending_chars += chars
        if self.pending_chars_pos is None:
            self.pending_chars_pos = pos

    def flush_pending_chars(self):
        charspos, chars = self.pending_chars_pos, self.pending_chars
        self.pending_chars = ''
        self.pending_chars_pos = None

        strnode = latex_walker.make_node(LatexCharsNode,
                                         parsing_state=self.parsing_state,
                                         chars=chars+tok.pre_space,
                                         pos=charspos,
                                         len=tok.pos - charspos)
        return self.push_to_nodelist(strnode)
        
    def finalize(self):
        exc = self.flush_pending_chars()
        if exc is not None:
            raise exc

    def pos_start(self):
        return next([ n.pos for n in self.nodelist if n is not None], None)

    def push_to_nodelist(self, node):
        self.nodelist.append(node)
        exc = self._check_nodelist_stop_condition()
        if exc is not None:
            return exc
        return None

    def _check_nodelist_stop_condition(self):
        stop_nodelist_condition = self.parserobj.stop_nodelist_condition
        if stop_nodelist_condition is not None:
            stop_data = stop_nodelist_condition(self.nodelist)
            if stop_data:
                self.stop_nodelist_condition_met = True
                e = _WeReachedAStoppingCondition()
                e.stop_data = stop_data
                return e

    def _check_token_stop_condition(self, tok):
        stop_token_condition = self.parserobj.stop_token_condition
        if stop_token_condition is not None:
            stop_data = stop_token_condition(tok):
            if stop_data:
                self.stop_token_condition_met = True
                e = _WeReachedAStoppingCondition()
                e.stop_data = stop_data
                return e



    def read_and_process_one_token(self):
        r"""
        Read a single token and process it, recursing into brace blocks and
        environments etc if needed, and appending stuff to nodelist.

        Raises an exception whenever we should stop reading (this might include
        non-error exceptions like `_WeSimplyReachedEndOfStream` or
        `_WeReachedAStoppingCondition`).  This function never returns any value.
        If this function returns, we should continue reading nodes.
        """

        latex_walker = self.latex_walker
        token_reader = self.token_reader

        tok = token_reader.next_token(parsing_state=self.parsing_state)

        # if it's a char, just append it to the stream of last "pending"
        # characters.
        if tok.tok == 'char':
            self.push_pending_chars(
                chars=(tok.pre_space + tok.arg),
                pos=(tok.pos - len(tok.pre_space)),
            )
            return

        # if it's not a char, push the last pending chars into the node list
        # before we do anything else (include the present token's pre_space)
        if self.pending_chars:
            exc = self.flush_pending_chars()
            if stop_exc is not None:
                # rewind to position immediately after the new token's
                # pre_space, because we didn't parse that new token yet but we
                # absorbed its pre_space
                token_reader.rewind_to_pos(tok.pos)
                stop_exc.pos_end = tok.pos
                raise stop_exc

        # If we have pre_space, add a separate chars node that contains the
        # spaces.  We do this seperately, so that latex2text can ignore these
        # groups by default to avoid too much space on the output.  This allows
        # latex2text to implement the `strict_latex_spaces=...` flag correctly.

        elif tok.pre_space:
            spacestrnode = latex_walker.make_node(LatexCharsNode,
                                                  parsing_state=self.parsing_state,
                                                  chars=tok.pre_space,
                                                  pos=tok.pos-len(tok.pre_space),
                                                  len=len(tok.pre_space))
            stop_exc = self.push_to_nodelist(spacestrnode)
            if stop_exc is not None:
                # rewind to position immediately after the new token's
                # pre_space, because we didn't parse that new token yet but we
                # absorbed its pre_space
                token_reader.rewind_to_pos(tok.pos)
                stop_exc.pos_end = tok.pos
                raise stop_exc

        # now, process the encountered token `tok`, keeping in mind that the
        # pre_space has already been dealt with.


        # first, let's check if a token-based stopping condition is met.
        
        stop_exc = self._check_token_stop_condition(tok):
        if stop_exc is not None:
            stop_exc.pos_end = tok.pos + tok.len
            raise stop_exc

        # check for tokens that are illegal in this context

        if tok.tok == 'brace_close':
            raise LatexWalkerParseError(
                msg=("Unexpected mismatching closing delimiter ‘{}’".format(tok.arg)),
                pos=tok.pos,
                recovery_pos=tok.pos+tok.len,
            )

        if tok.tok == 'end_environment':
            raise LatexWalkerParseError(
                msg=("Unexpected closing environment: ‘{}’".format(tok.arg)),
                pos=tok.pos,
                recovery_pos=tok.pos+tok.len,
            )

        if tok.tok in ('mathmode_inline', 'mathmode_display') \
           and tok.arg not in parsing_state._math_delims_info_by_open:
            # an unexpected closing math mode delimiter
            raise LatexWalkerParseError(
                msg="Unexpected closing math mode token ‘{}’".format(
                    tok.arg,
                ),
                pos=tok.pos,
                recovery_pos=tok.pos+tok.len,
            )

        # now we can start parsing the token and taking the appropriate action.

        if tok.tok == 'comment':
            commentnode = latex_walker.make_node(
                LatexCommentNode,
                parsing_state=self.parsing_state,
                comment=tok.arg,
                comment_post_space=tok.post_space,
                pos=tok.pos,
                len=tok.len
            )
            stop_exc = self.push_to_nodelist(spacestrnode)
            if stop_exc is not None:
                stop_exc.pos_end = tok.pos + tok.len
                raise stop_exc

        elif tok.tok == 'brace_open':
            # a braced group.
            groupnode = \
                latex_walker.parse_construct(
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

        elif tok.tok == 'macro':

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
                mspec = macrospec.MacroSpec('')

            self.handle_invocable_token(tok, mspec)
            return

        elif tok.tok == 'begin_environment':
            
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
                envspec = macrospec.EnvironmentSpec('')

            self.handle_invocable_token(tok, envspec)
            return

        elif tok.tok == 'specials':

            specials_spec = tok.arg

            self.handle_invocable_token(tok, specials_spec)
            return

        elif tok.tok in ('mathmode_inline', 'mathmode_display'):

            # a math inline or display environment
            mathnode = \
                latex_walker.parse_construct(
                    LatexMathParser(
                        require_brace_type=tok.arg,
                    ),
                    token_reader=token_reader,
                    parsing_state=self.parsing_state,
            )

            stop_exc = self.push_to_nodelist(mathnode)
            if stop_exc is not None:
                stop_exc.pos_end = mathnode.pos + mathnode.len
                raise stop_exc
            
            return

        else:
            
            raise LatexWalkerParseError(
                "Unknown token type: {}".format(tok.tok),
                pos=tok.pos
            )



    def handle_invocable_token(self, tok, spec, what):

        latex_walker = self.latex_walker
        token_reader = self.token_reader

        if spec.instance_parser is not None:

            result_node = latex_walker.parse_construct(
                lambda *args, **kwargs: \
                    spec.instance_parser(*args, instance_token=tok, **kwargs),
                latex_walker=latex_walker,
                token_reader=token_reader,
                parsing_state=self.parsing_state,
                open_context=( what, tok.pos )
                **kwargs,
            )

        else:

            result_node = latex_walker.parse_construct(
                LatexLegacyThingWithArgumentsParser(
                    invocable_token=tok,
                    spec=spec,
                ),
                token_reader=token_reader,
                parsing_state=self.parsing_state,
                open_context=( "arguments of "+what, tok.pos )
            )

        if result_node is None:
            return

        # see if we should change the current parsing state!
        after_set_parsing_state = getattr(result_node, 'after_set_parsing_state', None)
        if after_set_parsing_state is not None:
            self.parsing_state = after_set_parsing_state

        exc = self.push_to_nodelist(result_node)
        if exc is not None:
            exc.pos_end = result_node.pos + result_node.len
            raise exc





# ------------------------------------------------------------------------------


class LatexLegacyThingWithArgumentsParser(object):
    def __init__(self, invocable_token, spec):
        super(LatexLegacyThingWithArgumentsParser, self).__init__()
        self.invocable_token = invocable_token
        self.spec = spec

        if isinstance(self.spec, MacroSpec):
            self.node_class = LatexMacroNode
        elif isinstance(self.spec, EnvironmentSpec):
            self.node_class = LatexEnvironmentNode
        elif isinstance(self.spec, SpecialsSpec):
            self.node_class = LatexSpecialsNode
        else:
            raise TypeError("Invalid/unknown spec class {!r}".format(self.spec))



    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        # we are immediately after `self.invocable_token`, which expects
        # arguments as specified in the specification instance `spec` (either a
        # MacroSpec, EnvironmentSpec, or SpecialsSpec)
        #
        # Note that this parser is not called for specs that have the
        # `instance_parser` attribute.


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
            node.after_set_parsing_state = new_parsing_state

        return node


    def read_environment_body(self, latex_walker, token_reader, parsing_state):

        environmentname = self.invocable_token.arg

        def stop_token_condition(token, environmentname=environmentname):
            if token.tok == 'end_environment' and token.arg == environmentname:
                return True
            return False

        nodes = latex_walker.parse_construct(
            LatexGeneralNodesParser(
                stop_token_condition=stop_token_condition,
            ),
            token_reader=token_reader,
            parsing_state=parsing_state,
            open_context=(
                'body of ‘{'+environmentname+'}’',
                self.invocable_token.pos
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
                token_reader.rewind_last_token(firsttok)
                return None

            #
            if require_brace_type:
                acceptable_braces = '‘'+require_brace_type+'’'
            else:
                acceptable_braces = ", ".join([
                    '‘'+od+'’'
                    for od,cd in parsing_state.latex_group_delimiters
                ])
            raise LatexWalkerParseError(
                msg='Expected an opening LaTeX delimiter (%s), got ‘%s’' %(
                    acceptable_braces,
                    latex_walker.s[firsttok.pos:firsttok.pos+firsttok.len]
                )
                recovery_nodes=LatexNodeList([]),
                revovery_pos=tok.pos
            )

        brace_type = firsttok.arg
        closing_brace = parsing_state._latex_group_delimchars_by_open[brace_type]

        def stop_token_condition(token):
            if token.tok == 'brace_close' and token.arg == closing_brace:
                return True
            return False

        nodelist = latex_walker.parse_construct(
            LatexGeneralNodesParser(
                stop_token_condition=stop_token_condition,
            ),
            token_reader=token_reader,
            parsing_state=parsing_state,
            open_context=(
                'LaTeX delimited expression ‘{}…{}’'.format(brace_type, closing_brace),
                firsttok.pos
            )
        )

        return latex_walker.make_node(LatexGroupNode,
                                      nodelist=nodelist,
                                      parsing_state=parsing_state,
                                      delimiters=(brace_type, closing_brace),
                                      pos = firsttok.pos,
                                      len = nodelist.pos + nodelist.len - firsttok.pos)





# ------------------------------------------------------------------------------



class _TryAgainWithSkippedCommentNodes(Exception):
    def __init__(self, skipped_comment_nodes, pos):
        super(_TryAgainWithSkippedCommentNodes, self).__init__("<internal>")
        self.skipped_comment_nodes = skipped_comment_nodes
        self.pos = pos



class LatexExpressionParser(object):
    def __init__(self,
                 include_skipped_comments=True,
                 beginend_macro_is_error=True,
                 single_token_requiring_arg_is_error=True,
                 **kwargs
                 ):
        super(LatexExpressionParser, self).__init__(**kwargs)
        self.include_skipped_comments = include_skipped_comments
        self.beginend_macro_is_error = beginend_macro_is_error
        self.single_token_requiring_arg_is_error = single_token_requiring_arg_is_error

    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        expr_parsing_state = parsing_state.sub_context(enable_environments=False)
        
        exprnodes = []
        p = None
        l = None
        while True:
            try:
                moreexprnodes = \
                    self._parse_single_token(latex_walker,
                                             token_reader,
                                             expr_parsing_state,
                                             **kwargs)
            except _TryAgainWithSkippedCommentNodes as e:
                exprnodes += e.skipped_comment_nodes
                if p is None:
                    p = e.pos
                continue

            exprnodes += moreexprnodes
            if p is None:
                p = pp
            l = pp + ll - p

            return LatexNodeList(nodelist=exprnodes, pos=p, len=l,)


    def _parse_single_token(self, latex_walker, token_reader, expr_parsing_state, **kwargs):

        try:
            tok = token_reader.next_token(environments=False,
                                          parsing_state=expr_parsing_state)
        except LatexWalkerTokenParseError as e:
            exc = latex_walker.check_tolerant_parsing_ignore_error(e)
            if exc is not None:
                raise exc

            # recover from error and continue:
            tok = exc.recovery_token_placeholder
            token_reader.jump_to_pos(exc.recovery_pos)


        if tok.tok == 'macro':

            macroname = tok.arg

            if self.beginend_macro_is_error and macroname in ('begin', 'end',):
                # error, we were expecting a single token
                exc = latex_walker.check_tolerant_parsing_ignore_error(
                    LatexWalkerParseError(
                        r"Expected expression, got \{}".format(macroname),
                    )
                )
                if exc is not None:
                    raise exc

                # recover from error ->
                return [
                    latex_walker.make_node(
                        LatexMacroNode,
                        parsing_state=expr_parsing_state,
                        macroname=macroname,
                        spec=None,
                        nodeargd=None,
                        macro_post_space=tok.post_space,
                        nodeoptarg=None,
                        nodeargs=None,
                        pos=tok.pos,
                        len=tok.len
                    )
                ]

            macrospec = expr_parsing_state.latex_context.get_macro_spec(macroname)

            self._check_if_requires_args(latex_walker, macrospec,
                                         r"a single macro ‘\{}’".format(macroname))

            return [
                latex_walker.make_node(
                    LatexMacroNode,
                    parsing_state=expr_parsing_state,
                    macroname=tok.arg,
                    spec=macrospec,
                    nodeargd=None,
                    macro_post_space=tok.post_space,
                    nodeoptarg=None,
                    nodeargs=None,
                    pos=tok.pos,
                    len=tok.len
                )
            ]

        if tok.tok == 'specials':

            specialsspec = tok.arg

            self._check_if_requires_args(latex_walker, specialsspec,
                                         r"specials ‘{}’".format(specialsspec.specials_chars))

            return [
                latex_walker.make_node(
                    LatexSpecialsNode,
                    parsing_state=expr_parsing_state,
                    specials_chars=specialsspec.specials_chars,
                    spec=specialsspec,
                    nodeargd=None,
                    pos=tok.pos,
                    len=tok.len
                )
            ]

        if tok.tok == 'comment':

            if self.include_skipped_comments:
                cnodes = [
                    latex_walker.make_node(LatexCommentNode,
                                           parsing_state=expr_parsing_state,
                                           comment=tok.arg,
                                           comment_post_space=tok.post_space,
                                           pos=tok.pos,
                                           len=tok.len)
                ]
            else:
                cnodes = []

            raise _TryAgainWithSkippedCommentNodes(cnodes, tok.pos)


        if tok.tok == 'brace_open':

            groupnode = latex_walker.parse_construct(
                LatexDelimitedGroupParser(
                    require_brace_type=tok.arg
                ),
                token_reader=token_reader,
                parsing_state=parsing_state,
            )
            return [ groupnode ]

        if tok.tok == 'brace_close':

            raise LatexWalkerParseError(
                msg="Expected LaTeX expression, got closing brace ‘{}’".format(tok.arg),
                pos=tok.pos,
                recovery_nodes=latex_walker.make_node(LatexCharsNode,
                                                      parsing_state=parsing_state,
                                                      chars='',
                                                      pos=tok.pos,
                                                      len=0),
                # don't consume the closing brace if we're trying to recover
                # from the parse error
                recovery_pos=tok.pos
            )

        if tok.tok == 'char':

            return [ latex_walker.make_node(LatexCharsNode,
                                            parsing_state=parsing_state,
                                            chars=tok.arg,
                                            pos=tok.pos,
                                            len=tok.len) ]

        if tok.tok in ('mathmode_inline', 'mathmode_display'):
            
            # I can't think of a good reason why this shouldn't be an error.  If
            # a macro need to handle very special arguments (such as a single $
            # token), then it should provide its own argument parser for that
            # argument.

            # try to figure out a smart recovery node
            if tok.arg.startswith('\\'):
                recovery_nodes = latex_walker.make_node(LatexMacroNode,
                                                        parsing_state=parsing_state,
                                                        macroname=tok.arg,
                                                        nodeoptarg=None,
                                                        nodeargs=None,
                                                        macro_post_space=tok.post_space,
                                                        pos=tok.pos,
                                                        len=tok.len)
            else:
                recovery_nodes = latex_walker.make_node(LatexCharsNode,
                                                        parsing_state=parsing_state,
                                                        chars=tok.arg,
                                                        pos=tok.pos,
                                                        len=tok.len)
                
            raise LatexWalkerParseError(
                "Unexpected math mode delimiter ‘{}’, was expecting a LaTeX expression"
                .format(tok.arg),
                pos=tok.pos,
                recovery_nodes=recovery_nodes,
                recovery_pos=tok.pos+tok.len
            )

        raise LatexWalkerParseError(
            "Unknown token type: ‘{}’".format(tok.tok),
            pos=tok.pos
        )


    def _check_if_requires_args(self, latex_walker, spec, what_we_got):

        if self.single_token_requiring_arg_is_error \
           and spec.needs_arguments():
            exc = latex_walker.check_tolerant_parsing_ignore_error(
                LatexWalkerParseError(
                    (r"Expected a LaTeX expression but got {} which "
                     r"expects arguments; did you mean to provide an expression "
                     r"in {{curly braces}} ?").format(what_we_got),
                )
            )
            if exc is not None:
                raise exc




# ------------------------------------------------------------------------------


