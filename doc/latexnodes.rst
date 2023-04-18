`latexnodes` — LaTeX Nodes Tree and Parsers
===========================================

.. automodule:: pylatexenc.latexnodes
   :no-undoc-members:

.. contents:: Contents:
   :local:



Parsing State
-------------

.. autoclass:: ParsingState
   :members:

.. autoclass:: ParsingStateDelta
   :members:

.. autoclass:: ParsingStateDeltaReplaceParsingState
   :members:

.. autoclass:: ParsingStateDeltaWalkerEvent
   :members:

.. autoclass:: ParsingStateDeltaEnterMathMode
   :members:

.. autoclass:: ParsingStateDeltaLeaveMathMode
   :members:



Latex Token
-----------

.. autoclass:: LatexToken
   :members:


Token Readers
-------------

.. autoclass:: LatexTokenReaderBase
   :members:

.. autoclass:: LatexTokenReader
   :members:

.. autoclass:: LatexTokenListTokenReader
   :members:



LaTeX Node Classes
------------------


.. autoclass:: pylatexenc.latexnodes.nodes.LatexNode
   :members:

.. autoclass:: pylatexenc.latexnodes.nodes.LatexNodeList
   :members:

.. autoclass:: pylatexenc.latexnodes.nodes.LatexNodesVisitor
   :members:


LaTeX Node Types
~~~~~~~~~~~~~~~~

.. autoclass:: pylatexenc.latexnodes.nodes.LatexCharsNode
   :members:

.. autoclass:: pylatexenc.latexnodes.nodes.LatexGroupNode
   :members:

.. autoclass:: pylatexenc.latexnodes.nodes.LatexCommentNode
   :members:

.. autoclass:: pylatexenc.latexnodes.nodes.LatexMacroNode
   :members:

.. autoclass:: pylatexenc.latexnodes.nodes.LatexEnvironmentNode
   :members:

.. autoclass:: pylatexenc.latexnodes.nodes.LatexSpecialsNode
   :members:

.. autoclass:: pylatexenc.latexnodes.nodes.LatexMathNode
   :members:




Arguments and Parsed Arguments
------------------------------

.. autoclass:: LatexArgumentSpec
   :members:

.. autoclass:: ParsedArguments
   :members:

.. autoclass:: ParsedArgumentsInfo
   :members:

.. autoclass:: SingleParsedArgumentInfo
   :members:


Nodes Collector
---------------

.. autoclass:: LatexNodesCollector
   :members:


Exception classes
-----------------

.. autoclass:: LatexWalkerError
   :members:

.. autoclass:: LatexWalkerLocatedError
   :members:

.. autoclass:: LatexWalkerLocatedErrorFormatter
   :members:

.. autoclass:: LatexWalkerParseError
   :members:

.. autoclass:: LatexWalkerNodesParseError
   :members:

.. autoclass:: LatexWalkerTokenParseError
   :members:

.. autoclass:: LatexWalkerEndOfStream
   :members:


Base classes
------------

.. autoclass:: CallableSpecBase
   :members:

.. autoclass:: LatexWalkerParsingStateEventHandler
   :members:

.. autoclass:: LatexWalkerBase
   :members:

.. autoclass:: LatexContextDbBase
   :members:



Parser Classes
--------------

.. toctree::
   :maxdepth: 2

   latexnodes.parsers
