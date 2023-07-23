`latexnodes.parsers` — Latex Construct Parsers
==============================================

.. automodule:: pylatexenc.latexnodes.parsers
   :members:
   :no-undoc-members:
   :show-inheritance:

.. contents:: Contents:
   :local:


Parser base class
~~~~~~~~~~~~~~~~~

.. autoclass:: LatexParserBase
   :members:


General nodes
~~~~~~~~~~~~~

.. autoclass:: LatexGeneralNodesParser
   :members:
   :show-inheritance:

.. autoclass:: LatexSingleNodeParser
   :members:
   :show-inheritance:


Delimited expressions
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: LatexDelimitedExpressionParserInfo
   :members:

.. autoclass:: LatexDelimitedExpressionParser
   :members:
   :show-inheritance:

.. autoclass:: LatexDelimitedGroupParserInfo
   :members:
   :show-inheritance:

.. autoclass:: LatexDelimitedGroupParser
   :members:
   :show-inheritance:

.. autoclass:: LatexDelimitedExpressionParserOpeningDelimiterNotFound
   :members:
   :show-inheritance:

.. autoclass:: LatexMathParser
   :members:
   :show-inheritance:



Single expression parser
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: LatexExpressionParser
   :members:
   :show-inheritance:


Optional expression parser
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: LatexOptionalSquareBracketsParser
   :members:
   :show-inheritance:

.. autoclass:: LatexOptionalCharsMarkerParser
   :members:
   :show-inheritance:


Verbatim/literal expressions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: LatexVerbatimBaseParser
   :members:
   :show-inheritance:

.. autoclass:: LatexDelimitedVerbatimParser
   :members:
   :show-inheritance:

.. autoclass:: LatexVerbatimEnvironmentContentsParser
   :members:
   :show-inheritance:



Typical macro arguments
~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: get_standard_argument_parser

.. autoclass:: LatexStandardArgumentParser
   :members:
   :show-inheritance:

.. autoclass:: LatexCharsCommaSeparatedListParser
   :members:
   :show-inheritance:

.. autoclass:: LatexCharsGroupParser
   :members:
   :show-inheritance:

.. autoclass:: LatexTackOnInformationFieldMacrosParser
   :members:
   :show-inheritance:

