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

from ..latexnodes import LatexMacroNode, LatexEnvironmentNode, LatexSpecialsNode
from ..latexnodes.parsers import LatexParserBase, LatexGeneralNodesParser


# works for macros, environments, and specials.
class _LatexCallableParserBase(LatexParserBase):
    def __init__(self,
                 token_call,
                 spec_object,
                 what,
                 node_class,
                 node_extra_kwargs,
                 parse_body=False,
                 ):

        self.token_call = token_call
        self.spec_object = spec_object
        self.what = what
        self.node_class = node_class
        self.node_extra_kwargs = node_extra_kwargs

        self.arguments_parser = spec_object.arguments_parser

        self.parse_body = parse_body

        self.make_carryover_info = spec_object.make_carryover_info


    def parse_call_arguments(self, latex_walker, token_reader, parsing_state, **kwargs):

        nodeargd, carryover_info = latex_walker.parse_content(
            self.arguments_parser,
            token_reader,
            parsing_state,
            # open_context=(
            #     "Arguments of {}".format(what),
            #     token_reader.cur_pos()
            # )
            **kwargs
        )
        return nodeargd, carryover_info

    def make_body_parser(self, nodeargd, arg_carryover_info):
        raise RuntimeError(
            "No default implementation of make_body_parser() in base class")

    def make_body_parsing_state(self, nodeargd, arg_carryover_info, parsing_state):
        raise RuntimeError(
            "No default implementation of make_body_parsing_state() in base class")

    def parse_call_body(self, nodeargd, arg_carryover_info,
                        latex_walker, token_reader, parsing_state, **kwargs):

        body_parser = self.make_body_parser(nodeargd, arg_carryover_info)

        parsing_state = \
            self.make_body_parsing_state(nodeargd, arg_carryover_info, parsing_state)

        nodelist, carryover_info = latex_walker.parse_content(
            body_parser,
            token_reader,
            parsing_state,
            # open_context=(
            #     "Body of {}".format(what),
            #     token_reader.cur_pos()
            # )
            **kwargs
        )
        return nodelist, carryover_info


    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        pos_start = self.token_call.pos #token_reader.cur_pos()

        # parse any arguments first
        if self.arguments_parser is not None:
            nodeargd, arg_carryover_info = self.parse_call_arguments(
                latex_walker, token_reader, parsing_state, **kwargs
            )
        else:
            nodeargd, arg_carryover_info = None, None

        logger.debug("Parsed macro/env/specials arguments; nodeargd=%r, arg_carryover_info=%r",
                     nodeargd, arg_carryover_info)

        # parse any body, if applicable (e.g. environments)
        if self.parse_body:
            body_nodelist, body_carryover_info = self.parse_call_body(
                nodeargd, arg_carryover_info,
                latex_walker, token_reader, parsing_state,
                **kwargs
            )
        else:
            body_nodelist = None
            body_carryover_info = None

        if body_carryover_info is not None:
            logger.warning(
                "Parsing carry-over information (%r) ignored after body!",
                body_carryover_info
            )


        # pos_end = None
        # if nodeargd is not None:
        #     pos_end = nodeargd.pos_end
        # if body_nodelist is not None:
        #     pos_end = body_nodelist.pos_end

        # use cur_pos() because we want to include stuff like \end{environemnt}.
        pos_end = token_reader.cur_pos()

        node_kwargs = dict(self.node_extra_kwargs)
        if self.parse_body:
            node_kwargs['nodelist'] = body_nodelist

        node = latex_walker.make_node(
            self.node_class,
            parsing_state=parsing_state,
            spec=self.spec_object,
            nodeargd=nodeargd,
            # pos/len:
            pos=pos_start,
            pos_end=pos_end,
            # per-node-type stuff:
            **node_kwargs
        )

        logger.debug("Parsed macro/env/specials call to node %r", node)

        carryover_info = self.make_carryover_info(node)

        return node, carryover_info




class LatexMacroCallParser(_LatexCallableParserBase):

    def __init__(self, token_call, macrospec):
        macroname = token_call.arg
        macro_post_space = token_call.post_space
        super(LatexMacroCallParser, self).__init__(
            token_call=token_call,
            spec_object=macrospec,
            what="macro call (\{})".format(macroname),
            node_class=LatexMacroNode,
            node_extra_kwargs=dict(macroname=macroname,
                                   macro_post_space=macro_post_space)
        )
        self.macroname = macroname
        self.macro_post_space = macro_post_space


class LatexEnvironmentCallParser(_LatexCallableParserBase):

    def __init__(self, token_call, environmentspec):
        environmentname = token_call.arg
        super(LatexEnvironmentCallParser, self).__init__(
            token_call=token_call,
            spec_object=environmentspec,
            what="environment {{{}}}".format(environmentname),
            parse_body=True,
            node_class=LatexEnvironmentNode,
            node_extra_kwargs=dict(environmentname=environmentname)
        )
        self.environmentname = environmentname

    def make_body_parser(self, nodeargd, arg_carryover_info):
        if arg_carryover_info is not None:
            logger.warning(
                "Parsing carry-over information (%r) ignored after arguments to %s!",
                arg_carryover_info,
                self.what
            )

        if self.spec_object.body_parser is not None:
            return self.spec_object.body_parser

        # can't cache parser instance because the stop condition depends on the
        # environment name
        return LatexGeneralNodesParser(
            stop_token_condition=self._parse_body_token_stop_condition,
            handle_stop_condition_token=self._handle_stop_condition_token,
        )

    def make_body_parsing_state(self, nodeargd, arg_carryover_info, parsing_state):

        if arg_carryover_info is not None \
           and arg_carryover_info.inner_parsing_state is not None:
            #
            parsing_state = arg_carryover_info.inner_parsing_state

        kw = {}
        if self.spec_object.is_math_mode is not None:
            kw.update(in_math_mode=self.spec_object.is_math_mode)

        if kw:
            return parsing_state.sub_context(**kw)
        return parsing_state

    def _handle_stop_condition_token(self, t, token_reader):
        token_reader.move_past_token(t)

    def _parse_body_token_stop_condition(self, t):
        if t.tok == 'end_environment' and t.arg == self.environmentname:
            return True
        return False



class LatexSpecialsCallParser(_LatexCallableParserBase):

    def __init__(self, token_call, specialsspec):
        specials_chars = specialsspec.specials_chars
        super(LatexSpecialsCallParser, self).__init__(
            token_call=token_call,
            spec_object=specialsspec,
            what="specials ‘{}’".format(specials_chars),
            node_class=LatexSpecialsNode,
            node_extra_kwargs=dict(specials_chars=specials_chars)
        )
        self.specials_chars = specials_chars
