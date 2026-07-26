import unittest
import logging
logger = logging.getLogger(__name__)


# Everything in this module exercises the pylatexenc 2 compatibility interface
# of the spec classes, which isn't part of the JavaScript build of the library.

### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE

from pylatexenc import latexwalker

from pylatexenc.latexnodes import ParsingStateDeltaEnterMathMode

from pylatexenc.macrospec import (
    MacroSpec,
    EnvironmentSpec,
    LatexContextDb,
    MacroStandardArgsParser,
    VerbatimArgsParser,
)


class _NoArgsLegacyArgsParser(MacroStandardArgsParser):
    r"""
    A pylatexenc 2 style argument parser that doesn't read any arguments at all.
    """
    def __init__(self):
        super(_NoArgsLegacyArgsParser, self).__init__('')


class _InnerParsingStateLegacyArgsParser(MacroStandardArgsParser):
    r"""
    A pylatexenc 2 style argument parser that reports, in the fourth item of the
    tuple it returns, the parsing state in which the environment body should be
    parsed.
    """
    def __init__(self):
        super(_InnerParsingStateLegacyArgsParser, self).__init__('')

    def parse_args(self, w, pos, parsing_state=None, **kwargs):
        argd, argspos, argslen = \
            super(_InnerParsingStateLegacyArgsParser, self).parse_args(
                w, pos, parsing_state=parsing_state, **kwargs
            )
        inner_parsing_state = parsing_state.sub_context(in_math_mode=True)
        return (argd, argspos, argslen,
                {'inner_parsing_state': inner_parsing_state},)


def _parse_with_specs(latex, macros=[], environments=[]):
    latex_context = LatexContextDb()
    latex_context.add_context_category('test', macros=macros, environments=environments)
    lw = latexwalker.LatexWalker(latex, latex_context=latex_context)
    nodes, parsing_state, _ = lw.get_latex_nodes()
    return nodes


def _environment_body_parsing_state(spec, latex):
    nodes = _parse_with_specs(latex, environments=[spec])
    return nodes[0].nodelist[0].parsing_state



class TestCallableSpecLegacyArgsParser(unittest.TestCase):

    def test_args_parser_as_string_provides_the_arguments(self):
        # MacroSpec('foo', args_parser='{[') must accept the very same arguments
        # as MacroSpec('foo', '{[')
        spec = MacroSpec('foo', args_parser='{[')

        self.assertEqual(spec.arguments_parser.argspec, '{[')

        nodes = _parse_with_specs(r'\foo{X}[Y] tail', macros=[spec])

        self.assertEqual(len(nodes), 2)
        self.assertEqual(len(nodes[0].nodeargd.argnlist), 2)
        self.assertEqual(nodes[1].chars, ' tail')


    def test_is_math_mode_with_legacy_args_parser(self):
        # is_math_mode= and args_parser= are both pylatexenc 2 style options, so
        # they can be used together
        spec = EnvironmentSpec('myeq',
                               args_parser=_NoArgsLegacyArgsParser(),
                               is_math_mode=True)
        parsing_state = _environment_body_parsing_state(
            spec, r'\begin{myeq} x \end{myeq}')
        self.assertTrue(parsing_state.in_math_mode)


    def test_legacy_args_parser_without_math_mode(self):
        spec = EnvironmentSpec('myenv', args_parser=_NoArgsLegacyArgsParser())
        parsing_state = _environment_body_parsing_state(
            spec, r'\begin{myenv} x \end{myenv}')
        self.assertFalse(parsing_state.in_math_mode)


    def test_legacy_args_parser_inner_parsing_state(self):
        # the parsing state that the legacy argument parser reports for the
        # environment body must be honored
        spec = EnvironmentSpec('myeq', args_parser=_InnerParsingStateLegacyArgsParser())
        parsing_state = _environment_body_parsing_state(
            spec, r'\begin{myeq} x \end{myeq}')
        self.assertTrue(parsing_state.in_math_mode)


    def test_cannot_combine_args_parser_and_body_parsing_state_delta(self):
        self.assertRaises(
            ValueError,
            EnvironmentSpec, 'myeq',
            args_parser=_NoArgsLegacyArgsParser(),
            body_parsing_state_delta=ParsingStateDeltaEnterMathMode(),
        )

    def test_cannot_combine_args_parser_and_make_after_parsing_state_delta(self):
        def my_make_after_parsing_state_delta(parsed_node, latex_walker):
            return None
        self.assertRaises(
            ValueError,
            MacroSpec, 'mymacro',
            args_parser=_NoArgsLegacyArgsParser(),
            make_after_parsing_state_delta=my_make_after_parsing_state_delta,
        )

    def test_cannot_combine_args_parser_string_and_finalize_node(self):
        def my_finalize_node(node):
            return node
        self.assertRaises(
            ValueError,
            MacroSpec, 'mymacro',
            args_parser='{',
            finalize_node=my_finalize_node,
        )

    def test_cannot_combine_args_parser_and_arguments_spec_list(self):
        self.assertRaises(
            ValueError,
            MacroSpec, 'mymacro', '{',
            args_parser=_NoArgsLegacyArgsParser(),
        )


    def test_parse_args_reports_positions(self):
        spec = MacroSpec('cmd', '{[')
        lw = latexwalker.LatexWalker(r'\cmd{ab}[cd] rest')
        parsing_state = lw.make_parsing_state()

        argd, apos, alen = spec.parse_args(lw, len(r'\cmd'),
                                           parsing_state=parsing_state)

        self.assertEqual(apos, len(r'\cmd'))
        self.assertEqual(alen, len(r'{ab}[cd]'))
        self.assertEqual(len(argd.argnlist), 2)



class TestVerbatimArgsParserLegacy(unittest.TestCase):

    def test_verb_macro_reads_its_argument(self):
        lw = latexwalker.LatexWalker(r'\verb+ab+')
        args_parser = VerbatimArgsParser(verbatim_arg_type='verb-macro')
        argd, apos, alen = args_parser.parse_args(
            lw, len(r'\verb'), parsing_state=lw.make_parsing_state())
        self.assertEqual(argd.verbatim_text, 'ab')

    def test_verb_macro_at_end_of_input(self):
        # reaching the end of the string while looking for the delimiter of the
        # verbatim argument must be reported as a parse error, and not raise an
        # IndexError
        lw = latexwalker.LatexWalker(r'\verb')
        args_parser = VerbatimArgsParser(verbatim_arg_type='verb-macro')
        self.assertRaises(
            latexwalker.LatexWalkerParseError,
            args_parser.parse_args, lw, len(r'\verb'),
        )

    def test_verb_macro_at_end_of_input_after_spaces(self):
        lw = latexwalker.LatexWalker('\\verb   ')
        args_parser = VerbatimArgsParser(verbatim_arg_type='verb-macro')
        self.assertRaises(
            latexwalker.LatexWalkerParseError,
            args_parser.parse_args, lw, len(r'\verb'),
        )

### END_PYLATEXENC2_LEGACY_SUPPORT_CODE



# ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
