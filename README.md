# conjectures

A working guide to [conjectures.io](https://conjectures.io) — Bittensor Subnet 66 — for
someone who intends to actually solve something, rather than read about it.

The subnet publishes open mathematical problems as exact Lean 4 statements and pays a
bounty to whoever produces a machine-checked proof **or a machine-checked counterexample**.
This repository is what I worked out from the live API, the pinned task pool, the validator
source, and the reward-review decisions it publishes: what the system really is, which of the
260 targets are worth your time, what a defect is worth, and how to get a submission in
without wasting the fee.

Everything factual here was read from a live endpoint, a repository, or a published decision
record, and every number is dated. Where I could not confirm something I say so.

---

## The sixty-second version

| | |
|---|---|
| **Targets** | 260, all from Google DeepMind's [`formal-conjectures`](https://github.com/google-deepmind/formal-conjectures) — 236 Erdős problems, 24 of Ben Green's Open Problems |
| **Modes** | Every target accepts **both** a proof and a refutation. Two independent bounties? No — one reward identity per problem, two ways to take it |
| **Fee** | **0.25 τ** per submission (TAO), read live from the validator API |
| **Coin** | Payouts are in **alpha** (SN66), not TAO. The USD figures are a display conversion at ~$0.603/α |
| **Headline bounty** | $3,341.58 or $3,809.84 — exactly two tiers, 56 and 197 targets |
| **Defect award** | **$750 or the locked bounty, whichever is less** — for proving the published statement is *not* the intended conjecture |
| **Dedicated provers?** | You will need one, but the counterexample path is where the 2026 wins actually were |

## The five things that matter most

1. **There are two games, not one.** Proving the statement is the advertised game. Finding a
   formalization defect — showing the published Lean statement materially differs from the
   informal conjecture, then discharging *that* — is a second, sanctioned game worth a flat
   $750, and it is an analysis problem rather than an insight problem. It has already been
   played for real money at least five times. → [`docs/03-attack-vectors.md`](docs/03-attack-vectors.md)

2. **The headline bounty is roughly 18× the pool that backs it.** 253 live quotes sum to
   **1,554,110 α ($937,669)** against a treasury of **83,971 α ($50,664)**. The advertised
   number is a share-of-a-pool formula, not a receivable. → [`docs/04-economics.md`](docs/04-economics.md)

3. **The quote you get is set at submission, and it moves.** The validator takes a fresh
   quote at acceptance and subtracts other miners' outstanding locks from the treasury first.
   One target advertised at $3,341 today had **1,130.78 α (≈$682)** locked for the submission
   accepted three days earlier — a 4.9× difference. → [`docs/04-economics.md`](docs/04-economics.md)

4. **Check freshness before you pay.** The subnet retires a target the moment it is settled
   elsewhere, and two submissions were already rejected for exactly that. In 2026 these
   problems are falling fast, in public. → [`docs/research/target-freshness.md`](docs/research/target-freshness.md)

5. **246 of 260 targets have never been attempted.** The catalogue is not crowded. What is
   scarce is a correct Lean formalization, not the idea.

---

## Read in this order

| Document | What it answers |
|---|---|
| [`docs/01-the-system.md`](docs/01-the-system.md) | What the subnet is, how verification works, what the pins mean |
| [`docs/02-problem-catalog.md`](docs/02-problem-catalog.md) | The 260 targets: families, fields, the bounty tiers, what is tractable |
| [`docs/03-attack-vectors.md`](docs/03-attack-vectors.md) | **The strategy.** Defect hunting, counterexample search, proof mode, partial credit |
| [`docs/04-economics.md`](docs/04-economics.md) | Fees, quotes, the treasury overhang, what a win is actually worth |
| [`docs/05-setup.md`](docs/05-setup.md) | Reproducible environment: Lean, the pin, the local verifier |
| [`docs/06-submission-walkthrough.md`](docs/06-submission-walkthrough.md) | The CLI, end to end, with every guard explained |
| [`docs/07-partial-credits.md`](docs/07-partial-credits.md) | The contribution track — lemmas, tactics, search bounds |
| [`docs/08-pitfalls.md`](docs/08-pitfalls.md) | Everything that has already gone wrong for someone else |
| [`docs/research/`](docs/research/) | Cited appendices: models and harnesses, community notes, freshness pipeline |

## Reproduce everything

```bash
./scripts/sync_pool.sh          # live catalog + pinned task pool -> data/ and _research/
python3 scripts/build_catalog.py
```

That produces `data/targets.json`, `data/targets.csv`, `data/summary.json` and
`data/retirements.json` from the live API, so the numbers above can be re-checked rather
than believed.

## What is in here

```
data/           generated: the catalog, the retirements, the summary
docs/           the guide
docs/research/  cited deep-dives (models, community, freshness)
scripts/        sync_pool.sh, build_catalog.py, freshness_check.py
templates/      a submission skeleton and a review checklist
```

## Scope and honesty

This is an independent write-up. It is not affiliated with Conjectures, with Bittensor, or
with DeepMind, and it is not financial advice. The subnet is young — it opened for mining in
early August 2026 — and several of its own documents disagree with each other and with live
endpoints. Those disagreements are recorded here rather than smoothed over, in
[`docs/08-pitfalls.md`](docs/08-pitfalls.md).

Reward eligibility is decided by a human review team applying a published policy. Read that
policy before you spend money; it is quoted at length in
[`docs/03-attack-vectors.md`](docs/03-attack-vectors.md) and
[`docs/07-partial-credits.md`](docs/07-partial-credits.md).

## Licence

MIT for this write-up. The target statements, task bundles and validator source are the
property of their authors and keep their own terms.
