pylatexenc
==========

Simple LaTeX parser providing latex-to-unicode and unicode-to-latex conversion

.. image:: https://img.shields.io/github/license/phfaist/pylatexenc.svg?style=flat
   :target: https://github.com/phfaist/pylatexenc/blob/master/LICENSE.txt

.. image:: https://img.shields.io/pypi/v/pylatexenc.svg?style=flat
   :target: https://pypi.org/project/pylatexenc/

Python: ≥ 3.4 or ≥ 2.7. The library is designed to be as backwards-compatible as
reasonably possible and is able to run on old python verisons should it be
necessary. (Use the setup.py script directly if you have python<3.7, poetry
doesn't seem to work with old python versions.)

**NEW (4/2023)**: *PYLATEXENC 3.0alpha* is in pre-release on PyPI.  See `new features
and major changes <https://pylatexenc.readthedocs.io/en/latest/new-in-pylatexenc-3/>`_.
The `documentation <https://pylatexenc.readthedocs.io/en/latest/>`_ is still
incomplete, and the new APIs are still subject to changes.  The code is meant
to be as backwards compatible as is reasonably possible.  Feel free to try it
out & submit feedback!


Unicode Text to LaTeX code
--------------------------

The ``pylatexenc.latexencode`` module provides a function ``unicode_to_latex()``
which converts a unicode string into LaTeX text and escape sequences. It should
recognize accented characters and most math symbols. A couple of switches allow
you to alter how this function behaves.

You can also run ``latexencode`` in command-line to convert plain unicode text
(from the standard input or from files given on the command line) into LaTeX
code, written on to the standard output.

A third party plug-in for Vim
`vim-latexencode <https://github.com/Konfekt/vim-latexencode>`_
by `@Konfekt <https://github.com/Konfekt>`_
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

To build the documentation manually, run::

  > poetry install --with=builddoc
  > cd doc/
  doc> poetry run make html


License
-------

See LICENSE.txt (MIT License).

NOTE: See copyright notice and license information for file
``tools/unicode.xml`` provided in ``tools/unicode.xml.LICENSE``.  (The file
``tools/unicode.xml`` was downloaded from
https://www.w3.org/2003/entities/2007xml/unicode.xml as linked from
https://www.w3.org/TR/xml-entity-names/#source.)


Javascript Library
------------------

Some core parts of this library can be transcribed to JavaScript.  This feature
is used (and was developed for) my `Flexible Latex-like Markup
project <https://github.com/phfaist/flm>`_.  See the *js-transcrypt/* folder and
its `README file <js-transcrypt/README.md>`_.
