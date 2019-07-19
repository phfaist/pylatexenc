Simple Parser for LaTeX Code
----------------------------

.. automodule:: pylatexenc.latexwalker


The main `LatexWalker` class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pylatexenc.latexwalker.LatexWalker
   :members:



.. autofunction:: pylatexenc.latexwalker.get_default_latex_context_db


Exception Classes
~~~~~~~~~~~~~~~~~

.. autoclass:: pylatexenc.latexwalker.LatexWalkerError

.. autoclass:: pylatexenc.latexwalker.LatexWalkerParseError

.. autoclass:: pylatexenc.latexwalker.LatexWalkerEndOfStream


Data Node Classes
~~~~~~~~~~~~~~~~~

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


Parsing helpers
~~~~~~~~~~~~~~~

.. autoclass:: pylatexenc.latexwalker.ParsingContext
   :members:

.. autoclass:: pylatexenc.latexwalker.LatexToken
   :members:



Legacy Macro Definitions (for `pylatexenc 1.x`)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autodata:: pylatexenc.latexwalker.MacrosDef

.. autodata:: pylatexenc.latexwalker.default_macro_dict
   :annotation:


