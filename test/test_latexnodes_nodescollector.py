import unittest
import logging

logger = logging.getLogger(__name__)



from pylatexenc.latexnodes._nodescollector import (
    LatexNodesCollector
)

from pylatexenc.latexnodes import (
    LatexWalkerParseError,
    LatexTokenReader,
    ParsingState,
    ParsedArguments,
)
from pylatexenc.latexnodes.nodes import *

from ._helpers_tests import (
    DummyWalker,
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

        lw.mkgroup_assert_delimiters_equals = '{'

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
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

        lw.mkmath_assert_delimiters_equals = r'\('

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertFalse(ps.in_math_mode)

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

        lw.mkgroup_assert_delimiters_equals = '{'

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
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
                    nodeargd=ParsedArguments(),
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
                    nodeargd=ParsedArguments(),
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
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexSpecialsNode(
                    parsing_state=ps,
                    specials_chars='~',
                    nodeargd=ParsedArguments(),
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
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()
        parsing_state_delta = nc.get_parser_parsing_state_delta()

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
                    nodeargd=ParsedArguments(),
                    pos=0,
                    pos_end=13,
                ),
                LatexMacroNode(
                    parsing_state=ps2,
                    macroname='Z',
                    macro_post_space='',
                    spec=ps2.latex_context.get_macro_spec('Z'),
                    nodeargd=ParsedArguments(),
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

        self.assertIs(parsing_state_delta.set_parsing_state, ps2)
        

    # ---------- stop conditions -----------------

    def test_stops_on_token_condition(self):

        latextext = r'''Chars node'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        lw = DummyWalker()

        def my_stop_token_condition(token):
            if token.tok == 'char' and token.arg == 's':
                # stop upon 's'
                return True
            return False

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 stop_token_condition=my_stop_token_condition,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexCharsNode(
                    parsing_state=ps,
                    chars='Char',
                    pos=0,
                    pos_end=4,
                )
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), 4)
        self.assertFalse(nc.reached_end_of_stream())
        self.assertTrue(nc.stop_token_condition_met())
        self.assertFalse(nc.stop_nodelist_condition_met())

    def test_stops_on_token_condition_stopdata(self):

        latextext = r'''Chars node'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        lw = DummyWalker()

        def my_stop_token_condition(token):
            if token.tok == 'char' and token.arg in ('s', ' ', '\t', '\n'):
                # stop upon 's'
                return token.arg
            return False

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 stop_token_condition=my_stop_token_condition,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexCharsNode(
                    parsing_state=ps,
                    chars='Char',
                    pos=0,
                    pos_end=4,
                )
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), 4)
        self.assertFalse(nc.reached_end_of_stream())
        self.assertTrue(nc.stop_token_condition_met())
        self.assertFalse(nc.stop_nodelist_condition_met())

        self.assertEqual(nc.stop_condition_stop_data(), 's')

    def test_stops_on_token_condition_withprespacechars(self):

        latextext = r'''some characters'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        lw = DummyWalker()

        def my_stop_token_condition(token):
            if token.tok == 'char' and token.arg == 'c':
                # stop upon 'c' after space.
                return True
            return False

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 stop_token_condition=my_stop_token_condition,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexCharsNode(
                    parsing_state=ps,
                    chars='some ',
                    pos=0,
                    pos_end=5,
                )
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), 5)
        self.assertFalse(nc.reached_end_of_stream())
        self.assertTrue(nc.stop_token_condition_met())
        self.assertFalse(nc.stop_nodelist_condition_met())

    def test_stops_on_token_condition_noprespacechars(self):

        latextext = r'''some characters'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        lw = DummyWalker()

        def my_stop_token_condition(token):
            if token.tok == 'char' and token.arg == 'c':
                # stop upon 'c' after space.
                return True
            return False

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 stop_token_condition=my_stop_token_condition,
                                 include_stop_token_pre_space_chars=False,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexCharsNode(
                    parsing_state=ps,
                    chars='some',
                    pos=0,
                    pos_end=4,
                )
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), 4)
        self.assertFalse(nc.reached_end_of_stream())
        self.assertTrue(nc.stop_token_condition_met())
        self.assertFalse(nc.stop_nodelist_condition_met())


    def test_stops_on_nodelist_condition(self):

        latextext = r'''Hello \yourname, how are you?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        def my_stop_nodelist_condition(nodelist):
            if len(nodelist) >= 2:
                # stop after the second node
                return 2
            return False

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 stop_nodelist_condition=my_stop_nodelist_condition,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexCharsNode(
                    parsing_state=ps,
                    chars='Hello ',
                    pos=0,
                    pos_end=6,
                ),
                LatexMacroNode(
                    parsing_state=ps,
                    macroname='yourname',
                    macro_post_space='',
                    spec=ps.latex_context.get_macro_spec('yourname'),
                    nodeargd=ParsedArguments(),
                    pos=6,
                    pos_end=15,
                ),
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), 15)
        self.assertFalse(nc.reached_end_of_stream())
        self.assertFalse(nc.stop_token_condition_met())
        self.assertTrue(nc.stop_nodelist_condition_met())
        self.assertEqual(nc.stop_condition_stop_data(), 2)




    # ---------- child parsing state -------------

    def test_makes_child_parsing_state_group(self):
        latextext = r'''Hello {}.'''
        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        # let's set a flag such as in_math_mode to distinguish child_ps from ps
        child_ps = ps.sub_context(in_math_mode=True)

        def my_make_child_parsing_state(parsing_state, node_class):
            self.assertIs(parsing_state, ps)
            if node_class is LatexGroupNode:
                return child_ps
            self.assertTrue(False) # Didn't expect this node class with our latex input code

        lw.mkgroup_assert_delimiters_equals = '{'

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 make_child_parsing_state=my_make_child_parsing_state,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexCharsNode(
                    parsing_state=ps,
                    chars='Hello ',
                    pos=0,
                    pos_end=6,
                ),
                LatexGroupNode(
                    parsing_state=child_ps,
                    delimiters=('{','}'),
                    pos=6,
                    pos_end=8,
                    nodelist=LatexNodeList([], pos='<POS>', pos_end='<POS_END>'),
                ),
                LatexCharsNode(
                    parsing_state=ps,
                    chars='.',
                    pos=8,
                    pos_end=9,
                ),
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), 9)
        self.assertTrue(nc.reached_end_of_stream())

    def test_makes_child_parsing_state_macro(self):
        latextext = r'''Hello \yourname.'''
        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        # let's set a flag such as in_math_mode to distinguish macro_ps from ps
        macro_ps = ps.sub_context(in_math_mode=True)

        def my_make_child_parsing_state(parsing_state, node_class):
            self.assertIs(parsing_state, ps)
            if node_class is LatexMacroNode:
                return macro_ps
            self.assertTrue(False and "Didn't expect a non-macro in our latex example")

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 make_child_parsing_state=my_make_child_parsing_state,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexCharsNode(
                    parsing_state=ps,
                    chars='Hello ',
                    pos=0,
                    pos_end=6,
                ),
                LatexMacroNode(
                    parsing_state=macro_ps,
                    macroname='yourname',
                    macro_post_space='',
                    spec=ps.latex_context.get_macro_spec('yourname'),
                    nodeargd=ParsedArguments(),
                    pos=6,
                    pos_end=15,
                ),
                LatexCharsNode(
                    parsing_state=ps,
                    chars='.',
                    pos=15,
                    pos_end=16,
                ),
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), 16)
        self.assertTrue(nc.reached_end_of_stream())

    def test_makes_child_parsing_state_environ(self):
        latextext = r'''Hello \begin{someenv}\end{someenv}.'''
        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        # let's set a flag such as in_math_mode to distinguish child_ps from ps
        child_ps = ps.sub_context(in_math_mode=True)

        def my_make_child_parsing_state(parsing_state, node_class):
            self.assertIs(parsing_state, ps)
            if node_class is LatexEnvironmentNode:
                return child_ps
            self.assertTrue(False) # Didn't expect this node class in our latex example

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 make_child_parsing_state=my_make_child_parsing_state,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexCharsNode(
                    parsing_state=ps,
                    chars='Hello ',
                    pos=0,
                    pos_end=6,
                ),
                LatexEnvironmentNode(
                    parsing_state=child_ps,
                    environmentname='someenv',
                    spec=ps.latex_context.get_environment_spec('someenv'),
                    nodeargd=ParsedArguments(),
                    nodelist=LatexNodeList([]),
                    pos=6,
                    pos_end=34,
                ),
                LatexCharsNode(
                    parsing_state=ps,
                    chars='.',
                    pos=34,
                    pos_end=35,
                ),
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), 35)
        self.assertTrue(nc.reached_end_of_stream())

    def test_makes_child_parsing_state_specials(self):
        latextext = r'''Hello ~.'''
        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        # let's set a flag such as in_math_mode to distinguish child_ps from ps
        child_ps = ps.sub_context(in_math_mode=True)

        def my_make_child_parsing_state(parsing_state, node_class):
            self.assertIs(parsing_state, ps)
            if node_class is LatexSpecialsNode:
                return child_ps
            self.assertTrue(False) # Didn't expect this node_class in our latex example

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 make_child_parsing_state=my_make_child_parsing_state,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexCharsNode(
                    parsing_state=ps,
                    chars='Hello ',
                    pos=0,
                    pos_end=6,
                ),
                LatexSpecialsNode(
                    parsing_state=child_ps,
                    specials_chars='~',
                    spec=ps.latex_context.get_specials_spec('~'),
                    nodeargd=ParsedArguments(),
                    pos=6,
                    pos_end=7,
                ),
                LatexCharsNode(
                    parsing_state=ps,
                    chars='.',
                    pos=7,
                    pos_end=8,
                ),
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), 8)
        self.assertTrue(nc.reached_end_of_stream())

    def test_makes_child_parsing_state_math(self):
        latextext = r'''Hello \(\).'''
        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        # let's set a speicifc flag such as enable_comments to distinguish
        # child_ps from ps
        child_ps = ps.sub_context(enable_comments=False)

        def my_make_child_parsing_state(parsing_state, node_class):
            # the nodes collection should already have provided a
            # math-mode-enabled parsing state
            self.assertTrue(parsing_state.in_math_mode)
            if node_class is LatexMathNode:
                return child_ps
            self.assertTrue(False) # Didn't expect this node class with our latex input code

        lw.mkmath_assert_delimiters_equals = r'\('

        nc = LatexNodesCollector(latex_walker=lw,
                                 token_reader=tr,
                                 parsing_state=ps,
                                 make_child_parsing_state=my_make_child_parsing_state,
                                 )

        nc.process_tokens()
        
        nodelist = nc.get_final_nodelist()

        self.assertEqual(
            nodelist,
            LatexNodeList([
                LatexCharsNode(
                    parsing_state=ps,
                    chars='Hello ',
                    pos=0,
                    pos_end=6,
                ),
                LatexMathNode(
                    parsing_state=child_ps,
                    delimiters=(r'\(',r'\)'),
                    displaytype='inline',
                    pos=6,
                    pos_end=10,
                    nodelist=LatexNodeList([], pos='<POS>', pos_end='<POS_END>'),
                ),
                LatexCharsNode(
                    parsing_state=ps,
                    chars='.',
                    pos=10,
                    pos_end=11,
                ),
            ])
        )
        self.assertEqual(nc.pos_start(), 0)
        self.assertEqual(nc.pos_end(), 11)
        self.assertTrue(nc.reached_end_of_stream())

# ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
