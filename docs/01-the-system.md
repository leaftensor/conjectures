# The system

What conjectures.io actually is, mechanically, without the marketing.

---

## The one-paragraph version

Conjectures is **Bittensor Subnet 66**. It publishes open mathematical problems as exact Lean 4
statements, frozen as immutable task bundles, and pays a bounty to anyone who submits a Lean
file that a pinned kernel accepts against one of those bundles. There is no mining UID to
compete for, no registration, and no scoring function to game: you pay a flat fee per
attempt, you get one verification, and a machine decides. It is closer to a
bounty board with a mechanical referee than to a Bittensor subnet in the usual sense.

---

## What is actually decentralised

Worth being precise, because it is not what the word usually implies here.

| Component | Decentralised? |
|---|---|
| Who may submit | **Yes** — permissionless, no UID, no hotkey registration |
| Whether a proof is valid | **Yes** — Lean's kernel, deterministic, reproducible by anyone |
| What the statement means | **No** — taken verbatim from Google DeepMind's `formal-conjectures` |
| Which targets exist | **No** — deny-by-default admission, team-audited |
| Whether you get paid | **No** — human review against a published policy, 2-of-3 multisig release |
| The bounty amount | Formulaic — `share × uncommitted treasury`, read live |

The genuine decentralisation is at the verification step, and it is real: the kernel check is
mechanical and the CLI ships the validator's own verifier so you can reproduce the verdict
locally before spending anything. Everything else — the pool, the admission, the review,
the payout — is operated by a team. That is not a criticism, it is the thing to plan around.

---

## The seven steps, as published

From <https://conjectures.io/how-it-works>:

1. **Pick a problem.** Each entry has an exact Lean type, a challenge file, and references.
2. **Attack it however you like.** Any model, any compute, any method.
3. **Check your file for free.** A static policy check reports whether the file will even
   build, with line and column.
4. **Pay.** One transfer per attempt. A submission is only created once the transfer is
   confirmed on finalised chain state.
5. **The kernel decides.** Lean verifies against the pinned toolchain in a sandbox.
   **Fourteen gates** must pass, including that the statement was not altered and that only
   permitted axioms were used.
6. **A human reviews it.** Acceptance by Lean is necessary, not sufficient.
7. **The bounty is paid** from the treasury multisig.

Step 5 is the one to internalise: it is not "does your proof compile". Your submitted
`Main.lean` is inserted between a trusted header and footer, compiled, and then the
*canonical type of `Bounty.target`* is compared against the task's recorded hash. You cannot
weaken, restate or re-scope the theorem.

---

## The pin

Everything is pinned, and the pin rotates — roughly weekly, on a Tuesday. At the time of
writing:

| Component | Pin |
|---|---|
| Formal Conjectures | `8432eac998110a563e03df65a28c117e97c8c142` |
| Lean | `leanprover/lean4:v4.27.0` |
| Mathlib | `a3a10db0e9d6` |
| Comparator | `68a064109f01` |
| nanoda (second kernel) | `f58f2f6d535e` |
| Sandbox | Landrun + seccomp |

**A rotation pauses submissions.** Most rotations only attach a newer toolchain to an
unchanged statement and nothing about your work changes. If a formalization was *materially*
updated, work against the old version has to start again. Check before starting a long
session:

```bash
conjectures status      # includes pin_rotation_in_progress and pin_rotation_starts_at
```

The pinned tasks commit is also the reason **task ids are not stable** — every id in the pool
changes on every rotation, because the id is seeded with the commit. Slugs are stable; ids are
not. Bookmark slugs.

---

## Both modes, always

Every target exists twice:

```lean
-- formalized/Challenge.lean
theorem target : fcTypeOfName% "Erdos944.erdos_944" := by sorry

-- counterexample/Challenge.lean
theorem target : ¬ (fcTypeOfName% "Erdos944.erdos_944") := by sorry
```

One reward identity per problem, two ways to claim it. `DUPLICATE_OF_EARLIER_SUBMISSION`
means only the first accepted submission on a reward target can be paid — so taking one
direction closes the other for everybody.

---

## What your file may contain

This trips people up, so it is worth stating flatly. `Main.lean` holds **declarations only**.
It is inserted between a trusted `SolutionHeader.lean` (which supplies the imports and opens
`namespace Bounty`) and a `SolutionFooter.lean`. Therefore an `import` line of your own is a
**refusal, not a duplicate**.

Refused outright: `sorry`, `admit`, `axiom`, `set_option`, `native_decide`, `instance`,
attributes, `macro`/`syntax`/`notation`, `unsafe`, `IO`, `#eval`, and **any reference to the
source theorem** (`forbidden_dependencies: ["Erdos944.erdos_944"]`).

Permitted axioms, and only these:

```
propext, Quot.sound, Classical.choice
```

For example, a full submission against Erdős 944 is exactly:

```lean
theorem target : fcTypeOfName% "Erdos944.erdos_944" := by
  -- your proof, using only what the header imported
  sorry  -- placeholder: this will be refused
```

Twelve gates are itemised in the public verification report for every accepted submission —
manifest validity, trusted hashes, submission policy, sandbox self-test, challenge build,
source type hash, solution build, statement unchanged, permitted axioms, kernel acceptance,
plus nanoda and the second-kernel check where the task requires it. `enable_nanoda` is
`false` on the tasks I sampled, so most verdicts rest on **a single kernel implementation**.

---

## Where the targets come from

`formal-conjectures` — a public repository DeepMind maintains, where each formalization is
reviewed before merge. The subnet's admission is downstream of that:

> Each statement is marked research open at the source revision it is pinned to, and
> cross-checked against the upstream problem record. Anything already settled, or with a
> resolution in flight, is dropped.

There is **no partnership or endorsement** — the FAQ says so explicitly. The subnet relies on
the upstream review to have established that each Lean statement means what the conjecture
means, and that reliance is the acknowledged weak point of the whole design. It is also why a
formalization defect pays $750 — see [`docs/03-attack-vectors.md`](03-attack-vectors.md).

---

## Roles, and why there is no mining

The FAQ is unusually blunt about this:

> Thinner roles than the words suggest. A miner carries the submitted Lean file and signs its
> commitment; the reference miner does not even ship a proof generator.

So: no UID to buy, no hotkey registration, no weight competition, no emissions for doing
model work. You are a person with a Lean file and a wallet. The validator sets weights 100%
to the treasury UID (`UID 121` in the repo's own description). This is why almost everything
in this guide is about *mathematics and Lean*, and almost nothing is about mining
infrastructure.

---

## Read next

- The exact API and every published policy: the validator repository,
  <https://github.com/conjectures-io/conjectures-validator>, especially `README.md`,
  `docs/PUBLIC_API.md`, `docs/MANUAL_REVIEW_CRITERIA.md` and `docs/SUBMISSION_TERMS.md`.
  `docs/review-decisions/` is the most interesting directory in the whole ecosystem — it
  contains the worked reasoning for the defect awards.
- What to attack: [`docs/02-problem-catalog.md`](02-problem-catalog.md) and
  [`docs/03-attack-vectors.md`](03-attack-vectors.md).
