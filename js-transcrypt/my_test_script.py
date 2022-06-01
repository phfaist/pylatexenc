# some custom JS patches are necessary ... comment out these lines to run with python
#import customjspatches
#customjspatches.custom_apply_patches()


#import pylatexenc.latexnodes as latexnodes
import pylatexenc.latexnodes.parsers as parsers
from pylatexenc.macrospec import LatexContextDb, MacroSpec, EnvironmentSpec, SpecialsSpec
from pylatexenc.latexwalker import LatexWalker


# # --- minitest ---
# from pylatexenc.latexnodes import ParsingState
# ps = ParsingState(s='', enable_comments=False)
# from unique_object_id import fn_unique_object_id
# print("Parsing state's id is = ", fn_unique_object_id(ps), "and its repr is = ", repr(ps))
# raise StopHereThatllBeAllThanks
# # ---


latextext = r"""
Here is some text that can contain some simple LaTeX macros, to produce
for instance~\textbf{bold text} and \emph{italic text}.

Two line breaks start a new paragraph. You can use inline math like
\(\alpha=\sum_j\beta_j\) and display equations like
\begin{align}
    S_1 &= I\,X\,Z\,Z\,X\ ;  \nonumber\\
    S_2, \ldots, S_4 &= \text{cyclical permutations of \(S_1\)}\ .
    \label{eq:stabilizers}
\end{align}

Refer to equations with~\eqref{eq:stabilizers}, etc. ...

Can we also parse citation commands like~\cite{Key1,Key2}.
"""

lw_context = LatexContextDb()
lw_context.add_context_category(
    'my-base-latex-category',
    macros=[
        MacroSpec('textbf', '{',),
        MacroSpec('textit', '{',),
        MacroSpec('emph', '{',),
        MacroSpec('cite', '{',),
        MacroSpec('text', '{',),
        MacroSpec('label', '{',),
        MacroSpec('eqref', '{',),
    ],
    specials=[
        SpecialsSpec('~'),
        # new paragraph
        SpecialsSpec('\n\n'),
    ],
    environments=[
        EnvironmentSpec('align')
    ]
)

# for \alpha, \, etc.
lw_context.set_unknown_macro_spec( MacroSpec('','') )



lw = LatexWalker(
    latextext,
    latex_context=lw_context,
    tolerant_parsing=False
)

nodes, carryover_info = lw.parse_content( parsers.LatexGeneralNodesParser() )

print("Got node list ->")
print(nodes)
