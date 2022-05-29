import unittest
import sys
import logging

logger = logging.getLogger(__name__)



from pylatexenc.latexnodes._parsedargsinfo import (
    SingleParsedArgumentInfo,
    ParsedArgumentsInfo,
)

from pylatexenc.latexnodes._parsedargs import (
    LatexArgumentSpec,
    ParsedArguments,
)

from pylatexenc.latexnodes import (
    LatexWalkerParseError,
)
from pylatexenc.latexnodes.nodes import *

from ._helpers_tests import (
    DummyWalker,
    DummyLatexContextDb,
)



class TestSingleParsedArgumentInfo(unittest.TestCase):

    maxDiff = None

    # --

    def test_was_provided_if_provided(self):
        arginfo = SingleParsedArgumentInfo(
            LatexGroupNode(
                delimiters=('{','}'),
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            chars='Hello world',
                            pos=13,
                            pos_end=13+11, # 11 == len('Hello world')
                        ),
                    ]
                )
            )
        )
        self.assertTrue(arginfo.was_provided())

    def test_was_provided_if_provided_even_with_None_item(self):
        arginfo = SingleParsedArgumentInfo(
            LatexGroupNode(
                delimiters=('{','}'),
                nodelist=LatexNodeList(
                    [
                        None,
                    ]
                )
            )
        )
        self.assertTrue(arginfo.was_provided())

    def test_was_provided_if_not_provided(self):
        arginfo = SingleParsedArgumentInfo(
            None,
        )
        self.assertFalse(arginfo.was_provided())

    def test_get_content_as_chars(self):
        arginfo = SingleParsedArgumentInfo(
            LatexGroupNode(
                delimiters=('{','}'),
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            chars='Hello world',
                            pos=13,
                            pos_end=13+11, # 11 == len('Hello world')
                        ),
                        None,
                        LatexCommentNode(
                            comment=' a comment',
                            pos=13+11,
                            pos_end=13+11+12, # 12 == len('% a comment\n')
                        ),
                    ],
                ),
            )
        )

        self.assertEqual(arginfo.get_content_as_chars(),
                         'Hello world')


    def test_get_content_as_chars_single_arg_node(self):
        arginfo = SingleParsedArgumentInfo(
            LatexCharsNode(
                chars='Hello world',
                pos=13,
                pos_end=13+11, # 11 == len('Hello world')
            ),
        )

        self.assertEqual(arginfo.get_content_as_chars(),
                         'Hello world')

        
    def test_get_content_as_chars_fails_with_invalid_node_type(self):

        arginfo = SingleParsedArgumentInfo(
            LatexGroupNode(
                delimiters=('{','}'),
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            chars='Hello world',
                            pos=13,
                            pos_end=13+11, # 11 == len('Hello world')
                        ),
                        None,
                        LatexMacroNode(
                            macroname='hello',
                            nodeargd=ParsedArguments(),
                            pos=13+11,
                            pos_end=13+11+6, # 6 == len(r'\hello')
                        ),
                        LatexCommentNode(
                            comment=' a comment',
                            pos=13+11+6,
                            pos_end=13+11+6+12, # 12 == len('% a comment\n')
                        ),
                    ],
                ),
            )
        )

        with self.assertRaises(LatexWalkerParseError):
            x = arginfo.get_content_as_chars()




class TestParsedArgumentsInfo(unittest.TestCase):

    maxDiff = None

    @unittest.skip
    def test_write_me(self):
        self.assertTrue(False)



# ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
