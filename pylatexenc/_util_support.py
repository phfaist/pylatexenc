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


try:
    # Python >= 3.3
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping

import warnings




def pylatexenc_deprecated_ver(ver, msg, stacklevel=2):
    warnings.warn(
        "Deprecated (pylatexenc {}): {} ".format(ver, msg.strip()),
        DeprecationWarning,
        stacklevel=stacklevel+1
    )


def pylatexenc_deprecated_2(msg, stacklevel=2):
    warnings.warn(
        ( "Deprecated (pylatexenc 2.0): {} "
          "[see https://pylatexenc.readthedocs.io/en/latest/new-in-pylatexenc-2/]" )
        .format(msg.strip()),
        DeprecationWarning,
        stacklevel=stacklevel+1
    )

def pylatexenc_deprecated_3(msg, stacklevel=2):
    warnings.warn(
        ( "Deprecated (pylatexenc 3.0): {} "
          "[see https://pylatexenc.readthedocs.io/en/latest/new-in-pylatexenc-3/]" )
        .format(msg.strip()),
        DeprecationWarning,
        stacklevel=stacklevel+1
    )



# ------------------------------------------------------------------------------


class LazyDict(MutableMapping):
    r"""
    A lazy dictionary that loads its data when it is first queried.

    This is used to store the legacy
    :py:data:`pylatexenc.latexwalker.default_macro_dict` as well as
    :py:data:`pylatexenc.latex2text.default_macro_dict` etc.  Such that these
    "dictionaries" are still exposed at the module-level, but the data is loaded
    only if they are actually queried.
    """
    def __init__(self, generate_dict_fn):
        self._full_dict = None
        self._generate_dict_fn = generate_dict_fn

    def _ensure_instance(self):
        if self._full_dict is not None:
            return
        self._full_dict = self._generate_dict_fn()

    def __getitem__(self, key):
        self._ensure_instance()
        return self._full_dict.__getitem__(key)

    def __setitem__(self, key, val):
        self._ensure_instance()
        return self._full_dict.__setitem__(key, val)

    def __delitem__(self, key):
        self._ensure_instance()
        return self._full_dict.__delitem__(key)

    def __iter__(self):
        self._ensure_instance()
        return iter(self._full_dict)

    def __len__(self):
        self._ensure_instance()
        return len(self._full_dict)

    def copy(self):
        self._ensure_instance()
        return self._full_dict.copy()

    def clear(self):
        self._ensure_instance()
        return self._full_dict.clear()



