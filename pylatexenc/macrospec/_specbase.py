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

# for Py3
_basestring = str

## Begin Py2 support code
import sys
if sys.version_info.major == 2:
    # Py2
    _basestring = basestring
## End Py2 support code





# class Argument(object):
#     def __init__(self, parser, argument_name=None, **kwargs):
#         super(Argument, self).__init__(**kwargs)
#         self.parser = parser
#         self.argument_name = argument_name






class .........SpecBase(object):
    def __init__(self, arguments=[], **kwargs):
        super(_BaseSpec, self).__init__(**kwargs)

        self.arguments = arguments

        # if isinstance(args_parser, _basestring):
        #     self.args_parser = MacroStandardArgsParser(args_parser)
        # else:
        #     self.args_parser = args_parser


    def get_instance_parser(self, instance_token):
        r"""
        """

        ......

        ................


    def parse_args(self, *args, **kwargs):
        r"""
        .............will be deprecated.

        Shorthand for calling the :py:attr:`args_parser`\ 's `parse_args()` method.
        See :py:class:`MacroStandardArgsParser`.
        """

        ................


        return self.args_parser.parse_args(*args, **kwargs)


