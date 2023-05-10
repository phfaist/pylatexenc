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


import bisect
bisect_right = bisect.bisect_right


# ------------------------------------------------------------------------------


class LineNumbersCalculator(object):
    r"""
    Utility to calculate line numbers.
    """
    def __init__(self, s,
                 line_number_offset=1, first_line_column_offset=0, column_offset=0):
        super(LineNumbersCalculator, self).__init__()

        self.line_number_offset = line_number_offset
        self.first_line_column_offset = first_line_column_offset
        self.column_offset = column_offset

        def find_all_new_lines(x):
            # first line starts at the beginning of the string
            yield 0
            k = 0
            while k < len(x):
                k = x.find('\n', k)
                if k == -1:
                    return
                k += 1
                # s[k] is the character after the newline, i.e., the 0-th column
                # of the new line
                yield k

        self._pos_new_lines = list(find_all_new_lines(s))

        
    def pos_to_lineno_colno(self, pos, as_dict=False):
        r"""
        Return the line and column number corresponding to the given `pos`.

        Return a tuple `(lineno, colno)` giving line number and column number.
        Line numbers start at 1 and column number start at zero, i.e., the
        beginning of the document (`pos=0`) has line and column number `(1,0)`.
        If `as_dict=True`, then a dictionary with keys 'lineno', 'colno' is
        returned instead of a tuple.
        """

        if pos is None:
            if as_dict:
                return {'lineno': None, 'colno': None}
            return (None, None)

        # find line number in list

        # line_no is the index of the last item in self._pos_new_lines that is <= pos.
        line_no = bisect_right(self._pos_new_lines, pos)-1
        assert line_no >= 0 and line_no < len(self._pos_new_lines)

        col_no = pos - self._pos_new_lines[line_no]

        if line_no == 0:
            col_no += self.first_line_column_offset
        else:
            col_no += self.column_offset
        line_no += self.line_number_offset

        if as_dict:
            return {'lineno': line_no, 'colno': col_no}
        return (line_no, col_no)



# ------------------------------------------------------------------------------


class PushPropOverride(object):
    def __init__(self, obj, propname, new_value):
        super(PushPropOverride, self).__init__()
        self.obj = obj
        self.propname = propname
        self.new_value = new_value

    def __enter__(self):
        if self.new_value is not None:
            self.initval = getattr(self.obj, self.propname)
            setattr(self.obj, self.propname, self.new_value)
        return self

    def __exit__(self, type, value, traceback):
        # clean-up
        if self.new_value is not None:
            setattr(self.obj, self.propname, self.initval)


# ------------------------------------------------------------------------------


try:
    from collections import ChainMap
except ImportError:
    pass
### BEGIN_PYTHON2_SUPPORT_CODE
    from chainmap import ChainMap
### END_PYTHON2_SUPPORT_CODE



# ------------------------------------------------------------------------------



pylatexenc_deprecated_ver = lambda *args: None  #lgtm [py/multiple-definition]
pylatexenc_deprecated_2 = lambda *args: None  #lgtm [py/multiple-definition]
pylatexenc_deprecated_3 = lambda *args: None  #lgtm [py/multiple-definition]
LazyDict = None  #lgtm [py/multiple-definition]

### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE

from ._util_support import (   # lgtm [py/unused-import]
    pylatexenc_deprecated_ver,
    pylatexenc_deprecated_2,
    pylatexenc_deprecated_3,
    #
    LazyDict
)

### END_PYLATEXENC2_LEGACY_SUPPORT_CODE
