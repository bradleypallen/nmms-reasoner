# Exploring Chapter 3 with the CLI

This tutorial walks through the worked examples from Hlobil & Brandom 2025, Chapter 3 ("Introducing Logical Vocabulary") using the `pynmms` CLI. By the end you will have built Toy Base T, verified its consequences, demonstrated monotonicity and transitivity failures, and used logical vocabulary to make those failures explicit.

## 1. Building Toy Base T

Toy Base T from p. 118 has 7 atoms and 5 consequences. Start an interactive session:

```
$ pynmms repl
Starting with empty base.
pyNMMS REPL. Type 'help' for commands.

pynmms> tell atom p "Tara is human"
Added atom: p — Tara is human
pynmms> tell atom q "Tara's body temp is 37°C"
Added atom: q — Tara's body temp is 37°C
pynmms> tell atom v "Tara is healthy"
Added atom: v — Tara is healthy
pynmms> tell atom s "X is a triangle"
Added atom: s — X is a triangle
pynmms> tell atom t "angle-sum of X exceeds two right angles"
Added atom: t — angle-sum of X exceeds two right angles
pynmms> tell atom w "angle-sum of X equals two right angles"
Added atom: w — angle-sum of X equals two right angles
pynmms> tell atom x "X is a Euclidean plane triangle"
Added atom: x — X is a Euclidean plane triangle
```

Now add the five base consequences. Note that `s, t |~` has an empty consequent — this encodes an *incompatibility* (s and t cannot hold together):

```
pynmms> tell p |~ q
Added: {'p'} |~ {'q'}
pynmms> tell s, t |~
Added: set() |~ set()
pynmms> tell p, q |~ v
Added: {'p', 'q'} |~ {'v'}
pynmms> tell s |~ w
Added: {'s'} |~ {'w'}
pynmms> tell s, w |~ x
Added: {'s', 'w'} |~ {'x'}
```

Verify everything with `show`:

```
pynmms> show
Language (7 atoms):
  p — Tara is human
  q — Tara's body temp is 37°C
  s — X is a triangle
  t — angle-sum of X exceeds two right angles
  v — Tara is healthy
  w — angle-sum of X equals two right angles
  x — X is a Euclidean plane triangle
Consequences (5):
  {'p'} |~ {'q'}
  {'p', 'q'} |~ {'v'}
  {'s'} |~ {'w'}
  {'s', 't'} |~ set()
  {'s', 'w'} |~ {'x'}
```

Save for later use:

```
pynmms> save toyT.json
Saved to toyT.json
```

## 2. Base consequences

Verify the five explicit consequences are derivable:

```
pynmms> ask p => q
DERIVABLE
pynmms> ask p, q => v
DERIVABLE
pynmms> ask s => w
DERIVABLE
pynmms> ask s, t =>
DERIVABLE
pynmms> ask s, w => x
DERIVABLE
```

## 3. Monotonicity failures

NMMS omits [Weakening], so adding premises can defeat inferences.

**MO-failure-1:** `p |~ q` but `p, r ̸|~ q` — adding atom `r` defeats the inference:

```
pynmms> ask p => q
DERIVABLE
pynmms> ask p, r => q
NOT DERIVABLE
```

This happens because the base relation uses exact syntactic match — the pair `({p, r}, {q})` is not in the base, and there is no Weakening rule to derive it from `({p}, {q})`.

## 4. Transitivity failures

NMMS omits [Mixed-Cut], so chaining good inferences can yield bad ones.

**CT-failure-1:** `p |~ q` and `p, q |~ v` but `p ̸|~ v`:

```
pynmms> ask p => q
DERIVABLE
pynmms> ask p, q => v
DERIVABLE
pynmms> ask p => v
NOT DERIVABLE
```

Intuitively: Tara is human, so normally her body temp is 37°C. And if Tara is human *and* her body temp is 37°C, she is healthy. But we cannot conclude from Tara being human alone that she is healthy — her body temp might not be 37°C (she might have a fever).

## 5. Explicitation with logical vocabulary

The NMMS rules let logical vocabulary "make explicit" the reason relations in the base.

**DD (Deduction-Detachment):** Since `p |~ q`, we have `|~ p -> q`:

```
pynmms> ask => p -> q
DERIVABLE
```

**II (Incoherence-Incompatibility):** Since `s, t |~` (s and t are incompatible), we have `|~ ~(s & t)`:

```
pynmms> ask => ~(s & t)
DERIVABLE
```

## 6. Batch base creation

Instead of typing each line interactively, create a `.base` file:

```
# toyT.base — Toy Base T from Hlobil & Brandom 2025, Ch. 3
atom p "Tara is human"
atom q "Tara's body temp is 37°C"
atom v "Tara is healthy"
atom s "X is a triangle"
atom t "angle-sum of X exceeds two right angles"
atom w "angle-sum of X equals two right angles"
atom x "X is a Euclidean plane triangle"
p |~ q
s, t |~
p, q |~ v
s |~ w
s, w |~ x
```

Then load it in one command:

```bash
pynmms tell -b toyT.json --create --batch toyT.base
```

## 7. Scripting with exit codes and JSON

### Exit codes

`pynmms ask` uses semantic exit codes following the `grep`/`diff` convention:

| Exit code | Meaning |
|-----------|---------|
| 0 | Derivable |
| 1 | Error |
| 2 | Not derivable |

Use this in shell scripts:

```bash
if pynmms ask -b toyT.json -q "p => q"; then
    echo "p entails q"
else
    echo "p does not entail q"
fi
```

### JSON output

Use `--json` for machine-readable output:

```bash
$ pynmms ask -b toyT.json --json "p => q"
{"status":"DERIVABLE","sequent":{"antecedent":["p"],"consequent":["q"]},"depth_reached":0,"cache_hits":0}
```

Pipe to `jq`:

```bash
$ pynmms ask -b toyT.json --json "p => q" | jq .status
"DERIVABLE"
```

### Batch queries

Query multiple sequents at once:

```bash
# queries.txt
p => q
p, r => q
=> p -> q
=> ~(s & t)
p => v
```

```bash
$ pynmms ask -b toyT.json --json --batch queries.txt
{"status":"DERIVABLE","sequent":{"antecedent":["p"],"consequent":["q"]},"depth_reached":0,"cache_hits":0}
{"status":"NOT_DERIVABLE","sequent":{"antecedent":["p","r"],"consequent":["q"]},"depth_reached":1,"cache_hits":0}
{"status":"DERIVABLE","sequent":{"antecedent":[],"consequent":["p -> q"]},"depth_reached":1,"cache_hits":0}
{"status":"DERIVABLE","sequent":{"antecedent":[],"consequent":["~(s & t)"]},"depth_reached":2,"cache_hits":0}
{"status":"NOT_DERIVABLE","sequent":{"antecedent":["p"],"consequent":["v"]},"depth_reached":1,"cache_hits":0}
```

The exit code reflects the aggregate: 0 if all derivable, 2 if any not derivable, 1 on error.
