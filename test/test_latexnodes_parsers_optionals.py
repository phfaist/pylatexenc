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


    def test_chars_marker_normalizes_chars_list(self):

        parser = LatexOptionalCharsMarkerParser([' * ', '  ', '+'])

        # markers that are empty after whitespace normalization are dropped
        self.assertEqual(parser.chars_list, ['*', '+'])

        with self.assertRaises(ValueError):
            LatexOptionalCharsMarkerParser(['  '])


    def test_chars_marker_each_marker_read_at_most_once(self):

        latextext = r'''*+*more'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexOptionalCharsMarkerParser(['*', '+'])

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        # the second ‘*’ is not read again, it is left in the token stream
        self.assertEqual(
            nodes,
            LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=ps,
                        chars='*',
                        pos=0,
                        pos_end=1,
                    ),
                    LatexCharsNode(
                        parsing_state=ps,
                        chars='+',
                        pos=1,
                        pos_end=2,
                    ),
                ],
                parsing_state=ps
            )
        )
        self.assertEqual(tr.cur_pos(), 2)


    def test_chars_marker_at_end_of_input(self):

        latextext = r'''*'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        # a second marker is still expected when the end of the input is reached
        parser = LatexOptionalCharsMarkerParser(['*', '+'])

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
                    ),
                ],
                parsing_state=ps
            )
        )


    def test_chars_marker_incomplete_at_end_of_input(self):

        latextext = r'''ca'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        # after ‘c’ was read, the input ends in the middle of a possible ‘ab’
        # marker
        parser = LatexOptionalCharsMarkerParser(['ab', 'c'])

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
                    ),
                ],
                parsing_state=ps
            )
        )
        self.assertEqual(tr.cur_pos(), 1)


    def test_chars_marker_matches_longest_marker(self):

        latextext = r'''abmore'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        # the shorter marker ‘a’ is listed after ‘ab’, but even if it were
        # listed first, the longest marker that matches should be picked
        parser = LatexOptionalCharsMarkerParser(['a', 'ab'])

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=ps,
                        chars='ab',
                        pos=0,
                        pos_end=2,
                    ),
                ],
                parsing_state=ps
            )
        )
        self.assertEqual(tr.cur_pos(), 2)


    def test_chars_marker_matches_shorter_marker_if_longer_doesnt_match(self):

        latextext = r'''axmore'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        # we need to read the ‘x’ to find out that the marker ‘ab’ doesn't
        # match; the token reader must then be moved back after the ‘a’
        parser = LatexOptionalCharsMarkerParser(['ab', 'a'])

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=ps,
                        chars='a',
                        pos=0,
                        pos_end=1,
                    ),
                ],
                parsing_state=ps
            )
        )
        self.assertEqual(tr.cur_pos(), 1)


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
