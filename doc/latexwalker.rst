
Simple Parser for LaTeX Code
----------------------------

.. automodule:: pylatexenc.latexwalker



The main `LatexWalker` class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pylatexenc.latexwalker.LatexWalker
   :members:


Exception Classes
~~~~~~~~~~~~~~~~~

.. autoclass:: pylatexenc.latexwalker.LatexWalkerError

.. autoclass:: pylatexenc.latexwalker.LatexWalkerParseError

.. autoclass:: pylatexenc.latexwalker.LatexWalkerEndOfStream


Macro Definitions
~~~~~~~~~~~~~~~~~

.. autoclass:: pylatexenc.latexwalker.MacrosDef

.. autodata:: pylatexenc.latexwalker.default_macro_dict
   :annotation:


Data Node Classes and Helpers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pylatexenc.latexwalker.LatexToken

.. autoclass:: pylatexenc.latexwalker.LatexNode

.. autoclass:: pylatexenc.latexwalker.LatexCharsNode

.. autoclass:: pylatexenc.latexwalker.LatexGroupNode

.. autoclass:: pylatexenc.latexwalker.LatexCommentNode

.. autoclass:: pylatexenc.latexwalker.LatexMacroNode

.. autoclass:: pylatexenc.latexwalker.LatexEnvironmentNode

.. autoclass:: pylatexenc.latexwalker.LatexMathNode


