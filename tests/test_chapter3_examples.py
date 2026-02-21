"""Tests derived from worked examples in Hlobil & Brandom 2025, Ch. 3.

These tests verify that the pyNMMS implementation produces correct results
for every concrete example given in Chapter 3 ("Introducing Logical Vocabulary").
Each test class references the specific page/section where the example appears.
"""

import pytest

from pynmms import MaterialBase, NMMSReasoner

# ============================================================
# Fixture: Toy Base T (p. 118 of Ch. 3)
# ============================================================
#
# L_T = {p, q, r, s, t, u, v, w, x}
# |~_T = { <{p},{q}>, <{s,t},{}>, <{p,q},{v}>, <{s},{w}>, <{s,w},{x}> }
#         + Containment (handled automatically by is_axiom)
#
# Encodes the following material inferences:
#   (1) p |~ q           — Tara is human → body temp is 37°C
#   (3) s, t |~          — triangle + angle-sum > 2 right angles → incoherence
#   (6) p, q |~ v        — human + temp 37°C → healthy
#   (8) s |~ w           — triangle → angle-sum = 2 right angles
#   (9) s, w |~ x        — triangle + angle-sum = 2 right → Euclidean plane triangle


@pytest.fixture
def toy_base_T():
    """Toy base T from Ch. 3, p. 118."""
    return MaterialBase(
        language={"p", "q", "r", "s", "t", "u", "v", "w", "x"},
        consequences={
            (frozenset({"p"}), frozenset({"q"})),       # (1)
            (frozenset({"s", "t"}), frozenset()),        # (3) incompatibility
            (frozenset({"p", "q"}), frozenset({"v"})),   # (6)
            (frozenset({"s"}), frozenset({"w"})),        # (8)
            (frozenset({"s", "w"}), frozenset({"x"})),   # (9)
        },
    )


@pytest.fixture
def toy_reasoner_T(toy_base_T):
    """Reasoner for toy base T with generous depth."""
    return NMMSReasoner(toy_base_T, max_depth=25)


# ============================================================
# 1. Base consequences of T — derivable (pp. 117-118)
# ============================================================

class TestToyBaseConsequences:
    """Verify that all explicit base consequences of T are derivable."""

    def test_1_p_derives_q(self, toy_reasoner_T):
        """(1) p |~ q — base consequence."""
        assert toy_reasoner_T.query(frozenset({"p"}), frozenset({"q"}))

    def test_3_s_t_incompatible(self, toy_reasoner_T):
        """(3) s, t |~ ∅ — incompatibility (empty succedent)."""
        assert toy_reasoner_T.query(frozenset({"s", "t"}), frozenset())

    def test_6_p_q_derives_v(self, toy_reasoner_T):
        """(6) p, q |~ v — base consequence."""
        assert toy_reasoner_T.query(
            frozenset({"p", "q"}), frozenset({"v"})
        )

    def test_8_s_derives_w(self, toy_reasoner_T):
        """(8) s |~ w — base consequence."""
        assert toy_reasoner_T.query(frozenset({"s"}), frozenset({"w"}))

    def test_9_s_w_derives_x(self, toy_reasoner_T):
        """(9) s, w |~ x — base consequence."""
        assert toy_reasoner_T.query(
            frozenset({"s", "w"}), frozenset({"x"})
        )


# ============================================================
# 2. Monotonicity failures in T (p. 119)
# ============================================================

class TestMonotonicityFailuresInT:
    """MO-failure-1 and MO-failure-2 from Ch. 3, p. 119."""

    def test_mo_failure_1(self, toy_reasoner_T):
        """MO-failure-1: p |~ q  BUT  p, r ̸|~ q.

        Adding premise r defeats the inference.
        """
        assert toy_reasoner_T.query(frozenset({"p"}), frozenset({"q"}))
        assert not toy_reasoner_T.query(
            frozenset({"p", "r"}), frozenset({"q"})
        )

    def test_mo_failure_2(self, toy_reasoner_T):
        """MO-failure-2: s, t |~  BUT  s, t, u ̸|~ .

        Adding premise u cures the incompatibility.
        """
        assert toy_reasoner_T.query(frozenset({"s", "t"}), frozenset())
        assert not toy_reasoner_T.query(
            frozenset({"s", "t", "u"}), frozenset()
        )


# ============================================================
# 3. Transitivity (Mixed-Cut) failures in T (p. 119)
# ============================================================

class TestTransitivityFailuresInT:
    """CT-failure-1 and CT-failure-2 from Ch. 3, p. 119."""

    def test_ct_failure_1(self, toy_reasoner_T):
        """CT-failure-1: p |~ q AND p, q |~ v BUT p ̸|~ v.

        Chaining (1) and (6) via Mixed-Cut would give p |~ v,
        but this is not derivable.
        """
        assert toy_reasoner_T.query(frozenset({"p"}), frozenset({"q"}))
        assert toy_reasoner_T.query(
            frozenset({"p", "q"}), frozenset({"v"})
        )
        assert not toy_reasoner_T.query(frozenset({"p"}), frozenset({"v"}))

    def test_ct_failure_2(self, toy_reasoner_T):
        """CT-failure-2: s |~ w AND s, w |~ x BUT s ̸|~ x.

        Chaining (8) and (9) via Mixed-Cut would give s |~ x,
        but this is not derivable.
        """
        assert toy_reasoner_T.query(frozenset({"s"}), frozenset({"w"}))
        assert toy_reasoner_T.query(
            frozenset({"s", "w"}), frozenset({"x"})
        )
        assert not toy_reasoner_T.query(frozenset({"s"}), frozenset({"x"}))


# ============================================================
# 4. Explicitating theorems of T (pp. 118-119)
# ============================================================

class TestExplicitatingTheorems:
    """Theorems that make base consequences explicit via logical vocabulary.

    These are all theorems (derivable from empty antecedent) of the
    logically extended consequence relation. They correspond to the
    labeled examples (1e), (3e), (6e), (8e), (9e) on p. 118.
    """

    def test_1e_p_implies_q(self, toy_reasoner_T):
        """(1e) |~ p → q — makes explicit that p implies q."""
        assert toy_reasoner_T.query(frozenset(), frozenset({"p -> q"}))

    def test_3e_s_t_incompatible(self, toy_reasoner_T):
        """(3e) |~ ¬(s ∧ t) — makes explicit that s and t are incompatible."""
        assert toy_reasoner_T.query(frozenset(), frozenset({"~(s & t)"}))

    def test_6e_p_q_implies_v(self, toy_reasoner_T):
        """(6e) |~ (p ∧ q) → v — makes explicit that p together with q implies v."""
        assert toy_reasoner_T.query(
            frozenset(), frozenset({"(p & q) -> v"})
        )

    def test_8e_s_implies_w(self, toy_reasoner_T):
        """(8e) |~ s → w — makes explicit that s implies w."""
        assert toy_reasoner_T.query(frozenset(), frozenset({"s -> w"}))

    def test_9e_s_w_implies_x(self, toy_reasoner_T):
        """(9e) |~ (s ∧ w) → x — makes explicit that s with w implies x."""
        assert toy_reasoner_T.query(
            frozenset(), frozenset({"(s & w) -> x"})
        )


# ============================================================
# 5. Worked proof tree: ((p∧r)∨s) → q (pp. 113-114)
# ============================================================

class TestWorkedProofTree:
    """Worked proof tree from pp. 113-114 of Ch. 3.

    Base axioms: p, r |~ q  AND  s |~ q  AND  p, r, s |~ q
    The proof tree derives: ⊢ ((p ∧ r) ∨ s) → q

    The derivation proceeds:
      [L∧]: p, r ⊢ q  from  p ∧ r ⊢ q? No—[L∧] says p∧r, Γ ⊢ Δ <- p, r, Γ ⊢ Δ
      [L∨]: (p∧r)∨s ⊢ q  from  p∧r ⊢ q AND s ⊢ q AND p∧r, s ⊢ q
      [R→]: ⊢ ((p∧r)∨s) → q  from  (p∧r)∨s ⊢ q
    """

    @pytest.fixture
    def proof_tree_base(self):
        return MaterialBase(
            language={"p", "q", "r", "s"},
            consequences={
                (frozenset({"p", "r"}), frozenset({"q"})),
                (frozenset({"s"}), frozenset({"q"})),
                (frozenset({"p", "r", "s"}), frozenset({"q"})),
            },
        )

    @pytest.fixture
    def proof_tree_reasoner(self, proof_tree_base):
        return NMMSReasoner(proof_tree_base, max_depth=25)

    def test_base_axiom_p_r_q(self, proof_tree_reasoner):
        """Axiom: p, r ⊢ q."""
        assert proof_tree_reasoner.query(
            frozenset({"p", "r"}), frozenset({"q"})
        )

    def test_base_axiom_s_q(self, proof_tree_reasoner):
        """Axiom: s ⊢ q."""
        assert proof_tree_reasoner.query(
            frozenset({"s"}), frozenset({"q"})
        )

    def test_base_axiom_p_r_s_q(self, proof_tree_reasoner):
        """Axiom: p, r, s ⊢ q."""
        assert proof_tree_reasoner.query(
            frozenset({"p", "r", "s"}), frozenset({"q"})
        )

    def test_intermediate_conj_p_and_r_derives_q(self, proof_tree_reasoner):
        """Intermediate step: p ∧ r ⊢ q (via [L∧])."""
        assert proof_tree_reasoner.query(
            frozenset({"p & r"}), frozenset({"q"})
        )

    def test_intermediate_disj_derives_q(self, proof_tree_reasoner):
        """Intermediate step: (p ∧ r) ∨ s ⊢ q (via [L∨])."""
        assert proof_tree_reasoner.query(
            frozenset({"(p & r) | s"}), frozenset({"q"})
        )

    def test_final_theorem(self, proof_tree_reasoner):
        """Final result: ⊢ ((p ∧ r) ∨ s) → q (via [R→])."""
        assert proof_tree_reasoner.query(
            frozenset(), frozenset({"((p & r) | s) -> q"})
        )


# ============================================================
# 6. Complex reflexivity: p ∧ q ⊢ p ∧ q (p. 112)
# ============================================================

class TestComplexReflexivity:
    """Complex reflexivity via Containment + rules (p. 112).

    Deriving p ∧ q ⊢ p ∧ q from:
      - p, q ⊢ p (Containment)
      - p, q ⊢ q (Containment)
      - p, q ⊢ p, q (Containment)
    using [L∧] and [R∧].

    This works for any base obeying Containment (no explicit consequences needed).
    """

    def test_conj_reflexivity(self):
        """p ∧ q ⊢ p ∧ q — reflexivity for a conjunction."""
        base = MaterialBase(language={"p", "q"})
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(frozenset({"p & q"}), frozenset({"p & q"}))

    def test_disj_reflexivity(self):
        """p ∨ q ⊢ p ∨ q — reflexivity for a disjunction."""
        base = MaterialBase(language={"p", "q"})
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(frozenset({"p | q"}), frozenset({"p | q"}))

    def test_impl_reflexivity(self):
        """(p → q) ⊢ (p → q) — reflexivity for a conditional."""
        base = MaterialBase(language={"p", "q"})
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(frozenset({"p -> q"}), frozenset({"p -> q"}))

    def test_neg_reflexivity(self):
        """¬p ⊢ ¬p — reflexivity for a negation."""
        base = MaterialBase(language={"p"})
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(frozenset({"~p"}), frozenset({"~p"}))

    def test_nested_reflexivity(self):
        """(p ∧ q) → r ⊢ (p ∧ q) → r — reflexivity for nested formula."""
        base = MaterialBase(language={"p", "q", "r"})
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(
            frozenset({"(p & q) -> r"}), frozenset({"(p & q) -> r"})
        )


# ============================================================
# 7. Distribution failure (pp. 119-120)
# ============================================================

class TestDistributionFailure:
    """Substitution of classically equivalent sentences can fail.

    Base: ⊢_B p, ⊢_B q, r, ⊢_B p, q, r but NOT ⊢_B p, r

    Then:
      - ⊢ p ∧ (q ∨ r) is derivable
      - p ∧ (q ∨ r) ⊢ (p ∧ q) ∨ (p ∧ r) is derivable (classically valid)
      - ⊢ (p ∧ (q ∨ r)) → ((p ∧ q) ∨ (p ∧ r)) is derivable
      - BUT ⊢ (p ∧ q) ∨ (p ∧ r) is NOT derivable

    This shows that meta-modus-ponens fails and that substituting classically
    equivalent sentences can turn a good implication into a bad one.
    """

    @pytest.fixture
    def distrib_base(self):
        """Base with ⊢ p, ⊢ q,r, ⊢ p,q,r but NOT ⊢ p,r."""
        return MaterialBase(
            language={"p", "q", "r"},
            consequences={
                (frozenset(), frozenset({"p"})),          # ⊢ p
                (frozenset(), frozenset({"q", "r"})),     # ⊢ q, r
                (frozenset(), frozenset({"p", "q", "r"})),  # ⊢ p, q, r
            },
        )

    @pytest.fixture
    def distrib_reasoner(self, distrib_base):
        return NMMSReasoner(distrib_base, max_depth=25)

    def test_base_axiom_p(self, distrib_reasoner):
        """⊢ p is a base consequence."""
        assert distrib_reasoner.query(frozenset(), frozenset({"p"}))

    def test_base_axiom_q_r(self, distrib_reasoner):
        """⊢ q, r is a base consequence."""
        assert distrib_reasoner.query(frozenset(), frozenset({"q", "r"}))

    def test_base_axiom_p_q_r(self, distrib_reasoner):
        """⊢ p, q, r is a base consequence."""
        assert distrib_reasoner.query(
            frozenset(), frozenset({"p", "q", "r"})
        )

    def test_not_base_p_r(self, distrib_reasoner):
        """⊢ p, r is NOT a base consequence (and not derivable)."""
        assert not distrib_reasoner.query(frozenset(), frozenset({"p", "r"}))

    def test_derives_p_and_q_or_r(self, distrib_reasoner):
        """⊢ p ∧ (q ∨ r) is derivable.

        Proof tree (from Ch. 3 p. 120):
          ⊢ p   ⊢ q, r   ⊢ p, q, r
          --------[R∨]--- ---------[R∨]---
          ⊢ p   ⊢ q ∨ r   ⊢ p, q ∨ r
          ---------[R∧]----------------
          ⊢ p ∧ (q ∨ r)
        """
        assert distrib_reasoner.query(
            frozenset(), frozenset({"p & (q | r)"})
        )

    def test_classically_valid_distribution(self, distrib_reasoner):
        """p ∧ (q ∨ r) ⊢ (p ∧ q) ∨ (p ∧ r) — classically valid."""
        assert distrib_reasoner.query(
            frozenset({"p & (q | r)"}),
            frozenset({"(p & q) | (p & r)"}),
        )

    def test_conditional_distribution(self, distrib_reasoner):
        """⊢ (p ∧ (q ∨ r)) → ((p ∧ q) ∨ (p ∧ r)) — classically valid theorem."""
        assert distrib_reasoner.query(
            frozenset(),
            frozenset({"(p & (q | r)) -> ((p & q) | (p & r))"}),
        )

    def test_not_derives_distributed_form(self, distrib_reasoner):
        """⊢ (p ∧ q) ∨ (p ∧ r) is NOT derivable.

        Even though p ∧ (q ∨ r) and (p ∧ q) ∨ (p ∧ r) are classically
        equivalent, and ⊢ p ∧ (q ∨ r) holds, ⊢ (p ∧ q) ∨ (p ∧ r) fails.

        This is because deriving it requires ⊢ p, r which is not
        in the base.
        """
        assert not distrib_reasoner.query(
            frozenset(), frozenset({"(p & q) | (p & r)"})
        )


# ============================================================
# 8. Meta-modus-ponens failure (p. 119)
# ============================================================

class TestMetaModusPonensFailure:
    """Meta-modus-ponens: if ⊢ φ and ⊢ φ → ψ, then ⊢ ψ. Can fail.

    From CT-failure-1 in T: p |~ q and p, q |~ v but p ̸|~ v.
    By DD: |~ p → q and p |~ q → v.
    By replacing premises with empty set: we can construct the analogous
    pattern from the distribution example.
    """

    def test_meta_mp_fails_via_distribution(self):
        """⊢ p ∧ (q ∨ r) and p ∧ (q ∨ r) ⊢ (p ∧ q) ∨ (p ∧ r)
        but NOT ⊢ (p ∧ q) ∨ (p ∧ r).

        This is the concrete example from Ch. 3 p. 120.
        """
        base = MaterialBase(
            language={"p", "q", "r"},
            consequences={
                (frozenset(), frozenset({"p"})),
                (frozenset(), frozenset({"q", "r"})),
                (frozenset(), frozenset({"p", "q", "r"})),
            },
        )
        r = NMMSReasoner(base, max_depth=25)

        # Premise 1: ⊢ p ∧ (q ∨ r)
        assert r.query(frozenset(), frozenset({"p & (q | r)"}))
        # Premise 2 (classically valid): p ∧ (q ∨ r) ⊢ (p ∧ q) ∨ (p ∧ r)
        assert r.query(
            frozenset({"p & (q | r)"}),
            frozenset({"(p & q) | (p & r)"}),
        )
        # But meta-MP fails: NOT ⊢ (p ∧ q) ∨ (p ∧ r)
        assert not r.query(frozenset(), frozenset({"(p & q) | (p & r)"}))

    def test_meta_mp_fails_via_ct_in_T(self, toy_reasoner_T):
        """From CT-failure-1: |~ p → q (by DD from p |~ q) and
        p → q, p ⊢ q (modus ponens, classically valid).

        The meta-level failure: |~ p → q and p |~ q → v
        but we cannot conclude |~ (p → q) ∧ (q → v) in a useful way
        that would give us p |~ v.

        Simpler: |~ p → q (theorem), and q ⊢ q (containment),
        but p |~ q (already works), while p ̸|~ v despite the chain.
        """
        # |~ p → q holds (by DD, since p |~ q)
        assert toy_reasoner_T.query(frozenset(), frozenset({"p -> q"}))
        # |~ (p & q) → v holds (by DD, since p, q |~ v)
        assert toy_reasoner_T.query(
            frozenset(), frozenset({"(p & q) -> v"})
        )
        # But p ̸|~ v (transitivity failure)
        assert not toy_reasoner_T.query(frozenset({"p"}), frozenset({"v"}))


# ============================================================
# 9. Mingle-Mix failure (p. 128)
# ============================================================

class TestMingleMixFailure:
    """Mingle-Mix says: if Γ |~ Δ and Θ |~ Λ, then Γ, Θ |~ Δ, Λ.

    This can fail in nonmonotonic bases. Example from Ch. 3 p. 128:
    p |~ q and r |~ s but p, r ̸|~ q, s.
    """

    @pytest.fixture
    def mingle_base(self):
        return MaterialBase(
            language={"p", "q", "r", "s"},
            consequences={
                (frozenset({"p"}), frozenset({"q"})),
                (frozenset({"r"}), frozenset({"s"})),
            },
        )

    @pytest.fixture
    def mingle_reasoner(self, mingle_base):
        return NMMSReasoner(mingle_base, max_depth=15)

    def test_p_derives_q(self, mingle_reasoner):
        """p |~ q — base consequence."""
        assert mingle_reasoner.query(frozenset({"p"}), frozenset({"q"}))

    def test_r_derives_s(self, mingle_reasoner):
        """r |~ s — base consequence."""
        assert mingle_reasoner.query(frozenset({"r"}), frozenset({"s"}))

    def test_mingle_mix_fails(self, mingle_reasoner):
        """p, r ̸|~ q, s — Mingle-Mix does NOT hold."""
        assert not mingle_reasoner.query(
            frozenset({"p", "r"}), frozenset({"q", "s"})
        )


# ============================================================
# 10. Conservative Extension (Fact 3/Prop. 26)
# ============================================================

class TestConservativeExtension:
    """If Γ ∪ Δ ⊆ L_B, then Γ |~ Δ iff Γ |~_B Δ (Proposition 26).

    Adding logical vocabulary does not change base-level reason relations.
    We verify this by checking that purely atomic sequents are derivable
    iff they are axioms (base consequences or Containment).
    """

    def test_base_consequence_preserved(self, toy_reasoner_T):
        """Base consequence p |~ q is preserved in extension."""
        assert toy_reasoner_T.query(frozenset({"p"}), frozenset({"q"}))

    def test_no_new_atomic_consequences(self, toy_reasoner_T):
        """p, r ̸|~ q is not an atomic consequence, and logical extension
        does not add it."""
        assert not toy_reasoner_T.query(
            frozenset({"p", "r"}), frozenset({"q"})
        )

    def test_containment_preserved(self, toy_reasoner_T):
        """Atomic containment: p ⊢ p."""
        assert toy_reasoner_T.query(frozenset({"p"}), frozenset({"p"}))

    def test_non_consequence_stays_non(self, toy_reasoner_T):
        """p ̸|~ v is not a base consequence and remains underivable
        at the atomic level."""
        assert not toy_reasoner_T.query(frozenset({"p"}), frozenset({"v"}))


# ============================================================
# 11. Modus ponens holds indefeasibly (p. 119)
# ============================================================

class TestModusPonensIndefeasible:
    """All instances of modus ponens hold: φ, φ → ψ |~ ψ.

    Moreover, they are indefeasible: weakening modus ponens with any
    additional premises still holds. This is because φ, φ → ψ ⊢ ψ
    is classically valid, and all classically valid sequents hold
    persistently (Fact 2).
    """

    def test_mp_basic(self, toy_reasoner_T):
        """p, p → q ⊢ q — modus ponens."""
        assert toy_reasoner_T.query(
            frozenset({"p", "p -> q"}), frozenset({"q"})
        )

    def test_mp_with_extra_premise(self, toy_reasoner_T):
        """p, p → q, r ⊢ q — weakened modus ponens still holds."""
        assert toy_reasoner_T.query(
            frozenset({"p", "p -> q", "r"}), frozenset({"q"})
        )

    def test_mp_with_unrelated_atoms(self, toy_reasoner_T):
        """s, s → w, t ⊢ w — modus ponens with extra premise."""
        assert toy_reasoner_T.query(
            frozenset({"s", "s -> w", "t"}), frozenset({"w"})
        )


# ============================================================
# 12. Proof-search termination and order-independence (Prop. 22)
# ============================================================

class TestProofSearchProperties:
    """Properties of proof-search from Definition 20 and Propositions 21-22."""

    def test_contraction_invariance(self, toy_reasoner_T):
        """Proposition 21: duplicating a sentence doesn't change result.

        p ⊢ q iff p, p ⊢ q — but since we use frozensets, duplicates
        are handled automatically. We verify the semantics match.
        """
        # p |~ q
        assert toy_reasoner_T.query(frozenset({"p"}), frozenset({"q"}))
        # p, p |~ q is the same sequent (frozenset collapses duplicates)
        assert toy_reasoner_T.query(frozenset({"p"}), frozenset({"q"}))

    def test_complex_formula_terminates(self, toy_reasoner_T):
        """Proposition 22: proof-search terminates for finite sequents.

        Test with a moderately complex formula to ensure termination.
        """
        result = toy_reasoner_T.derives(
            frozenset({"(p & q) | (r -> s)"}),
            frozenset({"(s | t) & (w -> x)"}),
        )
        # We just need it to terminate; derivability depends on the base
        assert isinstance(result.derivable, bool)
        assert result.depth_reached >= 0


# ============================================================
# 13. DD condition with T (various examples)
# ============================================================

class TestDDConditionWithT:
    """DD biconditional tested against Toy Base T.

    For each base consequence Γ |~ Δ where |Δ| = 1 (say Δ = {d}),
    we should have Γ' |~ d' → d where the conditional makes the
    consequence explicit (adapting for set notation).
    """

    def test_dd_for_consequence_1(self, toy_reasoner_T):
        """p |~ q iff ⊢ p → q."""
        assert toy_reasoner_T.query(frozenset({"p"}), frozenset({"q"}))
        assert toy_reasoner_T.query(frozenset(), frozenset({"p -> q"}))

    def test_dd_for_consequence_6(self, toy_reasoner_T):
        """p, q |~ v iff ⊢ (p ∧ q) → v."""
        assert toy_reasoner_T.query(
            frozenset({"p", "q"}), frozenset({"v"})
        )
        assert toy_reasoner_T.query(
            frozenset(), frozenset({"(p & q) -> v"})
        )

    def test_dd_for_consequence_8(self, toy_reasoner_T):
        """s |~ w iff ⊢ s → w."""
        assert toy_reasoner_T.query(frozenset({"s"}), frozenset({"w"}))
        assert toy_reasoner_T.query(frozenset(), frozenset({"s -> w"}))

    def test_dd_for_consequence_9(self, toy_reasoner_T):
        """s, w |~ x iff ⊢ (s ∧ w) → x."""
        assert toy_reasoner_T.query(
            frozenset({"s", "w"}), frozenset({"x"})
        )
        assert toy_reasoner_T.query(
            frozenset(), frozenset({"(s & w) -> x"})
        )


# ============================================================
# 14. II condition with T
# ============================================================

class TestIIConditionWithT:
    """II (Incoherence-Incompatibility) tested against Toy Base T.

    (3) s, t |~ ∅ iff ⊢ ¬(s ∧ t).
    """

    def test_ii_for_incompatibility_3(self, toy_reasoner_T):
        """s, t |~ iff ⊢ ¬(s ∧ t)."""
        assert toy_reasoner_T.query(frozenset({"s", "t"}), frozenset())
        assert toy_reasoner_T.query(frozenset(), frozenset({"~(s & t)"}))

    def test_ii_inverse(self, toy_reasoner_T):
        """⊢ ¬(s ∧ t) implies s, t |~."""
        # By II inverse: if ⊢ ¬(s ∧ t), then s ∧ t ⊢ (via L∧ and II)
        # which means s, t ⊢
        assert toy_reasoner_T.query(frozenset(), frozenset({"~(s & t)"}))
        assert toy_reasoner_T.query(frozenset({"s", "t"}), frozenset())


# ============================================================
# 15. Supraclassicality (Fact 2 / Prop. 25)
# ============================================================

class TestSupraclassicalityChapter3:
    """Fact 2 from Ch. 3: CL ⊆ |~.

    All classically valid sequents are derivable when base obeys Containment.
    Tests specific classical tautologies mentioned or implied in Ch. 3.
    """

    @pytest.fixture
    def classical_reasoner(self):
        """Reasoner with empty base (Containment only)."""
        return NMMSReasoner(MaterialBase(language={"p", "q", "r"}), max_depth=20)

    def test_lem(self, classical_reasoner):
        """⊢ p ∨ ¬p — law of excluded middle."""
        assert classical_reasoner.query(frozenset(), frozenset({"p | ~p"}))

    def test_identity(self, classical_reasoner):
        """p ⊢ p — identity (Containment)."""
        assert classical_reasoner.query(frozenset({"p"}), frozenset({"p"}))

    def test_explosion(self, classical_reasoner):
        """p, ¬p ⊢ q — ex falso quodlibet."""
        assert classical_reasoner.query(
            frozenset({"p", "~p"}), frozenset({"q"})
        )

    def test_double_negation(self, classical_reasoner):
        """¬¬p ⊢ p and p ⊢ ¬¬p — double negation."""
        assert classical_reasoner.query(frozenset({"~~p"}), frozenset({"p"}))
        assert classical_reasoner.query(frozenset({"p"}), frozenset({"~~p"}))

    def test_conditional_tautology(self, classical_reasoner):
        """⊢ p → p — conditional tautology."""
        assert classical_reasoner.query(frozenset(), frozenset({"p -> p"}))

    def test_distribution_classically_valid(self, classical_reasoner):
        """p ∧ (q ∨ r) ⊢ (p ∧ q) ∨ (p ∧ r) — distribution."""
        assert classical_reasoner.query(
            frozenset({"p & (q | r)"}),
            frozenset({"(p & q) | (p & r)"}),
        )

    def test_demorgan_1(self, classical_reasoner):
        """¬(p ∧ q) ⊢ ¬p ∨ ¬q — De Morgan."""
        assert classical_reasoner.query(
            frozenset({"~(p & q)"}), frozenset({"~p | ~q"})
        )

    def test_demorgan_2(self, classical_reasoner):
        """¬(p ∨ q) ⊢ ¬p ∧ ¬q — De Morgan."""
        assert classical_reasoner.query(
            frozenset({"~(p | q)"}), frozenset({"~p & ~q"})
        )

    def test_modus_ponens_classically(self, classical_reasoner):
        """p, p → q ⊢ q — modus ponens."""
        assert classical_reasoner.query(
            frozenset({"p", "p -> q"}), frozenset({"q"})
        )

    def test_hypothetical_syllogism(self, classical_reasoner):
        """p → q, q → r ⊢ p → r — hypothetical syllogism."""
        assert classical_reasoner.query(
            frozenset({"p -> q", "q -> r"}), frozenset({"p -> r"})
        )
