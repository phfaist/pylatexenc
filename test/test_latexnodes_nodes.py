import unittest
import logging

logger = logging.getLogger(__name__)



from pylatexenc.latexnodes.nodes import *

from pylatexenc.latexnodes import (
    LatexArgumentSpec,
    ParsedArguments,
)



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



    def test_split_at_chars_1(self):


        innercharsnode = LatexCharsNode(
            chars='X,,,Z',
            pos=10,
            pos_end=15,
        )

        innermacronode = LatexMacroNode(
            macroname='test',
            nodeargd=ParsedArguments(
                arguments_spec_list=[ LatexArgumentSpec('{') ],
                argnlist=[ innercharsnode, ]
            ),
            pos=6,
            pos_end=15,
        )

        nodelist = LatexNodeList(
            [
                LatexCharsNode(
                    chars='a,b,,c',
                    pos=0,
                    pos_end=6,
                ),
                innermacronode,
                LatexCharsNode(
                    chars='d,',
                    pos=15,
                    pos_end=17,
                ),
            ],
        )

        self.assertEqual(
            nodelist.split_at_chars(',', keep_empty=False),
            [
                LatexNodeList([
                    LatexCharsNode(
                        chars='a',
                        pos=0,
                        pos_end=1,
                    ),
                ]),
                LatexNodeList([
                    LatexCharsNode(
                        chars='b',
                        pos=2,
                        pos_end=3,
                    ),
                ]),
                LatexNodeList([
                    LatexCharsNode(
                        chars='c',
                        pos=5,
                        pos_end=6,
                    ),
                    innermacronode,
                    LatexCharsNode(
                        chars='d',
                        pos=15,
                        pos_end=16,
                    ),
                ]),
            ]
        )


    def test_split_at_chars_keepempty(self):


        innercharsnode = LatexCharsNode(
            chars='X,,,Z',
            pos=10,
            pos_end=15,
        )

        innermacronode = LatexMacroNode(
            macroname='test',
            nodeargd=ParsedArguments(
                arguments_spec_list=[ LatexArgumentSpec('{') ],
                argnlist=[ innercharsnode, ]
            ),
            pos=6,
            pos_end=15,
        )

        nodelist = LatexNodeList(
            [
                LatexCharsNode(
                    chars='a,b,,c',
                    pos=0,
                    pos_end=6,
                ),
                innermacronode,
                LatexCharsNode(
                    chars='d,',
                    pos=15,
                    pos_end=17,
                ),
            ],
        )

        self.assertEqual(
            nodelist.split_at_chars(',', keep_empty=True),
            [
                LatexNodeList([
                    LatexCharsNode(
                        chars='a',
                        pos=0,
                        pos_end=1,
                    ),
                ]),
                LatexNodeList([
                    LatexCharsNode(
                        chars='b',
                        pos=2,
                        pos_end=3,
                    ),
                ]),
                LatexNodeList([], pos=4, pos_end=4),
                LatexNodeList([
                    LatexCharsNode(
                        chars='c',
                        pos=5,
                        pos_end=6,
                    ),
                    innermacronode,
                    LatexCharsNode(
                        chars='d',
                        pos=15,
                        pos_end=16,
                    ),
                ]),
                LatexNodeList([], pos=17, pos_end=17),
            ]
        )



    def test_split_at_chars_edges_nokeepempty(self):

        innercharsnode = LatexCharsNode(
            chars='X,,,Z',
            pos=6,
            pos_end=11,
        )

        innermacronode = LatexMacroNode(
            macroname='test',
            nodeargd=ParsedArguments(
                arguments_spec_list=[ LatexArgumentSpec('{') ],
                argnlist=[ innercharsnode, ]
            ),
            pos=2,
            pos_end=11,
        )

        nodelist = LatexNodeList(
            [
                LatexCharsNode(
                    chars=',a',
                    pos=0,
                    pos_end=2,
                ),
                innermacronode,
                LatexCharsNode(
                    chars='d,',
                    pos=11,
                    pos_end=13,
                ),
            ],
        )

        self.assertEqual(
            nodelist.split_at_chars(',', keep_empty=False),
            [
                LatexNodeList([
                    LatexCharsNode(
                        chars='a',
                        pos=1,
                        pos_end=2,
                    ),
                    innermacronode,
                    LatexCharsNode(
                        chars='d',
                        pos=11,
                        pos_end=12,
                    ),
                ]),
            ]
        )

    def test_split_at_chars_edges_keepempty(self):

        innercharsnode = LatexCharsNode(
            chars='X,,,Z',
            pos=6,
            pos_end=11,
        )

        innermacronode = LatexMacroNode(
            macroname='test',
            nodeargd=ParsedArguments(
                arguments_spec_list=[ LatexArgumentSpec('{') ],
                argnlist=[ innercharsnode, ]
            ),
            pos=2,
            pos_end=11,
        )

        nodelist = LatexNodeList(
            [
                LatexCharsNode(
                    chars=',a',
                    pos=0,
                    pos_end=2,
                ),
                innermacronode,
                LatexCharsNode(
                    chars='d,',
                    pos=11,
                    pos_end=13,
                ),
            ],
        )

        self.assertEqual(
            nodelist.split_at_chars(',', keep_empty=True),
            [
                LatexNodeList([], pos=0, pos_end=0),
                LatexNodeList([
                    LatexCharsNode(
                        chars='a',
                        pos=1,
                        pos_end=2,
                    ),
                    innermacronode,
                    LatexCharsNode(
                        chars='d',
                        pos=11,
                        pos_end=12,
                    ),
                ]),
                LatexNodeList([], pos=13, pos_end=13),
            ]
        )








# class TestLatexNodesVisitor(unittest.TestCase):

#     # @unittest.skip
#     # def test_are_these_tests_written(self):
#     #
#     #     self.assertTrue(False)

#     pass






# ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
