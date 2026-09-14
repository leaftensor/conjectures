# Attack vectors

There are four ways to take money off this subnet. They have very different difficulty,
different payoff, and different paperwork. This is the document that decides what you
actually do on Monday morning.

Read [`docs/04-economics.md`](04-economics.md) alongside it: several of these are worth
much less than the headline number suggests.

---

## The four vectors at a glance

| | Vector | Pays | Difficulty | Evidence it works |
|---|---|---|---|---|
| **A** | Formalization-defect award | **$750**, or the locked bounty if lower | Read the statement very carefully | **5 paid** since 5 Aug 2026 |
| **B** | Counterexample (refute the statement) | Full quote | Hard, but the 2026 wins were all here | Jacobian d3, DGG, unit distance |
| **C** | Proof (prove the statement) | Full quote | Hardest | Erdős 728, 347, 369, 1199, Green 29 |
| **D** | Partial contribution (lemma/tactic) | Share of a pool, **paid only if someone else closes the problem** | Low | Track launched 1 Sept 2026 |

---

## Vector A — Formalization-defect awards

**This is the highest expected-value play on the subnet and it is not a loophole.**

### Why it exists

The subnet does not pay for mathematics. It pays for a Lean kernel accepting a file. Those
are different things, and the design says so out loud:

> The real risk in this design is not that Lean accepts a bad proof — it is that a formalized
> statement does not faithfully capture the original conjecture, which is exactly why we ask
> people to report one that looks wrong.
> — <https://conjectures.io/faq>

The published review policy formalises that risk into a payout. From the validator's
[`docs/MANUAL_REVIEW_CRITERIA.md`](https://github.com/conjectures-io/conjectures-validator/blob/main/docs/MANUAL_REVIEW_CRITERIA.md),
policy `v3`:

> **Formalization-defect award — `FORMALIZATION_DEFECT_AWARD`**
> Use this outcome when: the production verifier accepted the exact committed task; the proof
> or refutation succeeds because the published Lean statement materially differs from the
> intended informal conjecture; the result therefore does not genuinely settle the intended
> conjecture; and no disqualification reason applies.
>
> The miner receives **$750 USD equivalent or the task bounty locked for the submission,
> whichever is less, paid in Subnet 66 Alpha**.

And the policy defines *material* precisely — this is your checklist:

> A material formalization defect includes **an omitted or added hypothesis, an incorrect
> domain or quantifier, the wrong notion of convergence or equality, an incorrect negation,
> or another difference that changes the mathematical problem being solved.**

It is also explicit that leaving the challenge untouched is correct behaviour, not gaming:

> A defect in the task published by the validator is not `TRIVIALISED_STATEMENT` when the
> miner left the challenge unchanged and proved or refuted it exactly. Use
> `FORMALIZATION_DEFECT_AWARD` instead.

**You are not solving the conjecture.** You produce a valid Lean proof of the *published*
`Challenge.lean` whose validity depends on the defect. That is the whole deliverable — and
historically it has been a short proof, not a hard one.

### The complete precedent set

All five defect awards paid to date, from the public results ledger:

| Target | What the defect was | Paid |
|---|---|---|
| Erdős 15 | Informal problem asks for **real** convergence; Lean states `Summable` over **ℚ**. Failure of ℚ-summability is not real divergence | 1,044.29 α |
| Erdős 939 | `Erdos939Sums` omits positivity of summands and `Nat.Full` is vacuous at 0 and 1, so the `r = 4` case — the one with no known example — is discharged by the degenerate set `{0, 1}` | 1,074.75 α |
| Green 42 | `SatisfiesCohnElkiesScheme` omits **continuity** of the test function `f`. Continuity is what makes Poisson summation link `f 0` to `f̂ 0`; without it, `f 0` can be set at a single point. The winning witness was a Gaussian modified only at the origin | 1,074.75 α |
| Erdős 567 part i | Informal problem asks for the ordinary Ramsey number `R(Q₃, H)`; Lean states `SimpleGraph.sizeRamsey Q₃ H` — a different quantity | 1,062.22 α |
| Erdős 726 | Recorded as a defect in the published task | 1,257.22 α |

Plus three more retired on the same grounds that a miner never got paid for, because they
were caught by the audit instead:

| Target | The defect |
|---|---|
| Green 77 | `Erdos507.minTriangleArea` takes an infimum over `Affine.Triangle`, which is **affinely independent points only**. Collinear-heavy configurations were excluded, which refutes the formalized `n^(−2+o(1))` claim by elementary geometry |
| Green 54 | Green asks the question **per-**n on ℝⁿ; the formalization is a single statement on `ℕ → ℝ` with a Gaussian product measure — a non-equivalent setting |
| Erdős 1093 part ii | `Nat.smoothNumbers k` means primes `< k`; erdosproblems.com/1093 defines k-smooth as primes `≤ k` |

Read those seven side by side and the shape of the bug is obvious. **It is almost always an
ambient condition that the informal problem carries in prose and the formalization dropped.**

### The hit rate, honestly

From the public ledger at 14 Sept 2026: **24 submissions, 19 Lean-verified**. Of those 19:

- **8 approved** for the full bounty
- **5 paid a defect award** — 26% of all verified submissions
- **4 rejected** (`NOT_NOVEL`, `DUPLICATE_OF_EARLIER_SUBMISSION`, `PRIOR_EXTERNAL_FORMALIZATION`)
- **2 still unreviewed**

Two warnings about that 26%:

1. **All five defect awards landed 5–6 August 2026**, in the first week. The obvious defects
   have been found, and the pool has since been through two further audits (24 Aug and
   8 Sept). The remaining surface is smaller. Treat 26% as an upper bound on a historical
   rate, not a forecast.
2. The five defect targets are **retired**. Retiring a target removes both of its modes, so a
   defect you find today must be one nobody has found yet, on a target still in the pool.

### How to actually hunt one

The procedure is a semantic diff of three artefacts per target. All three are free and
offline once you have run `scripts/sync_pool.sh`.

```
Erdos944.erdos_944
├─ data/targets.json   ->  .lean_type    the exact Lean statement
│                          .docstring    the informal problem, from the source
└─ https://www.erdosproblems.com/944     the canonical informal record
```

`scripts/defect_scan.py` automates the first pass: it applies the seven historical bug
shapes as filters across the live pool and triages what deserves a human read. It is a
*triage* tool. It cannot certify a defect, and a candidate that survives the scan is a
hypothesis, not a finding.

Then, by hand, ask in this order:

1. **Is every hypothesis the informal problem needs actually in the type?** Continuity,
   positivity, monotonicity, integrality, distinctness, finiteness, non-degeneracy.
   *Green 42, Erdős 939.*
2. **Is the domain the same domain?** ℚ vs ℝ; `ℕ` vs `ℤ`; per-`n` on ℝⁿ vs a single
   sequence; `Finset` vs `Set`. *Erdős 15, Green 54.*
3. **Is the named object the object the informal problem names?** `sizeRamsey` vs `Ramsey`;
   `<` vs `≤`; a different smoothness convention. *Erdős 567, Erdős 1093.*
4. **Is the quantifier order what the prose says?** `∀ n ∃ k` is not `∃ k ∀ n`.
5. **Is the statement vacuous, or trivially satisfiable, on a degenerate case the informal
   problem does not intend?** `0`, `1`, the empty set, the singleton. *Erdős 939, Green 77.*
6. **Is the negation you would have to prove the actual negation?** For counterexample mode
   the `Challenge.lean` is `¬ (fcTypeOfName% "...")`. `¬∀` is `∃¬`. Push the negation through
   by hand before you believe it.

The leanest way to confirm a candidate: **prove the degenerate case in Lean and check the
elaborated goal.** If `{0,1}` discharges the `r = 4` branch, you have your answer.

### What disqualifies you

Read [`docs/08-pitfalls.md`](08-pitfalls.md). In short: do not touch the challenge, do not
restate the theorem, do not import the source theorem, do not `sorry`, and do not pull a
proof from an unmerged pull request. A defect finding is only paid when the submission is a
faithful proof of the frozen published task and nothing else.

---

## Vector B — Counterexample mode

Every one of the 260 targets accepts a refutation. Not a separate prize — one reward
identity per problem, and either direction can claim it. The **`counterexample`** task's
`Challenge.lean` is the same statement with `¬` in front.

**This is where 2026's actual results came from.** Every high-profile settlement this year
was a counterexample found by search, not a proof found by insight:

| Result | Who | Model |
|---|---|---|
| Jacobian conjecture, dimension 3 (open 87 years) | Levent Alpöge | Claude Fable 5 |
| Dinitz–Garg–Goemans (open ~30 years) | Dmitry Rybin | GPT 5.6 Pro |
| Erdős 90, unit distance (open 80 years) | OpenAI, internal | — |
| Erdős 728 | Barreto & Price | ChatGPT 5.2 + Aristotle Lean API |
| Erdős 369 | Sky Yang (17) | verified in Lean |

The reason is structural, and it is the single most useful idea in this document: **a
counterexample is a witness, and a witness can be searched for.** A proof requires an
argument to exist; a refutation only requires an object to exist and to be checkable. IBM's
summary of the Jacobian result is the right framing:

> the Jacobian conjecture was not unsolvable by a human. It's just that the model tried more
> things.
> — <https://www.ibm.com/think/news/ai-cracked-jacobian-conjecture-humans-called-play>

The subnet's own admission policy was written with this in mind. From
[`POOL.md`](https://github.com/conjectures-io/conjectures-tasks/blob/main/POOL.md), every
admitted source must have:

> at least one recorded feasibility signal: a compact target, discrete domain, finite or
> finitary structure, partial results in the same source, or a standard Mathlib surface.

**How to work it**

1. Filter `data/targets.csv` on `tractability` — the script scores finite/decidable domains,
   existential targets, and short statements highest, because those are the ones where a
   search can terminate.
2. Attack the *mathematical* question first, outside Lean: brute force, SAT/SMT, a targeted
   computer search, or a strong general reasoning model looking for a construction.
3. **Then formalize.** This is the part that eats the time and the part that stops most
   attempts. Budget for it: the Lean statement is already written for you, but turning a
   numerical or combinatorial witness into a kernel-checkable term is real work. Existing
   example: [`arex1337/formal-conjectures-proofs`](https://github.com/arex1337/formal-conjectures-proofs).
4. Watch `timeout_seconds = 3600` in the manifest — your proof gets one hour of wall clock.

Full model and harness recommendations: [`docs/research/models-and-harnesses.md`](research/models-and-harnesses.md).

---

## Vector C — Proof mode

Advertised, hardest, and largely what dedicated neural provers are for. Two things make it
more tractable here than it sounds:

- **246 of 260 targets have zero attempts.** Nobody is competing with you.
- **The pool is pre-filtered for a standard Mathlib surface** — the admission policy rejects
  statements that would make you fight the formalization instead of the mathematics.

Stack recommendation, in order of what to try first, is in
[`docs/research/models-and-harnesses.md`](research/models-and-harnesses.md). The short
version: a dedicated prover for the statement, a strong general reasoning model for the
mathematics, and a lean tool-use loop in between — and note the ICML 2026 *ProofGate* audit
finding that at least one prominent prover's released "proofs" are `sorry` placeholders.
Verify any benchmark claim you are about to build a stack on.

---

## Vector D — Partial contributions

Separate repository, separate payout, separate risk profile. A lemma, a definition with its
API, a tactic that closes a recurring goal shape, or a checked search bound. Recognition is
weighted 0–10 by maintainers; **payment happens only after the target is fully closed**, and
then it is shared pro rata.

Full detail: [`docs/07-partial-credits.md`](07-partial-credits.md).

---

## Two rules that decide whether you get paid at all

### 1. Chronology runs from acceptance, not from review

The review policy is unusually explicit, and it cuts both ways:

> Use the validator's paid-submission acceptance time for chronology, not the later
> verification or review time.

> A solution first made public **after** the validator accepted the submission does not
> disqualify the miner. Approve the submission if it otherwise qualifies, even when the two
> proofs are similar.

So: **the submission timestamp is the thing you are racing.** Get a submission accepted
before the competing result is public, and you are safe even if someone publishes the same
result an hour later. Conversely, `DUPLICATE_OF_EARLIER_SUBMISSION` means only the *first*
accepted submission on a reward target can be paid. Two modes, one reward identity: if
someone else takes the proof, the counterexample is gone too.

### 2. Uncertainty is resolved in your favour

Step 9 of the review procedure:

> Unresolved uncertainty favors `REVIEW_APPROVED`.

The same instinct runs through the whole policy — `NOT_NOVEL` requires proving a *concrete
correspondence* between the earlier source and your proof, not merely a shared conclusion,
and:

> If chronology, target match, substantial use, attribution, or independence remains
> genuinely uncertain, do not reject under the corresponding code.

This is not a reason to be sloppy. It is a reason not to talk yourself out of a submission
you believe is right.

---

## What to do first

If you have one week and one target:

1. Run `./scripts/sync_pool.sh`. Take `data/targets.csv`.
2. Drop every target with `bounty_available == False`, and every one on a family the
   retirement log shows has been picked over — especially the seven above.
3. Run `scripts/defect_scan.py` and read the top candidates. Vector A is the cheapest win
   and it is an afternoon of reading, not a research programme.
4. In parallel, take the highest-`tractability` targets and ask a general reasoning model the
   *informal* question — "is this false? find a counterexample" — outside Lean.
5. Only once you have a candidate object or a candidate defect, start the Lean work.
   Formalization is the bottleneck; do not pay it before you have something to formalize.
6. Before you spend 0.25 τ: run `scripts/freshness_check.py` and read
   [`docs/08-pitfalls.md`](08-pitfalls.md).

And then the one non-negotiable step, from the CLI's own documentation: build the verifier
locally and run `conjectures verify` **before** `conjectures pay`. The verifier is free. The
fee is not.
