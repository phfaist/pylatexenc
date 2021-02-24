import unittest

from pylatexenc.latexwalker import LatexWalker
from pylatexenc.latex2text import LatexNodes2Text


upgreek_letters = (
    (r"\upmu", "μ"),
    (r"\upalpha", "α"),
    (r"\upbeta", "β"),
    (r"\upgamma", "γ"),
    (r"\updelta", "δ"),
    (r"\upepsilon", "ϵ"),     # not sure...
    (r"\upvarepsilon", "ε"),  #
    (r"\upzeta", "ζ"),
    (r"\upeta", "η"),
    (r"\uptheta", "θ"),     # not sure...
    (r"\upvartheta", "ϑ"),  #
    (r"\upiota", "ι"),
    (r"\upkappa", "κ"),
    (r"\uplambda", "λ"),
    (r"\upmu", "μ"),
    (r"\upnu", "ν"),
    (r"\upxi", "ξ"),
    (r"\uppi", "π"),
    (r"\upvarpi", "ϖ"),
    (r"\uprho", "ρ"),     # not sure...
    (r"\upvarrho", "ϱ"),  #
    (r"\upsigma", "σ"),     # not sure...
    (r"\upvarsigma", "ς"),  #
    (r"\uptau", "τ"),
    (r"\upupsilon", "υ"),
    (r"\upphi", "ϕ"),     # not sure...
    (r"\upvarphi", "φ"),  # NB: 'ϕ' != 'φ'
    (r"\upchi", "χ"),
    (r"\uppsi", "ψ"),
    (r"\upomega", "ω"),
    #
    (r"\Upgamma", "Γ"),
    (r"\Updelta", "Δ"),
    (r"\Uptheta", "Θ"),
    (r"\Uplambda", "Λ"),
    (r"\Upxi", "Ξ"),
    (r"\Uppi", "Π"),
    (r"\Upsigma", "Σ"),
    (r"\Upupsilon", "Υ"),
    (r"\Upphi", "Φ"),
    (r"\Uppsi", "Ψ"),
    (r"\Upomega", "Ω"),
)


class TestLatexNodes2TextUpgreek(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        # super(TestLatexNodes2Text, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)
        # self.maxDiff = None

    def test_upgreek(self):
        for source, expected_dest in upgreek_letters:
            with self.subTest():
                self.assertEqual(
                    LatexNodes2Text().nodelist_to_text(
                        LatexWalker(source).get_latex_nodes()[0]),
                    expected_dest
                )
