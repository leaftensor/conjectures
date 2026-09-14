# Worked example: Green's Open Problem 12

A complete run of the process in [`docs/03-attack-vectors.md`](03-attack-vectors.md), from
target selection to a machine-checked artifact — including the parts that did not work.

**Outcome, stated plainly: the open problem is NOT solved.** What was produced instead is a
genuine, machine-verified **partial result**, plus a validated computational search showing
the published bound is tight and unviolated on everything reachable. Both are in this
repository and both can be re-run. The target can still not be submitted for a bounty, because
no submission closes it.

---

## The target

| | |
|---|---|
| Target | Green's open problem 12 (`Green12.green_12`) |
| Slug / URL | `green12-green-12` — <https://conjectures.io/problems/green12-green-12> |
| Formal mode task | `fc-8432eac9-green-12-…-formalized-v1` |
| Bounty | 6,314.50 α (tier 1) |
| Attempts | 0 |
| Field | AMS 5 11 — combinatorics / number theory |

The published statement, verbatim from the frozen pool:

```lean
theorem green_12 : answer(sorry) ↔
    ∀ {G : Type*} [AddCommGroup G] [Fintype G] [DecidableEq G],
    ∀ (A : Finset G),
    let N := Fintype.card G
    let α := (A.card : ℝ) / N
    let valid_tuples : Finset ((Fin 5 → G) × (Fin 5 → G)) := Finset.univ.filter (fun t =>
      ∀ i : Fin 5, ∀ j ∈ ({i, i + 1, i + 2} : Finset (Fin 5)), t.1 i + t.2 j ∈ A)
    (valid_tuples.card : ℝ) ≥ α ^ 15 * (N : ℝ) ^ 10 := by
  sorry
```

Informally: in an abelian group of size `N`, a subset `A` of density `α` should support at
least `α^15 N^10` of the `N^10` tuples `(x, y) ∈ G^5 × G^5` satisfying `x_i + y_j ∈ A`
whenever `j ∈ {i, i+1, i+2}` (indices mod 5).

`answer(sorry)` elaborates to `True` — confirmed in
`FormalConjecturesUtil/Answer.lean`, *"Default mode: `answer(sorry)` defaults to `True` when
`sorry` has type `Prop`"* — which is why the pool's rendering reads `True ↔ …`.

## Why this target

Selection followed the guide's own procedure, and each step changed the choice:

1. **Freshness came first.** `bounty.available: true`, `attempts: 0`. Still worth attacking.
2. **The defect scan was used as intended — as triage, and it produced a negative.** The ~50
   flagged candidates were read against their raw sources and **every one checked was
   faithful**: Green 24's `gamma = 1/3` is `limsup (max013AffineTranslates n / n²) = 1/3`, not
   a vacuous equation; Green 62's `↑x = ↑a₁ * ↑a₂` coerces to `ZMod p`, so it *is* the
   informal "congruent" claim; Erdős 244 really does quantify `C : ℝ, C > 1`; Green 32 really
   does use `⌊√p⌋`. This is the expected outcome — the pool has been audited three times — and
   it is the single most useful thing the guide can say about Vector A.
3. **Green 12 was chosen because it is computationally falsifiable.** The target is a
   *counting* statement over *finite abelian groups*, with a fully explicit constant `α^15
   N^10`. A counterexample is a pair `(G, A)` that a machine can certify. That is the
   "counterexample = a witness that can be searched for" principle from the guide, and it
   needs no insight to test.

---

## Step 1 — the search, and its validation

Naive enumeration is `N^10`, which is hopeless past `N = 5`. But **fix `x`**: then `y_j` is
constrained only by the three indices `i` with `j ∈ {i, i+1, i+2}`, i.e. `i ∈ {j−2, j−1, j}`.
The five constraints on `y` are independent given `x`, so

```
count(x) = ∏_{j=0..4}  | ⋂_{i ∈ {j−2,j−1,j}} (A − x_i) |
```

which makes the total `N^5 · O(N)` instead of `N^10`, and lets every subset of `Z/nZ` be swept
for `n ≤ 9`. The intersections are integer bitmask ANDs.

**A search is worthless until its counter is checked**, and this one was:

- `scripts/green12_search.py` validates the optimised count against a naive `N^10` enumeration
  on **every** subset of `Z/nZ` for `n ≤ 3`, and on a sample at `n = 4` — the largest that
  brute force reaches in Python.
- Then, independently, against **Lean's own kernel reduction**. `lean/Green12CrossCheck.lean`
  is a `#eval` file that recomputes `valid_tuples.card` inside the pinned toolchain. All ten
  values agree exactly:

  | Group | `A` | Lean `#eval` | Python |
  |---|---|---|---|
  | `Z/2` | `{0}` / `univ` / `∅` | 2 / 1024 / 0 | 2 / 1024 / 0 |
  | `Z/3` | `{0}` / `{0,1}` / `univ` | 3 / 306 / 59049 | 3 / 306 / 59049 |
  | `Z/4` | `{0}` / `{0,1}` / `{0,2}` / `{0,1,2}` | 4 / 408 / 2048 / 17532 | 4 / 408 / 2048 / 17532 |

## Step 2 — the search result: no counterexample

`scripts/green12_search.py` sweeps **every subset** for `n ≤ 9`. `scripts/green12_focus.py`
targets the regime where the bound can actually fail (see the theorem below for why the
bound is free at low density), scanning `k` from `N^{3/5}+1` to `N−1` with structured sets —
intervals, arithmetic progressions, subgroups, complements, and random samples:

| `N` | `k` range | min `count / bound` | at `k` | verdict |
|---|---|---|---|---|
| 3 | 2–2 | 2.2692 | 2 | ok |
| 4 | 3–3 | 1.2512 | 3 | ok |
| 5 | 3–4 | 1.0922 | 4 | ok |
| 6 | 3–5 | 1.0443 | 5 | ok |
| 7 | 4–6 | 1.0248 | 6 | ok |
| 8 | 4–7 | 1.0153 | 7 | ok |
| 9 | 4–8 | 1.0101 | 8 | ok |
| 10 | 4–9 | 1.0071 | 9 | ok |
| 11 | 5–10 | 1.0051 | 10 | ok |
| 12 | 5–11 | 1.0038 | 11 | ok |

**No counterexample.** And the pattern is informative rather than merely negative: the minimum
ratio is always attained at `k = N − 1` (that is, `A = G` minus a single element) and marches
toward 1 as `N` grows — `1.25, 1.09, 1.04, 1.025, 1.015, 1.010, 1.007, 1.005, 1.0038`.

So the published bound is **tight**, and the extremal set is the complement of a singleton. The
statement is very likely true, and the remaining gap is a genuine mathematical gap rather than
a formalization artifact.

## Step 3 — the theorem that is actually proved

Reading the constant term of the count gives a lower bound that needs no search at all.

**Take `x` constant, `x = (a,a,a,a,a)`.** Then every constraint becomes `a + y_j ∈ A`, i.e.
`y_j ∈ A − a`, and `y` is unconstrained beyond that. So that one `x` contributes exactly
`|A|^5` valid tuples, and distinct `a` give distinct `x`:

```
count  ≥  N · |A|^5
```

Since the required bound is `α^15 N^10 = |A|^15 / N^5`, the inequality holds whenever

```
N · |A|^5  ≥  |A|^15 / N^5   ⟺   |A|^5 ≤ N^3   ⟺   |A| ≤ N^(3/5)
```

**So Green 12 is settled for all groups and all `A` with `|A| ≤ N^(3/5)`.**

That is machine-checked in [`lean/Green12Partial.lean`](../lean/Green12Partial.lean):

```lean
theorem card_validTuples_ge (A : Finset G) :
    Fintype.card G * A.card ^ 5 ≤ (validTuples A).card

theorem bound_of_small_card (A : Finset G)
    (h : (A.card : ℝ) ^ 5 ≤ (Fintype.card G : ℝ) ^ 3) :
    ((validTuples A).card : ℝ)
      ≥ ((A.card : ℝ) / (Fintype.card G : ℝ)) ^ 15 * (Fintype.card G : ℝ) ^ 10
```

The proof is a Fintype-level injection
`(a, y) ↦ ((a,a,a,a,a), y − a)` from `G × (Fin 5 → A)` into the valid tuples — about 60 lines,
and the only subtle part is that `a + (y_j − a) = y_j`.

**Verification actually performed**, not asserted:

```bash
cd _research/formal-conjectures
lake env lean /path/to/lean/Green12Partial.lean
```

- Compiles with **no errors and no warnings** under `leanprover/lean4:v4.27.0`, the pinned
  toolchain.
- `#print axioms` on both theorems reports exactly `[propext, Classical.choice, Quot.sound]` —
  **the same three axioms the pool's machine contract permits**, and no `sorryAx`.
- The constants and the `{i, i+1, i+2}` index pattern were checked against the *frozen*
  statement, not against the API's pretty-printed rendering (see
  [`docs/08-pitfalls.md`](08-pitfalls.md) §16 for why that distinction cost real time).

Two independent confidences, then: the search agrees with the kernel on ten computed counts,
and the theorem agrees with the kernel on its axiom closure.

---

## What this is worth, honestly

**To the subnet: nothing directly.** There is no partial-credit path via the validator, and the
target is not closed, so no bounty is payable. Do not read this as a template for getting paid.

**As a contribution: plausibly something.** `|A| ≤ N^(3/5)` is a real, reusable lemma for
Green 12, and `N · |A|^5 ≤ count` is the kind of checkable bound the contribution track
explicitly rewards ("a counterexample search with the bound it establishes"). Both are
axiom-clean and self-contained. That track only pays if someone else closes the target, which
may never happen.

**As evidence about the pool:** three things worth carrying forward.

1. **The defect well is dry on the candidates that look like history.** Every flagged target
   read in full was faithful. The five paid awards were in the first week; the three audit
   passes since have done their job.
2. **The open problems are actually open.** Green 12's bound is tight to within 0.4% at
   `N = 12`, no counterexample exists in the reachable range, and the remaining regime
   `|A| > N^(3/5)` is not a formalization slip but the hard part.
3. **"Computationally falsifiable" is still the right filter.** It did not produce a bounty
   here, but it converted a hostile 260-target catalogue into one target with a definite,
   checkable answer and a proof that came out of it — in an afternoon, with no GPU.

---

## Reproducing

```bash
bash scripts/setup_lean.sh                                    # Lean v4.27.0 + Mathlib, ~15 min
cd _research/formal-conjectures
lake env lean ../../lean/Green12Partial.lean                  # the theorem + axiom audit
lake env lean ../../lean/Green12CrossCheck.lean               # Lean's own counts

cd /Users/leaf/Work/conjectures
python3 scripts/green12_search.py 4                           # counter validation vs naive
python3 scripts/green12_search.py 9                           # exhaustive, every subset
python3 scripts/green12_focus.py 12                           # the tight regime
```

`scripts/setup_lean.sh` records one thing worth knowing: **the subnet's pinned commit
`8432eac9…` does not resolve on either public `formal-conjectures` remote** — `git cat-file -t`
fails with *"not our ref"* on both. The fork's `HEAD` is used instead, and its `lean-toolchain`
is `leanprover/lean4:v4.27.0`, matching the subnet's pin. So the Lean semantics are identical
even though the statement bytes are from a nearby commit rather than the frozen one.
