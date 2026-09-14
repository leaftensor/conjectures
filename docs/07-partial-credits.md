# Partial credits

The second payout track, launched 1 September 2026. It pays for Lean that helps *someone else*
close a target — a lemma, a definition, a tactic, a checked search bound.

**Read the deferred-payment rule before you invest a week here:**

> A payment obligation exists only when the target has been formally settled by an accepted
> validator proof or refutation and the operator publishes a signed payout event naming that
> accepted result.
> — [`contribution-contract.md`](https://github.com/conjectures-io/conjectures-contribution/blob/main/contribution-contract.md)

You are not paid when your contribution merges. You are paid **if and when the target is
closed**, pro rata with everyone else recognized on it. A merge is "a permanent publication
record, not a promise of recognition or payment."

---

## Where it lives, and why not the other repo

Two repositories, and mixing them up is the commonest mistake:

| Repository | Use it for |
|---|---|
| [`conjectures-tasks`](https://github.com/conjectures-io/conjectures-tasks) | **Read only.** The pinned pool: `Challenge.lean`, manifests, metadata, references |
| [`conjectures-contribution`](https://github.com/conjectures-io/conjectures-contribution) | **Submit here.** Partial contributions, as pull requests |

Do not open a contribution pull request against `conjectures-tasks`. A **target** is a problem
(`erdos-944`), not a task bundle — both bundles sit under it and the payload's `mode` says
which side you are helping.

Full solutions do **not** go here. They go to the validator.

---

## Setup

```bash
git clone --recurse-submodules https://github.com/conjectures-io/conjectures-contribution
cd conjectures-contribution
./install.sh
```

The recursive clone pins the task pool at `conjectures/`. Treat it as read-only.

```bash
contrib config set wallet_name my-wallet
contrib config set wallet_hotkey my-hotkey
contrib wallet show
```

`contrib` owns `~/.config/conjectures/contribution.toml` and does **not** read the miner CLI's
`config.toml`. **The author key and the reward wallet are separate on purpose** — see
`docs/identity.md` in that repository.

---

## Before you write anything

```bash
# What is already there for this target?
contrib ls contributions --target erdos-944

# Has anyone in the whole repository declared this name?
contrib ls contributions --declares '*Name*'
```

> Ask before you write: duplicating an existing contribution earns nothing, and `C015` rejects
> a byte-identical resubmission outright.

Two more checks that are easy to skip and expensive to miss:

1. **A target directory can exist while the target is retired.** `conjectures/allowlist.json`
   is the authority, not the directory listing. Cross-check against
   `data/targets.json` → `bounty_available`.
2. **Say what your contribution is *for*** in `title` and `sources.md`. That one line is what
   everyone else sees in the index.

---

## What gets recognized

The contract's six gates, abbreviated:

| Gate | Test |
|---|---|
| **G1 Direct relevance** | A later solver can use declaration **X** to discharge obligation **Y** in target **Z** |
| **G2 Verified value** | Everything elaborates, and says what you claim. Passing Lean is necessary, not sufficient — a true but irrelevant or vacuous theorem fails |
| **G3 Material progress** | Proves a nontrivial lemma or complete special case; or a definition plus the API to use it; or a checked search bound |
| **G4 Novel or incrementally new** | Not already in the pinned environment or a published contribution. List what you build on in `parents` |
| **G5 Reusable handoff** | Named declarations in a non-conflicting namespace, a stated obstacle and intended use, no undeclared sibling dependency |
| **G6 Provenance** | `sources.md` attributes accurately. **Tool-assisted and generated work is allowed** — the signer is responsible for correctness |

Explicitly **not** evidence of value: "Reputation, wallet balance, employer, time spent,
generated token count, and lines of code."

And explicitly not a contribution: "Formatting changes, renamed copies, thin wrappers,
restatements, unused generated lemmas, and claims without a checked deliverable."

The rewarded / not-rewarded table from `guidelines.md` is the clearest statement of intent:

| Rewarded | Not rewarded |
|---|---|
| A lemma Mathlib is missing that the statement needs | A restatement of the target under a different name |
| A definition plus its basic API (`simp` lemmas, instances) | A wall of generated lemmas nobody will import |
| A special case proved in full | A special case proved with `sorry` |
| A counterexample search with the bound it establishes | A search script with no theorem attached |
| A tactic or `simp` set that closes a recurring goal shape | A copy of an existing contribution under a new id |

**Note the fourth row.** "A counterexample search with the bound it establishes" is rewarded —
"a search script with no theorem attached" is not. If you run a computational search and it
fails to find a witness, that failure is still a contribution *provided you certify the bound
in Lean*. That is the cheapest legitimate way into this track: a bounded exhaustive search
with a checked theorem describing what it established.

---

## Writing the Lean

Each `.lean` file is **elaborated on its own**. A contribution is not a Lake package, so one
file cannot import another in the same directory.

- Imports are limited to `Mathlib`, `Std`, `Init`, `Batteries`, `Aesop`, `Qq`, `Plausible`,
  `ProofWidgets`, `ImportGraph`, `FormalConjectures`, `TaskSupport`.
- Namespace everything under `Contribution.<Something>` so two contributions to the same
  target cannot collide.
- **Rejected outright:** `sorry`, `admit`, `axiom`, `native_decide`, `set_option debug.*`,
  `maxHeartbeats 0`, `#eval`, `#exit`, `run_cmd`, `run_elab`, top-level `initialize`,
  `unsafe`, `@[extern]`, `@[implemented_by]`, `@[init]`, anything reaching `IO.FS` /
  `IO.Process`, the reserved `Bounty` namespace, and out-of-allowlist imports.

  "Most of these are not style rules. Elaborating Lean runs code, and this pipeline runs it on
  someone's hardware."

- **Sent to a human instead of auto-merged:** metaprogramming (`macro`, `elab`, `syntax`,
  `notation`), global `attribute` changes, `open Lean`, `import Lean`, root-namespace
  declarations, and elaboration budgets over one million heartbeats. Allowed — a tactic is a
  perfectly good contribution — but no auto-merge.

Per-artifact: valid UTF-8, no control or bidi characters (`C014`), LF endings, no BOM, trailing
newline (`C022`), and a `sources.md` with `https` links (`C023`).

---

## Layout and submission

One pull request adds exactly one directory:

```
contributions/<target>/<contribution-id>/
    metadata.json    # written by `contrib promote`; never edit
    script.lean      # at least one .lean file (C007)
    sources.md       # required attribution
```

Flat: at most 32 artifacts, 1 MiB each, 4 MiB total, no subdirectories, no symlinks.

`<contribution-id>` is the sha256 of your canonical payload. **You do not choose it** —
`contrib promote` computes it and creates the directory.

**Contributions are immutable.** To correct one, submit a new contribution that lists the old
one in `parents` and explains the delta in `sources.md`. A PR that edits an existing directory
is rejected by `C012`.

```bash
contrib new                      # draft in drafts/ (gitignored)
# ... edit drafts/<...>/script.lean, sources.md ...
contrib check                    # every rule CI runs, except the Lean build
contrib promote                  # compute the id, create contributions/<target>/<id>/
contrib submit                   # opens the pull request
```

`contrib checks` lists the rules by id. `contrib check` is the one that saves you a CI
round-trip — note it does **not** run the Lean build, so it will not catch a proof that fails
to elaborate.

---

## Weighing it against the other vectors

| | Contribution track | Direct submission |
|---|---|---|
| Upfront cost | Free | 0.25 τ |
| When paid | Only if the target is later closed, pro rata | On approval |
| Ceiling | A 0–10 weight share of a pool | $750–$3,800 |
| Best move | A missing lemma, or a certified failed search | A defect, or a counterexample |
| Risk | The target is never closed and nothing is ever paid | The fee |

The honest read: **the contribution track is a lottery ticket on someone else's success**, and
the target may never be closed. Its real advantage is that it costs nothing but time, and that
"we searched exhaustively and there is no witness below N" is genuinely useful mathematics
that nobody else is producing.

The strongest play on the subnet combines it with Vector A from
[`docs/03-attack-vectors.md`](03-attack-vectors.md): while you read a target closely enough to
hunt a formalization defect, you will find the lemmas the statement needs. Those are
contributions whether or not the defect pans out. One close reading, two chances at payment.
