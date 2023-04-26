import unittest
import logging



from pylatexenc.latexnodes._tokenreader import (
    LatexTokenReader
)

from pylatexenc.latexnodes import (
    LatexWalkerTokenParseError,
    LatexWalkerEndOfStream,
    LatexToken,
    ParsingState
)



class TestLatexTokenReader(unittest.TestCase):

    def test_simple_char(self):
        latextext = r"Some Chars"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)

        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='char', arg='S', pos=0, pos_end=1, pre_space=''))

    def test_simple_char_pre_space(self):
        pre_space = '   \t\n \t'
        latextext = pre_space+r"Some Chars"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)

        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='char', arg='S',
                                    pos=len(pre_space), pos_end=len(pre_space)+1,
                                    pre_space=pre_space))

    def test_macro(self):
        latextext = r"\somemacro and more stuff"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)

        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='macro', arg='somemacro',
                                    pos=0, pos_end=len(r'\somemacro '),
                                    pre_space='', post_space=' '))

    def test_macro_pre_space(self):
        pre_space = '   \t\n \t'
        latextext = pre_space+r"\somemacro and more stuff"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)

        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='macro', arg='somemacro',
                                    pos=len(pre_space)+0,
                                    pos_end=len(pre_space)+len(r'\somemacro '),
                                    pre_space=pre_space, post_space=' '))

    def test_comment(self):
        latextext = "% Comment here\n  more stuff"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)

        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='comment', arg=' Comment here',
                                    pos=0, pos_end=len('% Comment here\n  '),
                                    pre_space='', post_space='\n  '))

    def test_comment_altstartstring(self):
        latextext = "%!!COMMENT!! Comment here\n  more stuff"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext, comment_start='%!!COMMENT!!')

        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='comment', arg=' Comment here',
                                    pos=0, pos_end=len('%!!COMMENT!! Comment here\n  '),
                                    pre_space='', post_space='\n  '))


    def test_comment_with_pre_space(self):
        pre_space = '   \t\n \t'
        latextext = pre_space+"% Comment here\n  more stuff"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)

        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='comment', arg=' Comment here',
                                    pos=len(pre_space),
                                    pos_end=len(pre_space)+len('% Comment here\n  '),
                                    pre_space=pre_space, post_space='\n  '))

    def test_comment_with_endofinput(self):
        latextext = "% Comment here" # directly hits end of string

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)

        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='comment', arg=' Comment here',
                                    pos=0, pos_end=len('% Comment here'),
                                    pre_space='', post_space=''))

    def test_comment_with_par(self):
        latextext = "% Comment here\n\nBegin new paragraph here"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)

        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='comment', arg=' Comment here',
                                    pos=0, pos_end=len('% Comment here'),
                                    pre_space='', post_space=''))

    def test_group_delimiter_open(self):
        latextext = "{begin group here"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)

        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='brace_open', arg='{',
                                    pos=0, pos_end=1,
                                    pre_space=''))

    def test_group_delimiter_open_with_pre_space(self):
        pre_space = '   \t\n \t'
        latextext = pre_space+"{begin group here"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)

        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='brace_open', arg='{',
                                    pos=len(pre_space), pos_end=len(pre_space)+1,
                                    pre_space=pre_space))

    def test_group_delimiter_close(self):
        latextext = "} a braced group just ended here"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)

        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='brace_close', arg='}',
                                    pos=0, pos_end=1,
                                    pre_space=''))

    def test_group_delimiter_close_with_pre_space(self):
        pre_space = '   \t\n \t'
        latextext = pre_space+"} a braced group just ended here"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)

        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='brace_close', arg='}',
                                    pos=len(pre_space), pos_end=len(pre_space)+1,
                                    pre_space=pre_space))


    def test_beginenviron(self):
        latextext = r"\begin{environment}"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)

        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='begin_environment', arg='environment',
                                    pos=0, pos_end=len(latextext),
                                    pre_space=''))

    def test_beginenviron_tokenparseerror(self):
        latextext = r"\begin<forgot environment name!{z}"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)

        with self.assertRaises(LatexWalkerTokenParseError):
            tr.peek_token(ps)


    def test_beginmacro_confusing_name(self):
        latextext = r"\beginMacroWithConfusingName"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)

        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='macro', arg='beginMacroWithConfusingName',
                                    pos=0, pos_end=len(latextext),
                                    pre_space=''))

    def test_endenviron_simple(self):
        latextext = r"\end{myenvironment}"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)

        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='end_environment', arg='myenvironment',
                                    pos=0, pos_end=len(latextext),
                                    pre_space=''))


    def test_multiple_tokens_advances_and_stuff(self):
        
        latextext = \
            r'''Text \`accent and \textbf{bold text} and $\vec b$ vector \& also Fran\c cois
\begin{enumerate}[(i)]
\item Hi there!  % here goes a comment
\item[a] Hello!  @@@
     \end{enumerate}
\mymacro

New paragraph
'''
        tr = LatexTokenReader(latextext)
        
        ps = ParsingState(s=latextext)

        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='char', arg='T', pos=0, pos_end=1, pre_space=''))
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='char', arg='T', pos=0, pos_end=1, pre_space=''))

        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='char', arg='e', pos=1, pos_end=2, pre_space=''))

        p = latextext.find(r'\`')
        tr.move_to_pos_chars(p)
        
        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='macro', arg='`', pos=p, pos_end=p+2, pre_space=''))
        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='macro', arg='`', pos=p, pos_end=p+2, pre_space=''))
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='macro', arg='`', pos=p, pos_end=p+2, pre_space=''))

        p = latextext.find(r'\textbf')-1 # pre space
        tr.move_to_pos_chars(p)

        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='macro', arg='textbf', pos=p+1, pos_end=p+1+7,
                                    pre_space=' '))

        p = latextext.find(r'\vec') # post-space
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='macro', arg='vec', pos=p, pos_end=p+5,
                                    pre_space='', post_space=' '))
        p = latextext.find(r'\&')-1 # pre-space and *no* post-space
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='macro', arg='&', pos=p+1, pos_end=p+1+2,
                                    pre_space=' ', post_space=''))
        p = latextext.find(r'\begin')
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='begin_environment', arg='enumerate', pos=p,
                                    pos_end=p+len(r'\begin{enumerate}'), pre_space=''))
        p = latextext.find(r'@@@')+3 # pre space to \end
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='end_environment', arg='enumerate', pos=p+6,
                                    pos_end=p+6+len(r'\end{enumerate}'),
                                    pre_space='\n     '))
        p = latextext.find(r'%')-1
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='comment', arg=' here goes a comment', pos=p+1,
                                    pos_end=p+1+len('% here goes a comment\n'), pre_space=' ',
                                    post_space='\n'))
        p = latextext.find(r'{')
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='brace_open', arg='{', pos=p, pos_end=p+1,
                                    pre_space=''))
        p = latextext.find(r'}')
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='brace_close', arg='}', pos=p, pos_end=p+1,
                                    pre_space=''))

        p = latextext.find(r'\mymacro')
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.next_token(ps),
                         # no post_space because of paragraph
                         LatexToken(tok='macro', arg='mymacro', pos=p, pos_end=p+8,
                                    pre_space='', post_space=''))

        # paragraphs, by default, yield a single char token on their own (if
        # r'\n\n' is not declared as specials)
        p = latextext.find('\n\n')
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='char', arg='\n\n', pos=p,
                                    pos_end=p+2, pre_space=''))


    def test_newpar_tokens_1(self):

        latextext = """Abc    \n\n  z"""
        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        
        p = 3 # whitespace
        tr.move_to_pos_chars(p)
        self.assertEqual(
            tr.next_token(ps),
            LatexToken(tok='char', arg='\n\n', pos=7, pos_end=7+2, pre_space='    ')
        )

    def test_newpar_tokens_2(self):

        latextext = """Abc  \t \n   \t\nz"""
        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        
        p = 3 # whitespace
        tr.move_to_pos_chars(p)
        self.assertEqual(
            tr.next_token(ps),
            LatexToken(tok='char', arg='\n   \t\n', pos=7, pos_end=7+6, pre_space='  \t ')
        )

    def test_newpar_token_after_macro_1(self):

        latextext = """\\macroname\n  \n """
        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        
        p = 0
        tr.move_to_pos_chars(p)
        self.assertEqual(
            tr.next_token(ps),
            LatexToken(tok='macro', arg='macroname', pos=0, pos_end=10, pre_space='',
                       post_space='')
        )

    def test_newpar_token_after_macro_2(self):

        latextext = """\\macroname   \n  \n """
        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        
        p = 0
        tr.move_to_pos_chars(p)
        self.assertEqual(
            tr.next_token(ps),
            LatexToken(tok='macro', arg='macroname', pos=0, pos_end=13, pre_space='',
                       post_space='   ')
        )


    def test_nonewpar_token_after_comment_1(self):

        latextext = """% comment \n   xyz"""
        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        
        p = 0
        tr.move_to_pos_chars(p)
        self.assertEqual(
            tr.next_token(ps),
            LatexToken(tok='comment', arg=' comment ', pos=0, pos_end=14, pre_space='',
                       post_space='\n   ')
        )


    def test_newpar_token_after_comment_2(self):

        latextext = """% comment \n  \n """
        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        
        p = 0
        tr.move_to_pos_chars(p)
        self.assertEqual(
            tr.next_token(ps),
            LatexToken(tok='comment', arg=' comment ', pos=0, pos_end=10, pre_space='',
                       post_space='')
        )



    def test_no_environments(self):

        latextext = \
            r'''Text \`accent and \textbf{bold text} and $\vec b$ vector \& also Fran\c cois
\begin{enumerate}[(i)]
\item Hi there!  % here goes a comment
\item[a] Hello!  @@@
     \end{enumerate}
\mymacro

New paragraph
'''
        tr = LatexTokenReader(latextext)
        
        ps = ParsingState(s=latextext, enable_environments=False)

        p = latextext.find(r'\begin') - 1
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='macro', arg='begin', pos=p+1,
                                    pos_end=p+1+len(r'\begin'), pre_space='\n'))
        

        p = latextext.find(r'\end') - 4
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='macro', arg='end', pos=p+4,
                                    pos_end=p+4+len(r'\end'), pre_space='    '))
        
    def test_no_paragraphs(self):

        latextext = \
            r'''Text \`accent and \textbf{bold text} and $\vec b$ vector \& also Fran\c cois
\begin{enumerate}[(i)]
\item Hi there!  % here goes a comment
\item[a] Hello!  @@@
     \end{enumerate}
\mymacro

New paragraph
'''
        tr = LatexTokenReader(latextext)
        
        ps = ParsingState(s=latextext, enable_double_newline_paragraphs=False)

        p = latextext.find('\n\n')
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='char', arg='N', pos=p+2, pos_end=p+2+1,
                                    pre_space='\n\n'))
        
    def test_no_comments(self):

        latextext = \
            r'''Text \`accent and \textbf{bold text} and $\vec b$ vector \& also Fran\c cois
\begin{enumerate}[(i)]
\item Hi there!  % here goes a comment
\item[a] Hello!  @@@
     \end{enumerate}
\mymacro

New paragraph
'''
        tr = LatexTokenReader(latextext)
        
        ps = ParsingState(s=latextext, enable_comments=False)

        p = latextext.find(r' % here')
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='char', arg='%', pos=p+1, pos_end=p+1+1,
                                    pre_space=' '))
        
    def test_macro_alpha_chars(self):

        latextext = \
            r'''\zzz1234567890-haha_works! is a macro with the appropriate parsing state.'''

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext,
                          macro_alpha_chars=(
                              '0123456789'
                              'abcdefghijklmnopqrstuvwxyz'
                              'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                              '_+!-'
                          ))

        arg = 'zzz1234567890-haha_works!'
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='macro', arg=arg, pos=0, pos_end=1+len(arg)+1,
                                    pre_space='', post_space=' '))
        

    def test_forbidden_chars(self):

        latextext = r"% Here is a forbidden character."

        tr = LatexTokenReader(latextext)
        ps = ParsingState(enable_comments=False, forbidden_characters='%$')

        with self.assertRaises(LatexWalkerTokenParseError):
            _ = tr.peek_token(ps)


    def test_stuff_mathmodes(self):
        
        latextext = r"""
Here is an inline expression like $\vec{x} + \hat p$ and a display equation $$
   ax + b = y
$$ and another, with a subtle inner math mode:
\[ cx^2+z=-d\quad\text{if $x<0$} \]
And a final inline math mode \(\mbox{Prob}(\mbox{some event if $x>0$})=1\).
Some sneaky stuff can happen with consecutive math modes like here: $\zeta$$\gamma$.
"""

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        ps_mm = lambda mmdelim: ps.sub_context(in_math_mode=True,
                                               math_mode_delimiter=mmdelim)

        p = latextext.find(r'$')
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='mathmode_inline', arg='$', pos=p, pos_end=p+1,
                                    pre_space=''))
        p = latextext.find(r' \(')
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='mathmode_inline', arg=r'\(', pos=p+1, pos_end=p+1+2,
                                    pre_space=' '))
        p = latextext.find(r'\)')
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.peek_token(ps_mm(r'\(')),
                         LatexToken(tok='mathmode_inline', arg=r'\)', pos=p, pos_end=p+2,
                                    pre_space=''))
        # report closing '\)' also with incorrect parsing_state -- it's not the
        # tokenizer's job to report syntax errors
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='mathmode_inline', arg=r'\)', pos=p, pos_end=p+2,
                                    pre_space=''))

        p = latextext.find(r'$$')
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='mathmode_display', arg='$$', pos=p, pos_end=p+2,
                                    pre_space=''))

        p = latextext.find('\n'+r'\[')
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.peek_token(ps),
                         LatexToken(tok='mathmode_display', arg=r'\[', pos=p+1, pos_end=p+1+2,
                                    pre_space='\n'))
        # report opening math mode also with incorrect parsing_state -- it's not the
        # tokenizer's job to report syntax errors
        self.assertEqual(tr.peek_token(ps_mm(r'$')),
                         LatexToken(tok='mathmode_display', arg=r'\[', pos=p+1, pos_end=p+1+2,
                                    pre_space='\n'))

        p = latextext.find(r'\]')
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='mathmode_display', arg=r'\]', pos=p, pos_end=p+2,
                                    pre_space=''))

        p = latextext.find(r'$\zeta$$\gamma$')
        tr.move_to_pos_chars(p)
        self.assertEqual(tr.next_token(ps),
                         LatexToken(tok='mathmode_inline', arg='$', pos=p, pos_end=p+1,
                                    pre_space=''))
        tr.next_token(ps) # gobble macro "\zeta"
        self.assertEqual(tr.peek_token(ps), # wrong parsing state gives wrong "display"
                         LatexToken(tok='mathmode_display', arg='$$',
                                    pos=p+6, pos_end=p+6+2, pre_space=''))
        self.assertEqual(tr.next_token(ps_mm('$')), # should correctly detect "inline"
                         LatexToken(tok='mathmode_inline', arg='$',
                                    pos=p+6, pos_end=p+6+1, pre_space=''))
        self.assertEqual(tr.next_token(ps), # next opening "inline" math mode
                         LatexToken(tok='mathmode_inline', arg='$',
                                    pos=p+7, pos_end=p+7+1, pre_space=''))
        tr.next_token(ps) # gobble macro "\gamma"
        self.assertEqual(tr.next_token(ps), # should correctly detect "inline" again
                         LatexToken(tok='mathmode_inline', arg='$',
                                    pos=p+14, pos_end=p+14+1, pre_space=''))


    def test_get_token_mathmodes_dollardollar(self):
        
        # extra tests for this weird case of two dollars that follow each other.

        # pos counter:  |0        |10       |20       |30     |38
        latextext = r"""x$\dagger$$\dagger$$$A=B\mbox{$b=a$}$$"""

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)
        ps_mm = lambda mmdelim: ps.sub_context(in_math_mode=True,
                                               math_mode_delimiter=mmdelim)

        p = 1
        tr.move_to_pos_chars(p)
        self.assertEqual(
            tr.peek_token(parsing_state=ps),
            LatexToken(tok='mathmode_inline', arg='$', pos=p, pos_end=p+1, pre_space='')
        )
        p = 9
        tr.move_to_pos_chars(p)
        self.assertEqual(
            tr.peek_token(parsing_state=ps_mm('$')),
            LatexToken(tok='mathmode_inline', arg='$', pos=p, pos_end=p+1, pre_space='')
        )
        p = 10
        tr.move_to_pos_chars(p)
        self.assertEqual(
            tr.peek_token(parsing_state=ps),
            LatexToken(tok='mathmode_inline', arg='$', pos=p, pos_end=p+1, pre_space='')
        )
        p = 18
        tr.move_to_pos_chars(p)
        self.assertEqual(
            tr.peek_token(parsing_state=ps_mm('$')),
            LatexToken(tok='mathmode_inline', arg='$', pos=p, pos_end=p+1, pre_space='')
        )
        p = 19
        tr.move_to_pos_chars(p)
        self.assertEqual(
            tr.peek_token(parsing_state=ps),
            LatexToken(tok='mathmode_display', arg='$$', pos=p, pos_end=p+2, pre_space='')
        )
        p = 30
        tr.move_to_pos_chars(p)
        self.assertEqual(
            tr.peek_token(parsing_state=ps),
            LatexToken(tok='mathmode_inline', arg='$', pos=p, pos_end=p+1, pre_space='')
        )
        p = 34
        tr.move_to_pos_chars(p)
        self.assertEqual(
            tr.peek_token(parsing_state=ps_mm('$')),
            LatexToken(tok='mathmode_inline', arg='$', pos=p, pos_end=p+1, pre_space='')
        )
        p = 36
        tr.move_to_pos_chars(p)
        self.assertEqual(
            tr.peek_token(parsing_state=ps_mm('$$')),
            LatexToken(tok='mathmode_display', arg='$$', pos=p, pos_end=p+2, pre_space='')
        )
        
    
        # -----

        # test char-level access

    def test_charlevel_peek_next_chars(self):
        latextext = r"Some Chars"

        tr = LatexTokenReader(latextext)
        ps = ParsingState(s=latextext)

        self.assertEqual(tr.peek_chars(4, ps), "Some")
        self.assertEqual(tr.next_chars(4, ps), "Some")
        self.assertEqual(tr.peek_chars(1, ps), " ")
        self.assertEqual(tr.next_chars(1, ps), " ")
        self.assertEqual(tr.next_chars(1, ps), "C")
        self.assertEqual(tr.next_chars(1, ps), "h")
        self.assertEqual(tr.next_chars(1, ps), "a")
        self.assertEqual(tr.next_chars(1, ps), "r")
        self.assertEqual(tr.next_chars(1, ps), "s")

        with self.assertRaises(LatexWalkerEndOfStream):
            c = tr.next_chars(1, ps)
            




# ---

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
#
