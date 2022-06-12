============
Changes
============


pylatexenc 3.0alpha
===================

(Still in active development.)

.. toctree::
   :maxdepth: 1

   new-in-pylatexenc-3

- see in particular the :ref:`list of changes that might affect existing code
  <new-in-pylatexenc-3-possible-pitfall-changes>` if you're using some more
  advanced features of `pylatexenc`.




pylatexenc 2.10
===============

- Added :py:class:`pylatexenc.latexencode.PartialLatexToLatexEncoder` which can
  help to avoid double-escaping some existing LaTeX expressions in the string
  that we want to LaTeX-encode.

- The :py:class:`pylatexenc.latexencode.UnicodeToTextConversionRule` now has a
  :py:attr:`~pylatexenc.latexencode.UnicodeToTextConversionRule.replacement_text_protection`
  field which can be used to override the default `replacement_text_protection`
  set on a :py:class:`pylatexenc.latexencode.UnicodeToTextEncoder` object.  Also
  the `replacement_text_protection` fields accept an arbitrary callable object.

- added some known macro definitions for :py:mod:`~pylatexenc.latexwalker` and
  :py:mod:`~pylatexenc.latex2text`, such as ``\definecolor`` and ``\textcolor``.

- Bug fixes (including :issue:`57`)

pylatexenc 2.9
==============

- Bug fixes (including issues :issue:`49`, :issue:`51`, :pr:`52`, :pr:`53`,
  :pr:`54`)

pylatexenc 2.8
==============

- `latex2text` module: Basic support for array and matrix environments.
  Matrices are represented inline, in the form ``[ a b; c d ]``.

- `latexencode` bugfix (issue :issue:`44`)

pylatexenc 2.7
==============

- Bug fix: the parser now disambiguates ``$$`` as either a display math
  delimiter or two inline math delimiters as in ``$a$$b$`` (issue :issue:`43`)

pylatexenc 2.6
==============

- In `latex2text`:

  + Bug fix: default behavior of the `strict_latex_spaces` option in the
    :py:class:`pylatexenc.latex2text.LatexNodes2Text()` constructor

  + fix ``\le``, ``\ge``, ``\leqslant``, ``\geqslant`` (issue :issue:`41`)

  + reorganized the default latex symbol categories


pylatexenc 2.5
==============

- `latex2text`: Add support for ``\mathbb{}``, ``\mathbf{}`` and some friends
  (issue :issue:`40`)

pylatexenc 2.4
==============

- Bug fixes in how `latex2text` attempts to recover from parse errors in
  tolerant mode

pylatexenc 2.3
==============

- Minor bug fixes in `latex2text`


pylatexenc 2.2
==============

Version 2.2 brings a few minor bug fixes and improvements over version 2.1:

- `pylatexenc.latex2text` supports more LaTeX symbols

- `latex2text` and `latexwalker` command-line utilities accept a new `-c` option
  where you can directly specify LaTeX code

- minor bug fixes


pylatexenc 2.1
==============

Version 2.1 brings a few minor bug fixes to version 2.0.


pylatexenc 2.0
==============

.. toctree::
   :maxdepth: 1

   new-in-pylatexenc-2

- see in particular the :ref:`list of changes that might affect existing code
  <new-in-pylatexenc-2-api-changes>` if you're using some advanced features of
  `pylatexenc`.


pylatexenc 1.x
==============

See description of updates and changes on the `github releases page
<https://github.com/phfaist/pylatexenc/releases>`_.
