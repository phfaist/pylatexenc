import unittest
import sys
import logging

logger = logging.getLogger(__name__)



from pylatexenc.latexnodes._nodescollector import (
    LatexNodesCollector
)

from pylatexenc.latexnodes import (
    LatexWalkerParseError,
    LatexTokenReader,
    LatexNodeList,
    LatexCharsNode,
    LatexGroupNode,
    LatexMathNode,
    LatexCommentNode,
    LatexMacroNode,
    LatexEnvironmentNode,
    LatexSpecialsNode,
    ParsingState,
    ParsedMacroArgs,
)


from ._helpers_tests import (
    DummyWalker,
    dummy_empty_group_parser,
    dummy_empty_mathmode_parser,
    DummyLatexContextDb,
)



class TestLatexNodesCollector(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestLatexNodesCollector, self).__init__(*args, **kwargs)

        self.maxDiff = None

    def test_simple_charsnode(self):
        
        latextext = r'''Chars node'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        lw = DummyWalker()

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 make_group_parser=None,
                                 make_math_parser=None,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexCharsNode(
                    parsing_state=ps,
                    chars='Chars node',
                    pos=0,
                    pos_end=len(latextext)
                )
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), len(latextext))
        self.assertTrue(nc.reached_end_of_stream())
        self.assertFalse(nc.stop_token_condition_met())
        self.assertFalse(nc.stop_nodelist_condition_met())

    def test_simple_comment_node(self):
        
        latextext = '''% Comment node\n    '''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        lw = DummyWalker()

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 make_group_parser=None,
                                 make_math_parser=None,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexCommentNode(
                    parsing_state=ps,
                    comment=' Comment node',
                    comment_post_space='\n    ',
                    pos=0,
                    pos_end=len(latextext),
                )
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), len(latextext))
        self.assertTrue(nc.reached_end_of_stream())
        self.assertFalse(nc.stop_token_condition_met())
        self.assertFalse(nc.stop_nodelist_condition_met())

    def test_simple_group_node(self):
        
        latextext = '''{}'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        lw = DummyWalker()

        def make_dummy_empty_group_parser(require_delimiter_type):
            self.assertEqual(require_delimiter_type, '{')
            return dummy_empty_group_parser

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 make_group_parser=make_dummy_empty_group_parser,
                                 make_math_parser=None,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexGroupNode(
                    parsing_state=ps,
                    nodelist=LatexNodeList([], pos='<POS>', pos_end='<POS_END>'),
                    delimiters=('{','}'),
                    pos=0,
                    pos_end=2,
                )
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), len(latextext))
        self.assertTrue(nc.reached_end_of_stream())
        self.assertFalse(nc.stop_token_condition_met())
        self.assertFalse(nc.stop_nodelist_condition_met())

    def test_simple_math_node(self):
        
        latextext = r'''\(\)'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        lw = DummyWalker()

        def make_dummy_empty_mathmode_parser(require_math_mode_delimiter):
            self.assertEqual(require_math_mode_delimiter, r'\(')
            return dummy_empty_mathmode_parser

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 make_group_parser=None,
                                 make_math_parser=make_dummy_empty_mathmode_parser,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexMathNode(
                    parsing_state=ps,
                    nodelist=LatexNodeList([], pos='<POS>', pos_end='<POS_END>'),
                    delimiters=(r'\(',r'\)'),
                    displaytype='inline',
                    pos=0,
                    pos_end=4,
                )
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), len(latextext))
        self.assertTrue(nc.reached_end_of_stream())
        self.assertFalse(nc.stop_token_condition_met())
        self.assertFalse(nc.stop_nodelist_condition_met())
        
    def test_final_whitespace_after_chars(self):
        
        latextext = '''Chars node       \t\n    '''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        lw = DummyWalker()

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 make_group_parser=None,
                                 make_math_parser=None,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexCharsNode(
                    parsing_state=ps,
                    chars='Chars node       \t\n    ',
                    pos=0,
                    pos_end=len(latextext)
                )
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), len(latextext))
        self.assertTrue(nc.reached_end_of_stream())
        self.assertFalse(nc.stop_token_condition_met())
        self.assertFalse(nc.stop_nodelist_condition_met())

    def test_final_whitespace_after_group(self):
        
        latextext = '''{}       \t\n    '''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        lw = DummyWalker()

        def make_dummy_empty_group_parser(require_delimiter_type):
            self.assertEqual(require_delimiter_type, '{')
            return dummy_empty_group_parser


        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 make_group_parser=make_dummy_empty_group_parser,
                                 make_math_parser=None,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexGroupNode(
                    parsing_state=ps,
                    nodelist=LatexNodeList([], pos='<POS>', pos_end='<POS_END>'),
                    delimiters=('{','}'),
                    pos=0,
                    pos_end=2,
                ),
                LatexCharsNode(
                    parsing_state=ps,
                    chars='       \t\n    ',
                    pos=2,
                    pos_end=len(latextext)
                )
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), len(latextext))
        self.assertTrue(nc.reached_end_of_stream())
        self.assertFalse(nc.stop_token_condition_met())
        self.assertFalse(nc.stop_nodelist_condition_met())


    #
    # test macros and other callables
    #

    def test_simple_macro_node(self):
        
        latextext = r'''\somemacro    '''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 make_group_parser=None,
                                 make_math_parser=None,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexMacroNode(
                    parsing_state=ps,
                    macroname='somemacro',
                    macro_post_space='    ',
                    spec=ps.latex_context.get_macro_spec('somemacro'),
                    nodeargd=ParsedMacroArgs(),
                    pos=0,
                    pos_end=len(latextext),
                )
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), len(latextext))
        self.assertTrue(nc.reached_end_of_stream())
        self.assertFalse(nc.stop_token_condition_met())
        self.assertFalse(nc.stop_nodelist_condition_met())

    def test_simple_environment_node(self):
        
        latextext = r'''\begin{someenv}\end{someenv}'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 make_group_parser=None,
                                 make_math_parser=None,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexEnvironmentNode(
                    parsing_state=ps,
                    environmentname='someenv',
                    spec=ps.latex_context.get_environment_spec('someenv'),
                    nodeargd=ParsedMacroArgs(),
                    nodelist=LatexNodeList([]),
                    pos=0,
                    pos_end=len(latextext),
                )
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), len(latextext))
        self.assertTrue(nc.reached_end_of_stream())
        self.assertFalse(nc.stop_token_condition_met())
        self.assertFalse(nc.stop_nodelist_condition_met())


    def test_simple_specials_node(self):
        
        latextext = r'''~'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 make_group_parser=None,
                                 make_math_parser=None,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexSpecialsNode(
                    parsing_state=ps,
                    specials_chars='~',
                    nodeargd=ParsedMacroArgs(),
                    spec=ps.latex_context.get_specials_spec('~'),
                    pos=0,
                    pos_end=len(latextext),
                )
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), len(latextext))
        self.assertTrue(nc.reached_end_of_stream())
        self.assertFalse(nc.stop_token_condition_met())
        self.assertFalse(nc.stop_nodelist_condition_met())



    def test_macro_simple_unknown(self):
        
        latextext = r'''\unknownmacronameshouldraiseexception'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 make_group_parser=None,
                                 make_math_parser=None,
                                 )

        with self.assertRaises(LatexWalkerParseError):
            nc.process_tokens()


    def test_macro_simple_state_change(self):
        
        latextext = r'''\definemacroZ\Z'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 make_group_parser=None,
                                 make_math_parser=None,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()
        carryover_info = nc.get_parser_carryover_info()

        ps2 = nodelist[1].parsing_state
        self.assertIsNot(ps, ps2)

        self.assertIsNone(ps.latex_context.get_macro_spec('Z'))
        self.assertIsNotNone(ps2.latex_context.get_macro_spec('Z'))
        
        self.assertEqual(
            nodelist[:],
            LatexNodeList([
                LatexMacroNode(
                    parsing_state=ps,
                    macroname='definemacroZ',
                    macro_post_space='',
                    spec=ps.latex_context.get_macro_spec('definemacroZ'),
                    nodeargd=ParsedMacroArgs(),
                    pos=0,
                    pos_end=13,
                ),
                LatexMacroNode(
                    parsing_state=ps2,
                    macroname='Z',
                    macro_post_space='',
                    spec=ps2.latex_context.get_macro_spec('Z'),
                    nodeargd=ParsedMacroArgs(),
                    pos=13,
                    pos_end=15,
                )
            ])[:]
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), len(latextext))
        self.assertTrue(nc.reached_end_of_stream())
        self.assertFalse(nc.stop_token_condition_met())
        self.assertFalse(nc.stop_nodelist_condition_met())

        self.assertIs(carryover_info.set_parsing_state, ps2)
        

# ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
