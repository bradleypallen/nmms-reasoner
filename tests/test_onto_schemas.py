"""Tests for ontology schema functionality.

Defeasible ontology axiom schemas: subClassOf, range, domain, subPropertyOf.
Tests cover schema matching, nonmonotonicity, non-transitivity, lazy
evaluation, and integration with NMMSReasoner.
"""


from pynmms.onto.base import CommitmentStore, OntoMaterialBase
from pynmms.reasoner import NMMSReasoner

# -------------------------------------------------------------------
# subClassOf schemas
# -------------------------------------------------------------------


class TestSubClassOf:
    def test_basic(self):
        """{Man(x)} |~ {Mortal(x)} for any x."""
        base = OntoMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        assert base.is_axiom(
            frozenset({"Man(socrates)"}),
            frozenset({"Mortal(socrates)"}),
        )

    def test_different_individual(self):
        """Schema works for any individual."""
        base = OntoMaterialBase(language={"Man(socrates)", "Man(plato)"})
        base.register_subclass("Man", "Mortal")
        assert base.is_axiom(
            frozenset({"Man(plato)"}),
            frozenset({"Mortal(plato)"}),
        )

    def test_wrong_concept(self):
        base = OntoMaterialBase(language={"Woman(alice)"})
        base.register_subclass("Man", "Mortal")
        assert not base.is_axiom(
            frozenset({"Woman(alice)"}),
            frozenset({"Mortal(alice)"}),
        )

    def test_no_weakening(self):
        base = OntoMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        assert not base.is_axiom(
            frozenset({"Man(socrates)", "Extra(x)"}),
            frozenset({"Mortal(socrates)"}),
        )

    def test_mismatched_individuals(self):
        """subClassOf requires same individual on both sides."""
        base = OntoMaterialBase(language={"Man(socrates)"})
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
        base = OntoMaterialBase(language={"hasChild(alice,bob)"})
        base.register_range("hasChild", "Person")
        assert base.is_axiom(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"Person(bob)"}),
        )

    def test_no_weakening(self):
        base = OntoMaterialBase(language={"hasChild(alice,bob)"})
        base.register_range("hasChild", "Person")
        assert not base.is_axiom(
            frozenset({"hasChild(alice,bob)", "Extra(x)"}),
            frozenset({"Person(bob)"}),
        )

    def test_wrong_individual(self):
        """Range applies to arg2, not arg1."""
        base = OntoMaterialBase(language={"hasChild(alice,bob)"})
        base.register_range("hasChild", "Person")
        assert not base.is_axiom(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"Person(alice)"}),
        )

    def test_different_subject(self):
        """Range schema works for any subject and object."""
        base = OntoMaterialBase(language={"hasChild(carol,dave)"})
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
        base = OntoMaterialBase(language={"hasChild(alice,bob)"})
        base.register_domain("hasChild", "Parent")
        assert base.is_axiom(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"Parent(alice)"}),
        )

    def test_wrong_individual(self):
        """Domain applies to arg1, not arg2."""
        base = OntoMaterialBase(language={"hasChild(alice,bob)"})
        base.register_domain("hasChild", "Parent")
        assert not base.is_axiom(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"Parent(bob)"}),
        )

    def test_no_weakening(self):
        base = OntoMaterialBase(language={"hasChild(alice,bob)"})
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
        base = OntoMaterialBase(language={"hasChild(alice,bob)"})
        base.register_subproperty("hasChild", "hasDescendant")
        assert base.is_axiom(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"hasDescendant(alice,bob)"}),
        )

    def test_swapped_args(self):
        """Arguments must match exactly."""
        base = OntoMaterialBase(language={"hasChild(alice,bob)"})
        base.register_subproperty("hasChild", "hasDescendant")
        assert not base.is_axiom(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"hasDescendant(bob,alice)"}),
        )

    def test_no_weakening(self):
        base = OntoMaterialBase(language={"hasChild(alice,bob)"})
        base.register_subproperty("hasChild", "hasDescendant")
        assert not base.is_axiom(
            frozenset({"hasChild(alice,bob)", "Extra(x)"}),
            frozenset({"hasDescendant(alice,bob)"}),
        )


# -------------------------------------------------------------------
# Onto Nonmonotonicity
# -------------------------------------------------------------------


class TestOntoNonmonotonicity:
    def test_extra_premise_defeats_subclass(self):
        base = OntoMaterialBase(language={"Man(socrates)"})
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
        base = OntoMaterialBase(language={"hasChild(alice,bob)"})
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
        base = OntoMaterialBase(language={"hasChild(alice,bob)"})
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
        base = OntoMaterialBase(language={"hasChild(alice,bob)"})
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
# Onto Non-transitivity (no Cut)
# -------------------------------------------------------------------


class TestDisjointWith:
    def test_basic(self):
        """{Man(x), Woman(x)} |~ {} for any x."""
        base = OntoMaterialBase(language={"Man(socrates)", "Woman(socrates)"})
        base.register_disjoint("Man", "Woman")
        assert base.is_axiom(
            frozenset({"Man(socrates)", "Woman(socrates)"}),
            frozenset(),
        )

    def test_order_independence(self):
        """Order of concepts in antecedent doesn't matter."""
        base = OntoMaterialBase(language={"Man(alice)", "Woman(alice)"})
        base.register_disjoint("Man", "Woman")
        assert base.is_axiom(
            frozenset({"Woman(alice)", "Man(alice)"}),
            frozenset(),
        )

    def test_wrong_concepts(self):
        base = OntoMaterialBase(language={"Cat(alice)", "Dog(alice)"})
        base.register_disjoint("Man", "Woman")
        assert not base.is_axiom(
            frozenset({"Cat(alice)", "Dog(alice)"}),
            frozenset(),
        )

    def test_mismatched_individuals(self):
        """disjointWith requires same individual for both concepts."""
        base = OntoMaterialBase(language={"Man(socrates)", "Woman(alice)"})
        base.register_disjoint("Man", "Woman")
        assert not base.is_axiom(
            frozenset({"Man(socrates)", "Woman(alice)"}),
            frozenset(),
        )

    def test_no_weakening(self):
        """Extra premise defeats incompatibility."""
        base = OntoMaterialBase(
            language={"Man(socrates)", "Woman(socrates)", "Extra(socrates)"},
        )
        base.register_disjoint("Man", "Woman")
        assert not base.is_axiom(
            frozenset({"Man(socrates)", "Woman(socrates)", "Extra(socrates)"}),
            frozenset(),
        )

    def test_nonempty_consequent_no_match(self):
        """disjointWith is incompatibility -- consequent must be empty."""
        base = OntoMaterialBase(language={"Man(socrates)", "Woman(socrates)"})
        base.register_disjoint("Man", "Woman")
        assert not base.is_axiom(
            frozenset({"Man(socrates)", "Woman(socrates)"}),
            frozenset({"Extra(socrates)"}),
        )

    def test_lazy_evaluation(self):
        """Schema matches any individual."""
        base = OntoMaterialBase(
            language={"Man(socrates)", "Woman(socrates)", "Man(plato)", "Woman(plato)"},
        )
        base.register_disjoint("Man", "Woman")
        for ind in ["socrates", "plato"]:
            assert base.is_axiom(
                frozenset({f"Man({ind})", f"Woman({ind})"}),
                frozenset(),
            )


class TestDisjointProperties:
    def test_basic(self):
        """{R(x,y), S(x,y)} |~ {} for any x, y."""
        base = OntoMaterialBase(
            language={"hasChild(alice,bob)", "hasParent(alice,bob)"},
        )
        base.register_disjoint_properties("hasChild", "hasParent")
        assert base.is_axiom(
            frozenset({"hasChild(alice,bob)", "hasParent(alice,bob)"}),
            frozenset(),
        )

    def test_order_independence(self):
        """Order of roles in antecedent doesn't matter."""
        base = OntoMaterialBase(
            language={"hasChild(alice,bob)", "hasParent(alice,bob)"},
        )
        base.register_disjoint_properties("hasChild", "hasParent")
        assert base.is_axiom(
            frozenset({"hasParent(alice,bob)", "hasChild(alice,bob)"}),
            frozenset(),
        )

    def test_wrong_roles(self):
        base = OntoMaterialBase(
            language={"likes(alice,bob)", "hates(alice,bob)"},
        )
        base.register_disjoint_properties("hasChild", "hasParent")
        assert not base.is_axiom(
            frozenset({"likes(alice,bob)", "hates(alice,bob)"}),
            frozenset(),
        )

    def test_mismatched_args(self):
        """Both role assertions must share the same arg1 and arg2."""
        base = OntoMaterialBase(
            language={"hasChild(alice,bob)", "hasParent(carol,dave)"},
        )
        base.register_disjoint_properties("hasChild", "hasParent")
        assert not base.is_axiom(
            frozenset({"hasChild(alice,bob)", "hasParent(carol,dave)"}),
            frozenset(),
        )

    def test_no_weakening(self):
        base = OntoMaterialBase(
            language={"hasChild(alice,bob)", "hasParent(alice,bob)", "Extra(alice)"},
        )
        base.register_disjoint_properties("hasChild", "hasParent")
        assert not base.is_axiom(
            frozenset({"hasChild(alice,bob)", "hasParent(alice,bob)", "Extra(alice)"}),
            frozenset(),
        )


# -------------------------------------------------------------------
# Onto Nonmonotonicity (incompatibility schemas)
# -------------------------------------------------------------------


class TestDisjointWithNonmonotonicity:
    def test_extra_premise_defeats_incompatibility(self):
        base = OntoMaterialBase(
            language={"Man(socrates)", "Woman(socrates)", "Extra(socrates)"},
        )
        base.register_disjoint("Man", "Woman")
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(
            frozenset({"Man(socrates)", "Woman(socrates)"}),
            frozenset(),
        )
        assert not r.query(
            frozenset({"Man(socrates)", "Woman(socrates)", "Extra(socrates)"}),
            frozenset(),
        )


class TestDisjointWithReasonerIntegration:
    def test_ii_condition(self):
        """II condition: {Man(x), Woman(x)} |~ {} implies {Man(x)} |~ {~Woman(x)}."""
        base = OntoMaterialBase(language={"Man(socrates)", "Woman(socrates)"})
        base.register_disjoint("Man", "Woman")
        r = NMMSReasoner(base, max_depth=15)
        # Direct incompatibility
        assert r.query(
            frozenset({"Man(socrates)", "Woman(socrates)"}),
            frozenset(),
        )
        # II condition: Gamma, A |~ Delta iff Gamma |~ ~A, Delta
        assert r.query(
            frozenset({"Man(socrates)"}),
            frozenset({"~Woman(socrates)"}),
        )

    def test_ddt_with_disjoint(self):
        """DDT: Man(a) -> ~Woman(a) derivable via disjointWith + II + R->."""
        base = OntoMaterialBase(language={"Man(socrates)", "Woman(socrates)"})
        base.register_disjoint("Man", "Woman")
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(
            frozenset(),
            frozenset({"Man(socrates) -> ~Woman(socrates)"}),
        )


class TestOntoNontransitivity:
    def test_subclass_no_chain(self):
        """Man ⊑ Mortal + Mortal ⊑ Physical does NOT yield Man(x) |~ Physical(x)."""
        base = OntoMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        base.register_subclass("Mortal", "Physical")
        r = NMMSReasoner(base, max_depth=15)
        assert not r.query(
            frozenset({"Man(socrates)"}),
            frozenset({"Physical(socrates)"}),
        )

    def test_subproperty_no_chain(self):
        """hasChild ⊑ hasDescendant + hasDescendant ⊑ hasRelative does NOT chain."""
        base = OntoMaterialBase(language={"hasChild(alice,bob)"})
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


class TestOntoLazyEvaluation:
    def test_no_eager_grounding(self):
        """Schemas are stored, not expanded to ground entries."""
        base = OntoMaterialBase(
            language={"Man(socrates)", "Man(plato)", "Man(aristotle)"},
        )
        base.register_subclass("Man", "Mortal")
        assert len(base._onto_schemas) == 1
        for individual in ["socrates", "plato", "aristotle"]:
            assert base.is_axiom(
                frozenset({f"Man({individual})"}),
                frozenset({f"Mortal({individual})"}),
            )

    def test_new_individual_works_without_regrounding(self):
        base = OntoMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        base.add_atom("Man(plato)")
        assert base.is_axiom(
            frozenset({"Man(plato)"}),
            frozenset({"Mortal(plato)"}),
        )


# -------------------------------------------------------------------
# Reasoner integration
# -------------------------------------------------------------------


class TestOntoReasonerIntegration:
    def test_subclass_with_reasoner(self):
        """NMMSReasoner works transparently with OntoMaterialBase."""
        base = OntoMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(
            frozenset({"Man(socrates)"}),
            frozenset({"Mortal(socrates)"}),
        )

    def test_ddt_with_subclass(self):
        """DDT: Man(a) -> Mortal(a) derivable via R-> decomposition."""
        base = OntoMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(
            frozenset(),
            frozenset({"Man(socrates) -> Mortal(socrates)"}),
        )

    def test_multiple_schemas(self):
        """Multiple schemas coexist."""
        base = OntoMaterialBase(language={"hasChild(alice,bob)"})
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
