# -*- coding: utf-8 -*-
#
# The MIT License (MIT)
# 
# Copyright (c) 2022 Philippe Faist
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


class LatexContextDbBase(object):

    def get_macro_spec(self, macroname):
        r"""
        ..........

        Should return `None` if no spec for a macro with the given name is
        found.
        """
        return None

    def get_environment_spec(self, environmentname):
        return None

    def get_specials_spec(self, specials_chars):
        return None

    def test_for_specials(self, s, pos, parsing_state):
        r"""
        ..............

        If non-`None`, the returned object, in addition to being a
        `CallableSpecBase` type object, must also expose the attribute
        `specials_chars`.
        """
        return None

    # ### Too specific to how macrospec's etc are implemented.
    #
    # def extended_with(category, **kwargs):
    #     macros = kwargs.pop('macros', None)
    #     environments = kwargs.pop('environments', None)
    #     specials = kwargs.pop('specials', None)
    #     raise RuntimeError(
    #         "This LatexContextDbBase instance does not implement extended_with()"
    #     )
