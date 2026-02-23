"""Tests for pynmms.rdfs.base -- RDFSMaterialBase and CommitmentStore."""

import tempfile
from pathlib import Path

import pytest

from pynmms.rdfs.base import (
    CommitmentStore,
    RDFSMaterialBase,
    _validate_rdfs_atomic,
)

# -------------------------------------------------------------------
# RDFSMaterialBase construction and validation
# -------------------------------------------------------------------


class TestRDFSMaterialBaseConstruction:
    def test_empty_base(self):
        base = RDFSMaterialBase()
        assert base.language == frozenset()
        assert base.consequences == frozenset()
        assert base.individuals == frozenset()
        assert base.concepts == frozenset()
        assert base.roles == frozenset()

    def test_with_concept_assertions(self):
        base = RDFSMaterialBase(language={"Happy(alice)", "Sad(bob)"})
        assert "Happy(alice)" in base.language
        assert base.individuals == frozenset({"alice", "bob"})
        assert base.concepts == frozenset({"Happy", "Sad"})

    def test_with_role_assertions(self):
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        assert base.individuals == frozenset({"alice", "bob"})
        assert base.roles == frozenset({"hasChild"})

    def test_rejects_bare_atoms(self):
        with pytest.raises(ValueError, match="not valid in NMMS_RDFS"):
            RDFSMaterialBase(language={"A", "B"})

    def test_with_consequences(self):
        base = RDFSMaterialBase(
            language={"Happy(alice)", "Sad(alice)"},
            consequences={
                (frozenset({"Happy(alice)"}), frozenset({"Sad(alice)"})),
            },
        )
        assert len(base.consequences) == 1

    def test_rejects_negation_in_language(self):
        with pytest.raises(ValueError, match="not valid in NMMS_RDFS"):
            RDFSMaterialBase(language={"~A"})

    def test_rejects_conjunction_in_consequence(self):
        with pytest.raises(ValueError, match="not valid in NMMS_RDFS"):
            RDFSMaterialBase(
                consequences={
                    (frozenset({"P(a) & Q(a)"}), frozenset({"R(a)"})),
                },
            )


class TestRDFSMaterialBaseValidateAtomic:
    def test_concept_assertion_ok(self):
        _validate_rdfs_atomic("Happy(alice)", "test")  # no error

    def test_role_assertion_ok(self):
        _validate_rdfs_atomic("hasChild(alice,bob)", "test")

    def test_bare_atom_rejected(self):
        with pytest.raises(ValueError, match="not valid in NMMS_RDFS"):
            _validate_rdfs_atomic("A", "test")

    def test_negation_rejected(self):
        with pytest.raises(ValueError):
            _validate_rdfs_atomic("~A", "test")


# -------------------------------------------------------------------
# Mutation
# -------------------------------------------------------------------


class TestRDFSMaterialBaseMutation:
    def test_add_atom_concept(self):
        base = RDFSMaterialBase()
        base.add_atom("Happy(alice)")
        assert "Happy(alice)" in base.language
        assert "alice" in base.individuals
        assert "Happy" in base.concepts

    def test_add_atom_role(self):
        base = RDFSMaterialBase()
        base.add_atom("hasChild(alice,bob)")
        assert "hasChild" in base.roles

    def test_add_consequence(self):
        base = RDFSMaterialBase()
        base.add_consequence(
            frozenset({"Happy(alice)"}), frozenset({"Good(alice)"})
        )
        assert len(base.consequences) == 1
        assert "alice" in base.individuals

    def test_add_individual(self):
        base = RDFSMaterialBase()
        base.add_individual("hasChild", "alice", "bob")
        assert "hasChild(alice,bob)" in base.language
        assert "hasChild" in base.roles

    def test_add_atom_rejects_complex(self):
        base = RDFSMaterialBase()
        with pytest.raises(ValueError):
            base.add_atom("~Happy(alice)")

    def test_add_consequence_rejects_complex(self):
        base = RDFSMaterialBase()
        with pytest.raises(ValueError):
            base.add_consequence(frozenset({"P(a) -> Q(a)"}), frozenset({"R(a)"}))


# -------------------------------------------------------------------
# Axiom checking
# -------------------------------------------------------------------


class TestRDFSMaterialBaseIsAxiom:
    def test_containment(self):
        base = RDFSMaterialBase(language={"Happy(alice)"})
        assert base.is_axiom(
            frozenset({"Happy(alice)"}), frozenset({"Happy(alice)"})
        )

    def test_explicit_consequence(self):
        base = RDFSMaterialBase(
            consequences={
                (frozenset({"Happy(alice)"}), frozenset({"Good(alice)"})),
            },
        )
        assert base.is_axiom(
            frozenset({"Happy(alice)"}), frozenset({"Good(alice)"})
        )

    def test_no_weakening(self):
        """Extra premises defeat the axiom match."""
        base = RDFSMaterialBase(
            consequences={
                (frozenset({"Happy(alice)"}), frozenset({"Good(alice)"})),
            },
        )
        assert not base.is_axiom(
            frozenset({"Happy(alice)", "Sad(alice)"}),
            frozenset({"Good(alice)"}),
        )

    def test_rdfs_subclass(self):
        base = RDFSMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        assert base.is_axiom(
            frozenset({"Man(socrates)"}),
            frozenset({"Mortal(socrates)"}),
        )

    def test_rdfs_range(self):
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        base.register_range("hasChild", "Person")
        assert base.is_axiom(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"Person(bob)"}),
        )

    def test_rdfs_domain(self):
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        base.register_domain("hasChild", "Parent")
        assert base.is_axiom(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"Parent(alice)"}),
        )

    def test_rdfs_subproperty(self):
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        base.register_subproperty("hasChild", "hasDescendant")
        assert base.is_axiom(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"hasDescendant(alice,bob)"}),
        )

    def test_rdfs_no_weakening(self):
        """Extra premises defeat RDFS schema match."""
        base = RDFSMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        assert not base.is_axiom(
            frozenset({"Man(socrates)", "Extra(x)"}),
            frozenset({"Mortal(socrates)"}),
        )

    def test_no_match(self):
        base = RDFSMaterialBase(language={"P(a)"})
        assert not base.is_axiom(frozenset({"P(a)"}), frozenset({"Q(a)"}))


# -------------------------------------------------------------------
# Serialization
# -------------------------------------------------------------------


class TestRDFSMaterialBaseSerialization:
    def test_to_dict_and_back(self):
        base = RDFSMaterialBase(
            language={"Happy(alice)", "hasChild(alice,bob)"},
            consequences={
                (frozenset({"Happy(alice)"}), frozenset({"Good(alice)"})),
            },
        )
        base.register_subclass("Man", "Mortal")

        d = base.to_dict()
        assert "rdfs_schemas" in d
        assert len(d["rdfs_schemas"]) == 1

        restored = RDFSMaterialBase.from_dict(d)
        assert restored.language == base.language
        assert restored.consequences == base.consequences
        assert len(restored._rdfs_schemas) == 1

    def test_to_file_and_back(self):
        base = RDFSMaterialBase(
            language={"Happy(alice)"},
            consequences={
                (frozenset({"Happy(alice)"}), frozenset({"Good(alice)"})),
            },
        )
        base.register_range("hasChild", "Person")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            base.to_file(path)
            restored = RDFSMaterialBase.from_file(path)
            assert restored.language == base.language
            assert restored.consequences == base.consequences
            assert len(restored._rdfs_schemas) == 1
        finally:
            Path(path).unlink()


# -------------------------------------------------------------------
# CommitmentStore
# -------------------------------------------------------------------


class TestCommitmentStore:
    def test_empty(self):
        cs = CommitmentStore()
        assert len(cs.assertions) == 0
        assert len(cs._rdfs_commitments) == 0

    def test_add_assertion(self):
        cs = CommitmentStore()
        cs.add_assertion("Happy(alice)")
        assert "Happy(alice)" in cs.assertions

    def test_add_role(self):
        cs = CommitmentStore()
        cs.add_role("hasChild", "alice", "bob")
        assert "hasChild(alice,bob)" in cs.assertions

    def test_add_concept(self):
        cs = CommitmentStore()
        cs.add_concept("Happy", "alice")
        assert "Happy(alice)" in cs.assertions

    def test_commit_subclass(self):
        cs = CommitmentStore()
        cs.commit_subclass("man_mortal", "Man", "Mortal")
        assert len(cs._rdfs_commitments) == 1
        assert cs._rdfs_commitments[0] == ("man_mortal", "subClassOf", "Man", "Mortal")

    def test_commit_range(self):
        cs = CommitmentStore()
        cs.commit_range("child_person", "hasChild", "Person")
        assert len(cs._rdfs_commitments) == 1

    def test_commit_domain(self):
        cs = CommitmentStore()
        cs.commit_domain("child_parent", "hasChild", "Parent")
        assert len(cs._rdfs_commitments) == 1

    def test_commit_subproperty(self):
        cs = CommitmentStore()
        cs.commit_subproperty("child_desc", "hasChild", "hasDescendant")
        assert len(cs._rdfs_commitments) == 1

    def test_commit_defeasible_rule(self):
        cs = CommitmentStore()
        cs.commit_defeasible_rule(
            "bob's happiness",
            frozenset({"Happy(bob)"}),
            frozenset({"Good(bob)"}),
        )
        base = cs.compile()
        assert base.is_axiom(
            frozenset({"Happy(bob)"}), frozenset({"Good(bob)"})
        )

    def test_retract_schema(self):
        cs = CommitmentStore()
        cs.commit_subclass("man_mortal", "Man", "Mortal")
        assert len(cs._rdfs_commitments) == 1
        cs.retract_schema("man_mortal")
        assert len(cs._rdfs_commitments) == 0

    def test_compile_produces_base(self):
        cs = CommitmentStore()
        cs.add_assertion("Man(socrates)")
        cs.commit_subclass("man_mortal", "Man", "Mortal")
        base = cs.compile()
        assert isinstance(base, RDFSMaterialBase)
        assert "Man(socrates)" in base.language

    def test_compile_caches(self):
        cs = CommitmentStore()
        cs.add_assertion("P(a)")
        base1 = cs.compile()
        base2 = cs.compile()
        assert base1 is base2

    def test_compile_invalidated_by_assertion(self):
        cs = CommitmentStore()
        cs.add_assertion("P(a)")
        base1 = cs.compile()
        cs.add_assertion("Q(a)")
        base2 = cs.compile()
        assert base1 is not base2

    def test_compile_with_subclass_schema(self):
        cs = CommitmentStore()
        cs.add_assertion("Man(socrates)")
        cs.commit_subclass("man_mortal", "Man", "Mortal")
        base = cs.compile()
        assert base.is_axiom(
            frozenset({"Man(socrates)"}),
            frozenset({"Mortal(socrates)"}),
        )

    def test_describe(self):
        cs = CommitmentStore()
        cs.add_assertion("Happy(alice)")
        cs.commit_subclass("test", "Man", "Mortal")
        desc = cs.describe()
        assert "Happy(alice)" in desc
        assert "test" in desc
        assert "subClassOf" in desc

    def test_rejects_complex_assertion(self):
        cs = CommitmentStore()
        with pytest.raises(ValueError):
            cs.add_assertion("~Happy(alice)")
