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


# Internal module. Internal API may move, disappear or otherwise change at any
# time and without notice.

from __future__ import print_function, unicode_literals



import logging
logger = logging.getLogger(__name__)



class CarryoverInformation(object):
    r"""
    ........................

    .. py:attribute::  set_parsing_state

    .. py:attribute::  inner_parsing_state

       Specifically used for when a custom callable arguments parser (not a
       LatexArgumentsParser) wants to set a custom parsing state for the
       environment body.  The use of this feature is discouraged and mainly
       exists to smooth transitions from `pylatexenc 2` code.  It's better to
       subclass `LatexMacroCallParser`, `LatexEnvironmentCallParser`, or
       `LatexSpecialsCallParser` directly if you need custom behavior that
       affects the entire call.

    .. py:attribute::  extend_latex_context

       A dictionary with keys 'macros', 'environments', 'specials', as accepted
       by :py:meth:`LatexContextDb.add_context_category()`.
        
       Can be used along with set_parsing_state; in which case definitions are
       added on top of the parsing state change.


    """
    def __init__(self,
                 set_parsing_state=None,
                 update_parsing_state_kwargs=None,
                 inner_parsing_state=None,
                 extend_latex_context=None,
                 **kwargs):

        self.set_parsing_state = set_parsing_state
        self.update_parsing_state_attributes = dict(update_parsing_state_attributes)

        self.inner_parsing_state = inner_parsing_state

        self.extend_latex_context = extend_latex_context

        self.extra_info = dict(kwargs)


    def get_updated_parsing_state(self, parsing_state):

        new_parsing_state = parsing_state

        if self.set_parsing_state is not None:
            new_parsing_state = self.set_parsing_state

        if self.update_parsing_state_attributes:
            new_parsing_state = new_parsing_state.sub_context(
                **self.update_parsing_state_attributes
            )

        if self.extend_latex_context:
            new_parsing_state = new_parsing_state.sub_context(
                latex_context=parsing_state.latex_context.extended_with(
                    category=None,
                    **self.extend_latex_context
                )
            )

        return new_parsing_state





### BEGIN_PYLATEXENC2_LEGACY_SUPPORT_CODE

def _legacy_pyltxenc2_carryover_dict(carryover_info):
    d = {}
    if carryover_info.set_parsing_state is not None:
        d['new_parsing_state'] = carryover_info.set_parsing_state
    return d

setattr(CarryoverInformation, '_to_legacy_pyltxenc2_dict', _legacy_pyltxenc2_carryover_dict)

### END_PYLATEXENC2_LEGACY_SUPPORT_CODE
