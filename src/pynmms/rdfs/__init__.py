"""pyNMMS RDFS extension.

Extends propositional NMMS with defeasible RDFS-style axiom schemas
(subClassOf, range, domain, subPropertyOf) for ontology reasoning.

Public API::

    from pynmms.rdfs import RDFSMaterialBase, CommitmentStore
    from pynmms.rdfs import (
        RDFSSentence, parse_rdfs_sentence, is_rdfs_atomic, all_rdfs_atomic,
        make_concept_assertion, make_role_assertion,
    )
"""

from pynmms.rdfs.base import CommitmentStore, RDFSMaterialBase
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

__all__ = [
    "ATOM_CONCEPT",
    "ATOM_ROLE",
    "CommitmentStore",
    "RDFSMaterialBase",
    "RDFSSentence",
    "all_rdfs_atomic",
    "is_rdfs_atomic",
    "make_concept_assertion",
    "make_role_assertion",
    "parse_rdfs_sentence",
]
