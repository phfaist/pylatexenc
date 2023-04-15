Simple Parser for LaTeX Code
----------------------------

.. automodule:: pylatexenc.latexwalker

.. contents:: Contents:
   :local:


The main `LatexWalker` class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pylatexenc.latexwalker.LatexWalker
   :members:


.. autofunction:: pylatexenc.latexwalker.get_default_latex_context_db


Exception Classes
~~~~~~~~~~~~~~~~~

.. py:class:: pylatexenc.latexwalker.LatexWalkerError

   Moved to :py:class:`pylatexenc.latexnodes.LatexWalkerError`.

   .. deprecated:: 3.0

      Since Pylatexenc 3.0, this class now resides in the new module
      :py:mod:`pylatexenc.latexnodes`.  It is aliased in
      `pylatexenc.latexwalker` for backwards compatibility.

.. py:class:: pylatexenc.latexwalker.LatexWalkerParseError

   Moved to :py:class:`pylatexenc.latexnodes.LatexWalkerParseError`.

   .. deprecated:: 3.0

      Since Pylatexenc 3.0, this class now resides in the new module
      :py:mod:`pylatexenc.latexnodes`.  It is aliased in
      `pylatexenc.latexwalker` for backwards compatibility.

.. py:class:: pylatexenc.latexwalker.LatexWalkerEndOfStream

   Moved to :py:class:`pylatexenc.latexnodes.LatexWalkerEndOfStream`.

   .. deprecated:: 3.0

      Since Pylatexenc 3.0, this class now resides in the new module
      :py:mod:`pylatexenc.latexnodes`.  It is aliased in
      `pylatexenc.latexwalker` for backwards compatibility.


Data Node Classes
~~~~~~~~~~~~~~~~~

.. py:class:: pylatexenc.latexwalker.LatexNode

   Moved to :py:class:`pylatexenc.latexnodes.nodes.LatexNode`.

   .. deprecated:: 3.0

      Since Pylatexenc 3.0, this class now resides in the new module
      :py:mod:`pylatexenc.latexnodes.nodes`.  It is aliased in
      `pylatexenc.latexwalker` for backwards compatibility.

.. py:class:: pylatexenc.latexwalker.LatexCharsNode

   Moved to :py:class:`pylatexenc.latexnodes.nodes.LatexCharsNode`.

   .. deprecated:: 3.0

      Since Pylatexenc 3.0, this class now resides in the new module
      :py:mod:`pylatexenc.latexnodes.nodes`.  It is aliased in
      `pylatexenc.latexwalker` for backwards compatibility.

.. py:class:: pylatexenc.latexwalker.LatexGroupNode

   Moved to :py:class:`pylatexenc.latexnodes.nodes.LatexGroupNode`.

   .. deprecated:: 3.0

      Since Pylatexenc 3.0, this class now resides in the new module
      :py:mod:`pylatexenc.latexnodes.nodes`.  It is aliased in
      `pylatexenc.latexwalker` for backwards compatibility.

.. py:class:: pylatexenc.latexwalker.LatexCommentNode

   Moved to :py:class:`pylatexenc.latexnodes.nodes.LatexCommentNode`.

   .. deprecated:: 3.0

      Since Pylatexenc 3.0, this class now resides in the new module
      :py:mod:`pylatexenc.latexnodes.nodes`.  It is aliased in
      `pylatexenc.latexwalker` for backwards compatibility.

.. py:class:: pylatexenc.latexwalker.LatexMacroNode

   Moved to :py:class:`pylatexenc.latexnodes.nodes.LatexMacroNode`.

   .. deprecated:: 3.0

      Since Pylatexenc 3.0, this class now resides in the new module
      :py:mod:`pylatexenc.latexnodes.nodes`.  It is aliased in
      `pylatexenc.latexwalker` for backwards compatibility.

.. py:class:: pylatexenc.latexwalker.LatexEnvironmentNode

   Moved to :py:class:`pylatexenc.latexnodes.nodes.LatexEnvironmentNode`.

   .. deprecated:: 3.0

      Since Pylatexenc 3.0, this class now resides in the new module
      :py:mod:`pylatexenc.latexnodes.nodes`.  It is aliased in
      `pylatexenc.latexwalker` for backwards compatibility.

.. py:class:: pylatexenc.latexwalker.LatexSpecialsNode

   Moved to :py:class:`pylatexenc.latexnodes.nodes.LatexSpecialsNode`.

   .. deprecated:: 3.0

      Since Pylatexenc 3.0, this class now resides in the new module
      :py:mod:`pylatexenc.latexnodes.nodes`.  It is aliased in
      `pylatexenc.latexwalker` for backwards compatibility.

.. py:class:: pylatexenc.latexwalker.LatexMathNode

   Moved to :py:class:`pylatexenc.latexnodes.nodes.LatexMathNode`.

   .. deprecated:: 3.0

      Since Pylatexenc 3.0, this class now resides in the new module
      :py:mod:`pylatexenc.latexnodes.nodes`.  It is aliased in
      `pylatexenc.latexwalker` for backwards compatibility.


Parsing helpers
~~~~~~~~~~~~~~~

.. py:class:: pylatexenc.latexwalker.ParsingState

   .. deprecated:: 3.0

      Since Pylatexenc 3.0, this class now resides in the new module
      :py:mod:`pylatexenc.latexnodes`.  It is aliased in
      `pylatexenc.latexwalker` for backwards compatibility.

.. py:class:: pylatexenc.latexwalker.LatexToken

   .. deprecated:: 3.0

      Since Pylatexenc 3.0, this class now resides in the new module
      :py:mod:`pylatexenc.latexnodes`.  It is aliased in
      `pylatexenc.latexwalker` for backwards compatibility.



Legacy Macro Definitions (for `pylatexenc 1.x`)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autodata:: pylatexenc.latexwalker.MacrosDef

.. autodata:: pylatexenc.latexwalker.default_macro_dict
   :annotation:


