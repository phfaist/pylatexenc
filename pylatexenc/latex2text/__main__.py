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

import sys
import fileinput
import argparse


from .. import latexwalker
from ..latex2text import LatexNodes2Text, _strict_latex_spaces_predef


def main(argv=None):

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser()

    group = parser.add_argument_group("LatexWalker options")

    group.add_argument('--parser-keep-inline-math', action='store_const', const=True,
                       dest='parser_keep_inline_math', default=None,
                       help=argparse.SUPPRESS)
    group.add_argument('--no-parser-keep-inline-math', action='store_const', const=False,
                       dest='parser_keep_inline_math',
                       help=argparse.SUPPRESS)

    group.add_argument('--tolerant-parsing', action='store_const', const=True,
                       dest='tolerant_parsing', default=True)
    group.add_argument('--no-tolerant-parsing', action='store_const', const=False,
                       dest='tolerant_parsing',
                       help="Tolerate syntax errors when parsing, and attempt to continue (default yes)")

    group.add_argument('--strict-braces', action='store_const', const=True,
                       dest='strict_braces', default=False)
    group.add_argument('--no-strict-braces', action='store_const', const=False,
                       dest='strict_braces',
                       help="Report errors for mismatching LaTeX braces (default no)")

    group = parser.add_argument_group("LatexNodes2Text options")

    group.add_argument('--text-keep-inline-math', action='store_const', const=True,
                       dest='text_keep_inline_math', default=None,
                       help=argparse.SUPPRESS)
    group.add_argument('--no-text-keep-inline-math', action='store_const', const=False,
                       dest='text_keep_inline_math',
                       help=argparse.SUPPRESS)

    group.add_argument('--math-mode', action='store', dest='math_mode',
                       choices=['text', 'with-delimiters', 'verbatim', 'remove'],
                       default='text',
                       help="How to handle chunks of math mode LaTeX code. 'text' = convert "
                       "to text like the rest; 'with-delimiters' = same as 'text' but retain "
                       "the original math mode delimiters; 'verbatim' = keep verbatim LaTeX code; "
                       "'remove' = remove from input entirely")

    group.add_argument('--fill-text', dest='fill_text', action='store', nargs='?',
                       default=-1,
                       help="Wrap text to the given width, or 80 columns if no argument "
                       "is specified" )

    group.add_argument('--keep-comments', action='store_const', const=True,
                       dest='keep_comments', default=False)
    group.add_argument('--no-keep-comments', action='store_const', const=False,
                       dest='keep_comments',
                       help="Keep LaTeX comments in text output (default no)")

    group.add_argument('--strict-latex-spaces',
                       choices=['off', 'on']+list(_strict_latex_spaces_predef.keys()),
                       dest='strict_latex_spaces', default='macros',
                       help="How to handle whitespace. See documentation for the class "
                       "LatexNodes2Text().")

    group.add_argument('--keep-braced-groups', action='store_const', const=True,
                       dest='keep_braced_groups', default=False)
    group.add_argument('--no-keep-braced-groups', action='store_const', const=False,
                       dest='keep_braced_groups',
                       help="Keep LaTeX {braced groups} in text output (default no)")

    group.add_argument('--keep-braced-groups-minlen', type=int, default=2,
                       dest='keep_braced_groups_minlen',
                       help="Only apply --keep-braced-groups to groups that contain at least"
                       "this many characters")

    parser.add_argument('files', metavar="FILE", nargs='*',
                        help='Input files (if none specified, read from stdandard input)')

    args = parser.parse_args(argv)

    if args.parser_keep_inline_math is not None or args.text_keep_inline_math is not None:
        logger.warning("Options --parser-keep-inline-math and --text-keep-inline-math are "
                       "deprecated and no longer have any effect.  Please use "
                       "--math-mode=... instead.")

    latex = ''
    for line in fileinput.input(files=args.files):
        latex += line

    if args.fill_text != -1:
        if args.fill_text is not None and len(args.fill_text):
            fill_text = int(args.fill_text)
        else:
            fill_text = True
    else:
        fill_text = None

    lw = latexwalker.LatexWalker(latex,
                                 tolerant_parsing=args.tolerant_parsing,
                                 strict_braces=args.strict_braces)

    (nodelist, pos, len_) = lw.get_latex_nodes()

    ln2t = LatexNodes2Text(math_mode=args.math_mode,
                           keep_comments=args.keep_comments,
                           strict_latex_spaces=args.strict_latex_spaces,
                           keep_braced_groups=args.keep_braced_groups,
                           keep_braced_groups_minlen=args.keep_braced_groups_minlen,
                           fill_text=fill_text)

    print(ln2t.nodelist_to_text(nodelist) + "\n")



def run_main():

    try:

        main()

    except SystemExit:
        raise
    except: # lgtm [py/catch-base-exception]
        import pdb
        import traceback
        traceback.print_exc()
        pdb.post_mortem()


if __name__ == '__main__':

    run_main()
