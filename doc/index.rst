.. pylatexenc documentation master file, created by
   sphinx-quickstart on Mon Apr 24 16:32:21 2017.
   You can adapt this file completely to your liking,
   but it should at least contain the root `toctree` directive.

Welcome to pylatexenc's documentation!
======================================

This package provides simple and heuristic conversion of LaTeX to unicode and
vice versa.

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

    >>> from pylatexenc.latexencode import utf8tolatex
    >>> text = "À votre santé!"
    >>> print(utf8tolatex(text))
    {\`A} votre sant{\'e}!


You can also use these utilities directly in command line, e.g.::

    $ echo 'À votre santé!' | latexencode
    {\`A} votre sant{\'e}!


Documentation
=============


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   latexwalker
   macrospec
   latex2text
   latexencode
   changes


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
