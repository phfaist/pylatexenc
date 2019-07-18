Change Log
----------

New in pylatexenc 2.0
~~~~~~~~~~~~~~~~~~~~~

Changes that are not directly source compatible:

- objects that specify macros and environments (`MacrosDef` / `MacroDef`), etc.

- `keep_inline_math=` option was removed in `latexwalker` and replaced in
  `latex2text` (see `Issue #14
  <https://github.com/phfaist/pylatexenc/issues/14>`_).  Replace idioms::

    LatexNodes2Text(keep_inline_math=True).latex_to_text(..., keep_inline_math=True)
    -->
    LatexNodes2Text(math_mode='verbatim').latex_to_text(...)

    LatexNodes2Text(keep_inline_math=True).latex_to_text(..., keep_inline_math=False)
    -->
    LatexNodes2Text(math_mode='with-delimiters').latex_to_text(...)

    LatexNodes2Text(keep_inline_math=False).latex_to_text(..., keep_inline_math=True|False)
    -->
    LatexNodes2Text(math_mode='text').latex_to_text(...)
