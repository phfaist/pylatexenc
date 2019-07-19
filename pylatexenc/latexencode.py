# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2018 Philippe Faist
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

"""
The `latexencode` module provides a set of routines that allows you to
convert a unicode string to LaTeX escape sequences.  See
:py:class:`UnicodeToLatexEncoder`.
"""

from __future__ import print_function, absolute_import, unicode_literals

import unicodedata
import logging
import sys
import functools 

if sys.version_info.major > 2:
    def unicode(string): return string
    basestring = str
    # use MappingProxyType for keeping
    from types import MappingProxyType as _MappingProxyType
    # inspect function argument names
    from inspect import getfullargspec
else:
    _MappingProxyType = dict
    # inspect function argument names -- simulate getfullargspec with getargspec (argh...)
    from inspect import getargspec as getfullargspec

logger = logging.getLogger(__name__)



from ._uni2latexmap import uni2latex as _uni2latex
from . import _util


def get_builtin_uni2latex_dict():
    r"""
    Return a dictionary that contains the default collection of known LaTeX
    escape sequences for unicode characters.

    The keys of the dictionary are integers that correspond to unicode code
    points (i.e., `ord(char)`).  The values are the corresponding LaTeX
    replacement strings.

    The returned dictionary may not be modified.  To alter the default behavior,
    you should specify custom rules to :py:class:`UnicodeToLatexEncoder`.
    """
    return _MappingProxyType(_uni2latex)




RULE_DICT = 0
r"""
Indicates a rule type that is a dictionary of unicode point values to
replacement strings. See :py:class:`UnicodeToLatexConversionRule`.

.. versionadded:: 2.0

   This member was introduced in pylatexenc version 2.0.
"""

RULE_REGEX = 1
r"""
Indicates a rule type that is a list (or iterable) of pairs
`(compiled_regular_expression, replacement_string)`.  See
:py:class:`UnicodeToLatexConversionRule`.

.. versionadded:: 2.0

   This member was introduced in pylatexenc version 2.0.
"""

RULE_CALLABLE = 2
r"""
Indicates a rule type that is a custom callable.  See
:py:class:`UnicodeToLatexConversionRule`.

.. versionadded:: 2.0

   This member was introduced in pylatexenc version 2.0.
"""


class UnicodeToLatexConversionRule:
    r"""
    Specify a rule how to convert unicode characters into LaTeX escapes.

    .. py:attribute:: rule_type
    
       One of :py:data:`RULE_DICT`, :py:data:`RULE_REGEX`, or
       :py:data:`RULE_CALLABLE`.

    .. py:attribute:: rule

       A specification of the rule itself.  The `rule` attribute is an object
       that depends on what `rule_type` is set to.  See below.

    Constructor syntax::
    
        UnicodeToLatexConversionRule(RULE_XXX, <...>)
        UnicodeToLatexConversionRule(rule_type=RULE_XXX, rule=<...>)

    Note that you can get some built-in rules via the
    :py:func:`get_bulitin_conversion_rule()` function::

        conversion_rules = get_builtin_conversion_rules('defaults') # all defaults


    Rules types:
    
      - `RULE_DICT`: If `rule_type` is `RULE_DICT`, then `rule` should be a
        dictionary whose keys are integers representing unicode code points
        (e.g., `0x210F`), and whose values are corresponding replacement
        strings.  See :py:func:`get_builtin_uni2latex_dict()` for an example.

      - `RULE_REGEX`: If `rule_type` is `RULE_REGEX`, then `rule` should be an
        iterable of tuple pairs `(compiled_regular_expression,
        replacement_string)` where `compiled_regular_expression` was obtained
        with `re.compile(...)` and `replacement_string` is anything that can be
        specified as the second (`repl`) argument of `re.sub(...)`.  This can be
        a replacement string that includes escapes for captured sub-expressions
        or a callable that takes a match object as argument.

        Example::

          regex_conversion_rule = UnicodeToLatexConversionRule(
              rule_type=RULE_REGEX,
              rule=[
                  # protect acronyms of capital letters with braces ABC -> {ABC}
                  (re.compile(r'[A-Z]{2,}'), r'{\1}'),
                  # can specify several rules. For instance, convert ... -> \ldots
                  (re.compile(r'...'), r'\ldots'),
              ]
          )

      - `RULE_CALLABLE`: If `rule_type` is `RULE_CALLABLE`, then `rule` should
        be a callable that accepts two arguments, the unicode string and the
        position in the string (an integer), and a possible additional argument
        called `u2lobj`.  The callable will be called with the original unicode
        string as argument and the position of the character that needs to be
        encoded.  If this rule can encode the given character at the given
        position, it should return a tuple `(consumed_length,
        replacement_string)` where `consumed_length` is the number of characters
        in the unicode string that `replacement_string` represents.  If the
        character(s) at the given position can't be encoded by this rule, the
        callable should return `None` to indicate that further rules should be
        attempted.

        For example, the following callable should achieve the same effect as
        the previous example with regexes::

          def convert_stuff(s, pos):
              m = re.match(r'[A-Z]{2,}', s, pos)
              if m is not None:
                  return (m.end()-m.start(), '{'+m.group()+'}')
              if s.startswith('...', pos): # or  s[pos:pos+3] == '...'
                  return (3, r'\ldots')
              return None


    .. versionadded:: 2.0

       This class was introduced in `pylatexenc 2.0`.
    """
    def __init__(self, rule_type, rule=None):
        self.rule_type = rule_type
        self.rule = rule



def get_builtin_conversion_rules(which):
    r"""
    Return a built-in set of conversion rules specified by name `which`.

    Currently, only the name `which='defaults'` is accepted.

    The return value is a list of :py:class:`UnicodeToLatexConversionRule`
    objects that can be either directly specified to the `conversion_rules=`
    argument of :py:class:`UnicodeToLatexEncoder`, or included in a larger list
    that can be provided to that argument.
    
    .. versionadded:: 2.0

       This function was introduced in `pylatexenc 2.0`.
    """
    if which == 'defaults':
        return [ UnicodeToLatexConversionRule(rule_type=RULE_DICT,
                                              rule=get_builtin_uni2latex_dict()) ]
    raise ValueError("Unknown builtin rule set: {}".format(which))



class UnicodeToLatexEncoder(object):
    r"""
    Encode a string with unicode characters into a LaTeX snippet.

    The following general attributes can be specified as keyword arguments to
    the constructor.  Note: These attributes must be specified to the
    constructor and may NOT be subsequently modified.  This is because in the
    constructor we pre-compile some rules and flags to optimize calls to
    :py:text:`unicode_to_text()`.

    .. py:attribute:: non_ascii_only

       Whether we should convert only non-ascii characters into LaTeX sequences,
       or also all known ascii characters with special LaTeX meaning such as
       '\\', '$', '&', etc.

       If `non_ascii_only` is set to `True` (the default is `False`), then
       conversion rules are not applied at positions in the string where an
       ASCII character is encountered.

    .. py:attribute:: conversion_rules

       The conversion rules, specified as a list of
       :py:class:`UnicodeToLatexConversionRule` objects.  If you specify your
       own list of rules using this argument, you will probably want to add
       presumably at the end of your list the list of rules obtained by
       ``get_builtin_conversion_rules('defaults')`` to include all built-in
       default conversion rules.  To override built-in rules, simply add your
       custom rules earlier in the list.

    .. py:attribute:: replacement_latex_protection

       How to "protect" LaTeX replacement text that looks like it could be
       interpreted differently if concatenated to arbitrary strings before and
       after.

       Currently only one situation is recognized: if the replacement string
       ends with a latex macro invokation with a non-symbol macro name,
       e.g. ``\textemdash`` or ``\^\i``.  Indeed, if we naively replace these
       texts in an arbitrary string (like ``ma\N{LATIN SMALL LETTER I WITH
       CIRCUMFLEX}tre``), we might get an invalid macro invokation (like
       ``ma\^\itre`` which causes un known macro name ``\itre``).

       Possible protection schemes are:

         - 'braces' (the default).  Any suspicious replacement text (that
           might look fragile) is placed in curly braces ``{...}``.

         - 'braces-all'.  All replacement latex escapes are surrounded in
           protective curly braces ``{...}``.

         - 'braces-almost-all'.  Almost all replacement latex escapes are
           surrounded in protective curly braces ``{...}``.  (Specifically, all
           those replacement strings that start with a backslash.)  [I'm not
           sure this is useful, but it provides a way to reproduce the previous
           behavior of `utf8tolatex()`.]

         - 'braces-after-macro'.  If the situation described above (where the
           replacement text ends with a string-named macro) is encountered, then
           a pair of empty braces is added at the end of the replacement text to
           protect the macro.

         - `none`.  No protection is applied.  This is not recommended.

    .. py:attribute:: bad_char_policy

       What to do when a non-ascii character is encountered without any known
       substitution macro.  The attribute `bad_char_policy` can be set to one of:

         - 'keep' (keep the character as is)

         - 'replace' (replace the character by a boldface question mark)

         - 'ignore' (ignore the character from the input entirely and don't
           output anything for it)

         - 'fail' (raise a `ValueError` exception)

         - a Python callable --- will be called with argument the character that
           could not be encoded.  (If the callable accepts a second argument
           called 'u2lobj', then the `UnicodeToLatexEncoder` instance is
           provided to that argument.)  The return value of the callable is used
           as LaTeX replacement code.

    .. py:attribute:: bad_char_warning

       In addition to the `bad_char_policy`, this attribute indicates whether or
       not (`True` or `False`) one should generate a warning when a "bad char"
       is encountered. (Default: True)

    The database of rules specifying how to convert unicode characters into
    LaTeX are organized into categories, and can be specified with the
    `add_conversion_rule()`.

    .. warning::
      
       None of the above attributes should be modified after constructing the
       object.  Their final value must be specified to the class constructor.
       [Indeed, the class constructor "compiles" these attribute values into a
       data structure that makes :py:meth:`unicode_to_text()` more efficient.]

    .. versionadded:: 2.0

       This class was introduced in `pylatexenc 2.0`.
    """
    def __init__(self, **kwargs):
        self.non_ascii_only = kwargs.pop('non_ascii_only', False)
        self.conversion_rules = kwargs.pop('conversion_rules', 
                                           get_builtin_conversion_rules('defaults'))
        self.replacement_latex_protection = kwargs.pop('replacement_latex_protection', 'braces')
        self.bad_char_policy = kwargs.pop('bad_char_policy', 'keep')
        self.bad_char_warning = kwargs.pop('bad_char_warning', True)

        if kwargs:
            logger.warning("Ignoring unknown keyword arguments: %s", ",".join(kwargs.keys())) 

        super(UnicodeToLatexEncoder, self).__init__(**kwargs)

        #
        # now "pre-compile" some stuff so that calls to unicode_to_latex() can
        # execute fast
        #

        # "pre-compile" rules and check rule types:
        self._compiled_rules = []
        for rule in self.conversion_rules:
            if rule.rule_type == RULE_DICT:
                self._compiled_rules.append( functools.partial(self._apply_rule_dict, rule.rule) )
            elif rule.rule_type == RULE_REGEX:
                self._compiled_rules.append( functools.partial(self._apply_rule_regex, rule.rule) )
            elif rule.rule_type == RULE_CALLABLE:
                thecallable = rule.rule
                if 'u2lobj' in getfullargspec(thecallable)[0]:
                    thecallable = partial(rule.rule, u2lobj=self)
                self._compiled_rules.append( functools.partial(self._apply_rule_callable, thecallable) )
            else:
                raise TypeError("Invalid rule type: {}".format(rule.rule_type))
        
        # bad char policy:
        if isinstance(self.bad_char_policy, basestring):
            selfmethname = '_do_bad_char_'+self.bad_char_policy
            if not hasattr(self, selfmethname):
                raise ValueError("Invalid bad-char policy: {}".format(self.bad_char_policy))
            self._do_bad_char = getattr(self, selfmethname)
        elif callable(self.bad_char_policy):
            import inspect
            fn = self.bad_char_policy
            if 'u2lobj' in getfullargspec(fn)[0]:
                self._do_bad_char = functools.partial(self.bad_char_policy, u2lobj=self)
            else:
                self._do_bad_char = self.bad_char_policy
        else:
            raise TypeError("Invalid argument for bad_char_policy: {!r}".format(self.bad_char_policy))

        # bad char warning:
        if not self.bad_char_warning:
            self._do_warn_bad_char = lambda ch: None # replace method by no-op

        # set a method that will skip ascii characters if required:
        if self.non_ascii_only:
            self._maybe_skip_ascii = self._check_do_skip_ascii
        else:
            self._maybe_skip_ascii = lambda s, p: False

        # set a method to protect replacement latex code, if necessary:
        if self.replacement_latex_protection and self.replacement_latex_protection != 'none':
            selfmethname = '_apply_protection_'+self.replacement_latex_protection.replace('-', '_')
            if not hasattr(self, selfmethname):
                raise ValueError("Invalid replacement_latex_protection: {}".format(
                    self.replacement_latex_protection
                ))
            self._apply_protection = getattr(self, selfmethname)
        else:
            self._apply_protection = lambda x: x


    def unicode_to_latex(self, s):
        """
        Convert unicode characters in the string `s` into latex escape sequences.
        """

        s = unicode(s) # make sure s is unicode
        s = unicodedata.normalize('NFC', s)

        class _NS: pass
        p = _NS()
        p.latex = ''
        p.pos = 0

        while p.pos < len(s):
            
            if self._maybe_skip_ascii(s, p):
                continue

            for compiledrule in self._compiled_rules:
                if compiledrule(s, p):
                    break
            else:
                # for-else, see
                # https://docs.python.org/2/tutorial/controlflow.html\
                # #break-and-continue-statements-and-else-clauses-on-loops
                ch = s[p.pos]
                o = ord(ch)
                if (o >= 32 and o <= 127) or (ch in "\n\r\t"):
                    p.latex += ch
                    p.pos += 1
                else:
                    self._do_warn_bad_char(ch)
                    p.latex += self._do_bad_char(ch)
                    p.pos += 1
                
        return p.latex


    def _check_do_skip_ascii(self, s, p):
        if ord(s[p.pos]) < 127:
            # skip, we only want to convert non-ascii chars
            p.latex += s[p.pos]
            p.pos += 1
            return True
        return False


    def _apply_rule_dict(self, ruledict, s, p):
        o = ord(s[p.pos])
        if o in ruledict:
            self._apply_replacement(p, ruledict[o], 1)
            return True
        return None
    def _apply_rule_regex(self, ruleregexes, s, p):
        for regex, repl in ruleregexes:
            m = regex.match(s, p.pos)
            if m is not None:
                # is there a better way than to re-match with sub() and still
                # accept the wide range of possibilities for repl incl, \1, \2,
                # etc.?
                self._apply_replacement(p, regex.sub(repl, m.group()), m.end() - m.start())
                return True
        return None
    def _apply_rule_callable(self, rulecallable, s, p):
        res = rulecallable(s, p.pos)
        if res is None:
            return None
        (consumed, repl) = res
        self._apply_replacement(p, repl, consumed)
        return True

    def _apply_replacement(self, p, repl, numchars):
        # check for possible replacement latex protection, like braces:
        repl = self._apply_protection(repl)
        p.latex += repl
        p.pos += numchars

    def _apply_protection_braces(self, repl):
        k = repl.rfind('\\')
        if k >= 0 and repl[k+1:].isalpha():
            # has dangling named macro, apply protection.
            return '{' + repl + '}'
        return repl
    def _apply_protection_braces_almost_all(self, repl):
        if repl[0:1] == '\\':
            return '{' + repl + '}'
        return repl
    def _apply_protection_braces_all(self, repl):
        return '{' + repl + '}'
    def _apply_protection_braces_after_macro(self, repl):
        k = repl.rfind('\\')
        if k > 0 and repl[k+1:].isalpha():
            # has dangling named macro, apply protection.
            return repl + '{}'
        return repl

    # policies for "bad chars":
    def _do_bad_char_keep(self, ch):
        return ch

    def _do_bad_char_replace(self, ch):
        return r'{\bfseries ?}'

    def _do_bad_char_ignore(self, ch):
        return ''

    def _do_bad_char_fail(self, ch):
        raise ValueError("Character cannot be encoded into LaTeX: U+%04X - ‘%s’"%(ord(ch), ch))

    def _do_warn_bad_char(self, ch):
        logger.warning("Character cannot be encoded into LaTeX: U+%04X - ‘%s’", ord(ch), ch)



# ------------------------------------------------



_u2l_obj_cache = {}


def unicode_to_latex(s, non_ascii_only=False, replacement_latex_protection='braces',
                     bad_char_policy='keep', bad_char_warning=True):
    r"""
    Shorthand for constructing a :py:class:`UnicodeToLatexEncoder` instance and
    calling its :py:meth:`~UnicodeToLatexEncoder.unicode_to_latex()` method.

    The :py:class:`UnicodeToLatexEncoder` instances for given values of the
    options are cached.

    The parameters `non_ascii_only`, `replacement_latex_protection`,
    `bad_char_policy`, and `bad_char_warning` are directly passed on to the
    :py:class:`UnicodeToLatexEncoder` constructor.  See the class doc for
    :py:class:`UnicodeToLatexEncoder` for more information about their effect.

    It is not possible to specify custom conversion rules with this helper
    function.  If you need custom conversion rules, simply create a
    :py:class:`UnicodeToLatexEncoder` instance directly.
    """

    key = (non_ascii_only, replacement_latex_protection, bad_char_policy, bad_char_warning)

    if key in _u2l_obj_cache:
        u = _u2l_obj_cache[key]
    else:
        u = UnicodeToLatexEncoder(non_ascii_only=non_ascii_only,
                                  replacement_latex_protection=replacement_latex_protection,
                                  bad_char_policy=bad_char_policy,
                                  bad_char_warning=bad_char_warning)
        _u2l_obj_cache[key] = u

    return u.unicode_to_latex(s)
    



# ------------------------------------------------------------------------------------------------

# Don't change pylatexenc 1.x function:



utf82latex = _util.LazyDict(generate_dict_fn=lambda: _uni2latex)
"""
.. deprecated:: 2.0

   Pylatexenc 1.x exposed the module-level dictionary `utf82latex` that could be
   modified to alter the behavior of `utf8tolatex()`.

   If you would like to obtain a copy of the built-in unicode to text
   dictionary, see :py:func:`get_builtin_uni2latex_dict()`.  If you would like
   to alter the behavior of :py:func:`utf82latex()`, you should use
   :py:class:`UnicodeToLatexEncoder` which provides a rich interface for
   specifying rules how to convert chars to LaTeX escapes.

   For backwards compatibility, you can still modify the module-level dictionary
   `utf82latex` (but don't assign a new object to it) and this will directly
   modify the global built-in dictionary of known latex escapes.  This is not
   recommended however, and the `utf82latex` module-level dictionary might be
   removed in the future.
"""




def utf8tolatex(s, non_ascii_only=False, brackets=True, substitute_bad_chars=False,
                fail_bad_chars=False):
    """
    .. note::

       Since `pylatexenc 2.0`, it is recommended to use the
       :py:class:`TextLatexEncoder()` function instead, which provides more
       flexibility and versatility.  (For instance, it allows you to specify
       custom escape sequences for certain characters.)

       The function `utf8tolatex()` is provided unchanged from `pylatexenc 1.x`.
       We have no plans to remove this function in the near future so it is not
       (yet) considered as deprecated and we will continue to provide it in near
       future versions of `pylatexenc`.  Bug reports and improvements will
       however be directed to :py:func:`TextLatexEncoder()`.

    Encode a UTF-8 string to a LaTeX snippet.

    If `non_ascii_only` is set to `True`, then usual (ascii) characters such as ``#``,
    ``{``, ``}`` etc. will not be escaped.  If set to `False` (the default), they are
    escaped to their respective LaTeX escape sequences.

    If `brackets` is set to `True` (the default), then LaTeX macros are enclosed in
    brackets.  For example, ``sant\N{LATIN SMALL LETTER E WITH ACUTE}`` is replaced by
    ``sant{\\'e}`` if `brackets=True` and by ``sant\\'e`` if `brackets=False`.

    .. warning::
        Using `brackets=False` might give you an invalid LaTeX string, so avoid
        it! (for instance, ``ma\N{LATIN SMALL LETTER I WITH CIRCUMFLEX}tre`` will be
        replaced incorrectly by ``ma\\^\\itre`` resulting in an unknown macro ``\\itre``).

    If `substitute_bad_chars=True`, then any non-ascii character for which no LaTeX escape
    sequence is known is replaced by a question mark in boldface. Otherwise (by default),
    the character is left as it is.

    If `fail_bad_chars=True`, then a `ValueError` is raised if we cannot find a
    character substitution for any non-ascii character.

    .. versionchanged:: 1.3

        Added `fail_bad_chars` switch
    """

    s = unicode(s) # make sure s is unicode
    s = unicodedata.normalize('NFC', s)

    if not s:
        return ""

    result = u""
    for ch in s:
        #logger.longdebug("Encoding char %r", ch)
        if (non_ascii_only and ord(ch) < 127):
            result += ch
        else:
            lch = utf82latex.get(ord(ch), None)
            if (lch is not None):
                # add brackets if needed, i.e. if we have a substituting macro.
                # note: in condition, beware, that lch might be of zero length.
                result += (  '{'+lch+'}' if brackets and lch[0:1] == '\\' else
                             lch  )
            elif ((ord(ch) >= 32 and ord(ch) <= 127) or
                  (ch in "\n\r\t")):
                # ordinary printable ascii char, just add it
                result += ch
            else:
                # non-ascii char
                msg = u"Character cannot be encoded into LaTeX: U+%04X - `%s'" % (ord(ch), ch)
                if fail_bad_chars:
                    raise ValueError(msg)

                logger.warning(msg)
                if substitute_bad_chars:
                    result += r'{\bfseries ?}'
                else:
                    # keep unescaped char
                    result += ch

    return result






# ------------------------------------------------------------------------------



def main(argv=None):
    import fileinput
    import argparse

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser()
    parser.add_argument('files', metavar="FILE", nargs='*',
                        help='Input files (if none specified, read from stdandard input)')

    args = parser.parse_args(argv)

    latex = ''
    for line in fileinput.input(files=args.files):
        latex += line

    print(utf8tolatex(latex))


def run_main():
    try:

        logging.basicConfig(level=logging.DEBUG)

        main()

    except SystemExit:
        raise
    except: # lgtm [py/catch-base-exception]
        import pdb
        import traceback
        traceback.print_exc()
        pdb.post_mortem()


if __name__ == '__main__':

    run_main()
