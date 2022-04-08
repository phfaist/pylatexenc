import unittest
import sys
import logging


from pylatexenc.latexnodes.parsers._delimitedgroup import (
    LatexDelimitedGroupParser,
)

from pylatexenc.latexnodes import (
    LatexWalkerParseError,
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



class TestDelimitedGroupParser(unittest.TestCase):

    def test_simple_1(self):

        latextext = r'''{Hello there}'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedGroupParser(
            delimiters=('{','}')
        )

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                delimiters=('{','}'),
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=ps,
                            chars='Hello there',
                            pos=1,
                            pos_end=36-24,
                        ),
                    ],
                    pos=1,
                    pos_end=36-24,
                ),
                pos=0,
                pos_end=37-24,
            )
        )

    def test_stops_after_group(self):

        latextext = r'''{Hello there} did the parser stop after the group?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedGroupParser(
            delimiters=('{','}')
        )

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                delimiters=('{','}'),
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=ps,
                            chars='Hello there',
                            pos=1,
                            pos_end=36-24,
                        ),
                    ],
                    pos=1,
                    pos_end=36-24,
                ),
                pos=0,
                pos_end=37-24,
            )
        )

    def test_optional_and_group_is_present(self):

        latextext = r'''{Hello there} did the parser stop after the group?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedGroupParser(
            delimiters=('{','}'),
            optional=True,
        )

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                delimiters=('{','}'),
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=ps,
                            chars='Hello there',
                            pos=1,
                            pos_end=36-24,
                        ),
                    ],
                    pos=1,
                    pos_end=36-24,
                ),
                pos=0,
                pos_end=37-24,
            )
        )

    def test_optional_and_group_is_not_present(self):

        latextext = r''' did the parser stop after the group?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedGroupParser(
            delimiters=('{','}'),
            optional=True,
        )

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            None
        )


    def test_automatic_detection_of_delimiters(self):

        latextext = r'''<Hello there> did the parser stop after the group?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext,
                          latex_context=DummyLatexContextDb(),
                          latex_group_delimiters=[('{','}'),('<','>')],
                          )
        lw = DummyWalker()

        parser = LatexDelimitedGroupParser(delimiters=None)

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                delimiters=('<','>'),
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=ps,
                            chars='Hello there',
                            pos=1,
                            pos_end=36-24,
                        ),
                    ],
                    pos=1,
                    pos_end=36-24,
                ),
                pos=0,
                pos_end=37-24,
            )
        )

    def test_automatic_closing_delimiter(self):

        latextext = r'''[Hello there] did the parser stop after the group?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext,
                          latex_context=DummyLatexContextDb(),
                          latex_group_delimiters=[('{','}'),('[',']')],
                          )
        lw = DummyWalker()

        parser = LatexDelimitedGroupParser(delimiters='[')

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                delimiters=('[',']'),
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=ps,
                            chars='Hello there',
                            pos=1,
                            pos_end=36-24,
                        ),
                    ],
                    pos=1,
                    pos_end=36-24,
                ),
                pos=0,
                pos_end=37-24,
            )
        )

    def test_skip_space_albeit_unnecessary(self):

        latextext = r'''{Hello there} did the parser stop after the group?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedGroupParser(
            delimiters=('{','}'),
            allow_pre_space=True,
        )

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                delimiters=('{','}'),
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=ps,
                            chars='Hello there',
                            pos=1,
                            pos_end=36-24,
                        ),
                    ],
                    pos=1,
                    pos_end=36-24,
                ),
                pos=0,
                pos_end=37-24,
            )
        )

    def test_does_not_skip_space_by_default(self):

        latextext = r'''   {Hello there} did the parser stop after the group?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedGroupParser(
            delimiters=('{','}'),
        )

        with self.assertRaises(LatexWalkerParseError):
            nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

    def test_skip_space_and_group_has_pre_space(self):

        latextext = r'''   {Hello there} did the parser stop after the group?'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedGroupParser(
            delimiters=('{','}'),
            allow_pre_space=True,
        )

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        # pre-space simply gets discarded, which is a strong reason not to use
        # this option at all; prefer to use robust argument parsers that can
        # keep spaces & comments between arguments. ...

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                delimiters=('{','}'),
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=ps,
                            chars='Hello there',
                            pos=1+3,
                            pos_end=36-24+3,
                        ),
                    ],
                    pos=1+3,
                    pos_end=36-24+3,
                ),
                pos=0+3,
                pos_end=37-24+3,
            )
        )





    def test_are_these_tests_really_complete(self):
        
        # WRITE ME
        self.assertTrue( False )
