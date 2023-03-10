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


# for Py3
_basestring = str
_unicode_from_str = lambda x: x


## Begin Py2 support code
import sys
if sys.version_info.major == 2:
    # Py2
    _basestring = basestring
    _unicode_from_str = lambda x: x.decode('utf-8')
## End Py support code


from .. import macrospec

from ._types import *



import json



#
# small utilities for displaying & debugging
#


def nodelist_to_latex(nodelist):

    # It's NOT recommended to use this function.  You should use
    # node.latex_verbatim() instead.

    # Here, we don't use latex_verbatim() and continue to provide (an updated
    # version of) the old code, because we want to be compatible with code that
    # used this function on custom instantiated nodes without setting the
    # parsing_state.

    def add_args(nodeargd):
        if nodeargd is None or nodeargd.argspec is None or nodeargd.argnlist is None:
            return ''
        argslatex = ''
        for argt, argn in zip(nodeargd.argspec, nodeargd.argnlist):
            if argt == '*':
                if argn is not None:
                    argslatex += nodelist_to_latex([argn])
            elif argt == '[':
                if argn is not None:
                    # the node is a group node with '[' delimiter char anyway
                    argslatex += nodelist_to_latex([argn])
            elif argt == '{':
                # either a group node with '{' delimiter char, or single node argument
                argslatex += nodelist_to_latex([argn])
            else:
                raise ValueError("Unknown argument type: {!r}".format(argt))
        return argslatex

    latex = ''
    for n in nodelist:
        if n is None:
            continue
        if isinstance(n, LatexCharsNode):
            latex += n.chars
            continue

        if isinstance(n, LatexMacroNode):
            latex += r'\%s%s%s' %(n.macroname, n.macro_post_space, add_args(n.nodeargd))
            continue

        if isinstance(n, LatexSpecialsNode):
            latex += r'%s%s' %(n.specials_chars, add_args(n.nodeargd))
            continue
        
        if isinstance(n, LatexCommentNode):
            latex += '%'+n.comment+n.comment_post_space
            continue
        
        if isinstance(n, LatexGroupNode):
            latex += n.delimiters[0] + nodelist_to_latex(n.nodelist) + n.delimiters[1]
            continue
        
        if isinstance(n, LatexEnvironmentNode):
            latex += r'\begin{%s}%s' %(n.envname, add_args(n.nodeargd))
            latex += nodelist_to_latex(n.nodelist)
            latex += r'\end{%s}' %(n.envname)
            continue
        
        if isinstance(n, LatexMathNode):
            latex += n.delimiters[0] + nodelist_to_latex(n.nodelist) + n.delimiters[1]
            continue
        
        latex += "<[UNKNOWN LATEX NODE: \'%s\']>"%(type(n).__name__)

    return latex
    



def put_in_braces(brace_char, thestring):
    # DON'T USE. WILL BE REMOVED IN FUTURE VERSION.
    if (brace_char == '{'):
        return '{%s}' %(thestring)
    if (brace_char == '['):
        return '[%s]' %(thestring)
    if (brace_char == '('):
        return '(%s)' %(thestring)
    if (brace_char == '<'):
        return '<%s>' %(thestring)

    return brace_char + thestring + brace_char



def disp_node(n, indent=0, context='* ', skip_group=False):
    # Don't rely upon this function.
    title = ''
    comment = ''
    iterchildren = []

    def add_args():
        if n.nodeargd is None:
            #iterchildren.append(('<no args>', '', None))
            return
        elif n.nodeargd.argspec is None or n.nodeargd.argnlist is None:
            iterchildren.append(('<args> ', '<cannot be displayed>', None))
            return
        for argt, argn in zip(n.nodeargd.argspec, n.nodeargd.argnlist):
            if argt == '[':
                t = '[.]: '
            elif argt == '{':
                t = '{.}: '
            elif argt == '*':
                t = '<*>:   '
            else:
                t = '<unknown>: '
            iterchildren.append((t, [argn], False))

    if n is None:
        title = '<None>'
    elif isinstance(n, LatexCharsNode):
        title = repr(n.chars)
    elif isinstance(n, LatexMacroNode):
        title = '\\'+n.macroname
        add_args()
    elif isinstance(n, LatexSpecialsNode):
        title = n.specials_chars + ' (specials)'
        add_args()
    elif isinstance(n, LatexCommentNode):
        title = '%' + n.comment.strip()
    elif isinstance(n, LatexGroupNode):
        if (skip_group):
            for nn in n.arg:
                disp_node(nn, indent=indent, context=context)
            return
        title = 'Group: '
        iterchildren.append(('* ', n.nodelist, False))
    elif isinstance(n, LatexEnvironmentNode):
        title = '\\begin{%s}' %(n.environmentname)
        add_args()
        iterchildren.append(('* ', n.nodelist, False))
    elif isinstance(n, LatexMathNode):
        title = n.delimiters[0]+n.displaytype+' math'+n.delimiters[1]
        iterchildren.append(('* ', n.nodelist, False))
    else:
        print("UNKNOWN NODE TYPE: %s"%(type(n).__name__))

    print(' '*indent + context + title + '  '+comment)

    for context, nodelist, skip in iterchildren:
        if isinstance(nodelist, _basestring):
            print(' '*(indent+4) + context + nodelist)
            continue
        for nn in nodelist:
            disp_node(nn, indent=indent+4, context=context, skip_group=skip)




# ------------------------------------------------------------------------------


def make_json_encoder(latexwalker, use_line_numbers=True):

    class LatexNodesJSONEncoder(json.JSONEncoder):
        # not official API for now
        """
        A :py:class:`json.JSONEncoder` that can encode :py:class:`LatexNode` objects
        (and subclasses).
        """

        def __init__(self, *args, **kwargs):
            super(LatexNodesJSONEncoder, self).__init__(*args, **kwargs)

        def default(self, obj):
            if isinstance(obj, LatexNode):
                # Prepare a dictionary with the correct keys and values.
                n = obj
                d = {
                    'nodetype': n.__class__.__name__,
                }
                #redundant_fields = getattr(n, '_redundant_fields', n._fields)
                for fld in n._fields:
                    d[fld] = n.__dict__[fld]
                d.update(latexwalker.pos_to_lineno_colno(n.pos, as_dict=True))
                return d

            if isinstance(obj, macrospec.ParsedMacroArgs):
                return obj.to_json_object()

            # else:
            return super(LatexNodesJSONEncoder, self).default(obj)

    
    return LatexNodesJSONEncoder
