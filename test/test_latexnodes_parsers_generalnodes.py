import unittest
import sys
import logging


from pylatexenc.latexnodes.parsers._generalnodes import (
    LatexGeneralNodesParser,
    LatexSingleNodeParser,
)

from pylatexenc.latexnodes import (
    LatexWalkerTokenParseError,
    LatexTokenReader,
    LatexToken,
    ParsingState,
    ParsedMacroArgs,
)
from pylatexenc.latexnodes.nodes import *


from ._helpers_tests import (
    DummyWalker,
    DummyLatexContextDb,
)


# ------------------------------------------------------------------------------


class TestGeneralNodesParser(unittest.TestCase):

    def test_gets_nodes_with_stuff(self):
        latextext = r'''Hello there, \yourname. What's that about {}?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexGeneralNodesParser()

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList([
                LatexCharsNode(
                    parsing_state=ps,
                    chars='Hello there, ',
                    pos=0,
                    pos_end=37-24,
                ),
                LatexMacroNode(
                    parsing_state=ps,
                    macroname='yourname',
                    nodeargd=ParsedMacroArgs(),
                    macro_post_space='',
                    spec=ps.latex_context.get_macro_spec('yourname'),
                    pos=37-24,
                    pos_end=46-24,
                ),
                LatexCharsNode(
                    parsing_state=ps,
                    chars=". What's that about ",
                    pos=46-24,
                    pos_end=66-24,
                ),
                LatexGroupNode(
                    parsing_state=ps,
                    delimiters=('{','}'),
                    nodelist=LatexNodeList(
                        [
                            # LatexCharsNode(
                            #     parsing_state=ps,
                            #     chars="A",
                            #     pos=67-24,
                            #     pos_end=68-24,
                            # ),
                        ],
                        pos='<POS>',
                        pos_end='<POS_END>',
                    ),
                    pos=66-24,
                    pos_end=68-24,
                ),
                LatexCharsNode(
                    parsing_state=ps,
                    chars="?",
                    pos=68-24,
                    pos_end=69-24,
                ),
            ])
        )

    def test_gets_nodes_starts_with_macro(self):
        latextext = r'''\yourname, hello'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexGeneralNodesParser()

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList([
                LatexMacroNode(
                    parsing_state=ps,
                    macroname='yourname',
                    nodeargd=ParsedMacroArgs(),
                    macro_post_space='',
                    spec=ps.latex_context.get_macro_spec('yourname'),
                    pos=0,
                    pos_end=9,
                ),
                LatexCharsNode(
                    parsing_state=ps,
                    chars=", hello",
                    pos=9,
                    pos_end=16,
                ),
            ], pos=0, pos_end=16)
        )

    def test_gets_nodes_starts_with_math(self):
        latextext = r'''\(\), hello'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexGeneralNodesParser()

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList([
                LatexMathNode(
                    parsing_state=ps,
                    delimiters=(r'\(',r'\)'),
                    displaytype='inline',
                    nodelist=LatexNodeList([], pos='<POS>', pos_end='<POS_END>'),
                    pos=0,
                    pos_end=4,
                ),
                LatexCharsNode(
                    parsing_state=ps,
                    chars=", hello",
                    pos=4,
                    pos_end=11,
                ),
            ], pos=0, pos_end=11)
        )

    def test_gets_nodes_starts_with_math_2(self):
        latextext = r'''$ $, hello'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexGeneralNodesParser()

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList([
                LatexMathNode(
                    parsing_state=ps,
                    delimiters=(r'$',r'$'),
                    displaytype='inline',
                    nodelist=LatexNodeList([], pos='<POS>', pos_end='<POS_END>'),
                    pos=0,
                    pos_end=3,
                ),
                LatexCharsNode(
                    parsing_state=ps,
                    chars=", hello",
                    pos=3,
                    pos_end=10,
                ),
            ], pos=0, pos_end=10)
        )

    def test_gets_nodes_starts_with_math_display(self):
        latextext = r'''\[\], hello'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexGeneralNodesParser()

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList([
                LatexMathNode(
                    parsing_state=ps,
                    delimiters=(r'\[',r'\]'),
                    displaytype='display',
                    nodelist=LatexNodeList([], pos='<POS>', pos_end='<POS_END>'),
                    pos=0,
                    pos_end=4,
                ),
                LatexCharsNode(
                    parsing_state=ps,
                    chars=", hello",
                    pos=4,
                    pos_end=11,
                ),
            ], pos=0, pos_end=11)
        )

    def test_gets_nodes_starts_with_group(self):
        latextext = r'''{}, hello'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexGeneralNodesParser()

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList([
                LatexGroupNode(
                    parsing_state=ps,
                    delimiters=(r'{',r'}'),
                    nodelist=LatexNodeList([], pos='<POS>', pos_end='<POS_END>'),
                    pos=0,
                    pos_end=2,
                ),
                LatexCharsNode(
                    parsing_state=ps,
                    chars=", hello",
                    pos=2,
                    pos_end=9,
                ),
            ], pos=0, pos_end=9)
        )


# ------------------------------------------------------------------------------

class TestSingleNodeParser(unittest.TestCase):
    def test_simple(self):
        latextext = r'''Hello there, \yourname. What's that about {}?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexSingleNodeParser()

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList([
                LatexCharsNode(
                    parsing_state=ps,
                    chars='Hello there, ',
                    pos=0,
                    pos_end=37-24,
                ),
            ])
        )

    def test_simple_get_comment(self):
        latextext = r'''% comment here.
Hello there, \yourname. What's that about {}?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexSingleNodeParser() #stop_on_comment=True

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList([
                LatexCommentNode(
                    parsing_state=ps,
                    comment=' comment here.',
                    comment_post_space='\n',
                    pos=0,
                    pos_end=40-24,
                ),
            ])
        )
        

    def test_simple_skip_comment(self):
        latextext = r'''% comment here.
Hello there, \yourname. What's that about {}?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexSingleNodeParser(stop_on_comment=False)

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList([
                LatexCommentNode(
                    parsing_state=ps,
                    comment=' comment here.',
                    comment_post_space='\n',
                    pos=0,
                    pos_end=40-24,
                ),
                LatexCharsNode(
                    parsing_state=ps,
                    chars='Hello there, ',
                    pos=16,
                    pos_end=16+13,
                ),
            ])
        )
        










if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
