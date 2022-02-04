import unittest
import sys
import logging


from pylatexenc.latexnodes.parsers._stdarg import (
    get_standard_argument_parser,
    LatexStandardArgumentParser,
)

from pylatexenc.latexnodes import (
    LatexWalkerTokenParseError,
    LatexTokenReader,
    LatexToken,
    LatexNodeList,
    LatexCommentNode,
    LatexCharsNode,
    LatexMacroNode,
    LatexGroupNode,
    ParsingState,
    ParsedMacroArgs,
)


from ._helpers_tests import (
    DummyWalker,
    dummy_empty_group_parser,
    dummy_empty_mathmode_parser,
    DummyLatexContextDb,
)


class TestLatexStandardArgumentParser(unittest.TestCase):

    def test_arg_m_0(self):
        latextext = r'''{mandatory argument} (more stuff)'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexStandardArgumentParser(arg_spec='m')

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

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
        lw = DummyWalker()

        parser = LatexStandardArgumentParser(arg_spec='{')

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

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
        lw = DummyWalker()

        parser = LatexStandardArgumentParser(arg_spec='m', include_skipped_comments=False)

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

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
        lw = DummyWalker()

        parser = LatexStandardArgumentParser(arg_spec='m') # i.e. include_skipped_comments=True

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

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

    def test_arg_m_argstatemathmode(self):
        latextext = r'''{mandatory argument} (more stuff)'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexStandardArgumentParser(arg_spec='m',
                                             is_math_mode=True)

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        mmps = nodes.nodelist[0].parsing_state
        self.assertTrue(mmps.in_math_mode)

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=mmps,
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=mmps,
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

    def test_arg_m_argstatetextmode(self):
        latextext = r'''{mandatory argument} (more stuff)'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexStandardArgumentParser(arg_spec='m',
                                             is_math_mode=False)

        nodes, carryover_info = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        nommps = nodes.nodelist[0].parsing_state
        self.assertFalse(nommps.in_math_mode)

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=nommps,
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=nommps,
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



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
