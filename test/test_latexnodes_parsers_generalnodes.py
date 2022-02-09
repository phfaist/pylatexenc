import unittest
import sys
import logging


from pylatexenc.latexnodes.parsers._generalnodes import (
    LatexGeneralNodesParser,
    LatexSingleNodeParser,
    LatexDelimitedGroupParser,
    LatexMathParser,
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
    dummy_empty_group_parser,
    dummy_empty_mathmode_parser,
    DummyLatexContextDb,
)


class TestGeneralNodesParser(unittest.TestCase):

    def test_gets_nodes_with_stuff(self):
        latextext = r'''Hello there, \yourname. What's that about {A}?'''

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
                    nodelist=LatexNodeList([
                        LatexCharsNode(
                            parsing_state=ps,
                            chars="A",
                            pos=67-24,
                            pos_end=68-24,
                        ),
                    ]),
                    pos=66-24,
                    pos_end=69-24,
                ),
                LatexCharsNode(
                    parsing_state=ps,
                    chars="?",
                    pos=69-24,
                    pos_end=70-24,
                ),
            ])
        )




if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
