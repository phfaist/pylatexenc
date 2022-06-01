import unittest
import logging


from pylatexenc.latexnodes.parsers._stdarg import (
    #get_standard_argument_parser,
    LatexStandardArgumentParser,
    LatexCharsCommaSeparatedListParser,
    #LatexCharsGroupParser,
)
from pylatexenc.latexnodes import parsers

from pylatexenc.latexnodes import (
    LatexWalkerNodesParseError,
    LatexTokenReader,
    ParsingState,
)
from pylatexenc.latexnodes.nodes import *

from ._helpers_tests import (
    DummyWalker,
    DummyLatexContextDb,
)


class DummyWalkerWithGroupsAndMath(DummyWalker):
    make_latex_group_parser = parsers.LatexDelimitedGroupParser
    make_latex_math_parser = parsers.LatexMathParser



class TestLatexStandardArgumentParser(unittest.TestCase):

    def test_arg_m_0(self):
        latextext = r'''{mandatory argument} (more stuff)'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexStandardArgumentParser(arg_spec='m')

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=ps,
                            chars='mandatory argument',
                            pos=1,
                            pos_end=19,
                        )
                    ],
                    pos=1,
                    pos_end=19,
                ),
                delimiters=('{','}'),
                pos=0,
                pos_end=20,
            )
        )

    def test_arg_openbrace_0(self):
        latextext = r'''{mandatory argument} (more stuff)'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexStandardArgumentParser(arg_spec='{')

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=ps,
                            chars='mandatory argument',
                            pos=1,
                            pos_end=19,
                        )
                    ],
                    pos=1,
                    pos_end=19,
                ),
                delimiters=('{','}'),
                pos=0,
                pos_end=20,
            )
        )


    def test_arg_m_precomment_noincludeskip(self):
        latextext = r'''%comment here
{mandatory argument} (more stuff)'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexStandardArgumentParser(arg_spec='m', include_skipped_comments=False)

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=ps,
                            chars='mandatory argument',
                            pos=14+1,
                            pos_end=14+19,
                        )
                    ],
                    pos=14+1,
                    pos_end=14+19,
                ),
                delimiters=('{','}'),
                pos=14+0,
                pos_end=14+20,
            )
        )

    def test_arg_m_precomment_includeskip(self):
        latextext = r'''%comment here
{mandatory argument} (more stuff)'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexStandardArgumentParser(arg_spec='m') # i.e. include_skipped_comments=True

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                delimiters=('',''),
                nodelist=LatexNodeList(
                    [
                        LatexCommentNode(
                            parsing_state=ps,
                            comment='comment here',
                            comment_post_space='\n',
                            pos=0,
                            pos_end=14,
                        ),
                        LatexGroupNode(
                            parsing_state=ps,
                            nodelist=LatexNodeList(
                                [
                                    LatexCharsNode(
                                        parsing_state=ps,
                                        chars='mandatory argument',
                                        pos=14+1,
                                        pos_end=14+19,
                                    )
                                ],
                                pos=14+1,
                                pos_end=14+19,
                            ),
                            delimiters=('{','}'),
                            pos=14,
                            pos_end=14+20,
                        )
                    ],
                    pos=0,
                    pos_end=14+20,
                ),
                pos=0,
                pos_end=14+20
            )
        )



class TestLatexCharsCommaSeparatedListParser(unittest.TestCase):

    def test_stuff(self):
        latextext = "{a;b}"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexCharsCommaSeparatedListParser(
            comma_char=';',
            enable_groups=True,
            enable_comments=True,
        )

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        cps = nodes.nodelist[0].parsing_state
        self.assertFalse(cps.enable_macros)
        self.assertFalse(cps.enable_environments)
        self.assertTrue(cps.enable_groups)
        self.assertTrue(cps.enable_comments)

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                nodelist=LatexNodeList(
                    [
                        LatexGroupNode(
                            parsing_state=cps,
                            nodelist=LatexNodeList(
                                [
                                    LatexCharsNode(
                                        parsing_state=cps,
                                        chars='a',
                                        pos=1,
                                        pos_end=2,
                                    )
                                ],
                                pos=1,
                                pos_end=2,
                            ),
                            delimiters=('',';'),
                            pos=1,
                            pos_end=3,
                        ),
                        LatexGroupNode(
                            parsing_state=cps,
                            nodelist=LatexNodeList(
                                [
                                    LatexCharsNode(
                                        parsing_state=cps,
                                        chars='b',
                                        pos=3,
                                        pos_end=4,
                                    )
                                ],
                                pos=3,
                                pos_end=4,
                            ),
                            delimiters=('',''),
                            pos=3,
                            pos_end=4,
                        ),
                    ],
                    pos=1,
                    pos_end=4,
                ),
                delimiters=('{','}'),
                pos=0,
                pos_end=5,
            )
        )


    def test_empty_argument(self):
        latextext = "{}"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexCharsCommaSeparatedListParser(
            comma_char=',',
            enable_groups=True,
            enable_comments=True,
        )

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        print(nodes)
        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                nodelist=LatexNodeList([], pos=1, pos_end=1),
                delimiters=('{','}'),
                pos=0,
                pos_end=2,
            )
        )


    def test_zmore_stuff(self):
        latextext = r"""{d{zz};% ;comment;
}"""

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexCharsCommaSeparatedListParser(
            comma_char=';',
            enable_groups=True,
            enable_comments=True,
        )

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        cps = nodes.nodelist[0].parsing_state
        self.assertFalse(cps.enable_macros)
        self.assertFalse(cps.enable_environments)
        self.assertTrue(cps.enable_groups)
        self.assertTrue(cps.enable_comments)


        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                nodelist=LatexNodeList(
                    [
                        LatexGroupNode(
                            parsing_state=cps,
                            nodelist=LatexNodeList(
                                [
                                    LatexCharsNode(
                                        parsing_state=cps,
                                        chars='d',
                                        pos=1,
                                        pos_end=2,
                                    ),
                                    LatexGroupNode(
                                        parsing_state=ps,
                                        nodelist=LatexNodeList([
                                            LatexCharsNode(
                                                parsing_state=ps,
                                                chars='zz',
                                                pos=3,
                                                pos_end=5,
                                            )
                                            ], pos=3, pos_end=5),
                                        delimiters=('{','}'),
                                        pos=2,
                                        pos_end=6,
                                    )
                                ],
                                pos=1,
                                pos_end=6,
                            ),
                            delimiters=('',';'),
                            pos=1,
                            pos_end=7,
                        ),
                        LatexGroupNode(
                            parsing_state=cps,
                            nodelist=LatexNodeList(
                                [
                                    LatexCommentNode(
                                        parsing_state=cps,
                                        comment=' ;comment;',
                                        comment_post_space='\n',
                                        pos=7,
                                        pos_end=19,
                                    )
                                ],
                                pos=7,
                                pos_end=19,
                            ),
                            delimiters=('',''),
                            pos=7,
                            pos_end=19,
                        ),
                    ],
                    pos=1,
                    pos_end=19,
                ),
                delimiters=('{','}'),
                pos=0,
                pos_end=20,
            )
        )


    def test_missing_brace(self):
        latextext = "{a;b{z}"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexCharsCommaSeparatedListParser(
            comma_char=';',
            enable_groups=True,
            enable_comments=True,
        )

        with self.assertRaises(LatexWalkerNodesParseError):
            _, _ = lw.parse_content(parser, token_reader=tr,
                                    parsing_state=ps)






if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
