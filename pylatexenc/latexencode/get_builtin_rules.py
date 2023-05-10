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
                                              rule=get_builtin_uni2latex_dict()) ]

    if builtin_name == 'unicode-xml':
        from . import _uni2latexmap_xml
        return [ UnicodeToLatexConversionRule(rule_type=RULE_DICT,
                                              rule=_uni2latexmap_xml.uni2latex) ]

    raise ValueError("Unknown builtin rule set: {}".format(builtin_name))

