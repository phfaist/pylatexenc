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

from __future__ import print_function, unicode_literals, absolute_imports

from _exctypes import *
from _nodetypes import *


class LatexNodesCollectorBase(object):

    class ReachedEndOfStream(Exception):
        pass

    class ReachedStoppingCondition(Exception):
        def __init__(self, stop_data, **kwargs):
            super(LatexNodesCollector.ReachedStoppingCondition, self).__init__(**kwargs)
            self.stop_data = stop_data


    def __init__(self, latex_walker, token_reader, parsing_state,
                 stop_token_condition=None, stop_nodelist_condition=None):

        super(LatexNodesCollectorBase, self).__init__()

        self.latex_walker = latex_walker
        self.token_reader = token_reader

        self.stop_token_condition = stop_token_condition
        self.stop_nodelist_condition = stop_nodelist_condition

        self.stop_token_condition_met = False
        self.stop_nodelist_condition_met = False

        # current parsing state. This attribute might change as we parse tokens
        # and nodes.
        self.parsing_state = parsing_state

        # a node list that we are building
        self._nodelist = []

        # characters that we are accumulating
        self._pending_chars_pos = None
        self._pending_chars = ''

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

    def get_final_nodelist(self):
        self.finalize()
        return self._nodelist


    def pos_start(self):
        p = next([ n.pos for n in self._nodelist if n is not None], None)
        if p is not None:
            return p
        return self._pending_chars_pos

    def push_to_nodelist(self, node):
        self._nodelist.append(node)
        exc = self._check_nodelist_stop_condition()
        if exc is not None:
            return exc
        return None

    def _check_nodelist_stop_condition(self):
        stop_nodelist_condition = self.parserobj.stop_nodelist_condition
        if stop_nodelist_condition is not None:
            stop_data = stop_nodelist_condition(self._nodelist)
            if stop_data:
                self.stop_nodelist_condition_met = True
                return LatexNodesCollector.ReachedStoppingCondition(stop_data=stop_data)

    def _check_token_stop_condition(self, tok):
        stop_token_condition = self.parserobj.stop_token_condition
        if stop_token_condition is not None:
            stop_data = stop_token_condition(tok):
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
        if self._pending_chars:
            exc = self.flush_pending_chars()
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
        
        stop_exc = self._check_token_stop_condition(tok):
        if stop_exc is not None:
            stop_exc.pos_end = tok.pos + tok.len
            raise stop_exc

        # check for tokens that are illegal in this context

        if tok.tok == 'brace_close':
            raise LatexWalkerParseError(
                msg=("Unexpected mismatching closing delimiter ‘{}’".format(tok.arg)),
                pos=tok.pos,
                recovery_past_token=tok,
            )

        if tok.tok == 'end_environment':
            raise LatexWalkerParseError(
                msg=("Unexpected closing environment: ‘{}’".format(tok.arg)),
                pos=tok.pos,
                recovery_past_token=tok,
            )

        if tok.tok in ('mathmode_inline', 'mathmode_display') \
           and tok.arg not in parsing_state._math_delims_info_by_open:
            # an unexpected closing math mode delimiter
            raise LatexWalkerParseError(
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

            # a math inline or display environment
            mathnode = \
                latex_walker.parse_content(
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


    def update_state_from_carryover_info(self, carryover_info):
    
        # see if we should change the current parsing state!
        if 'new_parsing_state' in carryover_info:
            self.parsing_state = carryover_info['new_parsing_state']
        

