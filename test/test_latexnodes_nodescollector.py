import unittest
import sys
import logging

logger = logging.getLogger(__name__)



from pylatexenc.latexnodes._nodescollector import (
    LatexNodesCollector
)

from pylatexenc.latexnodes import (
    LatexTokenReader,
    LatexNodeList,
    LatexCharsNode,
    LatexGroupNode,
    LatexMathNode,
    LatexCommentNode,
    LatexMacroNode,
    LatexEnvironmentNode,
    LatexSpecialsNode,
    LatexWalkerBase,
    ParsingState
)


class DummyWalker(LatexWalkerBase):

    def make_node(self, node_class, **kwargs):
        return node_class(**kwargs)

    def make_nodes_collector(self,
                             latex_walker,
                             token_reader,
                             parsing_state,
                             **kwargs):
        return latexnodes.LatexNodesCollector(
            latex_walker,
            token_reader,
            parsing_state,
            **kwargs
        )

    def parse_content(self, parser, token_reader=None, parsing_state=None,
                      open_context=None):

        if open_context is not None:
            what, tok = open_context
            logger.debug("Parsing content -- %s -- (%r)", what, tok)
        else:
            logger.debug("Parsing content (%s) ...", parser.__class__.__name__)

        nodes, carryover_info = parser(latex_walker=self,
                                       token_reader=token_reader,
                                       parsing_state=parsing_state)

        logger.debug("Parsing content done (%s).", parser.__class__.__name__)

        return nodes, carryover_info




def dummy_empty_group_parser(latex_walker, token_reader, parsing_state):
    first_token = token_reader.next_token(parsing_state=parsing_state)
    second_token = token_reader.next_token(parsing_state=parsing_state)

    if first_token.tok == 'brace_open' and second_token.tok == 'brace_close':
        # good
        n = latex_walker.make_node(
            LatexGroupNode,
            delimiters=(first_token.arg, second_token.arg),
            nodelist=LatexNodeList([], pos='<POS>', pos_end='<POS_END>'),
            pos=first_token.pos,
            pos_end=second_token.pos_end,
            parsing_state=parsing_state
        )
        return n, None

    raise RuntimeError("dummy empty group parser: expected an empty group.")

def dummy_empty_mathmode_parser(latex_walker, token_reader, parsing_state):
    first_token = token_reader.next_token(parsing_state=parsing_state)
    second_token = token_reader.next_token(parsing_state=parsing_state)

    if first_token.tok in ('mathmode_inline','mathmode_display') \
       and second_token.tok == ('mathmode_inline', 'mathmode_display'):
        # good
        n = latex_walker.make_node(
            LatexMathNode,
            delimiters=(first_token.arg, second_token.arg),
            nodelist=LatexNodeList([], pos='<POS>', pos_end='<POS_END>'),
            pos=first_token.pos,
            pos_end=second_token.pos_end,
            parsing_state=parsing_state
        )
        return n, None

    raise RuntimeError("dummy math mode group parser: expected an empty math mode group.")



class TestLatexNodesCollector(unittest.TestCase):

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

    def test_simple_group_node(self):
        
        latextext = '''{}'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        lw = DummyWalker()

        def make_dummy_empty_group_parser(require_brace_type):
            self.assertEqual(require_brace_type, '{')
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
            



# ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
