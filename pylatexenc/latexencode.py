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
The `latexencode` module provides a single function, :py:func:`utf8tolatex()` which
allows you to convert a unicode string to LaTeX escape sequences.
"""

from __future__ import print_function #, absolute_import

import unicodedata
import logging
import sys

if sys.version_info.major > 2:
    def unicode(string): return string
    basestring = str

log = logging.getLogger(__name__)



from ._utf8latexmap import utf82latex


# ------------------------------------------------------------------------------------------------




def utf8tolatex(s, non_ascii_only=False, brackets=True, substitute_bad_chars=False, fail_bad_chars=False):
    u"""
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
        #log.longdebug("Encoding char %r", ch)
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

                log.warning(msg)
                if substitute_bad_chars:
                    result += r'{\bfseries ?}'
                else:
                    # keep unescaped char
                    result += ch

    return result



if __name__ == '__main__':

    try:

        logging.basicConfig(level=logging.DEBUG)

        import fileinput
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument('files', metavar="FILE", nargs='*',
                            help='Input files (if none specified, read from stdandard input)')

        args = parser.parse_args()

        latex = u''
        for line in fileinput.input(files=args.files):
            latex += line

        print(utf8tolatex(latex))

    except: # lgtm [py/catch-base-exception]
        import pdb
        import traceback
        traceback.print_exc()
        pdb.post_mortem()


