`latexnodes` — LaTeX Nodes Tree and Parsers
===========================================

.. automodule:: pylatexenc.latexnodes
   :no-undoc-members:
   :show-inheritance:

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

.. autoclass:: ParsingStateDeltaChained
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



Node Classes
------------

.. toctree::
   :maxdepth: 2

   latexnodes.nodes


Parser Classes
--------------

.. toctree::
   :maxdepth: 2

   latexnodes.parsers
