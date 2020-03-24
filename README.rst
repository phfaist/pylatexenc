pylatexenc
==========

Simple LaTeX parser providing latex-to-unicode and unicode-to-latex conversion

.. image:: https://img.shields.io/github/license/phfaist/pylatexenc.svg?style=flat
   :target: https://github.com/phfaist/pylatexenc/blob/master/LICENSE.txt

.. image:: https://img.shields.io/travis/phfaist/pylatexenc.svg?style=flat
   :target: https://travis-ci.org/phfaist/pylatexenc
   
.. image:: https://img.shields.io/pypi/v/pylatexenc.svg?style=flat
   :target: https://pypi.org/project/pylatexenc/

.. image:: https://img.shields.io/lgtm/alerts/g/phfaist/pylatexenc.svg?logo=lgtm&logoWidth=18&style=flat
   :target: https://lgtm.com/projects/g/phfaist/pylatexenc/alerts/


Unicode Text to LaTeX code
--------------------------

The ``pylatexenc.latexencode`` module provides a function ``unicode_to_latex()``
which converts a unicode string into LaTeX text and escape sequences. It should
recognize accented characters and most math symbols. A couple of switches allow
you to alter how this function behaves.

You can also run ``latexencode`` in command-line to convert plain unicode text
(from the standard input or from files given on the command line) into LaTeX
code, written on to the standard output. The Vim plug-in 
`vim-latexencode <https://github.com/Konfekt/vim-latexencode>`_
provides a corresponding command to operate on a given range.

Parsing LaTeX code & converting to plain text (unicode)
-------------------------------------------------------

The ``pylatexenc.latexwalker`` module provides a series of routines that parse
the LaTeX structure of given LaTeX code and returns a logical structure of
objects, which can then be used to produce output in another format such as
plain text.  This is not a replacement for a full (La)TeX engine, rather, this
module provides a way to parse a chunk of LaTeX code as mark-up code.

The ``pylatexenc.latex2text`` module builds up on top of
``pylatexenc.latexwalker`` and provides functions to convert given LaTeX code to
plain text with unicode characters.

You can also run ``latex2text`` in command-line to convert LaTeX input (either
from the standard input, or from files given on the command line) into plain
text written on the standard output.


Documentation
-------------

Full documentation is available at https://pylatexenc.readthedocs.io/.


License
-------

See LICENSE.txt (MIT License).

NOTE: See copyright notice and license information for file ``unicode.xml``
provided in ``unicode.xml.LICENSE``.  (The file ``unicode.xml`` was downloaded
from https://www.w3.org/2003/entities/2007xml/unicode.xml as linked from
https://www.w3.org/TR/xml-entity-names/#source.)
