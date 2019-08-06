import unittest
import sys
import logging

if sys.version_info.major > 2:
    def unicode(string): return string
    basestring = str

from pylatexenc.macrospec import (
    ParsedMacroArgs, MacroStandardArgsParser,
    MacroSpec, EnvironmentSpec, #SpecialsSpec,
    std_macro, std_environment, LatexContextDb
)

from pylatexenc import latexwalker
from pylatexenc.latexwalker import (
    LatexCharsNode, LatexGroupNode,
    #LatexCommentNode, LatexMacroNode, LatexEnvironmentNode, LatexMathNode
)


class MyAsserts(object):
    def assertPMAEqual(self, a, b):

        logger = logging.getLogger(__name__)

        if len(a.argnlist) != len(b.argnlist):
            logger.warning("assertParsedArgsEqual fails:\na = [\n%s\n]\nb = [\n%s\n]\n",
                           "\n".join('    '+str(x) for x in a.argnlist),
                           "\n".join('    '+str(x) for x in b.argnlist),)
            raise AssertionError("ParsedMacroArgs are different, lengths differ")

        self.assertEqual(a.argspec, b.argspec)

        for j in range(len(a.argnlist)):
            try:
                self.assertEqual(a.argnlist[j], b.argnlist[j])
            except AssertionError:
                logger.warning("Mismatch for item %d of parsed arguments:\n"
                               "a = [\n%s\n]\nb = [\n%s\n]\n",
                               j,
                               "\n".join('    '+str(x) for x in a.argnlist),
                               "\n".join('    '+str(x) for x in b.argnlist),)
                raise


class TestMacroStandardArgsParser(unittest.TestCase, MyAsserts):

    def __init__(self, *args, **kwargs):
        super(TestMacroStandardArgsParser, self).__init__(*args, **kwargs)
        self.maxDiff = None
        
    def test_marg_0(self):
        lw = latexwalker.LatexWalker(r'{ab}')
        s = MacroStandardArgsParser('{')
        parsing_state = lw.make_parsing_state()
        (argd, p, l) = s.parse_args(lw, 0, parsing_state=parsing_state)
        self.assertPMAEqual(
            argd,
            ParsedMacroArgs(
                argspec='{',
                argnlist=[ LatexGroupNode(
                    parsing_state=parsing_state,
                    delimiters=('{','}'),
                    nodelist=[
                        LatexCharsNode(parsing_state=parsing_state,
                                       chars='ab',
                                       pos=1,len=2)
                    ],
                    pos=0,len=4)
                ])
        )

    def test_marg_1(self):
        lw = latexwalker.LatexWalker(r'\cmd ab')
        s = MacroStandardArgsParser('{')
        parsing_state = lw.make_parsing_state()
        (argd, p, l) = s.parse_args(lw, len(r'\cmd'), parsing_state=parsing_state)
        self.assertPMAEqual(
            argd,
            ParsedMacroArgs(argspec='{', argnlist=[
                LatexCharsNode(parsing_state=parsing_state,
                               chars='a',
                               pos=len(r'\cmd')+1,len=1)
            ])
        )

    def test_oarg_0(self):
        lw = latexwalker.LatexWalker(r'\cmd[ab] xyz')
        s = MacroStandardArgsParser('[')
        parsing_state = lw.make_parsing_state()
        (argd, p, l) = s.parse_args(lw, len(r'\cmd'), parsing_state=parsing_state)
        self.assertPMAEqual(
            argd,
            ParsedMacroArgs(argspec='[', argnlist=[
                LatexGroupNode(
                    parsing_state=parsing_state,
                    delimiters=('[', ']'),
                    nodelist=[
                        LatexCharsNode(parsing_state=parsing_state,
                                       chars='ab',
                                       pos=5,len=2)
                    ],
                    pos=4,len=4)
            ])
        )

    def test_oarg_1(self):
        lw = latexwalker.LatexWalker(r'\cmd xyz')
        s = MacroStandardArgsParser('[')
        (argd, p, l) = s.parse_args(lw, len(r'\cmd'))
        self.assertPMAEqual(
            argd,
            ParsedMacroArgs(argspec='[', argnlist=[ None ])
        )

    def test_star_0(self):
        lw = latexwalker.LatexWalker(r'\cmd xyz')
        s = MacroStandardArgsParser('*')
        (argd, p, l) = s.parse_args(lw, len(r'\cmd'))
        self.assertPMAEqual(
            argd,
            ParsedMacroArgs(argspec='*', argnlist=[ None ])
        )

    def test_star_1(self):
        lw = latexwalker.LatexWalker(r'\cmd* xyz')
        s = MacroStandardArgsParser('*')
        parsing_state = lw.make_parsing_state()
        (argd, p, l) = s.parse_args(lw, len(r'\cmd'), parsing_state=parsing_state)
        self.assertPMAEqual(
            argd,
            ParsedMacroArgs(argspec='*', argnlist=[
                LatexCharsNode(parsing_state=parsing_state,
                               chars='*',
                               pos=4,len=1)
            ])
        )

    def test_star_2(self):
        lw = latexwalker.LatexWalker(r'\cmd * xyz')
        s = MacroStandardArgsParser('*')
        parsing_state = lw.make_parsing_state()
        (argd, p, l) = s.parse_args(lw, len(r'\cmd'), parsing_state=parsing_state)
        self.assertPMAEqual(
            argd,
            ParsedMacroArgs(argspec='*', argnlist=[
                LatexCharsNode(parsing_state=parsing_state,
                               chars='*',
                               pos=5,len=1)
            ])
        )

    def test_combined_0(self):
        lw = latexwalker.LatexWalker(r'\cmd{ab}c*')
        s = MacroStandardArgsParser('{*[{*')
        parsing_state = lw.make_parsing_state()
        (argd, p, l) = s.parse_args(lw, len(r'\cmd'), parsing_state=parsing_state)
        self.assertPMAEqual(
            argd,
            ParsedMacroArgs(argspec='{*[{*', argnlist=[
                LatexGroupNode(parsing_state=parsing_state,
                               delimiters=('{', '}'),
                               nodelist=[
                                   LatexCharsNode(parsing_state=parsing_state,
                                                  chars='ab',
                                                  pos=5,len=2)
                               ],
                               pos=4,len=4),
                None, 
                None,
                LatexCharsNode(parsing_state=parsing_state,
                               chars='c',
                               pos=8,len=1),
                LatexCharsNode(parsing_state=parsing_state,
                               chars='*',
                               pos=9,len=1)
            ])
        )

    def test_combined_1(self):
        lw = latexwalker.LatexWalker(r'\cmd x[ab]c*')
        s = MacroStandardArgsParser('{*[{*')
        parsing_state = lw.make_parsing_state()
        (argd, p, l) = s.parse_args(lw, len(r'\cmd'), parsing_state=parsing_state)
        self.assertPMAEqual(
            argd,
            ParsedMacroArgs(argspec='{*[{*', argnlist=[
                LatexCharsNode(parsing_state=parsing_state,
                               chars='x',
                               pos=5,len=1),
                None,
                LatexGroupNode(parsing_state=parsing_state,
                               delimiters=('[', ']'),
                               nodelist=[
                                   LatexCharsNode(parsing_state=parsing_state,
                                                  chars='ab',
                                                  pos=7,len=2)
                               ],
                               pos=6,len=4),
                LatexCharsNode(parsing_state=parsing_state,
                               chars='c',
                               pos=10,len=1),
                LatexCharsNode(parsing_state=parsing_state,
                               chars='*',
                               pos=11,len=1)
            ])
        )



class Test_std_macro(unittest.TestCase):

    def test_idiom_0(self):
        spec = std_macro('cmd', '*[{')
        self.assertEqual(spec.macroname, 'cmd')
        self.assertEqual(spec.args_parser.argspec, '*[{')

    def test_idiom_1(self):
        spec = std_macro('cmd', True, 3)
        self.assertEqual(spec.macroname, 'cmd')
        self.assertEqual(spec.args_parser.argspec, '[{{{')

    def test_idiom_1b(self):
        spec = std_macro('cmd', False, 3)
        self.assertEqual(spec.macroname, 'cmd')
        self.assertEqual(spec.args_parser.argspec, '{{{')

    def test_idiom_1c(self):
        spec = std_macro('cmd', None, '{{{')
        self.assertEqual(spec.macroname, 'cmd')
        self.assertEqual(spec.args_parser.argspec, '{{{')

    def test_idiom_2(self):
        spec = std_macro( ('cmd', '*[{['), )
        self.assertEqual(spec.macroname, 'cmd')
        self.assertEqual(spec.args_parser.argspec, '*[{[')

    def test_idiom_2b(self):
        spec = std_macro( ('cmd', True, 3), )
        self.assertEqual(spec.macroname, 'cmd')
        self.assertEqual(spec.args_parser.argspec, '[{{{')

    def test_idiom_3(self):
        # spec is already a `MacroSpec` -- no-op
        spec = std_macro( std_macro('cmd', True, 3) )
        self.assertEqual(spec.macroname, 'cmd')
        self.assertEqual(spec.args_parser.argspec, '[{{{')



class Test_std_environment(unittest.TestCase):

    def test_idiom_0(self):
        spec = std_environment('environ', '[*{{', is_math_mode=True)
        self.assertEqual(spec.environmentname, 'environ')
        self.assertEqual(spec.args_parser.argspec, '[*{{')
        self.assertEqual(spec.is_math_mode, True)

    def test_idiom_0b(self):
        spec = std_environment('environ', None, is_math_mode=False)
        self.assertEqual(spec.environmentname, 'environ')
        self.assertEqual(spec.args_parser.argspec, '')
        self.assertEqual(spec.is_math_mode, False)

    def test_idiom_0c(self):
        spec = std_environment('environ', '[{')
        self.assertEqual(spec.environmentname, 'environ')
        self.assertEqual(spec.args_parser.argspec, '[{')
        self.assertEqual(spec.is_math_mode, False)

    def test_idiom_1(self):
        spec = std_environment('environ', True, 3, is_math_mode=True)
        self.assertEqual(spec.environmentname, 'environ')
        self.assertEqual(spec.args_parser.argspec, '[{{{')
        self.assertEqual(spec.is_math_mode, True)

    def test_idiom_2(self):
        spec = std_environment( ('environ', '[*{{'), is_math_mode=True)
        self.assertEqual(spec.environmentname, 'environ')
        self.assertEqual(spec.args_parser.argspec, '[*{{')
        self.assertEqual(spec.is_math_mode, True)

    def test_idiom_3(self):
        spec = std_environment( ('environ', False, 4), )
        self.assertEqual(spec.environmentname, 'environ')
        self.assertEqual(spec.args_parser.argspec, '{{{{')
        self.assertEqual(spec.is_math_mode, False)

    def test_idiom_3b(self):
        spec = std_environment( ('environ', None, '{{{{'), )
        self.assertEqual(spec.environmentname, 'environ')
        self.assertEqual(spec.args_parser.argspec, '{{{{')
        self.assertEqual(spec.is_math_mode, False)

    def test_idiom_4(self):
        spec = std_environment(  std_environment('environ', '{*{{{', is_math_mode=True) )
        self.assertEqual(spec.environmentname, 'environ')
        self.assertEqual(spec.args_parser.argspec, '{*{{{')
        self.assertEqual(spec.is_math_mode, True)



class TestLatexContextDb(unittest.TestCase):

    def test_can_get_macro_spec(self):
        db = LatexContextDb()
        db.set_unknown_macro_spec(MacroSpec('<unknown>'))
        db.add_context_category('cat1', [ std_macro('aaa', '{'), std_macro('bbb', '[{[') ], [])
        db.add_context_category('cat2', [ std_macro('aaa', '[{'), std_macro('ccc', None) ], [])
        db.add_context_category('cat3', [ std_macro('ccc', '*{'), std_macro('ddd', '{{[') ], [],
                                prepend=True)

        self.assertEqual(list(db.categories()), ['cat3', 'cat1', 'cat2'])
        
        self.assertEqual(db.get_macro_spec('aaa').macroname, 'aaa')
        self.assertEqual(db.get_macro_spec('aaa').args_parser.argspec, '{')

        self.assertEqual(db.get_macro_spec('bbb').macroname, 'bbb')
        self.assertEqual(db.get_macro_spec('bbb').args_parser.argspec, '[{[')

        self.assertEqual(db.get_macro_spec('ccc').macroname, 'ccc')
        self.assertEqual(db.get_macro_spec('ccc').args_parser.argspec, '*{')

        self.assertEqual(db.get_macro_spec('ddd').macroname, 'ddd')
        self.assertEqual(db.get_macro_spec('ddd').args_parser.argspec, '{{[')

        # default for unknown
        self.assertEqual(db.get_macro_spec('nonexistent').macroname, '<unknown>')
        self.assertEqual(db.get_macro_spec('nonexistent').args_parser.argspec, '')
        
    def test_can_get_environment_spec(self):

        db = LatexContextDb()
        db.set_unknown_environment_spec(EnvironmentSpec('<unknown>'))
        db.add_context_category('cat1', [],
                                [ std_environment('eaaa', '{'), std_environment('ebbb', '[{[') ])
        db.add_context_category('cat2', [],
                                [ std_environment('eaaa', '[{'), std_environment('eccc', None) ])
        db.add_context_category('cat3', [],
                                [ std_environment('eccc', '*{'), std_environment('eddd', '{{[') ],
                                prepend=True)
        
        self.assertEqual(list(db.categories()), ['cat3', 'cat1', 'cat2'])

        self.assertEqual(db.get_environment_spec('eaaa').environmentname, 'eaaa')
        self.assertEqual(db.get_environment_spec('eaaa').args_parser.argspec, '{')

        self.assertEqual(db.get_environment_spec('ebbb').environmentname, 'ebbb')
        self.assertEqual(db.get_environment_spec('ebbb').args_parser.argspec, '[{[')

        self.assertEqual(db.get_environment_spec('eccc').environmentname, 'eccc')
        self.assertEqual(db.get_environment_spec('eccc').args_parser.argspec, '*{')

        self.assertEqual(db.get_environment_spec('eddd').environmentname, 'eddd')
        self.assertEqual(db.get_environment_spec('eddd').args_parser.argspec, '{{[')

        # default for unknown
        self.assertEqual(db.get_environment_spec('nonexistent').environmentname, '<unknown>')
        self.assertEqual(db.get_environment_spec('nonexistent').args_parser.argspec, '')


    def test_filter_context_0(self):
        
        db = LatexContextDb()
        db.set_unknown_macro_spec(MacroSpec('<macro unknown>'))
        db.set_unknown_environment_spec(EnvironmentSpec('<env unknown>'))
        db.add_context_category('cat1',
                                [ std_macro('aaa', '{'), std_macro('bbb', '[{[') ],
                                [ std_environment('eaaa', '{'), std_environment('ebbb', '[{[') ])
        db.add_context_category('cat2',
                                [ std_macro('aaa', '[{'), std_macro('ccc', None) ],
                                [ std_environment('eaaa', '[{'), std_environment('eccc', None) ])
        db.add_context_category('cat3',
                                [ std_macro('ccc', '*{'), std_macro('ddd', '{{[') ],
                                [ std_environment('eccc', '*{'), std_environment('eddd', '{{[') ],
                                prepend=True)
        
        db2 = db.filter_context(keep_categories=['cat1', 'cat2'])
        # this should give 'ccc' from cat2, not cat3
        self.assertEqual(db2.get_macro_spec('ccc').macroname, 'ccc')
        self.assertEqual(db2.get_macro_spec('ccc').args_parser.argspec, '')
        # this should no longer exist
        self.assertEqual(db2.get_macro_spec('ddd').macroname, '<macro unknown>')
        self.assertEqual(db2.get_macro_spec('ddd').args_parser.argspec, '')

        # this should give 'eccc' from cat2, not cat3
        self.assertEqual(db2.get_environment_spec('eccc').environmentname, 'eccc')
        self.assertEqual(db2.get_environment_spec('eccc').args_parser.argspec, '')
        # this should no longer exist
        self.assertEqual(db2.get_environment_spec('eddd').environmentname, '<env unknown>')
        self.assertEqual(db2.get_environment_spec('eddd').args_parser.argspec, '')

        # "unknowns" should be preserved
        self.assertEqual(db2.unknown_macro_spec, db.unknown_macro_spec)
        self.assertEqual(db2.unknown_environment_spec, db.unknown_environment_spec)
        self.assertEqual(db2.unknown_specials_spec, db.unknown_specials_spec)

    def test_filter_context_1(self):
        
        db = LatexContextDb()
        db.set_unknown_macro_spec(MacroSpec('<macro unknown>'))
        db.set_unknown_environment_spec(EnvironmentSpec('<env unknown>'))
        db.add_context_category('cat1',
                                [ std_macro('aaa', '{'), std_macro('bbb', '[{[') ],
                                [ std_environment('eaaa', '{'), std_environment('ebbb', '[{[') ])
        db.add_context_category('cat2',
                                [ std_macro('aaa', '[{'), std_macro('ccc', None) ],
                                [ std_environment('eaaa', '[{'), std_environment('eccc', None) ])
        db.add_context_category('cat3',
                                [ std_macro('ccc', '*{'), std_macro('ddd', '{{[') ],
                                [ std_environment('eccc', '*{'), std_environment('eddd', '{{[') ],
                                prepend=True)
        
        db2 = db.filter_context(exclude_categories=['cat3'])
        # this should give 'ccc' from cat2, not cat3
        self.assertEqual(db2.get_macro_spec('ccc').macroname, 'ccc')
        self.assertEqual(db2.get_macro_spec('ccc').args_parser.argspec, '')
        # this should no longer exist
        self.assertEqual(db2.get_macro_spec('ddd').macroname, '<macro unknown>')
        self.assertEqual(db2.get_macro_spec('ddd').args_parser.argspec, '')

        # this should give 'eccc' from cat2, not cat3
        self.assertEqual(db2.get_environment_spec('eccc').environmentname, 'eccc')
        self.assertEqual(db2.get_environment_spec('eccc').args_parser.argspec, '')
        # this should no longer exist
        self.assertEqual(db2.get_environment_spec('eddd').environmentname, '<env unknown>')
        self.assertEqual(db2.get_environment_spec('eddd').args_parser.argspec, '')

    def test_filter_context_2(self):
        
        db = LatexContextDb()
        db.set_unknown_macro_spec(MacroSpec('<macro unknown>'))
        db.set_unknown_environment_spec(EnvironmentSpec('<env unknown>'))
        db.add_context_category('cat1',
                                [ std_macro('aaa', '{'), std_macro('bbb', '[{[') ],
                                [ std_environment('eaaa', '{'), std_environment('ebbb', '[{[') ])
        db.add_context_category('cat2',
                                [ std_macro('aaa', '[{'), std_macro('ccc', None) ],
                                [ std_environment('eaaa', '[{'), std_environment('eccc', None) ])
        db.add_context_category('cat3',
                                [ std_macro('ccc', '*{'), std_macro('ddd', '{{[') ],
                                [ std_environment('eccc', '*{'), std_environment('eddd', '{{[') ],
                                prepend=True)
        
        db2 = db.filter_context(keep_categories=['cat1', 'cat3'], exclude_categories=['cat3'])
        # this should give 'aaa' from cat1
        self.assertEqual(db2.get_macro_spec('aaa').macroname, 'aaa')
        self.assertEqual(db2.get_macro_spec('aaa').args_parser.argspec, '{')
        # this should no longer exist
        self.assertEqual(db2.get_macro_spec('ddd').macroname, '<macro unknown>')
        self.assertEqual(db2.get_macro_spec('ddd').args_parser.argspec, '')

        # this should give 'eaaa' from cat1
        self.assertEqual(db2.get_environment_spec('eaaa').environmentname, 'eaaa')
        self.assertEqual(db2.get_environment_spec('eaaa').args_parser.argspec, '{')
        # this should no longer exist
        self.assertEqual(db2.get_environment_spec('eddd').environmentname, '<env unknown>')
        self.assertEqual(db2.get_environment_spec('eddd').args_parser.argspec, '')

    def test_filter_context_3(self):
        
        db = LatexContextDb()
        db.set_unknown_macro_spec(MacroSpec('<macro unknown>'))
        db.set_unknown_environment_spec(EnvironmentSpec('<env unknown>'))
        db.add_context_category('cat1',
                                [ std_macro('aaa', '{'), std_macro('bbb', '[{[') ],
                                [ std_environment('eaaa', '{'), std_environment('ebbb', '[{[') ])
        db.add_context_category('cat2',
                                [ std_macro('aaa', '[{'), std_macro('ccc', None) ],
                                [ std_environment('eaaa', '[{'), std_environment('eccc', None) ])
        db.add_context_category('cat3',
                                [ std_macro('ccc', '*{'), std_macro('ddd', '{{[') ],
                                [ std_environment('eccc', '*{'), std_environment('eddd', '{{[') ],
                                prepend=True)
        
        db2 = db.filter_context(keep_categories=['cat1', 'cat3'], exclude_categories=['cat3'],
                                keep_which=['macros'])
        # this should give 'aaa' from cat1
        self.assertEqual(db2.get_macro_spec('aaa').macroname, 'aaa')
        self.assertEqual(db2.get_macro_spec('aaa').args_parser.argspec, '{')
        # this should no longer exist
        self.assertEqual(db2.get_macro_spec('ddd').macroname, '<macro unknown>')
        self.assertEqual(db2.get_macro_spec('ddd').args_parser.argspec, '')

        # no environments should exist any longer
        self.assertEqual(db2.get_environment_spec('eaaa').environmentname, '<env unknown>')
        self.assertEqual(db2.get_environment_spec('eaaa').args_parser.argspec, '')
        self.assertEqual(db2.get_environment_spec('eddd').environmentname, '<env unknown>')
        self.assertEqual(db2.get_environment_spec('eddd').args_parser.argspec, '')


    def test_filter_context_4(self):
        
        db = LatexContextDb()
        db.set_unknown_macro_spec(MacroSpec('<macro unknown>'))
        db.set_unknown_environment_spec(EnvironmentSpec('<env unknown>'))
        db.add_context_category('cat1',
                                [ std_macro('aaa', '{'), std_macro('bbb', '[{[') ],
                                [ std_environment('eaaa', '{'), std_environment('ebbb', '[{[') ])
        db.add_context_category('cat2',
                                [ std_macro('aaa', '[{'), std_macro('ccc', None) ],
                                [ std_environment('eaaa', '[{'), std_environment('eccc', None) ])
        db.add_context_category('cat3',
                                [ std_macro('ccc', '*{'), std_macro('ddd', '{{[') ],
                                [ std_environment('eccc', '*{'), std_environment('eddd', '{{[') ],
                                prepend=True)
        
        db2 = db.filter_context(keep_categories=['cat1', 'cat3'], exclude_categories=['cat3'],
                                keep_which=['environments'])
        # no macros should exist any longer
        self.assertEqual(db2.get_macro_spec('aaa').macroname, '<macro unknown>')
        self.assertEqual(db2.get_macro_spec('aaa').args_parser.argspec, '')
        self.assertEqual(db2.get_macro_spec('ddd').macroname, '<macro unknown>')
        self.assertEqual(db2.get_macro_spec('ddd').args_parser.argspec, '')

        # this should give 'eaaa' from cat1
        self.assertEqual(db2.get_environment_spec('eaaa').environmentname, 'eaaa')
        self.assertEqual(db2.get_environment_spec('eaaa').args_parser.argspec, '{')
        # this should no longer exist
        self.assertEqual(db2.get_environment_spec('eddd').environmentname, '<env unknown>')
        self.assertEqual(db2.get_environment_spec('eddd').args_parser.argspec, '')


        




if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#

