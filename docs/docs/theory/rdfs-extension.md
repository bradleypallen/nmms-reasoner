# The NMMS_RDFS Extension: Defeasible RDFS Axiom Schemas

## 1. Introduction

NMMS (Non-Monotonic Multi-Succedent) provides a proof-theoretic framework for codifying **open reason relations** -- consequence relations where Monotonicity ([Weakening]) and Transitivity ([Mixed-Cut]) can fail. Hlobil & Brandom (2025), Chapter 3 ("Introducing Logical Vocabulary"), develops the propositional fragment: a sequent calculus whose eight Ketonen-style rules extend an arbitrary material base B = <L_B, |~_B> to a full propositional consequence relation |~. The calculus enjoys Supraclassicality, Conservative Extension, Invertibility, and a Projection theorem reducing derivability to base-level axiom checking.

NMMS_RDFS extends the propositional fragment by **enriching the material base** with defeasible axiom schemas drawn from a subset of the W3C RDF Schema vocabulary. The extension adds no new proof rules: the same eight propositional rules apply unchanged. Instead, four RDFS axiom schema types -- `subClassOf`, `range`, `domain`, `subPropertyOf` -- are registered as schematic patterns that the material base evaluates lazily when checking whether a sequent is an axiom. Because the extension operates entirely at the level of the base, all of Hlobil's proofs for the propositional calculus are preserved without modification.

The resulting system, NMMS_RDFS, occupies a distinctive niche: it supports defeasible ontological reasoning (class hierarchies, role constraints, property hierarchies) within a framework where adding premises can defeat inferences and chaining good inferences can yield bad ones -- precisely the features that distinguish NMMS from classical and monotonic nonclassical logics.


## 2. Design Decision: Axiom Extensions, Not Proof Rules

The central architectural decision in NMMS_RDFS is to extend the material base rather than the proof rules. To appreciate why this matters, it helps to recall the structure of NMMS proof trees.

An NMMS proof tree has two kinds of nodes:

- **Leaves (axioms)**: Sequents that hold by virtue of the base alone. These are checked by `is_axiom(Gamma, Delta)`, which succeeds if (a) Gamma and Delta overlap (Containment), or (b) the pair (Gamma, Delta) is explicitly in |~_B (exact match).

- **Internal nodes (rule applications)**: Sequents derived by applying one of the eight Ketonen-style propositional rules to reduce a complex sequent to simpler subgoals. The rules decompose logical connectives (~, ->, &, |) until only atomic sentences remain.

Hlobil's Chapter 3 proofs -- Supraclassicality (Fact 2), Conservative Extension (Fact 3 / Prop. 26), Invertibility (Prop. 27), and the Projection Theorem (Theorem 7) -- are established for **any** material base satisfying the Containment axiom (Definition 1). The proofs make no assumptions about the internal structure of base-level axioms beyond Containment. This means that any extension of |~_B that preserves Containment automatically inherits all of these results.

NMMS_RDFS exploits this observation. The four RDFS axiom schemas add new pairs to the base consequence relation |~_B. Each schema generates axioms of the form {s} |~ {t} where s and t are atomic sentences with disjoint singleton antecedent and consequent sets. Since Gamma = {s} and Delta = {t} with s != t, these pairs have Gamma intersection Delta = empty, so they do not conflict with Containment (which only requires that overlapping pairs be included). The schemas therefore extend |~_B while preserving Containment, and all of Hlobil's metatheoretic results carry over without any additional proof work.

By contrast, introducing new **proof rules** -- for instance, unrestricted quantifier rules [forall-L], [forall-R], [exists-L], [exists-R] -- would modify the internal structure of proof trees. This would require:

1. Re-establishing Invertibility for the new rules.
2. Re-proving the Projection Theorem with a modified AtomicImp decomposition.
3. Verifying that Supraclassicality and Conservative Extension still hold with the expanded rule set.
4. Ensuring that the third-top-sequent pattern (which compensates for the absence of structural contraction) interacts correctly with the new rules.

None of this work is necessary for NMMS_RDFS, because the proof rules are left unchanged. The RDFS schemas are visible only to the axiom checker, not to the proof search engine.

**Implementation consequence**: In `pyNMMS`, the `NMMSReasoner` class from the propositional core works without modification with `RDFSMaterialBase`. No subclassing of the reasoner is required. The only change is that `RDFSMaterialBase.is_axiom()` adds a third axiom check (Ax3: RDFS schema match) after the standard Ax1 (Containment) and Ax2 (explicit base consequence).


## 3. The NMMS_RDFS Material Base

An NMMS_RDFS material base B_RDFS = <L_B, |~_B, S> extends the standard NMMS material base with a set S of defeasible RDFS axiom schemas. The atomic language L_B is partitioned into two syntactic categories:

**ABox assertions** (ground facts about individuals):

- **Concept assertions**: `C(a)` -- individual `a` belongs to concept `C`. Examples: `Man(socrates)`, `Happy(alice)`, `HeartAttack(patient)`.
- **Role assertions**: `R(a,b)` -- individual `a` stands in role `R` to individual `b`. Examples: `hasChild(alice,bob)`, `hasSymptom(patient,chestPain)`.

**TBox schemas** (defeasible terminological axioms):

The TBox consists of four RDFS axiom schema types. Each schema is evaluated lazily at query time -- not eagerly grounded over all known individuals. All schemas use **exact match** (singleton antecedent, singleton consequent, no weakening), which is what preserves nonmonotonicity.

### 3.1 subClassOf(C, D)

**Schema**: For any individual x,

    {C(x)} |~_B {D(x)}

**Intended reading**: Concept C is (defeasibly) a subclass of concept D. Any individual that is a C is, defeasibly, also a D.

**Example**: `subClassOf(Man, Mortal)` generates the axiom `{Man(socrates)} |~ {Mortal(socrates)}` for any individual `socrates`, without needing to enumerate all individuals in advance.

### 3.2 range(R, C)

**Schema**: For any individuals x, y,

    {R(x,y)} |~_B {C(y)}

**Intended reading**: The range of role R is (defeasibly) concept C. The second argument of any R-assertion is, defeasibly, a C.

**Example**: `range(hasChild, Person)` generates `{hasChild(alice,bob)} |~ {Person(bob)}` -- if alice has a child bob, then bob is (defeasibly) a Person.

### 3.3 domain(R, C)

**Schema**: For any individuals x, y,

    {R(x,y)} |~_B {C(x)}

**Intended reading**: The domain of role R is (defeasibly) concept C. The first argument of any R-assertion is, defeasibly, a C.

**Example**: `domain(hasChild, Parent)` generates `{hasChild(alice,bob)} |~ {Parent(alice)}` -- if alice has a child, then alice is (defeasibly) a Parent.

### 3.4 subPropertyOf(R, S)

**Schema**: For any individuals x, y,

    {R(x,y)} |~_B {S(x,y)}

**Intended reading**: Role R is (defeasibly) a subproperty of role S. Any R-assertion between two individuals defeasibly entails the corresponding S-assertion.

**Example**: `subPropertyOf(hasChild, hasDescendant)` generates `{hasChild(alice,bob)} |~ {hasDescendant(alice,bob)}` -- if alice has child bob, then alice (defeasibly) has descendant bob.


## 4. Containment Preservation

**Claim**: If B = <L_B, |~_B> satisfies Containment, then the extended base B_RDFS = <L_B, |~_B union S_ground> also satisfies Containment, where S_ground denotes the set of all ground instances of the registered RDFS schemas.

**Proof sketch**: Containment requires that Gamma |~_B Delta whenever Gamma intersection Delta is nonempty. We must show two things:

1. **The original Containment pairs are preserved**: B_RDFS extends |~_B, so all original pairs remain.

2. **The new schema pairs do not violate Containment**: Each RDFS schema adds pairs of the form ({s}, {t}) where s and t are distinct atomic sentences (e.g., s = `Man(socrates)` and t = `Mortal(socrates)` for a subClassOf schema). Since s != t, we have {s} intersection {t} = empty, so these pairs are in the region where Containment is silent -- Containment only mandates inclusion of pairs with nonempty intersection, and imposes no constraint on pairs with empty intersection. Adding pairs with empty intersection cannot violate the requirement that pairs with nonempty intersection are included.

More precisely, Containment states: for all Gamma, Delta in P(L_B), if Gamma intersection Delta != empty then Gamma |~_B Delta. The RDFS schemas only add pairs where the intersection **is** empty. So the condition "if Gamma intersection Delta != empty then Gamma |~_B Delta" is unaffected: the "if" side is unchanged (no new Gamma, Delta with nonempty intersection are introduced that were not already covered), and the "then" side is only strengthened (more pairs are in |~_B, not fewer).

**Corollary**: Since B_RDFS satisfies Containment, all of the following results from Hlobil & Brandom (2025), Ch. 3, hold for NMMS_RDFS without modification:

- **Fact 2 (Supraclassicality)**: CL is a subset of |~. All classically valid sequents are derivable.
- **Fact 3 / Proposition 26 (Conservative Extension)**: If Gamma union Delta is a subset of L_B, then Gamma |~ Delta iff Gamma |~_B Delta. Logical vocabulary does not alter base-level reason relations.
- **Proposition 27 (Invertibility)**: All NMMS rules are invertible.
- **Theorem 7 (Projection)**: Every sequent in the logically extended language decomposes into a set of base-vocabulary sequents (AtomicImp) such that derivability reduces to checking AtomicImp against |~_B.


## 5. Key Properties

### 5.1 Defeasibility

All RDFS schemas are **defeasible**: adding premises to the antecedent side of a derivable sequent can defeat the inference. This is because the `is_axiom` check uses exact match -- a schema `{C(x)} |~ {D(x)}` matches only when the antecedent is exactly `{C(x)}` and the consequent is exactly `{D(x)}`, with no additional sentences on either side.

**Example**: With `subClassOf(Man, Mortal)`:

- `{Man(socrates)} |~ {Mortal(socrates)}` -- derivable (schema match).
- `{Man(socrates), Immortal(socrates)} |~ {Mortal(socrates)}` -- **not derivable**. The antecedent `{Man(socrates), Immortal(socrates)}` does not match the schema's singleton antecedent pattern.

This is not a bug but a feature: learning that Socrates is immortal defeats the defeasible inference that he is mortal. The exact-match semantics of the material base (inherited from Hlobil's framework) is what makes this possible without any explicit defeat mechanism or priority ordering.

### 5.2 Non-transitivity

Because NMMS lacks [Mixed-Cut], chaining two individually valid schema applications does not yield a valid inference. Schemas compose only when the intermediate step is explicitly recorded in the base as an axiom.

**Example**: With `subClassOf(Man, Mortal)` and `subClassOf(Mortal, Physical)`:

- `{Man(socrates)} |~ {Mortal(socrates)}` -- derivable (first schema).
- `{Mortal(socrates)} |~ {Physical(socrates)}` -- derivable (second schema).
- `{Man(socrates)} |~ {Physical(socrates)}` -- **not derivable**. There is no axiom matching `({Man(socrates)}, {Physical(socrates)})`, and backward proof search cannot chain the two schemas because the calculus lacks [Mixed-Cut].

Similarly, `subPropertyOf(hasChild, hasDescendant)` and `subPropertyOf(hasDescendant, hasRelative)` do not jointly entail `{hasChild(alice,bob)} |~ {hasRelative(alice,bob)}`.

This distinguishes NMMS_RDFS from classical RDFS, where `rdfs:subClassOf` is transitive. In NMMS_RDFS, if one wants the transitive closure, one must explicitly register each link: `subClassOf(Man, Mortal)`, `subClassOf(Man, Physical)`, and `subClassOf(Mortal, Physical)` as separate schemas. This is by design -- some subclass chains should compose, and others should not, depending on the domain.

### 5.3 Lazy Evaluation

RDFS schemas are stored as abstract patterns and evaluated lazily during `is_axiom` checks. This means:

- **Storage**: O(k) schemas, where k is the number of registered schemas. Not O(n * k) ground entries, where n is the number of known individuals.
- **Adding individuals**: O(1). When a new individual enters the language (e.g., `Man(plato)` is added), no schema re-expansion or re-grounding is needed. The schema `subClassOf(Man, Mortal)` will automatically match `{Man(plato)} |~ {Mortal(plato)}` at query time.
- **Query time**: Each `is_axiom` call iterates over the registered schemas and attempts pattern matching against the concrete antecedent and consequent. For singleton pairs (the only ones RDFS schemas generate), this is O(k) per axiom check.

This lazy evaluation strategy avoids the combinatorial explosion that would arise from eagerly grounding all schemas over all known individuals, especially in bases with many individuals and many schemas.

### 5.4 Deduction-Detachment Theorem (DDT)

The DDT -- Gamma |~ A -> B, Delta iff Gamma, A |~ B, Delta -- is a property of the proof rules ([R->] and [L->]), not of the base. Since NMMS_RDFS does not modify the proof rules, DDT holds automatically.

**Example**: With `subClassOf(Man, Mortal)`:

- `{Man(socrates)} |~ {Mortal(socrates)}` is derivable (schema match).
- Therefore, by DDT, `{} |~ {Man(socrates) -> Mortal(socrates)}` is also derivable.

The backward proof proceeds: [R->] decomposes `{} => {Man(socrates) -> Mortal(socrates)}` into `{Man(socrates)} => {Mortal(socrates)}`, which is an axiom via the subClassOf schema. This means that NMMS_RDFS can express RDFS schema relationships as object-language implications -- the logical vocabulary "makes explicit" the defeasible material inferences encoded in the schemas.


## 6. Relationship to Classical RDFS and Description Logics

NMMS_RDFS draws its vocabulary from a subset of the W3C RDF Schema 1.1 specification (2014), but the semantics differ fundamentally:

| Feature | Classical RDFS | NMMS_RDFS |
|---------|---------------|-----------|
| Entailment regime | Monotonic, model-theoretic | Nonmonotonic, proof-theoretic |
| Weakening | Holds | Fails (exact match) |
| Transitivity of subClassOf | Built-in (RDFS semantics) | Fails (no [Mixed-Cut]) |
| Transitivity of subPropertyOf | Built-in (RDFS semantics) | Fails (no [Mixed-Cut]) |
| Open-world assumption | Yes | Not applicable (proof-theoretic) |
| Schema grounding | Eager (RDF graph closure) | Lazy (pattern matching at query time) |

The four NMMS_RDFS schema types correspond to four RDFS vocabulary terms:

- `subClassOf(C, D)` corresponds to `C rdfs:subClassOf D`
- `range(R, C)` corresponds to `R rdfs:range C`
- `domain(R, C)` corresponds to `R rdfs:domain C`
- `subPropertyOf(R, S)` corresponds to `R rdfs:subPropertyOf S`

However, the correspondence is structural, not semantic. In classical RDFS, these terms participate in monotonic entailment with built-in transitivity, reflexivity, and interactions defined by the RDFS entailment rules (e.g., if `R rdfs:range C` and `C rdfs:subClassOf D`, then `R rdfs:range D`). In NMMS_RDFS, each schema is an independent defeasible axiom with no built-in interactions.

The relationship to Description Logics (DLs) is also worth noting. The ABox/TBox distinction in NMMS_RDFS is borrowed from DL terminology, and the concept/role assertion syntax follows DL conventions. However, NMMS_RDFS does not implement any DL tableau calculus or reasoning procedure. The proof search is Hlobil's propositional backward search; the RDFS schemas participate only as base-level axioms checked at the leaves. For work on defeasible extensions of Description Logics proper, see Casini & Straccia (2010) and Giordano et al. (2013).


## 7. What NMMS_RDFS Does NOT Include

To be explicit about the boundaries of the extension:

- **No unrestricted quantifiers**: NMMS_RDFS does not add universal or existential quantifier rules (forall-L, forall-R, exists-L, exists-R). Hlobil identifies fundamental problems with unrestricted quantification in nonmonotonic settings: unrestricted forall-R overgeneralizes from specific instances, and unrestricted forall-L smuggles in defeating information via universal instantiation. NMMS_RDFS avoids these problems entirely by working at the schema level rather than adding quantifier proof rules.

- **No ALL/SOME proof rules**: Unlike ALC-style restricted quantifier extensions, NMMS_RDFS does not include proof rules for restricted universal (`ALL R.C`) or restricted existential (`SOME R.C`) expressions. These would require new internal proof tree nodes, revalidation of Invertibility and Projection, and careful treatment of the third-top-sequent pattern. The RDFS schema approach achieves useful ontological reasoning without this complexity.

- **No transitive closure**: `subClassOf` and `subPropertyOf` are not transitively closed. Each link must be explicitly registered. This is a consequence of the absence of [Mixed-Cut] and is a deliberate design feature of the NMMS framework.

- **No concept intersection, union, or complement**: NMMS_RDFS does not support complex concept expressions such as `C AND D`, `C OR D`, or `NOT C`. The propositional connectives (~, &, |, ->) are available in the proof rules and can combine atomic sentences, but there is no mechanism for constructing complex concepts from simpler ones within the RDFS schema language itself.

- **No cardinality restrictions or nominals**: Features such as `MIN n R.C`, `MAX n R.C`, `EXACTLY n R.C`, or `{a}` (nominals) from expressive DLs (SHOIN, SROIQ) are not included.

- **No role characteristics**: NMMS_RDFS does not support role transitivity, symmetry, reflexivity, inverseness, functionality, or role chains as built-in features. If `R` should be symmetric, both `{R(a,b)} |~ {R(b,a)}` and `{R(b,a)} |~ {R(a,b)}` must be registered as explicit ground consequences or handled through additional schemas.


## 8. Assumptions and Open Questions

### Assumptions

1. **Containment suffices**: The Containment axiom (Definition 1 in Ch. 3) is the only structural requirement on the material base. We assume that Hlobil's proofs depend on no other properties of |~_B beyond Containment and the specific form of the proof rules. This assumption is supported by the text of Ch. 3, which states the results for "any material base satisfying Containment."

2. **Exact match is the right notion of defeasibility**: The schemas use singleton antecedent and singleton consequent with no weakening. This means that *any* additional premise defeats the inference. In practice, one might want finer-grained defeat: `{Man(socrates), Greek(socrates)} |~ {Mortal(socrates)}` might be desired even though the schema only directly generates the singleton-antecedent form. Users can accommodate this by adding explicit ground consequences for the desired multi-premise patterns.

3. **Propositional connectives are sufficient for logical structure**: The claim is that the four RDFS schemas, combined with propositional connectives via the eight proof rules, provide adequate expressive power for a useful fragment of ontological reasoning. This is an empirical claim that depends on the intended applications.

### Open Questions

1. **Schema interaction principles**: Should there be systematic rules for how schemas interact? For instance, should `subClassOf(C, D)` and `domain(R, C)` jointly entail anything about `R` and `D`? In classical RDFS, they do (via monotonic closure). In NMMS_RDFS, they do not, by design. But are there principled middle grounds -- forms of controlled interaction that preserve the nonmonotonic character while recovering some useful entailments?

2. **Retraction semantics**: The `CommitmentStore` supports retracting schemas by source label. What are the formal properties of retraction? Does retracting a schema correspond to a well-defined operation on the consequence relation? How does retraction interact with cached proof results?

3. **Relationship to preferential and rational consequence relations**: The defeasible RDFS literature (Casini & Straccia 2010, Giordano et al. 2013) works with preferential and rational consequence relations from the KLM framework. How does the NMMS notion of defeasibility (failure of Weakening) relate to the KLM notion (failure of Monotonicity in preferential models)? Are there translations or embeddings between the two frameworks?

4. **Completeness relative to intended models**: NMMS_RDFS is sound by construction (all axioms are explicitly registered). But is there a natural model-theoretic semantics for RDFS schemas in the NMMS framework, and if so, is the system complete with respect to that semantics?

5. **Scaling properties**: The lazy evaluation strategy avoids combinatorial explosion in schema grounding, but the proof search itself has exponential worst-case complexity (due to the multi-premise Ketonen rules for [L->], [L|], [R&]). How does the addition of RDFS schemas affect proof search performance in practice? Are there heuristics for ordering schema checks to improve average-case behavior?


## 9. References

- Hlobil, U. & Brandom, R. B. (2025). *Reasons for Logic, Logic for Reasons*. Chapter 3: "Introducing Logical Vocabulary."

- Casini, G. & Straccia, U. (2010). Rational Closure for Defeasible Description Logics. In *Proceedings of the 12th European Conference on Logics in Artificial Intelligence (JELIA)*, pp. 77--90. Springer.

- Giordano, L., Gliozzi, V., Olivetti, N., & Pozzato, G. L. (2013). A Non-Monotonic Description Logic for Reasoning About Typicality. *Artificial Intelligence*, 195, 165--202.

- W3C (2014). *RDF Schema 1.1*. W3C Recommendation, 25 February 2014. https://www.w3.org/TR/rdf-schema/
