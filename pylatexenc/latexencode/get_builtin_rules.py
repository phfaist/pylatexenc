# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2023 Philippe Faist
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


import unicodedata


_MappingProxyType = dict
#__pragma__('skip')
import sys
if sys.version_info.major > 2:
    from types import MappingProxyType as _MappingProxyType
else:
    _MappingProxyType = dict
#__pragma__('noskip')


from ._rule import (
    RULE_DICT,
    RULE_REGEX,
    RULE_CALLABLE,
    UnicodeToLatexConversionRule,
)


# LaTeX accent macros indexed by the unicode combining character they render.
# Only accents that LaTeX renders with a standard accent macro are listed here;
# combining characters without such a macro (e.g. the Vietnamese horn or the
# hook above) are left to the unknown-character policy.
_accent_macros = {
    0x0300: '`',    # COMBINING GRAVE ACCENT
    0x0301: "'",    # COMBINING ACUTE ACCENT
    0x0302: '^',    # COMBINING CIRCUMFLEX ACCENT
    0x0303: '~',    # COMBINING TILDE
    0x0306: 'u',    # COMBINING BREVE
    0x0323: 'd',    # COMBINING DOT BELOW
}

# Accent macros that build a box around their argument, as opposed to the
# \accent-based marks which attach directly to the following character.
# Box-building marks must be applied outermost, so that the \accent-based
# marks stay directly on the base character: e.g. U+1EAD (a + dot below +
# circumflex) encodes as \d{\^{a}}, not \^{\d{a}}.  (Other box-building marks
# such as \c, \k, \b and \t would need the same treatment if they were ever
# added to _accent_macros above.)
_box_building_accent_macros = frozenset(['d'])


def _accent_decomposition_rule(s, pos):
    r"""
    `RULE_CALLABLE` fallback rule: encode a character that has no direct
    conversion rule by decomposing it into an ascii letter and combining
    accents (e.g. ``ị`` → ``\d{i}``).

    Returns `(1, latex)` if the character at `s[pos]` decomposes into an ascii
    letter and only known LaTeX accents, `None` otherwise so that the
    character is left to the unknown-character policy.
    """
    ch = s[pos]
    decomposed = unicodedata.normalize('NFD', ch)
    if len(decomposed) < 2:
        return None
    base = decomposed[0]
    if not (('a' <= base <= 'z') or ('A' <= base <= 'Z')):
        # Only accept a plain ascii letter as base character; anything else
        # would itself need to be encoded, which the preceding rules already
        # failed to do.
        return None
    accent_macros = []
    for accent_char in decomposed[1:]:
        macro = _accent_macros.get(ord(accent_char), None)
        if macro is None:
            return None
        accent_macros.append(macro)
    # \accent-based marks go innermost, directly on the base character;
    # box-building marks go outermost.
    latex = base
    for macro in accent_macros:
        if macro not in _box_building_accent_macros:
            latex = '\\' + macro + '{' + latex + '}'
    for macro in accent_macros:
        if macro in _box_building_accent_macros:
            latex = '\\' + macro + '{' + latex + '}'
    return (1, latex)




def get_builtin_uni2latex_dict():
    r"""
    Return a dictionary that contains the default collection of known LaTeX
    escape sequences for unicode characters.

    The keys of the dictionary are integers that correspond to unicode code
    points (i.e., `ord(char)`).  The values are the corresponding LaTeX
    replacement strings.

    The returned dictionary may not be modified.  To alter the behavior of
    :py:func:`unicode_to_latex()`, you should specify custom rules to a new
    instance of :py:class:`UnicodeToLatexEncoder`.

    .. versionadded:: 2.0

       This function was introduced in `pylatexenc 2.0`.
    """

    from ._uni2latexmap import uni2latex as _uni2latex
    return _MappingProxyType(_uni2latex)


def get_builtin_conversion_rules(builtin_name):
    r"""
    Return a built-in set of conversion rules specified by a given name
    `builtin_name`.

    There are two builtin conversion rules, with the following names:

      - `'defaults'`: the default conversion rules, a custom-curated list of
        unicode chars to LaTeX escapes.

      - `'unicode-xml'`: the conversion rules derived from the `unicode.xml` file
        maintained at https://www.w3.org/TR/xml-entity-names/#source by David
        Carlisle.

    The return value is a list of :py:class:`UnicodeToLatexConversionRule`
    objects that can be either directly specified to the `conversion_rules=`
    argument of :py:class:`UnicodeToLatexEncoder`, or included in a larger list
    that can be provided to that argument.
    
    .. versionadded:: 2.0

       This function was introduced in `pylatexenc 2.0`.
    """
    if builtin_name == 'defaults':
        return [ UnicodeToLatexConversionRule(rule_type=RULE_DICT,
                                              rule=get_builtin_uni2latex_dict()),
                 UnicodeToLatexConversionRule(rule_type=RULE_CALLABLE,
                                              rule=_accent_decomposition_rule), ]

    if builtin_name == 'unicode-xml':
        from . import _uni2latexmap_xml
        return [ UnicodeToLatexConversionRule(rule_type=RULE_DICT,
                                              rule=_uni2latexmap_xml.uni2latex) ]

    raise ValueError("Unknown builtin rule set: {}".format(builtin_name))

