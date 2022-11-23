LaTeX Nodes Tree and Parsers
============================

.. automodule:: pylatexenc.latexnodes

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



Token Readers
-------------

.. autoclass:: LatexToken
   :members:

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




Parsed Arguments
----------------

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

.. autoclass:: LatexWalkerParseError
   :members:

.. autoclass:: LatexWalkerParseErrorFormatter
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

.. automodule:: pylatexenc.latexnodes.parsers
   :members:


.. autoclass:: LatexParserBase
   :members:


General Nodes
~~~~~~~~~~~~~

.. autoclass:: LatexGeneralNodesParser
   :members:

.. autoclass:: LatexSingleNodeParser
   :members:


Delimited Expressions
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: LatexDelimitedExpressionParserInfo
   :members:

.. autoclass:: LatexDelimitedExpressionParser
   :members:

.. autoclass:: LatexDelimitedGroupParserInfo
   :members:

.. autoclass:: LatexDelimitedGroupParser
   :members:

.. autoclass:: LatexDelimitedExpressionParserOpeningDelimiterNotFound
   :members:

.. autoclass:: LatexMathParser
   :members:



Other Types of Expressions
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: LatexExpressionParser
   :members:

.. autoclass:: LatexOptionalSquareBracketsParser
   :members:

.. autoclass:: LatexOptionalCharsMarkerParser
   :members:

.. autoclass:: LatexStandardArgumentParser
   :members:

.. autofunction:: get_standard_argument_parser

.. autoclass:: LatexCharsCommaSeparatedListParser
   :members:

.. autoclass:: LatexCharsGroupParser
   :members:

.. autoclass:: LatexVerbatimBaseParser
   :members:

.. autoclass:: LatexDelimitedVerbatimParser
   :members:

.. autoclass:: LatexVerbatimEnvironmentContentsParser
   :members:
