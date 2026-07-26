import unittest
import logging


from pylatexenc.latexnodes.parsers._expression import (
    LatexExpressionParser,
)

from pylatexenc.latexnodes import (
    LatexWalkerParseError,
    LatexWalkerNodesParseError,
    LatexTokenReader,
    LatexToken,
    ParsingState,
    CallableSpecBase,
    LatexArgumentSpec,
    ParsedArguments,
)
from pylatexenc.latexnodes.nodes import *

from ._helpers_tests import (
    DummyWalker,
    DummyLatexContextDb,
)


class TolerantDummyWalker(DummyWalker):
    r"""
    A dummy walker that behaves as if tolerant parsing mode were enabled, i.e.,
    it always requests that recovery from parse errors be attempted.
    """
    def check_tolerant_parsing_ignore_error(self, exc):
        return None



# --------------------------------------

class TestLatexExpression(unittest.TestCase):
    
    maxDiff = None

    def test_simple_first_char(self):
        latextext = r'''characters'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser()

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
                    )
                ],
                parsing_state=ps
            )
        )

    def test_unexpected_math_mode_delimiter(self):
        # a math mode delimiter where an expression is expected is an error; the
        # error object must carry the recovery nodes for tolerant parsing mode.
        # As for an unexpected closing brace, the delimiter itself is not
        # consumed so that whichever parser is waiting for it can still see it.
        latextext = r'''$'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser()

        exc = None
        try:
            lw.parse_content(parser, token_reader=tr, parsing_state=ps)
        except LatexWalkerNodesParseError as e:
            exc = e

        self.assertTrue(exc is not None)
        self.assertTrue('math mode delimiter' in exc.msg)
        self.assertEqual(
            exc.recovery_nodes,
            LatexCharsNode(
                parsing_state=ps,
                chars='',
                pos=0,
                pos_end=0,
            )
        )
        # the math mode delimiter is not consumed
        self.assertEqual(tr.cur_pos(), 0)
        self.assertTrue(exc.recovery_past_token is None)
        self.assertEqual(exc.recovery_at_token.tok, 'mathmode_inline')
        self.assertEqual(exc.recovery_at_token.pos, 0)

    def test_simple_first_char_nofulllist(self):
        latextext = r'''characters'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser(return_full_node_list=False)

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexCharsNode(
                parsing_state=ps,
                chars='c',
                pos=0,
                pos_end=1,
            )
        )
    

    def test_simple_first_char_wspace(self):
        latextext = ' \n \t characters'

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser()

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=ps,
                        chars=' \n \t ',
                        pos=0,
                        pos_end=5,
                    ),
                    LatexCharsNode(
                        parsing_state=ps,
                        chars='c',
                        pos=5,
                        pos_end=6,
                    ),
                ],
            )
        )

    def test_simple_first_char_wspace_nofulllist(self):
        latextext = ' \n \t characters'

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser(return_full_node_list=False)

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexCharsNode(
                parsing_state=ps,
                chars='c',
                pos=5,
                pos_end=6,
            ),
        )


    def test_disallowed_pre_space_does_not_eat_the_token(self):
        # in tolerant parsing mode, only the whitespace is discarded; the token
        # that follows it must still be picked up as the expression.
        latextext = '  characters'

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = TolerantDummyWalker()

        parser = LatexExpressionParser(allow_pre_space=False)

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=ps,
                        chars='c',
                        pos=2,
                        pos_end=3,
                    ),
                ],
            )
        )
        self.assertEqual(tr.cur_pos(), 3)

    def test_disallowed_pre_space_is_an_error_also_for_a_macro(self):
        # the check for leading whitespace must apply to all token types, not
        # only to those that are inspected after the macro & specials cases
        latextext = r'''  \somemacro'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser(allow_pre_space=False)

        exc = None
        try:
            lw.parse_content(parser, token_reader=tr, parsing_state=ps)
        except LatexWalkerParseError as e:
            exc = e

        self.assertTrue(exc is not None)
        self.assertTrue('whitespace' in exc.msg)

    def test_disallowed_pre_space_before_macro_recovers_with_the_macro(self):
        latextext = r'''  \somemacro'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = TolerantDummyWalker()

        parser = LatexExpressionParser(allow_pre_space=False,
                                       return_full_node_list=False,
                                       single_token_requiring_arg_is_error=False)

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertTrue(nodes.isNodeType(LatexMacroNode))
        self.assertEqual(nodes.macroname, 'somemacro')
        self.assertEqual(nodes.pos, 2)

    def test_end_environment_is_not_an_expression(self):
        # ‘\end{someenv}’ must not be picked up as the expression, otherwise the
        # environment never gets closed and its name leaks into the contents.
        latextext = r'''\end{someenv} more text'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser()

        exc = None
        try:
            lw.parse_content(parser, token_reader=tr, parsing_state=ps)
        except LatexWalkerNodesParseError as e:
            exc = e

        self.assertTrue(exc is not None)
        self.assertEqual(
            exc.recovery_nodes,
            LatexCharsNode(
                parsing_state=ps,
                chars='',
                pos=0,
                pos_end=0,
            )
        )
        # the ‘\end’ is not consumed
        self.assertEqual(tr.cur_pos(), 0)
        self.assertEqual(exc.recovery_at_token.tok, 'macro')
        self.assertEqual(exc.recovery_at_token.arg, 'end')
        self.assertEqual(exc.error_type_info['unexpected'], 'beginend')

    def test_simple_first_char_wspaceandcomment(self):
        latextext = ' \n \t % comment\n  characters'

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser()

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=ps,
                        chars=' \n \t ',
                        pos=0,
                        pos_end=5,
                    ),
                    LatexCommentNode(
                        parsing_state=ps,
                        comment=' comment',
                        comment_post_space='\n  ',
                        pos=5,
                        pos_end=17,
                    ),
                    LatexCharsNode(
                        parsing_state=ps,
                        chars='c',
                        pos=17,
                        pos_end=18,
                    ),
                ],
            )
        )


    def test_simple_first_char_wspaceandcomment_nofulllist(self):
        latextext = ' \n \t % comment\n  characters'

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser(return_full_node_list=False)

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexCharsNode(
                parsing_state=ps,
                chars='c',
                pos=17,
                pos_end=18,
            ),
        )


    def test_simple_group_char_wspace(self):
        latextext = ' \n \t {char}acters'

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser()

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexNodeList(
                [
                    LatexCharsNode(
                        parsing_state=ps,
                        chars=' \n \t ',
                        pos=0,
                        pos_end=5,
                    ),
                    LatexGroupNode(
                        parsing_state=ps,
                        nodelist=LatexNodeList(
                            [
                                LatexCharsNode(
                                    parsing_state=ps,
                                    chars='char',
                                    pos=6,
                                    pos_end=10,
                                ),
                            ],
                            parsing_state=ps,
                        ),
                        delimiters=('{','}'),
                        pos=5,
                        pos_end=11,
                    ),
                ],
            )
        )

    def test_simple_group_char_wspace_nofulllist(self):
        latextext = ' \n \t {char}acters'

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser(return_full_node_list=False)

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

        self.assertEqual(
            nodes,
            LatexGroupNode(
                parsing_state=ps,
                nodelist=LatexNodeList(
                    [
                        LatexCharsNode(
                            parsing_state=ps,
                            chars='char',
                            pos=6,
                            pos_end=10,
                        ),
                    ],
                    parsing_state=ps,
                ),
                delimiters=('{','}'),
                pos=5,
                pos_end=11,
            ),
        )
    
    def test_simple_group_wcomment(self):
        latextext = r'''
%comment here
{mandatory argument} (more stuff)'''.lstrip()

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser()

        nodes, parsing_state_delta = lw.parse_content(parser, token_reader=tr, parsing_state=ps)

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
                                ),
                            ],
                            parsing_state=ps,
                        ),
                        pos=14,
                        pos_end=14+20,
                    ),
                ],
            )
        )

    def test_simple_group_wcomment_nofulllist(self):
        latextext = r'''
%comment here
{mandatory argument} (more stuff)'''.lstrip()

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDb())
        lw = DummyWalker()

        parser = LatexExpressionParser(return_full_node_list=False)

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
                        ),
                    ],
                    parsing_state=ps,
                ),
                pos=14,
                pos_end=14+20,
            ),
        )





# ---


#


# --------------------------------------

#
# Dummy specs whose node parser actually reads an argument.  The dummy specs in
# `_helpers_tests` never consume any arguments, so they cannot exercise the
# `parse_callable_arguments=` option.  These are kept local to this test module
# so that adding them cannot disturb any other test's context database.
#

class _DummyMacroWithArgParser(object):
    def __init__(self, tok, spec):
        self.tok = tok
        self.spec = spec

    def contents_can_be_empty(self):
        return False

    def parse(self, latex_walker, token_reader, parsing_state):
        argnode, _ = latex_walker.parse_content(
            LatexExpressionParser(return_full_node_list=False),
            token_reader=token_reader,
            parsing_state=parsing_state,
        )
        n = latex_walker.make_node(
            LatexMacroNode,
            parsing_state=parsing_state,
            macroname=self.tok.arg,
            spec=self.spec,
            nodeargd=ParsedArguments(argnlist=[argnode],
                                     arguments_spec_list=[LatexArgumentSpec('{')]),
            macro_post_space=self.tok.post_space,
            pos=self.tok.pos,
            pos_end=argnode.pos_end,
        )
        return n, None

class DummyMacroWithArgSpec(CallableSpecBase):
    def __init__(self, macroname):
        super(DummyMacroWithArgSpec, self).__init__()
        self.macroname = macroname

    def get_node_parser(self, token, parsing_state):
        return _DummyMacroWithArgParser(token, self)


class _DummySpecialsWithArgParser(object):
    def __init__(self, tok, spec):
        self.tok = tok
        self.spec = spec

    def contents_can_be_empty(self):
        return False

    def parse(self, latex_walker, token_reader, parsing_state):
        argnode, _ = latex_walker.parse_content(
            LatexExpressionParser(return_full_node_list=False),
            token_reader=token_reader,
            parsing_state=parsing_state,
        )
        n = latex_walker.make_node(
            LatexSpecialsNode,
            parsing_state=parsing_state,
            specials_chars=self.tok.arg.specials_chars,
            spec=self.spec,
            nodeargd=ParsedArguments(argnlist=[argnode],
                                     arguments_spec_list=[LatexArgumentSpec('{')]),
            pos=self.tok.pos,
            pos_end=argnode.pos_end,
        )
        return n, None

class DummySpecialsWithArgSpec(CallableSpecBase):
    def __init__(self, specials_chars):
        super(DummySpecialsWithArgSpec, self).__init__()
        self.specials_chars = specials_chars

    def get_node_parser(self, token, parsing_state):
        return _DummySpecialsWithArgParser(token, self)


class DummyLatexContextDbWithArgSpecs(DummyLatexContextDb):
    def __init__(self):
        super(DummyLatexContextDbWithArgSpecs, self).__init__()
        self.specs['macros']['macrowitharg'] = DummyMacroWithArgSpec('macrowitharg')
        self.specs['specials']['^'] = DummySpecialsWithArgSpec('^')
        self.specials_by_len = sorted(
            self.specs['specials'].keys(),
            key=lambda x: len(x),
            reverse=True
        )



class TestLatexExpressionParseCallableArguments(unittest.TestCase):

    maxDiff = None

    def test_macro_without_its_arguments_by_default(self):
        # by default, the macro that forms the expression is picked up on its
        # own and its argument is left for whoever parses the following content
        latextext = r'''\macrowitharg{value}acters'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDbWithArgSpecs())
        lw = DummyWalker()

        parser = LatexExpressionParser(return_full_node_list=False,
                                       single_token_requiring_arg_is_error=False)

        node, parsing_state_delta = lw.parse_content(parser, token_reader=tr,
                                                     parsing_state=ps)

        self.assertEqual(
            node,
            LatexMacroNode(
                parsing_state=ps,
                macroname='macrowitharg',
                spec=ps.latex_context.get_macro_spec('macrowitharg'),
                nodeargd=ParsedArguments(),
                macro_post_space='',
                pos=0,
                pos_end=len(r'\macrowitharg'),
            )
        )
        self.assertEqual(tr.cur_pos(), len(r'\macrowitharg'))

    def test_macro_with_its_arguments(self):
        latextext = r'''\macrowitharg{value}acters'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDbWithArgSpecs())
        lw = DummyWalker()

        parser = LatexExpressionParser(parse_callable_arguments=True,
                                       return_full_node_list=False)

        node, parsing_state_delta = lw.parse_content(parser, token_reader=tr,
                                                     parsing_state=ps)

        p = len(r'\macrowitharg')
        self.assertEqual(
            node,
            LatexMacroNode(
                parsing_state=ps,
                macroname='macrowitharg',
                spec=ps.latex_context.get_macro_spec('macrowitharg'),
                nodeargd=ParsedArguments(
                    arguments_spec_list=[LatexArgumentSpec('{')],
                    argnlist=[
                        LatexGroupNode(
                            parsing_state=ps,
                            nodelist=LatexNodeList(
                                [
                                    LatexCharsNode(
                                        parsing_state=ps,
                                        chars='value',
                                        pos=p+1,
                                        pos_end=p+6,
                                    ),
                                ],
                                parsing_state=ps,
                            ),
                            delimiters=('{','}'),
                            pos=p,
                            pos_end=p+7,
                        ),
                    ],
                ),
                macro_post_space='',
                pos=0,
                pos_end=p+7,
            )
        )
        # the token reader is left immediately after the macro's argument
        self.assertEqual(tr.cur_pos(), p+7)

    def test_specials_with_its_arguments(self):
        # the same applies to a "latex specials" that accepts arguments; this is
        # what '^' and '_' need in math mode
        latextext = r'''^{value}acters'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDbWithArgSpecs())
        lw = DummyWalker()

        parser = LatexExpressionParser(parse_callable_arguments=True,
                                       return_full_node_list=False)

        node, parsing_state_delta = lw.parse_content(parser, token_reader=tr,
                                                     parsing_state=ps)

        self.assertEqual(
            node,
            LatexSpecialsNode(
                parsing_state=ps,
                specials_chars='^',
                spec=ps.latex_context.get_specials_spec('^'),
                nodeargd=ParsedArguments(
                    arguments_spec_list=[LatexArgumentSpec('{')],
                    argnlist=[
                        LatexGroupNode(
                            parsing_state=ps,
                            nodelist=LatexNodeList(
                                [
                                    LatexCharsNode(
                                        parsing_state=ps,
                                        chars='value',
                                        pos=2,
                                        pos_end=7,
                                    ),
                                ],
                                parsing_state=ps,
                            ),
                            delimiters=('{','}'),
                            pos=1,
                            pos_end=8,
                        ),
                    ],
                ),
                pos=0,
                pos_end=8,
            )
        )
        self.assertEqual(tr.cur_pos(), 8)

    def test_macro_with_single_token_argument(self):
        # only a single token is picked up as the macro's own argument, so that
        # "\macrowitharg 12" reads the "1" and leaves the "2"
        latextext = r'''\macrowitharg 12'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, latex_context=DummyLatexContextDbWithArgSpecs())
        lw = DummyWalker()

        parser = LatexExpressionParser(parse_callable_arguments=True,
                                       return_full_node_list=False)

        node, parsing_state_delta = lw.parse_content(parser, token_reader=tr,
                                                     parsing_state=ps)

        self.assertEqual(node.nodeargd.argnlist[0].chars, '1')
        self.assertEqual(tr.cur_pos(), len(r'\macrowitharg 1'))



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
