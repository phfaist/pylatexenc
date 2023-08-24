# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2019 Philippe Faist
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

# Internal module. Internal API may move, disappear or otherwise change at any
# time and without notice.

from __future__ import print_function, unicode_literals


from .. import _util

from ..latexnodes import ParsingStateDelta


import logging
logger = logging.getLogger(__name__)



_autogen_category_prefix = '__lctxdb_cat_'


### BEGINPATCH_UNIQUE_OBJECT_ID
fn_unique_object_id = id
### ENDPATCH_UNIQUE_OBJECT_ID



class LatexContextDb(object):
    r"""
    Store a database of specifications of known macros, environments, and other
    latex specials.  This might be, e.g., how many arguments a macro accepts, or
    how to determine the text representation of a macro or environment.

    When used with :py:class:`pylatexenc.latexwalker.LatexWalker`, the
    specifications describe mostly rules for parsing arguments of macros and
    environments, and which sequences of characters to consider as "latex
    specials".  Specifications for macros, environments, and other specials are
    stored as :py:class:`MacroSpec`, :py:class:`EnvironmentSpec`, and
    :py:class:`SpecialsSpec` instances, respectively.
    When used with :py:class:`pylatexenc.latex2text.LatexNodes2Text`, the
    specifications for macros, environments, and other specials are stored as
    :py:class:`pylatexenc.latex2text.MacroTextSpec` ,
    :py:class:`pylatexenc.latex2text.EnvironmentTextSpec`, and
    :py:class:`pylatexenc.latex2text.SpecialsTextSpec` instances, respectively.

    In fact, the objects stored in this database may be of any type, except that
    macro specifications must have an attribute `macroname`, environment
    specifications must have an attribute `environmentname`, and specials
    specification must have an attribute `specials_chars`.

    The `LatexContextDb` instance is meant to be (pseudo-)immutable.  Once
    constructed and all the definitions added with
    :py:meth:`add_context_category()`, one should refrain from modifying it
    directly after providing it to, e.g., a
    :py:class:`~pylatexenc.latexwalker.LatexWalker` object.  The reason is that
    the latex walker keeps track of what the latex context was when parsing
    nodes, and modifying the context will modify that stored information, too.
    Instead of being tempted to modify the object, create a new one with
    :py:meth:`filtered_context()`.
    
    To (partially) ensure that the database isn't modified while it is being
    used, it can be "frozen" with the method :py:meth:`freeze()`.  This method
    simply sets a flag and will cause methods like `add_context_category()` to
    raise an error.  You can always construct new context category instances
    based on the present one by calling :py:meth:`filtered_context()` or
    :py:meth:`extended_with()`.

    See :py:func:`pylatexenc.latexwalker.get_default_latex_context_db()` for the
    default latex context for `latexwalker` with a default collection of known
    latex macros and environments.
    See :py:func:`pylatexenc.latex2text.get_default_latex_context_db()` for the
    default latex context for `latex2text` with a set of text replacements for a
    collection of known macros and environments.

    The constructor doesn't accept any meaningful arguments.
    """
    def __init__(self, **kwargs):
        super(LatexContextDb, self).__init__(**kwargs)

        self.category_list = []
        self.d = {}

        self.frozen = False

        # these chainmaps' list of maps mirror the category_list item for item.
        self.lookup_chain_maps = {
            'macros': _util.ChainMap({}),
            'environments': _util.ChainMap({}),
            'specials': _util.ChainMap({}),
        }

        self.unknown_macro_spec = None
        self.unknown_environment_spec = None
        self.unknown_specials_spec = None

        self._autogen_category_counter = 0


    def freeze(self):
        r"""
        Disable future changes to the information contained in this object.

        LatexWalker objects expect that context category databases are
        immutable, they don't change.  Building a context database object,
        however, might require several calls to add_context_category, etc.

        So what the latexwalker does is that it `freeze()`\ s the context db
        object to prevent future changes.
        """
        self.frozen = True

    
    def __repr__(self):
        return "<LatexContextDb {:#x}{}>".format(
            fn_unique_object_id(self),
            ("" if self.frozen else " unfrozen")
        )


    def add_context_category(self, category, macros=[], environments=[], specials=[],
                             prepend=False, insert_before=None, insert_after=None):
        r"""
        Register a category of macro and environment specifications in the context
        database.

        The category name `category` must not already exist in the database.  If
        `category` is `None`, then a unique automatically-generated and internal
        category name is used.

        The argument `macros` is an iterable (e.g., a list) of macro
        specification objects.  The argument `environments` is an iterable
        (e.g., a list) of environment spec objects.  Similarly, the `specials`
        argument is an iterable of latex specials spec instances.

        If you specify `prepend=True`, then macro and environment lookups will
        prioritize this category over other categories.  Categories are normally
        searched for in the order they are registered to the database; if you
        specify `prepend=True`, then the new category is prepended to the
        existing list so that it is searched first.

        If `insert_before` is not `None`, then it must be a string; the
        definitions are inserted in the category list immediately before the
        given category name, or at the beginning of the list if the given
        category doesn't exist.  If `insert_after` is not `None`, then it must
        be a string; the definitions are inserted in the category list
        immediately after the given category name, or at the end of the list if
        the given category doesn't exist.

        You may only specify one of `prepend=True`, `insert_before='...'` or
        `insert_after='...'`.
        """

        if self.frozen:
            raise RuntimeError("You attempted to modify a frozen LatexContextDb object.")

        if category is not None and category.startswith(_autogen_category_prefix):
            raise ValueError("Category name {} is unfortunately reserved for internal use"
                             .format(category))

        if category is None:
            _autogen_category_counter, category = self._get_new_autogen_category()
            self._autogen_category_counter = _autogen_category_counter + 1

        if category in self.category_list:
            raise ValueError("Category {} is already registered in the context database"
                             .format(category))

        # ensure only one of these options is set
        if len([ x for x in (prepend, insert_before, insert_after) if x ]) > 1:
            raise TypeError("add_context_category(): You may only specify one of "
                            "prepend=True, insert_before=... or insert_after=...")

        category_dicts = {
            'macros': dict( (m.macroname, m) for m in macros ),
            'environments': dict( (e.environmentname, e) for e in environments ),
            'specials': dict( (s.specials_chars, s) for s in specials ),
        }

        logger.debug("Adding category context in db: %r", category_dicts)

        if prepend:
            insert_fn = lambda listobj, item: listobj.insert(0, item)
        elif insert_before:
            if insert_before in self.category_list:
                i = self.category_list.index(insert_before)
            else:
                i = 0
            insert_fn = lambda listobj, item: listobj.insert(i, item)
        elif insert_after:
            if insert_after in self.category_list:
                i = self.category_list.index(insert_after) + 1 # insert after found category
            else:
                i = len(self.category_list)
            insert_fn = lambda listobj, item: listobj.insert(i, item)
        else:
            insert_fn = lambda listobj, item: listobj.append(item)

        insert_fn(self.category_list, category)
        for which in ('macros', 'environments', 'specials',):
            insert_fn(self.lookup_chain_maps[which].maps, category_dicts[which])

        self.d[category] = category_dicts

        
    def set_unknown_macro_spec(self, macrospec):
        r"""
        Set the macro spec to use when encountering a macro that is not in the
        database.
        """
        if self.frozen:
            raise RuntimeError("You attempted to modify a frozen LatexContextDb object.")
        self.unknown_macro_spec = macrospec

    def set_unknown_environment_spec(self, environmentspec):
        r"""
        Set the environment spec to use when encountering a LaTeX environment that
        is not in the database.
        """
        if self.frozen:
            raise RuntimeError("You attempted to modify a frozen LatexContextDb object.")
        self.unknown_environment_spec = environmentspec

    def set_unknown_specials_spec(self, specialsspec):
        r"""
        Set the latex specials spec to use when encountering a LaTeX environment
        that is not in the database.
        
        ### FIXME: When is an "unknown specials" encountered ??
        """
        if self.frozen:
            raise RuntimeError("You attempted to modify a frozen LatexContextDb object.")
        self.unknown_specials_spec = specialsspec

    def categories(self):
        r"""
        Return a list of valid category names that are registered in the current
        database context.
        """
        return list(self.category_list)

    def get_macro_spec(self, macroname, raise_if_not_found=False):
        r"""
        Look up a macro specification by macro name.  The macro name is searched for
        in all categories one by one and the first match is returned.

        Returns a macro spec instance that matches the given `macroname`.  If
        the macro name was not found, we return the default macro specification
        set by :py:meth:`set_unknown_macro_spec()` or `None` if no such spec was
        set.  
        """
        # for cat in self.category_list:
        #     # search categories in the given order
        #     if macroname in self.d[cat]['macros']:
        #         return self.d[cat]['macros'][macroname]
        try:
            return self.lookup_chain_maps['macros'][macroname]
        except KeyError:
            if raise_if_not_found:
                raise
            return self.unknown_macro_spec
    
    def get_environment_spec(self, environmentname, raise_if_not_found=False):
        r"""
        Look up an environment specification by environment name.  The environment
        name is searched for in all categories one by one and the first match is
        returned.

        Returns the environment spec.  If the environment name was not found, we
        return the default environment specification set by
        :py:meth:`set_unknown_environment_spec()` or `None` if no such spec was
        set.
        """
        # for cat in self.category_list:
        #     # search categories in the given order
        #     if environmentname in self.d[cat]['environments']:
        #         return self.d[cat]['environments'][environmentname]
        try:
            return self.lookup_chain_maps['environments'][environmentname]
        except KeyError:
            if raise_if_not_found:
                raise
            return self.unknown_environment_spec

    def get_specials_spec(self, specials_chars, raise_if_not_found=False):
        r"""
        Look up a "latex specials" specification by character sequence.  The
        sequence name is searched for in all categories one by one and the first
        match is returned.

        If you are parsing a chunk of LaTeX code, you should use
        :py:meth:`test_for_specials()` instead.  Unlike
        :py:meth:`test_for_specials()`, :py:meth:`get_specials_spec()` returns
        the first match regardless of matched length.  [Rationale: we only need
        to worry about matching the longest specials sequence when parsing LaTeX
        code.  Calling `get_specials_spec()` means one has already parsed the
        sequence and one is looking up additional specs on it.]

        Returns the specials spec.  If the latex specials was not found, we
        return the default latex specials specification set by
        :py:meth:`set_unknown_specials_spec()` or `None` if no such spec was
        set.
        """
        # for cat in self.category_list:
        #     # search categories in the given order
        #     if specials_chars in self.d[cat]['specials']:
        #         return self.d[cat]['specials'][specials_chars]
        try:
            return self.lookup_chain_maps['specials'][specials_chars]
        except KeyError:
            if raise_if_not_found:
                raise
            return self.unknown_specials_spec

    def test_for_specials(self, s, pos, parsing_state=None):
        r"""
        Test the given position in the string for any LaTeX specials.  The lookup
        proceeds by searching for in all categories one by one and the first
        match is returned, except that the longest match accross all categories
        is returned.  For instance, a match of '``' in a later category will
        take precedence over a match of '`' in a earlier-searched category.

        Returns a specials spec instance, or `None` if no specials are detected
        at the position `pos`.
        """
        best_match_len = 0
        best_match_s = None

        # logger.debug("test_for_specials() category_list=%r", self.category_list)

        for cat in self.category_list:
            # search categories in the given order
            for specials_chars in self.d[cat]['specials'].keys():
                # logger.debug("test_for_specials() ‘%s...’ testing %r",
                #              s[pos:pos+4], specials_chars)
                if len(specials_chars) > best_match_len and s.startswith(specials_chars, pos):
                    best_match_s = self.d[cat]['specials'][specials_chars]
                    best_match_len = len(specials_chars)
                    # logger.debug("        -> best_match_s=%s, best_match_len=%s",
                    #              best_match_s, best_match_len)

        return best_match_s # this is None if no match

    def iter_macro_specs(self, categories=None):
        r"""
        Yield the macro specs corresponding to all macros in the given categories.

        If `categories` is `None`, then the known macro specs from all
        categories are provided in one long iterable sequence.  Otherwise,
        `categories` should be a list or iterable of category names (e.g.,
        'latex-base') of macro specs to return.

        The macro specs from the different categories specified are concatenated
        into one long sequence which is yielded spec by spec.
        """

        if categories is None:
            categories = self.category_list

        for c in categories:
            if c not in self.category_list:
                raise ValueError(
                    "Invalid latex macro spec db category: {!r} (Expected one of {!r})"
                    .format(c, self.category_list)
                )
            for spec in self.d[c]['macros'].values():
                yield spec

    def iter_environment_specs(self, categories=None):
        r"""
        Yield the environment specs corresponding to all environments in the given
        categories.

        If `categories` is `None`, then the known environment specs from all
        categories are provided in one long iterable sequence.  Otherwise,
        `categories` should be a list or iterable of category names (e.g.,
        'latex-base') of environment specs to return.

        The environment specs from the different categories specified are
        concatenated into one long sequence which is yielded spec by spec.
        """

        if categories is None:
            categories = self.category_list

        for c in categories:
            if c not in self.category_list:
                raise ValueError(
                    "Invalid latex environment spec db category: {!r} (Expected one of {!r})"
                    .format(c, self.category_list)
                )
            for spec in self.d[c]['environments'].values():
                yield spec

    def iter_specials_specs(self, categories=None):
        r"""
        Yield the specials specs corresponding to all environments in the given
        categories.

        If `categories` is `None`, then the known specials specs from all
        categories are provided in one long iterable sequence.  Otherwise,
        `categories` should be a list or iterable of category names (e.g.,
        'latex-base') of specials specs to return.

        The specials specs from the different categories specified are
        concatenated into one long sequence which is yielded spec by spec.
        """

        if categories is None:
            categories = self.category_list

        for c in categories:
            if c not in self.category_list:
                raise ValueError(
                    "Invalid latex environment spec db category: {!r} (Expected one of {!r})"
                    .format(c, self.category_list)
                )
            for spec in self.d[c]['specials'].values():
                yield spec


### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE

    def filter_context(self, *args, **kwargs):
        r"""
        .. deprecated:: 3.0

           The `filter_context()` method was renamed `filtered_context()`.  The
           method signature is unchanged.
        """
        _util.pylatexenc_deprecated_3("`LatexContextDb.filter_context()` was renamed to "
                                      "`filtered_context()`.")
        return self.filtered_context(*args, **kwargs)

### END_PYLATEXENC2_LEGACY_SUPPORT_CODE


    def filtered_context(self, keep_categories=[], exclude_categories=[],
                         keep_which=[], create_class=None):
        r"""
        Return a new :py:class:`LatexContextDb` instance where we only keep
        certain categories of macro and environment specifications.
        
        If `keep_categories` is set to a nonempty list, then the returned
        context will not contain any definitions that do not correspond to the
        specified categories.

        If `exclude_categories` is set to a nonempty list, then the returned
        context will not contain any definitions that correspond to the
        specified categories.

        It is explicitly fine to have category names in `keep_categories` and
        `exclude_categories` that don't exist in the present object
        (cf. :py:meth:`categories()`).

        The argument `keep_which`, if non-empty, specifies which definitions to
        keep.  It should be a subset of the list ['macros', 'environments',
        'specials'].
        
        The returned context will make a copy of the dictionaries that store the
        macro and environment specifications, but the specification classes (and
        corresponding argument parsers) might correspond to the same instances.
        I.e., the returned context is not a full deep copy.

        .. versionadded:: 3.0

           The `filter_context()` method was renamed `filtered_context()` in
           `pylatexenc 3.0`.
        """
        
        if create_class is None:
            create_class = self.__class__

        new_context = create_class()

        new_context.unknown_macro_spec = self.unknown_macro_spec
        new_context.unknown_environment_spec = self.unknown_environment_spec
        new_context.unknown_specials_spec = self.unknown_specials_spec

        keep_macros = not keep_which or 'macros' in keep_which
        keep_environments = not keep_which or 'environments' in keep_which
        keep_specials = not keep_which or 'specials' in keep_which

        for cat in self.category_list:
            if keep_categories and cat not in keep_categories:
                continue
            if exclude_categories and cat in exclude_categories:
                continue

            # include this category
            new_context.add_context_category(
                cat,
                macros=self.d[cat]['macros'].values() if keep_macros else [],
                environments=self.d[cat]['environments'].values() if keep_environments else [],
                specials=self.d[cat]['specials'].values() if keep_specials else [],
            )

        return new_context

    def _get_new_autogen_category(self):
        while True:
            category = _autogen_category_prefix + str(self._autogen_category_counter)
            if category not in self.category_list:
                break
            self._autogen_category_counter += 1
            
        return (self._autogen_category_counter, category)

    def extended_with(self, category=None, macros=None, environments=None, specials=None,
                      create_class=None, **kwargs):
        r"""
        Creates a new context category by adding a new category before all others.
        (Behaves as you'd imagine immediately after issuing a
        ``\newcommand\newmacro{...}``).

        If `category` is `None`, then an internal category name is used.

        (Note: If `category` is `None`, it might happen that a new category
        isn't actually created; if the current object's first category is
        already an internally-created one, that one is used.)
        """

        if category in self.category_list:
            raise ValueError

        if not self.frozen:
            raise RuntimeError(
                "You can only call extended_with() on frozen objects, because extended "
                "objects keep references to the original objects' data"
            )

        if create_class is None:
            create_class = self.__class__

        new_context = create_class()

        new_context.unknown_macro_spec = \
            kwargs.pop('unknown_macro_spec', self.unknown_macro_spec)
        new_context.unknown_environment_spec = \
            kwargs.pop('unknown_environment_spec', self.unknown_environment_spec)
        new_context.unknown_specials_spec = \
            kwargs.pop('unknown_specials_spec', self.unknown_specials_spec)

        if macros is None: macros = []
        if environments is None: environments = []
        if specials is None: specials = []

        new_category_dicts = {
            'macros': dict( (m.macroname, m) for m in macros ),
            'environments': dict( (e.environmentname, e) for e in environments ),
            'specials': dict( (s.specials_chars, s) for s in specials ),
        }

        new_context.category_list = self.category_list

        # actual changes in macros/environments/specials, not only
        # unknown_macro_spec=...

        # logger.debug("extended_with() extending context, category=%r, category_list=%r",
        #              category, self.category_list)

        if category is None and len(self.category_list) > 0 \
           and self.category_list[0].startswith(_autogen_category_prefix):
            # no need to create new category, can merge with our current
            # internally-named one.
            cat = self.category_list[0]
            dd = dict(self.d)
            d_cat = dd[cat]
            # logger.debug("extended_with() DEBUG: d_cat=%r, new_category_dicts=%r",
            #              d_cat, new_category_dicts)
            # Make copies of macros, environments, specials dicts to update them
            # with the new definitions.  Avoid the construction dict(olddict,
            # **new_stuff) because it doesn't seem to work with Transcrypt.
            d_cat = dict(
                macros=dict(d_cat['macros']),
                environments=dict(d_cat['environments']),
                specials=dict(d_cat['specials']),
            )
            d_cat['macros'].update(new_category_dicts['macros'])
            d_cat['environments'].update(new_category_dicts['environments'])
            d_cat['specials'].update(new_category_dicts['specials'])
            # logger.debug("extended_with() DEBUG: updated d_cat is now = %r ; None is %r",
            #              d_cat, None)
            dd[cat] = d_cat
            new_context.d = dd
            new_context.lookup_chain_maps = {
                'macros': _util.ChainMap(
                    d_cat['macros'],
                    *self.lookup_chain_maps['macros'].maps[1:]
                ),
                'environments': _util.ChainMap(
                    d_cat['environments'],
                    *self.lookup_chain_maps['environments'].maps[1:]
                ),
                'specials': _util.ChainMap(
                    d_cat['specials'],
                    *self.lookup_chain_maps['specials'].maps[1:]
                ),
            }
            new_context._autogen_category_counter = self._autogen_category_counter

            # need to be frozen to prevent edits here affecting edits in the original object
            new_context.frozen = True
            logger.debug(
                "Latex Context DB %r ---> extended with %r [extend auto-cat %s] ---> %r",
                self,
                {k: list(v.keys()) for k, v in new_category_dicts.items()},
                cat,
                new_context
            )
            return new_context

        if category is None:
            a, category = self._get_new_autogen_category()
            new_context._autogen_category_counter = a + 1
        else:
            new_context._autogen_category_counter = self._autogen_category_counter

        # creating new category
        dd = dict(self.d)
        dd[category] = new_category_dicts

        new_context.category_list = [category] + self.category_list

        new_context.d = dd

        # logger.debug('new context category_list = %r\n        d = %r',
        #              new_context.category_list, new_context.d)

        # these chainmaps' list of maps mirror the category_list item for item.
        new_context.lookup_chain_maps = {
            'macros':
                self.lookup_chain_maps['macros']
                .new_child(new_category_dicts['macros']),
            'environments':
                self.lookup_chain_maps['environments']
                .new_child(new_category_dicts['environments']),
            'specials':
                self.lookup_chain_maps['specials']
                .new_child(new_category_dicts['specials']),
        }

        new_context.frozen = True

        logger.debug(
            "Latex Context DB %r ---> extended with %r [new cat %s] ---> %r",
            self,
            {k: list(v.keys()) for k, v in new_category_dicts.items()},
            category,
            new_context
        )

        #logger.debug("extended_with(): new context is = %r", new_context)
        return new_context





class ParsingStateDeltaExtendLatexContextDb(ParsingStateDelta):
    r"""
    In addition to setting attributes, this parsing state delta object can also
    extend the latex context.

    .. py:attribute::  extend_latex_context

       A dictionary with keys 'macros', 'environments', 'specials', as accepted
       by :py:meth:`LatexContextDb.add_context_category()`.
        
       Can be used along with set_parsing_state; in which case definitions are
       added on top of the parsing state change.
    """
    def __init__(self, extend_latex_context, **kwargs):
        super(ParsingStateDeltaExtendLatexContextDb, self).__init__(
            _fields=('extend_latex_context', 'set_attributes',),
            **kwargs
        )
        self.extend_latex_context = extend_latex_context

    def get_updated_parsing_state(self, parsing_state, latex_walker):

        if self.extend_latex_context:

            if self.set_attributes:
                set_attributes = self.set_attributes
            else:
                set_attributes = {}

            latex_context = parsing_state.latex_context.extended_with(
                category=None,
                **self.extend_latex_context
            )

            return parsing_state.sub_context(
                latex_context=latex_context,
                **set_attributes
            )
        elif self.set_attributes:
            return parsing_state.sub_context(
                **self.set_attributes
            )

        return parsing_state

