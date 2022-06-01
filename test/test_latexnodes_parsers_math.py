import unittest
#import logging


from pylatexenc.latexnodes.parsers._math import (
    LatexMathParser,
)

from pylatexenc.latexnodes import (
    LatexTokenReader,
    ParsingState,
)
from pylatexenc.latexnodes.nodes import *


from ._helpers_tests import (
    DummyWalker,
    DummyLatexContextDb,
)



class TestMathParser(unittest.TestCase):

    def test_simple_1(self):
        
        latextext = r'''$a+b=c$'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexMathParser(math_mode_delimiters=None)

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        psmath = nodes.nodelist[0].parsing_state
        self.assertTrue(psmath.in_math_mode)

        self.assertEqual(
            nodes,
            LatexMathNode(
                parsing_state=ps,
                delimiters=('$','$'),
                displaytype='inline',
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=psmath,
                            chars='a+b=c',
                            pos=1,
                            pos_end=6,
                        ),
                    ],
                    pos=1,
                    pos_end=6,
                ),
                pos=0,
                pos_end=7,
            )
        )

    def test_simple_2(self):
        
        latextext = r'''\(a+b=c\)'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexMathParser(math_mode_delimiters=None)

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        psmath = nodes.nodelist[0].parsing_state
        self.assertTrue(psmath.in_math_mode)

        self.assertEqual(
            nodes,
            LatexMathNode(
                parsing_state=ps,
                delimiters=(r'\(',r'\)'),
                displaytype='inline',
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=psmath,
                            chars='a+b=c',
                            pos=2,
                            pos_end=7,
                        ),
                    ],
                    pos=2,
                    pos_end=7,
                ),
                pos=0,
                pos_end=9,
            )
        )

    def test_simple_3(self):
        
        latextext = r'''\[a+b=c\]'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexMathParser(math_mode_delimiters=None)

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        psmath = nodes.nodelist[0].parsing_state
        self.assertTrue(psmath.in_math_mode)

        self.assertEqual(
            nodes,
            LatexMathNode(
                parsing_state=ps,
                delimiters=(r'\[',r'\]'),
                displaytype='display',
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=psmath,
                            chars='a+b=c',
                            pos=2,
                            pos_end=7,
                        ),
                    ],
                    pos=2,
                    pos_end=7,
                ),
                pos=0,
                pos_end=9,
            )
        )

    def test_simple_3b(self):
        
        latextext = r'''$$a+b=c$$'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexMathParser(math_mode_delimiters=None)

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        psmath = nodes.nodelist[0].parsing_state
        self.assertTrue(psmath.in_math_mode)

        self.assertEqual(
            nodes,
            LatexMathNode(
                parsing_state=ps,
                delimiters=('$$','$$'),
                displaytype='display',
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=psmath,
                            chars='a+b=c',
                            pos=2,
                            pos_end=7,
                        ),
                    ],
                    pos=2,
                    pos_end=7,
                ),
                pos=0,
                pos_end=9,
            )
        )

    def test_simple_4(self):
        
        latextext = r'''$a+b=c$'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexMathParser(math_mode_delimiters='$')

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        psmath = nodes.nodelist[0].parsing_state
        self.assertTrue(psmath.in_math_mode)

        self.assertEqual(
            nodes,
            LatexMathNode(
                parsing_state=ps,
                delimiters=('$','$'),
                displaytype='inline',
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=psmath,
                            chars='a+b=c',
                            pos=1,
                            pos_end=6,
                        ),
                    ],
                    pos=1,
                    pos_end=6,
                ),
                pos=0,
                pos_end=7,
            )
        )

    def test_simple_5(self):
        
        latextext = r'''$a+b=c$'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexMathParser(math_mode_delimiters=('$','$'))

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        psmath = nodes.nodelist[0].parsing_state
        self.assertTrue(psmath.in_math_mode)

        self.assertEqual(
            nodes,
            LatexMathNode(
                parsing_state=ps,
                delimiters=('$','$'),
                displaytype='inline',
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=psmath,
                            chars='a+b=c',
                            pos=1,
                            pos_end=6,
                        ),
                    ],
                    pos=1,
                    pos_end=6,
                ),
                pos=0,
                pos_end=7,
            )
        )

    def test_simple_6(self):
        
        latextext = r'''\[a+b=c\]'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexMathParser(math_mode_delimiters=r'\[')

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        psmath = nodes.nodelist[0].parsing_state
        self.assertTrue(psmath.in_math_mode)

        self.assertEqual(
            nodes,
            LatexMathNode(
                parsing_state=ps,
                delimiters=(r'\[',r'\]'),
                displaytype='display',
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=psmath,
                            chars='a+b=c',
                            pos=2,
                            pos_end=7,
                        ),
                    ],
                    pos=2,
                    pos_end=7,
                ),
                pos=0,
                pos_end=9,
            )
        )
