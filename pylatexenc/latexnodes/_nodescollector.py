# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2019 Philippe Faist
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

from ._exctypes import *
from ._nodetypes import *


from ._carryoverinfo import CarryoverInformation


class LatexNodesCollector(object):

    class ReachedEndOfStream(Exception):
        pass

    class ReachedStoppingCondition(Exception):
        def __init__(self, stop_data, **kwargs):
            super(LatexNodesCollector.ReachedStoppingCondition, self).__init__(**kwargs)
            self.stop_data = stop_data


    def __init__(self,
                 latex_walker,
                 token_reader,
                 parsing_state,
                 make_group_parser,
                 make_math_parser,
                 stop_token_condition=None,
                 stop_nodelist_condition=None,
                 make_child_parsing_state=None,
                 ):

        super(LatexNodesCollector, self).__init__()

        self.latex_walker = latex_walker
        self.token_reader = token_reader

        self.stop_token_condition = stop_token_condition
        self.stop_nodelist_condition = stop_nodelist_condition

        self.stop_token_condition_met = False
        self.stop_nodelist_condition_met = False

        self.make_group_parser = make_group_parser # like "LatexDelimitedGroupParser"
        self.make_math_parser = make_math_parser # like "LatexMathParser"

        # current parsing state. This attribute might change as we parse tokens
        # and nodes.
        self.parsing_state = parsing_state

        # a node list that we are building
        self._nodelist = []

        # characters that we are accumulating
        self._pending_chars_pos = None
        self._pending_chars = ''

        # whether finalize() was called or not
        self._finalized = False

        # override custom function to make the child parsing state
        if make_child_parsing_state is not None:
            self.make_child_parsing_state = make_child_parsing_state


    def make_child_parsing_state(self, parsing_state, node_class):
        return self.parsing_state

    def push_pending_chars(self, chars, pos):
        self._pending_chars += chars
        if self._pending_chars_pos is None:
            self._pending_chars_pos = pos

    def flush_pending_chars(self):
        if not self._pending_chars:
            # no pending chars to flush
            return None

        charspos, chars = self._pending_chars_pos, self._pending_chars
        self._pending_chars = ''
        self._pending_chars_pos = None

        strnode = self.latex_walker.make_node(
            LatexCharsNode,
            parsing_state=self.parsing_state,
            chars=chars,
            pos=charspos,
            len=len(chars),
        )
        return self.push_to_nodelist(strnode)
        
    def finalize(self):
        if self._finalized:
            return
        self._finalized = True
        exc = self.flush_pending_chars()
        if exc is not None:
            raise exc

    def get_final_nodelist(self):
        self.finalize()
        return self._nodelist

    def get_parser_carryover_info(self):
        if not self._finalized:
            raise RuntimeError("Call to get_parser_carryover_info() before finalize()")

        # report our updated parsing state
        return CarryoverInformation(set_parsing_state=self.parsing_state)


    def pos_start(self):
        r"""
        Returns the first position of nodes in the collected node list (collected up
        to this point).
        """
        p = next( ( n.pos for n in self._nodelist if n is not None ),
                  None )
        if p is not None:
            return p
        return self._pending_chars_pos

    def pos_end(self):
        r"""
        Returns the position immediately after the last node in the collected node
        list (collected up to this point).
        """
        lastnode = next( ( n for n in reversed(self._nodelist) if n is not None ),
                         None )
        if lastnode is None:
            return None
        if lastnode.pos is None or lastnode.len is None:
            return None
        return lastnode.pos + lastnode.len


    def push_to_nodelist(self, node):
        if self._finalized:
            raise RuntimeError("You already called finalize()")

        self._nodelist.append(node)
        exc = self._check_nodelist_stop_condition()
        if exc is not None:
            return exc
        return None

    def _check_nodelist_stop_condition(self):
        stop_nodelist_condition = self.stop_nodelist_condition
        if stop_nodelist_condition is not None:
            stop_data = stop_nodelist_condition(self._nodelist)
            if stop_data:
                self.stop_nodelist_condition_met = True
                return LatexNodesCollector.ReachedStoppingCondition(stop_data=stop_data)

    def _check_token_stop_condition(self, tok):
        stop_token_condition = self.stop_token_condition
        if stop_token_condition is not None:
            stop_data = stop_token_condition(tok)
            if stop_data:
                self.stop_token_condition_met = True
                return LatexNodesCollector.ReachedStoppingCondition(stop_data=stop_data)


    def read_and_process_one_token(self):
        r"""
        Read a single token and process it, recursing into brace blocks and
        environments etc if needed, and appending stuff to nodelist.

        Raises an exception whenever we should stop reading (this might include
        non-error exceptions like `ReachedEndOfStream` or
        `ReachedStoppingCondition`).  This function never returns any value.  If
        this function returns, we should continue reading nodes.
        """

        if self._finalized:
            raise RuntimeError("You already called finalize()")

        latex_walker = self.latex_walker
        token_reader = self.token_reader

        try:

            tok = token_reader.next_token(parsing_state=self.parsing_state)

        except LatexWalkerEndOfStream as e:
            final_space = getattr(e, 'final_space', None)
            if final_space:
                tok = token_reader.make_token(
                    tok='char',
                    arg=final_space,
                    pos=token_reader.cur_pos()-len(final_space),
                    len=len(final_space)
                )
            else:
                exc = LatexNodesCollector.ReachedEndOfStream()
                exc.pos_end = token_reader.cur_pos()
                raise exc


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
        if self._pending_chars:
            self._pending_chars += tok.pre_space
            stop_exc = self.flush_pending_chars()
            if stop_exc is not None:
                # rewind to position immediately after the new token's
                # pre_space, because we didn't parse that new token yet but we
                # absorbed its pre_space
                token_reader.move_to_token(tok)
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
                token_reader.move_to_token(tok)
                stop_exc.pos_end = tok.pos
                raise stop_exc

        # now, process the encountered token `tok`, keeping in mind that the
        # pre_space has already been dealt with.


        # first, let's check if a token-based stopping condition is met.
        
        stop_exc = self._check_token_stop_condition(tok)
        if stop_exc is not None:
            stop_exc.pos_end = tok.pos + tok.len
            raise stop_exc

        # check for tokens that are illegal in this context

        if tok.tok == 'brace_close':
            raise LatexWalkerNodesParseError(
                msg=("Unexpected mismatching closing delimiter ‘{}’".format(tok.arg)),
                pos=tok.pos,
                recovery_past_token=tok,
            )

        if tok.tok == 'end_environment':
            raise LatexWalkerNodesParseError(
                msg=("Unexpected closing environment: ‘{}’".format(tok.arg)),
                pos=tok.pos,
                recovery_past_token=tok,
            )

        if tok.tok in ('mathmode_inline', 'mathmode_display') \
           and tok.arg not in parsing_state._math_delims_info_by_open:
            # an unexpected closing math mode delimiter
            raise LatexWalkerNodesParseError(
                msg="Unexpected closing math mode token ‘{}’".format(
                    tok.arg,
                ),
                pos=tok.pos,
                recovery_past_token=tok,
            )

        # now we can start parsing the token and taking the appropriate action.

        if tok.tok == 'comment':
            self.parse_comment_node(tok)
            return

        elif tok.tok == 'brace_open':
            # a braced group.
            self.parse_latex_group(tok)
            return

        elif tok.tok == 'macro':

            self.parse_macro(tok)
            return

        elif tok.tok == 'begin_environment':
            
            self.parse_environment(tok)
            return

        elif tok.tok == 'specials':

            self.parse_specials(tok)
            return

        elif tok.tok in ('mathmode_inline', 'mathmode_display'):

            self.parse_math(tok)
            return

        else:
            
            raise LatexWalkerParseError(
                "Unknown token type: {}".format(tok.tok),
                pos=tok.pos
            )


    def update_state_from_carryover_info(self, carryover_info):

        if carryover_info is not None:
            self.parsing_state = \
                carryover_info.get_updated_parsing_state(self.parsing_state)




    # ------------------




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

        token_reader.move_to_token(tok)

        groupnode = \
            latex_walker.parse_content(
                self.make_group_parser(
                    require_brace_type=tok.arg,
                ),
                token_reader=self.token_reader,
                parsing_state=self.make_child_parsing_state(self.parsing_state,
                                                            LatexGroupNode),
        )

        stop_exc = self.push_to_nodelist(groupnode)
        if stop_exc is not None:
            stop_exc.pos_end = groupnode.pos + groupnode.len
            raise stop_exc


    def parse_macro(self, tok):

        macroname = tok.arg
        # mspec = tok.spec
        # if mspec is None:
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

        latex_walker = self.latex_walker
        #token_reader = self.token_reader

        environmentname = tok.arg
        # envspec = tok.spec
        # if envspec is None:
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

        if spec is not None:

            node_parser = spec.get_node_parser(tok)

            result_node, carryover_info = latex_walker.parse_content(
                node_parser,
                token_reader=token_reader,
                parsing_state=self.make_child_parsing_state(self.parsing_state, node_class),
                open_context=(what, tok),
            )

        else:
            result_node = None
            carryover_info = None

        self.update_state_from_carryover_info(carryover_info)

        if result_node is None:
            return

        exc = self.push_to_nodelist(result_node)
        if exc is not None:
            exc.pos_end = result_node.pos + result_node.len
            raise exc


    def parse_math(self, tok):

        self.token_reader.move_to_token(tok)

        math_parsing_state = self.parsing_state.sub_context(
            in_math_mode=True,
            math_mode_delimiter=tok.arg
        )

        # a math inline or display environment
        mathnode = \
            latex_walker.parse_content(
                self.make_math_parser(
                    require_math_delimiter=tok.arg,
                ),
                token_reader=self.token_reader,
                parsing_state=self.make_child_parsing_state(math_parsing_state,
                                                            LatexMathNode)
            )

        stop_exc = self.push_to_nodelist(mathnode)
        if stop_exc is not None:
            stop_exc.pos_end = mathnode.pos + mathnode.len
            raise stop_exc
