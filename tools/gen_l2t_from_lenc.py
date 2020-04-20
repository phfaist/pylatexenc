#
# Inspect latexencode rules to see if there are symbols that we can use for
# latex2text, too
#

# Py3 only script
import sys
assert sys.version_info > (3,0)

import unicodedata

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


from pylatexenc import latexwalker, latex2text, latexencode #, macrospec

l2t_default_context = latex2text.get_default_latex_context_db()

def extract_symbol_node(nodelist, uni, latex):

    if len(nodelist) != 1:
        # more than one "thing"
        logger.warning("Got nodelist with more than one node, skipping (%s): %s = %r",
                       chr(uni), latex, nodelist)
        return

    thenode = nodelist[0]

    if not thenode.isNodeType(latexwalker.LatexMacroNode):
        logger.warning("Got node that is not a macro, skipping (%s): %s = %r",
                       chr(uni), latex, thenode)
        return
        
    if thenode.macroname == 'ensuremath':
        # ignore, parse contents instead
        if thenode.nodeargd is None or not thenode.nodeargd.argnlist or \
           len(thenode.nodeargd.argnlist) != 1:
            logger.warning(r"\ensuremath with no arguments or wrong # of arguments (%s): %s = %r",
                           chr(uni), latex, nodelist)
            return

        argnode = thenode.nodeargd.argnlist[0]
        if argnode.isNodeType(latexwalker.LatexGroupNode):
            argnodelist = argnode.nodelist
        else:
            argnodelist = [ argnode ]

        return extract_symbol_node(argnodelist, uni, latex)

    l2t_mspec = l2t_default_context.get_macro_spec(thenode.macroname)
    if l2t_mspec is not None and l2t_mspec.macroname:
        # macro found, already known
        logger.debug("Macro found (%s): %r", chr(uni), thenode)
        return

    if thenode.nodeargd and thenode.nodeargd.argnlist:
        logger.warning(r"Macro %r for ‘%s’ is not known to latex2text but it has arguments",
                       thenode, chr(uni))
        return

    # got a symbol macro, go for it:
    print("    MacroTextSpec(%r, u'\\N{%s}'), # ‘%s’" % (
        thenode.macroname, unicodedata.name(chr(uni)), chr(uni)
    ))


for builtin_name in ('defaults', 'unicode-xml'):

    rules = latexencode.get_builtin_conversion_rules(builtin_name)

    logger.info("Reader latexencode defaults %r", builtin_name)
    print("    # Rules from latexencode defaults '%s'"%(builtin_name))

    for rule in rules:

        if rule.rule_type != latexencode.RULE_DICT:
            logger.warning("Ignoring non-dict rule type %d", rule.rule_type)
            continue

        # inspect rules for symbols that latex2text might not already be aware of
        for uni, latex in rule.rule.items():
            try:
                nodelist, _, _ = latexwalker.LatexWalker(latex, tolerant_parsing=False).get_latex_nodes()
            except latexwalker.LatexWalkerError as e:
                logger.warning("Error parsing %r (%s): %s", latex, chr(uni), e)
                continue

            extract_symbol_node(nodelist, uni, latex)
