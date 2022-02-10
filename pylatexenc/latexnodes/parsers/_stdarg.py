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

from .._exctypes import LatexWalkerParseError, LatexWalkerTokenParseError
from ..nodes import *

from ._base import LatexParserBase
from ._generalnodes import LatexGeneralNodesParser, LatexDelimitedGroupParser
from ._optionals import LatexOptionalCharsMarkerParser
from ._expression import LatexExpressionParser
from ._verbatim import LatexDelimitedVerbatimParser



# for Py3
_basestring = str

## Begin Py2 support code
import sys
if sys.version_info.major == 2:
    # Py2
    _basestring = basestring
## End Py2 support code



# --------------------------------------



_std_arg_parser_instances = {}

def get_standard_argument_parser(arg_spec, **kwargs):

    d = {'arg_spec': arg_spec}
    d.update(kwargs)
    k = tuple(list(d.items()))
    if k not in _std_arg_parser_instances:
        instance = LatexStandardArgumentParser(arg_spec, **kwargs)
        _std_arg_parser_instances[k] = instance
        return instance

    return _std_arg_parser_instances[k]


#
# TODO: ALL ARGUMENT TYPES might have a preceding comment!! Not only an
# expression.
#

class LatexStandardArgumentParser(LatexParserBase):
    r"""
    Node parser that can parse standard macro argument types, such as a
    mandatory argument in braces, an optional argument in square braces, an
    optional star, as well as more advanced macro argument constructs.

    .................
    """

    def __init__(self,
                 arg_spec='{',
                 include_skipped_comments=True,
                 expression_single_token_requiring_arg_is_error=True,
                 is_math_mode=None,
                 allow_pre_space=True,
                 set_arg_parsing_state_kwargs=None,
                 **kwargs
                 ):
        super(LatexStandardArgumentParser, self).__init__(**kwargs)

        self.arg_spec = arg_spec

        self.include_skipped_comments = include_skipped_comments
        self.expression_single_token_requiring_arg_is_error = \
            expression_single_token_requiring_arg_is_error
        self.is_math_mode = is_math_mode
        self.allow_pre_space = allow_pre_space
        self.set_arg_parsing_state_kwargs = set_arg_parsing_state_kwargs

        self._arg_parsing_state_kwargs = None
        self._arg_parser = None


    def get_arg_parsing_state_kwargs(self):

        arg_parsing_state_kwargs = {}
        if self.is_math_mode is not None:
            arg_parsing_state_kwargs['in_math_mode'] = self.is_math_mode
        if self.set_arg_parsing_state_kwargs:
            arg_parsing_state_kwargs.update(self.set_arg_parsing_state_kwargs)

        return arg_parsing_state_kwargs


    def get_arg_parser_instance(self, arg_spec):

        if arg_spec in ('m', '{'):

            return LatexExpressionParser(
                include_skipped_comments=self.include_skipped_comments,
                single_token_requiring_arg_is_error=\
                    self.expression_single_token_requiring_arg_is_error,
            )

        elif arg_spec in ('o', '['):

            return LatexDelimitedGroupParser(
                delimiters=('[',']',),
                optional=True,
                allow_pre_space=self.allow_pre_space,
            )

        elif arg_spec in ('s', '*'):

            return LatexOptionalCharsMarkerParser(
                chars='*',
                allow_pre_space=self.allow_pre_space,
            )

        elif arg_spec.startswith('t'):
            # arg_spec = 't<char>', an optional token marker
            if len(arg_spec) != 2:
                raise ValueError("arg_spec for an optional char argument should "
                                 "be of the form ‘t<char>’")
            the_char = arg_spec[1]

            return LatexOptionalCharsMarkerParser(
                chars=the_char,
                allow_pre_space=self.allow_pre_space,
            )

        elif arg_spec.startswith('r'):
            # arg_spec = 'r<char1><char2>', required delimited argument
            if len(arg_spec) != 3:
                raise ValueError("arg_spec for a required delimited argument should "
                                 "be of the form ‘r<char1><char2>’")
            open_char = arg_spec[1]
            close_char = arg_spec[2]

            return LatexDelimitedGroupParser(
                delimiters=(open_char, close_char,),
                optional=False,
                allow_pre_space=self.allow_pre_space,
            )

        elif arg_spec.startswith('d'):
            # arg_spec = 'd<char1><char2>', optional delimited argument
            if len(arg_spec) != 3:
                raise ValueError("arg_spec for an optional delimited argument should "
                                 "be of the form ‘d<char1><char2>’")
            open_char = arg_spec[1]
            close_char = arg_spec[2]

            return LatexDelimitedGroupParser(
                delimiters=(open_char, close_char,),
                optional=True,
                allow_pre_space=self.allow_pre_space,
            )

        elif arg_spec.startswith('v'):
            # arg_spec = 'v' or 'v<char1><char2>', a verbatim argument with
            # automatically detected delimiters or specific delimiters
            if len(arg_spec) == 1:
                delimiter_chars = None # autodetect
            elif len(arg_spec) == 3:
                delimiter_chars = (arg_spec[1], arg_spec[2])
            else:
                raise ValueError("arg_spec for a verbatim argument should be either ‘v’ "
                                 "or ‘v<char1><char2>’")
            return LatexDelimitedVerbatimParser(
                delimiter_chars=delimiter_chars
            )

        else:
            
            raise ValueError("Unknown argument specification: {!r}".format(arg_spec))


    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        if self._arg_parsing_state_kwargs is None:
            self._arg_parsing_state_kwargs = self.get_arg_parsing_state_kwargs()
        if self._arg_parser is None:
            self._arg_parser = self.get_arg_parser_instance(self.arg_spec)

        arg_parsing_state = parsing_state

        if self._arg_parsing_state_kwargs:
            arg_parsing_state = parsing_state.sub_context(
                **self._arg_parsing_state_kwargs
            )
            logger.debug("Argument parsing state: %r", arg_parsing_state)

        arg_parser = self._arg_parser

        nodes, carryover_info = latex_walker.parse_content(
            arg_parser,
            token_reader=token_reader,
            parsing_state=arg_parsing_state,
            **kwargs
        )

        return nodes, carryover_info

            


# --------------------------------------------------------------------



class LatexCharsCommaSeparatedListParser(LatexDelimitedGroupParser):
    r"""
    """
    def __init__(self, comma_char=',', delimiters=('{','}'),
                 enable_comments=True, enable_groups=True):
        super(LatexCharsCommaSeparatedListParser, self).__init__(delimiters=delimiters)
        self.comma_char = comma_char
        self.enable_comments = enable_comments
        self.enable_groups = enable_groups

        self.make_group_contents_parser_info = \
            LatexCharsCommaSeparatedListParser.CommaSepContentsParserInfo


    class CommaSepContentsParserInfo(
            LatexDelimitedGroupParser.GroupContentsParserInfo
    ):
        def initialize(self):
            self.comma_char = self.delimited_group_parser.comma_char

            self.contents_parsing_state = self.group_parsing_state.sub_context(
                enable_macros=False,
                enable_environments=False,
                enable_comments=self.delimited_group_parser.enable_comments,
                enable_groups=self.delimited_group_parser.enable_groups,
                enable_specials=False,
                enable_math=False
            )
            self.child_parsing_state = self.parsing_state

            self.current_parsing_state = self.contents_parsing_state

            self.parsed_delimiters = self.get_parsed_delimiters()

            logger.debug("Initialized CommaSepContentsParserInfo; %r", self.__dict__)

        def stop_token_condition(self, token):
            logger.debug("stop_token_condition: %r", token)
            if token.tok == 'brace_close' and token.arg == self.parsed_delimiters[1]:
                return True
            if token.tok == 'char' and token.arg == self.comma_char:
                return True
            return None

        def handle_stop_condition_token(self, token,
                                        latex_walker, token_reader, parsing_state):
            token_reader.move_past_token(token)
            if token.tok == 'brace_close':
                # final element of a comma-separated list
                self._last_delimiter_token = None
                self._last_element_pos_end = token.pos
                self._parse_more = False
            else:
                self._last_delimiter_token = token
                self._last_element_pos_end = token.pos_end
                self._parse_more = True

        def parse_content(self, latex_walker, token_reader):

            logger.debug("parse_content! token pos is %r", token_reader.cur_pos())

            self._comma_sep_arg_list = []
            self._carryover_info = None

            self._contents_parser = LatexGeneralNodesParser(
                stop_token_condition=self.stop_token_condition,
                make_child_parsing_state=self.make_child_parsing_state,
                require_stop_condition_met=True,
                handle_stop_condition_token=self.handle_stop_condition_token,
            )

            self._parse_more = True
            while self._parse_more:

                self._parse_one_commasep_arg(latex_walker, token_reader)

                if self._parse_more and self._carryover_info is not None:
                    # merge any carry over info into the current parsing state
                    self.current_parsing_state = \
                        self._carryover_info.get_updated_parsing_state(
                            self.current_parsing_state
                        )

            return LatexNodeList(self._comma_sep_arg_list), self._carryover_info
                    

        def _parse_one_commasep_arg(self, latex_walker, token_reader):

            logger.debug("_parse_one_commasep_arg()")

            self._last_element_pos_end = None
            self._last_delimiter_token = None

            nodelist, carryover_info = latex_walker.parse_content(
                self._contents_parser,
                token_reader=token_reader,
                parsing_state=self.current_parsing_state,
                open_context=(
                    'Element {} of list separated by ‘{}’'.format(
                        len(self._comma_sep_arg_list),
                        self.comma_char
                    ),
                    self.first_token
                )
            )

            logger.debug("_parse_one_commasep_arg(): nodelist = %r", nodelist)

            # set in the stopping condition handler
            pos_end = self._last_element_pos_end
            if pos_end is None:
                logger.debug("_parse_one_commasep_arg(): STOP CONDITION DID NOT FIRE")

                pos_end = token_reader.final_pos()
                self._parse_more = False

            if self._last_delimiter_token is None:
                this_close_delim = ''
            else:
                this_close_delim = self._last_delimiter_token.arg

            this_group_node = latex_walker.make_node(
                LatexGroupNode,
                nodelist=nodelist,
                parsing_state=self.contents_parsing_state,
                delimiters=('', this_close_delim),
                pos=nodelist.pos,
                pos_end=pos_end
            )
            
            self._comma_sep_arg_list.append(this_group_node)

            self._carryover_info = carryover_info

            logger.debug("_parse_one_commasep_arg(), list is now %r",
                         self._comma_sep_arg_list)



class LatexCharsGroupParser(LatexCharsCommaSeparatedListParser):
    r"""
    ....................

    Very similar to a verbatim parser, but works with tokens instead of chars.
    You can use comments and recursive groups, too.
    """
    def __init__(self, delimiters=('{','}'),
                 enable_comments=True, enable_groups=True, **kwargs):
        super(LatexCharsGroupParser, self).__init__(comma_char=None, **kwargs)

