# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2021 Philippe Faist
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

from __future__ import print_function, absolute_import, unicode_literals

import logging
import functools
import itertools

import unicodedata


# "defaults" e.g. for Transcrypt:
def unicode_str(s=None):
    if s is None:
        return ''
    return str(s)
basestring_cls = str

#__pragma__('ecom')

#__pragma__('skip')
import sys
if sys.version_info.major > 2:
    unicode_str = str # need to support unicode() w/ no arguments
    basestring_cls = str
    # use MappingProxyType for keeping
    from types import MappingProxyType as _MappingProxyType
else:
    unicode_str = unicode
    basestring_cls = basestring
    _MappingProxyType = dict
#__pragma__('noskip')


logger = logging.getLogger(__name__)


### BEGINPATCH_LATEXENCODE_CALLABLE_ACCEPTS_U2LOBJ_ARG
import sys
if sys.version_info.major > 2:
    from inspect import getfullargspec
else:
    from inspect import getargspec as getfullargspec

def _callable_accepts_u2lobj_arg(fn):
    return ('u2lobj' in getfullargspec(fn)[0])
### ENDPATCH_LATEXENCODE_CALLABLE_ACCEPTS_U2LOBJ_ARG



# Apparently, Transcrypt does not support hexadecimal formatting, neither
# through a string format like '{:x}'.format(...), nor f'{...:x}', neither via
# hex(...) ... so we provide our own JS implementation.

# Feed some raw JS to transcrypt directly
#__pragma__('ecom')
"""?
__pragma__('js', 'var HexstrN = (v, N=4) => (+v).toString(16).toUpperCase().padStart(N, "0")');
?"""

#__pragma__('skip')
def HexstrN(value, N=4):
    return ('%X'%(value)).zfill(N)
#__pragma__('noskip')



## Transcrypt currently does not provide an implementation of m.expand() or
## rx.match(..., pos=) ... :/

#__pragma__('skip')
def re_match_expand(m, repl):
    return m.expand(repl)
def regex_match_pos(rx, s, pos):
    # CAREFUL !! m.start() and m.end() will differ on Transcrypt because we
    # slice the string.  Only rely on the difference m.start()-m.end() !!
    return rx.match(s, pos)
#__pragma__('noskip')

"""?
__pragma__('js', '''
var re_match_expand = (m, repl) => repl.replace(/\\\\((\\d)|g<(\\w+)>)/g, (esc, x, digit, gname) => m.group((digit != null) ? parseInt(digit) : gname)) ;
var regex_match_pos = (rx, s, pos) => rx.match(s.slice(pos)) ;
''');
?"""



### BEGIN_PYLATEXENC_GET_DEFAULT_SPECS_FN
from .get_builtin_rules import (
    get_builtin_uni2latex_dict, get_builtin_conversion_rules
)
### END_PYLATEXENC_GET_DEFAULT_SPECS_FN


from ._rule import (
    RULE_DICT,
    RULE_REGEX,
    RULE_CALLABLE,
    UnicodeToLatexConversionRule,
)



class UnicodeToLatexEncoder(object):
    r"""
    Encode a string with unicode characters into a LaTeX snippet.

    The following general attributes can be specified as keyword arguments to
    the constructor.  Note: These attributes must be specified to the
    constructor and may NOT be subsequently modified.  This is because in the
    constructor we pre-compile some rules and flags to optimize calls to
    :py:meth:`unicode_to_text()`.

    .. py:attribute:: non_ascii_only

       Whether we should convert only non-ascii characters into LaTeX sequences,
       or also all known ascii characters with special LaTeX meaning such as
       '\\\\', '$', '&', etc.

       If `non_ascii_only` is set to `True` (the default is `False`), then
       conversion rules are not applied at positions in the string where an
       ASCII character is encountered.

    .. py:attribute:: conversion_rules

       The conversion rules, specified as a list of
       :py:class:`UnicodeToLatexConversionRule` objects.  For each position in
       the string, the rules will be applied in the given sequence until a
       replacement string is found.

       Instead of a :py:class:`UnicodeToLatexConversionRule` object you may also
       specify a string specifying a built-in rule (e.g., 'defaults'), which
       will be expanded to the corresponding rules according to
       :py:func:`get_builtin_conversion_rules()`.
    
       If you specify your own list of rules using this argument, you will
       probably want to include presumably at the end of your list the element
       'defaults' to include all built-in default conversion rules.  To override
       built-in rules, simply add your custom rules earlier in the list.
       Example::

         conversion_rules = [
             # our custom rules
             UnicodeToLatexConversionRule(RULE_REGEX, [
                 # double \\ needed, see UnicodeToLatexConversionRule
                 ( re.compile(r'...'), r'\\ldots' ),
                 ( re.compile(r'î'), r'\\^i' ),
             ]),
             # plus all the default rules
             'defaults'
         ]
         u = UnicodeToLatexEncoder(conversion_rules=conversion_rules)

    .. py:attribute:: replacement_latex_protection

       How to "protect" LaTeX replacement text that looks like it could be
       interpreted differently if concatenated to arbitrary strings before and
       after.

       Currently in the default scheme only one situation is recognized: if the
       replacement string ends with a latex macro invocation with a non-symbol
       macro name, e.g. ``\textemdash`` or ``\^\i``.  Indeed, if we naively
       replace these texts in an arbitrary string (like ``maître``), we might
       get an invalid macro invocation (like ``ma\^\itre`` which causes un known
       macro name ``\itre``).

       Possible protection schemes are:

         - 'braces' (the default):  Any suspicious replacement text (that
           might look fragile) is placed in curly braces ``{...}``.

         - 'braces-all':  All replacement latex escapes are surrounded in
           protective curly braces ``{...}``, regardless of whether or not they
           might be deemed "fragile" or "unsafe".

         - 'braces-almost-all':  Almost all replacement latex escapes are
           surrounded in protective curly braces ``{...}``.  This option
           emulates closely the behavior of `brackets=True` of the function
           `utf8tolatex()` in `pylatexenc 1.x`, though I'm not sure it is really
           useful.  [Specifically, all those replacement strings that start with
           a backslash are surrounded by curly braces].

         - 'braces-after-macro':  In the situation where the replacement latex
           code ends with a string-named macro, then a pair of empty braces is
           added at the end of the replacement text to protect the macro.

         - 'none': No protection is applied, even in "unsafe" cases.  This is
           not recommended, as this will likely result in invalid LaTeX
           code. (Note this is the string 'none', not Python's built-in `None`.)

         - any callable object: The callable should take a single argument, the
           replacement latex string associated with a piece of the input (maybe
           a special character) that has been encoded; it should return the
           actual string to append to the output string.

         .. versionadded:: 2.10 

            You can specify a callable object to `replacement_latex_protection`
            since `pylatexenc 2.10`.

    .. py:attribute:: unknown_char_policy

       What to do when a non-ascii character is encountered without any known
       substitution macro.  The attribute `unknown_char_policy` can be set to one of:

         - 'keep': keep the character as is;

         - 'replace': replace the character by a boldface question mark;

         - 'ignore': ignore the character from the input entirely and don't
           output anything for it;

         - 'fail': raise a `ValueError` exception;

         - 'unihex': output the unicode hexadecimal code (U+XXXX) of the
           character in typewriter font;

         - a Python callable --- will be called with argument the character that
           could not be encoded.  (If the callable accepts a second argument
           called 'u2lobj', then the `UnicodeToLatexEncoder` instance is
           provided to that argument.)  The return value of the callable is used
           as LaTeX replacement code.

    .. py:attribute:: unknown_char_warning

       In addition to the `unknown_char_policy`, this attribute indicates
       whether or not (`True` or `False`) one should generate a warning when a
       nonascii character without any known latex representation is
       encountered. (Default: True)

    .. py:attribute:: latex_string_class

       The return type of :py:meth:`unicode_to_latex()`.  Normally this is a
       simple unicode string (`str` on `Python 3` or `unicode` on `Python 2`).

       But you can specify your custom string type via the `latex_string_class`
       argument.  The `latex_string_class` will be invoked with no arguments to
       construct an empty object (so `latex_string_class` can be either an
       object that can be constructed with no arguments or it can be a function
       with no arguments that return a fresh object instance).  The object must
       support the operation "+=", i.e., you should overload the ``__iadd__()``
       method.

       For instance, you can record the chunks that would have been appended
       into a single string as follows::

           class LatexChunkList:
               def __init__(self):
                   self.chunks = []

               def __iadd__(self, s):
                   self.chunks.append(s)
                   return self

           u = UnicodeToLatexEncoder(latex_string_class=LatexChunkList,
                                     replacement_latex_protection='none')
           result = u.unicode_to_latex("é → α")
           # result.chunks == [ r"\'e", ' ', r'\textrightarrow', ' ',
           #                    r'\ensuremath{\alpha}' ]

    .. warning::
      
       None of the above attributes should be modified after constructing the
       object.  The values specified to the class constructor are final and
       cannot be changed.  [Indeed, the class constructor "compiles" these
       attribute values into a data structure that makes
       :py:meth:`unicode_to_text()` slightly more efficient.]

    .. versionadded:: 2.0

       This class was introduced in `pylatexenc 2.0`.
    """
    def __init__(self, **kwargs):
        self.non_ascii_only = kwargs.pop('non_ascii_only', False)
        self.conversion_rules = kwargs.pop('conversion_rules', ['defaults'])
        self.replacement_latex_protection = kwargs.pop('replacement_latex_protection', 'braces')
        self.unknown_char_policy = kwargs.pop('unknown_char_policy', 'keep')
        self.unknown_char_warning = kwargs.pop('unknown_char_warning', True)
        self.latex_string_class = kwargs.pop('latex_string_class', unicode_str)

        if len(kwargs):
            logger.warning("Ignoring unknown keyword arguments: %s", ",".join(kwargs.keys())) 

        super(UnicodeToLatexEncoder, self).__init__(**kwargs)

        # build generator that expands built-in conversion rules
        expanded_conversion_rules = []
        # = itertools.chain.from_iterable([
        #     (get_builtin_conversion_rules(r) if isinstance(r, basestring_cls) else [ r ])
        #     for r in self.conversion_rules
        # ])
        for r in self.conversion_rules:
### BEGIN_PYLATEXENC_GET_DEFAULT_SPECS_FN
            if isinstance(r, basestring_cls):
                expanded_conversion_rules.extend( get_builtin_conversion_rules(r) )
                continue
### END_PYLATEXENC_GET_DEFAULT_SPECS_FN
            if isinstance(r, basestring_cls):
                logger.warning(
                    "The pylatexenc.latexencode module was preprocessed and/or transpiled "
                    "without support for implicit/string-specified default rules.  Please "
                    "import the pylatexenc.latexencode.get_builtin_rules module and "
                    "specify the relevant rules manually."
                )
                continue

            expanded_conversion_rules.append( r )

        #
        # now "pre-compile" some stuff so that calls to unicode_to_latex() can
        # hopefully execute faster
        #

        # "pre-compile" rules and check rule types:
        self._compiled_rules = []
        for rule in expanded_conversion_rules:
            if rule.rule_type == RULE_DICT:
                self._compiled_rules.append(
                    functools.partial(self._apply_rule_dict, rule.rule, rule)
                )
            elif rule.rule_type == RULE_REGEX:
                self._compiled_rules.append(
                    functools.partial(self._apply_rule_regex, rule.rule, rule)
                )
            elif rule.rule_type == RULE_CALLABLE:
                thecallable = rule.rule
                if _callable_accepts_u2lobj_arg(thecallable):
                #if 'u2lobj' in getfullargspec(thecallable)[0]:
                    thecallable = functools.partial(rule.rule, u2lobj=self)
                self._compiled_rules.append(
                    functools.partial(self._apply_rule_callable, thecallable, rule)
                )
            else:
                raise TypeError("Invalid rule type: {}".format(rule.rule_type))
        
        # bad char policy:
        if isinstance(self.unknown_char_policy, basestring_cls):
            self._do_unknown_char = self._get_method_fn(
                'do_unknown_char',
                self.unknown_char_policy,
                what='unknown_char_policy'
            )
        elif callable(self.unknown_char_policy):
            fn = self.unknown_char_policy
            if _callable_accepts_u2lobj_arg(fn):
            #if 'u2lobj' in getfullargspec(fn)[0]:
                self._do_unknown_char = functools.partial(self.unknown_char_policy, u2lobj=self)
            else:
                self._do_unknown_char = self.unknown_char_policy
        else:
            raise TypeError("Invalid argument for unknown_char_policy: {}"
                            .format(repr(self.unknown_char_policy)))

        # bad char warning:
        if not self.unknown_char_warning:
            self._do_warn_unknown_char = lambda ch: None # replace method by no-op
        else:
            self._do_warn_unknown_char = self._do_warn_unknown_char_defaultimpl

        # set a method that will skip ascii characters if required:
        if self.non_ascii_only:
            self._maybe_skip_ascii = self._check_do_skip_ascii
        else:
            self._maybe_skip_ascii = lambda s, p: False

        # set a method to protect replacement latex code, if necessary:
        self._apply_protection = self._get_replacement_latex_fn(
            self.replacement_latex_protection
        )

    def _get_method_fn(self, base, name, what):
        selfmethname = '_' + base + '_' + name.replace('-', '_')
        if not hasattr(self, selfmethname):
            raise ValueError("Invalid {}: {}".format(what, name))
        return getattr(self, selfmethname)

    def _get_replacement_latex_fn(self, replacement_latex_protection):
        if callable(replacement_latex_protection):
            return replacement_latex_protection
        return self._get_method_fn(
            'apply_protection',
            replacement_latex_protection,
            what='replacement_latex_protection'
        )

    def unicode_to_latex(self, s):
        """
        Convert unicode characters in the string `s` into latex escape sequences,
        according to the rules and options given to the constructor.
        """

        s = unicode_str(s) # make sure s is unicode
        s = unicodedata.normalize('NFC', s)

        class _NS: pass
        p = _NS()
        p.latex = self.latex_string_class()
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
                    self._do_warn_unknown_char(ch)
                    p.latex += self._do_unknown_char(ch)
                    p.pos += 1
                
        return p.latex


    def _check_do_skip_ascii(self, s, p):
        if ord(s[p.pos]) < 127:
            # skip, we only want to convert non-ascii chars
            p.latex += s[p.pos]
            p.pos += 1
            return True
        return False


    def _apply_rule_dict(self, ruledict, rule, s, p):
        o = ord(s[p.pos])
        if o in ruledict:
            self._apply_replacement(p, ruledict[o], 1, rule)
            return True
        return None
    def _apply_rule_regex(self, ruleregexes, rule, s, p):
        for regex, repl in ruleregexes:
            m = regex_match_pos(regex, s, p.pos)
            if m is not None:
                if callable(repl):
                    replstr = repl(m)
                else:
                    replstr = re_match_expand(m, repl)
                self._apply_replacement(p, replstr, m.end() - m.start(), rule)
                return True
        return None
    def _apply_rule_callable(self, rulecallable, rule, s, p):
        res = rulecallable(s, p.pos)
        if res is None:
            return None
        (consumed, repl) = res
        self._apply_replacement(p, repl, consumed, rule)
        return True

    def _apply_replacement(self, p, repl, numchars, ruleobj):
        # check for possible replacement latex protection, like braces.

        protect_fn = self._apply_protection

        # maybe the rule object has overridden the replacement_latex_protection to use.
        if ruleobj.replacement_latex_protection is not None:
            protect_fn = self._get_replacement_latex_fn(
                ruleobj.replacement_latex_protection
            )

        repl = protect_fn(repl)
        p.latex += repl
        p.pos += numchars

    def _apply_protection_none(self, repl):
        # no protection
        return repl
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
        if k >= 0 and repl[k+1:].isalpha():
            # has dangling named macro, apply protection.
            return repl + '{}'
        return repl

    # policies for "bad chars":
    def _do_unknown_char_keep(self, ch):
        return ch

    def _do_unknown_char_replace(self, ch):
        return r'{\bfseries ?}'

    def _do_unknown_char_ignore(self, ch):
        return ''

    def _do_unknown_char_fail(self, ch):
        raise ValueError(
            "No known latex representation for character: U+{} - ‘{}’"
            .format(HexstrN(ord(ch), 4), ch)
        )

    def _do_unknown_char_unihex(self, ch):
        return (
            r'\ensuremath{\langle}\texttt{U+' + HexstrN(ord(ch), 4)
            + r'}\ensuremath{\rangle}'
        )

    def _do_warn_unknown_char_defaultimpl(self, ch):
        logger.warning(
            "No known latex representation for character: U+{} - ‘{}’"
            .format(HexstrN(ord(ch), 4), ch)
        )


