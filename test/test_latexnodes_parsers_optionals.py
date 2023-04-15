import unittest
import logging


from pylatexenc.latexnodes.parsers._optionals import (
    LatexOptionalCharsMarkerParser,
    LatexOptionalSquareBracketsParser,
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

class TestLatexOptionalCharsMarkerParser(unittest.TestCase):
    
    maxDiff = None

    def test_simple_chars_marker_isthere(self):

        latextext = r'''*more'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexOptionalCharsMarkerParser('*')

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=ps,
                        chars='*',
                        pos=0,
                        pos_end=1,
                    )
                ],
                parsing_state=ps
            )
        )


    def test_simple_chars_marker_notthere(self):

        latextext = r'''more'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexOptionalCharsMarkerParser('*')

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            None,
        )

    def test_simple_chars_marker_notthere_reqempty(self):

        latextext = r'''more'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexOptionalCharsMarkerParser('*', return_none_instead_of_empty=False)

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList([], parsing_state=ps, pos=0, pos_end=0),
        )


    def test_simple_chars_marker_isthere_notlist(self):

        latextext = r'''*more'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexOptionalCharsMarkerParser('*', return_full_node_list=False)

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexCharsNode(
                parsing_state=ps,
                chars='*',
                pos=0,
                pos_end=1,
            )
        )


    def test_simple_chars_marker_notthere_notlist(self):

        latextext = r'''more'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexOptionalCharsMarkerParser('*', return_full_node_list=False)

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            None,
        )




# ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
