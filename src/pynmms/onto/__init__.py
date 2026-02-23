"""pyNMMS Ontology extension.

Extends propositional NMMS with ontology-style axiom schemas
(subClassOf, range, domain, subPropertyOf, disjointWith,
disjointProperties) for ontology reasoning.

Public API::

    from pynmms.onto import OntoMaterialBase, CommitmentStore
    from pynmms.onto import (
        OntoSentence, parse_onto_sentence, is_onto_atomic, all_onto_atomic,
        make_concept_assertion, make_role_assertion,
    )
"""

from pynmms.onto.base import CommitmentStore, OntoMaterialBase
from pynmms.onto.syntax import (
    ATOM_CONCEPT,
    ATOM_ROLE,
    OntoSentence,
    all_onto_atomic,
    is_onto_atomic,
    make_concept_assertion,
    make_role_assertion,
    parse_onto_sentence,
)

__all__ = [
    "ATOM_CONCEPT",
    "ATOM_ROLE",
    "CommitmentStore",
    "OntoMaterialBase",
    "OntoSentence",
    "all_onto_atomic",
    "is_onto_atomic",
    "make_concept_assertion",
    "make_role_assertion",
    "parse_onto_sentence",
]
