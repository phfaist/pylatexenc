
import unittest

import logging
logger = logging.getLogger(__name__)


from pylatexenc.latexnodes.parsers._math import (
    LatexMathParser,
)

from pylatexenc.latexnodes import (
    LatexTokenReader,
    ParsingState,
    LatexArgumentSpec,
    ParsingStateDeltaLeaveMathMode,
    ParsedArguments,
)
from pylatexenc.latexnodes.nodes import *
from pylatexenc.macrospec import MacroSpec, LatexContextDb
from pylatexenc.latexwalker import LatexWalker

from ._helpers_tests import (
    DummyWalker,
    DummyLatexContextDb,
    add_not_equal_warning_to_object
)



add_not_equal_warning_to_object(LatexNode)
add_not_equal_warning_to_object(ParsingState)
add_not_equal_warning_to_object(ParsedArguments)
add_not_equal_warning_to_object(LatexArgumentSpec)



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


    def test_nested(self):
        
        latextext = r'''
$a=z \text{with \(c=1\)}$'''.lstrip()

        textmodeargspec = LatexArgumentSpec(
            argname=None,
            parser='{',
            parsing_state_delta=ParsingStateDeltaLeaveMathMode()
        )
        textmacrospec = MacroSpec(
            "text",
            arguments_spec_list=[
                textmodeargspec,
            ]
        )

        latex_context = LatexContextDb()
        latex_context.add_context_category(
            'main-context-category',
            macros=[
                textmacrospec
            ]
        )

        tr = LatexTokenReader(latextext)
        lw = LatexWalker(latextext, latex_context=latex_context, tolerant_parsing=False)
        ps = lw.make_parsing_state()

        parser = LatexMathParser(math_mode_delimiters=None)

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        psmath = nodes.nodelist[0].parsing_state
        self.assertTrue(psmath.in_math_mode)
        ps_child = nodes.nodelist[1].nodeargd.argnlist[0].parsing_state
        self.assertFalse(ps_child.in_math_mode)
        ps_child_math = (
            nodes.nodelist[1].nodeargd.argnlist[0] # group "{with \(..."
            .nodelist[1].parsing_state
        )
        self.assertTrue(ps_child_math.in_math_mode)

        nodes_ok = LatexMathNode(
            parsing_state=ps,
            latex_walker=lw,
            delimiters=(r'$',r'$'),
            displaytype='inline',
            nodelist=LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=psmath,
                        latex_walker=lw,
                        chars='a=z ',
                        pos=1,
                        pos_end=5,
                    ),
                    LatexMacroNode(
                        parsing_state=psmath,
                        latex_walker=lw,
                        macroname='text',
                        spec=textmacrospec,
                        nodeargd=ParsedArguments(
                            arguments_spec_list=[
                                textmodeargspec,
                            ],
                            argnlist=[
                                LatexGroupNode(
                                    parsing_state=ps_child,
                                    latex_walker=lw,
                                    delimiters=('{','}'),
                                    nodelist=LatexNodeList(
                                        [
                                            LatexCharsNode(
                                                parsing_state=ps_child,
                                                latex_walker=lw,
                                                chars='with ',
                                                pos=11,
                                                pos_end=16,
                                            ),
                                            LatexMathNode(
                                                parsing_state=ps_child_math,
                                                latex_walker=lw,
                                                delimiters=(r'\(',r'\)'),
                                                displaytype='inline',
                                                nodelist=LatexNodeList(
                                                    nodelist=[
                                                        LatexCharsNode(
                                                            parsing_state=ps_child_math,
                                                            latex_walker=lw,
                                                            chars='c=1',
                                                            pos=18,
                                                            pos_end=21,
                                                        ),
                                                    ],
                                                    pos=18,
                                                    pos_end=21,
                                                    parsing_state=ps_child_math,
                                                ),
                                                pos=16,
                                                pos_end=23,
                                            ),
                                        ]
                                    ),
                                    pos=10,
                                    pos_end=24,
                                ),
                            ]
                        ),
                        pos=5,
                        pos_end=24,
                    ),
                ],
                pos=1,
                pos_end=24,
            ),
            pos=0,
            pos_end=25,
        )

        print(nodes)
        print(nodes_ok)

        self.assertEqual(
            nodes,
            nodes_ok
        )

