import unittest
import logging


from pylatexenc.latexnodes.parsers._stdarg import (
    #get_standard_argument_parser,
    LatexStandardArgumentParser,
    LatexCharsCommaSeparatedListParser,
    LatexTackOnInformationFieldMacrosParser,
    #LatexCharsGroupParser,
)
from pylatexenc.latexnodes import parsers

from pylatexenc.latexnodes import (
    LatexWalkerParseError,
    LatexWalkerNodesParseError,
    LatexTokenReader,
    ParsingState,
)
from pylatexenc.latexnodes.nodes import *

from ._helpers_tests import (
    DummyWalker,
    DummyLatexContextDb,
)

from pylatexenc.latexwalker import LatexWalker


class DummyWalkerWithGroupsAndMath(DummyWalker):
    make_latex_group_parser = parsers.LatexDelimitedGroupParser
    make_latex_math_parser = parsers.LatexMathParser



class TestLatexStandardArgumentParser(unittest.TestCase):

    maxDiff = None

    def test_arg_m_0(self):
        latextext = r'''{mandatory argument} (more stuff)'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexStandardArgumentParser(
            arg_spec='m',
            
        )

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

    def test_arg_openbrace_wspace(self):
        latextext = ' \t  ' + r'''{mandatory argument} (more stuff)'''

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
                            pos=4+1,
                            pos_end=4+19,
                        )
                    ],
                    pos=4+1,
                    pos_end=4+19,
                ),
                delimiters=('{','}'),
                pos=4+0,
                pos_end=4+20,
            )
        )


    def test_arg_m_precomment_noincludeskip(self):
        latextext = r'''%comment here
{mandatory argument} (more stuff)'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexStandardArgumentParser(
            arg_spec='m',
            return_full_node_list=False,
        )

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

        parser = LatexStandardArgumentParser(
            arg_spec='m',
            return_full_node_list=True,
        )

        nodes, parsing_state_delta = \
            lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList(
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
                parsing_state=ps,
            ),
        )


    def test_arg_star_0(self):
        latextext = r'''*{more} (more stuff)'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexStandardArgumentParser(
            arg_spec='*',
            
        )

        nodes, parsing_state_delta = \
            lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexCharsNode(
                parsing_state=ps,
                chars='*',
                pos=0,
                pos_end=1,
            ),
        )


    def test_arg_star_1(self):
        latextext = r'''  * {more} (more stuff)'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexStandardArgumentParser(
            arg_spec='*',
            
        )

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexCharsNode(
                parsing_state=ps,
                chars='*',
                pos=2,
                pos_end=3,
            ),
        )


    def test_arg_t_char_0(self):
        # the ‘t<char>’ argument type must report its argument in the same way
        # as the ‘s’/‘*’ argument type does
        latextext = r'''+{more} (more stuff)'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexStandardArgumentParser(
            arg_spec='t+',
        )

        nodes, parsing_state_delta = \
            lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexCharsNode(
                parsing_state=ps,
                chars='+',
                pos=0,
                pos_end=1,
            ),
        )


    def test_arg_t_char_fullnodelist(self):
        latextext = r'''+{more} (more stuff)'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexStandardArgumentParser(
            arg_spec='t+',
            return_full_node_list=True,
        )

        nodes, parsing_state_delta = \
            lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=ps,
                        chars='+',
                        pos=0,
                        pos_end=1,
                    ),
                ],
                parsing_state=ps,
            ),
        )


    def test_arg_embelishments_1(self):
        latextext = r'''^{test}_x{more stuff} stuff'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexStandardArgumentParser(
            arg_spec=r'e{_^`}'
        )

        nodes, parsing_state_delta = \
            lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        print("NODES:\n", nodes)

        self.assertEqual(
            nodes,
            LatexNodeList(
                parsing_state=ps,
                nodelist=[
                    LatexGroupNode(
                        parsing_state=ps,
                        delimiters=('^', ''),
                        nodelist=LatexNodeList(
                            parsing_state=ps,
                            nodelist=[
                                LatexGroupNode(
                                    parsing_state=ps,
                                    delimiters=('{', '}'),
                                    nodelist=LatexNodeList(
                                        parsing_state=ps,
                                        nodelist=[
                                            LatexCharsNode(
                                                parsing_state=ps,
                                                chars='test',
                                                pos=2,
                                                pos_end=6,
                                            ),
                                        ],
                                        pos=2,
                                        pos_end=6,
                                    ),
                                    pos=1,
                                    pos_end=7,
                                ),
                            ],
                            pos=1,
                            pos_end=7,
                        ),
                        pos=0,
                        pos_end=7,
                    ),
                    LatexGroupNode(
                        parsing_state=ps,
                        delimiters=('_', ''),
                        nodelist=LatexNodeList(
                            parsing_state=ps,
                            nodelist=[
                                LatexCharsNode(
                                    parsing_state=ps,
                                    chars='x',
                                    pos=8,
                                    pos_end=9,
                                ),
                            ],
                            pos=8,
                            pos_end=9,
                        ),
                        pos=7,
                        pos_end=9,
                    ),
                ],
                pos=0,
                pos_end=9
            )

        )

    def test_arg_embelishments_2(self):
        latextext = r'''more stuff'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexStandardArgumentParser(
            arg_spec=r'e{_^`}'
        )

        nodes, parsing_state_delta = \
            lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertIsNone(nodes)


    def test_arg_embelishments_chars(self):

        parser = LatexStandardArgumentParser(
            arg_spec=r'e{_^`}'
        )
        arg_parser = parser.get_arg_parser_instance(parser.arg_spec)

        # the closing brace of the ‘e{...}’ specification is not an
        # embellishment char
        self.assertEqual(arg_parser.embellishment_chars, '_^`')
        self.assertEqual(arg_parser.chars_list, ['_', '^', '`'])


    def test_arg_embelishments_chars_with_spaces(self):

        parser = LatexStandardArgumentParser(
            arg_spec=r'e{_ ^ `}'
        )
        arg_parser = parser.get_arg_parser_instance(parser.arg_spec)

        # spaces in the ‘e{...}’ specification don't introduce any empty
        # embellishment chars
        self.assertEqual(arg_parser.chars_list, ['_', '^', '`'])


    def test_arg_embelishments_no_repeated_char(self):
        latextext = r'''^{test}^x{more stuff} stuff'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexStandardArgumentParser(
            arg_spec=r'e{_^`}'
        )

        nodes, parsing_state_delta = \
            lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        # the second ‘^’ is not read as a further embellishment
        self.assertEqual(
            nodes,
            LatexNodeList(
                parsing_state=ps,
                nodelist=[
                    LatexGroupNode(
                        parsing_state=ps,
                        delimiters=('^', ''),
                        nodelist=LatexNodeList(
                            parsing_state=ps,
                            nodelist=[
                                LatexGroupNode(
                                    parsing_state=ps,
                                    delimiters=('{', '}'),
                                    nodelist=LatexNodeList(
                                        parsing_state=ps,
                                        nodelist=[
                                            LatexCharsNode(
                                                parsing_state=ps,
                                                chars='test',
                                                pos=2,
                                                pos_end=6,
                                            ),
                                        ],
                                        pos=2,
                                        pos_end=6,
                                    ),
                                    pos=1,
                                    pos_end=7,
                                ),
                            ],
                            pos=1,
                            pos_end=7,
                        ),
                        pos=0,
                        pos_end=7,
                    ),
                ],
                pos=0,
                pos_end=7
            )
        )
        self.assertEqual(tr.cur_pos(), 7)


    def test_arg_embelishments_end_of_input(self):
        latextext = r'''^x'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexStandardArgumentParser(
            arg_spec=r'e{_^`}'
        )

        nodes, parsing_state_delta = \
            lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        # the embellishment that was read is reported even though the input ends
        # while we are still looking for further embellishments
        self.assertEqual(
            nodes,
            LatexNodeList(
                parsing_state=ps,
                nodelist=[
                    LatexGroupNode(
                        parsing_state=ps,
                        delimiters=('^', ''),
                        nodelist=LatexNodeList(
                            parsing_state=ps,
                            nodelist=[
                                LatexCharsNode(
                                    parsing_state=ps,
                                    chars='x',
                                    pos=1,
                                    pos_end=2,
                                ),
                            ],
                            pos=1,
                            pos_end=2,
                        ),
                        pos=0,
                        pos_end=2,
                    ),
                ],
                pos=0,
                pos_end=2
            )
        )


    def test_arg_any_delimited_angleb(self):
        latextext = r'''<delimited>more stuff'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexStandardArgumentParser(
            arg_spec=r'AnyDelimited'
        )

        nodes, parsing_state_delta = \
            lw.parse_content(parser, token_reader=tr, parsing_state=ps)


        gps = nodes.parsing_state
        cps = nodes.nodelist[0].parsing_state

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=gps,
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=cps,
                            chars='delimited',
                            pos=1,
                            pos_end=10,
                        )
                    ],
                    pos=1,
                    pos_end=10,
                ),
                delimiters=('<','>'),
                pos=0,
                pos_end=11,
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


    def test_missing_brace_tolerant(self):
        # in tolerant parsing mode, the truncated last element is reported up to
        # the end of the input
        latextext = "{a;b;c"

        lw = LatexWalker(s=latextext, tolerant_parsing=True)
        tr = lw.make_token_reader()
        ps = lw.make_parsing_state()

        parser = LatexCharsCommaSeparatedListParser(
            comma_char=';',
            enable_groups=True,
            enable_comments=True,
        )

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr,
                                                      parsing_state=ps)

        self.assertEqual(len(nodes.nodelist), 3)
        self.assertEqual(nodes.nodelist[0].nodelist[0].chars, 'a')
        self.assertEqual(nodes.nodelist[1].nodelist[0].chars, 'b')
        self.assertEqual(nodes.nodelist[2].nodelist[0].chars, 'c')
        self.assertEqual(nodes.nodelist[2].pos, 5)
        self.assertEqual(nodes.nodelist[2].pos_end, 6)


    def test_empty_parts_skipped_by_default(self):
        latextext = "{a;;b;}"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexCharsCommaSeparatedListParser(
            comma_char=';',
            enable_groups=True,
            enable_comments=True,
        )

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr,
                                                      parsing_state=ps)

        self.assertEqual(len(nodes.nodelist), 2)
        self.assertEqual(nodes.nodelist[0].nodelist[0].chars, 'a')
        self.assertEqual(nodes.nodelist[1].nodelist[0].chars, 'b')


    def test_keep_empty_parts(self):
        latextext = "{a;;b;}"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexCharsCommaSeparatedListParser(
            comma_char=';',
            enable_groups=True,
            enable_comments=True,
            keep_empty_parts=True,
        )

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr,
                                                      parsing_state=ps)

        self.assertEqual(len(nodes.nodelist), 4)
        self.assertEqual(nodes.nodelist[0].nodelist[0].chars, 'a')
        self.assertEqual(len(nodes.nodelist[1].nodelist), 0)
        self.assertEqual(nodes.nodelist[2].nodelist[0].chars, 'b')
        self.assertEqual(len(nodes.nodelist[3].nodelist), 0)




class TestLatexTackOnInformationFieldMacrosParser(unittest.TestCase):

    maxDiff = None

    def test_multiple_not_allowed(self):
        latextext = r'''\foo{a}\foo{b}'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexTackOnInformationFieldMacrosParser(
            macronames=['foo'],
            allow_multiple=False,
        )

        exc = None
        try:
            lw.parse_content(parser, token_reader=tr, parsing_state=ps)
        except LatexWalkerParseError as e:
            exc = e

        self.assertTrue(exc is not None)
        self.assertEqual(
            exc.error_type_info['what'],
            'nodes_stdarg_illegal_multiple_information_field_macro'
        )
        self.assertEqual(exc.error_type_info['macroname'], 'foo')


    def test_multiple_allowed(self):
        latextext = r'''\foo{a}\foo{b}'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexTackOnInformationFieldMacrosParser(
            macronames=['foo'],
            allow_multiple=True,
        )

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr,
                                                      parsing_state=ps)

        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].delimiters[0], '\\foo')
        self.assertEqual(nodes[1].delimiters[0], '\\foo')


    def test_different_macros_are_not_multiple(self):
        latextext = r'''\foo{a}\bar{b}'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalkerWithGroupsAndMath()

        parser = LatexTackOnInformationFieldMacrosParser(
            macronames=['foo', 'bar'],
            allow_multiple=False,
        )

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr,
                                                      parsing_state=ps)

        self.assertEqual(len(nodes), 2)
        self.assertEqual(nodes[0].delimiters[0], '\\foo')
        self.assertEqual(nodes[1].delimiters[0], '\\bar')






if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
