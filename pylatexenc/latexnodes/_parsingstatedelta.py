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



class ParsingStateDelta(object):
    r"""
    Describe a change in the parsing state.  Can be the transition into math
    mode; the definition of a new macro causing the latex context to change;
    etc. etc.

    There are many ways in which the parsing state can change, and this is
    reflected in the many different subclasses of `ParsingStateDelta` (e.g.,
    :py:class:`ParsingStateDeltaSetMathMode`).

    It is the :py:class:`LatexWalkerBase` class that is being used that is
    responsible for actually updating a parsing state according to a
    `ParsingStateDelta` object.  Of course, `ParsingStateDelta` objects offer a
    `get_updated_parsing_state()` method that should minimally implement this
    parsing state change.  Yet the walker instance may take additional
    initiatives, for instance, changing the latex context as a consequence of a
    change to/from math mode.

    This class serves both as a base class for general parsing state changes, as
    well as a simple implementation of a parsing state change based on parsing
    state attributes that are to be changed.
    """
    def __init__(self, set_attributes=None, **kwargs):
        super(ParsingStateDelta, self).__init__(**kwargs)
        self.set_attributes = set_attributes
        self._fields = ('set_attributes',)

    def __repr__(self):
        return (
            self.__class__.__name__ + "("
            + ", ".join([
                "{}={!r}".format(k, getattr(self, k, '<??>'))
                for k in self._fields
            ])
            + ")"
        )

    def get_updated_parsing_state(self, parsing_state):
        r"""
        Apply any required changes to the given `parsing_state` and return a new
        parsing state that reflects all the necessary changes.

        The new parsing state instance might be the same object instance as is
        if no changes need to be applied.
        """

        if self.set_attributes:
            return parsing_state.sub_context( **self.set_attributes )

        return parsing_state    





class ParsingStateDeltaReplaceParsingState(ParsingStateDelta):
    r"""
    A parsing state change in which a new full parsing state object entirely
    replaces the previous parsing state.
    """
    def __init__(self, set_parsing_state, **kwargs):
        super(ParsingStateDeltaReplaceParsingState, self).__init__(**kwargs)
        self.set_parsing_state = set_parsing_state
        self._fields = ('set_parsing_state',)

    def get_updated_parsing_state(self, parsing_state):
        if self.set_parsing_state is not None:
            return self.set_parsing_state
        return parsing_state







class WalkerEventsParsingStateDeltasProvider(object):

    def enter_math_mode(self, math_mode_delimiter=None, trigger_token=None):
        return ParsingStateDelta(
            set_attributes=dict(
                in_math_mode=True,
                math_mode_delimiter=math_mode_delimiter
            )
        )

    def leave_math_mode(self, trigger_token=None):
        return ParsingStateDelta(
            set_attributes=dict(
                in_math_mode=False,
                math_mode_delimiter=None
            )
        )

    # def enter_group(self, latex_group_delimiter, parent_node, trigger_token,
    # parsing_state):
    #     return None

    # ...def leave_group(self, latex_group_delimiter, parent_node, trigger_token,
    # parsing_state):
    #     ........




def get_updated_parsing_state_from_delta(parsing_state, parsing_state_delta):
    if parsing_state_delta is None:
        return parsing_state
    return parsing_state_delta.get_updated_parsing_state(parsing_state)


