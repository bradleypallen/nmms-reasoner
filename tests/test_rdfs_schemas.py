"""Tests for RDFS schema functionality.

Defeasible RDFS axiom schemas: subClassOf, range, domain, subPropertyOf.
Tests cover schema matching, nonmonotonicity, non-transitivity, lazy
evaluation, and integration with NMMSReasoner.
"""


from pynmms.rdfs.base import CommitmentStore, RDFSMaterialBase
from pynmms.reasoner import NMMSReasoner

# -------------------------------------------------------------------
# subClassOf schemas
# -------------------------------------------------------------------


class TestSubClassOf:
    def test_basic(self):
        """{Man(x)} |~ {Mortal(x)} for any x."""
        base = RDFSMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        assert base.is_axiom(
            frozenset({"Man(socrates)"}),
            frozenset({"Mortal(socrates)"}),
        )

    def test_different_individual(self):
        """Schema works for any individual."""
        base = RDFSMaterialBase(language={"Man(socrates)", "Man(plato)"})
        base.register_subclass("Man", "Mortal")
        assert base.is_axiom(
            frozenset({"Man(plato)"}),
            frozenset({"Mortal(plato)"}),
        )

    def test_wrong_concept(self):
        base = RDFSMaterialBase(language={"Woman(alice)"})
        base.register_subclass("Man", "Mortal")
        assert not base.is_axiom(
            frozenset({"Woman(alice)"}),
            frozenset({"Mortal(alice)"}),
        )

    def test_no_weakening(self):
        base = RDFSMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        assert not base.is_axiom(
            frozenset({"Man(socrates)", "Extra(x)"}),
            frozenset({"Mortal(socrates)"}),
        )

    def test_mismatched_individuals(self):
        """subClassOf requires same individual on both sides."""
        base = RDFSMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        assert not base.is_axiom(
            frozenset({"Man(socrates)"}),
            frozenset({"Mortal(plato)"}),
        )


# -------------------------------------------------------------------
# range schemas
# -------------------------------------------------------------------


class TestRange:
    def test_basic(self):
        """{R(x,y)} |~ {C(y)} -- concept applies to arg2."""
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        base.register_range("hasChild", "Person")
        assert base.is_axiom(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"Person(bob)"}),
        )

    def test_no_weakening(self):
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        base.register_range("hasChild", "Person")
        assert not base.is_axiom(
            frozenset({"hasChild(alice,bob)", "Extra(x)"}),
            frozenset({"Person(bob)"}),
        )

    def test_wrong_individual(self):
        """Range applies to arg2, not arg1."""
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        base.register_range("hasChild", "Person")
        assert not base.is_axiom(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"Person(alice)"}),
        )

    def test_different_subject(self):
        """Range schema works for any subject and object."""
        base = RDFSMaterialBase(language={"hasChild(carol,dave)"})
        base.register_range("hasChild", "Person")
        assert base.is_axiom(
            frozenset({"hasChild(carol,dave)"}),
            frozenset({"Person(dave)"}),
        )


# -------------------------------------------------------------------
# domain schemas
# -------------------------------------------------------------------


class TestDomain:
    def test_basic(self):
        """{R(x,y)} |~ {C(x)} -- concept applies to arg1."""
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        base.register_domain("hasChild", "Parent")
        assert base.is_axiom(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"Parent(alice)"}),
        )

    def test_wrong_individual(self):
        """Domain applies to arg1, not arg2."""
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        base.register_domain("hasChild", "Parent")
        assert not base.is_axiom(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"Parent(bob)"}),
        )

    def test_no_weakening(self):
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        base.register_domain("hasChild", "Parent")
        assert not base.is_axiom(
            frozenset({"hasChild(alice,bob)", "Extra(x)"}),
            frozenset({"Parent(alice)"}),
        )


# -------------------------------------------------------------------
# subPropertyOf schemas
# -------------------------------------------------------------------


class TestSubPropertyOf:
    def test_basic(self):
        """{R(x,y)} |~ {S(x,y)} -- same arguments."""
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        base.register_subproperty("hasChild", "hasDescendant")
        assert base.is_axiom(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"hasDescendant(alice,bob)"}),
        )

    def test_swapped_args(self):
        """Arguments must match exactly."""
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        base.register_subproperty("hasChild", "hasDescendant")
        assert not base.is_axiom(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"hasDescendant(bob,alice)"}),
        )

    def test_no_weakening(self):
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        base.register_subproperty("hasChild", "hasDescendant")
        assert not base.is_axiom(
            frozenset({"hasChild(alice,bob)", "Extra(x)"}),
            frozenset({"hasDescendant(alice,bob)"}),
        )


# -------------------------------------------------------------------
# RDFS Nonmonotonicity
# -------------------------------------------------------------------


class TestRDFSNonmonotonicity:
    def test_extra_premise_defeats_subclass(self):
        base = RDFSMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(
            frozenset({"Man(socrates)"}),
            frozenset({"Mortal(socrates)"}),
        )
        assert not r.query(
            frozenset({"Man(socrates)", "Immortal(socrates)"}),
            frozenset({"Mortal(socrates)"}),
        )

    def test_extra_premise_defeats_range(self):
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        base.register_range("hasChild", "Person")
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"Person(bob)"}),
        )
        assert not r.query(
            frozenset({"hasChild(alice,bob)", "Robot(bob)"}),
            frozenset({"Person(bob)"}),
        )

    def test_extra_premise_defeats_domain(self):
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        base.register_domain("hasChild", "Parent")
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"Parent(alice)"}),
        )
        assert not r.query(
            frozenset({"hasChild(alice,bob)", "NonParent(alice)"}),
            frozenset({"Parent(alice)"}),
        )

    def test_extra_premise_defeats_subproperty(self):
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        base.register_subproperty("hasChild", "hasDescendant")
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"hasDescendant(alice,bob)"}),
        )
        assert not r.query(
            frozenset({"hasChild(alice,bob)", "Extra(x)"}),
            frozenset({"hasDescendant(alice,bob)"}),
        )


# -------------------------------------------------------------------
# RDFS Non-transitivity (no Cut)
# -------------------------------------------------------------------


class TestRDFSNontransitivity:
    def test_subclass_no_chain(self):
        """Man ⊑ Mortal + Mortal ⊑ Physical does NOT yield Man(x) |~ Physical(x)."""
        base = RDFSMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        base.register_subclass("Mortal", "Physical")
        r = NMMSReasoner(base, max_depth=15)
        assert not r.query(
            frozenset({"Man(socrates)"}),
            frozenset({"Physical(socrates)"}),
        )

    def test_subproperty_no_chain(self):
        """hasChild ⊑ hasDescendant + hasDescendant ⊑ hasRelative does NOT chain."""
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        base.register_subproperty("hasChild", "hasDescendant")
        base.register_subproperty("hasDescendant", "hasRelative")
        r = NMMSReasoner(base, max_depth=15)
        assert not r.query(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"hasRelative(alice,bob)"}),
        )


# -------------------------------------------------------------------
# Lazy evaluation
# -------------------------------------------------------------------


class TestRDFSLazyEvaluation:
    def test_no_eager_grounding(self):
        """Schemas are stored, not expanded to ground entries."""
        base = RDFSMaterialBase(
            language={"Man(socrates)", "Man(plato)", "Man(aristotle)"},
        )
        base.register_subclass("Man", "Mortal")
        assert len(base._rdfs_schemas) == 1
        for individual in ["socrates", "plato", "aristotle"]:
            assert base.is_axiom(
                frozenset({f"Man({individual})"}),
                frozenset({f"Mortal({individual})"}),
            )

    def test_new_individual_works_without_regrounding(self):
        base = RDFSMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        base.add_atom("Man(plato)")
        assert base.is_axiom(
            frozenset({"Man(plato)"}),
            frozenset({"Mortal(plato)"}),
        )


# -------------------------------------------------------------------
# Reasoner integration
# -------------------------------------------------------------------


class TestRDFSReasonerIntegration:
    def test_subclass_with_reasoner(self):
        """NMMSReasoner works transparently with RDFSMaterialBase."""
        base = RDFSMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(
            frozenset({"Man(socrates)"}),
            frozenset({"Mortal(socrates)"}),
        )

    def test_ddt_with_subclass(self):
        """DDT: Man(a) -> Mortal(a) derivable via R-> decomposition."""
        base = RDFSMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(
            frozenset(),
            frozenset({"Man(socrates) -> Mortal(socrates)"}),
        )

    def test_multiple_schemas(self):
        """Multiple schemas coexist."""
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        base.register_range("hasChild", "Person")
        base.register_domain("hasChild", "Parent")
        base.register_subproperty("hasChild", "hasDescendant")
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"Person(bob)"}),
        )
        assert r.query(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"Parent(alice)"}),
        )
        assert r.query(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"hasDescendant(alice,bob)"}),
        )

    def test_commitment_store_integration(self):
        """CommitmentStore + NMMSReasoner end-to-end."""
        cs = CommitmentStore()
        cs.add_assertion("Man(socrates)")
        cs.commit_subclass("man_mortal", "Man", "Mortal")
        base = cs.compile()
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(
            frozenset({"Man(socrates)"}),
            frozenset({"Mortal(socrates)"}),
        )
