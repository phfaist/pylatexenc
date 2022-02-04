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

from ..latexnodes.parsers import get_standard_argument_parser, LatexParserBase

from ..latexnodes import ParsedMacroArgs


# for Py3
_basestring = str

## Begin Py2 support code
import sys
if sys.version_info.major == 2:
    # Py2
    _basestring = basestring
## End Py2 support code



class LatexArgumentSpec(object):
    def __init__(self, spec, argname=None):

        self.spec = spec

        if isinstance(spec, _basestring):
            self.arg_node_parser = get_standard_argument_parser(spec)
        else:
            self.arg_node_parser = spec # it's directly the parser instance.

        self.argname = argname


    def __repr__(self):
        return "{cls}(argname={argname!r}, spec={spec!r})".format(
            cls=self.__class__.__name__,
            argname=self.argname,
            spec=self.spec
        )

    def to_json_object(self):
        if self.argname:
            return dict(argname=self.argname, spec=self.spec)
        return dict(spec=self.spec)
        


class LatexArgumentsParser(LatexParserBase):

    def __init__(self,
                 arguments_spec_list,
                 **kwargs
                 ):
        super(LatexArgumentsParser, self).__init__(**kwargs)

        if arguments_spec_list is None:
            arguments_spec_list = []

        self.arguments_spec_list = [
            (LatexArgumentSpec(arg) if isinstance(arg, _basestring) else arg)
            for arg in arguments_spec_list
        ]


    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        argnlist = []

        pos_start_default = token_reader.cur_pos()
        pos_start = None
        last_arg_node = None

        for argno, arg in enumerate(self.arguments_spec_list):

            logger.debug("Parsing argument %d / %s", argno, arg.arg_node_parser.__class__.__name__)

            peeked_token = token_reader.peek_token_or_none(parsing_state=parsing_state)

            arg_node_parser = arg.arg_node_parser
            argnodes, carryover_info = latex_walker.parse_content(
                arg_node_parser,
                token_reader,
                parsing_state,
                open_context=(
                    "Argument #{}".format(argno),
                    peeked_token
                )
            )
            if carryover_info is not None:
                logger.warning(
                    "Parsing carry-over information (%r) ignored when parsing arguments!",
                    carryover_info
                )
            argnlist.append( argnodes )

            if argnodes is not None:
                if pos_start is None:
                    pos_start = argnodes.pos
                last_arg_node = argnodes

        if pos_start is not None and last_arg_node is not None:
            pos = pos_start
            pos_end = last_arg_node.pos_end
        else:
            pos = pos_start_default
            pos_end = pos

        parsed = ParsedMacroArgs(
            arguments_spec_list=self.arguments_spec_list,
            argnlist=argnlist,
            pos=pos,
            pos_end=pos_end
        )

        logger.debug("Parsed arguments = %r", parsed)

        return parsed, None


# ------------------------------------------------------------------------------

### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE

class _LegacyPyltxenc2MacroArgsParserWrapper(LatexParserBase):
    def __init__(self, args_parser, spec_object):
        super(_LegacyPyltxenc2MacroArgsParserWrapper, self).__init__()

        self.args_parser = args_parser
        self.spec_object = spec_object


    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        argsresult = self.args_parser.parse_args(w=latex_walker,
                                                 pos=token_reader.cur_pos(),
                                                 parsing_state=parsing_state)

        if len(argsresult) == 4:
            (nodeargd, apos, alen, adic) = argsresult
        else:
            (nodeargd, apos, alen) = argsresult
            adic = {}

        apos_end = apos + alen
        token_reader.move_to_pos_chars(apos_end)

        nodeargd.pos = apos
        nodeargd.pos_end = apos_end

        new_parsing_state = adic.get('new_parsing_state', None)
        inner_parsing_state = adic.get('inner_parsing_state', None)

        carryover_info_kw = {}

        if new_parsing_state is not None:
            carryover_info_kw['set_parsing_state'] = new_parsing_state

        if inner_parsing_state is not None:
            carryover_info_kw['inner_parsing_state'] = inner_parsing_state

        if carryover_info_kw:
            carryover_info = CarryoverInformation(**carryover_info_kw)
        else:
            carryover_info = None

        return nodeargd, carryover_info





### END_PYLATEXENC2_LEGACY_SUPPORT_CODE
