"""RDFS Material Base -- defeasible RDFS axiom schemas for NMMS.

Extends the propositional ``MaterialBase`` with RDFS-style vocabulary
tracking (individuals, concepts, roles) and four defeasible axiom schema
types: subClassOf, range, domain, subPropertyOf.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pynmms.base import MaterialBase, Sequent
from pynmms.rdfs.syntax import (
    ATOM_CONCEPT,
    ATOM_ROLE,
    RDFSSentence,
    is_rdfs_atomic,
    make_concept_assertion,
    make_role_assertion,
    parse_rdfs_sentence,
)

logger = logging.getLogger(__name__)


def _validate_rdfs_atomic(s: str, context: str) -> None:
    """Raise ValueError if *s* is not an RDFS-atomic sentence."""
    if not is_rdfs_atomic(s):
        raise ValueError(
            f"{context}: '{s}' is not valid in NMMS_RDFS. "
            f"Only concept assertions C(a) and role assertions R(a,b) "
            f"are permitted in the RDFS material base."
        )


class RDFSMaterialBase(MaterialBase):
    """A material base for NMMS with defeasible RDFS axiom schemas.

    Extends ``MaterialBase`` to accept concept/role assertions as atomic,
    track vocabulary (individuals, concepts, roles), and support four
    RDFS axiom schema types: subClassOf, range, domain, subPropertyOf.

    Schemas are evaluated lazily at query time -- not grounded over known
    individuals. All use exact match (no weakening) to preserve
    nonmonotonicity.
    """

    def __init__(
        self,
        language: set[str] | frozenset[str] | None = None,
        consequences: (
            set[Sequent] | set[tuple[frozenset[str], frozenset[str]]] | None
        ) = None,
        annotations: dict[str, str] | None = None,
    ) -> None:
        self._individuals: set[str] = set()
        self._concepts: set[str] = set()
        self._roles: set[str] = set()
        self._rdfs_schemas: list[tuple[str, str, str, str | None]] = []
        # Temporarily bypass parent validation -- we override _validate
        self._rdfs_language: set[str] = set(language) if language else set()
        self._rdfs_consequences: set[Sequent] = set()

        # Validate RDFS-atomic
        for s in self._rdfs_language:
            _validate_rdfs_atomic(s, "RDFS material base language")
            self._extract_vocab(s)

        if consequences:
            for gamma, delta in consequences:
                for s in gamma | delta:
                    _validate_rdfs_atomic(s, "RDFS material base consequence")
                    self._extract_vocab(s)
                self._rdfs_consequences.add((gamma, delta))

        # Initialize parent with empty sets -- we manage storage ourselves
        super().__init__(annotations=annotations)
        self._language = self._rdfs_language
        self._consequences = self._rdfs_consequences

        logger.debug(
            "RDFSMaterialBase created: %d atoms, %d consequences, "
            "%d individuals, %d concepts, %d roles",
            len(self._language),
            len(self._consequences),
            len(self._individuals),
            len(self._concepts),
            len(self._roles),
        )

    def _extract_vocab(self, s: str) -> None:
        """Extract vocabulary (individuals, concepts, roles) from a sentence."""
        parsed = parse_rdfs_sentence(s)
        if isinstance(parsed, RDFSSentence):
            if parsed.type == ATOM_CONCEPT:
                self._individuals.add(parsed.individual)  # type: ignore[arg-type]
                self._concepts.add(parsed.concept)  # type: ignore[arg-type]
            elif parsed.type == ATOM_ROLE:
                self._individuals.add(parsed.arg1)  # type: ignore[arg-type]
                self._individuals.add(parsed.arg2)  # type: ignore[arg-type]
                self._roles.add(parsed.role)  # type: ignore[arg-type]

    # --- Read-only properties ---

    @property
    def individuals(self) -> frozenset[str]:
        """Known individuals (read-only)."""
        return frozenset(self._individuals)

    @property
    def concepts(self) -> frozenset[str]:
        """Known concepts (read-only)."""
        return frozenset(self._concepts)

    @property
    def roles(self) -> frozenset[str]:
        """Known roles (read-only)."""
        return frozenset(self._roles)

    @property
    def rdfs_schemas(self) -> list[tuple[str, str, str, str | None]]:
        """RDFS schemas (read-only copy)."""
        return list(self._rdfs_schemas)

    # --- Mutation ---

    def add_atom(self, s: str) -> None:
        """Add an RDFS-atomic sentence to the language."""
        _validate_rdfs_atomic(s, "add_atom")
        self._language.add(s)
        self._extract_vocab(s)
        logger.debug("Added atom: %s", s)

    def add_consequence(
        self, antecedent: frozenset[str], consequent: frozenset[str]
    ) -> None:
        """Add a base consequence. All sentences must be RDFS-atomic."""
        for s in antecedent | consequent:
            _validate_rdfs_atomic(s, "add_consequence")
            self._language.add(s)
            self._extract_vocab(s)
        self._consequences.add((antecedent, consequent))
        logger.debug("Added consequence: %s |~ %s", set(antecedent), set(consequent))

    def add_individual(self, role: str, subject: str, obj: str) -> None:
        """Add a role assertion R(subject, obj) to the language."""
        role_assertion = make_role_assertion(role, subject, obj)
        self._language.add(role_assertion)
        self._extract_vocab(role_assertion)
        logger.debug("Added individual: %s", role_assertion)

    # --- RDFS schema registration ---

    def register_subclass(
        self,
        sub_concept: str,
        super_concept: str,
        annotation: str | None = None,
    ) -> None:
        """Register subClassOf schema: {sub(x)} |~ {super(x)} for any x.

        Stored lazily -- not grounded over known individuals.
        """
        self._rdfs_schemas.append(("subClassOf", sub_concept, super_concept, annotation))
        logger.debug(
            "Registered subClassOf schema: %s ⊑ %s", sub_concept, super_concept
        )

    def register_range(
        self,
        role: str,
        concept: str,
        annotation: str | None = None,
    ) -> None:
        """Register range schema: {R(x,y)} |~ {C(y)} for any x, y.

        Stored lazily -- not grounded over known individuals.
        """
        self._rdfs_schemas.append(("range", role, concept, annotation))
        logger.debug("Registered range schema: range(%s) = %s", role, concept)

    def register_domain(
        self,
        role: str,
        concept: str,
        annotation: str | None = None,
    ) -> None:
        """Register domain schema: {R(x,y)} |~ {C(x)} for any x, y.

        Stored lazily -- not grounded over known individuals.
        """
        self._rdfs_schemas.append(("domain", role, concept, annotation))
        logger.debug("Registered domain schema: domain(%s) = %s", role, concept)

    def register_subproperty(
        self,
        sub_role: str,
        super_role: str,
        annotation: str | None = None,
    ) -> None:
        """Register subPropertyOf schema: {R(x,y)} |~ {S(x,y)} for any x, y.

        Stored lazily -- not grounded over known individuals.
        """
        self._rdfs_schemas.append(("subPropertyOf", sub_role, super_role, annotation))
        logger.debug(
            "Registered subPropertyOf schema: %s ⊑ %s", sub_role, super_role
        )

    # --- Axiom check (overrides parent) ---

    def is_axiom(self, gamma: frozenset[str], delta: frozenset[str]) -> bool:
        """Check if Gamma => Delta is an axiom.

        Ax1 (Containment): Gamma & Delta != empty.
        Ax2 (Base consequence): (Gamma, Delta) in |~_B exactly.
        Ax3 (RDFS schema consequence): matches a lazy RDFS schema.
        """
        # Ax1: Containment
        if gamma & delta:
            return True
        # Ax2: Explicit base consequence (exact match)
        if (gamma, delta) in self._consequences:
            return True
        # Ax3: RDFS schema evaluation
        if self._rdfs_schemas and self._check_rdfs_schemas(gamma, delta):
            return True
        return False

    def _check_rdfs_schemas(
        self, gamma: frozenset[str], delta: frozenset[str]
    ) -> bool:
        """Check if any RDFS schema makes gamma |~ delta hold.

        Exact match (no weakening) preserves nonmonotonicity.
        Each schema requires len(gamma) == 1 and len(delta) == 1.
        """
        if len(gamma) != 1 or len(delta) != 1:
            return False

        gamma_str = next(iter(gamma))
        delta_str = next(iter(delta))

        try:
            gamma_parsed = parse_rdfs_sentence(gamma_str)
            delta_parsed = parse_rdfs_sentence(delta_str)
        except ValueError:
            return False

        if not isinstance(gamma_parsed, RDFSSentence) or not isinstance(
            delta_parsed, RDFSSentence
        ):
            return False

        for schema_type, arg1, arg2, _annotation in self._rdfs_schemas:
            if schema_type == "subClassOf":
                # {C(x)} |~ {D(x)} -- same individual
                if (
                    gamma_parsed.type == ATOM_CONCEPT
                    and delta_parsed.type == ATOM_CONCEPT
                    and gamma_parsed.concept == arg1
                    and delta_parsed.concept == arg2
                    and gamma_parsed.individual == delta_parsed.individual
                ):
                    return True

            elif schema_type == "range":
                # {R(x,y)} |~ {C(y)} -- role.arg2 == concept.individual
                if (
                    gamma_parsed.type == ATOM_ROLE
                    and delta_parsed.type == ATOM_CONCEPT
                    and gamma_parsed.role == arg1
                    and delta_parsed.concept == arg2
                    and gamma_parsed.arg2 == delta_parsed.individual
                ):
                    return True

            elif schema_type == "domain":
                # {R(x,y)} |~ {C(x)} -- role.arg1 == concept.individual
                if (
                    gamma_parsed.type == ATOM_ROLE
                    and delta_parsed.type == ATOM_CONCEPT
                    and gamma_parsed.role == arg1
                    and delta_parsed.concept == arg2
                    and gamma_parsed.arg1 == delta_parsed.individual
                ):
                    return True

            elif schema_type == "subPropertyOf":
                # {R(x,y)} |~ {S(x,y)} -- same arg1, same arg2
                if (
                    gamma_parsed.type == ATOM_ROLE
                    and delta_parsed.type == ATOM_ROLE
                    and gamma_parsed.role == arg1
                    and delta_parsed.role == arg2
                    and gamma_parsed.arg1 == delta_parsed.arg1
                    and gamma_parsed.arg2 == delta_parsed.arg2
                ):
                    return True

        return False

    # --- Serialization ---

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict, including RDFS schemas."""
        base_dict = super().to_dict()
        base_dict["individuals"] = sorted(self._individuals)
        base_dict["concepts"] = sorted(self._concepts)
        base_dict["roles"] = sorted(self._roles)
        base_dict["rdfs_schemas"] = [
            {
                "type": schema_type,
                "arg1": arg1,
                "arg2": arg2,
                **({"annotation": annotation} if annotation else {}),
            }
            for schema_type, arg1, arg2, annotation in self._rdfs_schemas
        ]
        return base_dict

    @classmethod
    def from_dict(cls, data: dict) -> RDFSMaterialBase:
        """Deserialize from a dict (as produced by ``to_dict``)."""
        language = set(data.get("language", []))
        consequences: set[Sequent] = set()
        for entry in data.get("consequences", []):
            gamma = frozenset(entry["antecedent"])
            delta = frozenset(entry["consequent"])
            consequences.add((gamma, delta))
        annotations = data.get("annotations", {})

        base = cls(language=language, consequences=consequences, annotations=annotations)

        # Restore RDFS schemas
        for schema in data.get("rdfs_schemas", []):
            base._rdfs_schemas.append((
                schema["type"],
                schema["arg1"],
                schema["arg2"],
                schema.get("annotation"),
            ))

        return base

    def to_file(self, path: str | Path) -> None:
        """Write the base to a JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.debug("Saved RDFS base to %s", path)

    @classmethod
    def from_file(cls, path: str | Path) -> RDFSMaterialBase:
        """Load a base from a JSON file."""
        with open(path) as f:
            data = json.load(f)
        logger.debug("Loaded RDFS base from %s", path)
        return cls.from_dict(data)


class CommitmentStore:
    """Manages RDFS commitments and compiles them to an RDFSMaterialBase.

    Higher-level API for managing assertions and RDFS schemas, bridging
    natural language commitments to the atomic material base.
    """

    def __init__(self) -> None:
        self.assertions: set[str] = set()
        self._rdfs_commitments: list[tuple[str, str, str, str]] = []
        self._ground_rules: set[Sequent] = set()
        self._base: RDFSMaterialBase | None = None

    def add_assertion(self, s: str) -> None:
        """Add an atomic assertion."""
        _validate_rdfs_atomic(s, "CommitmentStore.add_assertion")
        self.assertions.add(s)
        self._base = None

    def add_role(self, role: str, subject: str, obj: str) -> None:
        """Add a role assertion R(subject, obj)."""
        self.add_assertion(make_role_assertion(role, subject, obj))

    def add_concept(self, concept: str, individual: str) -> None:
        """Add a concept assertion C(individual)."""
        self.add_assertion(make_concept_assertion(concept, individual))

    def commit_subclass(
        self,
        source: str,
        sub_concept: str,
        super_concept: str,
    ) -> None:
        """Record a subClassOf commitment: {sub(x)} |~ {super(x)}."""
        self._rdfs_commitments.append((source, "subClassOf", sub_concept, super_concept))
        self._base = None

    def commit_range(
        self,
        source: str,
        role: str,
        concept: str,
    ) -> None:
        """Record a range commitment: {R(x,y)} |~ {C(y)}."""
        self._rdfs_commitments.append((source, "range", role, concept))
        self._base = None

    def commit_domain(
        self,
        source: str,
        role: str,
        concept: str,
    ) -> None:
        """Record a domain commitment: {R(x,y)} |~ {C(x)}."""
        self._rdfs_commitments.append((source, "domain", role, concept))
        self._base = None

    def commit_subproperty(
        self,
        source: str,
        sub_role: str,
        super_role: str,
    ) -> None:
        """Record a subPropertyOf commitment: {R(x,y)} |~ {S(x,y)}."""
        self._rdfs_commitments.append((source, "subPropertyOf", sub_role, super_role))
        self._base = None

    def commit_defeasible_rule(
        self,
        source: str,
        antecedent: frozenset[str],
        consequent: frozenset[str],
    ) -> None:
        """Record a ground defeasible material inference."""
        for s in antecedent | consequent:
            _validate_rdfs_atomic(s, f"commit_defeasible_rule ({source})")
            self.assertions.add(s)
        self._ground_rules.add((antecedent, consequent))
        self._base = None

    def retract_schema(self, source: str) -> None:
        """Retract all schemas with the given source."""
        self._rdfs_commitments = [
            c for c in self._rdfs_commitments if c[0] != source
        ]
        self._base = None

    def compile(self) -> RDFSMaterialBase:
        """Compile current commitments into an RDFSMaterialBase.

        Schemas are registered lazily -- no eager grounding.
        """
        if self._base is not None:
            return self._base

        language = set(self.assertions)
        consequences: set[Sequent] = set(self._ground_rules)

        self._base = RDFSMaterialBase(
            language=language,
            consequences=consequences,
        )

        # Register RDFS schemas lazily
        for _source, schema_type, arg1, arg2 in self._rdfs_commitments:
            if schema_type == "subClassOf":
                self._base.register_subclass(arg1, arg2)
            elif schema_type == "range":
                self._base.register_range(arg1, arg2)
            elif schema_type == "domain":
                self._base.register_domain(arg1, arg2)
            elif schema_type == "subPropertyOf":
                self._base.register_subproperty(arg1, arg2)

        return self._base

    def describe(self) -> str:
        """Human-readable description of current commitments."""
        lines = ["Commitment Store:"]
        lines.append(f"  Assertions: {len(self.assertions)}")
        for s in sorted(self.assertions):
            lines.append(f"    {s}")
        lines.append(f"  RDFS Schemas: {len(self._rdfs_commitments)}")
        for source, schema_type, arg1, arg2 in self._rdfs_commitments:
            if schema_type == "subClassOf":
                pattern = f"{arg1}(x) |~ {arg2}(x)"
            elif schema_type == "range":
                pattern = f"{arg1}(x,y) |~ {arg2}(y)"
            elif schema_type == "domain":
                pattern = f"{arg1}(x,y) |~ {arg2}(x)"
            elif schema_type == "subPropertyOf":
                pattern = f"{arg1}(x,y) |~ {arg2}(x,y)"
            else:
                pattern = f"{arg1} -> {arg2}"  # pragma: no cover
            lines.append(f"    [{source}] {schema_type}: {pattern}")
        if self._ground_rules:
            lines.append(f"  Ground rules: {len(self._ground_rules)}")
            for ant, con in self._ground_rules:
                lines.append(f"    {set(ant)} |~ {set(con)}")
        return "\n".join(lines)
