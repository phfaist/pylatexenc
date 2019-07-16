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
    LatexWalkerParseError
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

        emptyargs = macrospec.ParsedMacroArgs()

        self.assertEqual(lw.get_latex_expression(pos=0),
                         (LatexCharsNode(parsed_context=lw.parsed_context,
                                         chars='T',
                                         pos=0, len=1),0,1,))
        p = latextext.find(r'\`')
        self.assertEqual(lw.get_latex_expression(pos=p),
                         (LatexMacroNode(parsed_context=lw.parsed_context,
                                         macroname='`',
                                         nodeargd=None, pos=p, len=2),p,2,))
        p = latextext.find(r'{')
        self.assertEqual(lw.get_latex_expression(pos=p),
                         (LatexGroupNode(parsed_context=lw.parsed_context,
                                         nodelist=[
                                             LatexCharsNode(parsed_context=lw.parsed_context,
                                                            chars='bold text',
                                                            pos=p+1,len=9)
                                         ],
                                         pos=p, len=11),
                          p,11,))
        p = latextext.find(r'%')-2 # check: correctly skips comments also after space
        self.assertEqual(lw.get_latex_expression(pos=p),
                         (LatexMacroNode(parsed_context=lw.parsed_context,
                                         macroname='item',
                                         nodeargd=None,
                                         pos=p+2+len('% here goes a comment\n'),
                                         len=5),
                          p+2+len('% here goes a comment\n'),5,))
        # check correct behavior if directly on brace close
        p = latextext.find(r'}')
        self.assertEqual(lw.get_latex_expression(pos=p, strict_braces=True),
                         (LatexCharsNode(parsed_context=lw.parsed_context,
                                         chars='', pos=p, len=0),p,0,))
        lw2 = LatexWalker(latextext, tolerant_parsing=False)
        self.assertEqual(lw2.get_latex_expression(pos=p, strict_braces=False),
                         (LatexCharsNode(parsed_context=lw2.parsed_context,
                                         chars='', pos=p, len=0),p,0,))
        with self.assertRaises(LatexWalkerParseError):
            dummy = lw2.get_latex_expression(pos=p, strict_braces=True)
        
        p = latextext.find(r'?`')
        self.assertEqual(lw.get_latex_expression(pos=p),
                         (LatexSpecialsNode(parsed_context=lw.parsed_context,
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

        p = latextext.find(r'\textbf')+len(r'\textbf')
        self.assertEqual(lw.get_latex_maybe_optional_arg(pos=p), None)
        p = latextext.find(r'\cite')+len(r'\cite')
        self.assertEqual(lw.get_latex_maybe_optional_arg(pos=p),
                         (LatexGroupNode(
                             parsed_context=lw.parsed_context,
                             nodelist=[
                                 LatexCharsNode(
                                     parsed_context=lw.parsed_context,
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

        p = latextext.find(r'Also: {')+len('Also:') # points on space after 'Also:'
        good_parsed_structure = \
            ( LatexGroupNode(
                parsed_context=lw.parsed_context,
                nodelist=[
                    LatexMacroNode(parsed_context=lw.parsed_context,
                                   macroname='itshape',
                                   macro_post_space=' ',
                                   pos=p+2,
                                   len=len(r'\itshape ')),
                    LatexCharsNode(parsed_context=lw.parsed_context,
                                   chars='some italic text',
                                   pos=(p+16-5),
                                   len=32-16)
                ],
                pos=p+1,
                len=len(r'{\itshape some italic text}')
              ),
              p+1, len(r'{\itshape some italic text}'), )
        self.assertEqual(
            lw.get_latex_braced_group(pos=p, brace_type='{'),
            good_parsed_structure
        )
        self.assertEqual(
            lw.get_latex_braced_group(pos=p+1, brace_type='{'),
            good_parsed_structure
        )

        p = latextext.find(r'[(i)]')
        self.assertEqual(
            lw.get_latex_braced_group(pos=p, brace_type='['),
            (LatexGroupNode(parsed_context=lw.parsed_context,
                            nodelist=[
                                LatexCharsNode(parsed_context=lw.parsed_context,
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

        p = latextext.find(r'\begin{enumerate}')
        good_parsed_structure = \
            (LatexEnvironmentNode(
                parsed_context=lw.parsed_context,
                envname='enumerate',
                nodelist=[
                    LatexCharsNode(parsed_context=lw.parsed_context,
                                   chars='\n',
                                   pos=p+22, len=1),
                    LatexMacroNode(parsed_context=lw.parsed_context,
                                   macroname='item',
                                   nodeargd=macrospec.ParsedMacroArgs([None]),
                                   macro_post_space=' ',
                                   pos=p+23, len=6),
                    LatexCharsNode(parsed_context=lw.parsed_context,
                                   chars='Hi there!  ',
                                   pos=p+23+6, len=17-6),
                    LatexCommentNode(parsed_context=lw.parsed_context,
                                     comment=' here goes a comment',
                                     comment_post_space='\n ',
                                     pos=p+23+17, len=38-17+2),
                    LatexMacroNode(
                        parsed_context=lw.parsed_context,
                        macroname='item',
                        nodeargd=macrospec.ParsedMacroArgs([
                            LatexGroupNode(
                                parsed_context=lw.parsed_context,
                                nodelist=[
                                    LatexCharsNode(parsed_context=lw.parsed_context,
                                                   chars='a',
                                                   pos=p+23+39+7, len=1)
                                ],
                                pos=p+23+39+6, len=3)
                        ]),
                        pos=p+23+39+1,
                        len=9-1
                    ),
                    LatexCharsNode(parsed_context=lw.parsed_context,
                                   chars=' Hello!  @@@\n     ',
                                   pos=p+23+39+9,
                                   len=22+5-9)
                ],
                nodeargd=macrospec.ParsedMacroArgs([
                    LatexGroupNode(
                        parsed_context=lw.parsed_context,
                        nodelist=[
                            LatexCharsNode(parsed_context=lw.parsed_context,
                                           chars='(i)',
                                           pos=p+18,len=21-18)
                        ],
                        pos=p+17,len=22-17),
                ]),
                pos=p,
                len=latextext.find(r'\end{enumerate}')+len(r'\end{enumerate}')-p
             ), p, latextext.find(r'\end{enumerate}')+len(r'\end{enumerate}')-p)
        self.assertEqual(
            lw.get_latex_environment(pos=p, environmentname='enumerate'),
            good_parsed_structure
        )
        self.assertEqual(
            lw.get_latex_environment(pos=p),
            good_parsed_structure
        )

        with self.assertRaises(LatexWalkerParseError):
            dummy = lw.get_latex_environment(pos=p, environmentname='XYZNFKLD-WRONG')

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

        #lw.get_latex_nodes(pos=0,stop_upon_closing_brace=None,stop_upon_end_environment=None,
        #                   stop_upon_closing_mathmode=None)

        p = latextext.find('Also: {')
        self.assertEqual(
            lw.get_latex_nodes(pos=p),
            ([
                LatexCharsNode(parsed_context=lw.parsed_context,
                               chars='Also: ',
                               pos=p, len=6),
                LatexGroupNode(parsed_context=lw.parsed_context,
                               nodelist=[
                                   LatexMacroNode(parsed_context=lw.parsed_context,
                                                  macroname='itshape',
                                                  macro_post_space=' ',
                                                  pos=p+7,len=16-7),
                                   LatexCharsNode(parsed_context=lw.parsed_context,
                                                  chars='some italic text',
                                                  pos=p+16,len=32-16)
                               ],
                               pos=p+6,len=33-6),
                LatexCharsNode(parsed_context=lw.parsed_context,
                               chars='.',
                               pos=p+33,len=1)
            ], p, len(latextext)-p-1)) # trailing '\n' is not included

        p = latextext.find('Also: {')+len('Also: {') # points inside right after open brace
        self.assertEqual(
            lw.get_latex_nodes(pos=p, stop_upon_closing_brace='}'),
            ([
                LatexMacroNode(parsed_context=lw.parsed_context,
                               macroname='itshape', macro_post_space=' ',
                               pos=p,len=16-7),
                LatexCharsNode(parsed_context=lw.parsed_context,
                               chars='some italic text',
                               pos=p+16-7,len=32-16),
             ], p, len(r'\itshape some italic text}')))

        # test our own macro lists etc.
        pindeed = latextext.find('Indeed thanks to')
        lineindeed = latextext[pindeed:latextext.find('\n', pindeed)]
        lw2 = LatexWalker(lineindeed, tolerant_parsing=False,
                          macro_dict={'cite': macrospec.std_macro('cite',False,4)})
        self.assertEqual(
            lw2.get_latex_nodes(pos=0),
            ([
                LatexCharsNode(parsed_context=lw2.parsed_context,
                               chars='Indeed thanks to ',
                               pos=0,len=17),
                LatexMacroNode(
                    parsed_context=lw2.parsed_context,
                    macroname='cite',
                    nodeargd=macrospec.ParsedMacroArgs([
                        LatexCharsNode(parsed_context=lw2.parsed_context,
                                       chars='[',
                                       pos=22,len=1),
                        LatexCharsNode(parsed_context=lw2.parsed_context,
                                       chars='L',
                                       pos=23,len=1),
                        LatexCharsNode(parsed_context=lw2.parsed_context,
                                       chars='e',
                                       pos=24,len=1),
                        LatexCharsNode(parsed_context=lw2.parsed_context,
                                       chars='m',
                                       pos=25,len=1),
                    ]),
                    pos=17,len=26-17),
            LatexCharsNode(parsed_context=lw2.parsed_context,
                           chars='ma 3]',
                           pos=26,len=31-26),
            LatexGroupNode(parsed_context=lw2.parsed_context,
                           nodelist=[
                               LatexCharsNode(parsed_context=lw2.parsed_context,
                                              chars='Author',
                                              pos=32,len=38-32),
                           ],
                           pos=31,len=39-31),
            LatexCharsNode(parsed_context=lw2.parsed_context,
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

        p = latextext.find('$')
        good_parsed_structure = [
            LatexMacroNode(parsed_context=lw.parsed_context,
                           macroname=r'vec',
                           nodeargd=macrospec.ParsedMacroArgs([
                               LatexGroupNode(parsed_context=lw.parsed_context,
                                              nodelist=[
                                                  LatexCharsNode(parsed_context=lw.parsed_context,
                                                                 chars='x',
                                                                 pos=1+40,len=1)
                                              ],
                                              pos=1+39,len=3)
                           ]),
                           macro_post_space='',
                           pos=1+35,len=42-35),
            LatexCharsNode(parsed_context=lw.parsed_context,
                           chars=r' + ',
                           pos=1+42,len=45-42),
            LatexMacroNode(parsed_context=lw.parsed_context,
                           macroname=r'hat',
                           nodeargd=macrospec.ParsedMacroArgs([
                               LatexCharsNode(parsed_context=lw.parsed_context,
                                              chars='p',
                                              pos=1+50,len=1)]),
                           macro_post_space=' ',
                           pos=1+45,len=51-45),
        ]
        self.assertEqual(
            lw.get_latex_nodes(pos=p+1, stop_upon_closing_mathmode='$'),
            ( good_parsed_structure ,
              p+1, len(r'\vec{x} + \hat p$') ) # len includes closing token
        )
        # check that first node is math mode node when parsing starting from & including first '$'
        self.assertEqual(
            lw.get_latex_nodes(pos=p)[0][0],
            LatexMathNode(parsed_context=lw.parsed_context,
                          displaytype='inline', nodelist=good_parsed_structure,
                          pos=p, len=len(r'$\vec{x} + \hat p$'), delimiters=('$','$'))
        )


        p = latextext.find('$$')
        self.assertEqual(
            lw.get_latex_nodes(pos=p+2, stop_upon_closing_mathmode='$$'),
            ( [ LatexCharsNode(parsed_context=lw.parsed_context,
                               chars='\n   ax + b = y\n',
                               pos=p+2,len=len('\n   ax + b = y\n')), ] ,
              p+2, len('\n   ax + b = y\n$$') ) # len includes closing token
        )
        # check that first node is math mode node when parsing including the math mode start
        self.assertEqual(
            lw.get_latex_nodes(pos=p)[0][0],
            LatexMathNode(parsed_context=lw.parsed_context,
                          displaytype='display',
                          nodelist=[ LatexCharsNode(parsed_context=lw.parsed_context,
                                                    chars='\n   ax + b = y\n',
                                                    pos=p+2,len=len('\n   ax + b = y\n')), ],
                          delimiters=('$$', '$$'),
                          pos=p,len=len('$$\n   ax + b = y\n$$'))
        )


        p = latextext.find(r'\[')
        good_parsed_structure = [
            LatexCharsNode(parsed_context=lw.parsed_context,
                           chars=' cx^2+z=-d',
                           pos=p+2,len=12-2),
            LatexMacroNode(parsed_context=lw.parsed_context,
                           macroname='quad',
                           pos=p+12,len=17-12),
            LatexMacroNode(parsed_context=lw.parsed_context,
                           macroname='text',
                           nodeargd=macrospec.ParsedMacroArgs([
                               LatexGroupNode(
                                   parsed_context=lw.parsed_context,
                                   nodelist=[
                                       LatexCharsNode(parsed_context=lw.parsed_context,
                                                      chars='if ',
                                                      pos=p+23,len=26-23),
                                       LatexMathNode(parsed_context=lw.parsed_context,
                                                     displaytype='inline', nodelist=[
                                                         LatexCharsNode(parsed_context=lw.parsed_context,
                                                                        chars='x<0',
                                                                        pos=p+27,len=3)
                                                     ],
                                                     delimiters=('$','$'),
                                                     pos=p+26,len=31-26)
                                   ],
                                   pos=p+22,len=32-22)
                           ]),
                           pos=p+17,len=32-17),
            LatexCharsNode(parsed_context=lw.parsed_context,
                           chars=' ',
                           pos=p+32,len=1),
        ]
        self.assertEqual(
            lw.get_latex_nodes(pos=p+2, stop_upon_closing_mathmode=r'\]'),
            ( good_parsed_structure ,
              p+2, latextext.find(r'\]', p+2) - (p+2) + 2 ) # len includes closing token
        )
        # check that first node is math mode node when parsing including the math mode start
        self.assertEqual(
            lw.get_latex_nodes(pos=p)[0][0],
            LatexMathNode(parsed_context=lw.parsed_context,
                          displaytype='display', nodelist=good_parsed_structure,
                          delimiters=(r'\[', r'\]'),
                          pos=p,len=latextext.find(r'\]', p+2) + 2 - p)
        )

        p = latextext.find(r'\(')
        good_parsed_structure = [
            LatexMacroNode(
                parsed_context=lw.parsed_context,
                macroname='mbox',
                nodeargd=macrospec.ParsedMacroArgs([
                    LatexGroupNode(parsed_context=lw.parsed_context,
                                   nodelist=[
                                       LatexCharsNode(parsed_context=lw.parsed_context,
                                                      chars='Prob',
                                                      pos=p-29+37,len=41-37)
                                   ],
                                   pos=p-29+36,len=42-36),
                ]),
                pos=p-29+31,len=42-31),
            LatexCharsNode(parsed_context=lw.parsed_context,
                           chars='(',
                           pos=p-29+42,len=1),
            LatexMacroNode(
                parsed_context=lw.parsed_context,
                macroname='mbox',
                nodeargd=macrospec.ParsedMacroArgs([
                    LatexGroupNode(
                        parsed_context=lw.parsed_context,
                        nodelist=[
                            LatexCharsNode(parsed_context=lw.parsed_context,
                                           chars='some event if ',
                                           pos=p-29+49,len=63-49),
                            LatexMathNode(parsed_context=lw.parsed_context,
                                          displaytype='inline', nodelist=[
                                              LatexCharsNode(parsed_context=lw.parsed_context,
                                                             chars='x>0',
                                                             pos=p-29+65,len=3)
                                          ], delimiters=(r'\(', r'\)'),
                                          pos=p-29+63,len=70-63),
                        ],
                        pos=p-29+48,len=71-48)
                ]),
                pos=p-29+43,len=71-43),
            LatexCharsNode(parsed_context=lw.parsed_context,
                           chars=')=1',
                           pos=p-29+71,len=3),
        ]
        self.assertEqual(
            lw.get_latex_nodes(pos=p+2, stop_upon_closing_mathmode=r'\)'),
            ( good_parsed_structure ,
              p+2, latextext.rfind(r'\)') - (p+2) + 2 ) # len includes closing token
        )
        # check that first node is math mode node when parsing including the math mode start
        self.assertEqual(
            lw.get_latex_nodes(pos=p)[0][0],
            LatexMathNode(parsed_context=lw.parsed_context,
                          displaytype='inline',
                          nodelist=good_parsed_structure, delimiters=(r'\(', r'\)'),
                          pos=p, len=latextext.rfind(r'\)') + 2 - p)
        )

        
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

