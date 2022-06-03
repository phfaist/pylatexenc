import unittest
import logging

logger = logging.getLogger(__name__)



from pylatexenc.latexnodes.nodes import *

#from pylatexenc.latexnodes import (
#    LatexWalkerParseError,
#    ParsedArguments
#)

# from ._helpers_tests import (
#     DummyWalker,
#     DummyLatexContextDb,
# )



class TestLatexNodeList(unittest.TestCase):

    maxDiff = None

    def test_picks_pos_correctly(self):

        nodelist = LatexNodeList(
            [
                LatexCharsNode(
                    chars='Hello world',
                    pos=13,
                    pos_end=13+11, # 11 == len('Hello world')
                ),
                LatexCommentNode(
                    comment=' a comment',
                    pos=13+11,
                    pos_end=13+11+12, # 12 == len('% a comment\n')
                ),
            ],
        )

        self.assertEqual(nodelist.pos, 13)
        self.assertEqual(nodelist.pos_end, 13+11+12)

    def test_picks_pos_correctly_with_None_at_beginning(self):

        nodelist = LatexNodeList(
            [
                None,
                LatexCharsNode(
                    chars='Hello world',
                    pos=13,
                    pos_end=13+11, # 11 == len('Hello world')
                ),
                LatexCommentNode(
                    comment=' a comment',
                    pos=13+11,
                    pos_end=13+11+12, # 12 == len('% a comment\n')
                ),
            ],
        )

        self.assertEqual(nodelist.pos, 13)
        self.assertEqual(nodelist.pos_end, 13+11+12)

    def test_picks_pos_correctly_with_None_at_end(self):

        nodelist = LatexNodeList(
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
                None,
            ],
        )

        self.assertEqual(nodelist.pos, 13)
        self.assertEqual(nodelist.pos_end, 13+11+12)


    def test_picks_pos_correctly_with_None_at_beginning_and_end(self):

        nodelist = LatexNodeList(
            [
                None,
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
                None,
            ],
        )

        self.assertEqual(nodelist.pos, 13)
        self.assertEqual(nodelist.pos_end, 13+11+12)







class TestLatexNodesVisitor(unittest.TestCase):

    def test_are_these_tests_written(self):

        self.assertTrue(False)


# ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
