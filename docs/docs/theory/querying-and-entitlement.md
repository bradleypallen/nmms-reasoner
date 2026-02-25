# Querying, Entitlement, and the Dialogue Layer

## 1. The Problem: "Is X True?"

A knowledge engineer coming from RDF/OWL expects to assert facts and query what's entailed. pyNMMS doesn't work that way. The engine maps **inferential relations** -- it answers "Does this commitment commit me to that?" not "Is X true?" Every query is a conditional: given *exactly* this, am I committed to that?

This document traces the design reasoning from that observation through to an architecture that can answer "Is X true?" within an inferentialist framework.


## 2. What You Can and Cannot Ask

### What's out

- **"Is X true?"** -- There are no atomic theorems. `=> Mortal(socrates)` is not derivable. The consequent is atomic, no proof rule applies, and no axiom matches: Containment fails (empty intersection), no explicit base consequence has an empty antecedent, and no ontology schema generates empty-antecedent pairs.

- **"Given everything I know, what follows?"** -- Putting all known commitments on the left side of a sequent defeats every inference except Containment. In NMMS, a maximally-informed antecedent is a maximally-defeated one. Exact match means any extra premise is a potential defeater.

### What's in

- **"Does commitment A commit me to B?"** -- Singleton queries against schemas: `{Man(socrates)} => {Mortal(socrates)}` is derivable via `subClassOf(Man, Mortal)`.

- **"Is this inferential relationship a theorem?"** -- Via DDT, `{} => {Man(socrates) -> Mortal(socrates)}` is derivable. The proof rule [R->] decomposes it to the singleton query, which matches the schema.

- **"Are A and B incompatible?"** -- `{Alive(socrates), Dead(socrates)} => {}` is derivable via `disjointWith(Alive, Dead)`.

The system answers "what follows from what?" rather than "what is the case?"


## 3. Three Layers to Get to "Is X True?"

To answer "Is X true?" in an inferentialist framework, you need three layers:

| Layer | Question | Mechanism | Status |
|-------|----------|-----------|--------|
| **NMMS engine** | Does this inferential relation hold? | Backward proof search | pyNMMS today |
| **Commitment store** | What are you committed to? | Forward chaining over assertions | Partially in pyNMMS (`CommitmentStore`) |
| **Entitlement tracker** | What are you entitled to? | Commitments minus incompatibilities, challenges, retractions | Elenchus (not yet built) |

### Layer 1: The NMMS Engine

A map of defeasible inferential relations. You query whether one commitment entails another. No accumulation of facts, no closed-world reasoning. This is pyNMMS today.

### Layer 2: The Commitment Store

Tracks what a respondent has explicitly asserted and forward-chains over schemas to compute what those assertions individually commit them to. For each explicit commitment, probe the schemas one at a time. The result is a set of **consequential commitments** -- things the respondent is committed to by virtue of what they've asserted.

A design decision arises here: **do you chase consequences of consequences?** If `Man(socrates)` commits you to `Mortal(socrates)`, and `subClassOf(Mortal, Physical)` is registered, do you add `Physical(socrates)`? If yes, you've reintroduced a form of transitivity at the commitment-tracking layer -- not in the proof theory, but in the application. The engine still says `{Man(socrates)} => {Physical(socrates)}` is NOT DERIVABLE. But the commitment store says "you're committed to it, via two individual inferential moves." This is a pragmatic choice for the dialogue layer, not a change to the calculus.

### Layer 3: The Entitlement Tracker

Resolves incompatibilities, handles challenges and retractions, and determines which commitments the respondent can still defend. This is where the Socratic move lives: "You're committed to both X and Y, but those are incompatible. Which do you retract?"

**"Is X true?"** becomes **"Am I entitled to X?"** -- which unpacks to "Have I made commitments that commit me to X, and has nothing defeated that entitlement?"

This is the inferentialist replacement for truth. There is no view from nowhere. There is just what you can defend given what you've asserted, what follows from it, and what challenges you've faced. Truth is a normative status you earn in the game, not a correspondence to how things are.


## 4. The Dialogue Assembles the Premises

### The exact-match brittleness problem

Multi-premise base axioms are already legal in pyNMMS:

```bash
pynmms tell -b base.json "ChestPain(patient), ElevatedTroponin(patient) |~ MyocardialInfarction(patient)"
```

But exact match means this fires only when the antecedent is *exactly* `{ChestPain(patient), ElevatedTroponin(patient)}`. A real patient with twelve findings on the table will never match it.

### The dialogue layer as navigator

The solution is that the dialogue layer -- Elenchus -- knows what multi-premise axioms and schemas exist, examines the respondent's full commitment set, and selectively assembles the right subsets of premises to query against the engine:

1. The doctor asserts twelve findings. Elenchus records them all.
2. Elenchus knows the shapes of the multi-premise axioms in the base.
3. For each axiom, Elenchus checks: are all the required premises in the commitment set?
4. If yes, it queries the engine with *exactly* those premises -- no more, no less.
5. Exact match succeeds. The conclusion is added to the commitment set.
6. Incompatibilities are checked. Socratic pushback if needed.

The engine stays pure -- exact match, no weakening, all metatheoretic properties preserved. The dialogue layer does the subsetting. The brittleness of exact match is not a problem -- it is a **division of labor**. The engine guarantees that each inferential move is individually sound and defeasible. The dialogue layer decides which moves to make given what the respondent has committed to.

**The engine is the map. Elenchus is the navigator.**


## 5. Example: Medical Diagnosis Without `jointCommitment`

Using only the six schema types currently in pyNMMS:

```
subClassOf(ChestPain, CardiacSymptom)
subClassOf(ElevatedTroponin, CardiacBiomarker)
subClassOf(PostprandialBurning, GISymptom)
subClassOf(MyocardialInfarction, CardiacCondition)
subClassOf(GERD, GICondition)
disjointWith(CardiacCondition, GICondition)
```

**Doctor:** "The patient has chest pain."

Assistant records `ChestPain(patient)`. Forward-chains: `subClassOf(ChestPain, CardiacSymptom)` fires, committed to `CardiacSymptom(patient)`. Reports: "Noted. That commits you to a cardiac symptom."

**Doctor:** "Troponin is elevated."

Assistant records `ElevatedTroponin(patient)`. Forward-chains: `subClassOf(ElevatedTroponin, CardiacBiomarker)` fires, committed to `CardiacBiomarker(patient)`. Reports: "Noted. That commits you to a cardiac biomarker."

The assistant **cannot** derive MI -- no schema combines two findings into a diagnosis. Each symptom individually commits you to a category, but the diagnostic synthesis doesn't happen automatically.

The assistant does what it can: "You have a cardiac symptom and a cardiac biomarker. What's your diagnosis?"

**Doctor:** "Myocardial infarction."

The doctor makes the diagnostic judgment. The assistant records `MyocardialInfarction(patient)` as an explicit commitment. Forward-chains: `subClassOf(MyocardialInfarction, CardiacCondition)` fires, committed to `CardiacCondition(patient)`.

**Doctor:** "But the patient also has burning after meals."

Assistant records `PostprandialBurning(patient)`. Forward-chains: `subClassOf(PostprandialBurning, GISymptom)` fires, committed to `GISymptom(patient)`. Reports: "Noted. That commits you to a GI symptom. Does that change your diagnosis?"

**Doctor:** "Yes. It's GERD."

Assistant records `GERD(patient)`. Forward-chains: `subClassOf(GERD, GICondition)` fires, committed to `GICondition(patient)`. Now `disjointWith(CardiacCondition, GICondition)` fires: **incompatibility detected**.

**"You're committed to both a cardiac condition and a GI condition, but those are incompatible. Which do you retract?"**

**Doctor:** "Retract MI."

Assistant retracts `MyocardialInfarction(patient)` and its consequential commitment `CardiacCondition(patient)`. Incompatibility resolved. The doctor is entitled to `GERD(patient)`.

Without multi-premise schemas, the system classifies individual findings and detects incompatibilities, but **the doctor does all the diagnostic synthesis**. The assistant is a scorekeeping partner, not a diagnostic engine.


## 6. The `jointCommitment` Question

### The pattern

The natural extension for multi-premise inferential commitments:

```
jointCommitment([C1, ..., Cn], D)
```

**Schema**: For any individual x, `{C1(x), ..., Cn(x)} |~_B {D(x)}`.

**Intended reading**: Holding commitments C1 through Cn jointly carries a defeasible material inferential commitment to D.

This is structurally a **production rule** -- a `defrule` in the ART/CLIPS lineage. The NMMS framing gives it exact-match defeasibility and composition with the proof-theoretic machinery, but the pattern is the same one production rule systems have used for decades.

| Schema | Antecedent | Consequent | Reading |
|-------|-----------|------------|---------|
| `subClassOf(C, D)` | `{C(x)}` | `{D(x)}` | single commitment entails |
| `disjointWith(C, D)` | `{C(x), D(x)}` | `{}` | joint commitments are incoherent |
| `jointCommitment([C1,...,Cn], D)` | `{C1(x),...,Cn(x)}` | `{D(x)}` | joint commitments entail |

### Metatheoretic properties preserved

- **Containment**: Antecedent and consequent are disjoint (assuming D is not among the Ci), so Containment is silent. Preserved.
- **Lazy evaluation**: Quantifies over individuals, no grounding needed.
- **Exact match**: All Ci must be present, nothing extra -- still defeasible.
- **No new proof rules**: Still just an axiom extension.

### The inferentialist concern

The existing six schemas have a clean reading as **meaning-constitutive** inferences -- they articulate what individual concepts and roles mean relative to each other. `subClassOf(Man, Mortal)` says something about what it is to be committed to someone being a Man. These define the **ontological vocabulary**.

`jointCommitment([ChestPain, ElevatedTroponin], MI)` is different. It doesn't say anything about what "chest pain" means or what "elevated troponin" means individually. It encodes **empirical domain knowledge** -- a medical fact about what combinations of observations indicate. That's substantive content, not conceptual structure.

Brandom allows multi-premise material inferences -- they are throughout *Making It Explicit*. So `jointCommitment` doesn't violate inferentialism. But it shifts the character of the schemas from articulating what concepts mean to encoding what the world is like.

Hlobil would note that the formalism already supports multi-premise base axioms -- nothing in the calculus restricts antecedent size. His concern would be pragmatic: exact match on a five-premise pattern is very brittle. A patient with twelve findings on the table will never match it directly. The dialogue layer must assemble the right subsets.

### Where `jointCommitment` belongs

The distinction suggests a separation:

- The six **ontology schemas** are the **conceptual structure layer** -- what concepts and roles mean relative to each other.
- **`jointCommitment`** is the **domain knowledge layer** -- what combinations of commitments indicate.

Both are material inferences. Both are defeasible. Both operate at the base level. But they serve different functions in the game of giving and asking for reasons. Being explicit about the difference matters even when the mechanism is shared.

### The pragmatic case: uniform defeasibility

In the Semantic Web stack, combining ontology axioms with domain rules means combining two formalisms with incompatible semantics. OWL is model-theoretic and monotonic; SWRL, SHACL rules, and Jena rules are procedural and forward-chaining. Bolting rules onto OWL can compromise decidability and produces a system where two semantic foundations interact unpredictably.

`jointCommitment` in NMMS avoids this entirely. It is a multi-premise base axiom pattern — the same kind of thing as `subClassOf` or `disjointWith`. It goes through the same `is_axiom()` check, the same exact-match defeasibility, the same proof search, the same metatheoretic guarantees (Containment preservation, Supraclassicality, Conservative Extension, Invertibility, Projection). No new engine, no new semantics, no interoperability headaches.

The formalism already accommodates it. The base already accepts multi-premise axioms. The schemas already generate axiom patterns lazily. `jointCommitment` is the obvious generalization that the existing design already supports. The fact that it looks like a `defrule` is not a problem — it is a production rule that lives in a framework with native defeasibility and clean metatheory.

The Semantic Web person bolts on SWRL and loses decidability. You add `jointCommitment` and lose nothing. That is the practical case for keeping domain rules inside the NMMS framework rather than exporting them to a separate rule layer.

The schema registry serves double duty: it is the ontology for the knowledge engineer, and it is Elenchus's **playbook** -- the set of patterns the dialogue layer uses to assemble the right queries from the respondent's commitments.


## 7. The Export Path

For deployment today, the cleanest architecture separates ontology engineering from query answering:

**pyNMMS for ontology engineering** -- The expert uses the defeasible, dialogue-driven framework to work out what concepts mean, how they relate, and what's incompatible with what. The Socratic pushback catches inconsistencies. The nonmonotonicity lets you explore provisional commitments and revise them. The result is a vetted ontological structure.

**Export to RDF/OWL for deployment** -- The six schema types map directly to standard vocabulary: `subClassOf`, `rdfs:range`, `rdfs:domain`, `rdfs:subPropertyOf`, `owl:disjointWith`, `owl:propertyDisjointWith`. Export the ontology, load it into a triple store, add the ABox, and query with SPARQL. The monotonic closed-world system handles "Is X true?"

**Domain rules live in the deployment system** -- Multi-premise diagnostic rules go into whatever rule engine sits on top of the triple store: SWRL, SHACL, Jena rules, or similar. They were never ontological structure to begin with.

The trade-off: exporting to OWL flattens the richest parts of what pyNMMS captures. The monotonic system can't represent "this inference holds unless you learn more" or "these two commitments are incompatible but resolvable through dialogue." The export path is pragmatic -- it gets you a deployable system today using existing infrastructure.

The fuller vision keeps the NMMS engine in the loop at runtime, with Elenchus doing the dialogue, the commitment store tracking assertions, the entitlement tracker resolving conflicts, and `jointCommitment` handling diagnostic synthesis. That system wouldn't need the classical export because it *is* the deployment platform.


## 8. Summary

For a Semantic Web person who wants to know how they can ask "Is X true?":

1. **pyNMMS doesn't answer "Is X true?"** -- it answers "Does this inferential relation hold?"
2. **To get to "Is X true?"** you need three layers: the engine (inferential map), the commitment store (forward chaining), and the entitlement tracker (incompatibility resolution and Socratic dialogue).
3. **"Is X true?" becomes "Am I entitled to X?"** -- a normative status earned in the game of giving and asking for reasons, not a correspondence to how things are.
4. **The dialogue layer assembles the premises.** Exact match is not brittleness -- it's a division of labor between the engine (which guarantees soundness) and the navigator (which selects the right inferential moves).
5. **`jointCommitment` stays inside NMMS.** It is a production rule (a `defrule` in the ART/CLIPS sense), but one that shares the same defeasibility semantics and metatheoretic guarantees as the ontology schemas. The Semantic Web alternative — bolting a rule language onto OWL — means two incompatible semantic foundations. NMMS gives you uniform defeasibility across ontological structure and domain rules at no cost.
6. **For deployment today**, export the ontology to RDF/OWL and use classical infrastructure. For the full inferentialist vision, build Elenchus.


## 9. References

- Brandom, R. B. (1994). *Making It Explicit: Reasoning, Representing, and Discursive Commitment*. Harvard University Press.

- Hlobil, U. & Brandom, R. B. (2025). *Reasons for Logic, Logic for Reasons*. Chapter 3: "Introducing Logical Vocabulary."