`macrospec` — Specifying definitions for the parser
---------------------------------------------------

.. automodule:: pylatexenc.macrospec

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


Macro arguments parser
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pylatexenc.macrospec.MacroStandardArgsParser
   :members:

.. autoclass:: pylatexenc.macrospec.ParsedMacroArgs
   :members:


Argument parser for verbatim LaTeX constructs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pylatexenc.macrospec.VerbatimArgsParser
   :show-inheritance:
   :members:

.. autoclass:: pylatexenc.macrospec.ParsedVerbatimArgs
   :show-inheritance:
   :members:


Latex Context "Database"
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pylatexenc.macrospec.LatexContextDb
   :members:
