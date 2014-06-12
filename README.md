pylatexenc
==========

Python library for encoding unicode to latex and for parsing LaTeX to generate unicode
text.


Unicode Text to LaTeX code
--------------------------

`latexencode.py` provides a function `utf8tolatex()` which, as its name suggests, converts
a unicode string into LaTeX text and escape sequences. It should recognize accented
characters and most math symbols. A couple of switches allow you to alter how this
function behaves.

You can also run `latexencode.py` as a script to convert plain unicode text (from the
standard input or from files given on the command line) into LaTeX code, written on to the
standard output.


Parsing LaTeX code & converting to plain text (unicode)
-------------------------------------------------------

`latexwalker.py` provides a series of routines (in particular, start with
`get_latex_nodes()`), that parse the LaTeX structure of given LaTeX code and returns a
logical structure of objects, which can then be used to produce output in another format
such as plain text.

`latex2text.py` builds up on top of `latexwalker.py`, and provides functions to convert
given LaTeX code to plain text with unicode characters.

Note that you can also run `latex2text.py` as a script to convert LaTeX input (either from
the standard input, or from files given on the command line) into plain text, written on
the standard output.
