
Encode Unicode to LaTeX
-----------------------

.. automodule:: pylatexenc.latexencode


Unicode to Latex Conversion
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: pylatexenc.latexencode.UnicodeToLatexEncoder
   :members:

.. autofunction:: pylatexenc.latexencode.unicode_to_latex


Specifying conversion rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autodata:: pylatexenc.latexencode.RULE_DICT

.. autodata:: pylatexenc.latexencode.RULE_REGEX

.. autodata:: pylatexenc.latexencode.RULE_CALLABLE



.. autoclass:: pylatexenc.latexencode.UnicodeToLatexConversionRule
   :members:



.. autofunction:: pylatexenc.latexencode.get_builtin_conversion_rules

.. autofunction:: pylatexenc.latexencode.get_builtin_uni2latex_dict


Compatibility with Pylatexenc 1.x
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: pylatexenc.latexencode.utf8tolatex

.. autodata:: pylatexenc.latexencode.utf82latex
