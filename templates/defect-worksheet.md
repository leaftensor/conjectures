# Formalization-defect worksheet

Print this. Fill one in per candidate, **before** you spend anything. The paid defect awards
were all found by doing this read carefully, and the wasted weeks were all spent writing Lean
first.

The question this worksheet answers is *not* "is this conjecture false". It is:

> **Does the published Lean statement mean what the informal conjecture means?**

If it does not, proving the Lean statement — which is usually far easier than proving the
conjecture — earns the defect award. See [`docs/03-attack-vectors.md`](../docs/03-attack-vectors.md).

---

## Target

| | |
|---|---|
| Slug | |
| Theorem | |
| Task id (note the **mode**) | |
| Informal problem URL | `https://www.erdosproblems.com/` |
| Lean type | |

```
<paste the full Lean type from Challenge.lean here>
```

```
<paste the informal statement, verbatim, from erdosproblems.com -- not the docstring>
```

---

## The six questions

Tick each one. A "no" on any of the first three is a strong candidate.

### 1. Ambient conditions

The informal problem carries conditions in prose. The formalization must carry all of them.

| Condition | In the prose? | In the Lean type? | Verdict |
|---|---|---|---|
| Continuity | | | |
| Positivity / non-negativity | | | |
| Monotonicity | | | |
| Integrality / distinctness | | | |
| Finiteness / boundedness | | | |
| Non-degeneracy (excludes 0, 1, ∅, singletons) | | | |
| Other: | | | |

*Precedent: Green 42 — `SatisfiesCohnElkiesScheme` omitted continuity of `f`. Paid.*

### 2. Domain

| | |
|---|---|
| Domain the prose means | |
| Domain the Lean type quantifies over | |
| Same? | |

Watch for: ℚ vs ℝ · `ℕ` vs `ℤ` · `Finset` vs `Set` · per-`n` on ℝⁿ vs a single `ℕ → ℝ`
statement · a bounded `Finset.range` where the prose means all `n`.

*Precedent: Erdős 15 (ℚ `Summable` vs real convergence, paid) · Green 54 (per-`n` ℝⁿ vs a
product-measure statement, retired).*

### 3. Named objects

Every library name in the type has a definition. Read it.

```lean
#print <the name>
#check <the name>
```

| Declaration in the type | What it actually means | What the prose means | Same? |
|---|---|---|---|
| | | | |
| | | | |

Watch for: `sizeRamsey` vs `Ramsey` · `Nat.smoothNumbers k` (primes `< k`) vs k-smooth
(primes `≤ k`) · `Affine.Triangle` (affinely **independent** only) · `<` vs `≤` · any
convention the source defines differently.

*Precedent: Erdős 567 part i (`sizeRamsey` vs `R(Q₃,H)`, paid) · Erdős 1093 part ii
(`<` vs `≤`, retired) · Green 77 (`Affine.Triangle` excludes collinear, retired).*

### 4. Quantifier order

| | |
|---|---|
| Prose | |
| Type | |
| Same order? | |

`∀ n ∃ k` is not `∃ k ∀ n`. For asymptotic statements, which variable is under `atTop`?

*Precedent: Green 72 — the published target asserted a size for **every** N, while the
informal question asks about **large** N. Withdrawn.*

### 5. Degenerate cases

Substitute each and check whether the statement becomes vacuous or trivially true.

| | Result |
|---|---|
| `0` | |
| `1` | |
| `∅` | |
| A singleton | |
| The smallest legal instance | |

*Precedent: Erdős 939 — `Nat.Full` is vacuous at 0 and 1, so the case with no known example
was discharged by `{0, 1}`. Paid.*

### 6. The negation (counterexample mode only)

```
¬ (published type)   =   ???
```

Push it through by hand. `¬∀` is `∃¬`. Write the resulting goal out in full and confirm it is
the thing the informal problem asks you to refute.

*If you are in `formalized` mode, skip this — but confirm you pinned the right mode.*

---

## Verdict

- [ ] **Defect candidate.** Which question failed, and what exactly differs:

  ```
  ```

- [ ] **Statement looks faithful.** The Lean means the prose. Then this is a real problem and
      you should decide whether to attack it on the mathematics
      ([Vector B/C](../docs/03-attack-vectors.md)) or move on.

- [ ] **Not sure.** Then do not submit. A rejected submission costs 0.25 τ and earns nothing,
      and the review policy will not pay a defect you cannot state concretely.

---

## If it is a defect candidate

1. **Prove the published statement.** Not the conjecture. Usually the degenerate case, the
   dropped hypothesis, or the weakened domain makes it short.
2. **Sanity-check season.** Before paying, search whether anyone has already reported it —
   the Bittensor Discord channel, and `data/retirements.json`.
3. **Expect $750, not $3,800.** The award is the lesser of $750 and the bounty locked at
   submission. Under policy `v3` that cap is live.
4. **Say what you proved.** The review outcome is published with a rationale, and the policy
   requires the public explanation to state that the miner received the capped defect award —
   not that the conjecture was settled.
5. **Report it even if you do not submit.** The FAQ asks for it directly: the mismatch is "the
   one real risk in the whole system", and they would rather hear about it before someone
   spends weeks on it.

---

*Sources for the precedents: [`data/retirements.json`](../data/retirements.json) (24 published
retirements with reasons) and the validator's
[`docs/review-decisions/`](https://github.com/conjectures-io/conjectures-validator/tree/main/docs/review-decisions).*
