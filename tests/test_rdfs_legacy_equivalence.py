"""RDFS demo scenario equivalence tests.

Verifies backward compatibility and RDFS schema functionality using
NMMSReasoner + RDFSMaterialBase.
"""

from pynmms.rdfs.base import RDFSMaterialBase
from pynmms.reasoner import NMMSReasoner


def _r(language=None, consequences=None, max_depth=25):
    base = RDFSMaterialBase(
        language=language or set(),
        consequences=consequences or set(),
    )
    return NMMSReasoner(base, max_depth=max_depth)


# -------------------------------------------------------------------
# Demo 1: Propositional backward compatibility
# -------------------------------------------------------------------


class TestDemo1PropositionalBackwardCompat:
    """NMMSReasoner + RDFSMaterialBase with propositional-only features."""

    def test_containment(self):
        r = _r(language={"P(a)", "Q(a)", "R(a)"}, consequences={
            (frozenset({"P(a)"}), frozenset({"Q(a)"})),
            (frozenset({"Q(a)"}), frozenset({"R(a)"})),
        }, max_depth=15)
        assert r.query(frozenset({"P(a)"}), frozenset({"P(a)"}))

    def test_base_consequence_ab(self):
        r = _r(language={"P(a)", "Q(a)", "R(a)"}, consequences={
            (frozenset({"P(a)"}), frozenset({"Q(a)"})),
            (frozenset({"Q(a)"}), frozenset({"R(a)"})),
        }, max_depth=15)
        assert r.query(frozenset({"P(a)"}), frozenset({"Q(a)"}))

    def test_base_consequence_bc(self):
        r = _r(language={"P(a)", "Q(a)", "R(a)"}, consequences={
            (frozenset({"P(a)"}), frozenset({"Q(a)"})),
            (frozenset({"Q(a)"}), frozenset({"R(a)"})),
        }, max_depth=15)
        assert r.query(frozenset({"Q(a)"}), frozenset({"R(a)"}))

    def test_nontransitivity(self):
        r = _r(language={"P(a)", "Q(a)", "R(a)"}, consequences={
            (frozenset({"P(a)"}), frozenset({"Q(a)"})),
            (frozenset({"Q(a)"}), frozenset({"R(a)"})),
        }, max_depth=15)
        assert not r.query(frozenset({"P(a)"}), frozenset({"R(a)"}))

    def test_nonmonotonicity(self):
        r = _r(language={"P(a)", "Q(a)", "R(a)"}, consequences={
            (frozenset({"P(a)"}), frozenset({"Q(a)"})),
            (frozenset({"Q(a)"}), frozenset({"R(a)"})),
        }, max_depth=15)
        assert not r.query(frozenset({"P(a)", "R(a)"}), frozenset({"Q(a)"}))

    def test_lem(self):
        r = _r(language={"P(a)"}, max_depth=15)
        assert r.query(frozenset(), frozenset({"P(a) | ~P(a)"}))

    def test_ddt(self):
        r = _r(language={"P(a)", "Q(a)"}, consequences={
            (frozenset({"P(a)"}), frozenset({"Q(a)"})),
        }, max_depth=15)
        assert r.query(frozenset(), frozenset({"P(a) -> Q(a)"}))


# -------------------------------------------------------------------
# Demo 3: Medical Diagnosis (concept/role assertions as opaque atoms)
# -------------------------------------------------------------------


class TestDemo3MedicalDiagnosis:
    """Medical scenario using concept/role assertions."""

    def test_symptoms_derive_diagnosis(self):
        r = _r(
            language={
                "hasSymptom(patient,chestPain)", "hasSymptom(patient,leftRadiation)",
                "HeartAttack(patient)",
            },
            consequences={
                (frozenset({"hasSymptom(patient,chestPain)",
                            "hasSymptom(patient,leftRadiation)"}),
                 frozenset({"HeartAttack(patient)"})),
            },
            max_depth=15,
        )
        assert r.query(
            frozenset({
                "hasSymptom(patient,chestPain)",
                "hasSymptom(patient,leftRadiation)",
            }),
            frozenset({"HeartAttack(patient)"}),
        )

    def test_normal_tests_defeat(self):
        r = _r(
            language={
                "hasSymptom(patient,chestPain)", "hasSymptom(patient,leftRadiation)",
                "hasTest(patient,ecg)", "hasTest(patient,enzymes)",
                "Normal(ecg)", "Normal(enzymes)",
                "HeartAttack(patient)", "NotHeartAttack(patient)",
            },
            consequences={
                (frozenset({"hasSymptom(patient,chestPain)",
                            "hasSymptom(patient,leftRadiation)"}),
                 frozenset({"HeartAttack(patient)"})),
                (frozenset({"hasTest(patient,ecg)", "Normal(ecg)",
                            "hasTest(patient,enzymes)", "Normal(enzymes)"}),
                 frozenset({"NotHeartAttack(patient)"})),
            },
            max_depth=15,
        )
        assert not r.query(
            frozenset({
                "hasSymptom(patient,chestPain)",
                "hasSymptom(patient,leftRadiation)",
                "hasTest(patient,ecg)", "Normal(ecg)",
                "hasTest(patient,enzymes)", "Normal(enzymes)",
            }),
            frozenset({"HeartAttack(patient)"}),
        )


# -------------------------------------------------------------------
# Demo 10: RDFS Schema Evaluation (replaces anchored schemas)
# -------------------------------------------------------------------


class TestDemo10RDFSSchemas:
    """RDFS schemas with NMMSReasoner."""

    def test_subclass_schema(self):
        base = RDFSMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(
            frozenset({"Man(socrates)"}),
            frozenset({"Mortal(socrates)"}),
        )

    def test_range_schema(self):
        base = RDFSMaterialBase(language={"hasChild(alice,bob)"})
        base.register_range("hasChild", "Person")
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(
            frozenset({"hasChild(alice,bob)"}),
            frozenset({"Person(bob)"}),
        )

    def test_new_individual_no_regrounding(self):
        base = RDFSMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        base.add_atom("Man(plato)")
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(
            frozenset({"Man(plato)"}),
            frozenset({"Mortal(plato)"}),
        )

    def test_nonmonotonicity_schema(self):
        base = RDFSMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        r = NMMSReasoner(base, max_depth=15)
        assert not r.query(
            frozenset({"Man(socrates)", "Immortal(socrates)"}),
            frozenset({"Mortal(socrates)"}),
        )

    def test_nontransitivity_schema(self):
        base = RDFSMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        base.register_subclass("Mortal", "Physical")
        r = NMMSReasoner(base, max_depth=15)
        assert not r.query(
            frozenset({"Man(socrates)"}),
            frozenset({"Physical(socrates)"}),
        )

    def test_ddt_schema(self):
        base = RDFSMaterialBase(language={"Man(socrates)"})
        base.register_subclass("Man", "Mortal")
        r = NMMSReasoner(base, max_depth=15)
        assert r.query(
            frozenset(),
            frozenset({"Man(socrates) -> Mortal(socrates)"}),
        )
