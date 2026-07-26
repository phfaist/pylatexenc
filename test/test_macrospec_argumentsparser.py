import unittest
import sys
import logging



# from pylatexenc.macrospec._argumentsparser import (
#     LatexArgumentSpec,
#     LatexNoArgumentsParser,
#     LatexArgumentsParser,
# )

# from pylatexenc.latexnodes import (
#     LatexWalkerTokenParseError,
#     LatexToken,
#     ParsingState
# )

from pylatexenc.macrospec import (
    LatexArgumentsParser,
    MacroSpec,
)


class TestLatexArgumentsParser(unittest.TestCase):

    # ............. TODO, need to write good tests .................

    def test_invalid_argument_type_is_rejected_immediately(self):
        # an unrecognized argument type must be reported where the arguments
        # parser is built, not later when a document happens to use the macro
        self.assertRaises(ValueError, LatexArgumentsParser, ['xyz'])
        self.assertRaises(ValueError, LatexArgumentsParser, ['{', 'q'])

    def test_multichar_argument_type_given_as_plain_string_is_rejected(self):
        # 'e{^_}' is a valid argument type when given as one list element, but a
        # bare string is iterated character by character, so the same text
        # written as a plain string is not the same thing at all; it must be
        # reported right away rather than at parse time
        LatexArgumentsParser(['e{^_}']) # a proper single argument type; no error

        self.assertRaises(ValueError, LatexArgumentsParser, 'e{^_}')
        self.assertRaises(ValueError, MacroSpec, 'emb', 'e{^_}')

    def test_valid_argument_types_are_accepted(self):
        for arguments_spec_list in ( ['{'], ['[', '{'], ['*', '{'], ['m', 'o'],
                                     ['t*'], ['e{^_}'], [] ):
            # should not raise
            LatexArgumentsParser(arguments_spec_list)



# class Test__LegacyPyltxenc2MacroArgsParserWrapper(unittest.TestCase):
#     def 



# ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
