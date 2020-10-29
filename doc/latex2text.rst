
Simple Latex to Text Converter
------------------------------

.. automodule:: pylatexenc.latex2text

.. contents:: Contents:
   :local:


Custom latex conversion rules: A simple template
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here is a short introduction on how to customize the way that
:py:class:`~pylatexenc.latex2text.LatexNodes2Text` converts LaTeX constructs
(macros, environments, and specials) to unicode text.  You can start off with
the example template below and adapt it to your needs.

Macros, environments and specials are parsed as corresponding node objects by
the parser (see :py:class:`pylatexenc.latexwalker.LatexMacroNode`,
:py:class:`pylatexenc.latexwalker.LatexEnvironmentNode`, and
:py:class:`pylatexenc.latexwalker.LatexSpecialsNode`).  These node objects are
then converted to unicode text by the
:py:class:`~pylatexenc.latex2text.LatexNodes2Text` object.

You can define new macros, environments, or specials, or override existing
definitions.  The definitions need to be provided twice: First, at the level of
the parser using the :py:mod:`~pylatexenc.macrospec` module, and second, at the
level of `latex2text`, to specify what the replacement strings are for the
different LaTeX constructs.

The following template is a simple illustrative example that implements the
following definitions:

  - A new macro ``\putinquotes[`][']{text}`` that puts its mandatory argument
    into quotes defined by the two optional arguments.  Let's say that the
    default quotes that are used are `````` and ``''``.  Another simpler macro
    ``\putindblquotes{text}`` is also provided for the sake of the example.

  - A new environment ``\begin{inquotes}[`]['] ... \end{inquotes}`` that does
    the same thing as its macro equivalent.  Another simpler environment
    ``\begin{indblquotes}...\end{indblquotes}`` is also provided for the sake of
    the example.

  - The usual LaTeX quote symbols `````, ``````, ``'``, and ``''`` for unicode
    quotes.  (See also issue #39)

Here is the code (see also docs for :py:class:`pylatexenc.macrospec.MacroSpec`,
:py:class:`pylatexenc.macrospec.EnvironmentSpec`,
:py:class:`pylatexenc.macrospec.SpecialsSpec`, as well as
:py:class:`pylatexenc.latex2text.MacroTextSpec`,
:py:class:`pylatexenc.latex2text.EnvironmentTextSpec`,
:py:class:`pylatexenc.latex2text.SpecialsTextSpec`):

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
