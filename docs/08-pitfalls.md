# Pitfalls

Everything that has already cost someone money, plus the places where the subnet's own
documents disagree with each other and with the live system. Each entry is either a documented
rejection, a published retirement, or a discrepancy I observed and dated.

Read this before you pay for anything.

---

## 1. The target was already solved — and nobody told you

The most expensive failure mode, because you can do everything right and still get nothing.
Three submissions to date were rejected on these grounds:

| Target | Rejection reason |
|---|---|
| Green's open problem 44 | `Already formalized elsewhere` |
| Green's open problem 3 | `Already solved before this submission` (twice, two different hotkeys) |
| Erdős problem 10 - grechuk | `SOLVED + NOT_OPEN` at retirement — the informal claim follows from Crocker's published theorem |

The subnet says so itself, in the FAQ:

> A problem resolved outside the subnet is retired from the pool and no bounty is payable on it.
> We check for this by hand today and intend to have an agent watching for published solutions;
> until that is running, the gap between a result appearing elsewhere and the problem being
> retired is real and is on us.

**And 2026 is a bad year to be on the wrong side of that gap.** DeepMind reported resolving 9
of 353 open Erdős problems autonomously at a few hundred dollars each; OpenAI's internal model
disproved the unit-distance conjecture; Erdős 728, 347 and 369 all fell; Erdős 1199 and
Erdős 126 were both retired from this pool after outside proofs appeared.

**Mitigation:** run [`scripts/freshness_check.py`](../scripts/freshness_check.py) before
submitting, and read [`docs/research/target-freshness.md`](research/target-freshness.md).

**The escape hatch:** chronology runs from the **acceptance time** of your paid submission, not
from when it is reviewed. A solution made public *after* acceptance does not disqualify you,
*even if the two proofs are similar*. So the race is winnable — submit early, do not polish.

---

## 2. Someone else's submission got there first

`DUPLICATE_OF_EARLIER_SUBMISSION`. One reward identity per problem, so the first *accepted*
submission wins and both modes close behind it. This is why the validator stops serving both
task ids once a submission is accepted (I measured this: six targets are withheld from the
live task list right now, and both modes are withheld together).

There is no defence except speed and checking `attempts` in `data/targets.csv` first.

---

## 3. You submitted the wrong mode

> The tool prints the mode you are answering back to you - getting this backwards is a refusal
> after the money has moved.

Both modes share a slug, so `conjectures tasks show erdos944` is a genuine ambiguity error.
Pin the mode.

---

## 4. Your proof was valid but the reward was not the headline

The **formalization-defect award** is a real outcome, not a rejection, and it pays $750 or the
locked bounty, whichever is less. Five submissions have received it. If you prove the
published `Challenge.lean` and the published statement turns out not to mean the informal
conjecture, you get a defect award, **not** $3,800.

Also note the policy versioning: submissions accepted under policy `v1`/`v2` keep a **fixed,
uncapped $750**; the `v3` policy (effective 11 September 2026) caps at the submission-time
bounty lock. Existing payout records are not repriced. The policy version captured at
acceptance is your contract.

---

## 5. A defect award is capped by a number you did not look at

Because the cap is the bounty **locked for the submission**, and the locked amount is a fresh
quote taken at acceptance with other miners' outstanding locks subtracted, a defect found in a
busy week pays less than one found in a quiet one. Measured case: Erdős 944 was quoted at
5,538.46 α on 14 September, but the submission accepted on 11 September locked only
**1,130.78 α**. See [`docs/04-economics.md`](04-economics.md).

---

## 6. The overhang

253 live quotes sum to **1,554,110 α ($937,669)** against a treasury of **83,971 α
($50,664)** — **18.5× over-committed**. The quote is a share-of-pool formula, not a balance.
Expect the payout to be what the treasury can cover, not the number on the card.

Payouts are signed manually from a 2-of-3 multisig; the validator's own status shows an
`awaiting_reward` queue.

---

## 7. The fee is not what three of the four sources say

| Source | Claimed fee |
|---|---|
| Validator `README.md` | 0.5 TAO |
| <https://conjectures.io/how-it-works> | 0.5 τ |
| A third-party write-up | 0.25 τ |
| **Live validator API (`/v1/catalog/meta`, `tasks sync`)** | **0.25 τ (250,000,000 rao)** |

The live API is what charges you. Assume any document can be stale for money-relevant values
and read the endpoint. Same applies to the bounty: `/v1/catalog/meta` also reports
`credit_price_rao` and the treasury balance directly.

---

## 8. `is_open` does not mean what it says

`GET /v1/catalog/conjectures` returns **`is_open: true` for all 260 targets**, including the 7
whose bounty returns `available: false, reason: "ALREADY_SOLVED"`. Filter on
**`bounty.available`**, never on `is_open`. A submission against an unavailable target is a
wasted fee.

Likewise `/problems` on the website still renders cards for retired and solved targets — six
of them show a `SOLVED` badge and `BOUNTY / -`.

---

## 9. Task ids are not stable; slugs are

Under the weekly drain-and-rotate pin policy **every task id in the pool changes on every
rotation**, even where the statement, docstring and Lean bytes are byte-identical, because the
id is seeded with the pinned commit:

```
fc-{repository_commit[:8]}-{slug}-{digest}-{mode}-v{adapter_version}
```

Since the tasks commit changes weekly, the first eight characters change weekly. Bookmark the
**slug** (`erdos944-erdos-944`), never the id.

A rotation also **pauses submissions**, so check `conjectures status` before a long session.

---

## 10. The Lean you write will probably fail, and the fee does not come back

Ledger to date: 24 submissions, **19 verified**, **5 Lean-rejected**. And credits are
explicitly non-transferable and non-refundable to TAO.

The mitigation is free and most people skip it: `conjectures verify --setup` builds the
validator's own verifier locally, and `conjectures verify` runs your exact sealed upload
through it. That is the difference between a 0.25 τ rejection and a 0.25 τ acceptance.

Watch the exit codes: `0` accepted, `1` rejected, **anything else means no verdict was
reached**. A broken host is not a wrong proof.

---

## 11. Benchmark claims about theorem provers are not reliable

The ICML 2026 paper *ProofGate* audits released proof artefacts from state-of-the-art Lean
provers and reports, among other findings, that **Goedel-Prover-V2's released "proofs" for
miniF2F are the benchmark input statements with `sorry` placeholders** — the public release
contains no auditable proofs, a property the accompanying paper does not state explicitly.

The same paper's kernel audit of DeepSeek-Prover-V2 did find the artefacts faithful. The
lesson is not "one lab is dishonest"; it is that **reported miniF2F numbers conflate
faithfulness, statement alignment and vacuity**, and that if you are choosing a model to build
a workflow on, you should check the released artefacts rather than the headline pass rate.

Detail and citations: [`docs/research/models-and-harnesses.md`](research/models-and-harnesses.md).

---

## 12. The corpus is contaminated, and the pool is pre-sorted

These are famous problems with decades of published commentary. Any model trained after 2024
has almost certainly seen discussion of them, and some of the pool's targets have *published
partial results in the same source* — which is deliberately one of the admission criteria.
Pass rates on these targets are not a clean measure of reasoning.

This cuts both ways: it makes the mathematics easier to search and it makes a model's
confident output less trustworthy. Verify in Lean, not in the chat window.

---

## 13. The pool's own audit is still moving

Do not treat the pinned pool as settled. In the last two months:

- 24 August 2026 — a batch of candidates admitted after review.
- 1 September 2026 — the partial-contribution bounty track launched.
- 8 September 2026 — a pool review that retired targets for `SOURCE_MISMATCH`,
  `TYPE_DEPENDS_ON_SORRY` and `QUARANTINE_DISPUTED_CLAIM`.
- 9–11 September 2026 — six submissions from one hotkey; the team committed to a bounty-formula
  rework "to more evenly reward problems and disincentivize waiting to submit as bounties rise".
- **The team has confirmed there will be no retroactive rewards on a problem already solved**
  — so do not wait for a bounty to rise.

Full retirement log with reasons: [`data/retirements.json`](../data/retirements.json). Every
entry is a mistake someone already made.

---

## 14. Quarantine is not solved

`QUARANTINE_UNVERIFIED_CLAIM` and `QUARANTINE_DISPUTED_CLAIM` retirements mean a third party
*claimed* a solution that nobody has confirmed. Five targets are in this state — Erdős 1059,
Erdős 12 part iii, Erdős 242, Erdős 727 variant k=2, Erdős 96. The subnet withholds them
conservatively.

Two of these are worth knowing because they show the review process is not credulous:

- Erdős 12 part iii: the public claim "identifies an assumed `growth_ineq` axiom and requests
  the missing block-growth argument. It does not constitute an unconditional proof."
- Erdős 96: quarantined on 8 September, then **reinstated on 10 September** after review —
  and a proof of it was approved two days later. Quarantine is reversible in both directions.

If you are working a quarantined target, you are working a target that pays nobody until the
claim is adjudicated.

---

## 15. Small things that cost real money

- **An `import` line in `Main.lean` is a refusal, not a duplicate.** The header supplies them.
- **A `sorry` anywhere kills the free policy check** — and the tool will tell you, before you
  pay, with line and column.
- **Do not edit `Challenge.lean`.** Those bytes are hashed into the task bundle.
- **Your proof gets 3600 seconds** (`timeout_seconds` in the manifest). A search that needs
  longer needs to be done outside Lean, with the result certified inside it.
- **Most tasks do not run a second kernel.** `enable_nanoda: false` on the tasks I sampled, so
  the verdict rests on a single kernel implementation. There is a history of kernel-level
  exploits in this space; if you find one, that is an `ABUSE` rejection, not a bounty.
- **Seven-day pin rotation on Tuesdays**, and submissions pause during it.

---

## Checklist before you pay 0.25 τ

```
[ ] bounty.available is true, read from /v1/catalog/conjectures TODAY
[ ] attempts is still 0 (or you know who the other attempt was)
[ ] freshness_check.py says OPEN on erdosproblems.com and arXiv
[ ] you pinned the correct MODE
[ ] defect_scan.py was read, and you compared the Lean type against the full informal record
[ ] Main.lean has no import, no sorry, no axiom, no instance, no attribute, no source reference
[ ] conjectures verify  -> exit 0
[ ] conjectures check   -> exit 0
[ ] conjectures status  -> submissions_open: true, pin_rotation_in_progress: false
[ ] you re-read the bounty quote and accepted the number it actually says
```
