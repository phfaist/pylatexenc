import unittest
import sys
import logging

if sys.version_info.major > 2:
    def unicode(string): return string
    basestring = str

from pylatexenc.macrospec import (
    ParsedMacroArgs, MacroSpec, MacroStandardArgsParser, std_macro, std_environment
)

from pylatexenc import latexwalker
from pylatexenc.latexwalker import (
    LatexCharsNode, LatexGroupNode, LatexCommentNode, LatexMacroNode,
    LatexEnvironmentNode, LatexMathNode
)


# # monkey-patch ParsedMacroArgs to allow for equality comparison to check test
# # results
# def _tmp1133(a, b):
#     return a.argnlist == b.argnlist
# ParsedMacroArgs.__eq__ = _tmp1133

class MyAsserts(object):
    def assertPMAEqual(self, a, b):

        logger = logging.getLogger(__name__)

        if len(a.argnlist) != len(b.argnlist):
            logger.warning("assertParsedArgsEqual fails:\na = [\n%s\n]\nb = [\n%s\n]\n",
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


class TestMacroSpec(unittest.TestCase, MyAsserts):

    def __init__(self, *args, **kwargs):
        super(TestMacroSpec, self).__init__(*args, **kwargs)
        self.maxDiff = None
        
    def test_args_parser_marg_0(self):
        lw = latexwalker.LatexWalker(r'\cmd{ab}')
        s = MacroSpec('cmd', '{')
        (argd, p, l) = s.parse_args(lw, len(r'\cmd'))
        self.assertPMAEqual(
            argd,
            ParsedMacroArgs([ LatexGroupNode([LatexCharsNode('ab')]) ])
        )

    def test_args_parser_marg_1(self):
        lw = latexwalker.LatexWalker(r'\cmd ab')
        s = MacroSpec('cmd', '{')
        (argd, p, l) = s.parse_args(lw, len(r'\cmd'))
        self.assertPMAEqual(
            argd,
            ParsedMacroArgs([ LatexCharsNode('a') ])
        )

    def test_args_parser_oarg_0(self):
        lw = latexwalker.LatexWalker(r'\cmd[ab] xyz')
        s = MacroSpec('cmd', '[')
        (argd, p, l) = s.parse_args(lw, len(r'\cmd'))
        self.assertPMAEqual(
            argd,
            ParsedMacroArgs([ LatexGroupNode([LatexCharsNode('ab')]) ])
        )

    def test_args_parser_oarg_1(self):
        lw = latexwalker.LatexWalker(r'\cmd xyz')
        s = MacroSpec('cmd', '[')
        (argd, p, l) = s.parse_args(lw, len(r'\cmd'))
        self.assertPMAEqual(
            argd,
            ParsedMacroArgs([ None ])
        )

    def test_args_parser_star_0(self):
        lw = latexwalker.LatexWalker(r'\cmd xyz')
        s = MacroSpec('cmd', '*')
        (argd, p, l) = s.parse_args(lw, len(r'\cmd'))
        self.assertPMAEqual(
            argd,
            ParsedMacroArgs([ None ])
        )

    def test_args_parser_star_1(self):
        lw = latexwalker.LatexWalker(r'\cmd* xyz')
        s = MacroSpec('cmd', '*')
        (argd, p, l) = s.parse_args(lw, len(r'\cmd'))
        self.assertPMAEqual(
            argd,
            ParsedMacroArgs([ LatexCharsNode('*') ])
        )

    def test_args_parser_star_2(self):
        lw = latexwalker.LatexWalker(r'\cmd * xyz')
        s = MacroSpec('cmd', '*')
        (argd, p, l) = s.parse_args(lw, len(r'\cmd'))
        self.assertPMAEqual(
            argd,
            ParsedMacroArgs([ LatexCharsNode('*') ])
        )

    def test_args_parser_combined_0(self):
        lw = latexwalker.LatexWalker(r'\cmd{ab}c*')
        s = MacroSpec('cmd', '{*[{*')
        (argd, p, l) = s.parse_args(lw, len(r'\cmd'))
        self.assertPMAEqual(
            argd,
            ParsedMacroArgs([ LatexGroupNode([LatexCharsNode('ab')]), None, 
                              None, LatexCharsNode('c'), LatexCharsNode('*') ])
        )

    def test_args_parser_combined_1(self):
        lw = latexwalker.LatexWalker(r'\cmd x[ab]c*')
        s = MacroSpec('cmd', '{*[{*')
        (argd, p, l) = s.parse_args(lw, len(r'\cmd'))
        self.assertPMAEqual(
            argd,
            ParsedMacroArgs([ LatexCharsNode('x'), None,
                              LatexGroupNode([LatexCharsNode('ab')]),
                              LatexCharsNode('c'), LatexCharsNode('*') ])
        )







if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#

