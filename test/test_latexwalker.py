import unittest
import sys
import logging

if sys.version_info.major > 2:
    def unicode(string): return string
    basestring = str

from pylatexenc.latexwalker import (
    MacrosDef, LatexWalker, LatexToken, LatexCharsNode, LatexGroupNode, LatexCommentNode,
    LatexMacroNode, LatexEnvironmentNode, LatexMathNode, LatexWalkerParseError
)


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
        p = latextext.find(r'$')
        self.assertEqual(lw.get_token(pos=p),
                         LatexToken(tok='char', arg='$', pos=p, len=1, pre_space=''))

        lw2 = LatexWalker(latextext, keep_inline_math=True)
        p = latextext.find(r'$')
        self.assertEqual(lw2.get_token(pos=p),
                         LatexToken(tok='mathmode_inline', arg='$', pos=p, len=1, pre_space=''))


    def test_get_latex_expression(self):
        
        latextext = r'''Text and \`accent and \textbf{bold text} and $\vec b$ more stuff for Fran\c cois
\begin{enumerate}[(i)]
\item Hi there!  % here goes a comment
\item[a] Hello!  @@@
     \end{enumerate}
'''
        lw = LatexWalker(latextext, tolerant_parsing=True)

        self.assertEqual(lw.get_latex_expression(pos=0),
                         (LatexCharsNode('T'),0,1,))
        p = latextext.find(r'\`')
        self.assertEqual(lw.get_latex_expression(pos=p),
                         (LatexMacroNode('`',None,[]),p,2,))
        p = latextext.find(r'{')
        self.assertEqual(lw.get_latex_expression(pos=p),
                         (LatexGroupNode([LatexCharsNode('bold text')]),p,11,))
        p = latextext.find(r'%') # check: correctly skips comments
        self.assertEqual(lw.get_latex_expression(pos=p),
                         (LatexMacroNode('item',None,[]),
                          p+len('% here goes a comment\n'),5,))
        p = latextext.find(r'%') # check: correctly skips comments
        self.assertEqual(lw.get_latex_expression(pos=p),
                         (LatexMacroNode('item',None,[]),
                          p+len('% here goes a comment\n'),5,))
        # check correct behavior if directly on brace close
        p = latextext.find(r'}')
        self.assertEqual(lw.get_latex_expression(pos=p, strict_braces=True),
                         (LatexCharsNode(''),p,0,))
        lw2 = LatexWalker(latextext, tolerant_parsing=False)
        self.assertEqual(lw2.get_latex_expression(pos=p, strict_braces=False),
                         (LatexCharsNode(''),p,0,))
        with self.assertRaises(LatexWalkerParseError):
            dummy = lw2.get_latex_expression(pos=p, strict_braces=True)


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
                         (LatexGroupNode([LatexCharsNode('Lemma 3')]),p,9,))


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
        self.assertEqual(lw.get_latex_braced_group(pos=p, brace_type='{'),
                         (LatexGroupNode([LatexMacroNode('itshape',None,[],macro_post_space=' '),
                                          LatexCharsNode('some italic text')]),
                          p+1, len('{\itshape some italic text}'),))
        self.assertEqual(lw.get_latex_braced_group(pos=p+1, brace_type='{'),
                         (LatexGroupNode([LatexMacroNode('itshape',None,[],macro_post_space=' '),
                                          LatexCharsNode('some italic text')]),
                          p+1, len('{\itshape some italic text}'),))
        p = latextext.find(r'[(i)]')
        self.assertEqual(lw.get_latex_braced_group(pos=p, brace_type='['),
                         (LatexGroupNode([LatexCharsNode('(i)')]), p, 5,))
        
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
        self.assertEqual(lw.get_latex_environment(pos=p, environmentname='enumerate'),
                         (LatexEnvironmentNode('enumerate', [
                             LatexCharsNode('\n'),
                             LatexMacroNode('item',None,[],macro_post_space=' '),
                             LatexCharsNode('Hi there!  '),
                             LatexCommentNode(' here goes a comment'),
                             LatexMacroNode('item',LatexGroupNode([LatexCharsNode('a')]),[]),
                             LatexCharsNode(' Hello!  @@@\n     ')
                         ], [LatexGroupNode([LatexCharsNode('(i)')])], []),
                          p, latextext.find(r'\end{enumerate}')+len(r'\end{enumerate}')-p,))
        self.assertEqual(lw.get_latex_environment(pos=p),
                         (LatexEnvironmentNode('enumerate', [
                             LatexCharsNode('\n'),
                             LatexMacroNode('item',None,[],macro_post_space=' '),
                             LatexCharsNode('Hi there!  '),
                             LatexCommentNode(' here goes a comment'),
                             LatexMacroNode('item',LatexGroupNode([LatexCharsNode('a')]),[]),
                             LatexCharsNode(' Hello!  @@@\n     ')
                         ], [LatexGroupNode([LatexCharsNode('(i)')])], []),
                          p, latextext.find(r'\end{enumerate}')+len(r'\end{enumerate}')-p,))
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
        self.assertEqual(lw.get_latex_nodes(pos=p), ([
            LatexCharsNode('Also: '),
            LatexGroupNode([ LatexMacroNode('itshape', None, [], macro_post_space=' '),
                             LatexCharsNode('some italic text') ]),
            LatexCharsNode('.')
            ], p, len(latextext)-p-1)) # trailing '\n' is not included

        p = latextext.find('Also: {')+len('Also: {') # points inside right after open brace
        self.assertEqual(lw.get_latex_nodes(pos=p, stop_upon_closing_brace='}'), ([
            LatexMacroNode('itshape', None, [], macro_post_space=' '),
            LatexCharsNode('some italic text')
            ], p, len('\itshape some italic text}')))

        # test our own macro lists etc.
        pindeed = latextext.find('Indeed thanks to')
        lineindeed = latextext[pindeed:latextext.find('\n', pindeed)]
        lw2 = LatexWalker(lineindeed, tolerant_parsing=False,
                          macro_dict={'cite': MacrosDef('cite',False,4)})
        self.assertEqual(lw2.get_latex_nodes(pos=0), ([
            LatexCharsNode('Indeed thanks to '),
            LatexMacroNode('cite', None, [
                LatexCharsNode('['),LatexCharsNode('L'),
                LatexCharsNode('e'),LatexCharsNode('m'),
                ]),
            LatexCharsNode('ma 3]'),
            LatexGroupNode([LatexCharsNode('Author')]),
            LatexCharsNode(', we know that...'),
            ], 0, len(lineindeed)))
       
        
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
            self.fail(u"get_latex_nodes() raised LatexWalkerParseError, but it shouldn't have in "
                      u"tolerant parsing mode!\n"+unicode(e))
            


# more test data

def get_test_latex_data_with_possible_inconsistencies():
    return r"""\
\documentclass[11pt,a4paper]{article}

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

