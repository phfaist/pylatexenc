.. pylatexenc documentation master file, created by
   sphinx-quickstart on Mon Apr 24 16:32:21 2017.
   You can adapt this file completely to your liking,
   but it should at least contain the root `toctree` directive.

Welcome to pylatexenc's documentation!
======================================

[pylatexenc version: |version|]  (:doc:`What's new? <changes>`)

A simple LaTeX parser providing latex-to-unicode and unicode-to-latex conversion.

Quick example::

    >>> from pylatexenc.latex2text import LatexNodes2Text
    >>> latex = r"""\textbf{Hi there!} Here is \emph{an equation}:
    ... \begin{equation}
    ...     \zeta = x + i y
    ... \end{equation}
    ... where $i$ is the imaginary unit.
    ... """
    >>> print(LatexNodes2Text().latex_to_text(latex))
    Hi there! Here is an equation:

        ζ = x + i y
    
    where i is the imaginary unit.

And the other way around::

    >>> from pylatexenc.latexencode import unicode_to_latex
    >>> text = "À votre santé!"
    >>> print(unicode_to_latex(text))
    \`A votre sant\'e!


You can also use these utilities directly in command line, e.g.::

    $ echo 'À votre santé!' | latexencode
    \`A votre sant\'e!


Documentation
=============

Which module do I want?
-----------------------

- :py:mod:`pylatexenc.latex2text` — convert LaTeX code to plain (unicode) text.
  This is what you want if you have LaTeX and you'd like to read it, index it,
  or feed it to something that doesn't understand LaTeX.

- :py:mod:`pylatexenc.latexencode` — the other direction: convert unicode text
  into LaTeX code and escape sequences.

- :py:mod:`pylatexenc.latexwalker` — parse LaTeX code into a tree of node
  objects, if you'd like to inspect or transform the LaTeX structure yourself.

- :py:mod:`pylatexenc.latexnodes` and :py:mod:`pylatexenc.macrospec` — the
  lower-level parsing layer that the modules above are built on: node classes,
  the token reader, the library of parser objects, and the specifications that
  tell the parser how many arguments each macro or environment takes.  Most
  users never need to touch these directly; you'll come here when you want to
  teach the parser about macros it doesn't know, or to write your own parser
  for a custom LaTeX construct.

The two command-line tools ``latex2text`` and ``latexencode`` expose the first
two modules directly from your shell.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   latex2text
   latexencode
   latexwalker
   latexnodes
   macrospec
   changes


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
