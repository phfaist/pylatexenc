// some custom JS patches are necessary ... comment out these lines to run with python
import * as latexnodes from 'pylatexenc-js/pylatexenc.latexnodes.js';
import * as macrospec from 'pylatexenc-js/pylatexenc.macrospec.js';
import * as latexwalker from 'pylatexenc-js/pylatexenc.latexwalker.js';
import * as parsers from 'pylatexenc-js/pylatexenc.latexnodes.parsers.js';

// some setup code

import * as customjspatches from 'pylatexenc-js/customjspatches.js';
customjspatches.custom_apply_patches();

import {__kwargtrans__, repr} from 'pylatexenc-js/org.transcrypt.__runtime__.js';
const $$kw = __kwargtrans__;



const {LatexContextDb, MacroSpec, EnvironmentSpec, SpecialsSpec} = macrospec;
const {LatexWalker} = latexwalker;


const latextext = `
Here is some text that can contain some simple LaTeX macros, to produce
for instance~\\textbf{bold text} and \\emph{italic text}.

Two line breaks start a new paragraph. You can use inline math like
\\(\\alpha=\\sum_j\\beta_j\\) and display equations like
\\begin{align}
    S_1 &= I\\,X\\,Z\\,Z\\,X\\ ;  \\nonumber\\\\
    S_2, \\ldots, S_4 &= \\text{cyclical permutations of \\(S_1\\)}\\ .
    \\label{eq:stabilizers}
\\end{align}

Refer to equations with~\\eqref{eq:stabilizers}, etc. ...

Can we also parse citation commands like~\\cite{Key1,Key2}.
`;

console.log('latextext = ', latextext);


const lw_context = new LatexContextDb()
lw_context.add_context_category(
    'my-base-latex-category',
    $$kw({
        macros: [
            new MacroSpec('textbf', '{',),
            new MacroSpec('textit', '{',),
            new MacroSpec('emph', '{',),
            new MacroSpec('cite', '{',),
            new MacroSpec('text', '{',),
            new MacroSpec('label', '{',),
            new MacroSpec('eqref', '{',),
        ],
        environments: [
            new EnvironmentSpec('align')
        ],
        specials: [
            new SpecialsSpec('~'),
            // new paragraph
            new SpecialsSpec('\n\n'),
        ],
    })
)

// for \alpha, \, etc.
lw_context.set_unknown_macro_spec( new MacroSpec('','') )

const lw = new LatexWalker(
    latextext,
    $$kw({
        latex_context: lw_context,
        tolerant_parsing: false
    })
)

const [nodes, carryover_info] = lw.parse_content( new parsers.LatexGeneralNodesParser() )

console.log("Got node list ->")
console.log(repr(nodes))
console.log(nodes)

