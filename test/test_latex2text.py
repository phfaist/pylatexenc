import unittest

import re


from pylatexenc.latexwalker import LatexWalker
from pylatexenc.latex2text import LatexNodes2Text


class TestLatexNodes2Text(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestLatexNodes2Text, self).__init__(*args, **kwargs)
        self.maxDiff = None
    
    def test_basic(self):

        self.assertEqual(LatexNodes2Text().nodelist_to_text(LatexWalker(r'\textbf{A}').get_latex_nodes()[0]), 'A')

        latex = r'''\textit{hi there!} This is {\em an equation}:
\begin{equation}
    x + y i = 0
\end{equation}

where $i$ is the imaginary unit.
'''
        self.assertEqualUpToWhitespace(LatexNodes2Text().nodelist_to_text(LatexWalker(latex).get_latex_nodes()[0]),
                         r'''hi there! This is an equation:

    x + y i = 0

where i is the imaginary unit.
''')
        self.assertEqualUpToWhitespace(LatexNodes2Text(keep_inline_math=True).nodelist_to_text(LatexWalker(latex).get_latex_nodes()[0]),
                         '''hi there! This is an equation:

    x + y i = 0

where $i$ is the imaginary unit.
''')

        self.assertEqual(LatexNodes2Text().nodelist_to_text(LatexWalker(latex).get_latex_nodes()[0]),
                         LatexNodes2Text().latex_to_text(latex))
        
    def test_input(self):
        latex = r'''ABCDEF fdksanfkld safnkd anfklsa

\input{test_input_1.tex}

MORENKFDNSN'''
        correct_text = r'''ABCDEF fdksanfkld safnkd anfklsa

hi there! This is an equation:

    x + y i = 0

where i is the imaginary unit.

MORENKFDNSN'''

        l2t = LatexNodes2Text()
        l2t.set_tex_input_directory('.')

        self.assertEqualUpToWhitespace(l2t.nodelist_to_text(LatexWalker(latex).get_latex_nodes()[0]),
                                       correct_text)

        latex = r'''ABCDEF fdksanfkld safnkd anfklsa

\input{test_input_1}

MORENKFDNSN'''

        self.assertEqualUpToWhitespace(l2t.nodelist_to_text(LatexWalker(latex).get_latex_nodes()[0]),
                                       correct_text)

        latex = r'''ABCDEF fdksanfkld safnkd anfklsa

\input{../test_input_1}

MORENKFDNSN'''

        correct_text_unsafe = correct_text # as before
        correct_text_safe = r'''ABCDEF fdksanfkld safnkd anfklsa

MORENKFDNSN'''

        # make sure that the \input{} directive failed to include the file.
        l2t = LatexNodes2Text()
        l2t.set_tex_input_directory('./dummy')
        self.assertEqualUpToWhitespace(l2t.nodelist_to_text(LatexWalker(latex).get_latex_nodes()[0]),
                                       correct_text_safe)
        # but without the strict_input flag, it can access it.
        l2t.set_tex_input_directory('./dummy', strict_input=False)
        self.assertEqualUpToWhitespace(l2t.nodelist_to_text(LatexWalker(latex).get_latex_nodes()[0]),
                                       correct_text_unsafe)




    def assertEqualUpToWhitespace(self, a, b):
        a2 = re.sub(r'\s+', ' ', a).strip()
        b2 = re.sub(r'\s+', ' ', b).strip()
        self.assertEqual(a2, b2)




if __name__ == '__main__':
    unittest.main()
#

