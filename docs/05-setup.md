# Setup

Two environments, and they are for different things:

- **The verifier host** — Linux, x86_64 or aarch64, ~20 GB of disk, 30–60 minutes to build.
  This is the one that answers "is my proof correct". Do not skip it.
- **The writing host** — anywhere with Lean 4 and the pinned dependencies, for iterating on
  `Main.lean` without rebuilding the sandbox each time.

You can use one machine for both. Most people should not use a laptop for the first.

---

## Part 1 — The verifier host (Linux)

`conjectures verify --setup` builds the validator's own verifier from source, locally. It is
the only thing that answers whether a proof is correct. `check` does not read your proof at all.

```bash
sudo apt install -y git curl ca-certificates python3 python3-venv zstd

# install the CLI
git clone https://github.com/conjectures-io/conjectures-miner
cd conjectures-miner
./install.sh

conjectures verify --setup
```

| | |
|---|---|
| Download | ~5 GB |
| Disk after build | ~20 GB |
| Time, first run | 30–60 minutes |
| Time, later runs | a couple of minutes — it moves the checkouts to the current revision and re-checks readiness rather than rebuilding |
| Platform | Linux, x86_64 or aarch64. On Windows, inside WSL2 |

Checkouts land under your cache directory. Two environment variables move them:

```bash
export CONJECTURES_VERIFIER_ROOT=/data/conjectures-verifier   # where the checkouts go
export CONJECTURES_VERIFIER_REF=<validator-revision>          # which revision to build
```

`conjectures verify --status` reports what it built and whether it is still ready.

**A local run uses a development sandbox, not the isolation a validator applies to a proof it
did not write.** It answers *is the proof correct* — not *will the submission be accepted*.
Those are different questions and you need both: `verify` for the first, `check` for the second.

Free disk check before you start:

```bash
df -h "$(conjectures verify --status 2>/dev/null | grep -o '/[^ ]*' | head -1 || echo /)"
```

If you only have a laptop with an ARM Mac, put the verifier on a small Linux VPS. The
workflow is `rsync` the sealed `submission.zip` across, `verify`, then either `pay` there or
bring the plan back. The plan cites the payment; it is portable.

---

## Part 2 — The writing host

You want Lean 4 at the pinned version with the pinned Mathlib, so that what compiles for you
compiles for the verifier. Read the pin from the live catalogue rather than from this document,
because it rotates weekly:

```bash
curl -s https://conjectures.io/v1/catalog/meta | python3 -m json.tool | sed -n '/"pins"/,/]/p'
```

At the time of writing: **Lean `leanprover/lean4:v4.27.0`**, Formal Conjectures
`8432eac998110a563e03df65a28c117e97c8c142`, Mathlib `a3a10db0e9d6`.

### Option A — build against the task bundles directly (recommended)

Each bundle is self-contained: `Challenge.lean`, `SolutionHeader.lean.txt`,
`SolutionFooter.lean.txt`, `manifest.json`, `source-metadata.json`, `comparator-config.json`,
`trusted-hashes.json`. The header and footer are literally the file your `Main.lean` will be
wrapped in, so you can reproduce the exact compilation locally:

```bash
./scripts/sync_pool.sh
cd _research/conjectures-tasks/pool/tier-1/erdos-944-formalized
cat SourceHeader.lean.txt 2>/dev/null || cat SolutionHeader.lean.txt
cat Challenge.lean
```

Then, in a scratch directory:

```bash
# reproduce what the verifier does: header + your declarations + footer
cat SolutionHeader.lean.txt > Solution.lean
cat /path/to/your/Main.lean   >> Solution.lean
cat SolutionFooter.lean.txt   >> Solution.lean
```

Rename `theorem target` if needed so the concatenation is a single valid file — the real
pipeline generates `Solution.lean` from your `Main.lean` by this exact concatenation, so any
mistake you make here is the mistake the verifier will report.

### Option B — a Lake project against upstream

```bash
curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh \
  | sh -s -- -y --default-toolchain none
source "$HOME/.elan/env"

git clone --depth 1 https://github.com/conjectures-io/formal-conjectures
cd formal-conjectures
git checkout 8432eac998110a563e03df65a28c117e97c8c142   # the pinned commit
lake exe cache get        # fetch prebuilt Mathlib instead of compiling it for hours
lake build
```

`lake exe cache get` is the difference between twenty minutes and most of a day. Do it.

Use Option B for *exploring* — reading definitions, checking what a name means, trying
`exact?`, `aesop?`, `simp?`. Use Option A for the final compile, because it is byte-exact with
the verifier.

---

## Multi-model tooling

The mathematics is usually easier than the formalization. Two things help:

**Premise retrieval.** Before writing a proof by hand, ask Lean what already exists:

```lean
import Mathlib
#check Nat.smoothNumbers
#print Nat.Full
example : ... := by exact?
```

`#print` on the definitions your target names is the single most valuable reflex for
[Vector A](03-attack-vectors.md) — the historical defects were nearly all "the library
definition does not mean what the docstring means", and `#print` answers that in one line.

For automated search across Mathlib, use `leansearch`, `loogle`, or a MCP/CLI client for them.
Recommendations: [`docs/research/models-and-harnesses.md`](research/models-and-harnesses.md).

**A dedicated prover.** Useful for the statement-proving direction, less so for counterexample
search. Sizing, quantization options, and the tradeoff against a strong general model with a
tool-use loop are in the same document.

---

## Agent loop

The work pattern that matches this subnet, in the order that minimises wasted effort:

```
read the informal problem          (erdosproblems.com — the full record, not the docstring)
  -> ask a strong general model     "is this false? propose a witness"
  -> search computationally         brute force / SAT / targeted construction
  -> only if you have a witness     start the Lean formalization
  -> verify locally                 conjectures verify
  -> pay, submit                    conjectures pay && conjectures submit
```

**Do not pay the formalization cost before you have something to formalize.** That is the
single most common way to lose a week on this subnet. And lean on a local prover loop for the
last mile — going from "I have the object" to "the kernel accepts `Bounty.target`" is where
most of the hours go.

---

## Sanity checks before you trust your setup

```bash
conjectures status                    # is submissions_open true?
conjectures tasks sync                # does the repo commit match what you pinned?
conjectures tasks list --filter erdos944
conjectures verify --status           # is the local verifier built and ready?
```

If `conjectures tasks sync` reports a different `repository_commit` than the one you cloned,
**your checkout is stale** and a proof that compiles locally may not compile for the
validator. Re-run `./scripts/sync_pool.sh` and start again from the current bundles.

---

## Cost note

Nothing in Part 2 costs money. Nothing in Part 1 costs money either, beyond the host. The
**only** command that spends is `conjectures pay` (0.25 τ), and `conjectures submit` spends
the payment you already made. If a step in your workflow is about to charge you, it will say
so and ask first.
