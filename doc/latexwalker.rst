
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
   :members:

.. autoclass:: pylatexenc.latexwalker.LatexNode
   :members:

.. autoclass:: pylatexenc.latexwalker.LatexCharsNode
   :show-inheritance:

.. autoclass:: pylatexenc.latexwalker.LatexGroupNode
   :show-inheritance:

.. autoclass:: pylatexenc.latexwalker.LatexCommentNode
   :show-inheritance:

.. autoclass:: pylatexenc.latexwalker.LatexMacroNode
   :show-inheritance:

.. autoclass:: pylatexenc.latexwalker.LatexEnvironmentNode
   :show-inheritance:

.. autoclass:: pylatexenc.latexwalker.LatexMathNode
   :show-inheritance:


