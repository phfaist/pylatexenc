# -*- coding: utf-8 -*-
from __future__ import print_function # no unicode_literals, test with native strings on py2

import unittest
import sys
import logging

if sys.version_info.major > 2:
    def unicode(string): return string
    basestring = str

from pylatexenc.latexwalker import (
    LatexWalker, LatexToken, LatexCharsNode, LatexGroupNode, LatexCommentNode,
    LatexMacroNode, LatexSpecialsNode, LatexEnvironmentNode, LatexMathNode,
    LatexWalkerParseError, get_default_latex_context_db
)

from pylatexenc import macrospec

def _tmp1133(a, b):
    return b is not None and a.argnlist == b.argnlist
macrospec.ParsedMacroArgs.__eq__ = _tmp1133


class TestLatexWalker(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestLatexWalker, self).__init__(*args, **kwargs)
        self.maxDiff = None
        
    def test_get_token(self):
        
        latextext = r'''Text \`accent and \textbf{bold text} and $\vec b$ vector \& also Fran\c cois
\begin{enumerate}[(i)]
\item Hi there!  % here goes a comment
\item[a] Hello!  @@@
     \end{enumerate}
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
                         (LatexSpecialsNode(parsing_state=parsing_state,
                                            specials_chars='?`',
                                            nodeargd=None,
                                            pos=p, len=2),
                          p, 2))



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
        self.assertEqual(lw.get_latex_maybe_optional_arg(pos=p, parsing_state=parsing_state), None)
        p = latextext.find(r'\cite')+len(r'\cite')
        self.assertEqual(lw.get_latex_maybe_optional_arg(pos=p, parsing_state=parsing_state),
                         (LatexGroupNode(
                             parsing_state=parsing_state,
                             delimiters=('[', ']'),
                             nodelist=[
                                 LatexCharsNode(
                                     parsing_state=parsing_state,
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
        self.assertEqual(
            lw.get_latex_braced_group(pos=p, brace_type='[', parsing_state=parsing_state),
            (LatexGroupNode(parsing_state=parsing_state,
                            delimiters=('[', ']'),
                            nodelist=[
                                LatexCharsNode(parsing_state=parsing_state,
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
                                parsing_state=parsing_state,
                                delimiters=('[', ']'),
                                nodelist=[
                                    LatexCharsNode(parsing_state=parsing_state,
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
                        parsing_state=parsing_state,
                        delimiters=('[', ']'),
                        nodelist=[
                            LatexCharsNode(parsing_state=parsing_state,
                                           chars='(i)',
                                           pos=p+18,len=21-18)
                        ],
                        pos=p+17,len=22-17),
                ]),
                pos=p,
                len=latextext.find(r'\end{enumerate}')+len(r'\end{enumerate}')-p
             ), p, latextext.find(r'\end{enumerate}')+len(r'\end{enumerate}')-p)
        self.assertEqual(
            lw.get_latex_environment(pos=p, environmentname='enumerate',
                                     parsing_state=parsing_state),
            good_parsed_structure
        )
        self.assertEqual(
            lw.get_latex_environment(pos=p,
                                     parsing_state=parsing_state),
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
            lw.get_latex_nodes(pos=p, stop_upon_closing_brace='}', parsing_state=parsing_state),
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
        good_parsed_structure = lambda parsing_state, ps2, ps3: [
            LatexCharsNode(parsing_state=parsing_state,
                           chars=' cx^2+z=-d',
                           pos=p+2,len=12-2),
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
        parsing_state2 = nodes[2].nodeargd.argnlist[0].parsing_state # "inner text mode" state
        parsing_state3 = nodes[2].nodeargd.argnlist[0].nodelist[1].nodelist[0].parsing_state
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
        parsing_state2 = nodes[0].nodelist[2].nodeargd.argnlist[0].parsing_state
        parsing_state3 = nodes[0].nodelist[2].nodeargd.argnlist[0].nodelist[1].nodelist[0].parsing_state
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
                LatexCharsNode(parsing_state=parsing_state,
                               chars='\n\nNew paragraph here.\n',
                               pos=21+18, len=1+1+19+1),
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
                LatexCharsNode(parsing_state=parsing_state,
                               chars='\n\n',
                               pos=26, len=2),
                LatexCommentNode(parsing_state=parsing_state,
                                 comment=' line comment on its own',
                                 comment_post_space='\n',
                                 pos=27+1, len=25+1),
                LatexCommentNode(parsing_state=parsing_state,
                                 comment=' and a second line',
                                 comment_post_space='',
                                 pos=27+1+26, len=19),
                LatexCharsNode(parsing_state=parsing_state,
                               chars='\n\nAlso a ',
                               pos=27+1+26+19, len=2+7),
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
        nodes, pos, len_ = lw.get_latex_nodes(pos=p, read_max_nodes=5, parsing_state=parsing_state)
        parsing_state_inner = nodes[3].nodelist[0].parsing_state # inner state -- math mode -- get this
        self.assertTrue(parsing_state_inner.in_math_mode)
        self.assertEqual(
            (nodes, pos, len_),
            ([
                LatexCharsNode(parsing_state=parsing_state,
                               chars='and ',
                               pos=p, len=4),
                LatexMacroNode(parsing_state=parsing_state,
                               macroname='textbf',
                               nodeargd=macrospec.ParsedMacroArgs(argspec='{', argnlist=[
                                   LatexGroupNode(parsing_state=parsing_state,
                                                  delimiters=('{', '}'),
                                                  nodelist=[
                                                      LatexCharsNode(parsing_state=parsing_state,
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
                                  LatexMacroNode(parsing_state=parsing_state_inner,
                                                 macroname='vec',
                                                 macro_post_space=' ',
                                                 nodeargd=macrospec.ParsedMacroArgs(argspec='{', argnlist=[
                                                     LatexCharsNode(parsing_state=parsing_state_inner,
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
            self.fail(unicode("get_latex_nodes() raised LatexWalkerParseError, but it shouldn't have in "
                              "tolerant parsing mode!\n")+unicode(e))
            
    

    def test_verbatim(self):

        latextext = r"""Use the environment \verb+\begin{verbatim}...\end{verbatim}+ to
\begin{verbatim}
typeset \verbatim text with \LaTeX $ escapes \(like this\).
\end{verbatim}
This is it."""

        lw = LatexWalker(latextext)

        parsing_state = lw.make_parsing_state()

        p=0
        self.assertEqual(
            lw.get_latex_nodes(pos=p, parsing_state=parsing_state),
            ([
                LatexCharsNode(parsing_state=parsing_state, pos=0, len=20,
                               chars='Use the environment '),
                LatexMacroNode(parsing_state=parsing_state, pos=20, len=40,
                               macroname='verb',
                               macro_post_space='',
                               nodeargd=macrospec.ParsedVerbatimArgs(
                                   verbatim_chars_node=
                                   LatexCharsNode(parsing_state=parsing_state, pos=26, len=33,
                                                  chars='\\begin{verbatim}...\\end{verbatim}'),
                                   verbatim_delimiters=('+', '+'),
                               )),
                LatexCharsNode(parsing_state=parsing_state, pos=60, len=4, chars=' to\n'),
                LatexEnvironmentNode(
                    parsing_state=parsing_state, pos=64, len=91,
                    environmentname='verbatim', nodelist=[],
                    nodeargd=macrospec.ParsedVerbatimArgs(
                        verbatim_chars_node=
                        LatexCharsNode(
                            parsing_state=parsing_state, pos=80, len=61,
                            chars='\ntypeset \\verbatim text with \\LaTeX $ escapes \\(like this\\).\n'
                        ),
                        verbatim_delimiters=None,
                    )
                ),
                LatexCharsNode(parsing_state=parsing_state, pos=155, len=12,
                               chars='\nThis is it.')
            ],
            0,
            167)
        )


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

        self.assertEqual((npos,nlen), (0,len(latextext)))
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
                                           pos=13, len=5, delimiters=('{', '}'),
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
                                           parsing_state=parsing_state_defa,
                                           pos=19+15, len=3, delimiters=('[', ']'),
                                           nodelist=[
                                               LatexCharsNode(
                                                   parsing_state=parsing_state_defa,
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
                LatexCharsNode(parsing_state=parsing_state_defab, pos=19+26, len=1+1+16+1+12,
                               chars=r"""

Blah blah blah.

Use macros: """,
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
        self.assertEqual(
            lw.get_latex_nodes(pos=p, read_max_nodes=3, parsing_state=parsing_state),
            ([
                LatexCharsNode(parsing_state=parsing_state,
                               chars='\n',
                               pos=0, len=1),
                LatexMacroNode(parsing_state=parsing_state,
                               macroname='documentclass',
                               nodeargd=macrospec.ParsedMacroArgs(argspec='[{', argnlist=[
                                   LatexGroupNode(parsing_state=parsing_state,
                                                  delimiters=('[', ']'),
                                                  nodelist=[
                                                      LatexCharsNode(parsing_state=parsing_state,
                                                                     chars='stuff',
                                                                     pos=1+15,len=20-15),
                                                  ],
                                                  pos=1+14,len=21-14),
                                   LatexGroupNode(parsing_state=parsing_state,
                                                  delimiters=('{', '}'),
                                                  nodelist=[
                                                      LatexCharsNode(parsing_state=parsing_state,
                                                                     chars='docclass',
                                                                     pos=1+22,len=30-22),
                                                  ],
                                                  pos=1+21,len=31-21)
                               ]),
                               pos=1+0,len=31),
                LatexCharsNode(parsing_state=parsing_state,
                               chars='\n\n',
                               pos=1+31, len=2),
            ], p, 34))




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

