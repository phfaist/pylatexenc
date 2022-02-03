import unittest
import sys
import logging



from pylatexenc.latexnodes._nodescollector import (
    LatexNodesCollector
)

from pylatexenc.latexnodes import (
    LatexTokenReader,
    LatexNodeList,
    LatexCharsNode,
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

        nodes, info = parser(latex_walker=self,
                             token_reader=token_reader,
                             parsing_state=parsing_state)

        return nodes, info



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
                    len=len(latextext)
                )
            ])
        )
        
    



# ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
