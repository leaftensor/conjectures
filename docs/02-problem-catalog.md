# The problem catalog

260 targets. This is what is in the pool, how it is weighted, and how to pick.

All figures from `data/targets.json`, generated from the live catalogue API on
**14 September 2026**, pinned task commit `8432eac998110a563e03df65a28c117e97c8c142`.

---

## Composition

| | Count |
|---|---|
| Total targets | **260** |
| Erdős problems | 236 |
| Ben Green's Open Problems | 24 |
| Accepting **both** a proof and a refutation | **260** (all of them) |
| With a live, payable bounty | 253 |
| Withdrawn (`ALREADY_SOLVED`) | 7 |
| Never attempted | **246** |
| Attempted at least once | 14 |

**Every target has two modes.** `formalized` is the statement; `counterexample` is its
negation. Two tasks, one reward identity — you cannot collect twice, and whoever takes one
direction closes the other. This is not a technicality: it means half the ways into any
given problem are refutations, and per [`docs/03-attack-vectors.md`](03-attack-vectors.md)
that is where 2026's results came from.

### By field

| AMS | Field | Count |
|---|---|---|
| 11 | Number theory | 202 |
| 5 | Combinatorics | 61 |
| 52 | Convex and discrete geometry | 12 |
| 20 | Group theory | 3 |
| 94 | Information and communication | 3 |
| 51 | Geometry | 2 |
| 37, 28, 40, 30, 3, 60, 42 | one each | 7 |

A heavily number-theoretic pool — that is what a catalogue built from the Erdős problems
looks like. If your background is combinatorics you are fishing in 61 targets; if it is
analysis, in seven.

---

## The bounty tiers

There are exactly two quotes, and they are the same for every target in each tier:

| α | USD | Targets |
|---|---|---|
| 6,314.50 α | $3,809.84 | 197 |
| 5,538.46 α | $3,341.58 | 56 |

That is the whole distribution. **There is no such thing as picking a target because it pays
more** — the spread between the best- and worst-paying target is 14%, and it is not a
judgement about difficulty. The FAQ is explicit that the figure is calculated from *how long
the problem has stood open*, not from how hard it is:

> an older problem pays more, solving one raises the bounty on everything left, and
> publishing new problems lowers them

So optimise for **probability of success**, not for the size of the prize. Read
[`docs/04-economics.md`](04-economics.md) before assuming you will receive the number on the
card at all.

The seven targets with no quote return `reason: ALREADY_SOLVED`. Note that the API still
reports `is_open: true` for all 260 — **`is_open` is not the field that matters.**
`bounty.available` is. Filter on that.

---

## Picking a target

`build_catalog.py` scores every target and writes the result to `data/targets.csv`. The score
is a **ranking heuristic**, deliberately crude, built on the pool's own admission bias
(`POOL.md` requires every admitted target to carry a feasibility signal such as "compact
target, discrete domain, finite or finitary structure, partial results in the same source, or
a standard Mathlib surface"). It rewards:

| Signal | Weight | Why |
|---|---|---|
| `Finset` / `Fin n` / `Decidable` / `Fintype` | 2.0 | A finite domain is one a search can exhaust |
| `∃` | 1.5 | An existential target accepts a single witness |
| `SimpleGraph` | 1.0 | Graph existentials are routinely searchable |
| `∀ … ℕ … (∃\|¬)` | 0.5 | Sometimes yields to bounded search plus a covering argument |
| Lean type under 120 characters | 1.0 | A compact goal |

Current distribution:

| Band | Targets |
|---|---|
| 8+ (read these first) | 7 |
| 5–7 | 43 |
| 3–4 | 80 |
| 0–2 | 130 |

```bash
column -s, -t < data/targets.csv | sort -k9 -nr | head -20
```

For the full ranked list with the exact Lean types, use the CSV. It is the artefact to work
from; this document is the commentary.

---

## What "tractable" does not mean

Be sceptical of the ranking, for three reasons.

**1. The score measures formalizability, not solvability.** A short existential statement
over a finite graph is easy to *state*, and the Erdős problems are not open because they are
easy to state. Erdős 23 — *"can every triangle-free graph on 5n vertices be made bipartite by
deleting at most n² edges?"* — scores well and is a real open problem in extremal graph
theory.

**2. The recent AI successes were not in the high-tractability band.** The Jacobian
conjecture, the Dinitz–Garg–Goemans conjecture and the unit-distance problem were all
*structurally simple and mathematically deep*: the counterexample was short, and finding it
was a search problem over an enormous space. That combination is exactly what a
`tractability` score cannot separate from "this is trivially false". The distinguishing
question is not *how hard is the statement* but **how large is the space of candidate
witnesses and how cheap is it to check one.**

**3. The pool has been audited three times.** Two batches were admitted on 24 August and
8 September 2026, and the 8 September pass retired targets for `SOURCE_MISMATCH`,
`QUARANTINE_DISPUTED_CLAIM` and `TYPE_DEPENDS_ON_SORRY`. The easy formalization errors have
largely been swept. Read [`data/retirements.json`](../data/retirements.json) — all 24
published retirements, with reasons — before you spend a week assuming something has been
overlooked.

---

## Practical filters

```bash
python3 - <<'PY'
import csv
rows = list(csv.DictReader(open("data/targets.csv")))
open_rows = [r for r in rows if r["bounty_available"] == "True"]
print(f"{len(open_rows)} payable targets")

# Start here: never attempted, no historical defect shape, ranked by tractability.
fresh = [r for r in open_rows if r["attempts"] == "0" and not r["defect_signs"]]
fresh.sort(key=lambda r: -float(r["tractability"]))
for r in fresh[:25]:
    print(f'{r["tractability"]:>4}  {r["display_title"]:<45} {r["url"]}')
PY
```

Then, before committing:

1. Run [`scripts/defect_scan.py`](../scripts/defect_scan.py) over your shortlist.
2. Run [`scripts/freshness_check.py`](../scripts/freshness_check.py) to confirm the problem
   has not been settled somewhere else — see
   [`docs/research/target-freshness.md`](research/target-freshness.md).
3. Read the target's page on erdosproblems.com (or Green's document) **in full**, not just
   the docstring. The docstring is a summary; the defect cases were all decided by comparing
   against the full informal record.

---

## On `targets.csv`

| Column | Meaning |
|---|---|
| `slug` | Stable identity. Use it everywhere; task ids change on every weekly re-pin |
| `theorem` | The Lean name, e.g. `Erdos944.erdos_944` |
| `bounty_usd`, `bounty_alpha` | The live quote. Alpha is authoritative |
| `bounty_available` | **The field that decides whether a submission can pay** |
| `attempts` | Submissions so far |
| `tractability` | Ranking heuristic above |
| `defect_signs` | Which historical bug shapes the Lean text resembles — triage only |
| `lean_type` | The exact goal |
| `formalized_task_id`, `counterexample_task_id` | Both modes, with their bundle digests |

The slug outlives the task id on purpose — under the weekly pin rotation **every task id in
the pool changes on every rotation**, even where the statement bytes are identical, because
the id is seeded with the pinned commit. Never bookmark a task id.
