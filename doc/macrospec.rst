`macrospec` — Specifying definitions for the parser
---------------------------------------------------

.. automodule:: pylatexenc.macrospec
   :no-undoc-members:

.. contents:: Contents:
   :local:


Macro and environment definitions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pylatexenc.macrospec.MacroSpec
   :members:

.. autoclass:: pylatexenc.macrospec.EnvironmentSpec
   :members:

.. autoclass:: pylatexenc.macrospec.SpecialsSpec
   :members:


.. autofunction:: pylatexenc.macrospec.std_macro

.. autofunction:: pylatexenc.macrospec.std_environment

.. autofunction:: pylatexenc.macrospec.std_specials


Latex Context "Database"
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pylatexenc.macrospec.LatexContextDb
   :members:

.. autoclass:: pylatexenc.macrospec.ParsingStateDeltaExtendLatexContextDb
   :show-inheritance:
   :members:


Lower-level parsers for macro, environments, and specials
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You shouldn't have to use these directly.

.. autoclass:: pylatexenc.macrospec.LatexNoArgumentsParser
   :show-inheritance:
   :members:

.. autoclass:: pylatexenc.macrospec.LatexArgumentsParser
   :show-inheritance:
   :members:

.. autoclass:: pylatexenc.macrospec.LatexEnvironmentBodyContentsParserInfo
   :show-inheritance:
   :members:

.. autoclass:: pylatexenc.macrospec.LatexEnvironmentBodyContentsParser
   :show-inheritance:
   :members:

.. autoclass:: pylatexenc.macrospec.LatexMacroCallParser
   :show-inheritance:
   :members:

.. autoclass:: pylatexenc.macrospec.LatexEnvironmentCallParser
   :show-inheritance:
   :members:

.. autoclass:: pylatexenc.macrospec.LatexSpecialsCallParser
   :show-inheritance:
   :members:




Legacy (2.x) Macro arguments parsers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pylatexenc.macrospec.MacroStandardArgsParser
   :members:

.. autoclass:: pylatexenc.macrospec.ParsedMacroArgs
   :members:

.. autoclass:: pylatexenc.macrospec.VerbatimArgsParser
   :show-inheritance:
   :members:

.. autoclass:: pylatexenc.macrospec.ParsedVerbatimArgs
   :show-inheritance:
   :members:

