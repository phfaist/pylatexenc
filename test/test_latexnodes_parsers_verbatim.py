import unittest
import logging


from pylatexenc.latexnodes.parsers._verbatim import (
    LatexVerbatimBaseParser,
    LatexDelimitedVerbatimParser,
    LatexVerbatimEnvironmentContentsParser,
)

from pylatexenc.latexnodes import (
    LatexWalkerParseError,
    LatexTokenReader,
    ParsingState,
)
from pylatexenc.latexnodes.nodes import *


from ._helpers_tests import (
    DummyWalker,
    DummyLatexContextDb,
)


class TestLatexVerbatimBaseParser(unittest.TestCase):

    def test_basic_1(self):
        latextext = r"$\%"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexVerbatimBaseParser()

        node, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        vps = node.parsing_state
        self.assertFalse(vps.enable_macros)
        self.assertFalse(vps.enable_environments)
        self.assertFalse(vps.enable_specials)
        self.assertFalse(vps.enable_groups)
        self.assertFalse(vps.enable_comments)
        self.assertFalse(vps.enable_math)
        self.assertFalse(vps.enable_double_newline_paragraphs)

        self.assertEqual(
            node,
            LatexCharsNode(
                parsing_state=vps,
                chars='$',
                pos=0,
                pos_end=1,
            )
        )

    def test_basic_2(self):
        latextext = r"\$%"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexVerbatimBaseParser()

        node, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        vps = node.parsing_state

        self.assertEqual(
            node,
            LatexCharsNode(
                parsing_state=vps,
                chars='\\',
                pos=0,
                pos_end=1,
            )
        )

    def test_end_of_stream(self):
        latextext = r""

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexVerbatimBaseParser()

        with self.assertRaises(LatexWalkerParseError):
            _, _ = lw.parse_content(parser, token_reader=tr, parsing_state=ps)





class TestLatexDelimitedVerbatimParser(unittest.TestCase):

    def test_simple_delimiters(self):
        latextext = r"|verbatim|"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedVerbatimParser()

        node, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        vps = node.nodelist[0].parsing_state

        self.assertFalse(vps.enable_macros)
        self.assertFalse(vps.enable_environments)
        self.assertFalse(vps.enable_specials)
        self.assertFalse(vps.enable_groups)
        self.assertFalse(vps.enable_comments)
        self.assertFalse(vps.enable_math)
        self.assertFalse(vps.enable_double_newline_paragraphs)

        self.assertEqual(
            node,
            LatexGroupNode(
                parsing_state=ps,
                delimiters=('|','|'),
                nodelist=LatexNodeList([
                    LatexCharsNode(
                        parsing_state=vps,
                        chars='verbatim',
                        pos=1,
                        pos_end=9,
                    )
                ]),
                pos=0,
                pos_end=10,
            )
        )
        
    def test_simple_delimiters_prespace(self):
        latextext = " \t |verbatim|"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedVerbatimParser()

        node, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        vps = node.nodelist[0].parsing_state

        self.assertEqual(
            node,
            LatexGroupNode(
                parsing_state=ps,
                delimiters=('|','|'),
                nodelist=LatexNodeList([
                    LatexCharsNode(
                        parsing_state=vps,
                        chars='verbatim',
                        pos=3+1,
                        pos_end=3+9,
                    )
                ]),
                pos=3+0,
                pos_end=3+10,
            )
        )
        
    def test_curlybrace_delimiters(self):
        latextext = "{verbatim}"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedVerbatimParser()

        node, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        vps = node.nodelist[0].parsing_state

        self.assertEqual(
            node,
            LatexGroupNode(
                parsing_state=ps,
                delimiters=('{','}'),
                nodelist=LatexNodeList([
                    LatexCharsNode(
                        parsing_state=vps,
                        chars='verbatim',
                        pos=1,
                        pos_end=9,
                    )
                ]),
                pos=0,
                pos_end=10,
            )
        )

    def test_special_contents(self):
        latextext = r"""<\$%*~+

%\)
verbatim>"""

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedVerbatimParser()

        node, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        vps = node.nodelist[0].parsing_state

        self.assertEqual(
            node,
            LatexGroupNode(
                parsing_state=ps,
                delimiters=('<','>'),
                nodelist=LatexNodeList([
                    LatexCharsNode(
                        parsing_state=vps,
                        chars=latextext[1:-1],
                        pos=1,
                        pos_end=len(latextext)-1,
                    )
                ]),
                pos=0,
                pos_end=len(latextext),
            )
        )
        

    def test_simple_delimiters_required_delims(self):
        latextext = r"{verbatim>"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedVerbatimParser(delimiters=('{','>'))

        node, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        vps = node.nodelist[0].parsing_state

        self.assertEqual(
            node,
            LatexGroupNode(
                parsing_state=ps,
                delimiters=('{','>'),
                nodelist=LatexNodeList([
                    LatexCharsNode(
                        parsing_state=vps,
                        chars='verbatim',
                        pos=1,
                        pos_end=9,
                    )
                ]),
                pos=0,
                pos_end=10,
            )
        )
        

    def test_simple_delimiters_auto_delims(self):
        latextext = r"`verbatim'"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexDelimitedVerbatimParser(auto_delimiters=[
            ('{','}'),
            ('<','>'),
            ('`','\''),
        ])

        node, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        vps = node.nodelist[0].parsing_state

        self.assertEqual(
            node,
            LatexGroupNode(
                parsing_state=ps,
                delimiters=('`','\''),
                nodelist=LatexNodeList([
                    LatexCharsNode(
                        parsing_state=vps,
                        chars='verbatim',
                        pos=1,
                        pos_end=9,
                    )
                ]),
                pos=0,
                pos_end=10,
            )
        )
        


class TestLatexVerbatimEnvironmentContentsParser(unittest.TestCase):

    def test_simple(self):
        # imagine that the following immediately follows "\begin{verbatim}"
        latextext = r"""
Hello world.\
\macro, \begin! This: % is not a comment; ~.\( all
special characters should be captured verbatim.
\end{verbatim}
"""

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexVerbatimEnvironmentContentsParser()

        node, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        vps = node.nodelist[0].parsing_state

        evpos = latextext.find(r'\end{verbatim}')

        self.assertEqual(
            node,
            LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=vps,
                        chars=latextext[1:evpos],
                        pos=1,
                        pos_end=evpos,
                    )
                ],
                pos=1,
                pos_end=evpos,
            )
        )        


    def test_simple_nofinaleol(self):
        # imagine that the following immediately follows "\begin{verbatim}" --
        # end of stream follows immediately after \end{verbatim}
        latextext = r"""
Hello world.\
\macro, \begin! This: % is not a comment; ~.\( all
special characters should be captured verbatim.
\end{verbatim}"""

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexVerbatimEnvironmentContentsParser()

        node, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        vps = node.nodelist[0].parsing_state

        evpos = latextext.find(r'\end{verbatim}')

        self.assertEqual(
            node,
            LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=vps,
                        chars=latextext[1:evpos],
                        pos=1,
                        pos_end=evpos,
                    )
                ],
                pos=1,
                pos_end=evpos,
            )
        )        



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
