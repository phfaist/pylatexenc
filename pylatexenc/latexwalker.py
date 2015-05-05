#
# The MIT License (MIT)
# 
# Copyright (c) 2015 Philippe Faist
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




import re
from collections import namedtuple



class LatexWalkerError(Exception):
    pass

class LatexWalkerParseError(LatexWalkerError):
    def __init__(self, msg, s=None, pos=None):
        self.msg = msg
        self.s = s
        self.pos = pos
        disp = '...'+s[max(pos-25,0):pos];
        disp = '\n%s\n'%(disp)  +  (' '*len(disp)) + s[pos:pos+25]+'...'
        LatexWalkerError.__init__(self, msg + (
            " @ %d:\n%s" %(pos, disp)
            ));

class LatexWalkerEndOfStream(LatexWalkerError):
    pass



MacrosDef = namedtuple('MacrosDef', ['macname', 'optarg', 'numargs'])



macro_list = (
    MacrosDef('documentclass', True, 1),
    MacrosDef('usepackage', True, 1),
    MacrosDef('selectlanguage', True, 1),
    MacrosDef('setlength', True, 2),
    MacrosDef('addlength', True, 2),
    MacrosDef('setcounter', True, 2),
    MacrosDef('addcounter', True, 2),
    MacrosDef('newcommand', None, "{[{"),
    MacrosDef('renewcommand', None, "{[{"),
    MacrosDef('DeclareMathOperator', False, 2),
    MacrosDef('input', False, 1),

    MacrosDef('hspace', False, 1),
    MacrosDef('vspace', False, 1),

    MacrosDef('\\', True, 0), # (Note: single backslash) end of line with optional spacing, e.g.  \\[2mm]
    MacrosDef('item', True, 0),

    MacrosDef('includegraphics', True, 1),

    MacrosDef('textit', False, 1),
    MacrosDef('textbf', False, 1),
    MacrosDef('textsc', False, 1),
    MacrosDef('textsl', False, 1),
    MacrosDef('text', False, 1),
    MacrosDef('mathrm', False, 1),

    MacrosDef('label', False, 1),
    MacrosDef('ref', False, 1),
    MacrosDef('eqref', False, 1),
    MacrosDef('url', False, 1),
    MacrosDef('hypersetup', False, 1),
    MacrosDef('footnote', True, 1),

    MacrosDef('keywords', False, 1),

    MacrosDef('hphantom', True, 1),
    MacrosDef('vphantom', True, 1),

    MacrosDef("'", False, 1),
    MacrosDef("`", False, 1),
    MacrosDef('"', False, 1),
    MacrosDef("c", False, 1),
    MacrosDef("^", False, 1),
    MacrosDef("~", False, 1),
    MacrosDef("H", False, 1),
    MacrosDef("k", False, 1),
    MacrosDef("=", False, 1),
    MacrosDef("b", False, 1),
    MacrosDef(".", False, 1),
    MacrosDef("d", False, 1),
    MacrosDef("r", False, 1),
    MacrosDef("u", False, 1),
    MacrosDef("v", False, 1),

    MacrosDef("vec", False, 1),
    MacrosDef("dot", False, 1),
    MacrosDef("hat", False, 1),
    MacrosDef("check", False, 1),
    MacrosDef("breve", False, 1),
    MacrosDef("acute", False, 1),
    MacrosDef("grave", False, 1),
    MacrosDef("tilde", False, 1),
    MacrosDef("bar", False, 1),
    MacrosDef("ddot", False, 1),


    MacrosDef('frac', False, 2),
    MacrosDef('nicefrac', False, 2),

    MacrosDef('sqrt', True, 1),

    MacrosDef('ket', False, 1),
    MacrosDef('bra', False, 1),
    MacrosDef('braket', False, 2),
    MacrosDef('ketbra', False, 2),

    MacrosDef('texorpdfstring', False, 2),

    # ethuebung
    MacrosDef('UebungLoesungFont', False, 1),
    MacrosDef('UebungHinweisFont', False, 1),
    MacrosDef('UebungExTitleFont', False, 1),
    MacrosDef('UebungSubExTitleFont', False, 1),
    MacrosDef('UebungTipsFont', False, 1),
    MacrosDef('UebungLabel', False, 1),
    MacrosDef('UebungSubLabel', False, 1),
    MacrosDef('UebungLabelEnum', False, 1),
    MacrosDef('UebungLabelEnumSub', False, 1),
    MacrosDef('UebungSolLabel', False, 1),
    MacrosDef('UebungHinweisLabel', False, 1),
    MacrosDef('UebungHinweiseLabel', False, 1),
    MacrosDef('UebungSolEquationLabel', False, 1),
    MacrosDef('UebungTipsLabel', False, 1),
    MacrosDef('UebungTipsEquationLabel', False, 1),
    MacrosDef('UebungsblattTitleSeries', False, 1),
    MacrosDef('UebungsblattTitleSolutions', False, 1),
    MacrosDef('UebungsblattTitleTips', False, 1),
    MacrosDef('UebungsblattNumber', False, 1),
    MacrosDef('UebungsblattTitleFont', False, 1),
    MacrosDef('UebungTitleCenterVSpacing', False, 1),
    MacrosDef('UebungAttachedSolutionTitleTop', False, 1),
    MacrosDef('UebungAttachedSolutionTitleFont', False, 1),
    MacrosDef('UebungAttachedSolutionTitle', False, 1),
    MacrosDef('UebungTextAttachedSolution', False, 1),
    MacrosDef('UebungDueByLabel', False, 1),
    MacrosDef('UebungDueBy', False, 1),
    MacrosDef('UebungLecture', False, 1),
    MacrosDef('UebungProf', False, 1),
    MacrosDef('UebungLecturer', False, 1),
    MacrosDef('UebungSemester', False, 1),
    MacrosDef('UebungLogoFile', False, 1),
    MacrosDef('UebungLanguage', False, 1),
    MacrosDef('UebungStyle', False, 1),
    #
    MacrosDef('uebung', False, '{['),
    MacrosDef('exercise', False, '{['),
    MacrosDef('keywords', False, 1),
    MacrosDef('subuebung', False, 1),
    MacrosDef('subexercise', False, 1),
    MacrosDef('pdfloesung', True, 1),
    MacrosDef('pdfsolution', True, 1),
    MacrosDef('exenumfulllabel', False, 1),
    MacrosDef('hint', False, 1),
    MacrosDef('hints', False, 1),
    MacrosDef('hinweis', False, 1),
    MacrosDef('hinweise', False, 1),

    );

macro_dict = dict([(m.macname, m) for m in macro_list]);



LatexToken = namedtuple('LatexToken', ['tok', 'arg', 'pos', 'len', 'pre_space'])


class LatexNode(object):
    """
    Represents an abstract 'node' of the latex document.

    Use :py:meth:`nodeType()` to figure out what type of node this is.
    """
    def __init__(self, **kwargs):
        super(LatexNode, self).__init__(**kwargs)

    def nodeType(self):
        return LatexNode

    def isNodeType(self, t):
        return isinstance(self, t)
        

class LatexCharsNode(LatexNode):
    """
    A string of characters in the LaTeX document, without any special meaning.
    """
    def __init__(self, chars, **kwargs):
        r"""
        Arguments:
            - `chars`: the actual characters.
        """
        super(LatexCharsNode, self).__init__(**kwargs)
        self.chars = chars

    def nodeType(self):
        return LatexCharsNode

class LatexGroupNode(LatexNode):
    r"""
    A LaTeX group, i.e. `{...}`.
    """
    def __init__(self, nodelist, **kwargs):
        """
        Arguments:
            - `nodelist`: a list of nodes which comprise the group.
        """
        super(LatexNode, self).__init__(**kwargs)
        self.nodelist = nodelist

    def nodeType(self):
        return LatexGroupNode

class LatexCommentNode(LatexNode):
    def __init__(self, comment, **kwargs):
        super(LatexCommentNode, self).__init__(**kwargs)
        self.comment = comment

    def nodeType(self):
        return LatexCommentNode

class LatexMacroNode(LatexNode):
    r"""
    Represents a 'macro' type node, e.g. '\textbf'
    """
    def __init__(self, macroname, nodeoptarg=None, nodeargs=[], **kwargs):
        r"""
        Represents a 'macro' type node, e.g. '\textbf'

        Arguments:
            - `macroname`: the name of the macro (string), *without* the leading
              backslash
            - `nodeoptarg`: if non-`None`, this corresponds to the optional argument
              of the macro
            - `nodeargs`: a list of arguments to the macro. Each item in the list
              should be a LatexNode.
        """
        super(LatexMacroNode, self).__init__(**kwargs)
        self.macroname = macroname
        self.nodeoptarg = nodeoptarg
        self.nodeargs = nodeargs

    def nodeType(self):
        return LatexMacroNode

class LatexEnvironmentNode(LatexNode):
    def __init__(self, envname, nodelist, optargs=[], args=[], **kwargs):
        r"""
        A LaTeX Environment Node, i.e. `\begin{something} ... \end{something}`.

        Arguments:
            - `envname`: the name of the environment ('itemize', 'equation', ...)
            - `nodelist`: a list of :py:class:`LatexNode`'s that represent all the
              contents between the `\begin{...}` instruction and the `\end{...}`
              instruction.
            - `optargs`: any possible optional argument passed to the `\begin{...}`
              instruction, for example in `\begin{enumerate}[label=\roman*)]
              (Currently, only a single optional argument is parsed, but this is
              anyway a list of :py:class:`LatexNode`'s.)
            - `args`: any possible regular arguments passed to the `\begin{...}`
              instruction, for example in `\begin{tabular}{clr}`. Currently, only a
              single regular argument is parsed at maximum, but this is anyway a
              list of :py:class:`LatexNode`'s.
        """
        super(LatexEnvironmentNode, self).__init__(**kwargs)
        self.envname = envname
        self.nodelist = nodelist
        self.optargs = optargs
        self.args = args

    def nodeType(self):
        return LatexEnvironmentNode

class LatexMathNode(LatexNode):
    def __init__(self, displaytype, nodelist=[], **kwargs):
        r"""
        A Math node type.

        Arguments:
            - `displaytype`: either 'inline' or 'display'
        """
        super(LatexMathNode, self).__init__(**kwargs)
        self.displaytype = displaytype
        self.nodelist = nodelist

    def nodeType(self):
        return LatexMathNode


def get_token(s, pos, brackets_are_chars=True, environments=True, **parse_flags):
    """
    Parse the next token in the stream.

    Returns a `LatexToken`. Raises `LatexWalkerEndOfStream` if end of stream reached.

    """

    space = '';
    while (pos < len(s) and s[pos].isspace()):
        space += s[pos];
        pos += 1;
        if (space.endswith('\n\n')):  # two \n's indicate new paragraph.
            # pre-space is overkill here I think.
            return LatexToken(tok='char', arg='\n\n', pos=pos-2, len=2, pre_space='');


    if (pos >= len(s)):
        raise LatexWalkerEndOfStream()

    if (s[pos] == '\\'):
        # escape sequence
        i = 2
        macro = s[pos+1] # next char is necessarily part of macro
        # following chars part of macro only if all are alphabetical
        if (s[pos+1].isalpha()):
            while pos+i<len(s) and s[pos+i].isalpha():
                macro += s[pos+i]
                i += 1;
        # possibly followed by a star
        if (pos+i<len(s) and s[pos+i] == '*'):
            macro += '*'
            i += 1

        # see if we have a begin/end environment
        if (environments and (macro == 'begin' or macro == 'end')):
            # \begin{environment} or \end{environment}
            envmatch = re.match(r'^\s*\{([\w*]+)\}', s[pos+i:])
            if (envmatch is None):
                raise LatexWalkerParseError(s=s, pos=pos, msg="Bad \\%s macro: expected {environment}" %(macro))

            return LatexToken(
                tok=('begin_environment' if macro == 'begin' else  'end_environment'),
                arg=envmatch.group(1),
                pos=pos,
                len=i+envmatch.end(), # !!envmatch.end() counts from pos+i
                pre_space=space
                );

        # # possibly eat one following whitespace
        # if (s[pos+i].isspace()):
        #     i += 1;
        
        return LatexToken(tok='macro', arg=macro, pos=pos, len=i, pre_space=space);

    if (s[pos] == '%'):
        # latex comment
        m = re.search(r'(\n|\r|\n\r)\s*', s[pos:])
        mlen = None
        if (m is not None):
            mlen = m.end(); # relative to pos already
        else:
            mlen = len(s)-pos;# [  ==len(s[pos:])  ]
        return LatexToken(tok='comment', arg=s[pos+1:pos+mlen], pos=pos, len=mlen, pre_space=space)
    
    openbracechars = '{';
    closebracechars = '}';
    if (not brackets_are_chars):
        openbracechars += '[';
        closebracechars += ']';

    if (s[pos] in openbracechars):
        return LatexToken(tok='brace_open', arg=s[pos], pos=pos, len=1, pre_space=space)

    if (s[pos] in closebracechars):
        return LatexToken(tok='brace_close', arg=s[pos], pos=pos, len=1, pre_space=space)

    # check if it is an inline math char, if we care about inline math.
    if (s[pos] == '$' and parse_flags.get('keep_inline_math', False)):
        # check that we don't have double-$$, which would be a display environment.
        if not (pos+1 < len(s) and s[pos+1] == '$'):
            return LatexToken(tok='mathmode_inline', arg=s[pos], pos=pos, len=1, pre_space=space);
        # otherwise, proceed to 'char' type.
        

    return LatexToken(tok='char', arg=s[pos], pos=pos, len=1, pre_space=space)



def get_latex_expression(s, pos, strict_braces=False, **parse_flags):
    """
    Reads a latex expression, e.g. macro argument. This may be a single char, an escape
    sequence, or a expression placed in braces.

    Returns a tuple `(<LatexNode instance>, pos, len)`. `pos` is the first char of the
    expression, and `len` is its length.
    """

    # keep these in parse_flags for when we call child functions
    tolerant_parsing = parse_flags.get('tolerant_parsing', False);

    pp = dict([(k,v) for (k,v) in parse_flags.iteritems()]);
    pp['keep_inline_math'] = False; # no inline math char

    tok = get_token(s, pos, environments=False, **pp);

    if (tok.tok == 'macro'):
        if (tok.arg == 'end'):
            if (not tolerant_parsing):
                # error, this should be an \end{environment}, not an argument in itself
                raise LatexWalkerParseError("Expected expression, got \end", s, pos);
            else:
                return (LatexCharsNode(chars=''), tok.pos, 0)
        return (LatexMacroNode(macroname=tok.arg, nodeoptarg=None, nodeargs=[]),
                tok.pos, tok.len)
    if (tok.tok == 'comment'):
        return get_latex_expression(s, pos+tok.len, **parse_flags)
    if (tok.tok == 'brace_open'):
        return get_latex_braced_group(s, tok.pos, **parse_flags)
    if (tok.tok == 'brace_close'):
        if (strict_braces and not tolerant_parsing):
            raise LatexWalkerParseError("Expected expression, got closing brace!", s, pos);
        return (LatexCharsNode(chars=''), tok.pos, 0)
    if (tok.tok == 'char'):
        return (LatexCharsNode(chars=tok.arg), tok.pos, tok.len)

    raise LatexWalkerParseError("Unknown token type: %s" %(tok.tok), s, pos)


def get_latex_maybe_optional_arg(s, pos, **parse_flags):
    """
    Attempts to parse an optional argument. Returns a tuple `(groupnode, pos, len)` if
    success, otherwise returns None.
    """
    
    tok = get_token(s, pos, brackets_are_chars=False, environments=False, **parse_flags);
    if (tok.tok == 'brace_open' and tok.arg == '['):
        return get_latex_braced_group(s, pos, brace_type='[', **parse_flags)

    return None

    
def get_latex_braced_group(s, pos, brace_type='{', **parse_flags):
    """
    Reads a latex expression enclosed in braces {...}. The first token of `s[pos:]` must
    be an opening brace.

    Returns a tuple `(node, pos, len)`. `pos` is the first char of the
    expression (which has to be an opening brace), and `len` is its length,
    including the closing brace.
    """

    closing_brace = None
    if (brace_type == '{'):
        closing_brace = '}'
    elif (brace_type == '['):
        closing_brace = ']'
    else:
        raise LatexWalkerParseError(s=s, pos=pos, msg="Uknown brace type: %s" %(brace_type));
    brackets_are_chars = (brace_type != '[');

    firsttok = get_token(s, pos, brackets_are_chars=brackets_are_chars, **parse_flags)
    if (firsttok.tok != 'brace_open'  or  firsttok.arg != brace_type):
        raise LatexWalkerParseError(s=s, pos=pos,
                                    msg='get_latex_braced_group: not an opening brace/bracket: %s' %(s[pos]));

    #pos = firsttok.pos + firsttok.len;

    (nodelist, npos, nlen) = get_latex_nodes(s, firsttok.pos + firsttok.len,
                                             stop_upon_closing_brace=closing_brace, **parse_flags);

    return (LatexGroupNode(nodelist=nodelist), firsttok.pos, npos + nlen - firsttok.pos)


def get_latex_environment(s, pos, environmentname=None, **parse_flags):
    """
    Reads a latex expression enclosed in a \\begin{environment}...\\end{environment}. The first
    token in the stream must be the \\begin{environment}.

    Returns a tuple (node, pos, len) with node being a :py:class:`LatexEnvironmentNode`.
    """

    firsttok = get_token(s, pos, **parse_flags)
    if (firsttok.tok != 'begin_environment'  or
        (environmentname is not None and firsttok.arg != environmentname)):
        raise LatexWalkerParseError(s=s, pos=pos,
                                    msg=r'get_latex_environment: expected \begin{%s}: %s' %(
            environmentname if environmentname is not None else '<environment name>',
            tok.arg
            ));
    if (environmentname is None):
        environmentname = firsttok.arg;
    
    pos = firsttok.pos + firsttok.len;


    optargs = []
    args = []
    
    # see if the \begin{environment} is immediately followed by some options.
    # BUG: Don't eat the brace of a commutator!! impose no space.
    optargtuple = None;
    if (s[pos] == '['):
        optargtuple = get_latex_maybe_optional_arg(s, pos)

    if (optargtuple is not None):
        optargs.append(optargtuple[0])
        pos = optargtuple[1]+optargtuple[2];
    else:
        # try to see if we have a mandatory argument
        # don't use get_token as we don't want to skip any space.
        if s[pos] == '{':
            (argnode, apos, alen) = get_latex_braced_group(s, pos)
            args.append(argnode)
            pos = apos+alen;

    (nodelist, npos, nlen) = get_latex_nodes(s, pos, stop_upon_end_environment=environmentname, **parse_flags);

    return (LatexEnvironmentNode(envname=environmentname,
                                 nodelist=nodelist,
                                 optargs=optargs,
                                 args=args),
            pos, npos+nlen-pos);

def get_latex_nodes(s, pos=0, stop_upon_closing_brace=None, stop_upon_end_environment=None,
                    stop_upon_closing_mathmode=None, keep_inline_math=False, tolerant_parsing=False):
    """
    Parses latex content `s`.

    Returns a tuple `(nodelist, pos, len)` where nodelist is a list of `LatexNode` 's.

    If `stop_upon_closing_brace` is given, then `len` includes the closing brace, but the
    closing brace is not included in any of the nodes in the `nodelist`.
    """

    # what we'll pass on to recursive calls
    parse_flags = {
        'keep_inline_math': keep_inline_math,
        'tolerant_parsing': tolerant_parsing,
        };

    nodelist = [];
    
    brackets_are_chars = True;
    if (stop_upon_closing_brace == ']'):
        brackets_are_chars = False;

    origpos = pos;

    class PosPointer:
        def __init__(self, pos=0, lastchars=''):
            self.pos = pos
            self.lastchars = lastchars

    p = PosPointer(pos)

    def do_read(nodelist, s, p):
        """
        Read a single token and process it, recursing into brace blocks and environments etc if
        needed, and appending stuff to nodelist.

        Return True whenever we should stop trying to read more. (e.g. upon reaching the a matched
        stop_upon_end_environment etc.)
        """

        try:
            tok = get_token(s, p.pos, brackets_are_chars=brackets_are_chars, **parse_flags);
        except LatexWalkerEndOfStream:
            if tolerant_parsing:
                return True
            raise # re-raise

        p.pos = tok.pos + tok.len;

        # if it's a char, just append it to the stream of last characters.
        if (tok.tok == 'char'):
            p.lastchars += tok.pre_space + tok.arg
            return False

        # maybe add the pre_space of the new token to lastchars, if applicable.
        #if (len(tok.pre_space)):
        #    p.lastchars += tok.pre_space # yields wayyy tooo much space in output!!
            
        # if it's not a char, push the last `p.lastchars` into the node list before anything else
        if (len(p.lastchars)):
            strnode = LatexCharsNode(chars=p.lastchars+tok.pre_space);
            nodelist.append(strnode);
            p.lastchars = ''; # reset lastchars.

        # and see what the token is.

        if (tok.tok == 'brace_close'):
            # we've reached the end of the group. stop the parsing.
            if (tok.arg != stop_upon_closing_brace):
                if (not tolerant_parsing):
                    raise LatexWalkerParseError(s=s, pos=tok.pos,
                                                msg='Unexpected mismatching closing brace: `%s\'' %(tok.arg))
                return False
            return True

        if (tok.tok == 'end_environment'):
            # we've reached the end of an environment.
            if (tok.arg != stop_upon_end_environment):
                if (not tolerant_parsing):
                    raise LatexWalkerParseError(s=s, pos=tok.pos,
                                                msg=('Unexpected mismatching closing environment: `%s\', '
                                                     'expecting `%s\'' %(tok.arg, stop_upon_end_environment))
                                                )
                return False
            return True

        if (tok.tok == 'mathmode_inline'):
            # if we care about keeping math mode inlines verbatim, gulp all of the expression.
            if (stop_upon_closing_mathmode is not None):
                if (stop_upon_closing_mathmode != '$'):
                    raise LatexWalkerParseError(s=s, pos=tok.pos,
                                                msg='Unexpected mismatching closing math mode: `$\'');
                return True

            # we have encountered a new math inline, so gulp all of the math expression
            (mathinline_nodelist, mpos, mlen) = get_latex_nodes(s, p.pos, stop_upon_closing_mathmode='$',
                                                                **parse_flags);
            p.pos = mpos + mlen;

            nodelist.append(LatexMathNode(displaytype='inline',
                                          nodelist=mathinline_nodelist));
            return

        if (tok.tok == 'comment'):
            commentnode = LatexCommentNode(comment=tok.arg);
            nodelist.append(commentnode)
            return

        if (tok.tok == 'brace_open'):
            # another braced group to read.
            (groupnode, bpos, blen) = get_latex_braced_group(s, tok.pos, **parse_flags);
            p.pos = bpos + blen;
            nodelist.append(groupnode)
            return

        if (tok.tok == 'begin_environment'):
            # an environment to read.
            (envnode, epos, elen) = get_latex_environment(s, tok.pos, environmentname=tok.arg, **parse_flags);
            p.pos = epos + elen;
            # add node and continue.
            nodelist.append(envnode)
            return

        if (tok.tok == 'macro'):
            # read a macro. see if it has arguments.
            nodeoptarg = None
            nodeargs = []
            macname = tok.arg.rstrip('*');
            if (macname in macro_dict):
                mac = macro_dict[macname]

                def getoptarg(s, pos):
                    """Gets a possibly optional argument. returns (argnode, new-pos) where argnode might
                    be `None` if the argument was not specified."""
                    optarginfotuple = get_latex_maybe_optional_arg(s, pos, **parse_flags);
                    if (optarginfotuple is not None):
                        (nodeoptarg, optargpos, optarglen) = optarginfotuple
                        return (nodeoptarg, optargpos+optarglen)
                    return (None, pos)

                def getarg(s, pos):
                    """Gets a mandatory argument. returns (argnode, new-pos)"""
                    (nodearg, npos, nlen) = get_latex_expression(s, pos, strict_braces=False, **parse_flags)
                    return (nodearg, npos + nlen)
                    
                if (mac.optarg):
                    (nodeoptarg, p.pos) = getoptarg(s, p.pos);

                if (isinstance(mac.numargs, basestring)):
                    # specific argument specification
                    for arg in mac.numargs:
                        if (arg == '{'):
                            (node, p.pos) = getarg(s, p.pos)
                            nodeargs.append(node)
                        elif (arg == '['):
                            (node, p.pos) = getoptarg(s, p.pos)
                            nodeargs.append(node)
                        else:
                            raise LatexWalkerError("Unknown macro argument kind for macro %s: %s"
                                                   % (mac.macroname, arg));
                else:
                    for n in range(mac.numargs):
                        (nodearg, p.pos) = getarg(s, p.pos)
                        nodeargs.append(nodearg)
                

            #import pdb; pdb.set_trace()
            
            nodelist.append(LatexMacroNode(macroname=tok.arg,
                                           nodeoptarg=nodeoptarg,
                                           nodeargs=nodeargs));
            return None

        raise LatexWalkerParseError(s=s, pos=p.pos, msg="Uknown token: %r" %(tok));

    

    while True:
        try:
            r_endnow = do_read(nodelist, s, p);
        except LatexWalkerEndOfStream:
            if (stop_upon_closing_brace or stop_upon_end_environment):
                # unexpected eof
                if (not tolerant_parsing):
                    raise LatexWalkerError("Unexpected end of stream!")
                else:
                    r_endnow = False
            else:
                r_endnow = True
            
        if (r_endnow):
            # add last chars
            if (p.lastchars):
                strnode = LatexCharsNode(chars=p.lastchars);
                nodelist.append(strnode);
            return (nodelist, origpos, p.pos - origpos)

    raise LatexWalkerError("CONGRATULATIONS !! "
                           "You are the first human to telepathically break an infinite loop !!!!!!!")


def put_in_braces(brace_char, thestring):
    if (brace_char == '{'):
        return '{%s}' %(thestring);
    if (brace_char == '['):
        return '[%s]' %(thestring);
    if (brace_char == '('):
        return '(%s)' %(thestring);
    if (brace_char == '<'):
        return '<%s>' %(thestring);

    return brace_char + thestring + brace_char;


def nodelist_to_latex(nodelist):
    latex = '';
    for n in nodelist:
        if n is None:
            continue
        if n.isNodeType(LatexCharsNode):
            latex += n.chars;
            continue
        if n.isNodeType(LatexMacroNode):
            latex += r'\%s' %(n.macroname);

            mac = None;
            if (n.macroname in macro_dict):
                mac = macro_dict[n.macroname]
            
            if (n.nodeoptarg is not None):
                latex += '[%s]' %(nodelist_to_latex([n.nodeoptarg]));

            if mac is not None:
                macbraces = (mac.numargs if isinstance(mac.numargs, basestring) else '{'*mac.numargs);
            else:
                macbraces = '{'*len(n.nodeargs);
                
            i = 0;
            if (len(n.nodeargs) != len(macbraces)):
                raise LatexWalkerError("Error: number of arguments (%d) provided to macro `\\%s' does not "
                                       "match its specification of `%s'"
                                       %(len(n.nodeargs), n.macroname, macbraces));
            for i in range(len(n.nodeargs)):
                nodearg = n.nodeargs[i]
                if nodearg is not None:
                    latex += put_in_braces(macbraces[i], nodelist_to_latex([nodearg]));

            continue
        
        if n.isNodeType(LatexCommentNode):
            latex += '%'+n.comment;
            continue
        
        if n.isNodeType(LatexGroupNode):
            latex += put_in_braces('{', nodelist_to_latex(n.nodelist));
            continue
        
        if n.isNodeType(LatexEnvironmentNode):
            latex += r'\begin{%s}' %(n.envname);
            for optarg in n.optargs:
                latex += put_in_braces('[', nodelist_to_latex([optarg]));
            for arg in n.args:
                latex += put_in_braces('{', nodelist_to_latex([arg]));
            latex += nodelist_to_latex(n.nodelist);
            latex += r'\end{%s}' %(n.envname);
            continue
        
        latex += '<[UNKNOWN LATEX NODE: `%s\']>' %(n.nodeType().__name__);

    return latex



def math_node_to_latex(node):

    if (not node.isNodeType(LatexMathNode)):
        raise LatexWalkerError("Expected math node, got `%s'" %(node.nodeType().__name__));

    if (node.displaytype == 'inline'):
        return '$%s$' %(nodelist_to_latex(node.nodelist));
    if (node.displaytype == 'display'):
        return '$$%s$$' %(nodelist_to_latex(node.nodelist));

    raise LatexWalkerError("Unkonwn displaytype: `%s'" %(node.displaytype));



def disp_node(n, indent=0, context='* ', skip_group=False):
    title = '';
    comment = '';
    iterchildren = [];
    if n is None:
        title = '<None>'
    elif n.isNodeType(LatexCharsNode):
        title = "'%s'" %(n.chars.strip());
    elif n.isNodeType(LatexMacroNode):
        title = '\\'+n.macroname;
        #comment = 'opt arg?: %d; %d args' % (n.arg.nodeoptarg is not None, len(n.arg.nodeargs));
        if (n.nodeoptarg):
            iterchildren.append(('[...]: ', [n.nodeoptarg], False));
        if (len(n.nodeargs)):
            iterchildren.append(('{...}: ', n.nodeargs, False));
    elif n.isNodeType(LatexCommentNode):
        title = '%' + n.comment.strip()
    elif n.isNodeType(LatexGroupNode):
        if (skip_group):
            for nn in n.arg:
                disp_node(nn, indent=indent, context=context);
            return
        title = 'Group: '
        iterchildren.append(('* ', n.nodelist, False));

    elif n.isNodeType(LatexEnvironmentNode):
        title = '\\begin{%s}' %(n.envname)
        iterchildren.append(('* ', n.nodelist, False));
    else:
        print "UNKNOWN NODE TYPE: %s"%(n.nodeType().__name__)

    print ' '*indent + context + title + '  '+comment

    for context, nodelist, skip in iterchildren:
        for nn in nodelist:
            disp_node(nn, indent=indent+4, context=context, skip_group=skip)




if __name__ == '__main__':


    try:

        #latex = '\\textit{hi there!} This is {\em an equation}: \\begin{equation}\n a + bi = 0\n\\end{equation}\n\nwhere $i$ is the imaginary unit.\n';
        #nodelist = get_latex_nodes_debug(latex);
        #print repr(nodelist);


        import fileinput

        latex = ''
        for line in fileinput.input():
            latex += line;

        (nodes, pos, llen) = get_latex_nodes(latex);

        print '\n--- NODES ---\n'
        print repr(nodes);
        print '\n-------------\n'

        print '\n--- NODES ---\n'
        for n in nodes:
            disp_node(n)
        print '\n-------------\n'

    except:
        import pdb;
        import sys;
        print "\nEXCEPTION: " + unicode(sys.exc_info()[1]) + "\n"
        pdb.post_mortem()

