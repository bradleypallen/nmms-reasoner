# Ontology Extension Tutorial

This tutorial introduces the **NMMS_Onto** ontology engineering extension of pyNMMS, which provides schema-level macros for material inferential commitments and incompatibilities within the NMMS sequent calculus. Ontology schemas (subClassOf, range, domain, subPropertyOf, disjointWith, disjointProperties) are encoded as lazy axiom schemas in the material base, evaluated at query time with exact match to preserve nonmonotonicity.

The vocabulary is borrowed from W3C RDFS and OWL for familiarity, but the semantics are those of NMMS -- exact-match defeasibility, no weakening, no transitivity. These schemas add no new reasoning capabilities; they are macros that generate ordinary base axioms.

The ontology extension lives in the `pynmms.onto` subpackage and uses the standard `NMMSReasoner` for proof search -- no special reasoner is required.

---

## 1. Building an Ontology Material Base

An `OntoMaterialBase` extends the propositional `MaterialBase` with ontology-style vocabulary tracking. Atoms in an ontology base are **ground atomic formulas**: concept assertions `C(a)` and role assertions `R(a,b)`. Bare propositional letters are not permitted.

### ABox: Concept and Role Assertions

The ABox (assertional box) is built from concept assertions and role assertions that describe particular individuals:

```python
from pynmms.onto import OntoMaterialBase

# Create a base with concept and role assertions
base = OntoMaterialBase(
    language={"Man(socrates)", "hasChild(alice,bob)"}
)

# The base automatically tracks vocabulary
print(base.individuals)  # frozenset({'socrates', 'alice', 'bob'})
print(base.concepts)     # frozenset({'Man'})
print(base.roles)        # frozenset({'hasChild'})
```

You can also add atoms incrementally:

```python
base = OntoMaterialBase()

base.add_atom("Man(socrates)")
base.add_atom("Greek(socrates)")
base.add_atom("hasChild(alice,bob)")
base.add_atom("Doctor(bob)")
```

### Base Consequences

Explicit base consequences (material inferences among atomic sentences) can be added at construction time or later:

```python
# At construction time
base = OntoMaterialBase(
    language={"Man(socrates)", "Mortal(socrates)"},
    consequences={
        (frozenset({"Man(socrates)"}), frozenset({"Mortal(socrates)"})),
    },
)

# Or incrementally
base.add_consequence(
    frozenset({"Greek(socrates)"}),
    frozenset({"Philosopher(socrates)"}),
)
```

These are exact-match axioms with no weakening -- adding extra premises will defeat the inference, which is the hallmark of nonmonotonic reasoning.

---

## 2. Adding Ontology Schemas (TBox)

The TBox (terminological box) consists of **ontology schema macros** that generate families of axiom instances via lazy evaluation. Six schema types are supported:

### subClassOf

Registers a subsumption relationship between concepts. For any individual x, `{C(x)} |~ {D(x)}`:

```python
base = OntoMaterialBase(language={"Man(socrates)"})

# Man is a subclass of Mortal
base.register_subclass("Man", "Mortal")

# This makes {Man(socrates)} |~ {Mortal(socrates)} an axiom,
# and likewise for any other individual that appears in the base.
```

### range

Registers a range constraint on a role. For any x, y, `{R(x,y)} |~ {C(y)}`:

```python
base = OntoMaterialBase(language={"hasChild(alice,bob)"})

# The range of hasChild is Person
base.register_range("hasChild", "Person")

# This makes {hasChild(alice,bob)} |~ {Person(bob)} an axiom.
# The concept is applied to the second argument (the object).
```

### domain

Registers a domain constraint on a role. For any x, y, `{R(x,y)} |~ {C(x)}`:

```python
base = OntoMaterialBase(language={"hasChild(alice,bob)"})

# The domain of hasChild is Parent
base.register_domain("hasChild", "Parent")

# This makes {hasChild(alice,bob)} |~ {Parent(alice)} an axiom.
# The concept is applied to the first argument (the subject).
```

### subPropertyOf

Registers a sub-property relationship between roles. For any x, y, `{R(x,y)} |~ {S(x,y)}`:

```python
base = OntoMaterialBase(language={"hasChild(alice,bob)"})

# hasChild is a sub-property of hasDescendant
base.register_subproperty("hasChild", "hasDescendant")

# This makes {hasChild(alice,bob)} |~ {hasDescendant(alice,bob)} an axiom.
```

### disjointWith

Registers an incompatibility between concepts. For any individual x, `{C(x), D(x)} |~ {}`:

```python
base = OntoMaterialBase(language={"Alive(socrates)", "Dead(socrates)"})

# Alive and Dead are incompatible concepts
base.register_disjoint_concepts("Alive", "Dead")

# This makes {Alive(socrates), Dead(socrates)} |~ {} an axiom.
# The empty consequent means the pair of premises is incoherent.
```

Incompatibility is foundational in Brandom's framework -- it is prior to negation, not derived from it. The `disjointWith` schema directly encodes material incompatibility between concepts.

### disjointProperties

Registers an incompatibility between roles. For any individuals x, y, `{R(x,y), S(x,y)} |~ {}`:

```python
base = OntoMaterialBase(language={"employs(alice,bob)", "isEmployedBy(alice,bob)"})

# employs and isEmployedBy are incompatible for the same pair
base.register_disjoint_properties("employs", "isEmployedBy")

# This makes {employs(alice,bob), isEmployedBy(alice,bob)} |~ {} an axiom.
```

### Annotations

All schema registration methods accept an optional `annotation` parameter for documentation:

```python
base.register_subclass("Man", "Mortal", annotation="All men are mortal")
base.register_range("hasChild", "Person", annotation="Children are persons")
base.register_disjoint_concepts("Alive", "Dead", annotation="Life and death are incompatible")
```

### Complete TBox Example

```python
from pynmms.onto import OntoMaterialBase

base = OntoMaterialBase(
    language={
        "Man(socrates)",
        "hasChild(alice,bob)",
        "Doctor(bob)",
        "Alive(socrates)",
    }
)

base.register_subclass("Man", "Mortal")
base.register_range("hasChild", "Person")
base.register_domain("hasChild", "Parent")
base.register_subproperty("hasChild", "hasDescendant")
base.register_disjoint_concepts("Alive", "Dead")
base.register_disjoint_properties("employs", "isEmployedBy")
```

### Lazy Evaluation

Schemas are **not** eagerly grounded over all known individuals. Instead, they are checked lazily during axiom evaluation: when the reasoner encounters a candidate sequent `{C(a)} => {D(a)}`, it tests whether any registered schema matches. This avoids combinatorial blowup and preserves the exact-match semantics needed for nonmonotonicity.

---

## 3. Querying with NMMSReasoner

The standard `NMMSReasoner` works transparently with `OntoMaterialBase` because ontology schemas are evaluated at the axiom level (via the overridden `is_axiom` method). No special reasoner class is needed.

```python
from pynmms.onto import OntoMaterialBase
from pynmms.reasoner import NMMSReasoner

# Build the base
base = OntoMaterialBase(language={"Man(socrates)"})
base.register_subclass("Man", "Mortal")

# Create a standard reasoner
r = NMMSReasoner(base, max_depth=15)

# Query: Man(socrates) => Mortal(socrates)?
result = r.derives(
    frozenset({"Man(socrates)"}),
    frozenset({"Mortal(socrates)"})
)
print(result.derivable)  # True

# Convenience method
print(r.query(
    frozenset({"Man(socrates)"}),
    frozenset({"Mortal(socrates)"})
))  # True
```

### Range and Domain Queries

```python
base = OntoMaterialBase(language={"hasChild(alice,bob)"})
base.register_range("hasChild", "Person")
base.register_domain("hasChild", "Parent")

r = NMMSReasoner(base, max_depth=15)

# Range: hasChild(alice,bob) => Person(bob)?
print(r.query(
    frozenset({"hasChild(alice,bob)"}),
    frozenset({"Person(bob)"})
))  # True

# Domain: hasChild(alice,bob) => Parent(alice)?
print(r.query(
    frozenset({"hasChild(alice,bob)"}),
    frozenset({"Parent(alice)"})
))  # True
```

### SubProperty Queries

```python
base = OntoMaterialBase(language={"hasChild(alice,bob)"})
base.register_subproperty("hasChild", "hasDescendant")

r = NMMSReasoner(base, max_depth=15)

# hasChild(alice,bob) => hasDescendant(alice,bob)?
print(r.query(
    frozenset({"hasChild(alice,bob)"}),
    frozenset({"hasDescendant(alice,bob)"})
))  # True
```

### Incompatibility Queries

```python
base = OntoMaterialBase(language={"Alive(socrates)", "Dead(socrates)"})
base.register_disjoint_concepts("Alive", "Dead")

r = NMMSReasoner(base, max_depth=15)

# Incompatibility: Alive(socrates), Dead(socrates) => {} (empty consequent)?
print(r.query(
    frozenset({"Alive(socrates)", "Dead(socrates)"}),
    frozenset()
))  # True

# With extra premise, the incompatibility is defeated
print(r.query(
    frozenset({"Alive(socrates)", "Dead(socrates)", "Zombie(socrates)"}),
    frozenset()
))  # False
```

### Proof Traces

The `derives` method returns a `ProofResult` with a human-readable trace:

```python
result = r.derives(
    frozenset({"Man(socrates)"}),
    frozenset({"Mortal(socrates)"})
)
for line in result.trace:
    print(line)
# AXIOM: Man(socrates) => Mortal(socrates)
```

---

## 4. Defeasibility

Because NMMS omits the structural rule of Weakening, ontology inferences are **defeasible**: adding extra premises can defeat an otherwise good inference.

```python
from pynmms.onto import OntoMaterialBase
from pynmms.reasoner import NMMSReasoner

base = OntoMaterialBase(language={"Man(socrates)"})
base.register_subclass("Man", "Mortal")

r = NMMSReasoner(base, max_depth=15)

# The basic inference holds
print(r.query(
    frozenset({"Man(socrates)"}),
    frozenset({"Mortal(socrates)"})
))  # True

# Adding an extra premise defeats it -- nonmonotonicity!
print(r.query(
    frozenset({"Man(socrates)", "Divine(socrates)"}),
    frozenset({"Mortal(socrates)"})
))  # False
```

The schema `{Man(x)} |~ {Mortal(x)}` is an exact-match axiom: it requires the antecedent to be exactly `{Man(socrates)}` and the consequent to be exactly `{Mortal(socrates)}`. The sequent `{Man(socrates), Divine(socrates)} => {Mortal(socrates)}` has an extra premise `Divine(socrates)`, so the schema does not fire. Without Weakening, there is no way to derive the strengthened sequent from the weaker one.

This models a natural reasoning pattern: we normally infer that Socrates is mortal from his being a man, but learning that he is divine defeats that inference. In NMMS, the defeat is structural -- it follows from the absence of Weakening, not from any explicit exception mechanism.

### Range Defeasibility

The same holds for range, domain, subPropertyOf, disjointWith, and disjointProperties schemas:

```python
base = OntoMaterialBase(language={"hasChild(alice,bob)"})
base.register_range("hasChild", "Person")

r = NMMSReasoner(base, max_depth=15)

# Range inference holds
print(r.query(
    frozenset({"hasChild(alice,bob)"}),
    frozenset({"Person(bob)"})
))  # True

# Extra premise defeats it
print(r.query(
    frozenset({"hasChild(alice,bob)", "Robot(bob)"}),
    frozenset({"Person(bob)"})
))  # False
```

---

## 5. Non-transitivity

NMMS also omits the structural rule of Mixed-Cut (Transitivity). This means that chaining individually good inferences can yield a bad inference -- subClassOf chains do **not** automatically propagate.

```python
from pynmms.onto import OntoMaterialBase
from pynmms.reasoner import NMMSReasoner

base = OntoMaterialBase(language={"Man(socrates)"})
base.register_subclass("Man", "Mortal")
base.register_subclass("Mortal", "Perishable")

r = NMMSReasoner(base, max_depth=15)

# Each step holds individually
print(r.query(
    frozenset({"Man(socrates)"}),
    frozenset({"Mortal(socrates)"})
))  # True

print(r.query(
    frozenset({"Mortal(socrates)"}),
    frozenset({"Perishable(socrates)"})
))  # True

# But the chain does NOT propagate
print(r.query(
    frozenset({"Man(socrates)"}),
    frozenset({"Perishable(socrates)"})
))  # False
```

The sequent `{Man(socrates)} => {Perishable(socrates)}` is not derivable because:

1. The subClassOf schema for Man/Mortal only fires on `{Man(x)} |~ {Mortal(x)}`.
2. The subClassOf schema for Mortal/Perishable only fires on `{Mortal(x)} |~ {Perishable(x)}`.
3. There is no Mixed-Cut rule to chain these two axioms.

This is a feature, not a bug. In open reason relations, transitivity failure models situations where each inference step is individually good but their composition is not -- for example, "penguins are birds" and "birds fly" are individually good inferences, but "penguins fly" is not.

If you **want** the transitive closure, you must explicitly add the composed consequence:

```python
base.add_consequence(
    frozenset({"Man(socrates)"}),
    frozenset({"Perishable(socrates)"})
)

# Now the chain holds (as an explicit base consequence)
print(r.query(
    frozenset({"Man(socrates)"}),
    frozenset({"Perishable(socrates)"})
))  # True
```

---

## 6. Deduction-Detachment Theorem (DDT)

The DDT is a fundamental property of NMMS: a conditional `A -> B` is derivable on the right exactly when `B` is derivable from `A`. More precisely:

> Gamma |~ A -> B, Delta &nbsp;&nbsp;iff&nbsp;&nbsp; Gamma, A |~ B, Delta

This means ontology schema consequences can be expressed in conditional form. If `{Man(socrates)} |~ {Mortal(socrates)}` is an axiom, then the conditional `Man(socrates) -> Mortal(socrates)` is derivable as a theorem:

```python
from pynmms.onto import OntoMaterialBase
from pynmms.reasoner import NMMSReasoner

base = OntoMaterialBase(language={"Man(socrates)"})
base.register_subclass("Man", "Mortal")

r = NMMSReasoner(base, max_depth=15)

# The material inference holds
print(r.query(
    frozenset({"Man(socrates)"}),
    frozenset({"Mortal(socrates)"})
))  # True

# So the conditional form is derivable (DDT, left-to-right)
print(r.query(
    frozenset(),
    frozenset({"Man(socrates) -> Mortal(socrates)"})
))  # True
```

The proof works via the [R->] rule:

```
  To derive: {} => {Man(socrates) -> Mortal(socrates)}
  Apply [R->]: need {Man(socrates)} => {Mortal(socrates)}
  This is an axiom (subClassOf schema).
```

DDT also interacts with defeasibility. Since the conditional form is a theorem (derivable from the empty antecedent), it holds without any premises. But the material inference `{Man(socrates)} |~ {Mortal(socrates)}` is defeasible -- adding extra premises defeats it. The conditional "makes explicit" the defeasible reason relation by encoding it as a logical constant that can appear in further inferences.

---

## 7. Using CommitmentStore

The `CommitmentStore` provides a higher-level API for managing ontology assertions and schemas. It accumulates commitments and compiles them into an `OntoMaterialBase` on demand. Each schema commitment includes a `source` string for provenance tracking and selective retraction.

### Building Commitments

```python
from pynmms.onto import OntoMaterialBase, CommitmentStore
from pynmms.reasoner import NMMSReasoner

store = CommitmentStore()

# Add ABox assertions
store.add_concept("Man", "socrates")
store.add_concept("Greek", "socrates")
store.add_role("hasChild", "alice", "bob")
store.add_concept("Doctor", "bob")

# Add TBox schemas with source attribution
store.commit_subclass("ontology-v1", "Man", "Mortal")
store.commit_range("ontology-v1", "hasChild", "Person")
store.commit_domain("ontology-v1", "hasChild", "Parent")
store.commit_subproperty("ontology-v1", "hasChild", "hasDescendant")
store.commit_disjoint_concepts("ontology-v1", "Alive", "Dead")
store.commit_disjoint_properties("ontology-v1", "employs", "isEmployedBy")

# Compile to a base and query
base = store.compile()
r = NMMSReasoner(base, max_depth=15)

print(r.query(
    frozenset({"Man(socrates)"}),
    frozenset({"Mortal(socrates)"})
))  # True

print(r.query(
    frozenset({"hasChild(alice,bob)"}),
    frozenset({"Person(bob)"})
))  # True
```

### Describing Commitments

The `describe()` method provides a human-readable summary:

```python
print(store.describe())
# Commitment Store:
#   Assertions: 4
#     Doctor(bob)
#     Greek(socrates)
#     Man(socrates)
#     hasChild(alice,bob)
#   Ontology Schemas: 6
#     [ontology-v1] subClassOf: Man(x) |~ Mortal(x)
#     [ontology-v1] range: hasChild(x,y) |~ Person(y)
#     [ontology-v1] domain: hasChild(x,y) |~ Parent(x)
#     [ontology-v1] subPropertyOf: hasChild(x,y) |~ hasDescendant(x,y)
#     [ontology-v1] disjointWith: Alive(x), Dead(x) |~
#     [ontology-v1] disjointProperties: employs(x,y), isEmployedBy(x,y) |~
```

### Adding Ground Defeasible Rules

Beyond ontology schemas, the `CommitmentStore` supports arbitrary ground defeasible rules:

```python
store.commit_defeasible_rule(
    "domain-expert",
    frozenset({"Doctor(bob)"}),
    frozenset({"Educated(bob)"}),
)

base = store.compile()
r = NMMSReasoner(base, max_depth=15)

print(r.query(
    frozenset({"Doctor(bob)"}),
    frozenset({"Educated(bob)"})
))  # True
```

### Retracting Schemas

Schemas can be retracted by source:

```python
store.retract_schema("ontology-v1")

base = store.compile()
r = NMMSReasoner(base, max_depth=15)

# The subClassOf schema no longer fires
print(r.query(
    frozenset({"Man(socrates)"}),
    frozenset({"Mortal(socrates)"})
))  # False
```

### Caching

The `compile()` method caches the result. Any mutation (adding assertions, committing schemas, retracting) invalidates the cache so the next `compile()` call rebuilds the base.

---

## 8. CLI Usage with `--onto`

The `--onto` flag on the `tell`, `ask`, and `repl` subcommands activates ontology mode. In this mode, atoms must be concept assertions `C(a)` or role assertions `R(a,b)`.

### `pynmms tell --onto`

```bash
# Create a new ontology base with an atom
pynmms tell -b onto_base.json --create --onto "atom Man(socrates)"

# Add more atoms
pynmms tell -b onto_base.json --onto "atom hasChild(alice,bob)"
pynmms tell -b onto_base.json --onto "atom Doctor(bob)"

# Add atoms with annotations
pynmms tell -b onto_base.json --onto 'atom Man(socrates) "Socrates is a man"'

# Add a base consequence
pynmms tell -b onto_base.json --onto "Man(socrates) |~ Greek(socrates)"

# Add incompatibility (empty consequent)
pynmms tell -b onto_base.json --onto "Alive(socrates), Dead(socrates) |~"

# Add theorem (empty antecedent)
pynmms tell -b onto_base.json --onto "|~ Exists(socrates)"
```

### `pynmms ask --onto`

```bash
# Query derivability
pynmms ask -b onto_base.json --onto "Man(socrates) => Greek(socrates)"
# Output: DERIVABLE

# JSON output
pynmms ask -b onto_base.json --onto --json "Man(socrates) => Greek(socrates)"

# Quiet mode (exit code only)
pynmms ask -b onto_base.json --onto -q "Man(socrates) => Greek(socrates)"
echo $?  # 0 = derivable, 2 = not derivable

# Proof trace
pynmms ask -b onto_base.json --onto --trace "Man(socrates) => Greek(socrates)"
```

### `pynmms repl --onto`

```bash
pynmms repl --onto
pynmms repl --onto -b onto_base.json
```

### Batch Mode

Batch files support `schema` lines in ontology mode:

```
# onto_base.txt
atom Man(socrates) "Socrates is a man"
atom hasChild(alice,bob)
atom Doctor(bob)
Man(socrates) |~ Greek(socrates)
schema subClassOf Man Mortal
schema range hasChild Person
schema domain hasChild Parent
schema subPropertyOf hasChild hasDescendant
schema disjointWith Alive Dead
schema disjointProperties employs isEmployedBy
```

```bash
pynmms tell -b onto_base.json --create --onto --batch onto_base.txt
```

Query batch:

```
# queries.txt
Man(socrates) => Mortal(socrates)
hasChild(alice,bob) => Person(bob)
hasChild(alice,bob) => Parent(alice)
hasChild(alice,bob) => hasDescendant(alice,bob)
Man(socrates) => Perishable(socrates)
```

```bash
pynmms ask -b onto_base.json --onto --batch queries.txt
```

---

## 9. REPL Commands

The ontology REPL (activated with `pynmms repl --onto`) provides all the standard REPL commands plus ontology-specific commands for managing schemas and inspecting vocabulary.

### Schema Commands

| Command | Description |
|---------|-------------|
| `tell schema subClassOf C D` | Register subClassOf: {C(x)} \|~ {D(x)} |
| `tell schema range R C` | Register range: {R(x,y)} \|~ {C(y)} |
| `tell schema domain R C` | Register domain: {R(x,y)} \|~ {C(x)} |
| `tell schema subPropertyOf R S` | Register subPropertyOf: {R(x,y)} \|~ {S(x,y)} |
| `tell schema disjointWith C D` | Register disjointWith: {C(x), D(x)} \|~ {} |
| `tell schema disjointProperties R S` | Register disjointProperties: {R(x,y), S(x,y)} \|~ {} |

### Inspection Commands

| Command | Description |
|---------|-------------|
| `show` | Display atoms, annotations, and consequences |
| `show schemas` | Display all registered ontology schemas |
| `show individuals` | Display known individuals, concepts, and roles |

### Complete Command Reference

| Command | Description |
|---------|-------------|
| `tell A \|~ B` | Add a consequence to the base |
| `tell A, B \|~` | Add incompatibility (empty consequent) |
| `tell \|~ A` | Add theorem (empty antecedent) |
| `tell atom C(a)` | Add a concept assertion |
| `tell atom R(a,b)` | Add a role assertion |
| `tell atom C(a) "desc"` | Add an atom with annotation |
| `tell schema subClassOf C D` | Register subClassOf schema |
| `tell schema range R C` | Register range schema |
| `tell schema domain R C` | Register domain schema |
| `tell schema subPropertyOf R S` | Register subPropertyOf schema |
| `tell schema disjointWith C D` | Register disjointWith schema |
| `tell schema disjointProperties R S` | Register disjointProperties schema |
| `ask A => B` | Query derivability |
| `show` | Display the current base |
| `show schemas` | Display registered schemas |
| `show individuals` | Display vocabulary (individuals, concepts, roles) |
| `trace on/off` | Toggle proof trace display |
| `save <file>` | Save base to JSON |
| `load <file>` | Load base from JSON |
| `help` | Show available commands |
| `quit` | Exit the REPL |

### Example REPL Session

```
$ pynmms repl --onto
Starting with empty ontology base.
pyNMMS REPL (ontology mode). Type 'help' for commands.

pynmms[onto]> tell atom Man(socrates) "Socrates is a man"
Added atom: Man(socrates) -- Socrates is a man

pynmms[onto]> tell atom hasChild(alice,bob)
Added atom: hasChild(alice,bob)

pynmms[onto]> tell schema subClassOf Man Mortal
Registered subClassOf schema: {Man(x)} |~ {Mortal(x)}

pynmms[onto]> tell schema range hasChild Person
Registered range schema: {hasChild(x,y)} |~ {Person(y)}

pynmms[onto]> tell schema domain hasChild Parent
Registered domain schema: {hasChild(x,y)} |~ {Parent(x)}

pynmms[onto]> tell schema subPropertyOf hasChild hasDescendant
Registered subPropertyOf schema: {hasChild(x,y)} |~ {hasDescendant(x,y)}

pynmms[onto]> tell schema disjointWith Alive Dead
Registered disjointWith schema: {Alive(x), Dead(x)} |~ {}

pynmms[onto]> tell schema disjointProperties employs isEmployedBy
Registered disjointProperties schema: {employs(x,y), isEmployedBy(x,y)} |~ {}

pynmms[onto]> show schemas
Schemas (6):
  subClassOf: {Man(x)} |~ {Mortal(x)}
  range: {hasChild(x,y)} |~ {Person(y)}
  domain: {hasChild(x,y)} |~ {Parent(x)}
  subPropertyOf: {hasChild(x,y)} |~ {hasDescendant(x,y)}
  disjointWith: {Alive(x), Dead(x)} |~ {}
  disjointProperties: {employs(x,y), isEmployedBy(x,y)} |~ {}

pynmms[onto]> show individuals
Individuals: ['alice', 'bob', 'socrates']
Concepts: ['Man']
Roles: ['hasChild']

pynmms[onto]> ask Man(socrates) => Mortal(socrates)
DERIVABLE

pynmms[onto]> ask hasChild(alice,bob) => Person(bob)
DERIVABLE

pynmms[onto]> ask hasChild(alice,bob) => Parent(alice)
DERIVABLE

pynmms[onto]> ask hasChild(alice,bob) => hasDescendant(alice,bob)
DERIVABLE

pynmms[onto]> ask Man(socrates), Divine(socrates) => Mortal(socrates)
NOT DERIVABLE

pynmms[onto]> trace on
Trace: ON

pynmms[onto]> ask Man(socrates) => Mortal(socrates)
DERIVABLE
  AXIOM: Man(socrates) => Mortal(socrates)
  Depth: 0, Cache hits: 0

pynmms[onto]> save my_onto_base.json
Saved to my_onto_base.json

pynmms[onto]> quit
```

---

## Summary

The ontology extension provides schema-level macros for material inferential commitments and incompatibilities within the NMMS framework:

| Feature | Mechanism |
|---------|-----------|
| **ABox assertions** | Concept `C(a)` and role `R(a,b)` atoms in the material base |
| **TBox schemas** | `register_subclass`, `register_range`, `register_domain`, `register_subproperty`, `register_disjoint_concepts`, `register_disjoint_properties` |
| **Lazy evaluation** | Schemas checked at query time, not eagerly grounded |
| **Exact match** | No weakening -- preserves defeasibility |
| **Standard reasoner** | `NMMSReasoner` works transparently with `OntoMaterialBase` |
| **Defeasibility** | Extra premises defeat ontology inferences (no Weakening) |
| **Non-transitivity** | SubClassOf chains do not propagate (no Mixed-Cut) |
| **Incompatibility** | `disjointWith` and `disjointProperties` encode material incompatibility directly |
| **DDT** | Conditional form `A -> B` derivable when material inference holds |
| **CommitmentStore** | Higher-level API with source tracking and retraction |
| **CLI** | `--onto` flag on `tell`, `ask`, `repl` |
