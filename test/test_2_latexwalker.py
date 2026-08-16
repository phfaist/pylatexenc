# -*- coding: utf-8 -*-

import unittest
import logging
import warnings
import json

import pytest

from pylatexenc.latexwalker import (
    LatexWalker, LatexToken, LatexCharsNode, LatexGroupNode, LatexCommentNode,
    LatexMacroNode, LatexSpecialsNode, LatexEnvironmentNode, LatexMathNode,
    LatexWalkerParseError, get_default_latex_context_db,
    MacrosDef, make_json_encoder,
    get_latex_nodes as pyltxenc1_get_latex_nodes,
)

from pylatexenc import macrospec

from pylatexenc.latexnodes import ParsedArgumentsInfo
from pylatexenc.latexnodes import parsers as latexnodes_parsers

from ._helpers_tests import HelperProvideAssertEqualsForLegacyTests

# These tests exercise the pylatexenc 2.x compatibility API on purpose, so the
# associated deprecation warnings are expected and would only drown out the
# pytest output.  (The warnings.simplefilter() calls in the test case
# constructors below don't help under pytest, which resets the warning filters
# around each test.)
pytestmark = pytest.mark.filterwarnings("ignore:Deprecated \\(pylatexenc")

# # patch __eq__ for comparison with lists
# from pylatexenc.latexnodes import LatexNode, LatexNodeList
# LatexNodeList.__eq__ = lambda self, other: self.nodelist == other


def _tmp1133(a, b):
    return b is not None and a.argnlist == b.argnlist
macrospec.ParsedMacroArgs.__eq__ = _tmp1133


class TestLatexWalker(HelperProvideAssertEqualsForLegacyTests, unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestLatexWalker, self).__init__(*args, **kwargs)
        self.maxDiff = None

        # self.addTypeEqualityFunc(LatexNode, self._assert_nodes_equal)
        # self.addTypeEqualityFunc(LatexNodeList, self._assert_lists_equal)
        # self.addTypeEqualityFunc(list, self._assert_lists_equal)
        # self.addTypeEqualityFunc(tuple, self._assert_lists_equal)

        warnings.simplefilter('ignore', DeprecationWarning)

        
    def test_get_token(self):
        
        latextext = \
            r'''Text \`accent and \textbf{bold text} and $\vec b$ vector \& also Fran\c cois
\begin{enumerate}[(i)]
\item Hi there!  % here goes a comment
\item[a] Hello!  @@@
     \end{enumerate}
\mymacro

New paragraph
'''
        lw = LatexWalker(latextext)
        
        self.assertEqual(lw.get_token(pos=0),
                         LatexToken(tok='char', arg='T', pos=0, len=1, pre_space=''))
        self.assertEqual(lw.get_token(pos=1),
                         LatexToken(tok='char', arg='e', pos=1, len=1, pre_space=''))
        p = latextext.find(r'\`')
        self.assertEqual(lw.get_token(pos=p),
                         LatexToken(tok='macro', arg='`', pos=p, len=2, pre_space=''))
        p = latextext.find(r'\textbf')-1 # pre space
        self.assertEqual(lw.get_token(pos=p),
                         LatexToken(tok='macro', arg='textbf', pos=p+1, len=7, pre_space=' '))
        p = latextext.find(r'\vec') # post-space
        self.assertEqual(lw.get_token(pos=p),
                         LatexToken(tok='macro', arg='vec', pos=p, len=5, pre_space='', post_space=' '))
        p = latextext.find(r'\&')-1 # pre-space and *no* post-space
        self.assertEqual(lw.get_token(pos=p),
                         LatexToken(tok='macro', arg='&', pos=p+1, len=2, pre_space=' ', post_space=''))
        p = latextext.find(r'\begin')
        self.assertEqual(lw.get_token(pos=p, environments=False),
                         LatexToken(tok='macro', arg='begin', pos=p, len=6, pre_space=''))
        p = latextext.find(r'\begin')
        self.assertEqual(lw.get_token(pos=p),
                         LatexToken(tok='begin_environment', arg='enumerate', pos=p,
                                    len=len(r'\begin{enumerate}'), pre_space=''))
        p = latextext.find(r'@@@')+3 # pre space to \end
        self.assertEqual(lw.get_token(pos=p),
                         LatexToken(tok='end_environment', arg='enumerate', pos=p+6,
                                    len=len(r'\end{enumerate}'), pre_space='\n     '))
        p = latextext.find(r'%')-1
        self.assertEqual(lw.get_token(pos=p),
                         LatexToken(tok='comment', arg=' here goes a comment', pos=p+1,
                                    len=len('% here goes a comment\n'), pre_space=' ',
                                    post_space='\n'))
        p = latextext.find(r'{')
        self.assertEqual(lw.get_token(pos=p),
                         LatexToken(tok='brace_open', arg='{', pos=p, len=1, pre_space=''))
        p = latextext.find(r'}')
        self.assertEqual(lw.get_token(pos=p),
                         LatexToken(tok='brace_close', arg='}', pos=p, len=1, pre_space=''))
        p = latextext.find(r'[')
        self.assertEqual(lw.get_token(pos=p, brackets_are_chars=False),
                         LatexToken(tok='brace_open', arg='[', pos=p, len=1, pre_space=''))
        p = latextext.find(r']')
        self.assertEqual(lw.get_token(pos=p, brackets_are_chars=False),
                         LatexToken(tok='brace_close', arg=']', pos=p, len=1, pre_space=''))
        p = latextext.find(r'[')
        self.assertEqual(lw.get_token(pos=p, brackets_are_chars=True),
                         LatexToken(tok='char', arg='[', pos=p, len=1, pre_space=''))
        p = latextext.find(r']')
        self.assertEqual(lw.get_token(pos=p, brackets_are_chars=True),
                         LatexToken(tok='char', arg=']', pos=p, len=1, pre_space=''))
        p = latextext.find(r'\mymacro')
        self.assertEqual(lw.get_token(pos=p),
                         # no post_space because of paragraph
                         LatexToken(tok='macro', arg='mymacro', pos=p, len=8,
                                    pre_space='', post_space=''))


    def test_get_token_mathmodes(self):
        
        latextext = r"""
Here is an inline expression like $\vec{x} + \hat p$ and a display equation $$
   ax + b = y
$$ and another, with a subtle inner math mode:
\[ cx^2+z=-d\quad\text{if $x<0$} \]
And a final inline math mode \(\mbox{Prob}(\mbox{some event if $x>0$})=1\).
"""

        lw = LatexWalker(latextext)

        p = latextext.find(r'$')
        self.assertEqual(lw.get_token(pos=p),
                         LatexToken(tok='mathmode_inline', arg='$', pos=p, len=1, pre_space=''))
        p = latextext.find(r' \(')
        self.assertEqual(lw.get_token(pos=p),
                         LatexToken(tok='mathmode_inline', arg=r'\(', pos=p+1, len=2, pre_space=' '))
        p = latextext.find(r'\)')
        self.assertEqual(lw.get_token(pos=p),
                         LatexToken(tok='mathmode_inline', arg=r'\)', pos=p, len=2, pre_space=''))

        p = latextext.find(r'$$')
        self.assertEqual(lw.get_token(pos=p),
                         LatexToken(tok='mathmode_display', arg='$$', pos=p, len=2, pre_space=''))

        p = latextext.find('\n'+r'\[')
        self.assertEqual(lw.get_token(pos=p),
                         LatexToken(tok='mathmode_display', arg=r'\[', pos=p+1, len=2, pre_space='\n'))

        p = latextext.find(r'\]')
        self.assertEqual(lw.get_token(pos=p),
                         LatexToken(tok='mathmode_display', arg=r'\]', pos=p, len=2, pre_space=''))

    def test_get_token_mathmodes_dollardollar(self):
        
        # pos counter:  |0        |10       |20       |30     |38
        latextext = r"""x$\dagger$$\dagger$$$A=B\mbox{$b=a$}$$"""

        lw = LatexWalker(latextext)

        ps = lw.make_parsing_state()

        def sub_math_ps(delim):
            return ps.sub_context(in_math_mode=True, math_mode_delimiter=delim)

        p = 1
        self.assertEqual(
            lw.get_token(pos=p, parsing_state=ps),
            LatexToken(tok='mathmode_inline', arg='$', pos=p, len=1, pre_space='')
        )
        p = 9
        self.assertEqual(
            lw.get_token(pos=p, parsing_state=sub_math_ps('$')),
            LatexToken(tok='mathmode_inline', arg='$', pos=p, len=1, pre_space='')
        )
        p = 10
        self.assertEqual(
            lw.get_token(pos=p),
            LatexToken(tok='mathmode_inline', arg='$', pos=p, len=1, pre_space='')
        )
        p = 18
        self.assertEqual(
            lw.get_token(pos=p, parsing_state=sub_math_ps('$')),
            LatexToken(tok='mathmode_inline', arg='$', pos=p, len=1, pre_space='')
        )
        p = 19
        self.assertEqual(
            lw.get_token(pos=p),
            LatexToken(tok='mathmode_display', arg='$$', pos=p, len=2, pre_space='')
        )
        p = 30
        self.assertEqual(
            lw.get_token(pos=p),
            LatexToken(tok='mathmode_inline', arg='$', pos=p, len=1, pre_space='')
        )
        p = 34
        self.assertEqual(
            lw.get_token(pos=p, parsing_state=sub_math_ps('$')),
            LatexToken(tok='mathmode_inline', arg='$', pos=p, len=1, pre_space='')
        )
        p = 36
        self.assertEqual(
            lw.get_token(pos=p, parsing_state=sub_math_ps('$$')),
            LatexToken(tok='mathmode_display', arg='$$', pos=p, len=2, pre_space='')
        )
        


    def test_get_latex_expression(self):
        
        latextext = r'''Text and \`accent and \textbf{bold text} and $\vec b$ more stuff for Fran\c cois
\begin{enumerate}[(i)]
\item Hi there!  % here goes a comment
\item[a] Hello!  @@@
     \end{enumerate}
?`Some ``specials,'' too & more?
'''
        lw = LatexWalker(latextext, tolerant_parsing=True)

        parsing_state = lw.make_parsing_state()

        self.assertEqual(lw.get_latex_expression(pos=0, parsing_state=parsing_state),
                         (LatexCharsNode(parsing_state=parsing_state,
                                         chars='T',
                                         pos=0, len=1),0,1,))
        p = latextext.find(r'\`')
        self.assertEqual(lw.get_latex_expression(pos=p, parsing_state=parsing_state),
                         (LatexMacroNode(parsing_state=parsing_state,
                                         macroname='`',
                                         nodeargd=None, pos=p, len=2),p,2,))
        p = latextext.find(r'{')
        self.assertEqual(lw.get_latex_expression(pos=p, parsing_state=parsing_state),
                         (LatexGroupNode(parsing_state=parsing_state,
                                         nodelist=[
                                             LatexCharsNode(parsing_state=parsing_state,
                                                            chars='bold text',
                                                            pos=p+1,len=9)
                                         ],
                                         pos=p, len=11),
                          p,11,))
        p = latextext.find(r'%')-2 # check: correctly skips comments also after space
        self.assertEqual(lw.get_latex_expression(pos=p, parsing_state=parsing_state),
                         (LatexMacroNode(parsing_state=parsing_state,
                                         macroname='item',
                                         nodeargd=None,
                                         pos=p+2+len('% here goes a comment\n'),
                                         len=5),
                          p+2+len('% here goes a comment\n'),5,))
        # check correct behavior if directly on brace close
        p = latextext.find(r'}')
        self.assertEqual(lw.get_latex_expression(pos=p, parsing_state=parsing_state,
                                                 strict_braces=True),
                         (LatexCharsNode(parsing_state=parsing_state,
                                         chars='', pos=p, len=0),p,0,))
        lw2 = LatexWalker(latextext, tolerant_parsing=False)
        parsing_state2 = lw2.make_parsing_state()
        self.assertEqual(lw2.get_latex_expression(pos=p, parsing_state=parsing_state2,
                                                  strict_braces=False),
                         (LatexCharsNode(parsing_state=parsing_state2,
                                         chars='', pos=p, len=0),p,0,))
        with self.assertRaises(LatexWalkerParseError):
            dummy = lw2.get_latex_expression(pos=p, parsing_state=parsing_state2,
                                             strict_braces=True)
        
        p = latextext.find(r'?`')
        self.assertEqual(lw.get_latex_expression(pos=p, parsing_state=parsing_state),
                         (LatexSpecialsNode(
                             parsing_state=parsing_state,
                             specials_chars='?`',
                             spec=parsing_state.latex_context.get_specials_spec(r'?`'),
                             nodeargd=None,
                             pos=p, len=2
                         ), p, 2))


    def test_get_latex_expression_always_advances(self):

        # The standard pylatexenc 1.x/2.x idiom is to call get_latex_expression()
        # repeatedly in a loop.  Even for tokens that cannot form an expression
        # (like a math mode delimiter), the reported position must advance so
        # that the loop terminates.

        latextext = r'a $x$ b'
        lw = LatexWalker(latextext, tolerant_parsing=True)

        positions = []
        pos = 0
        num_iterations = 0
        while pos < len(latextext):
            num_iterations += 1
            self.assertLess(num_iterations, 20) # protect against infinite loop
            positions.append(pos)
            dummy_node, p, l = lw.get_latex_expression(pos)
            self.assertGreater(p + l, pos)
            pos = p + l

        self.assertEqual(positions, [0, 1, 3, 4, 5])


    def test_get_latex_maybe_optional_arg_pre_space(self):

        # whitespace before the '[' is skipped, as in pylatexenc 2
        lw = LatexWalker('  [abc]', tolerant_parsing=True)
        result = lw.get_latex_maybe_optional_arg(pos=0)
        self.assertIsNotNone(result)
        gn, gn_pos, gn_len = result
        self.assertEqual((gn.delimiters, gn_pos, gn_len), (('[', ']'), 2, 5))

        # ... but there's still no optional argument if there's no '['
        lw2 = LatexWalker('  abc', tolerant_parsing=True)
        self.assertIsNone(lw2.get_latex_maybe_optional_arg(pos=0))


    def test_get_latex_maybe_optional_arg(self):
        
        latextext = r'''Text and \`accent and \textbf{bold text} and $\vec b$ more stuff for Fran\c cois
\begin{enumerate}[(i)]
\item Hi there!  % here goes a comment
\item[a] Hello!  @@@
     \end{enumerate}
Indeed thanks to \cite[Lemma 3]{Author}, we know that...
'''
        lw = LatexWalker(latextext, tolerant_parsing=False)

        parsing_state = lw.make_parsing_state()

        p = latextext.find(r'\textbf')+len(r'\textbf')
        self.assertIsNone(lw.get_latex_maybe_optional_arg(pos=p, parsing_state=parsing_state))

        p = latextext.find(r'\cite')+len(r'\cite')
        gn, gn_pos, gn_len = \
            lw.get_latex_maybe_optional_arg(pos=p, parsing_state=parsing_state)
        pssq = gn.nodelist[0].parsing_state
        self.assertEqual(set(pssq.latex_group_delimiters),
                         set([ ('{','}'), ('[',']'), ]))
        self.assertEqual((gn, gn_pos, gn_len),
                         (LatexGroupNode(
                             parsing_state=pssq,
                             delimiters=('[', ']'),
                             nodelist=[
                                 LatexCharsNode(
                                     parsing_state=pssq,
                                     chars='Lemma 3',
                                     pos=p+1,
                                     len=len('Lemma 3'),
                                 )
                             ],
                             pos=p,
                             len=9
                         ),p,9,))


    def test_get_latex_braced_group(self):

        latextext = r'''Text and \`accent and \textbf{bold text} and $\vec b$ more stuff for Fran\c cois
\begin{enumerate}[(i)]
\item Hi there!  % here goes a comment
\item[a] Hello!  @@@
     \end{enumerate}
Indeed thanks to \cite[Lemma 3]{Author}, we know that...
Also: {\itshape some italic text}.
'''
        lw = LatexWalker(latextext, tolerant_parsing=False)
        parsing_state = lw.make_parsing_state()

        p = latextext.find(r'Also: {')+len('Also:') # points on space after 'Also:'
        good_parsed_structure = \
            ( LatexGroupNode(
                parsing_state=parsing_state,
                delimiters=('{','}'),
                nodelist=[
                    LatexMacroNode(parsing_state=parsing_state,
                                   macroname='itshape',
                                   macro_post_space=' ',
                                   pos=p+2,
                                   len=len(r'\itshape ')),
                    LatexCharsNode(parsing_state=parsing_state,
                                   chars='some italic text',
                                   pos=(p+16-5),
                                   len=32-16)
                ],
                pos=p+1,
                len=len(r'{\itshape some italic text}')
              ),
              p+1, len(r'{\itshape some italic text}'), )
        self.assertEqual(
            lw.get_latex_braced_group(pos=p, brace_type='{', parsing_state=parsing_state),
            good_parsed_structure
        )
        self.assertEqual(
            lw.get_latex_braced_group(pos=p+1, brace_type='{', parsing_state=parsing_state),
            good_parsed_structure
        )

        p = latextext.find(r'[(i)]')
        (lbg_nl, lbg_pos, lbg_len) = \
            lw.get_latex_braced_group(pos=p, brace_type='[', parsing_state=parsing_state)
        pssq = lbg_nl.parsing_state
        self.assertEqual(set(pssq.latex_group_delimiters),
                         set([ ('{','}'), ('[',']'), ]))
        self.assertEqual(
            (lbg_nl, lbg_pos, lbg_len),
            (LatexGroupNode(parsing_state=pssq,
                            delimiters=('[', ']'),
                            nodelist=[
                                LatexCharsNode(parsing_state=pssq,
                                               chars='(i)',
                                               pos=p+1, len=3),
                            ],
                            pos=p, len=5),
             p, 5,)
        )
        
    def test_get_latex_environment(self):

        latextext = r'''Text and \`accent and \textbf{bold text} and $\vec b$ more stuff for Fran\c cois
\begin{enumerate}[(i)]
\item Hi there!  % here goes a comment
 \item[a] Hello!  @@@
     \end{enumerate}
Indeed thanks to \cite[Lemma 3]{Author}, we know that...
Also: {\itshape some italic text}.
'''
        lw = LatexWalker(latextext, tolerant_parsing=False)
        parsing_state = lw.make_parsing_state()

        p = latextext.find(r'\begin{enumerate}')
        (nl, nlpos, nllen) = \
            lw.get_latex_environment(pos=p, environmentname='enumerate',
                                     parsing_state=parsing_state)
        pssq1 = nl.nodeargd.argnlist[0].parsing_state
        self.assertEqual(set(pssq1.latex_group_delimiters),
                         set([ ('{','}'), ('[',']'), ]))
        pssq2x = nl.nodelist[4].nodeargd.argnlist[0].parsing_state
        self.assertEqual(set(pssq2x.latex_group_delimiters),
                         set([ ('{','}'), ('[',']'), ]))

        good_parsed_structure = \
            (LatexEnvironmentNode(
                parsing_state=parsing_state,
                environmentname='enumerate',
                nodelist=[
                    LatexCharsNode(parsing_state=parsing_state,
                                   chars='\n',
                                   pos=p+22, len=1),
                    LatexMacroNode(parsing_state=parsing_state,
                                   macroname='item',
                                   nodeargd=macrospec.ParsedMacroArgs(argspec='[', argnlist=[None]),
                                   macro_post_space=' ',
                                   pos=p+23, len=6),
                    LatexCharsNode(parsing_state=parsing_state,
                                   chars='Hi there!  ',
                                   pos=p+23+6, len=17-6),
                    LatexCommentNode(parsing_state=parsing_state,
                                     comment=' here goes a comment',
                                     comment_post_space='\n ',
                                     pos=p+23+17, len=38-17+2),
                    LatexMacroNode(
                        parsing_state=parsing_state,
                        macroname='item',
                        nodeargd=macrospec.ParsedMacroArgs(argspec='[', argnlist=[
                            LatexGroupNode(
                                parsing_state=pssq2x,
                                delimiters=('[', ']'),
                                nodelist=[
                                    LatexCharsNode(parsing_state=pssq2x,
                                                   chars='a',
                                                   pos=p+23+39+7, len=1)
                                ],
                                pos=p+23+39+6, len=3)
                        ]),
                        pos=p+23+39+1,
                        len=9-1
                    ),
                    LatexCharsNode(parsing_state=parsing_state,
                                   chars=' Hello!  @@@\n     ',
                                   pos=p+23+39+9,
                                   len=22+5-9)
                ],
                nodeargd=macrospec.ParsedMacroArgs(argspec='[', argnlist=[
                    LatexGroupNode(
                        parsing_state=pssq1,
                        delimiters=('[', ']'),
                        nodelist=[
                            LatexCharsNode(parsing_state=pssq1,
                                           chars='(i)',
                                           pos=p+18,len=21-18)
                        ],
                        pos=p+17,len=22-17),
                ]),
                pos=p,
                len=latextext.find(r'\end{enumerate}')+len(r'\end{enumerate}')-p
             ), p, latextext.find(r'\end{enumerate}')+len(r'\end{enumerate}')-p)
        self.assertEqual(
            (nl, nlpos, nllen),
            good_parsed_structure
        )

        with self.assertRaises(LatexWalkerParseError):
            dummy = lw.get_latex_environment(pos=p, environmentname='XYZNFKLD-WRONG',
                                             parsing_state=parsing_state)

    def test_get_latex_nodes(self):

        latextext = r'''Text and \`accent and \textbf{bold text} and $\vec b$ more stuff for Fran\c cois
\begin{enumerate}[(i)]
\item Hi there!  % here goes a comment
\item[a] Hello!  @@@
     \end{enumerate}
Indeed thanks to \cite[Lemma 3]{Author}, we know that...
Also: {\itshape some italic text}.
'''
        lw = LatexWalker(latextext, tolerant_parsing=False)
        parsing_state = lw.make_parsing_state()

        #lw.get_latex_nodes(pos=0,stop_upon_closing_brace=None,stop_upon_end_environment=None,
        #                   stop_upon_closing_mathmode=None)

        p = latextext.find('Also: {')
        self.assertEqual(
            lw.get_latex_nodes(pos=p, parsing_state=parsing_state),
            ([
                LatexCharsNode(parsing_state=parsing_state,
                               chars='Also: ',
                               pos=p, len=6),
                LatexGroupNode(parsing_state=parsing_state,
                               delimiters=('{', '}'),
                               nodelist=[
                                   LatexMacroNode(parsing_state=parsing_state,
                                                  macroname='itshape',
                                                  macro_post_space=' ',
                                                  pos=p+7,len=16-7),
                                   LatexCharsNode(parsing_state=parsing_state,
                                                  chars='some italic text',
                                                  pos=p+16,len=32-16)
                               ],
                               pos=p+6,len=33-6),
                LatexCharsNode(parsing_state=parsing_state,
                               chars='.\n',
                               pos=p+33,len=2)
            ], p, len(latextext)-p)
        )

        p = latextext.find('Also: {')+len('Also: {') # points inside right after open brace
        self.assertEqual(
            lw.get_latex_nodes(pos=p, stop_upon_closing_brace='}',
                               parsing_state=parsing_state),
            ([
                LatexMacroNode(parsing_state=parsing_state,
                               macroname='itshape', macro_post_space=' ',
                               pos=p,len=16-7),
                LatexCharsNode(parsing_state=parsing_state,
                               chars='some italic text',
                               pos=p+16-7,len=32-16),
             ], p, len(r'\itshape some italic text}')))

        # test our own macro lists etc.
        pindeed = latextext.find('Indeed thanks to')
        lineindeed = latextext[pindeed:latextext.find('\n', pindeed)]
        lw2 = LatexWalker(lineindeed, tolerant_parsing=False,
                          macro_dict={'cite': macrospec.std_macro('cite',False,4)})
        parsing_state2 = lw2.make_parsing_state()
        self.assertEqual(
            lw2.get_latex_nodes(pos=0, parsing_state=parsing_state2),
            ([
                LatexCharsNode(parsing_state=parsing_state2,
                               chars='Indeed thanks to ',
                               pos=0,len=17),
                LatexMacroNode(
                    parsing_state=parsing_state2,
                    macroname='cite',
                    nodeargd=macrospec.ParsedMacroArgs(argspec='{{{{', argnlist=[
                        LatexCharsNode(parsing_state=parsing_state2,
                                       chars='[',
                                       pos=22,len=1),
                        LatexCharsNode(parsing_state=parsing_state2,
                                       chars='L',
                                       pos=23,len=1),
                        LatexCharsNode(parsing_state=parsing_state2,
                                       chars='e',
                                       pos=24,len=1),
                        LatexCharsNode(parsing_state=parsing_state2,
                                       chars='m',
                                       pos=25,len=1),
                    ]),
                    pos=17,len=26-17),
            LatexCharsNode(parsing_state=parsing_state2,
                           chars='ma 3]',
                           pos=26,len=31-26),
            LatexGroupNode(parsing_state=parsing_state2,
                           delimiters=('{', '}'),
                           nodelist=[
                               LatexCharsNode(parsing_state=parsing_state2,
                                              chars='Author',
                                              pos=32,len=38-32),
                           ],
                           pos=31,len=39-31),
            LatexCharsNode(parsing_state=parsing_state2,
                           chars=', we know that...',
                           pos=39,len=56-39),
            ], 0, len(lineindeed)))
       

    def test_get_latex_nodes_mathmodes(self):

        latextext = r"""
Here is an inline expression like $\vec{x} + \hat p$ and a display equation $$
   ax + b = y
$$ and another, with a subtle inner math mode:
\[ cx^2+z=-d\quad\text{if $x<0$} \]
And a final inline math mode \(\mbox{Prob}(\mbox{some event if \(x>0\)})=1\).
"""

        lw = LatexWalker(latextext, tolerant_parsing=False)
        parsing_state = lw.make_parsing_state()

        p = latextext.find('$')
        good_parsed_structure = lambda parsing_state: [
            LatexMacroNode(parsing_state=parsing_state,
                           macroname=r'vec',
                           nodeargd=macrospec.ParsedMacroArgs(argspec='{', argnlist=[
                               LatexGroupNode(parsing_state=parsing_state,
                                              delimiters=('{', '}'),
                                              nodelist=[
                                                  LatexCharsNode(parsing_state=parsing_state,
                                                                 chars='x',
                                                                 pos=1+40,len=1)
                                              ],
                                              pos=1+39,len=3)
                           ]),
                           macro_post_space='',
                           pos=1+35,len=42-35),
            LatexCharsNode(parsing_state=parsing_state,
                           chars=r' + ',
                           pos=1+42,len=45-42),
            LatexMacroNode(parsing_state=parsing_state,
                           macroname=r'hat',
                           nodeargd=macrospec.ParsedMacroArgs(argspec='{', argnlist=[
                               LatexCharsNode(parsing_state=parsing_state,
                                              chars='p',
                                              pos=1+50,len=1)]),
                           macro_post_space=' ',
                           pos=1+45,len=51-45),
        ]
        parsing_state_math = lw.make_parsing_state(in_math_mode=True)
        self.assertTrue(parsing_state_math.in_math_mode)
        nodes, pos, len_ = lw.get_latex_nodes(pos=p+1, stop_upon_closing_mathmode='$',
                                              parsing_state=parsing_state_math)
        self.assertEqual(
            (nodes, pos, len_),
            ( good_parsed_structure(parsing_state_math) ,
              p+1, len(r'\vec{x} + \hat p$') ) # len includes closing token
        )
        # check that first node is math mode node when parsing starting from & including first '$'
        nodes = lw.get_latex_nodes(pos=p, parsing_state=parsing_state)[0]
        parsing_state_inner = nodes[0].nodelist[0].parsing_state # inner state -- math mode -- get this
        self.assertTrue(parsing_state_inner.in_math_mode)
        self.assertEqual(
            nodes[0],
            LatexMathNode(parsing_state=parsing_state,
                          displaytype='inline',
                          nodelist=good_parsed_structure(parsing_state_inner),
                          pos=p, len=len(r'$\vec{x} + \hat p$'), delimiters=('$','$'))
        )


        p = latextext.find('$$')
        self.assertEqual(
            lw.get_latex_nodes(pos=p+2, stop_upon_closing_mathmode='$$', parsing_state=parsing_state),
            ( [ LatexCharsNode(parsing_state=parsing_state,
                               chars='\n   ax + b = y\n',
                               pos=p+2,len=len('\n   ax + b = y\n')), ] ,
              p+2, len('\n   ax + b = y\n$$') ) # len includes closing token
        )
        # check that first node is math mode node when parsing including the math mode start
        nodes = lw.get_latex_nodes(pos=p, parsing_state=parsing_state)[0]
        parsing_state_inner = nodes[0].nodelist[0].parsing_state # inner "math mode" state
        self.assertEqual(
            nodes[0],
            LatexMathNode(parsing_state=parsing_state,
                          displaytype='display',
                          nodelist=[ LatexCharsNode(parsing_state=parsing_state_inner,
                                                    chars='\n   ax + b = y\n',
                                                    pos=p+2,len=len('\n   ax + b = y\n')), ],
                          delimiters=('$$', '$$'),
                          pos=p,len=len('$$\n   ax + b = y\n$$'))
        )


        p = latextext.find(r'\[')
        superscript_arguments_spec_list = \
            parsing_state.latex_context.get_specials_spec('^').arguments_spec_list
        good_parsed_structure = lambda parsing_state, ps2, ps3: [
            LatexCharsNode(parsing_state=parsing_state,
                           chars=' cx',
                           pos=p+2,len=5-2),
            # '^' picks up the single following token as its argument
            LatexSpecialsNode(parsing_state=parsing_state,
                              specials_chars='^',
                              nodeargd=macrospec.ParsedMacroArgs(
                                  arguments_spec_list=superscript_arguments_spec_list,
                                  argnlist=[
                                  LatexCharsNode(parsing_state=parsing_state,
                                                 chars='2',
                                                 pos=p+6,len=1)
                              ]),
                              pos=p+5,len=7-5),
            LatexCharsNode(parsing_state=parsing_state,
                           chars='+z=-d',
                           pos=p+7,len=12-7),
            LatexMacroNode(parsing_state=parsing_state,
                           macroname='quad',
                           pos=p+12,len=17-12),
            LatexMacroNode(parsing_state=parsing_state,
                           macroname='text',
                           nodeargd=macrospec.ParsedMacroArgs(argspec='{', argnlist=[
                               LatexGroupNode(
                                   parsing_state=ps2,
                                   delimiters=('{', '}'),
                                   nodelist=[
                                       LatexCharsNode(parsing_state=ps2,
                                                      chars='if ',
                                                      pos=p+23,len=26-23),
                                       LatexMathNode(parsing_state=ps2,
                                                     displaytype='inline', nodelist=[
                                                         LatexCharsNode(parsing_state=ps3,
                                                                        chars='x<0',
                                                                        pos=p+27,len=3)
                                                     ],
                                                     delimiters=('$','$'),
                                                     pos=p+26,len=31-26)
                                   ],
                                   pos=p+22,len=32-22)
                           ]),
                           pos=p+17,len=32-17),
            LatexCharsNode(parsing_state=parsing_state,
                           chars=' ',
                           pos=p+32,len=1),
        ]
        nodes, pos, len_ = lw.get_latex_nodes(pos=p+2, stop_upon_closing_mathmode=r'\]',
                                              parsing_state=parsing_state_math)
        parsing_state2 = nodes[4].nodeargd.argnlist[0].parsing_state # "inner text mode" state
        parsing_state3 = nodes[4].nodeargd.argnlist[0].nodelist[1].nodelist[0].parsing_state
        self.assertFalse(parsing_state2.in_math_mode)
        self.assertTrue(parsing_state3.in_math_mode)
        self.assertEqual(
            (nodes, pos, len_),
            ( good_parsed_structure(parsing_state_math, parsing_state2, parsing_state3) ,
              p+2, latextext.find(r'\]', p+2) - (p+2) + 2 ) # len includes closing token
        )
        # check that first node is math mode node when parsing including the math mode start
        nodes = lw.get_latex_nodes(pos=p, parsing_state=parsing_state)[0]
        parsing_state1 = nodes[0].nodelist[0].parsing_state
        parsing_state2 = nodes[0].nodelist[4].nodeargd.argnlist[0].parsing_state
        parsing_state3 = nodes[0].nodelist[4].nodeargd.argnlist[0].nodelist[1].nodelist[0].parsing_state
        self.assertEqual(
            nodes[0],
            LatexMathNode(parsing_state=parsing_state,
                          displaytype='display',
                          nodelist=good_parsed_structure(parsing_state1, parsing_state2,
                                                         parsing_state3),
                          delimiters=(r'\[', r'\]'),
                          pos=p,len=latextext.find(r'\]', p+2) + 2 - p)
        )

        p = latextext.find(r'\(')
        good_parsed_structure = lambda ps1, ps2a, ps2b, ps3: [
            LatexMacroNode(
                parsing_state=ps1,
                macroname='mbox',
                nodeargd=macrospec.ParsedMacroArgs(argspec='{', argnlist=[
                    LatexGroupNode(parsing_state=ps2a,
                                   delimiters=('{', '}'),
                                   nodelist=[
                                       LatexCharsNode(parsing_state=ps2a,
                                                      chars='Prob',
                                                      pos=p-29+37,len=41-37)
                                   ],
                                   pos=p-29+36,len=42-36),
                ]),
                pos=p-29+31,len=42-31),
            LatexCharsNode(parsing_state=ps1,
                           chars='(',
                           pos=p-29+42,len=1),
            LatexMacroNode(
                parsing_state=ps1,
                macroname='mbox',
                nodeargd=macrospec.ParsedMacroArgs(argspec='{', argnlist=[
                    LatexGroupNode(
                        parsing_state=ps2b,
                        delimiters=('{', '}'),
                        nodelist=[
                            LatexCharsNode(parsing_state=ps2b,
                                           chars='some event if ',
                                           pos=p-29+49,len=63-49),
                            LatexMathNode(parsing_state=ps2b,
                                          displaytype='inline',
                                          nodelist=[
                                              LatexCharsNode(parsing_state=ps3,
                                                             chars='x>0',
                                                             pos=p-29+65,len=3)
                                          ],
                                          delimiters=(r'\(', r'\)'),
                                          pos=p-29+63,len=70-63),
                        ],
                        pos=p-29+48,len=71-48)
                ]),
                pos=p-29+43,len=71-43),
            LatexCharsNode(parsing_state=ps1,
                           chars=')=1',
                           pos=p-29+71,len=3),
        ]
        nodes, pos, len_ = lw.get_latex_nodes(pos=p+2, stop_upon_closing_mathmode=r'\)',
                                              parsing_state=parsing_state_math)
        ps2a = nodes[0].nodeargd.argnlist[0].parsing_state
        self.assertFalse(ps2a.in_math_mode)
        ps2b = nodes[2].nodeargd.argnlist[0].parsing_state
        self.assertFalse(ps2b.in_math_mode)
        ps3 = nodes[2].nodeargd.argnlist[0].nodelist[1].nodelist[0].parsing_state
        self.assertTrue(ps3.in_math_mode)
        self.assertEqual(
            ( nodes, pos, len_ ),
            ( good_parsed_structure(parsing_state_math, ps2a, ps2b, ps3),
              p+2, latextext.rfind(r'\)') - (p+2) + 2 ) # len includes closing token
        )
        # artificially parse expression in text mode to see that \mbox{} copies
        # the state object instead of creating a new one
        nodes, pos, len_ = lw.get_latex_nodes(pos=p+2, stop_upon_closing_mathmode=r'\)',
                                              parsing_state=parsing_state)
        ps2a = nodes[0].nodeargd.argnlist[0].parsing_state
        self.assertFalse(ps2a.in_math_mode)
        ps2b = nodes[2].nodeargd.argnlist[0].parsing_state
        self.assertFalse(ps2b.in_math_mode)
        ps3 = nodes[2].nodeargd.argnlist[0].nodelist[1].nodelist[0].parsing_state
        self.assertTrue(ps3.in_math_mode)
        self.assertEqual(
            ( nodes, pos, len_ ),
            ( good_parsed_structure(parsing_state, ps2a, ps2b, ps3),
              p+2, latextext.rfind(r'\)') - (p+2) + 2 ) # len includes closing token
        )
        # check that first node is math mode node when parsing including the math mode start
        nodes, _, _ = lw.get_latex_nodes(pos=p, parsing_state=parsing_state)
        ps1 = nodes[0].nodelist[0].parsing_state
        ps2a = nodes[0].nodelist[0].nodeargd.argnlist[0].parsing_state
        self.assertFalse(ps2a.in_math_mode)
        ps2b = nodes[0].nodelist[2].nodeargd.argnlist[0].parsing_state
        self.assertFalse(ps2b.in_math_mode)
        ps3 = nodes[0].nodelist[2].nodeargd.argnlist[0].nodelist[1].nodelist[0].parsing_state
        self.assertTrue(ps3.in_math_mode)
        self.assertEqual(
            nodes[0],
            LatexMathNode(parsing_state=parsing_state,
                          displaytype='inline',
                          nodelist=good_parsed_structure(ps1, ps2a, ps2b, ps3),
                          delimiters=(r'\(', r'\)'),
                          pos=p, len=latextext.rfind(r'\)') + 2 - p)
        )



    def test_get_latex_nodes_mathmodes_dollardollar(self):

        # pos counter:  |0        |10       |20       |30     |38
        latextext = r"""x$\dagger$$\dagger$""" #$$A=B\mbox{$b=a$}$$"""

        lw = LatexWalker(latextext, tolerant_parsing=False)
        parsing_state = lw.make_parsing_state()

        nodes = lw.get_latex_nodes(parsing_state=parsing_state)[0]
        ps1 = nodes[1].nodelist[0].parsing_state
        ps2 = nodes[2].nodelist[0].parsing_state

        self.assertEqual(
            nodes,
            [
                LatexCharsNode(parsing_state=parsing_state,
                               chars=r'x',
                               pos=0,
                               len=1),
                LatexMathNode(parsing_state=parsing_state,
                              displaytype='inline',
                              delimiters=(r'$', r'$'),
                              nodelist=[
                                  LatexMacroNode(
                                      parsing_state=ps1,
                                      macroname='dagger',
                                      nodeargd=macrospec.ParsedMacroArgs(),
                                      pos=2,
                                      len=9-2,
                                  ),
                              ],
                              pos=1,
                              len=10-1),
                LatexMathNode(parsing_state=parsing_state,
                              displaytype='inline',
                              delimiters=(r'$', r'$'),
                              nodelist=[
                                  LatexMacroNode(
                                      parsing_state=ps2,
                                      macroname='dagger',
                                      nodeargd=macrospec.ParsedMacroArgs(),
                                      pos=11,
                                      len=18-11,
                                  ),
                              ],
                              pos=10,
                              len=19-10),
            ])


    def test_get_latex_nodes_comments(self):

        latextext = r'''
Hello % comment here
  % more comments 

New paragraph here.
% comment at end'''.lstrip()

        lw = LatexWalker(latextext, tolerant_parsing=True)
        parsing_state = lw.make_parsing_state()

        self.assertEqual(
            lw.get_latex_nodes(pos=0, parsing_state=parsing_state),
            ([
                LatexCharsNode(parsing_state=parsing_state,
                               chars='Hello ',
                               pos=0, len=6),
                LatexCommentNode(parsing_state=parsing_state,
                                 comment=' comment here',
                                 comment_post_space='\n  ',
                                 pos=6, len=20-6+1+2),
                LatexCommentNode(parsing_state=parsing_state,
                                 comment=' more comments ',
                                 comment_post_space='',
                                 pos=21+2, len=18-2),
                LatexSpecialsNode(parsing_state=parsing_state,
                                  specials_chars='\n\n',
                                  nodeargd=macrospec.ParsedMacroArgs(),
                                  pos=21+18, len=2),
                LatexCharsNode(parsing_state=parsing_state,
                               chars='New paragraph here.\n',
                               pos=21+20, len=19+1),
                LatexCommentNode(parsing_state=parsing_state,
                                 comment=' comment at end',
                                 comment_post_space='',
                                 pos=21+18+2+20, len=16),
             ],
             0,len(latextext))
        )

        latextext = r"""
Line with % a comment here

% line comment on its own
% and a second line

Also a \itshape% comment after a macro
% and also a second line
some italic text.""".lstrip()
        
        lw = LatexWalker(latextext, tolerant_parsing=True)
        parsing_state = lw.make_parsing_state()

        self.assertEqual(
            lw.get_latex_nodes(pos=0, parsing_state=parsing_state),
            ([
                LatexCharsNode(parsing_state=parsing_state,
                               chars='Line with ',
                               pos=0, len=10),
                LatexCommentNode(parsing_state=parsing_state,
                                 comment=' a comment here',
                                 comment_post_space='',
                                 pos=10, len=26-10),
                LatexSpecialsNode(parsing_state=parsing_state,
                                  specials_chars='\n\n',
                                  nodeargd=macrospec.ParsedMacroArgs(),
                                  pos=26, len=2),
                # LatexCharsNode(parsing_state=parsing_state,
                #                chars='\n\n',
                #                pos=26, len=2),
                LatexCommentNode(parsing_state=parsing_state,
                                 comment=' line comment on its own',
                                 comment_post_space='\n',
                                 pos=27+1, len=25+1),
                LatexCommentNode(parsing_state=parsing_state,
                                 comment=' and a second line',
                                 comment_post_space='',
                                 pos=27+1+26, len=19),
                LatexSpecialsNode(parsing_state=parsing_state,
                                  specials_chars='\n\n',
                                  nodeargd=macrospec.ParsedMacroArgs(),
                                  pos=27+1+26+19, len=2),
                LatexCharsNode(parsing_state=parsing_state,
                               chars='Also a ',
                               pos=27+1+26+19+2, len=7),
                LatexMacroNode(parsing_state=parsing_state,
                               macroname=r'itshape',
                               macro_post_space='',
                               nodeargd=macrospec.ParsedMacroArgs(argspec='',argnlist=[]),
                               pos=27+1+26+20+1+7, len=15-7),
                LatexCommentNode(parsing_state=parsing_state,
                                 comment=' comment after a macro',
                                 comment_post_space='\n',
                                 pos=27+1+26+20+1+15, len=39-15),
                LatexCommentNode(parsing_state=parsing_state,
                                 comment=' and also a second line',
                                 comment_post_space='\n',
                                 pos=27+1+26+20+1+39, len=25),
                LatexCharsNode(parsing_state=parsing_state,
                               chars='some italic text.',
                               pos=27+1+26+20+1+39+25, len=17),

             ],
             0,len(latextext))
        )


    def test_get_latex_nodes_read_max_nodes(self):

        latextext = r'''Text and \`accent and \textbf{bold text} and $\vec b$ more stuff for Fran\c cois
\begin{enumerate}[(i)]
\item Hi there!  % here goes a comment
\item[a] Hello!  @@@
     \end{enumerate}
Indeed thanks to \cite[Lemma 3]{Author}, we know that...
Also: {\itshape some italic text}.
'''
        lw = LatexWalker(latextext, tolerant_parsing=False)
        parsing_state = lw.make_parsing_state()

        p = 0
        self.assertEqual(
            lw.get_latex_nodes(pos=p, read_max_nodes=1, parsing_state=parsing_state),
            ([
                LatexCharsNode(parsing_state=parsing_state,
                               chars='Text and ',
                               pos=p, len=33-24),
            ], p, 33-24))

        p = latextext.find(r'ent and ') + 4 # points on second "and" on first line
        nodes, pos, len_ = lw.get_latex_nodes(pos=p, read_max_nodes=5,
                                              parsing_state=parsing_state)
        # inner state -- math mode -- get this
        parsing_state_innertextbf = nodes[1].nodeargd.argnlist[0].parsing_state
        parsing_state_innermath = nodes[3].nodelist[0].parsing_state
        self.assertFalse(parsing_state_innertextbf.in_math_mode)
        self.assertTrue(parsing_state_innermath.in_math_mode)
        self.assertEqual(
            (nodes, pos, len_),
            ([
                LatexCharsNode(parsing_state=parsing_state,
                               chars='and ',
                               pos=p, len=4),
                LatexMacroNode(parsing_state=parsing_state,
                               macroname='textbf',
                               nodeargd=macrospec.ParsedMacroArgs(argspec='{', argnlist=[
                                   LatexGroupNode(parsing_state=parsing_state_innertextbf,
                                                  delimiters=('{', '}'),
                                                  nodelist=[
                                                      LatexCharsNode(parsing_state=parsing_state_innertextbf,
                                                                     chars='bold text',
                                                                     pos=p+54-42, len=9)
                                                  ],
                                                  pos=p+53-42, len=11)
                               ]),
                               pos=p+46-42, len=64-46),
                LatexCharsNode(parsing_state=parsing_state,
                               chars=' and ',
                               pos=p+64-42, len=69-64),
                LatexMathNode(parsing_state=parsing_state,
                              displaytype='inline',
                              delimiters=('$', '$'),
                              nodelist=[
                                  LatexMacroNode(parsing_state=parsing_state_innermath,
                                                 macroname='vec',
                                                 macro_post_space=' ',
                                                 nodeargd=macrospec.ParsedMacroArgs(argspec='{', argnlist=[
                                                     LatexCharsNode(parsing_state=parsing_state_innermath,
                                                                    chars='b',
                                                                    pos=p+75-42, len=1)
                                                 ]),
                                                 pos=p+70-42, len=76-70),
                              ],
                              pos=p+69-42, len=77-69),
                LatexCharsNode(parsing_state=parsing_state,
                               chars=' more stuff for Fran',
                               pos=p+77-42, len=97-77),
            ], p, 97-42))


        
    def test_errors(self):
        latextext = get_test_latex_data_with_possible_inconsistencies()
        
        lw = LatexWalker(latextext, tolerant_parsing=False)
        with self.assertRaises(LatexWalkerParseError):
            dummy = lw.get_latex_nodes()

        lwOk = LatexWalker(latextext, tolerant_parsing=True)
        # make sure that it goes through without raising:
        try:
            lwOk.get_latex_nodes()
        except LatexWalkerParseError as e:
            # should not raise this.
            self.fail("get_latex_nodes() raised LatexWalkerParseError, but it shouldn't have in "
                      "tolerant parsing mode!\n"+str(e))
            
    

    def test_verbatim(self):

        latextext = r"""Use the environment \verb+\begin{verbatim}...\end{verbatim}+ to
\begin{verbatim}
typeset \verbatim text with \LaTeX $ escapes \(like this\).
\end{verbatim}
This is it."""

        lw = LatexWalker(latextext)

        parsing_state = lw.make_parsing_state()

        p=0
        nodelist, npos, nlen = lw.get_latex_nodes(pos=p, parsing_state=parsing_state)

        self.assertEqual((npos, nlen), (0, 167))
        self.assertEqual(len(nodelist), 5)

        self.assertEqual(nodelist[0].chars, 'Use the environment ')
        self.assertEqual((nodelist[0].pos, nodelist[0].pos_end), (0, 20))

        #
        # BEHAVIOR CHANGE vs pylatexenc 2 — the shape asserted below is *not*
        # the one pylatexenc 2 produced.
        #
        # Pylatexenc 2 exposed the verbatim content of ‘\verb’ as a chars node
        # placed directly at `nodeargd.argnlist[0]`, and carried the delimiters
        # on the parsed-arguments object (a `ParsedVerbatimArgs` instance).
        # Pylatexenc 3 parses the argument with
        # :py:class:`~pylatexenc.latexnodes.parsers.LatexDelimitedVerbatimParser`,
        # which reports a group node whose `delimiters` are the verbatim
        # delimiters and whose single child is the chars node; `nodeargd` is now
        # an ordinary `ParsedArguments` instance.
        #
        # Code written against pylatexenc 2 that read `verbatim_text` and
        # `verbatim_delimiters` keeps working — those attributes are still set,
        # see the two assertions at the end of this block — but code that
        # reached into `argnlist[0]` expecting a chars node needs updating.
        #
        self.assertEqual(nodelist[1].macroname, 'verb')
        self.assertEqual((nodelist[1].pos, nodelist[1].pos_end), (20, 60))
        verbgroup = nodelist[1].nodeargd.argnlist[0]
        self.assertEqual(verbgroup.delimiters, ('+', '+'))
        self.assertEqual(verbgroup.nodelist[0].chars,
                         '\\begin{verbatim}...\\end{verbatim}')
        self.assertEqual((verbgroup.nodelist[0].pos, verbgroup.nodelist[0].pos_end),
                         (26, 59))
        self.assertEqual(nodelist[1].nodeargd.verbatim_text,
                         '\\begin{verbatim}...\\end{verbatim}')
        self.assertEqual(nodelist[1].nodeargd.verbatim_delimiters, ('+', '+'))

        self.assertEqual(nodelist[2].chars, ' to\n')

        # the contents of the verbatim environment are its body
        self.assertEqual(nodelist[3].environmentname, 'verbatim')
        self.assertEqual((nodelist[3].pos, nodelist[3].pos_end), (64, 155))
        #
        # BEHAVIOR CHANGE vs pylatexenc 2 — the expected value below had to be
        # updated, it is *not* what pylatexenc 2 produced.
        #
        # Pylatexenc 2 reported the newline that immediately follows
        # ‘\begin{verbatim}’ as part of the verbatim contents, i.e. it expected
        # '\ntypeset \\verbatim text with ...'.  Pylatexenc 3 gobbles that first
        # newline, mirroring what LaTeX itself does, so the leading '\n' is
        # gone.  Everything else about this construct is unchanged.
        #
        self.assertEqual(
            nodelist[3].nodelist[0].chars,
            'typeset \\verbatim text with \\LaTeX $ escapes \\(like this\\).\n'
        )
        self.assertEqual(
            nodelist[3].nodeargd.verbatim_text,
            'typeset \\verbatim text with \\LaTeX $ escapes \\(like this\\).\n'
        )
        self.assertIsNone(nodelist[3].nodeargd.verbatim_delimiters)

        self.assertEqual(nodelist[4].chars, '\nThis is it.')

    #
    # The following tests pin down the behavior of the verbatim constructs of
    # the default latex context (‘\verb’, the ‘verbatim’ environment and the
    # ‘lstlisting’ environment), independently of which argument parser
    # implements them.  They are meant to keep the observable behavior stable if
    # the underlying parser implementation is changed.
    #

    def _verb_arg_group(self, node):
        # The verbatim argument of ‘\verb’ is a group node whose delimiters are
        # the verbatim delimiters and whose single child is a chars node with
        # the verbatim content.
        self.assertEqual(len(node.nodeargd.argnlist), 1)
        groupnode = node.nodeargd.argnlist[0]
        self.assertEqual(len(groupnode.nodelist), 1)
        return groupnode

    def assertVerbatimContent(self, node, verbatim_text, verbatim_delimiters):
        # The verbatim content of a ‘\verb’ call must be reachable in two ways:
        # through the argument group node, and through the `verbatim_text` and
        # `verbatim_delimiters` attributes that ‘pylatexenc 2’ provided on the
        # parsed-arguments object.
        groupnode = self._verb_arg_group(node)
        self.assertEqual(groupnode.nodelist[0].chars, verbatim_text)
        self.assertEqual(groupnode.delimiters, verbatim_delimiters)

        self.assertEqual(node.nodeargd.verbatim_text, verbatim_text)
        self.assertEqual(node.nodeargd.verbatim_delimiters, verbatim_delimiters)

    def test_verbatim_verb_delimiters(self):
        # \verb uses the first non-whitespace character that follows as its
        # delimiter, whichever character that is.
        for delimiter in ['+', '|', '!', '#', '"', ';', '/', '=']:
            latextext = '\\verb' + delimiter + 'foo bar' + delimiter

            lw = LatexWalker(latextext, tolerant_parsing=False)
            nodelist, p, l = lw.get_latex_nodes(pos=0)

            self.assertEqual(len(nodelist), 1)
            n = nodelist[0]
            self.assertEqual(n.macroname, 'verb')
            self.assertVerbatimContent(n, 'foo bar', (delimiter, delimiter))
            self.assertEqual(n.pos, 0)
            self.assertEqual(n.pos_end, len(latextext))
            # the node covers the delimiters, too
            self.assertEqual(n.latex_verbatim(), latextext)

    def test_verbatim_verb_contents_are_not_interpreted(self):
        # macros, braces, dollar signs and comment characters in the verbatim
        # content must be reported as they appear in the source
        latextext = r'''\verb!a\b{c}$d%e!'''

        lw = LatexWalker(latextext, tolerant_parsing=False)
        nodelist, p, l = lw.get_latex_nodes(pos=0)

        self.assertEqual(len(nodelist), 1)
        self.assertVerbatimContent(nodelist[0], 'a\\b{c}$d%e', ('!', '!'))

    def test_verbatim_verb_post_space(self):
        # whitespace between \verb and the delimiter is allowed; it is recorded
        # as the macro's post-space and is not part of the verbatim content
        latextext = r'''\verb  +spaced+'''

        lw = LatexWalker(latextext, tolerant_parsing=False)
        nodelist, p, l = lw.get_latex_nodes(pos=0)

        self.assertEqual(len(nodelist), 1)
        n = nodelist[0]
        self.assertEqual(n.macro_post_space, '  ')
        self.assertVerbatimContent(n, 'spaced', ('+', '+'))
        self.assertEqual(n.pos_end, len(latextext))

    def test_verbatim_verb_empty_content(self):
        latextext = r'''\verb++'''

        lw = LatexWalker(latextext, tolerant_parsing=False)
        nodelist, p, l = lw.get_latex_nodes(pos=0)

        self.assertEqual(len(nodelist), 1)
        self.assertVerbatimContent(nodelist[0], '', ('+', '+'))
        self.assertEqual(nodelist[0].pos_end, len(latextext))

    def test_verbatim_verb_in_surrounding_text(self):
        # parsing must resume immediately after the closing delimiter
        latextext = r'''a\verb+x+b'''

        lw = LatexWalker(latextext, tolerant_parsing=False)
        nodelist, p, l = lw.get_latex_nodes(pos=0)

        self.assertEqual(len(nodelist), 3)
        self.assertEqual(nodelist[0].chars, 'a')
        self.assertVerbatimContent(nodelist[1], 'x', ('+', '+'))
        self.assertEqual(nodelist[2].chars, 'b')

    def test_verbatim_environment_contents(self):
        latextext = '\\begin{verbatim}\nline1\nline2\n\\end{verbatim}'

        lw = LatexWalker(latextext, tolerant_parsing=False)
        nodelist, p, l = lw.get_latex_nodes(pos=0)

        self.assertEqual(len(nodelist), 1)
        n = nodelist[0]
        self.assertEqual(n.environmentname, 'verbatim')
        #
        # BEHAVIOR CHANGE vs pylatexenc 2 — the expected values below are *not*
        # what pylatexenc 2 produced.
        #
        # Pylatexenc 2 reported the newline that immediately follows
        # ‘\begin{verbatim}’ as part of the verbatim contents, i.e.
        # '\nline1\nline2\n'.  Pylatexenc 3 gobbles that first newline,
        # mirroring what LaTeX itself does.
        #
        # The verbatim content is the environment body, and is also reachable
        # the way ‘pylatexenc 2’ provided it, through `verbatim_text`.
        #
        self.assertEqual(len(n.nodelist), 1)
        self.assertEqual(n.nodelist[0].chars, 'line1\nline2\n')
        self.assertEqual(n.nodeargd.verbatim_text, 'line1\nline2\n')
        self.assertIsNone(n.nodeargd.verbatim_delimiters)
        self.assertEqual(n.pos, 0)
        self.assertEqual(n.pos_end, len(latextext))
        self.assertEqual(n.latex_verbatim(), latextext)

    def test_verbatim_environment_empty(self):
        latextext = '\\begin{verbatim}\\end{verbatim}'

        lw = LatexWalker(latextext, tolerant_parsing=False)
        nodelist, p, l = lw.get_latex_nodes(pos=0)

        self.assertEqual(len(nodelist), 1)
        self.assertEqual(nodelist[0].nodelist[0].chars, '')
        self.assertEqual(nodelist[0].nodeargd.verbatim_text, '')
        self.assertEqual(nodelist[0].pos_end, len(latextext))

    def test_verbatim_lstlisting_contents(self):
        latextext = '\\begin{lstlisting}\ncode\n\\end{lstlisting}'

        lw = LatexWalker(latextext, tolerant_parsing=False)
        nodelist, p, l = lw.get_latex_nodes(pos=0)

        self.assertEqual(len(nodelist), 1)
        n = nodelist[0]
        self.assertEqual(n.environmentname, 'lstlisting')
        #
        # BEHAVIOR CHANGE vs pylatexenc 2 — the expected values below are *not*
        # what pylatexenc 2 produced.
        #
        # Pylatexenc 2 reported the newline that immediately follows
        # ‘\begin{lstlisting}’ as part of the contents, i.e. '\ncode\n'.
        # Pylatexenc 3 gobbles that first newline, mirroring what LaTeX itself
        # does.
        #
        # The contents are the environment body, and are also reachable through
        # the attributes that ‘pylatexenc 2’ provided.
        #
        self.assertEqual(n.nodelist[0].chars, 'code\n')
        self.assertEqual(n.nodeargd.verbatim_text, 'code\n')
        self.assertEqual(n.nodeargd.lstlisting_text, 'code\n')
        self.assertIsNone(n.nodeargd.verbatim_delimiters)
        self.assertEqual(n.pos_end, len(latextext))

    def test_verbatim_lstlisting_with_optional_argument(self):
        latextext = '\\begin{lstlisting}[language=Python]\ncode\n\\end{lstlisting}'

        lw = LatexWalker(latextext, tolerant_parsing=False)
        nodelist, p, l = lw.get_latex_nodes(pos=0)

        self.assertEqual(len(nodelist), 1)
        n = nodelist[0]
        #
        # BEHAVIOR CHANGE vs pylatexenc 2 — the expected values below are *not*
        # what pylatexenc 2 produced.
        #
        # Pylatexenc 2 reported the newline that immediately follows the
        # optional argument as part of the contents, i.e. '\ncode\n'.
        # Pylatexenc 3 gobbles that first newline, mirroring what LaTeX itself
        # does.  The optional argument itself is parsed exactly as before.
        #
        self.assertEqual(n.nodelist[0].chars, 'code\n')
        self.assertEqual(n.nodeargd.verbatim_text, 'code\n')
        self.assertEqual(n.nodeargd.lstlisting_text, 'code\n')
        # the optional argument is parsed as a normal (non-verbatim) argument
        optarg = n.nodeargd.argnlist[0]
        self.assertIsNotNone(optarg)
        self.assertEqual(optarg.latex_verbatim(), '[language=Python]')
        self.assertEqual(n.pos_end, len(latextext))

    def test_verbatim_lstlisting_optional_argument_needs_no_pre_space(self):
        # a ‘[’ that does not immediately follow \begin{lstlisting} is part of
        # the verbatim contents, and not an optional argument
        for latextext in ['\\begin{lstlisting}\n[nope]\n\\end{lstlisting}',
                          '\\begin{lstlisting} [nope]\n\\end{lstlisting}']:
            lw = LatexWalker(latextext, tolerant_parsing=False)
            nodelist, p, l = lw.get_latex_nodes(pos=0)

            self.assertEqual(len(nodelist), 1)
            n = nodelist[0]
            self.assertIsNone(n.nodeargd.argnlist[0])
            self.assertIn('[nope]', n.nodeargd.verbatim_text)
            self.assertEqual(n.pos_end, len(latextext))

    def test_verbatim_lstlisting_empty(self):
        latextext = '\\begin{lstlisting}\\end{lstlisting}'

        lw = LatexWalker(latextext, tolerant_parsing=False)
        nodelist, p, l = lw.get_latex_nodes(pos=0)

        self.assertEqual(len(nodelist), 1)
        self.assertEqual(nodelist[0].nodeargd.verbatim_text, '')
        self.assertEqual(nodelist[0].pos_end, len(latextext))

    def test_verbatim_unterminated_lstlisting_raises(self):
        latextext = '\\begin{lstlisting}\ncode'

        lw = LatexWalker(latextext, tolerant_parsing=False)
        with self.assertRaises(LatexWalkerParseError):
            lw.get_latex_nodes(pos=0)

    def test_verbatim_unterminated_lstlisting_tolerant(self):
        latextext = '\\begin{lstlisting}\ncode'

        lw = LatexWalker(latextext, tolerant_parsing=True)
        nodelist, p, l = lw.get_latex_nodes(pos=0)

        self.assertEqual(len(nodelist), 1)
        self.assertEqual(nodelist[0].environmentname, 'lstlisting')
        #
        # BEHAVIOR CHANGE vs pylatexenc 2 — the expected values below are *not*
        # what pylatexenc 2 produced.  Two changes meet here:
        #
        #  - the first newline is gobbled, as it is for a well-terminated
        #    environment, so the recovered contents are 'code' and not '\ncode';
        #
        #  - `nodeargd` used to be `None` on an unterminated ‘lstlisting’, so
        #    `verbatim_text` was not reachable at all.  It is now populated from
        #    the contents that could be read before the end of the stream.
        #
        # the content that could be read is recovered as the environment body
        self.assertEqual(nodelist[0].nodelist[0].chars, 'code')
        self.assertEqual(nodelist[0].nodeargd.verbatim_text, 'code')

    def test_verbatim_unterminated_verb_raises(self):
        latextext = r'''\verb+unterminated'''

        lw = LatexWalker(latextext, tolerant_parsing=False)
        with self.assertRaises(LatexWalkerParseError):
            lw.get_latex_nodes(pos=0)

    def test_verbatim_unterminated_environment_raises(self):
        latextext = '\\begin{verbatim}unterminated'

        lw = LatexWalker(latextext, tolerant_parsing=False)
        with self.assertRaises(LatexWalkerParseError):
            lw.get_latex_nodes(pos=0)

    def test_verbatim_unterminated_verb_tolerant(self):
        # in tolerant parsing mode we still get a \verb macro node, and parsing
        # continues instead of raising.  The recovered argument has the same
        # shape as a successfully parsed one, so both ways of reaching the
        # verbatim content work here as well.
        latextext = r'''\verb+unterminated'''

        lw = LatexWalker(latextext, tolerant_parsing=True)
        nodelist, p, l = lw.get_latex_nodes(pos=0)

        self.assertTrue(len(nodelist) >= 1)
        self.assertEqual(nodelist[0].macroname, 'verb')
        self.assertVerbatimContent(nodelist[0], 'unterminated', ('+', '+'))

    def test_verbatim_unterminated_environment_tolerant(self):
        latextext = '\\begin{verbatim}unterminated'

        lw = LatexWalker(latextext, tolerant_parsing=True)
        nodelist, p, l = lw.get_latex_nodes(pos=0)

        self.assertEqual(len(nodelist), 1)
        self.assertEqual(nodelist[0].environmentname, 'verbatim')
        # the content that could be read is recovered as the environment body
        self.assertEqual(nodelist[0].nodelist[0].chars, 'unterminated')
        self.assertEqual(nodelist[0].nodeargd.verbatim_text, 'unterminated')

    def test_verbatim_verb_opening_brace_delimiter(self):
        # ‘{’ is auto-matched with ‘}’, so the content of ‘\verb{...}’ ends at
        # the closing brace.  (LaTeX itself would instead look for a second ‘{’.)
        latextext = r'''\verb{braced}'''

        lw = LatexWalker(latextext, tolerant_parsing=False)
        nodelist, p, l = lw.get_latex_nodes(pos=0)

        self.assertEqual(len(nodelist), 1)
        self.assertVerbatimContent(nodelist[0], 'braced', ('{', '}'))
        self.assertEqual(nodelist[0].pos_end, len(latextext))

    def test_verbatim_verb_at_end_of_stream(self):
        # a ‘\verb’ with nothing at all following it must not blow up; there is
        # no verbatim content to report in that case
        latextext = r'''\verb'''

        for tolerant in [False, True]:
            lw = LatexWalker(latextext, tolerant_parsing=tolerant)
            nodelist, p, l = lw.get_latex_nodes(pos=0)
            self.assertEqual(len(nodelist), 1)
            self.assertEqual(nodelist[0].macroname, 'verb')
            self.assertIsNone(nodelist[0].nodeargd.verbatim_text)
            self.assertIsNone(nodelist[0].nodeargd.verbatim_delimiters)

    def test_verbatim_via_specials(self):

        latextext = r"""
Use the |\verb| command or the
|\begin{verbatim}| ... |\end{verbatim}| environment
to typeset verbatim text!

Syntax errors within verbatim content, such as |{|, should
not cause processing problems.
"""

        walker_context = get_default_latex_context_db()
        walker_context.add_context_category(
            'specials-verbatim',
            specials=[
                macrospec.SpecialsSpec('|', args_parser=macrospec.VerbatimArgsParser(
                    verbatim_arg_type='specials-delimiters',
                    specials_delimiters=('|', '|'),
                )),
            ],
            prepend=True
        )

        lw = LatexWalker(latextext, latex_context=walker_context)

        parsing_state = lw.make_parsing_state()

        p=0
        self.assertEqual(
            lw.get_latex_nodes(pos=p, parsing_state=parsing_state),
            ([
                LatexCharsNode(parsing_state=parsing_state, pos=0, len=1+8,
                               chars='\nUse the '),
                LatexSpecialsNode(
                    parsing_state=parsing_state, pos=1+8, len=15-8,
                    specials_chars='|',
                    nodeargd=macrospec.ParsedVerbatimArgs(
                        verbatim_chars_node=
                        LatexCharsNode(parsing_state=parsing_state, pos=1+9, len=14-9,
                                       chars='\\verb'),
                        verbatim_delimiters=('|', '|'),
                    )
                ),
                LatexCharsNode(parsing_state=parsing_state, pos=1+15, len=(30-15)+1,
                               chars=' command or the\n'),
                LatexSpecialsNode(
                    parsing_state=parsing_state, pos=1+31, len=18-0,
                    specials_chars='|',
                    nodeargd=macrospec.ParsedVerbatimArgs(
                        verbatim_chars_node=
                        LatexCharsNode(parsing_state=parsing_state, pos=1+31+1, len=17-1,
                                       chars='\\begin{verbatim}'),
                        verbatim_delimiters=('|', '|'),
                    )
                ),
                LatexCharsNode(parsing_state=parsing_state, pos=1+31+18, len=23-18,
                               chars=' ... '),
                LatexSpecialsNode(
                    parsing_state=parsing_state, pos=1+31+23, len=39-23,
                    specials_chars='|',
                    nodeargd=macrospec.ParsedVerbatimArgs(
                        verbatim_chars_node=
                        LatexCharsNode(parsing_state=parsing_state, pos=1+31+24, len=38-24,
                                       chars='\\end{verbatim}'),
                        verbatim_delimiters=('|', '|'),
                    )
                ),
                LatexCharsNode(parsing_state=parsing_state,
                               pos=1+31+39, len=(52-39)+25,
                               chars=r""" environment
to typeset verbatim text!"""),
                LatexSpecialsNode(parsing_state=parsing_state,
                                  specials_chars='\n\n',
                                  nodeargd=macrospec.ParsedMacroArgs(),
                                  pos=1+31+52+25, len=2),
                LatexCharsNode(parsing_state=parsing_state,
                               pos=1+31+52+26+1, len=47,
                               chars=r"""Syntax errors within verbatim content, such as """),
                LatexSpecialsNode(
                    parsing_state=parsing_state, pos=1+31+52+26+1+47, len=3,
                    specials_chars='|',
                    nodeargd=macrospec.ParsedVerbatimArgs(
                        verbatim_chars_node=
                        LatexCharsNode(parsing_state=parsing_state,
                                       pos=1+31+52+26+1+48, len=1,
                                       chars='{'),
                        verbatim_delimiters=('|', '|'),
                    )
                ),
                LatexCharsNode(parsing_state=parsing_state,
                               pos=1+31+52+26+1+50, len=(59-50)+31,
                               chars=r""", should
not cause processing problems.
"""),
            ],
            0,
            len(latextext),
            )
        )

    def test_lstlisting_handling(self):

        s = r"""Use lstlisting environment for code
\begin{lstlisting}
int foo() {
    "^\\[1-9]+\n$" // some special chars
    // unmatched open brace confuses non-verbatim parsing
\end{lstlisting}
This is it."""

        lw = LatexWalker(s)

        parsing_state = lw.make_parsing_state()

        p=0
        nodelist, npos, nlen = lw.get_latex_nodes(pos=p, parsing_state=parsing_state)

        self.assertEqual((npos, nlen), (0, len(s)))
        self.assertEqual(len(nodelist), 3)

        self.assertEqual(nodelist[0].chars, 'Use lstlisting environment for code\n')

        #
        # BEHAVIOR CHANGE vs pylatexenc 2 — the expected value below had to be
        # updated, it is *not* what pylatexenc 2 produced.
        #
        # Pylatexenc 2 reported the newline that immediately follows
        # ‘\begin{lstlisting}’ as part of the contents, i.e. this string used to
        # start with an empty first line.  Pylatexenc 3 gobbles that first
        # newline, mirroring what LaTeX itself does.  Everything else about this
        # construct is unchanged.
        #
        expected_contents = r"""int foo() {
    "^\\[1-9]+\n$" // some special chars
    // unmatched open brace confuses non-verbatim parsing
"""

        n = nodelist[1]
        self.assertEqual(n.environmentname, 'lstlisting')
        self.assertEqual((n.pos, n.pos_end), ((53-18)+1, s.find(r'\end{lstlisting}')+16))
        self.assertIsNone(n.nodeargd.argnlist[0])
        # the contents are the environment body, and are also reachable through
        # the attributes that ‘pylatexenc 2’ provided
        self.assertEqual(n.nodelist[0].chars, expected_contents)
        self.assertEqual(n.nodeargd.verbatim_text, expected_contents)
        self.assertEqual(n.nodeargd.lstlisting_text, expected_contents)
        self.assertIsNone(n.nodeargd.verbatim_delimiters)

        self.assertEqual(nodelist[2].chars, '\nThis is it.')

    def test_lstlisting_withoptarg(self):

        latextext = r"""Use lstlisting environment for code
\begin{lstlisting}[language=C]
int foo() {
    "^\\[1-9]+\n$" // some special chars
    // unmatched open brace confuses non-verbatim parsing
\end{lstlisting}
This is it."""

        lw = LatexWalker(latextext)

        parsing_state = lw.make_parsing_state()

        #print("DEBUG")
        #print(lw.get_latex_nodes(pos=0, parsing_state=parsing_state)[0][1])

        p=0
        nodelist, npos, nlen = \
            lw.get_latex_nodes(pos=p, parsing_state=parsing_state)

        pssq = nodelist[1].nodeargd.argnlist[0].nodelist[0].parsing_state
        self.assertEqual(set(pssq.latex_group_delimiters),
                         set([ ('{','}'), ('[',']'), ]))

        self.assertEqual((npos, nlen), (0, len(latextext)))
        self.assertEqual(len(nodelist), 3)

        self.assertEqual(nodelist[0].chars, 'Use lstlisting environment for code\n')

        #
        # BEHAVIOR CHANGE vs pylatexenc 2 — the expected value below had to be
        # updated, it is *not* what pylatexenc 2 produced.
        #
        # Pylatexenc 2 reported the newline that immediately follows the
        # ‘[language=C]’ optional argument as part of the contents, i.e. this
        # string used to start with an empty first line.  Pylatexenc 3 gobbles
        # that first newline, mirroring what LaTeX itself does.  The optional
        # argument itself is parsed exactly as before.
        #
        expected_contents = r"""int foo() {
    "^\\[1-9]+\n$" // some special chars
    // unmatched open brace confuses non-verbatim parsing
"""

        n = nodelist[1]
        self.assertEqual(n.environmentname, 'lstlisting')
        self.assertEqual((n.pos, n.pos_end),
                         ((60-24), latextext.find(r'\end{lstlisting}')+16))

        optarg = n.nodeargd.argnlist[0]
        self.assertEqual(optarg.delimiters, ('[', ']'))
        self.assertEqual(optarg.nodelist[0].chars, 'language=C')
        self.assertEqual((optarg.pos, optarg.pos_end), ((60-24)+18, (60-24)+30))

        self.assertEqual(n.nodelist[0].chars, expected_contents)
        self.assertEqual(n.nodeargd.verbatim_text, expected_contents)
        self.assertEqual(n.nodeargd.lstlisting_text, expected_contents)

        self.assertEqual(nodelist[2].chars, '\nThis is it.')







    def test_parsing_state_changes(self):

        class MySimpleNewcommandArgsParser(macrospec.MacroStandardArgsParser):
            def __init__(self):
                super(MySimpleNewcommandArgsParser, self).__init__(
                    argspec='*{[[{',
                    )

            def parse_args(self, w, pos, parsing_state=None, **kwargs):
                (argd, npos, nlen) = super(MySimpleNewcommandArgsParser, self).parse_args(
                    w=w, pos=pos, parsing_state=parsing_state, **kwargs
                )
                if argd.argnlist[1].isNodeType(LatexGroupNode):
                    argd.argnlist[1] = argd.argnlist[1].nodelist[0] # {\command} -> \command
                assert argd.argnlist[1].isNodeType(LatexMacroNode)
                argd.argnlist[1].nodeargd = None # hmmm, we should really have a
                                                 # custom parser here to read a
                                                 # single token
                newcmdname = argd.argnlist[1].macroname
                numargs = int(argd.argnlist[2].nodelist[0].chars) if argd.argnlist[2] else 0
                new_latex_context = parsing_state.latex_context.filter_context()
                new_latex_context.add_context_category(
                    'newcommand-{}'.format(newcmdname),
                    macros=[
                        macrospec.MacroSpec(newcmdname, '{'*numargs)
                    ],
                    prepend=True
                )
                new_parsing_state = parsing_state.sub_context(latex_context=new_latex_context)
                return (argd, npos, nlen, dict(new_parsing_state=new_parsing_state))


        latextext = r"""
\newcommand\a{AAA}
\newcommand{\b}[2]{BBB #1}

Blah blah blah.

Use macros: \a{} and \b{xxx}{yyy}.
""".lstrip()

        latex_context = get_default_latex_context_db()
        latex_context.add_context_category('newcommand-category', prepend=True, macros=[
            macrospec.MacroSpec('newcommand', args_parser=MySimpleNewcommandArgsParser())
        ])

        lw = LatexWalker(latextext, latex_context=latex_context)

        parsing_state = lw.make_parsing_state()

        p=0
        nodes, npos, nlen = lw.get_latex_nodes(pos=p, parsing_state=parsing_state)

        parsing_state_defa = nodes[1].parsing_state
        parsing_state_defab = nodes[3].parsing_state

        parsing_state_defa_sqbr = nodes[2].nodeargd.argnlist[2].parsing_state
        self.assertEqual(set(parsing_state_defa_sqbr.latex_group_delimiters),
                         set([ ('{','}'), ('[',']'), ]))


        self.assertEqual(npos, 0)
        self.assertEqual(nlen, len(latextext))
        self.assertEqual(
            nodes,
            [
                LatexMacroNode(parsing_state=parsing_state, pos=0, len=18,
                               macroname='newcommand',
                               nodeargd=macrospec.ParsedMacroArgs(
                                   argspec='*{[[{',
                                   argnlist=[
                                       None,
                                       LatexMacroNode(
                                           parsing_state=parsing_state,
                                           pos=11, len=2,
                                           macroname='a',
                                           nodeargd=None,
                                       ),
                                       None,
                                       None,
                                       LatexGroupNode(
                                           parsing_state=parsing_state,
                                           pos=13, len=5,
                                           delimiters=('{', '}'),
                                           nodelist=[
                                               LatexCharsNode(
                                                   parsing_state=parsing_state,
                                                   pos=14, len=3,
                                                   chars='AAA'
                                               )
                                           ]
                                       )
                                   ]
                               )),
                LatexCharsNode(parsing_state=parsing_state_defa, pos=18, len=1, chars='\n'),
                LatexMacroNode(parsing_state=parsing_state_defa, pos=19, len=26,
                               macroname='newcommand',
                               nodeargd=macrospec.ParsedMacroArgs(
                                   argspec='*{[[{',
                                   argnlist=[
                                       None,
                                       LatexMacroNode(
                                           parsing_state=parsing_state_defa,
                                           pos=19+12, len=2,
                                           macroname='b',
                                           nodeargd=None,
                                       ),
                                       LatexGroupNode(
                                           parsing_state=parsing_state_defa_sqbr,
                                           pos=19+15, len=3, delimiters=('[', ']'),
                                           nodelist=[
                                               LatexCharsNode(
                                                   parsing_state=parsing_state_defa_sqbr,
                                                   pos=19+16, len=1,
                                                   chars='2'
                                               )
                                           ]
                                       ),
                                       None,
                                       LatexGroupNode(
                                           parsing_state=parsing_state_defa,
                                           pos=19+18, len=8, delimiters=('{', '}'),
                                           nodelist=[
                                               LatexCharsNode(
                                                   parsing_state=parsing_state_defa,
                                                   pos=19+19, len=6,
                                                   chars='BBB #1'
                                               )
                                           ]
                                       )
                                   ]
                               )),
                LatexSpecialsNode(parsing_state=parsing_state_defab,
                                  specials_chars='\n\n',
                                  nodeargd=macrospec.ParsedMacroArgs(),
                                  pos=19+26, len=2),
                LatexCharsNode(parsing_state=parsing_state_defab, pos=19+27+1, len=15,
                               chars=r"""Blah blah blah.""",
                               ),
                LatexSpecialsNode(parsing_state=parsing_state_defab,
                                  specials_chars='\n\n',
                                  nodeargd=macrospec.ParsedMacroArgs(),
                                  pos=19+27+1+15, len=2),
                LatexCharsNode(parsing_state=parsing_state_defab, pos=19+27+1+16+1, len=12,
                               chars=r"""Use macros: """,
                               ),
                LatexMacroNode(parsing_state=parsing_state_defab, pos=19+27+1+16+1+12, len=2,
                               macroname='a',
                               nodeargd=macrospec.ParsedMacroArgs()),
                LatexGroupNode(parsing_state=parsing_state_defab, pos=19+27+1+16+1+12+2, len=2,
                               delimiters=('{', '}'), nodelist=[]),
                LatexCharsNode(parsing_state=parsing_state_defab, pos=19+27+1+16+1+16, len=5,
                               chars=r""" and """),
                LatexMacroNode(parsing_state=parsing_state_defab, pos=19+27+1+16+1+21, len=33-21,
                               macroname='b',
                               nodeargd=macrospec.ParsedMacroArgs(argspec='{{', argnlist=[
                                   LatexGroupNode(
                                       parsing_state=parsing_state_defab,
                                       pos=19+27+1+16+1+23, len=5, delimiters=('{', '}'),
                                       nodelist=[
                                           LatexCharsNode(
                                               parsing_state=parsing_state_defab,
                                               pos=19+27+1+16+1+24, len=3,
                                               chars='xxx'
                                           )
                                       ]),
                                   LatexGroupNode(
                                       parsing_state=parsing_state_defab,
                                       pos=19+27+1+16+1+28, len=5, delimiters=('{', '}'),
                                       nodelist=[
                                           LatexCharsNode(
                                               parsing_state=parsing_state_defab,
                                               pos=19+27+1+16+1+29, len=3,
                                               chars='yyy'
                                           )
                                       ]),
                               ])),
                LatexCharsNode(parsing_state=parsing_state_defab, pos=19+27+1+16+1+33, len=2,
                               chars=".\n"),
            ]
        )




    def test_error_dangling_missing_args_0(self):
        latextext = r'''Test \textbf'''

        lw = LatexWalker(latextext, tolerant_parsing=False)
        parsing_state = lw.make_parsing_state()

        with self.assertRaises(LatexWalkerParseError):
            lw.get_latex_nodes(parsing_state=parsing_state)

    def test_error_dangling_missing_args_1(self):
        latextext = r'''Test \begin{tabular}''' # missing tabular arguments

        lw = LatexWalker(latextext, tolerant_parsing=False)
        parsing_state = lw.make_parsing_state()

        with self.assertRaises(LatexWalkerParseError):
            lw.get_latex_nodes(parsing_state=parsing_state)

    def test_error_dangling_missing_args_2(self):
        latextext = r'''Test _''' # missing underscore arguments

        latex_context = get_default_latex_context_db()
        latex_context.add_context_category('custom-category', prepend=True, specials=[
            macrospec.SpecialsSpec('_', args_parser=macrospec.MacroStandardArgsParser('{'))
        ])

        lw = LatexWalker(latextext, latex_context=latex_context, tolerant_parsing=False)
        parsing_state = lw.make_parsing_state()

        with self.assertRaises(LatexWalkerParseError):
            lw.get_latex_nodes(parsing_state=parsing_state)


#     ### What should be the correct behavior when macro args
#     ### are missing in tolerant parsing mode??
#     def test_error_dangling_missing_args_0b(self):
#         latextext = r'''
# Test \textbf'''.lstrip()
#
#         lw = LatexWalker(latextext, tolerant_parsing=True)
#         parsing_state = lw.make_parsing_state()
#
#         p = 0
#         self.assertEqual(
#             lw.get_latex_nodes(pos=p, parsing_state=parsing_state),
#             ([
#                 LatexCharsNode(parsing_state=parsing_state,
#                                chars='Test ',
#                                pos=p, len=5),
#                 LatexMacroNode(parsing_state=parsing_state,
#                                macroname='textbf',
#                                nodeargd=macrospec.ParsedMacroArgs(),
#                                pos=p+5, len=12-5)
#             ])
#         )



    def test_bug_000(self):
        latextext = r'''
\documentclass[stuff]{docclass}

\begin{document}
% empty document
\end{document}
'''

        lw = LatexWalker(latextext, tolerant_parsing=False)
        parsing_state = lw.make_parsing_state()

        p = 0
        gln_result = \
            lw.get_latex_nodes(pos=p, read_max_nodes=3, parsing_state=parsing_state)
        stuff_parsing_state = gln_result[0][1].nodeargd.argnlist[0].parsing_state
        # the class name is read as plain characters, so its contents have their
        # own parsing state (macros, specials, etc. disabled there)
        docclass_arguments_spec_list = \
            parsing_state.latex_context.get_macro_spec('documentclass').arguments_spec_list
        docclass_parsing_state = \
            gln_result[0][1].nodeargd.argnlist[1].nodelist[0].parsing_state
        self.assertEqual(
            gln_result,
            ([
                LatexCharsNode(parsing_state=parsing_state,
                               chars='\n',
                               pos=0, len=1),
                LatexMacroNode(parsing_state=parsing_state,
                               macroname='documentclass',
                               nodeargd=macrospec.ParsedMacroArgs(
                                   arguments_spec_list=docclass_arguments_spec_list,
                                   argnlist=[
                                   LatexGroupNode(parsing_state=stuff_parsing_state,
                                                  delimiters=('[', ']'),
                                                  nodelist=[
                                                      LatexCharsNode(
                                                          parsing_state=stuff_parsing_state,
                                                          chars='stuff',
                                                          pos=1+15,len=20-15),
                                                  ],
                                                  pos=1+14,len=21-14),
                                   LatexGroupNode(parsing_state=parsing_state,
                                                  delimiters=('{', '}'),
                                                  nodelist=[
                                                      LatexCharsNode(
                                                          parsing_state=docclass_parsing_state,
                                                          chars='docclass',
                                                          pos=1+22,len=30-22
                                                      ),
                                                  ],
                                                  pos=1+21,len=31-21)
                               ]),
                               pos=1+0,len=31),
                LatexSpecialsNode(parsing_state=parsing_state,
                                  specials_chars='\n\n',
                                  nodeargd=macrospec.ParsedMacroArgs(),
                                  pos=1+31, len=2),
                # LatexCharsNode(parsing_state=parsing_state,
                #                chars='\n\n',
                #                pos=1+31, len=2),
            ], p, 34))

    def test_invalid_environment_macros_0(self):
        latextext = r'''\begin \item stuff\end{itemize}'''

        lw = LatexWalker(latextext, tolerant_parsing=False)
        parsing_state = lw.make_parsing_state()

        with self.assertRaises(LatexWalkerParseError):
            lw.get_latex_nodes(parsing_state=parsing_state)

    def test_invalid_environment_macros_1(self):
        latextext = r'''\begin{itemize} \item stuff\end'''

        lw = LatexWalker(latextext, tolerant_parsing=False)
        parsing_state = lw.make_parsing_state()

        with self.assertRaises(LatexWalkerParseError):
            lw.get_latex_nodes(parsing_state=parsing_state)

    def test_invalid_environment_macros_2(self):
        latextext = r'''
\begin
  \item stuff
\end
'''.strip()

        lw = LatexWalker(latextext, tolerant_parsing=True)
        parsing_state = lw.make_parsing_state()

        p = 0
        self.assertEqual(
            lw.get_latex_nodes(pos=p, parsing_state=parsing_state),
            ([
                LatexCharsNode(parsing_state=parsing_state,
                               chars='\\begin\n  ',
                               pos=0, len=9),
                LatexMacroNode(parsing_state=parsing_state,
                               macroname='item',
                               nodeargd=macrospec.ParsedMacroArgs(argspec='[', argnlist=[ None ]),
                               macro_post_space=' ',
                               pos=7+2,len=8-2),
                LatexCharsNode(parsing_state=parsing_state,
                               chars='stuff\n\\end',
                               pos=7+8, len=13+1-8+4),
            ], p, 7+14+4))


    def test_tolerant_recovery_unterminated_group(self):
        # In tolerant parsing mode, whatever could be parsed before the error
        # occurred must be kept.  Here the stream ends before the closing brace
        # of the \textbf{...} argument; the argument group node must still
        # report the contents that were parsed so far, and in particular its
        # nodelist must not be None.

        latextext = r'''Text \textbf{unclosed bold'''

        lw = LatexWalker(latextext, tolerant_parsing=True)
        parsing_state = lw.make_parsing_state()

        nodelist, p, l = lw.get_latex_nodes(pos=0, parsing_state=parsing_state)

        self.assertEqual(len(nodelist), 2)

        groupnode = nodelist[1].nodeargd.argnlist[0]
        self.assertIsNotNone(groupnode.nodelist)
        self.assertEqual(len(groupnode.nodelist), 1)
        self.assertEqual(groupnode.nodelist[0].chars, 'unclosed bold')

        # the recovered group spans up to the end of the stream
        self.assertEqual(groupnode.pos, len('Text \\textbf'))
        self.assertEqual(groupnode.pos_end, len(latextext))


    def test_tolerant_recovery_unterminated_environment(self):
        # Same as above for an environment body that is never closed by a
        # matching \end{...}.

        latextext = r'''\begin{itemize}\item one'''

        lw = LatexWalker(latextext, tolerant_parsing=True)
        parsing_state = lw.make_parsing_state()

        nodelist, p, l = lw.get_latex_nodes(pos=0, parsing_state=parsing_state)

        self.assertEqual(len(nodelist), 1)

        envnode = nodelist[0]
        self.assertEqual(envnode.environmentname, 'itemize')
        self.assertIsNotNone(envnode.nodelist)
        self.assertEqual(len(envnode.nodelist), 2)
        self.assertEqual(envnode.nodelist[0].macroname, 'item')
        self.assertEqual(envnode.nodelist[1].chars, 'one')


    def test_bug_issueno49(self):
        # see issue #49
        #
        # The issue was that when a char token with whitespace was flushed
        # before looking at a new token, and when the read_max_nodes condition
        # was hit just at that moment, the third tuple element 'len' of the
        # return value of get_latex_nodes() was incorrect.

        doc_content = r"""\emph{A}
\emph{B}"""

        lw = LatexWalker(
            doc_content,
            tolerant_parsing=False,
        )

        pos = 0
        (nodelist, npos, nlen) = lw.get_latex_nodes(pos, read_max_nodes=1)
        self.assertEqual(len(nodelist), 1)
        node = nodelist[0]
        self.assertEqual(npos, node.pos)
        self.assertEqual(nlen, node.len)

        pos = doc_content.find('\n')
        (nodelist, npos, nlen) = lw.get_latex_nodes(pos, read_max_nodes=1)
        self.assertEqual(len(nodelist), 1)
        node = nodelist[0]
        self.assertEqual(npos, node.pos)
        self.assertEqual(nlen, node.len)




    def test_bug_issueno57(self):
        # see issue #57

        walker_context = get_default_latex_context_db()
        walker_context.add_context_category(
            'mymacros',
            macros=[
                macrospec.std_macro('foo', '[{['),
            ],
            prepend=True
        )

        doc_content = r"""\foo{test}"""

        lw = LatexWalker(
            doc_content,
            latex_context=walker_context,
            tolerant_parsing=False,
        )

        pos = 0
        # shouldn't raise exception
        (nodelist, npos, nlen) = lw.get_latex_nodes(pos, read_max_nodes=1)
        self.assertEqual(len(nodelist), 1)
        node = nodelist[0]
        self.assertTrue(node.macroname == 'foo')
        self.assertTrue(node.nodeargd)
        self.assertEqual(len(node.nodeargd.argnlist), 3)


    def test_title_author_date_optional_short_argument(self):
        # see issue #114.  The default specs declare \title, \author and \date
        # with the optional "short form" argument that beamer and the AMS
        # classes accept, in addition to the mandatory argument.

        for macroname in ('title', 'author', 'date'):

            lw = LatexWalker('\\'+macroname+r'[Short]{The Full Form}',
                             tolerant_parsing=False)
            (nodelist, npos, nlen) = lw.get_latex_nodes()
            self.assertEqual(len(nodelist), 1)
            argnlist = nodelist[0].nodeargd.argnlist
            self.assertEqual(len(argnlist), 2)
            self.assertEqual(argnlist[0].nodelist[0].chars, 'Short')
            self.assertEqual(argnlist[1].nodelist[0].chars, 'The Full Form')

            # the standard classes' form, with the optional argument absent
            lw = LatexWalker('\\'+macroname+r'{The Full Form}',
                             tolerant_parsing=False)
            (nodelist, npos, nlen) = lw.get_latex_nodes()
            self.assertEqual(len(nodelist), 1)
            argnlist = nodelist[0].nodeargd.argnlist
            self.assertEqual(len(argnlist), 2)
            self.assertTrue(argnlist[0] is None)
            self.assertEqual(argnlist[1].nodelist[0].chars, 'The Full Form')


    def test_href_url_argument_is_verbatim(self):
        # the target of \href is read verbatim, because a URL may well contain
        # characters that are special to LaTeX.  A percent sign in particular
        # would otherwise start a comment and swallow the rest of the line.

        latextext = r'\href{http://x.org/a%20b#f~g_h}{the \textbf{link}}'
        lw = LatexWalker(latextext, tolerant_parsing=False)

        (nodelist, npos, nlen) = lw.get_latex_nodes(pos=0, read_max_nodes=1)
        self.assertEqual(len(nodelist), 1)
        node = nodelist[0]

        self.assertEqual(node.macroname, 'href')
        self.assertEqual(len(node.nodeargd.argnlist), 2)

        # the URL argument is a group whose contents are a single chars node
        # holding the target exactly as it was written
        urlarg = node.nodeargd.argnlist[0]
        self.assertEqual(urlarg.delimiters, ('{','}'))
        self.assertEqual(len(urlarg.nodelist), 1)
        self.assertEqual(urlarg.nodelist[0].chars, 'http://x.org/a%20b#f~g_h')

        # the argument is named, so it can also be picked out by name
        argsinfo = ParsedArgumentsInfo(node=node).get_all_arguments_info(
            ('url',), allow_additional_arguments=True)
        self.assertEqual(
            argsinfo['url'].get_content_nodelist().get_content_as_chars(),
            'http://x.org/a%20b#f~g_h'
        )

        # the link text, in contrast, is still parsed as ordinary LaTeX
        textarg = node.nodeargd.argnlist[1]
        self.assertEqual(len(textarg.nodelist), 2)
        self.assertEqual(textarg.nodelist[0].chars, 'the ')
        self.assertEqual(textarg.nodelist[1].macroname, 'textbf')


    def test_url_argument_is_verbatim(self):
        # same for \url, which takes only the target

        latextext = r'\url{http://x.org/a%20b#f~g_h}'
        lw = LatexWalker(latextext, tolerant_parsing=False)

        (nodelist, npos, nlen) = lw.get_latex_nodes(pos=0, read_max_nodes=1)
        node = nodelist[0]

        self.assertEqual(node.macroname, 'url')
        self.assertEqual(len(node.nodeargd.argnlist), 1)

        urlarg = node.nodeargd.argnlist[0]
        self.assertEqual(urlarg.delimiters, ('{','}'))
        self.assertEqual(urlarg.nodelist[0].chars, 'http://x.org/a%20b#f~g_h')


    def test_href_url_repeated_with_braces(self):
        # the verbatim parser that reads the target is stored in the macro's
        # specification, so the very same parser object is used again for each
        # occurrence in the document.  Braces inside a target exercise the
        # parser's nesting depth bookkeeping, which must therefore not carry
        # over from one occurrence to the next.

        latextext = r'\url{http://a.org/x{y}} \url{http://b.org/p{q}} \href{http://c.org/{z}}{C}'
        lw = LatexWalker(latextext, tolerant_parsing=False)

        (nodelist, npos, nlen) = lw.get_latex_nodes(pos=0)

        urls = []
        for n in nodelist:
            if n.isNodeType(LatexMacroNode) and n.macroname in ('url', 'href'):
                urls.append(n.nodeargd.argnlist[0].nodelist[0].chars)

        self.assertEqual(
            urls,
            ['http://a.org/x{y}', 'http://b.org/p{q}', 'http://c.org/{z}']
        )


    def test_pyltxenc1_MacrosDef_ignores_leading_star(self):
        # in pylatexenc 1.x, a leading '*' in a macro call was always accepted
        # (and ignored); macro specs built with MacrosDef() must still absorb it
        # so that the arguments that follow are parsed correctly.
        macro_dict = {'mymacro': MacrosDef('mymacro', '[', 2)}

        lw = LatexWalker(r'\mymacro*[a]{b}{c} x', macro_dict=macro_dict,
                         tolerant_parsing=False)
        (nodelist, npos, nlen) = lw.get_latex_nodes(pos=0)

        macronode = nodelist[0]
        self.assertEqual(macronode.macroname, 'mymacro')
        self.assertEqual(macronode.latex_verbatim(), r'\mymacro*[a]{b}{c}')
        self.assertEqual(macronode.nodeoptarg.latex_verbatim(), '[a]')
        self.assertEqual(
            [ n.latex_verbatim() for n in macronode.nodeargs ],
            ['{b}', '{c}']
        )
        self.assertEqual(nodelist[1].chars, ' x')

        # the same macro without the star still works
        lw2 = LatexWalker(r'\mymacro[a]{b}{c} x', macro_dict=macro_dict,
                          tolerant_parsing=False)
        (nodelist2, npos2, nlen2) = lw2.get_latex_nodes(pos=0)
        self.assertEqual(nodelist2[0].latex_verbatim(), r'\mymacro[a]{b}{c}')
        self.assertEqual(nodelist2[0].nodeoptarg.latex_verbatim(), '[a]')
        self.assertEqual(nodelist2[1].chars, ' x')


    def test_pyltxenc1_module_get_latex_nodes_pos(self):
        # the module-level get_latex_nodes() must honor its pos= argument
        (nodelist, npos, nlen) = pyltxenc1_get_latex_nodes('abcdef', pos=3)
        self.assertEqual([ n.chars for n in nodelist ], ['def'])
        self.assertEqual(npos, 3)


    def test_make_json_encoder(self):
        # the json encoder must be able to serialize all the objects that show
        # up in a node tree, including the parsers and the parsing state deltas
        # stored in the argument specifications
        latextext = r'\textbf{hi} $x^2$ \begin{enumerate}\item[a] hi\end{enumerate}'
        lw = LatexWalker(latextext, tolerant_parsing=True)
        (nodelist, npos, nlen) = lw.get_latex_nodes(pos=0)

        jsonstr = json.dumps({'nodelist': nodelist},
                             cls=make_json_encoder(lw))
        # the result is valid JSON that we can read back
        jsonobj = json.loads(jsonstr)
        self.assertEqual(jsonobj['nodelist'][0]['nodetype'], 'LatexMacroNode')
        self.assertEqual(jsonobj['nodelist'][0]['macroname'], 'textbf')

    def test_document_ending_with_an_optional_argument_macro(self):
        # A document that ends right after a macro that accepts an optional
        # argument parses normally, and the walker doesn't report anything
        # about having reached the end of the input.  (The unit-level tests for
        # this live in test_latexnodes_parsers_delimited.py; this one needs the
        # default latex context database and so cannot run in the JavaScript
        # build.)
        latextext = r'''A title ending in \\'''

        lw = LatexWalker(s=latextext, tolerant_parsing=True)

        nodes, parsing_state_delta = lw.parse_content(
            latexnodes_parsers.LatexGeneralNodesParser(),
            token_reader=lw.make_token_reader(),
            parsing_state=lw.make_parsing_state(),
        )

        self.assertEqual(len(nodes), 2)
        self.assertTrue(nodes[0].isNodeType(LatexCharsNode))
        self.assertTrue(nodes[1].isNodeType(LatexMacroNode))
        self.assertEqual(nodes[1].macroname, '\\')

    def test_parse_content_default_parser(self):
        # parse_content() without a parser argument parses the full latex string
        # with a plain LatexGeneralNodesParser().
        latextext = r'''Hello \textbf{world}, \[ x+y \] and some more text.'''

        lw = LatexWalker(s=latextext)
        nodes, parsing_state_delta = lw.parse_content()

        lw_explicit = LatexWalker(s=latextext)
        nodes_explicit, parsing_state_delta_explicit = lw_explicit.parse_content(
            latexnodes_parsers.LatexGeneralNodesParser()
        )

        self.assertEqual(len(nodes), len(nodes_explicit))
        self.assertEqual(nodes.pos, nodes_explicit.pos)
        self.assertEqual(nodes.pos_end, nodes_explicit.pos_end)
        self.assertEqual(nodes.pos, 0)
        self.assertEqual(nodes.pos_end, len(latextext))
        self.assertEqual(
            [ n.nodeType() for n in nodes ],
            [ n.nodeType() for n in nodes_explicit ]
        )
        self.assertIsNone(parsing_state_delta)
        self.assertIsNone(parsing_state_delta_explicit)




# more test data

def get_test_latex_data_with_possible_inconsistencies():
    return r"""\documentclass[11pt,a4paper]{article}

\usepackage[utf8]{inputenc}
\usepackage{graphicx}
\usepackage{amsmath}

\begin{document}
D sklfmdklaf dafdaf sah. fjdkslanf \textbf{djksa fnjdka} fdsl\`a; \emph{fnkdsl} a. Fioe
fndjksf.  More {\it italic test} text. Inline math $\vec x$ and
\begin{align}
  \label{eq:Alphas}
  \alpha_{\boldk,\uparrow} =
  \begin{cases} c_{\boldk,\uparrow} & \text{for $k>k_F$} \\
    c_{-\boldk,\downarrow}^\dagger & \text{for $k<k_F$} \end{cases}
  \qquad ; \qquad
  \alpha_{\boldk,\downarrow} =
  \begin{cases} c_{\boldk,\downarrow} & \text{for $k>k_F$} \\
    c_{-\boldk,\uparrow}^\dagger & \text{for $k<k_F$} \end{cases}
  \quad .
\end{align}

\begin{itemize}
\item Show that the $\alpha$, $\alpha^\dagger$'s obey fermionic commutation relations.

  Remember that fermionic creation and annihilation operators $\alpha^\dagger$,
  $\alpha$ obey 
  \begin{align}
      \{\alpha^\nodagger_{\boldk,s}, \alpha^\nodagger_{\boldk',s'}\}
      = \{\alpha_{\boldk,s}^\dagger, \alpha_{\boldk',s'}^\dagger\} = 0
      \quad;\quad
      \{\alpha^\nodagger_{\boldk,s}, \alpha_{\boldk',s'}^\dagger\}
      = \delta_{\boldk,\boldk'}\delta_{s,s'}\ .
  \end{align}

\item Argue that eq.~\eqref{eq:Alphas} is a unitary transformation of the creation and annihilation
  operators. Such a transformation is also called a \emph{Bogoliubov transformation}.
  What happens if you act with the annihilators $c_{\boldk,s}$ and
  $\alpha_{\boldk,s}$ on the ground state of the gas?
\end{itemize}

\begin{abc}
  This environment is called `abc,' but I'm going to close it with the wrong "end" command.

  This will confuse the parser:
\end{zzzzz}

What would you think about a stray closing brace: } ?

This is a final sentence. { <-- this brace is not closed.

\end{document}
"""







if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#

