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



import re;
import unicodedata;
import latexwalker;
import logging;


log = logging.getLogger(__name__);



class EnvDef:
    def __init__(self, envname, simplify_repl=None, discard=False):
        self.envname = envname
        self.simplify_repl = simplify_repl
        self.discard = discard

class MacroDef:
    def __init__(self, macname, simplify_repl=None, discard=None):
        """
        Arguments:
            - `macname`: the name of the macro (no backslash)
            - `simplify_repl`: either a string or a callable. The string
              may contain '%s' replacements, in which the macro arguments
              will be substituted. The callable should accept the
              :py:class:`~latexwalker.LatexMacroNode` as an argument.
        """
        if (isinstance(macname, MacroDef)):
            o = macname
            self.macname = o.macname
            self.discard = o.discard
            self.simplify_repl = o.simplify_repl
        elif (isinstance(macname, tuple)):
            (self.macname, self.simplify_repl) = macname
            self.discard = True if (discard is None) else discard ;
            if (simplify_repl is not None or discard is not None):
                raise ValueError("macname=%r is tuple but other parameters specified" %(macname,))
        else:
            self.macname = macname
            self.discard = True if (discard is None) else discard ;
            self.simplify_repl = simplify_repl


env_list = [
    EnvDef('', discard=False), # default for unknown environments

    EnvDef('equation', discard=False),
    EnvDef('eqnarray', discard=False),
    EnvDef('align', discard=False),
    EnvDef('multline', discard=False),

    # spaces added so that database indexing doesn't index the word "array" or "pmatrix"
    EnvDef('array', simplify_repl='< a r r a y >'),
    EnvDef('pmatrix', simplify_repl='< p m a t r i x >'),
    EnvDef('bmatrix', simplify_repl='< b m a t r i x >'),
    EnvDef('smallmatrix', simplify_repl='< s m a l l m a t r i x >'),

    EnvDef('center', simplify_repl='\n%s\n'),
    EnvDef('flushleft', simplify_repl='\n%s\n'),
    EnvDef('flushright', simplify_repl='\n%s\n'),
    
    EnvDef('exenumerate', discard=False),
    EnvDef('enumerate', discard=False),
    EnvDef('list', discard=False),
    EnvDef('itemize', discard=False),
    EnvDef('subequations', discard=False),
    EnvDef('figure', discard=False),
    EnvDef('table', discard=False),
    ];


# NOTE: macro will only be assigned arguments if they are explicitely defined as accepting arguments
#       in latexwalker.py.

macro_list = [
    MacroDef('', discard=True), # default for unknown macros

    MacroDef('textbf', discard=False),
    MacroDef('textit', discard=False),
    MacroDef('textsl', discard=False),
    MacroDef('textsc', discard=False),
    MacroDef('text', discard=False),
    MacroDef('mathrm', discard=False),

    # spaces added so that database indexing doesn't index the word "graphics"
    ('includegraphics', '< g r a p h i c s >'),

    ('ref', '<ref>'),
    ('eqref', '(<ref>)'),
    ('url', '<%s>'),
    ('item', lambda r: '\n  '+(latexnodes2text([r.nodeoptarg]) if r.nodeoptarg else '*')),
    ('footnote', '[%s]'),

    ('texorpdfstring', lambda node: latexnodes2text(node.nodeargs[1:2])), # use second argument

    ('oe', u'\u0153'),
    ('OE', u'\u0152'),
    ('ae', u'\u00e6'),
    ('AE', u'\u00c6'),
    ('aa', u'\u00e5'), # a norvegien/nordique
    ('AA', u'\u00c5'), # A norvegien/nordique
    ('o', u'\u00f8'), # o norvegien/nordique
    ('O', u'\u00d8'), # O norvegien/nordique
    ('ss', u'\u00df'), # s-z allemand
    ('L', u"\N{LATIN CAPITAL LETTER L WITH STROKE}"),
    ('l', u"\N{LATIN SMALL LETTER L WITH STROKE}"),
    ('i', u"\N{LATIN SMALL LETTER DOTLESS I}"),
    ('j', u"\N{LATIN SMALL LETTER DOTLESS J}"),

    ("~", "~" ),
    ("&", "\\&" ), # HACK, see below for text replacement of '&'
    ("$", "$" ),
    ("{", "{" ),
    ("}", "}" ),
    ("%", lambda arg: u"%" ), # careful: % is formatting substituion symbol...
    ("#", "#" ),
    ("_", "_" ),

    ("\\", '\n'),

    ("textquoteleft", "`"),
    ("textquoteright", "'"),
    ("textquotedblright", u"\N{RIGHT DOUBLE QUOTATION MARK}"),
    ("textquotedblleft", u"\N{LEFT DOUBLE QUOTATION MARK}"),
    ("textendash", u"\N{EN DASH}"),
    ("textemdash", u"\N{EM DASH}"),

    ('textpm', u"\N{PLUS-MINUS SIGN}"),
    ('textmp', u"\N{MINUS-OR-PLUS SIGN}"),

    ("texteuro", u"\N{EURO SIGN}"),

    # math stuff

    ("hbar", u"\N{LATIN SMALL LETTER H WITH STROKE}"),
    ("ell", u"\N{SCRIPT SMALL L}"),

    ('forall', u"\N{FOR ALL}"),
    ('complement', u"\N{COMPLEMENT}"),
    ('partial', u"\N{PARTIAL DIFFERENTIAL}"),
    ('exists', u"\N{THERE EXISTS}"),
    ('nexists', u"\N{THERE DOES NOT EXIST}"),
    ('varnothing', u"\N{EMPTY SET}"),
    ('emptyset', u"\N{EMPTY SET}"),
    # increment?
    ('nabla', u"\N{NABLA}"),
    #
    ('in', u"\N{ELEMENT OF}"),
    ('notin', u"\N{NOT AN ELEMENT OF}"),
    ('ni', u"\N{CONTAINS AS MEMBER}"),
    ('prod', u'\N{N-ARY PRODUCT}'),
    ('coprod', u'\N{N-ARY COPRODUCT}'),
    ('sum', u'\N{N-ARY SUMMATION}'),
    ('setminus', u'\N{SET MINUS}'),
    ('smallsetminus', u'\N{SET MINUS}'),
    ('ast', u'\N{ASTERISK OPERATOR}'),
    ('circ', u'\N{RING OPERATOR}'),
    ('bullet', u'\N{BULLET OPERATOR}'),
    ('sqrt', u'\N{SQUARE ROOT}(%s)'),
    ('propto', u'\N{PROPORTIONAL TO}'),
    ('infty', u'\N{INFINITY}'),
    ('parallel', u'\N{PARALLEL TO}'),
    ('nparallel', u'\N{NOT PARALLEL TO}'),
    ('wedge', u"\N{LOGICAL AND}"),
    ('vee', u"\N{LOGICAL OR}"),
    ('cap', u'\N{INTERSECTION}'),
    ('cup', u'\N{UNION}'),
    ('int', u'\N{INTEGRAL}'),
    ('iint', u'\N{DOUBLE INTEGRAL}'),
    ('iiint', u'\N{TRIPLE INTEGRAL}'),
    ('oint', u'\N{CONTOUR INTEGRAL}'),

    ('sim', u'\N{TILDE OPERATOR}'),
    ('backsim', u'\N{REVERSED TILDE}'),
    ('simeq', u'\N{ASYMPTOTICALLY EQUAL TO}'),
    ('approx', u'\N{ALMOST EQUAL TO}'),
    ('neq', u'\N{NOT EQUAL TO}'),
    ('equiv', u'\N{IDENTICAL TO}'),
    ('ge', u'>'),#
    ('le', u'<'),#
    ('leq', u'\N{LESS-THAN OR EQUAL TO}'),
    ('geq', u'\N{GREATER-THAN OR EQUAL TO}'),
    ('leqslant', u'\N{LESS-THAN OR EQUAL TO}'),
    ('geqslant', u'\N{GREATER-THAN OR EQUAL TO}'),
    ('leqq', u'\N{LESS-THAN OVER EQUAL TO}'),
    ('geqq', u'\N{GREATER-THAN OVER EQUAL TO}'),
    ('lneqq', u'\N{LESS-THAN BUT NOT EQUAL TO}'),
    ('gneqq', u'\N{GREATER-THAN BUT NOT EQUAL TO}'),
    ('ll', u'\N{MUCH LESS-THAN}'),
    ('gg', u'\N{MUCH GREATER-THAN}'),
    ('nless', u'\N{NOT LESS-THAN}'),
    ('ngtr', u'\N{NOT GREATER-THAN}'),
    ('nleq', u'\N{NEITHER LESS-THAN NOR EQUAL TO}'),
    ('ngeq', u'\N{NEITHER GREATER-THAN NOR EQUAL TO}'),
    ('lesssim', u'\N{LESS-THAN OR EQUIVALENT TO}'),
    ('gtrsim', u'\N{GREATER-THAN OR EQUIVALENT TO}'),
    ('lessgtr', u'\N{LESS-THAN OR GREATER-THAN}'),
    ('gtrless', u'\N{GREATER-THAN OR LESS-THAN}'),
    ('prec', u'\N{PRECEDES}'),
    ('succ', u'\N{SUCCEEDS}'),
    ('preceq', u'\N{PRECEDES OR EQUAL TO}'),
    ('succeq', u'\N{SUCCEEDS OR EQUAL TO}'),
    ('precsim', u'\N{PRECEDES OR EQUIVALENT TO}'),
    ('succsim', u'\N{SUCCEEDS OR EQUIVALENT TO}'),
    ('nprec', u'\N{DOES NOT PRECEDE}'),
    ('nsucc', u'\N{DOES NOT SUCCEED}'),
    ('subset', u'\N{SUBSET OF}'),
    ('supset', u'\N{SUPERSET OF}'),
    ('subseteq', u'\N{SUBSET OF OR EQUAL TO}'),
    ('supseteq', u'\N{SUPERSET OF OR EQUAL TO}'),
    ('nsubseteq', u'\N{NEITHER A SUBSET OF NOR EQUAL TO}'),
    ('nsupseteq', u'\N{NEITHER A SUPERSET OF NOR EQUAL TO}'),
    ('subsetneq', u'\N{SUBSET OF WITH NOT EQUAL TO}'),
    ('supsetneq', u'\N{SUPERSET OF WITH NOT EQUAL TO}'),


    ('cdot', u'\N{MIDDLE DOT}'),
    ('times', u'\N{MULTIPLICATION SIGN}'),
    ('otimes', u'\N{CIRCLED TIMES}'),
    ('oplus', u'\N{CIRCLED PLUS}'),
    ('bigotimes', u'\N{CIRCLED TIMES}'),
    ('bigoplus', u'\N{CIRCLED PLUS}'),

    ('frac', '%s/%s'),
    ('nicefrac', '%s/%s'),

    ('cos', 'cos'),
    ('sin', 'sin'),
    ('tan', 'tan'),
    ('arccos', 'arccos'),
    ('arcsin', 'arcsin'),
    ('arctan', 'arctan'),

    ('prime', "'"),
    ('dag', u"\N{DAGGER}"),
    ('dagger', u"\N{DAGGER}"),
    ('pm', u"\N{PLUS-MINUS SIGN}"),
    ('mp', u"\N{MINUS-OR-PLUS SIGN}"),

    (',', u" "),
    (';', u" "),
    (':', u" "),
    (' ', u" "),
    ('!', u""), # sorry, no negative space in ascii
    ('quad', u"  "),
    ('qquad', u"    "),

    ('ldots', u"..."),
    ('cdots', u"..."),
    ('ddots', u"..."),
    ('dots', u"..."),
    
    ('langle', u'\N{LEFT ANGLE BRACKET}'),
    ('rangle', u'\N{RIGHT ANGLE BRACKET}'),
    ('mid', u'|'),
    ('nmid', u'\N{DOES NOT DIVIDE}'),
    
    ('ket', u'|%s\N{RIGHT ANGLE BRACKET}'),
    ('bra', u'\N{LEFT ANGLE BRACKET}%s|'),
    ('braket', u'\N{LEFT ANGLE BRACKET}%s|%s\N{RIGHT ANGLE BRACKET}'),
    ('ketbra', u'|%s\N{RIGHT ANGLE BRACKET}\N{LEFT ANGLE BRACKET}%s|'),
    ('uparrow', u'\N{UPWARDS ARROW}'),
    ('downarrow', u'\N{DOWNWARDS ARROW}'),
    ('rightarrow', u'\N{RIGHTWARDS ARROW}'),
    ('to', u'\N{RIGHTWARDS ARROW}'),
    ('leftarrow', u'\N{LEFTWARDS ARROW}'),
    ('longrightarrow', u'\N{LONG RIGHTWARDS ARROW}'),
    ('longleftarrow', u'\N{LONG LEFTWARDS ARROW}'),

    # we use these conventions as Identity operator (\mathbbm{1})
    ('id', u'\N{MATHEMATICAL DOUBLE-STRUCK CAPITAL I}'),
    ('Ident', u'\N{MATHEMATICAL DOUBLE-STRUCK CAPITAL I}'),
    ];



def _format_uebung(n):
    s = '\n%s\n' %(latexnodes2text([n.nodeargs[0]]));
    optarg = n.nodeargs[1];
    if (optarg is not None):
        s += '[%s]\n' %(latexnodes2text([optarg]));
    return s


macro_list += [
    # some ethuebung.sty macros
    ('exercise', _format_uebung),
    ('uebung', _format_uebung),
    ('hint', 'Hint: %s'),
    ('hints', 'Hints: %s'),
    ('hinweis', 'Hinweis: %s'),
    ('hinweise', 'Hinweise: %s'),
    ];





def greekletters(letterlist):
    for l in letterlist:
        ucharname = l.upper()
        if (ucharname == 'LAMBDA'):
            ucharname = 'LAMDA'
        smallname = "GREEK SMALL LETTER "+ucharname;
        if (ucharname == 'EPSILON'):
            smallname = "GREEK LUNATE EPSILON SYMBOL"
        if (ucharname == 'PHI'):
            smallname = "GREEK PHI SYMBOL"
        macro_list.append(
            (l, unicodedata.lookup(smallname))
            );
        macro_list.append(
            (l[0].upper()+l[1:], unicodedata.lookup("GREEK CAPITAL LETTER "+ucharname))
            );
greekletters( ('alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta', 'iota', 'kappa',
               'lambda', 'mu', 'nu', 'xi', 'omicron', 'pi', 'rho', 'sigma', 'tau', 'upsilon', 'phi',
               'chi', 'psi', 'omega') )
macro_list += [
    ('varepsilon', u'\N{GREEK SMALL LETTER EPSILON}'),
    ('vartheta', u'\N{GREEK THETA SYMBOL}'),
    ('varpi', u'\N{GREEK PI SYMBOL}'),
    ('varrho', u'\N{GREEK RHO SYMBOL}'),
    ('varsigma', u'\N{GREEK SMALL LETTER FINAL SIGMA}'),
    ('varphi', u'\N{GREEK SMALL LETTER PHI}'),
    ]

unicode_accents_list = (
    # see http://en.wikibooks.org/wiki/LaTeX/Special_Characters for a list
    ("'", u"\N{COMBINING ACUTE ACCENT}"),
    ("`", u"\N{COMBINING GRAVE ACCENT}"),
    ('"', u"\N{COMBINING DIAERESIS}"),
    ("c", u"\N{COMBINING CEDILLA}"),
    ("^", u"\N{COMBINING CIRCUMFLEX ACCENT}"),
    ("~", u"\N{COMBINING TILDE}"),
    ("H", u"\N{COMBINING DOUBLE ACUTE ACCENT}"),
    ("k", u"\N{COMBINING OGONEK}"),
    ("=", u"\N{COMBINING MACRON}"),
    ("b", u"\N{COMBINING MACRON BELOW}"),
    (".", u"\N{COMBINING DOT ABOVE}"),
    ("d", u"\N{COMBINING DOT BELOW}"),
    ("r", u"\N{COMBINING RING ABOVE}"),
    ("u", u"\N{COMBINING BREVE}"),
    ("v", u"\N{COMBINING CARON}"),

    ("vec", u"\N{COMBINING RIGHT ARROW ABOVE}"),
    ("dot", u"\N{COMBINING DOT ABOVE}"),
    ("hat", u"\N{COMBINING CIRCUMFLEX ACCENT}"),
    ("check", u"\N{COMBINING CARON}"),
    ("breve", u"\N{COMBINING BREVE}"),
    ("acute", u"\N{COMBINING ACUTE ACCENT}"),
    ("grave", u"\N{COMBINING GRAVE ACCENT}"),
    ("tilde", u"\N{COMBINING TILDE}"),
    ("bar", u"\N{COMBINING OVERLINE}"),
    ("ddot", u"\N{COMBINING DIAERESIS}"),

    ("not", u"\N{COMBINING LONG SOLIDUS OVERLAY}"),

    );

def make_accented_char(node, combining):
    nodearg = node.nodeargs[0] if len(node.nodeargs) else latexwalker.LatexCharsNode(chars=' ')

    c = latexnodes2text([nodearg]).strip();

    def getaccented(ch, combining):
        ch = unicode(ch)
        combining = unicode(combining)
        if (ch == u"\N{LATIN SMALL LETTER DOTLESS I}"):
            ch = u"i"
        if (ch == u"\N{LATIN SMALL LETTER DOTLESS I}"):
            ch = u"j"
        #print u"Accenting %s with %s"%(ch, combining) # this causes UnicdeDecodeError!!!
        return unicodedata.normalize('NFC', unicode(ch)+combining)

    return u"".join([getaccented(ch, combining) for ch in c]);


for u in unicode_accents_list:
    (mname, mcombining) = u;
    macro_list.append(
        (mname, lambda x, c=mcombining: make_accented_char(x, c))
        );






text_replacements = (
    # remove indentation provided by LaTeX
    #(re.compile(r'\n[ \t]*'), '\n'),
    
    ("~", " "),
    ("``", '"'),
    ("''", '"'),

    (r'(?<!\\)&', '   '), # ignore tabular alignments, just add a little space
    ('\\&', '&'), # but preserve the \& escapes, that we before *hackingly* kept as '\&' for this purpose ...

    );









env_dict = dict([(e.envname, e) for e in env_list])
macro_dict = dict([(m.macname, m) for m in (MacroDef(m) for m in macro_list)])





def latex2text(content, tolerant_parsing=False, keep_inline_math=False, keep_comments=False):
    """
    Extracts text from `content` meant for database indexing. `content` is
    some LaTeX code.
    """

    (nodelist, tpos, tlen) = latexwalker.get_latex_nodes(content, keep_inline_math=keep_inline_math,
                                                         tolerant_parsing=tolerant_parsing);

    return latexnodes2text(nodelist, keep_inline_math=keep_inline_math, keep_comments=keep_comments);


def latexnodes2text(nodelist, keep_inline_math=False, keep_comments=False):
    """
    Extracts text from a node list. `nodelist` is a list of nodes as returned by
    `latexwalker.get_latex_nodes()`.
    """
    

    def text_from_node(node):
        if (node is None):
            return ""
        
        if (node.isNodeType(latexwalker.LatexCharsNode)):
            return node.chars
        if (node.isNodeType(latexwalker.LatexCommentNode)):
            if (keep_comments):
                return '%'+node.comment
            return ""
        if (node.isNodeType(latexwalker.LatexGroupNode)):
            return "".join([text_from_node(n) for n in node.nodelist]);
        if (node.isNodeType(latexwalker.LatexMacroNode)):
            # get macro behavior definition.
            macroname = node.macroname.rstrip('*');
            if (macroname in macro_dict):
                mac = macro_dict[macroname]
            else:
                # no predefined behavior, use default:
                mac = macro_dict['']
            if mac.simplify_repl:
                if (callable(mac.simplify_repl)):
                    return mac.simplify_repl(node)
                if ('%' in mac.simplify_repl):
                    try:
                        return mac.simplify_repl % tuple([text_from_node(nn) for nn in node.nodeargs])
                    except (TypeError, ValueError):
                        log.warning("WARNING: Error in configuration: macro '%s' failed its substitution!"
                                    %(macroname));
                        return mac.simplify_repl; # too bad, keep the percent signs as they are...
                return mac.simplify_repl
            if mac.discard:
                return ""
            a = node.nodeargs;
            if (node.nodeoptarg):
                a.prepend(node.nodeoptarg)
            return "".join([text_from_node(n) for n in a])

        if (node.isNodeType(latexwalker.LatexEnvironmentNode)):
            # get environment behavior definition.
            envname = node.envname.rstrip('*');
            if (envname in env_dict):
                envdef = env_dict[envname]
            else:
                # no predefined behavior, use default:
                envdef = env_dict['']
            if envdef.simplify_repl:
                if (callable(envdef.simplify_repl)):
                    return envdef.simplify_repl(node)
                if ('%' in envdef.simplify_repl):
                    return envdef.simplify_repl % ("".join([text_from_node(nn) for nn in node.nodelist]))
                return envdef.simplify_repl
            if envdef.discard:
                return ""
            return "".join([text_from_node(n) for n in node.nodelist])

        if (node.isNodeType(latexwalker.LatexMathNode)):
            # if we have a math node, this means we care about math modes and we should keep this verbatim.
            return latexwalker.math_node_to_latex(node);

        print "extract_from_latex(): IGNORING NODE: "+repr(node)

        # discard anything else.
        return ""
    

    s = "".join([text_from_node(n) for n in nodelist]);

    # now, perform suitable replacements
    for pattern, replacement in text_replacements:
        if (hasattr(pattern, 'sub')):
            s = pattern.sub(replacement, s)
        else:
            s = s.replace(pattern, replacement)


    #  ###TODO: more clever handling of math modes??

    if (not keep_inline_math):
        s = s.replace('$', ''); # removing math mode inline signs, just keep their Unicode counterparts..

    return s







if __name__ == '__main__':

    try:

        #latex = '\\textit{hi there!} This is {\em an equation}: \\begin{equation}\n a + bi = 0\n\\end{equation}\n\nwhere $i$ is the imaginary unit.\n';

        import fileinput

        print "Please type some latex text (Ctrl+D twice to stop) ..."

        latex = ''
        for line in fileinput.input():
            latex += line;


        print '\n--- WORDS ---\n'
        print latex2text(latex.decode('utf-8')#, keep_inline_math=True
                         ).encode('utf-8')
        print '\n-------------\n'

    except:
        import pdb;
        import traceback;
        import sys;
        (exc_type, exc_value, exc_traceback) = sys.exc_info()
        
        print "\nEXCEPTION: " + unicode(sys.exc_value) + "\n"
        
        pdb.post_mortem()


