import unittest
import logging


from pylatexenc.latexnodes.parsers._expression import (
    LatexExpressionParser,
)

from pylatexenc.latexnodes import (
    LatexWalkerParseError,
    LatexTokenReader,
    LatexToken,
    ParsingState,
)
from pylatexenc.latexnodes.nodes import *

from ._helpers_tests import (
    DummyWalker,
    DummyLatexContextDb,
)




# --------------------------------------

class TestLatexExpression(unittest.TestCase):
    
    maxDiff = None

    def test_simple_first_char(self):
        latextext = r'''characters'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser()

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=ps,
                        chars='c',
                        pos=0,
                        pos_end=1,
                    )
                ],
                parsing_state=ps
            )
        )

    def test_simple_first_char_nofulllist(self):
        latextext = r'''characters'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser(return_full_node_list=False)

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexCharsNode(
                parsing_state=ps,
                chars='c',
                pos=0,
                pos_end=1,
            )
        )
    

    def test_simple_first_char_wspace(self):
        latextext = ' \n \t characters'

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser()

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=ps,
                        chars=' \n \t ',
                        pos=0,
                        pos_end=5,
                    ),
                    LatexCharsNode(
                        parsing_state=ps,
                        chars='c',
                        pos=5,
                        pos_end=6,
                    ),
                ],
            )
        )

    def test_simple_first_char_wspace_nofulllist(self):
        latextext = ' \n \t characters'

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser(return_full_node_list=False)

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexCharsNode(
                parsing_state=ps,
                chars='c',
                pos=5,
                pos_end=6,
            ),
        )


    def test_simple_first_char_wspaceandcomment(self):
        latextext = ' \n \t % comment\n  characters'

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser()

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=ps,
                        chars=' \n \t ',
                        pos=0,
                        pos_end=5,
                    ),
                    LatexCommentNode(
                        parsing_state=ps,
                        comment=' comment',
                        comment_post_space='\n  ',
                        pos=5,
                        pos_end=17,
                    ),
                    LatexCharsNode(
                        parsing_state=ps,
                        chars='c',
                        pos=17,
                        pos_end=18,
                    ),
                ],
            )
        )


    def test_simple_first_char_wspaceandcomment_nofulllist(self):
        latextext = ' \n \t % comment\n  characters'

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser(return_full_node_list=False)

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexCharsNode(
                parsing_state=ps,
                chars='c',
                pos=17,
                pos_end=18,
            ),
        )


    def test_simple_group_char_wspace(self):
        latextext = ' \n \t {char}acters'

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser()

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=ps,
                        chars=' \n \t ',
                        pos=0,
                        pos_end=5,
                    ),
                    LatexGroupNode(
                        parsing_state=ps,
                        nodelist=LatexNodeList(
                            [
                                LatexCharsNode(
                                    parsing_state=ps,
                                    chars='char',
                                    pos=6,
                                    pos_end=10,
                                ),
                            ],
                            parsing_state=ps,
                        ),
                        delimiters=('{','}'),
                        pos=5,
                        pos_end=11,
                    ),
                ],
            )
        )

    def test_simple_group_char_wspace_nofulllist(self):
        latextext = ' \n \t {char}acters'

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser(return_full_node_list=False)

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=ps,
                            chars='char',
                            pos=6,
                            pos_end=10,
                        ),
                    ],
                    parsing_state=ps,
                ),
                delimiters=('{','}'),
                pos=5,
                pos_end=11,
            ),
        )
    
    def test_simple_group_wcomment(self):
        latextext = r'''
%comment here
{mandatory argument} (more stuff)'''.lstrip()

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser()

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList(
                [
                    LatexCommentNode(
                        parsing_state=ps,
                        comment='comment here',
                        comment_post_space='\n',
                        pos=0,
                        pos_end=14,
                    ),
                    LatexGroupNode(
                        parsing_state=ps,
                        nodelist=LatexNodeList(
                            [
                                LatexCharsNode(
                                    parsing_state=ps,
                                    chars='mandatory argument',
                                    pos=14+1,
                                    pos_end=14+19,
                                ),
                            ],
                            parsing_state=ps,
                        ),
                        pos=14,
                        pos_end=14+20,
                    ),
                ],
            )
        )

    def test_simple_group_wcomment_nofulllist(self):
        latextext = r'''
%comment here
{mandatory argument} (more stuff)'''.lstrip()

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser(return_full_node_list=False)

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=ps,
                            chars='mandatory argument',
                            pos=14+1,
                            pos_end=14+19,
                        ),
                    ],
                    parsing_state=ps,
                ),
                pos=14,
                pos_end=14+20,
            ),
        )





# ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
