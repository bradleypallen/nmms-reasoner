"""Tests for pynmms.rdfs logging -- base creation and schema logging."""

import logging

from pynmms.rdfs.base import RDFSMaterialBase
from pynmms.reasoner import NMMSReasoner


class TestRDFSLogging:
    def test_base_creation_logged(self, caplog):
        with caplog.at_level(logging.DEBUG, logger="pynmms.rdfs.base"):
            RDFSMaterialBase(language={"Happy(alice)"})
        assert any("RDFSMaterialBase created" in msg for msg in caplog.messages)

    def test_schema_registration_logged(self, caplog):
        base = RDFSMaterialBase(language={"Man(socrates)"})
        with caplog.at_level(logging.DEBUG, logger="pynmms.rdfs.base"):
            base.register_subclass("Man", "Mortal")
        assert any("subClassOf" in msg for msg in caplog.messages)

    def test_range_schema_logged(self, caplog):
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        with caplog.at_level(logging.DEBUG, logger="pynmms.rdfs.base"):
            base.register_range("hasChild", "Person")
        assert any("range" in msg for msg in caplog.messages)

    def test_domain_schema_logged(self, caplog):
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        with caplog.at_level(logging.DEBUG, logger="pynmms.rdfs.base"):
            base.register_domain("hasChild", "Parent")
        assert any("domain" in msg for msg in caplog.messages)

    def test_subproperty_schema_logged(self, caplog):
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        with caplog.at_level(logging.DEBUG, logger="pynmms.rdfs.base"):
            base.register_subproperty("hasChild", "hasDescendant")
        assert any("subPropertyOf" in msg for msg in caplog.messages)


class TestRDFSProofTraces:
    def test_propositional_rules_in_trace(self):
        base = RDFSMaterialBase(language={"P(a)", "Q(a)"})
        r = NMMSReasoner(base, max_depth=15)
        result = r.derives(frozenset({"P(a) & Q(a)"}), frozenset({"P(a)"}))
        assert result.derivable
        trace = "\n".join(result.trace)
        assert "[L\u2227]" in trace

    def test_axiom_in_trace(self):
        base = RDFSMaterialBase(language={"Happy(alice)"})
        r = NMMSReasoner(base, max_depth=15)
        result = r.derives(
            frozenset({"Happy(alice)"}), frozenset({"Happy(alice)"})
        )
        assert result.derivable
        assert any("AXIOM" in t for t in result.trace)

    def test_depth_limit_in_trace(self):
        base = RDFSMaterialBase()
        r = NMMSReasoner(base, max_depth=0)
        result = r.derives(frozenset({"P(a) -> Q(a)"}), frozenset({"R(a)"}))
        assert not result.derivable
        assert any("DEPTH LIMIT" in t for t in result.trace)
