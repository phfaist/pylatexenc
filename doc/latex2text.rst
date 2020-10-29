
Simple Latex to Text Converter
------------------------------

.. automodule:: pylatexenc.latex2text

.. contents:: Contents:
   :local:


Custom latex conversion rules: A quick reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is a short introduction and example on how to customize the way that
:py:class:`~pylatexenc.latex2text.LatexNodes2Text` converts LaTeX constructs (macros,
environments, and specials) to unicode text.

Macros, environments and specials are parsed as corresponding node objects by
the parser (see :py:class:`pylatexenc.latexwalker.LatexMacroNode`,
:py:class:`pylatexenc.latexwalker.LatexEnvironmentNode`, and
:py:class:`pylatexenc.latexwalker.LatexSpecialsNode`).  These node objects are
then converted to unicode text by the
:py:class:`~pylatexenc.latex2text.LatexNodes2Text` object.

You can define new macros, environments, or specials, or override existing
definitions, using the :py:mod:`~pylatexenc.macrospec` module.  The catch is
that you will probably have to do that twice: once for the parser, once for the
converter to text.

As an illustrative example, say you would like to support the following LaTeX
definitions:

  - A new macro ``\putinquotes[`][']{c}`` that puts its mandatory argument into
    quotes defined by the two optional arguments.  Let's say that the default
    quotes that are used are `````` and ``''``.

  - A new environment ``\begin{inquotes}[`]['] ... \end{inquotes}`` that does
    the same thing as its macro equivalent.

  - The usual LaTeX quote symbols `````, ``````, ``'``, and ``''`` for unicode
    quotes.  (See also issue #39)

You would write:

.. literalinclude:: example_latex2text_custom_quotes.py
   :language: python


Latex to Text Converter Class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pylatexenc.latex2text.LatexNodes2Text
   :members:


.. autofunction:: pylatexenc.latex2text.get_default_latex_context_db



Define replacement texts
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pylatexenc.latex2text.MacroTextSpec
   :members:

.. autoclass:: pylatexenc.latex2text.EnvironmentTextSpec
   :members:

.. autoclass:: pylatexenc.latex2text.SpecialsTextSpec
   :members:



Obsolete members
~~~~~~~~~~~~~~~~

.. autofunction:: pylatexenc.latex2text.EnvDef

.. autofunction:: pylatexenc.latex2text.MacroDef


.. autodata:: pylatexenc.latex2text.default_env_dict
   :annotation:

.. autodata:: pylatexenc.latex2text.default_macro_dict
   :annotation:

.. autodata:: pylatexenc.latex2text.default_text_replacements
   :annotation:
