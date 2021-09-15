import unittest
import sys
import logging

if sys.version_info.major > 2:
    def unicode(string): return string
    basestring = str

from pylatexenc.macrospec._argparsers.elaborateargs import (
    ParsedElaborateMacroArgs,
    MacroElaborateArgsParser,
    #
    ElaborateArgumentBase,
    ElaborateExpressionArgument,
    ElaborateNestableDelimitedArgument,
    ElaborateNestableDelimitedSimpleTokensArgument,
)

from pylatexenc import latexwalker


class MyAsserts(object):
    def __init__(self, *args, **kwargs):
        super(MyAsserts, self).__init__(*args, **kwargs)
        self.maxDiff = None

    def assertPEMAEqual(self, a, b):

        logger = logging.getLogger(__name__)

        if len(a.argnlist) != len(b.argnlist):
            logger.warning("assertParsedElaborateArgsEqual fails:\n"
                           "a = [\n%s\n]\nb = [\n%s\n]\n",
                           "\n".join('    '+str(x) for x in a.argnlist),
                           "\n".join('    '+str(x) for x in b.argnlist),)
            raise AssertionError("ParsedMacroArgs are different, lengths differ")

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


# ------------------------------------------------------------------------------

class TestElaborateExpressionArgument(unittest.TestCase, MyAsserts):

    def test_simple_1(self):
        lw = latexwalker.LatexWalker(r'{ab}\relax')
        
        parsing_state = lw.make_parsing_state()
        n, p, l = ElaborateExpressionArgument().parse_argument(lw, 0, parsing_state)
        
        self.assertEqual(
            n,
            latexwalker.LatexGroupNode(
                parsing_state=parsing_state,
                delimiters=('{','}'),
                nodelist=[
                    latexwalker.LatexCharsNode(
                        parsing_state=parsing_state,
                        chars='ab',
                        pos=1,len=2
                    )
                ],
                pos=0,
                len=4)
        )
        self.assertEqual(p, 0)
        self.assertEqual(l, 4)

    def test_simple_2(self):
        lw = latexwalker.LatexWalker(r'{ab}\relax')
        
        parsing_state = lw.make_parsing_state()
        n, p, l = ElaborateExpressionArgument().parse_argument(lw, 4, parsing_state)
        
        self.assertEqual(
            n,
            latexwalker.LatexMacroNode(
                parsing_state=parsing_state,
                macroname='relax',
                nodeargd=None,
                pos=4,
                len=6
            )
        )
        self.assertEqual(p, 4)
        self.assertEqual(l, 6)

class TestElaborateNestableDelimitedArgument(unittest.TestCase, MyAsserts):

    def test_simple_1(self):
        lw = latexwalker.LatexWalker(r'{ab}')
        
        A = ElaborateNestableDelimitedArgument(
            delimiters=('{','}')
        )

        parsing_state = lw.make_parsing_state()
       
        n, p, l = A.parse_argument(lw, 0, parsing_state)
        
        self.assertEqual(
            n,
            latexwalker.LatexGroupNode(
                parsing_state=parsing_state,
                delimiters=('{','}'),
                nodelist=[
                    latexwalker.LatexCharsNode(
                        parsing_state=parsing_state,
                        chars='ab',
                        pos=1,len=2
                    )
                ],
                pos=0,
                len=4)
        )
        self.assertEqual(p, 0)
        self.assertEqual(l, 4)

    def test_simple_1b(self):
        lw = latexwalker.LatexWalker(r'(ab)')
        
        A = ElaborateNestableDelimitedArgument(
            delimiters=('(',')')
        )

        parsing_state = lw.make_parsing_state()
       
        n, p, l = A.parse_argument(lw, 0, parsing_state)
        
        self.assertEqual(
            n,
            latexwalker.LatexGroupNode(
                parsing_state=parsing_state,
                delimiters=('(',')'),
                nodelist=[
                    latexwalker.LatexCharsNode(
                        parsing_state=parsing_state,
                        chars='ab',
                        pos=1,len=2
                    )
                ],
                pos=0,
                len=4)
        )
        self.assertEqual(p, 0)
        self.assertEqual(l, 4)

    def test_simple_1c(self):
        lw = latexwalker.LatexWalker(r'[ab]')
        
        A = ElaborateNestableDelimitedArgument(
            delimiters=('[',']')
        )

        parsing_state = lw.make_parsing_state()
       
        n, p, l = A.parse_argument(lw, 0, parsing_state)
        
        self.assertEqual(
            n,
            latexwalker.LatexGroupNode(
                parsing_state=parsing_state,
                delimiters=('[',']'),
                nodelist=[
                    latexwalker.LatexCharsNode(
                        parsing_state=parsing_state,
                        chars='ab',
                        pos=1,len=2
                    )
                ],
                pos=0,
                len=4)
        )
        self.assertEqual(p, 0)
        self.assertEqual(l, 4)

    def test_simple_2(self):
        lw = latexwalker.LatexWalker(r'{ab}\relax')
        
        A = ElaborateNestableDelimitedArgument(
            delimiters=('{','}'),
        )

        parsing_state = lw.make_parsing_state()
        with self.assertRaises(latexwalker.LatexWalkerParseError):
            n, p, l = A.parse_argument(lw, 4, parsing_state)


    def test_simple_2(self):
        lw = latexwalker.LatexWalker(r'{ab}\relax')
        
        A = ElaborateNestableDelimitedArgument(
            delimiters=('{','}'),
            optional=True
        )

        parsing_state = lw.make_parsing_state()
        n, p, l = A.parse_argument(lw, 4, parsing_state)
        self.assertIsNone(n)
        self.assertEqual(p, 4)
        self.assertEqual(l, 0)


class TestElaborateNestableDelimitedSimpleTokensArgument(unittest.TestCase, MyAsserts):

    def test_simple_1(self):
        lw = latexwalker.LatexWalker(r'<a\begin\relax{]}{$}>.....')
        
        A = ElaborateNestableDelimitedSimpleTokensArgument(
            delimiters=('<','>')
        )

        parsing_state = lw.make_parsing_state()
       
        n, p, l = A.parse_argument(lw, 0, parsing_state)
        
        self.assertEqual(
            n,
            latexwalker.LatexGroupNode(
                parsing_state=parsing_state,
                delimiters=('<','>'),
                nodelist=[
                    latexwalker.LatexCharsNode(
                        parsing_state=parsing_state,
                        chars=r'a\begin\relax{]}{$}',
                        pos=1,len=19
                    )
                ],
                pos=0,
                len=21)
        )
        self.assertEqual(p, 0)
        self.assertEqual(l, 21)


# --------------------------------------

class TestMacroElaborateArgsParser(unittest.TestCase, MyAsserts):

    def __init__(self, *args, **kwargs):
        super(TestMacroElaborateArgsParser, self).__init__(*args, **kwargs)
        self.maxDiff = None
        
    def test_marg2_0(self):
        lw = latexwalker.LatexWalker(r'{ab}\relax{\begin{subequations}$$}')
        argument_spec_list = [
            ElaborateExpressionArgument(),
            ElaborateNestableDelimitedArgument(delimiters=('[',']'), optional=True),
            ElaborateExpressionArgument(),
            ElaborateNestableDelimitedSimpleTokensArgument(optional=True)
        ]
        s = MacroElaborateArgsParser(argument_spec_list=argument_spec_list)
        parsing_state = lw.make_parsing_state()
        (argd, p, l) = s.parse_args(lw, 0, parsing_state=parsing_state)
        self.assertPEMAEqual(
            argd,
            ParsedElaborateMacroArgs(
                argument_spec_list=argument_spec_list,
                argnlist=[
                    latexwalker.LatexGroupNode(
                        parsing_state=parsing_state,
                        delimiters=('{','}'),
                        nodelist=[
                            latexwalker.LatexCharsNode(
                                parsing_state=parsing_state,
                                chars='ab',
                                pos=1,len=2
                            )
                        ],
                        pos=0,len=4),
                    None,
                    latexwalker.LatexMacroNode(
                        parsing_state=parsing_state,
                        macroname='relax',
                        nodeargd=None,
                        pos=4,len=6),
                    latexwalker.LatexGroupNode(
                        parsing_state=parsing_state,
                        delimiters=('{','}'),
                        nodelist=[
                            latexwalker.LatexCharsNode(
                                parsing_state=parsing_state,
                                chars=r'\begin{subequations}$$',
                                pos=11,len=22
                            )
                        ],
                        pos=10,len=24),
                ])
        )
    
    def test_marg2_1(self):
        lw = latexwalker.LatexWalker(r'{ab}(hell)')
        argument_spec_list = [
            ElaborateExpressionArgument(),
            ElaborateNestableDelimitedArgument(delimiters=('(',')'))
        ]
        s = MacroElaborateArgsParser(argument_spec_list=argument_spec_list)
        parsing_state = lw.make_parsing_state()
        (argd, p, l) = s.parse_args(lw, 0, parsing_state=parsing_state)

        self.assertPEMAEqual(
            argd,
            ParsedElaborateMacroArgs(
                argument_spec_list=argument_spec_list,
                argnlist=[
                    latexwalker.LatexGroupNode(
                        parsing_state=parsing_state,
                        delimiters=('{','}'),
                        nodelist=[
                            latexwalker.LatexCharsNode(
                                parsing_state=parsing_state,
                                chars='ab',
                                pos=1,len=2
                            )
                        ],
                        pos=0,len=4),
                    latexwalker.LatexGroupNode(
                        parsing_state=parsing_state,
                        delimiters=('(',')'),
                        nodelist=[
                            latexwalker.LatexCharsNode(
                                parsing_state=parsing_state,
                                chars='hell',
                                pos=5,len=4
                            )
                        ],
                        pos=4,len=6),
                ])
        )




if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#

