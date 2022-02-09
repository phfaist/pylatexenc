What's new in `pylatexenc 3`
============================

Wow, lots of stuff. I don't know where to start.

The good news is, your code depending on `pylatexenc 2` should run without any
chagnes.  You might get some deprecation warnings which you can silence using
python's warnings filter management (e.g., ``python -W
'ignore::DeprecationWarnings'`` or using :py:func:`warnings.simplefilter`)




A couple things to look out for
-------------------------------

- If you created a `LatexContextDb` database from scratch, you might suddenly
  get errors about unknown macros.  The default initialization for unknown
  macro, environment and specials specification objects for `LatexContextDb`
  was, and remains, `None`.  What has changed is the interpretation of this
  `None`: Now, the latex walker (more precisely,
  :py:class:`LatexNodesCollector`) reports an error, whereas previously, the
  parser would simply assume the macro doesn't accept any arguments.  To restore
  the earlier behavior, simply set the spec objects for unknown
  macro/environment/specials in your latex context db object::

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

- Node lists are now encapsulated in a :py:class:`LatexNodeList`.  It behaves
  very much like a list in all respects (indexing, slicing, etc.), except that
  it does not satisfy ``isinstance(nodelist, list)``.  If you relied on such
  tests, you'll need to update them to the liking of ``isinstance(nodelist,
  (LatexNodeList, list))``.
