"""Tests for pynmms.onto logging -- base creation and schema logging."""

import logging

from pynmms.onto.base import OntoMaterialBase
from pynmms.reasoner import NMMSReasoner


class TestOntoLogging:
    def test_base_creation_logged(self, caplog):
        with caplog.at_level(logging.DEBUG, logger="pynmms.onto.base"):
            OntoMaterialBase(language={"Happy(alice)"})
        assert any("OntoMaterialBase created" in msg for msg in caplog.messages)

    def test_schema_registration_logged(self, caplog):
        base = OntoMaterialBase(language={"Man(socrates)"})
        with caplog.at_level(logging.DEBUG, logger="pynmms.onto.base"):
            base.register_subclass("Man", "Mortal")
        assert any("subClassOf" in msg for msg in caplog.messages)

    def test_range_schema_logged(self, caplog):
        base = OntoMaterialBase(language={"hasChild(alice,bob)"})
        with caplog.at_level(logging.DEBUG, logger="pynmms.onto.base"):
            base.register_range("hasChild", "Person")
        assert any("range" in msg for msg in caplog.messages)

    def test_domain_schema_logged(self, caplog):
        base = OntoMaterialBase(language={"hasChild(alice,bob)"})
        with caplog.at_level(logging.DEBUG, logger="pynmms.onto.base"):
            base.register_domain("hasChild", "Parent")
        assert any("domain" in msg for msg in caplog.messages)

    def test_subproperty_schema_logged(self, caplog):
        base = OntoMaterialBase(language={"hasChild(alice,bob)"})
        with caplog.at_level(logging.DEBUG, logger="pynmms.onto.base"):
            base.register_subproperty("hasChild", "hasDescendant")
        assert any("subPropertyOf" in msg for msg in caplog.messages)

    def test_disjoint_schema_logged(self, caplog):
        base = OntoMaterialBase(language={"Man(socrates)", "Woman(socrates)"})
        with caplog.at_level(logging.DEBUG, logger="pynmms.onto.base"):
            base.register_disjoint("Man", "Woman")
        assert any("disjointWith" in msg for msg in caplog.messages)

    def test_disjoint_properties_schema_logged(self, caplog):
        base = OntoMaterialBase(
            language={"hasChild(alice,bob)", "hasParent(alice,bob)"},
        )
        with caplog.at_level(logging.DEBUG, logger="pynmms.onto.base"):
            base.register_disjoint_properties("hasChild", "hasParent")
        assert any("disjointProperties" in msg for msg in caplog.messages)

    def test_joint_commitment_schema_logged(self, caplog):
        base = OntoMaterialBase(
            language={"ChestPain(patient)", "ElevatedTroponin(patient)"},
        )
        with caplog.at_level(logging.DEBUG, logger="pynmms.onto.base"):
            base.register_joint_commitment(["ChestPain", "ElevatedTroponin"], "MI")
        assert any("jointCommitment" in msg for msg in caplog.messages)


class TestOntoProofTraces:
    def test_propositional_rules_in_trace(self):
        base = OntoMaterialBase(language={"P(a)", "Q(a)"})
        r = NMMSReasoner(base, max_depth=15)
        result = r.derives(frozenset({"P(a) & Q(a)"}), frozenset({"P(a)"}))
        assert result.derivable
        trace = "\n".join(result.trace)
        assert "[L\u2227]" in trace

    def test_axiom_in_trace(self):
        base = OntoMaterialBase(language={"Happy(alice)"})
        r = NMMSReasoner(base, max_depth=15)
        result = r.derives(
            frozenset({"Happy(alice)"}), frozenset({"Happy(alice)"})
        )
        assert result.derivable
        assert any("AXIOM" in t for t in result.trace)

    def test_depth_limit_in_trace(self):
        base = OntoMaterialBase()
        r = NMMSReasoner(base, max_depth=0)
        result = r.derives(frozenset({"P(a) -> Q(a)"}), frozenset({"R(a)"}))
        assert not result.derivable
        assert any("DEPTH LIMIT" in t for t in result.trace)
