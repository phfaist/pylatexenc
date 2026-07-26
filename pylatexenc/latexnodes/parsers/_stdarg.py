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


import logging
logger = logging.getLogger(__name__)

from .._exctypes import LatexWalkerParseError
from ..nodes import *

from ._base import LatexParserBase
from ._generalnodes import LatexGeneralNodesParser
from ._delimited import (
    LatexDelimitedExpressionParserInfo,
    LatexDelimitedGroupParserInfo,
    LatexDelimitedGroupParser,
    LatexDelimitedMultiDelimGroupParser,
)
from ._optionals import (
    LatexOptionalCharsMarkerParser, LatexOptionalEmbellishmentArgsParser
)
from ._expression import LatexExpressionParser
from ._verbatim import LatexDelimitedVerbatimParser




# --------------------------------------



_std_arg_parser_instances = {}

def get_standard_argument_parser(arg_spec, **kwargs):
    r"""
    Return an argument parser instance associated with the string shorthand
    `arg_spec` and given keyword arguments.  This creates a
    :py:class:`LatexStandardArgumentParser` instance and caches it (with the
    given `arg_spec` and any given keyword arguments) for future use.
    """
    if not len(kwargs):
        k = arg_spec
    else:
        d = {'arg_spec': arg_spec}
        d.update(kwargs)
        k = tuple(list(sorted(d.items(), key=lambda v: v[0]))) # sort by key

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

    Which argument type to parse is selected by the `arg_spec` string, whose
    syntax is inspired by that of the LaTeX `xparse` package.  The recognized
    values are:

      - ``'m'`` or ``'{'`` — a mandatory argument, given either as a single
        token or as a braced group.  See :py:class:`LatexExpressionParser`.

      - ``'o'`` or ``'['`` — an optional argument delimited by square brackets,
        as in ``\mymacro[optional]``.

      - ``'s'`` or ``'*'`` — an optional star, as in ``\section*``.

      - ``'t<char>'`` — an optional single-character marker `<char>`; like
        ``'s'``, but for a character other than the star.

      - ``'r<char1><char2>'`` — a mandatory argument delimited by the two given
        characters.

      - ``'d<char1><char2>'`` — an optional argument delimited by the two given
        characters.

      - ``'e{<chars>}'`` — a sequence of optional embellishments, each
        introduced by one of the given characters, as the ``^`` and ``_`` in
        ``x^i_j``.  See :py:class:`LatexOptionalEmbellishmentArgsParser`.

      - ``'v'`` — a verbatim argument whose delimiters are whichever characters
        follow the macro (the behavior of ``\verb``); or
        ``'v<char1><char2>'`` — a verbatim argument delimited by the two given
        characters.  See :py:class:`LatexDelimitedVerbatimParser`.

      - ``'AnyDelimited'`` — a mandatory argument delimited by any of the
        standard delimiter pairs ``{}``, ``[]``, ``()`` and ``<>``; or
        ``'AnyDelimitedOptional'`` for the same thing as an optional argument.
        See :py:class:`LatexDelimitedMultiDelimGroupParser`.

    Any other value of `arg_spec` causes a :py:exc:`ValueError` to be raised.
    The relevant parser instance is created lazily, the first time
    :py:meth:`parse()` is called, and is then reused for subsequent calls.

    Further constructor arguments:

      - `return_full_node_list` is relayed to the parsers used for the ``'m'``
        and ``'s'``/``'*'`` argument types.  It determines whether all the nodes
        that were read are reported (including preceding whitespace and comment
        nodes), or only the single node that carries the argument itself.

      - `expression_single_token_requiring_arg_is_error` is relayed as
        `single_token_requiring_arg_is_error` to the
        :py:class:`LatexExpressionParser` used for the ``'m'`` argument type.
        It determines whether it is an error if the single token picked up as
        the argument is a macro that itself requires arguments.

      - `allow_pre_space` determines whether whitespace is allowed between the
        callable and its argument.  It is relayed to all the argument parsers
        above except the verbatim ones.

    .. py:attribute:: arg_spec

       The argument type specification that was given to the constructor.
    """

    def __init__(self,
                 arg_spec='{',
                 return_full_node_list=False,
                 expression_single_token_requiring_arg_is_error=True,
                 allow_pre_space=True,
                 **kwargs
                 ):
        super(LatexStandardArgumentParser, self).__init__(**kwargs)

        self.arg_spec = arg_spec

        self.return_full_node_list = return_full_node_list
        self.expression_single_token_requiring_arg_is_error = \
            expression_single_token_requiring_arg_is_error

        self.allow_pre_space = allow_pre_space

        self._arg_parser = None



    def get_arg_parser_instance(self, arg_spec):
        r"""
        Create and return the parser instance that reads an argument of the type
        given by the `arg_spec` string.  See class doc for the recognized
        values.

        Raises :py:exc:`ValueError` if `arg_spec` is not a recognized argument
        type specification.

        Reimplement this method in a subclass if you'd like to support further
        argument types of your own.
        """

        if arg_spec in ('m', '{'):

            return LatexExpressionParser(
                return_full_node_list=self.return_full_node_list,
                single_token_requiring_arg_is_error=\
                    self.expression_single_token_requiring_arg_is_error,
                allow_pre_space=self.allow_pre_space,
                allow_pre_comments=self.allow_pre_space,
            )

        elif arg_spec in ('o', '['):

            return LatexDelimitedGroupParser(
                delimiters=('[',']',),
                optional=True,
                allow_pre_space=self.allow_pre_space,
            )

        elif arg_spec in ('s', '*'):

            return LatexOptionalCharsMarkerParser(
                chars_list=['*'],
                allow_pre_space=self.allow_pre_space,
                return_full_node_list=self.return_full_node_list,
            )

        elif arg_spec.startswith('e'):
        
            arg_spec_arg = arg_spec[1:].strip()

            if len(arg_spec_arg) <= 2 or \
               arg_spec_arg[0] != '{' or arg_spec_arg[len(arg_spec_arg)-1] != '}':
                raise ValueError("Expected embellishment chars with syntax ‘e{<chars>}’ in "
                                 + "arg_spec; got ‘{}’".format(arg_spec))

            embellishment_chars = arg_spec_arg[1:len(arg_spec_arg)-1]

            return LatexOptionalEmbellishmentArgsParser(
                embellishment_chars=embellishment_chars,
                allow_pre_space=self.allow_pre_space,
            )

        elif arg_spec.startswith('t'):
            # arg_spec = 't<char>', an optional token marker
            if len(arg_spec) != 2:
                raise ValueError("arg_spec for an optional char argument should "
                                 "be of the form ‘t<char>’")
            the_char = arg_spec[1]

            return LatexOptionalCharsMarkerParser(
                chars_list=[the_char],
                allow_pre_space=self.allow_pre_space,
                return_full_node_list=self.return_full_node_list,
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
                delimiters=delimiter_chars,
            )


        elif arg_spec == 'AnyDelimited':

            return LatexDelimitedMultiDelimGroupParser(
                optional=False,
                allow_pre_space=self.allow_pre_space,
            )

        elif arg_spec == 'AnyDelimitedOptional':

            return LatexDelimitedMultiDelimGroupParser(
                optional=True,
                allow_pre_space=self.allow_pre_space,
            )

        else:
            
            raise ValueError("Unknown argument specification: {!r}".format(arg_spec))


    def parse(self, latex_walker, token_reader, parsing_state, **kwargs):
        r"""
        Read the argument by handing over to the parser that corresponds to this
        object's `arg_spec`, and return that parser's result unchanged.

        The relevant parser instance is created on the first call to this method
        (see :py:meth:`get_arg_parser_instance()`) and reused afterwards.

        Reimplemented from :py:meth:`LatexParserBase.parse()`.
        """

        if self._arg_parser is None:
            self._arg_parser = self.get_arg_parser_instance(self.arg_spec)

        arg_parser = self._arg_parser

        nodes, parsing_state_delta = latex_walker.parse_content(
            arg_parser,
            token_reader=token_reader,
            parsing_state=parsing_state,
            **kwargs
        )

        return nodes, parsing_state_delta

            




# --------------------------------------------------------------------




class LatexCharsGroupParser(LatexDelimitedGroupParser):
    r"""
    Parse a delimited group whose contents are read as plain characters, i.e., a
    group in which macros, environments, specials, and math mode are all
    disabled.

    This is what you want for an argument that is a piece of text rather than
    LaTeX code, such as a label name or a file name.  Comments and nested groups
    can be enabled or disabled with the `enable_comments` and `enable_groups`
    constructor arguments (both are enabled by default); everything else is
    reported as ordinary characters.

    The `delimiters` constructor argument is as for
    :py:class:`LatexDelimitedGroupParser` and defaults to ``('{','}')``.  The
    parsing state changes described above apply to the group contents only, not
    to any children of nested groups: those are parsed with the parsing state
    that surrounds this group.

    Very similar to a verbatim parser, but works with tokens instead of chars.
    You can use comments and recursive groups, too.

    Will result in a group node that contains one char node (and possibly a
    combination of group, chars, and comment nodes if those were enabled)
    """
    def __init__(self, delimiters=('{','}'),
                 enable_comments=True, enable_groups=True, **kwargs):
        super(LatexCharsGroupParser, self).__init__(
            delimiters=delimiters,
            delimited_expression_parser_info_class=
                LatexCharsGroupParser.CharsContentsParserInfo,
            **kwargs
        )
        self.enable_comments = enable_comments
        self.enable_groups = enable_groups
            

    class CharsContentsParserInfo(LatexDelimitedGroupParserInfo):
        def initialize(self):
            self.contents_parsing_state = self.group_parsing_state.sub_context(
                enable_macros=False,
                enable_environments=False,
                enable_comments=self.delimited_expression_parser.enable_comments,
                enable_groups=self.delimited_expression_parser.enable_groups,
                enable_specials=False,
                enable_math=False
            )

            self.current_parsing_state = self.contents_parsing_state

            self.parsed_delimiters = self.get_parsed_delimiters()

            logger.debug("Initialized CharsContentsParserInfo; %r", self.__dict__)

        def make_child_parsing_state(self, parsing_state, node_class, token):
            return self.parsing_state

        def stop_token_condition(self, token):
            logger.debug("stop_token_condition: %r", token)
            if token.tok == 'brace_close' and token.arg == self.parsed_delimiters[1]:
                return True
            # in case we set enable_groups=False, the token is reported as a 'char' token
            if token.tok == 'char' and token.arg == self.parsed_delimiters[1]:
                return True
            return None



# --------------------------------------------------------------------



class LatexCharsCommaSeparatedListParser(LatexDelimitedGroupParser):
    r"""
    Parse a delimited group that contains a list of items separated by a given
    character, e.g. ``{one,two,three}``.

    As for :py:class:`LatexCharsGroupParser`, the contents are read as plain
    characters: macros, environments, specials, and math mode are disabled,
    while comments and nested groups can be enabled or disabled with the
    `enable_comments` and `enable_groups` constructor arguments (both are
    enabled by default).  The separator is the `comma_char` constructor
    argument, which defaults to ``','``, and the group delimiters are given by
    `delimiters`, which defaults to ``('{','}')``.

    The result is a :py:class:`~pylatexenc.latexnodes.nodes.LatexGroupNode` for
    the group as a whole, whose node list has one
    :py:class:`~pylatexenc.latexnodes.nodes.LatexGroupNode` per item.  Each item
    node has an empty opening delimiter, and its closing delimiter is the
    separator character that terminated it (an empty string for the last item).

    Empty items are skipped unless `keep_empty_parts` is set to `True`.  An
    entirely empty group (``{}``) never produces any item node, even when
    `keep_empty_parts` is set.

    NOTE: It might be better to use a standard argument, and parse the argument
    as a comma-separated list using
    :py:meth:`~pylatexenc.latexnodes.nodes.LatexNodeList.split_at_chars()`.

    Careful, when accessing the value of this group via a `ParsedArgumentsInfo`
    and `get_contents_nodelist()`, make sure to use `unwrap_double_group=False`
    as otherwise the inner group is going to be unwrapped if a single group is
    present.
    """
    def __init__(self, comma_char=',', delimiters=('{','}'),
                 enable_comments=True, enable_groups=True,
                 keep_empty_parts=False, **kwargs):
        super(LatexCharsCommaSeparatedListParser, self).__init__(
            delimiters=delimiters,
            delimited_expression_parser_info_class=
                LatexCharsCommaSeparatedListParser.CommaSepParserInfo,
            **kwargs
        )

        self.comma_char = comma_char
        self.enable_comments = enable_comments
        self.enable_groups = enable_groups
        self.keep_empty_parts = keep_empty_parts

    class CommaSepParserInfo(LatexDelimitedGroupParserInfo):
        def initialize(self):
            self.comma_char = self.delimited_expression_parser.comma_char
            self.keep_empty_parts = self.delimited_expression_parser.keep_empty_parts

            self.contents_parsing_state = self.group_parsing_state.sub_context(
                enable_macros=False,
                enable_environments=False,
                enable_comments=self.delimited_expression_parser.enable_comments,
                enable_groups=self.delimited_expression_parser.enable_groups,
                enable_specials=False,
                enable_math=False
            )
            self.parsed_delimiters = self.get_parsed_delimiters()

            logger.debug("Initialized CommaSepContentsParserInfo; %r", self.__dict__)

        def make_child_parsing_state(self, parsing_state, node_class, token):
            return self.parsing_state

        def make_content_parser(self, latex_walker, token_reader):
            return _CommaSepContentCustomParser(self)


class _CommaSepContentCustomParser(LatexParserBase):
    def __init__(self, contents_parser_info, **kwargs):
        super(_CommaSepContentCustomParser, self).__init__(**kwargs)
        self.contents_parser_info = contents_parser_info
        self.main_content_parser = LatexGeneralNodesParser(
            stop_token_condition=self.stop_token_condition,
            make_child_parsing_state=contents_parser_info.make_child_parsing_state,
            require_stop_condition_met=True,
            handle_stop_condition_token=self.handle_stop_condition_token,
            stop_condition_message=(
                "Expected matching ‘{}’ of ‘{}’-separated group initiated by ‘{}’"
                .format(
                    contents_parser_info.parsed_delimiters[1],
                    self.contents_parser_info.comma_char,
                    contents_parser_info.parsed_delimiters[0],
                )
            ),
        )
        # A specific parser instance of this type cannot be re-used
        # reliably !  (Nor will it ever be.)
        self.current_parsing_state = self.contents_parser_info.contents_parsing_state
        self.comma_sep_arg_list = []
        self.parsing_state_delta = None
        self.parse_more = True
        self.pos_start = None
        self.is_very_first_element = True # true up to the first comma char
        self.last_element_pos_start = None
        self.last_delimiter_token = None
        self.last_element_pos_end = None

    def stop_token_condition(self, token):
        logger.debug("stop_token_condition: %r", token)
        if token.tok == 'brace_close' \
           and token.arg == self.contents_parser_info.parsed_delimiters[1]:
            return True
        if token.tok == 'char':
            if token.arg == self.contents_parser_info.parsed_delimiters[1]:
                return True
            elif token.arg == self.contents_parser_info.comma_char:
                return True
            return False
        return False

    def handle_stop_condition_token(self, token,
                                    latex_walker, token_reader, parsing_state):
        token_reader.move_past_token(token)
        if token.tok == 'brace_close':
            # final element of a comma-separated list
            self.last_delimiter_token = None
            self.last_element_pos_end = token.pos
            self.parse_more = False
        else:
            self.last_delimiter_token = token
            self.last_element_pos_end = token.pos_end
            self.parse_more = True


    def parse(self, latex_walker, token_reader, parsing_state):

        logger.debug("parse_content! token pos is %r", token_reader.cur_pos())

        self.pos_start = token_reader.cur_pos()

        self.parse_more = True
        while self.parse_more:

            self._parse_one_commasep_arg(latex_walker, token_reader)

            if self.parse_more and self.parsing_state_delta is not None:
                # merge any carry over info into the current parsing state
                self.current_parsing_state = \
                    self.parsing_state_delta.get_updated_parsing_state(
                        self.current_parsing_state,
                        latex_walker
                    )

        final_node_list = latex_walker.make_nodelist(
            self.comma_sep_arg_list,
            pos=self.pos_start,
            pos_end=self.last_element_pos_end,
            parsing_state=parsing_state,
        )

        return final_node_list, self.parsing_state_delta


    def _parse_one_commasep_arg(self, latex_walker, token_reader):

        logger.debug("_parse_one_commasep_arg()")

        self.last_element_pos_start = token_reader.cur_pos()

        self.last_element_pos_end = None
        self.last_delimiter_token = None

        nodelist, parsing_state_delta = latex_walker.parse_content(
            self.main_content_parser,
            token_reader=token_reader,
            parsing_state=self.current_parsing_state,
            open_context=(
                'Element {} of list separated by ‘{}’'.format(
                    len(self.comma_sep_arg_list),
                    self.contents_parser_info.comma_char
                ),
                self.contents_parser_info.first_token
            )
        )

        logger.debug("_parse_one_commasep_arg(): nodelist = %r", nodelist)

        # set in the stopping condition handler
        pos_end = self.last_element_pos_end
        if pos_end is None:
            logger.debug("_parse_one_commasep_arg(): STOP CONDITION DID NOT FIRE")
            # the stopping condition didn't fire because the input ran out; the
            # token reader is then positioned at the end of the input.
            pos_end = token_reader.cur_pos()
            self.parse_more = False

        if self.last_delimiter_token is None:
            this_close_delim = ''
        else:
            this_close_delim = self.last_delimiter_token.arg

        this_group_node = latex_walker.make_node(
            LatexGroupNode,
            nodelist=nodelist,
            parsing_state=self.current_parsing_state,
            delimiters=('', this_close_delim),
            pos=self.last_element_pos_start,
            pos_end=pos_end
        )

        add_group_node = True
        if not len(nodelist):
            if self.is_very_first_element and self.last_delimiter_token is None:
                # this would have been the very first comma-sep argument element
                # and it's also the last one (encountered final '}' delimiter).
                # I.e., we have an empty {} argument.  The empty argument {}
                # should not generate any group node, even if keep_empty_parts
                # is set.
                add_group_node = False
            elif self.contents_parser_info.keep_empty_parts:
                add_group_node = True
            else:
                add_group_node = False

        if add_group_node:
            self.comma_sep_arg_list.append(this_group_node)

        self.parsing_state_delta = parsing_state_delta

        self.is_very_first_element = False

        logger.debug("_parse_one_commasep_arg(), list is now %r",
                     self.comma_sep_arg_list)




# ------------------------------------------------------------------------------


class LatexTackOnInformationFieldMacrosParser(LatexParserBase):
    r"""
    - `macronames` is iterable/list/set of names of macros for which information
      can be specified.  (Name without backslash.)

    - `allow_multiple` can be either True, False, or an iterable/list/set.  Set
      to `True` to allow any information field macro to be specified multiple
      times; set to `False` to disallow all multiple occurrences of an
      information field macro.  Providing a set (or iterable or list) of macro
      names (w/o backslash) will allow repeated specification of those macro
      names only and not the other macro names in `macronames`.

    - `default_macro_arg_parser` is a `LatexParserBase` instance or `True` (the
      default) or `None`.  It is used to parse arguments to each of the
      tacked-on macros that we encounter, except for ones for which a specific
      parser is found in `macro_arg_parsers`.  If set to `True` (the default), a
      standard single-expression parser is used (single token or braced group).
      If set to `None`, no arguments are expected to the given tack-on macros
      for which the default parser is used.

    - `macro_arg_parsers` can be set to a dictionary containing specific parsers
      to use for specific macro names of tacked-on macros.  Specifying
      `macro_arg_parsers=None` is equivalent to specifying an empty dictionary.
      The keys in the dictionaries are the macro names.  Each value is either
      `None` (no argument is expected), `True` (use the default parser), or a
      parser instance.
    """
    def __init__(self, macronames, allow_multiple=False,
                 macro_arg_parsers=None, default_macro_arg_parser=True,
                 **kwargs):
        super(LatexTackOnInformationFieldMacrosParser, self).__init__(**kwargs)

        self.macronames = set(macronames)
        if allow_multiple is False:
            self.allow_multiple = set()
        elif allow_multiple is True:
            self.allow_multiple = self.macronames
        else:
            self.allow_multiple = set(allow_multiple)

        if default_macro_arg_parser is True:
            self.default_macro_arg_parser = LatexExpressionParser()
        else:
            # might be None for no arguments
            self.default_macro_arg_parser = default_macro_arg_parser

        self.macro_arg_parsers = macro_arg_parsers # might be None
        
    def contents_can_be_empty(self):
        return True

    def get_macro_arg_parser(self, macroname):
        r"""
        You can reimplement this method if you want to be able to read more
        complex macro call syntaxes. It is probably simpler, however, to use the
        `macro_arg_parsers` constructor argument.  If you reimplement this
        function, then `macro_arg_parsers` and `default_macro_arg_parser` have
        no effect unless you call the base implementation.
        """
        if self.macro_arg_parsers is None:
            # remember, default_macro_arg_parser might be None to indicate that
            # we don't expect any args
            return self.default_macro_arg_parser
        if macroname not in self.macro_arg_parsers:
            return self.default_macro_arg_parser
        parser = self.macro_arg_parsers[macroname]
        if parser is True:
            return self.default_macro_arg_parser
        return parser # might be None
            

    def parse(self, latex_walker, token_reader, parsing_state):
        
        arg_nodes = []

        seen_macronames = set()

        while True:
            tok = token_reader.peek_token_or_none(parsing_state)

            if tok is None or tok.tok != 'macro' or tok.arg not in self.macronames:
                logger.debug("Finished parsing tack-on macro arguments")
                break

            macroname = tok.arg
            tolerant_parsing_skip_add_this_node = False

            # the token that we read is an information field macro and we will
            # parse its corresponding value.
            token_reader.move_past_token(tok)

            if macroname in seen_macronames and not macroname in self.allow_multiple:
                message = (
                    "You cannot specify information field macro \\{} multiple times"
                    .format(macroname)
                )
                exc = LatexWalkerParseError(
                    msg=message,
                    pos=tok.pos,
                    error_type_info={
                        'what': 'nodes_stdarg_illegal_multiple_information_field_macro',
                        'macroname': macroname
                    },
                )
                exc = latex_walker.check_tolerant_parsing_ignore_error(exc)
                if exc is not None:
                    raise exc
                logger.warning("%s; ignoring the additional information field macros", message)
                tolerant_parsing_skip_add_this_node = True

            seen_macronames.add(macroname)

            macro_arg_parser = self.get_macro_arg_parser(macroname)

            if macro_arg_parser is None:

                arg_content_node = None
                arg_parsing_state_delta = None

            else:
            
                arg_content_node, arg_parsing_state_delta = latex_walker.parse_content(
                    macro_arg_parser,
                    token_reader=token_reader,
                    parsing_state=parsing_state,
                    open_context=(
                        'Argument of information field macro \\{}'.format(macroname),
                        tok,
                    )
                )

                if arg_parsing_state_delta is not None:
                    logger.warning(
                        "Parsing state delta is ignored when parsing tack-on information "
                        "field macro \\{}: {}"
                        .format(macroname, arg_parsing_state_delta)
                    )

            if tolerant_parsing_skip_add_this_node:
                continue

            if isinstance(arg_content_node, LatexNodeList):
                arg_content_nodelist = arg_content_node
            else:
                arg_content_nodelist = latex_walker.make_nodelist(
                    [arg_content_node],
                    parsing_state=parsing_state,
                )

            arg_node = latex_walker.make_node(
                LatexGroupNode,
                parsing_state=parsing_state,
                delimiters=('\\'+macroname, ''),
                nodelist=arg_content_nodelist,
                pos=tok.pos,
                pos_end=(
                    arg_content_node.pos_end
                    if (arg_content_node is not None)
                    else tok.pos_end
                )
            )

            arg_nodes.append( arg_node )

        arg_nodelist = latex_walker.make_nodelist(
            arg_nodes,
            parsing_state=parsing_state,
        )

        return (arg_nodelist, None)
