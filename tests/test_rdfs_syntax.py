"""Tests for pynmms.rdfs.syntax -- RDFS sentence parsing and helpers."""

import pytest

from pynmms.rdfs.syntax import (
    ATOM_CONCEPT,
    ATOM_ROLE,
    RDFSSentence,
    all_rdfs_atomic,
    is_rdfs_atomic,
    make_concept_assertion,
    make_role_assertion,
    parse_rdfs_sentence,
)
from pynmms.syntax import CONJ, DISJ, IMPL, NEG, Sentence

# -------------------------------------------------------------------
# Parsing: RDFS-specific sentence types
# -------------------------------------------------------------------


class TestParseConceptAssertion:
    def test_simple(self):
        p = parse_rdfs_sentence("Human(alice)")
        assert isinstance(p, RDFSSentence)
        assert p.type == ATOM_CONCEPT
        assert p.concept == "Human"
        assert p.individual == "alice"

    def test_str_roundtrip(self):
        p = parse_rdfs_sentence("Happy(bob)")
        assert str(p) == "Happy(bob)"

    def test_with_whitespace(self):
        p = parse_rdfs_sentence("  Happy(bob)  ")
        assert isinstance(p, RDFSSentence)
        assert p.type == ATOM_CONCEPT


class TestParseRoleAssertion:
    def test_simple(self):
        p = parse_rdfs_sentence("hasChild(alice,bob)")
        assert isinstance(p, RDFSSentence)
        assert p.type == ATOM_ROLE
        assert p.role == "hasChild"
        assert p.arg1 == "alice"
        assert p.arg2 == "bob"

    def test_with_spaces(self):
        p = parse_rdfs_sentence("hasChild(alice, bob)")
        assert isinstance(p, RDFSSentence)
        assert p.type == ATOM_ROLE
        assert p.arg2 == "bob"

    def test_str_roundtrip(self):
        p = parse_rdfs_sentence("teaches(dept,alice)")
        assert str(p) == "teaches(dept,alice)"


# -------------------------------------------------------------------
# Parsing: propositional fallthrough
# -------------------------------------------------------------------


class TestParsePropositional:
    def test_bare_atom_rejected(self):
        with pytest.raises(ValueError, match="not valid in NMMS_RDFS"):
            parse_rdfs_sentence("A")

    def test_negation(self):
        p = parse_rdfs_sentence("~A")
        assert isinstance(p, Sentence)
        assert p.type == NEG

    def test_conjunction(self):
        p = parse_rdfs_sentence("A & B")
        assert isinstance(p, Sentence)
        assert p.type == CONJ

    def test_disjunction(self):
        p = parse_rdfs_sentence("A | B")
        assert isinstance(p, Sentence)
        assert p.type == DISJ

    def test_implication(self):
        p = parse_rdfs_sentence("A -> B")
        assert isinstance(p, Sentence)
        assert p.type == IMPL

    def test_nested_parens(self):
        p = parse_rdfs_sentence("(A & B) -> C")
        assert isinstance(p, Sentence)
        assert p.type == IMPL

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            parse_rdfs_sentence("")


# -------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------


class TestMakeAssertions:
    def test_concept(self):
        assert make_concept_assertion("Happy", "bob") == "Happy(bob)"

    def test_role(self):
        assert make_role_assertion("hasChild", "alice", "bob") == "hasChild(alice,bob)"


# -------------------------------------------------------------------
# Atomicity checks
# -------------------------------------------------------------------


class TestIsRDFSAtomic:
    def test_concept_assertion(self):
        assert is_rdfs_atomic("Happy(alice)") is True

    def test_role_assertion(self):
        assert is_rdfs_atomic("hasChild(alice,bob)") is True

    def test_bare_atom(self):
        assert is_rdfs_atomic("A") is False

    def test_negation_not_atomic(self):
        assert is_rdfs_atomic("~A") is False

    def test_conjunction_not_atomic(self):
        assert is_rdfs_atomic("A & B") is False


class TestAllRDFSAtomic:
    def test_all_atomic(self):
        sentences = frozenset({"Happy(alice)", "hasChild(alice,bob)"})
        assert all_rdfs_atomic(sentences) is True

    def test_bare_atom_not_atomic(self):
        sentences = frozenset({"Happy(alice)", "A"})
        assert all_rdfs_atomic(sentences) is False

    def test_empty(self):
        assert all_rdfs_atomic(frozenset()) is True
