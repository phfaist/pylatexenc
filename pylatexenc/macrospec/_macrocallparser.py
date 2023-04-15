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

from ..latexnodes.nodes import LatexMacroNode, LatexEnvironmentNode, LatexSpecialsNode
from ..latexnodes.parsers import LatexParserBase

from ..latexnodes import get_updated_parsing_state_from_delta

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
        super(_LatexCallableParserBase, self).__init__()

        logger.debug("_LatexCallableParserBase, token_call=%r, spec_object=%r (%s)",
                     token_call, spec_object, what)

        self.token_call = token_call
        self.spec_object = spec_object
        self.what = what
        self.node_class = node_class
        self.node_extra_kwargs = node_extra_kwargs

        self.arguments_parser = self.spec_object.arguments_parser

        self.parse_body = parse_body

        self.make_arguments_parsing_state_delta = \
            self.spec_object.make_arguments_parsing_state_delta
        self.make_body_parsing_state_delta = \
            self.spec_object.make_body_parsing_state_delta
        self.make_after_parsing_state_delta = \
            self.spec_object.make_after_parsing_state_delta


    def parse_call_arguments(self, latex_walker, token_reader, parsing_state, **kwargs):

        arguments_parsing_state = get_updated_parsing_state_from_delta(
            parsing_state,
            self.make_arguments_parsing_state_delta(
                token=self.token_call,
                latex_walker=latex_walker,
            ),
            latex_walker,
        )

        nodeargd, parsing_state_delta = latex_walker.parse_content(
            self.arguments_parser,
            token_reader,
            arguments_parsing_state,
            # open_context=(
            #     "Arguments of {}".format(what),
            #     token_reader.cur_pos()
            # )
            **kwargs
        )
        return nodeargd, parsing_state_delta

    def make_body_parser_and_parsing_state(self, nodeargd, arg_parsing_state_delta,
                                           parsing_state, latex_walker):
        raise RuntimeError(
            "No default implementation of make_body_parser_and_parsing_state() in base class")

    def parse_call_body(self, nodeargd, arg_parsing_state_delta,
                        latex_walker, token_reader, parsing_state, **kwargs):

        body_parser, body_parsing_state = \
            self.make_body_parser_and_parsing_state(nodeargd, arg_parsing_state_delta,
                                                    parsing_state, latex_walker)

        nodelist, parsing_state_delta = latex_walker.parse_content(
            body_parser,
            token_reader,
            body_parsing_state,
            # open_context=(
            #     "Body of {}".format(self.what),
            #     token_reader.peek_token()
            # )
            **kwargs
        )
        return nodelist, parsing_state_delta


    def parse(self, latex_walker, token_reader, parsing_state, **kwargs):

        pos_start = self.token_call.pos #token_reader.cur_pos()

        # parse any arguments first
        if self.arguments_parser is not None:
            nodeargd, arg_parsing_state_delta = self.parse_call_arguments(
                latex_walker, token_reader, parsing_state, **kwargs
            )
        else:
            nodeargd, arg_parsing_state_delta = None, None

        logger.debug("Parsed macro/env/specials arguments; nodeargd=%r, "
                     "arg_parsing_state_delta=%r",
                     nodeargd, arg_parsing_state_delta)

        # parse any body, if applicable (e.g. environments)
        if self.parse_body:
            body_nodelist, body_parsing_state_delta = self.parse_call_body(
                nodeargd, arg_parsing_state_delta,
                latex_walker, token_reader, parsing_state,
                **kwargs
            )
        else:
            if arg_parsing_state_delta is not None:
                logger.warning(
                    "Parsing carry-over information (%r) ignored after arguments to %s!",
                    arg_parsing_state_delta,
                    self.what
                )

            body_nodelist = None
            body_parsing_state_delta = None

        if body_parsing_state_delta is not None:
            logger.warning(
                "Parsing carry-over information (%r) ignored after body!",
                body_parsing_state_delta
            )

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

        # in case any subclasses would like to tweak the node, register
        # additional information, etc.
        node = self.spec_object.finalize_node(node)

        parsing_state_delta = self.make_after_parsing_state_delta(
            parsed_node=node,
            latex_walker=latex_walker,
        )

        logger.debug("Parsed macro/env/specials call - node %r - parsing_state_delta %r",
                     node, parsing_state_delta)

        return node, parsing_state_delta




class LatexMacroCallParser(_LatexCallableParserBase):

    def __init__(self, token_call, macrospec):
        macroname = token_call.arg
        macro_post_space = token_call.post_space
        super(LatexMacroCallParser, self).__init__(
            token_call=token_call,
            spec_object=macrospec,
            what=r"macro call (\{})".format(macroname),
            node_class=LatexMacroNode,
            node_extra_kwargs=dict(macroname=macroname,
                                   macro_post_space=macro_post_space),
        )
        self.macroname = macroname
        self.macro_post_space = macro_post_space


class LatexEnvironmentCallParser(_LatexCallableParserBase):

    def __init__(self, token_call, environmentspec):
        environmentname = token_call.arg
        super(LatexEnvironmentCallParser, self).__init__(
            token_call=token_call,
            spec_object=environmentspec,
            what="environment {}{}{}".format('{',environmentname,'}'),
            parse_body=True,
            node_class=LatexEnvironmentNode,
            node_extra_kwargs=dict(environmentname=environmentname)
        )
        self.environmentname = environmentname

    def make_body_parser_and_parsing_state(self, nodeargd, arg_parsing_state_delta,
                                           parsing_state, latex_walker):
        if arg_parsing_state_delta is not None:
            logger.warning(
                "Parsing carry-over information (%r) ignored after arguments to %s!",
                arg_parsing_state_delta,
                self.what
            )

        parser = self.spec_object.make_body_parser(self.token_call, nodeargd,
                                                   arg_parsing_state_delta)

        body_parsing_state = get_updated_parsing_state_from_delta(
            parsing_state,
            self.make_body_parsing_state_delta(
                token=self.token_call,
                nodeargd=nodeargd,
                arg_parsing_state_delta=arg_parsing_state_delta,
                latex_walker=latex_walker,
            ),
            latex_walker,
        )

        return parser, body_parsing_state


    def _handle_stop_condition_token(self, t, latex_walker, token_reader, parsing_state):
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
