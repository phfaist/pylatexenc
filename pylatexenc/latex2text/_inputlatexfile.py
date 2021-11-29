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

import os.path

import logging
logger = logging.getLogger(__name__)


def read_latex_file(tex_input_directory, strict_input, fn):

    fnfull = os.path.realpath(os.path.join(tex_input_directory, fn))
    if strict_input:
        # make sure that the input file is strictly within dirfull, and
        # didn't escape with '../..' tricks or via symlinks.
        dirfull = os.path.realpath(tex_input_directory)
        if not fnfull.startswith(dirfull):
            logger.warning(
                "Can't access path '%s' leading outside of mandated directory "
                "[strict input mode]",
                fn
            )
            return ''

    if not os.path.exists(fnfull) and os.path.exists(fnfull + '.tex'):
        fnfull = fnfull + '.tex'
    if not os.path.exists(fnfull) and os.path.exists(fnfull + '.latex'):
        fnfull = fnfull + '.latex'
    if not os.path.isfile(fnfull):
        logger.warning("Error, file doesn't exist: '%s'", fn)
        return ''

    logger.debug("Reading input file %r", fnfull)

    try:
        with open(fnfull) as f:
            return f.read()
    except IOError as e:
        logger.warning("Error, can't access '%s': %s", fn, e)
        return ''
