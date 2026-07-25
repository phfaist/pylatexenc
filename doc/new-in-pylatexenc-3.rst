What's new in `pylatexenc 3`
============================

Wow, a *lot* of stuff has changed in the `latexwalker` and `macrospec` modules.
There's even a new `latexnodes` module.  I don't know where to start!

The good news is, if you're simply using the latex-to-unicode and
unicode-to-latex conversion tools, your code depending on `pylatexenc 2` should
run without any chagnes.  You might get some deprecation warnings which you can
silence using python's warnings filter management (e.g., ``python -W
'ignore::DeprecationWarnings'`` or using :py:func:`warnings.simplefilter`)

The `latex2text` and `latexencode` modules have barely changed.

- New parsing mechanism in a new `latexnodes` module — everything gets delegated
  to "parser objects" that are specialized in parsing a specific construct.  See
  :py:class:`pylatexenc.latexnodes.parsers.LatexParserBase`.

- The parser has new enhanced handling of macro, environment, and specials
  arguments.  Arguments can be named for easier lookup when traversing the node
  tree.

- **WARNING**: While in *alpha* stage, I'm expecting that the new APIs might
  still change.  I'll try to remain as backwards-compatible as possible with
  `pylatexenc 2.x` but new APIs introduced in the `3.0alphaX` versions might
  still change a bit until they are finalized.

- Lists of latex node objects
  (:py:class:`~pylatexenc.latexnodes.nodes.LatexNode`) are now wrapped in a
  special object for node lists →
  :py:class:`pylatexenc.latexnodes.nodes.LatexNodeList`.
  
- so much more ... ...

- The `len` attribute in node objects is replaced by a `pos_end` attribute.  The
  `len` attribute can still be accessed as a read-only computed attribute for
  compatibility with existing code using pylatexenc 2.



.. _new-in-pylatexenc-3-possible-pitfall-changes:

A couple things to look out for
-------------------------------

- If you created a :py:class:`~pylatexenc.macrospec.LatexContextDb` database
  from scratch, you might suddenly get errors about unknown macros.  The default
  initialization for unknown macro, environment and specials specification
  objects for :py:class:`~pylatexenc.macrospec.LatexContextDb` was, and remains,
  `None`.  What has changed is the interpretation of this `None`: Now, the latex
  walker (more precisely,
  :py:class:`~pylatexenc.latexnodes.LatexNodesCollector`) reports an error,
  whereas previously, the parser would simply assume the macro doesn't accept
  any arguments.  To restore the earlier behavior, simply set the spec objects
  for unknown macro/environment/specials in your latex context db object::

    latex_context_db = macrospec.LatexContextDb()
    # ...
    latex_context_db.add_context_category( ... )
    # ...
    latex_context_db.set_unknown_macro_spec(macrospec.MacroSpec(''))
    latex_context_db.set_unknown_environment_spec(macrospec.EnvironmentSpec(''))
    #
    # unknown macros and environemnts are now accepted and are assumed
    # not to take any arguments
    #

- Node lists are now encapsulated in a
  :py:class:`~pylatexenc.latexnodes.nodes.LatexNodeList`.  It behaves very much
  like a list in all respects (indexing, slicing, etc.), except that it does not
  satisfy ``isinstance(nodelist, list)``.  If you relied on such tests, you'll
  need to update them to the liking of ``isinstance(nodelist, (LatexNodeList,
  list))``.



Some bug fixes in behavior
--------------------------

- The :py:mod:`~pylatexenc.latex2text` 's ``\paragraph{...}`` output
  was fixed to produce simply ``"Paragraph Title\nBody"``.  (Pylatexenc 2
  didn't get the newlines quite right.)

- The ``verbatim`` and ``lstlisting`` environments no longer report the newline
  that immediately follows ``\begin{...}`` as part of their contents, mirroring
  what LaTeX itself does.

- An unterminated ``lstlisting`` environment no longer loses its parsed
  arguments in tolerant parsing mode; ``nodeargd`` used to be `None` there.


- You might notice other fixes that we forgot to include here.


Details that v3 might get different
-----------------------------------

Pylatexenc v3's behavior might get some minor things a bit differently.  We don't
expect these to lead to downstream issues, but we're listing the ones we're aware
of here for completeness:

- The :py:mod:`~pylatexenc.latexencode` module no longer uses the dotless
  ``\i`` command when encoding the accented characters ‘ì’, ‘í’, ‘î’ and ‘ï’
  (U+00EC–U+00EF), producing ``\'i`` instead of ``{\'\i}``.  This follows
  a long-standing change in LaTeX where ``\i`` is no longer needed for such
  accented characters.  (If you prefer to keep braces around your replacement,
  remember to use a "latex replacement protection" option, see
  :py:attr:`pylatexenc.latexencode.UnicodeToLatexEncoder.replacement_latex_protection`.)


- You might notice other differences that we forgot to include here.
