
import logging
logger = logging.getLogger(__name__)

from ._types import LatexWalkerParseError, LatexWalkerTokenParseError

from ._std import LatexDelimitedGroupParser



# --------------------------------------

from ._optionals import *

# --------------------------------------



class LatexStandardArgumentParser(object):

    def __init__(self,
                 arg_spec='{',
                 include_skipped_comments=True,
                 expression_single_token_requiring_arg_is_error=True,
                 is_math_mode=None,
                 **kwargs
                 ):
        super(LatexStandardArgument, self).__init__(**kwargs)

        self.arg_spec = arg_spec

        self.include_skipped_comments = include_skipped_comments
        self.expression_single_token_requiring_arg_is_error = \
            expression_single_token_requiring_arg_is_error
        self.is_math_mode = is_math_mode

        self.arg_parsing_state_kwargs = dict(enable_environments=False)
        if self.is_math_mode is not None:
            self.arg_parsing_state_kwargs['in_math_mode'] = self.is_math_mode

        if arg_spec in ('m', '{'):

            self.arg_parser = LatexExpressionParser(
                include_skipped_comments=self.include_skipped_comments,
                single_token_requiring_arg_is_error=single_token_requiring_arg_is_error,
            )

        elif arg_spec in ('o', '['):

            self.arg_parser = LatexDelimitedGroupParser(
                require_brace_type='[',
                include_brace_chars=('[',']',),
                optional=True
            )

        elif arg_spec in ('s', '*'):

            self.arg_parser = LatexOptionalCharsMarker(
                chars='*'
            )

        elif arg_spec.startswith('t'):
            # arg_spec = 't<char>', an optional token marker
            if len(arg_spec) != 2:
                raise ValueError("arg_spec for an optional char argument should "
                                 "be of the form ‘t<char>’")
            the_char = arg_spec[1]

            self.arg_parser = LatexOptionalCharsMarker(
                chars=the_char
            )

        elif arg_spec.startswith('r'):
            # arg_spec = 'r<char1><char2>', required delimited argument
            if len(arg_spec) != 3:
                raise ValueError("arg_spec for a required delimited argument should "
                                 "be of the form ‘r<char1><char2>’")
            open_char = arg_spec[1]
            close_char = arg_spec[2]

            self.arg_parser = LatexDelimitedGroupParser(
                require_brace_type=open_char,
                include_brace_chars=(open_char, close_char,),
                optional=False
            )

        elif arg_spec.startswith('d'):
            # arg_spec = 'd<char1><char2>', optional delimited argument
            if len(arg_spec) != 3:
                raise ValueError("arg_spec for an optional delimited argument should "
                                 "be of the form ‘d<char1><char2>’")
            open_char = arg_spec[1]
            close_char = arg_spec[2]

            self.arg_parser = LatexDelimitedGroupParser(
                require_brace_type=open_char,
                include_brace_chars=(open_char, close_char,),
                optional=True
            )

        else:
            
            raise ValueError("Unknown argument specification: {!r}".format(arg_spec))


    def __call__(self, latex_walker, token_reader, parsing_state, **kwargs):

        arg_parsing_state = parsing_state.sub_context(
            **self.arg_parsing_state_kwargs
        )

        nodes, carryover_info = latex_walker.parse_content(
            self.arg_parser,
            latex_walker=latex_walker,
            token_reader=token_reader,
            parsing_state=arg_parsing_state,
            **kwargs
        )

        # if carryover_info:
        #     logger.warning("Ignoring carryover information (%r) when parsing macro arguments!",
        #                    carryover_info)

        return node, carryover_info

            
