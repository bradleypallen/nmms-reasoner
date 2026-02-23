# CLI Usage

## Overview

pyNMMS provides the `pynmms` command with three subcommands:

```bash
pynmms tell   # Add atoms or consequences to a base
pynmms ask    # Query derivability
pynmms repl   # Interactive REPL
```

## `pynmms tell`

Add atoms or consequences to a JSON base file.

```bash
# Create a new base and add a consequence
pynmms tell -b base.json --create "A |~ B"

# Add more consequences (base file must exist)
pynmms tell -b base.json "B |~ C"

# Add atoms
pynmms tell -b base.json "atom X"

# Add atoms with annotations
pynmms tell -b base.json 'atom p "Tara is human"'

# Empty consequent (incompatibility)
pynmms tell -b base.json "s, t |~"

# Empty antecedent (theorem)
pynmms tell -b base.json "|~ p"
```

### Syntax

- **Consequence**: `A |~ B` or `A, B |~ C, D` (comma-separated)
- **Incompatibility**: `A, B |~` (empty consequent)
- **Theorem**: `|~ A` (empty antecedent)
- **Atom**: `atom X`
- **Atom with annotation**: `atom X "description"`

### Options

| Flag | Description |
|------|-------------|
| `-b`, `--base` | Path to JSON base file (required) |
| `--create` | Create the base file if missing |
| `--rq` | Use restricted quantifier mode |
| `--json` | Output as JSON (pipe-friendly) |
| `-q`, `--quiet` | Suppress output; rely on exit code |
| `--batch FILE` | Read statements from FILE (use `-` for stdin) |

## `pynmms ask`

Query whether a sequent is derivable.

```bash
pynmms ask -b base.json "A => B"
# Output: DERIVABLE

pynmms ask -b base.json "A => C"
# Output: NOT DERIVABLE
```

### Exit codes

Following the `grep`/`diff`/`cmp` convention:

| Exit code | Meaning |
|-----------|---------|
| 0 | Derivable |
| 1 | Error |
| 2 | Not derivable |

### Options

| Flag | Description |
|------|-------------|
| `-b`, `--base` | Path to JSON base file (required) |
| `--trace` | Print the proof trace |
| `--max-depth N` | Set the maximum proof depth (default: 25) |
| `--rq` | Use restricted quantifier mode |
| `--json` | Output as JSON (pipe-friendly) |
| `-q`, `--quiet` | Suppress output; rely on exit code |
| `--batch FILE` | Read sequents from FILE (use `-` for stdin) |

### JSON output

```bash
pynmms ask -b base.json --json "A => B"
# Output: {"status":"DERIVABLE","sequent":{"antecedent":["A"],"consequent":["B"]},"depth_reached":0,"cache_hits":0}
```

With `--trace`, adds a `"trace"` array.

### Stdin input

```bash
echo "A => B" | pynmms ask -b base.json -
```

### Batch mode

```bash
pynmms ask -b base.json --batch queries.txt
pynmms ask -b base.json --json --batch queries.txt
cat queries.txt | pynmms ask -b base.json --batch -
```

```bash
pynmms ask -b base.json --trace "=> A -> B"
# Output:
# DERIVABLE
#
# Proof trace:
#   [R→] on A -> B
#     AXIOM: A => B
#
# Depth reached: 1
# Cache hits: 0
```

## `pynmms repl`

Interactive REPL for exploring reason relations.

```bash
pynmms repl
pynmms repl -b base.json  # Load existing base
```

### REPL Commands

| Command | Description |
|---------|-------------|
| `tell A \|~ B` | Add a consequence |
| `tell A, B \|~` | Add incompatibility (empty consequent) |
| `tell \|~ A` | Add theorem (empty antecedent) |
| `tell atom A` | Add an atom |
| `tell atom A "desc"` | Add an atom with annotation |
| `ask A => B` | Query derivability |
| `show` | Display the current base (with annotations) |
| `trace on/off` | Toggle proof trace display |
| `save <file>` | Save base to JSON |
| `load <file>` | Load base from JSON |
| `help` | Show available commands |
| `quit` | Exit the REPL |

### Example Session

```
$ pynmms repl
Starting with empty base.
pyNMMS REPL. Type 'help' for commands.

pynmms> tell atom p "Tara is human"
Added atom: p — Tara is human
pynmms> tell atom q "Tara's body temp is 37°C"
Added atom: q — Tara's body temp is 37°C
pynmms> tell p |~ q
Added: {'p'} |~ {'q'}
pynmms> tell s, t |~
Added: set() |~ set()
pynmms> ask p => q
DERIVABLE
pynmms> ask p, r => q
NOT DERIVABLE
pynmms> show
Language (4 atoms):
  p — Tara is human
  q — Tara's body temp is 37°C
  s
  t
Consequences (2):
  {'p'} |~ {'q'}
  {'s', 't'} |~ set()
pynmms> save mybase.json
Saved to mybase.json
pynmms> quit
```

## Batch files

### Tell batch format

One statement per line. Blank lines and `#` comments are skipped:

```
# mybase.base
atom p "Tara is human"
atom q "Tara's body temp is 37°C"
p |~ q
s, t |~
```

```bash
pynmms tell -b base.json --create --batch mybase.base
```

### RQ batch format

With `--rq`, batch files also support `schema` lines:

```
atom Happy(alice) "Alice is happy"
atom hasChild(alice,bob)
Happy(alice) |~ Good(alice)
schema concept hasChild alice Happy
schema inference hasChild alice Serious HeartAttack
```

```bash
pynmms tell -b rq_base.json --create --rq --batch rq_base.base
```

### Ask batch format

One sequent per line:

```
# queries.txt
A => B
A, B => C
=> A -> B
```

```bash
pynmms ask -b base.json --batch queries.txt
pynmms ask -b base.json --json --batch queries.txt  # JSONL output
```
