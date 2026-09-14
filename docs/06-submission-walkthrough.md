# Submission walkthrough

End to end, with the guard rails explained. Every command below was run against the live
validator on 14 September 2026; the outputs quoted are real.

---

## Why the CLI is separate commands

From the CLI's own README, and it is the design decision worth understanding first:

> A single command that paid *and* submitted would make every submission failure look like a
> lost transfer, and would invite a retry that pays twice.

So paying and submitting are deliberately separate, and a proof gets a local check in
between. Write it as `conjectures check && conjectures pay`, not as one step.

**What is free:** `tasks`, `status`, `build`, `verify`, `check`, `auth`, `pay reference`.
**What costs money:** `pay` moves TAO; `submit` spends it. Both show you what is about to
happen first (`--yes` skips the prompt).

---

## 0. Install

```bash
git clone https://github.com/conjectures-io/conjectures-miner
cd conjectures-miner
./install.sh
```

Installs with `uv` if present, otherwise into a private virtualenv linked from
`~/.local/bin`. **Python 3.12+ is the only requirement.**

To reproduce what is in this guide without touching your PATH:

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e .
export PATH="$PWD/.venv/bin:$PATH"
```

## 1. Look before you touch anything

```bash
conjectures status
```

```json
{
  "awaiting_review": 2,
  "awaiting_reward": 4,
  "awaiting_verification": 0,
  "banner": null,
  "pin_rotation_in_progress": false,
  "pin_rotation_starts_at": "2026-09-15 02:00:00+00:00",
  "repository_commit": "8432eac998110a563e03df65a28c117e97c8c142",
  "status": "ok",
  "submissions_open": true,
  "task_cache_current": null
}
```

Read the queues. **`awaiting_reward` is money waiting to be signed**, and a queue is a reason
not to expect a fast payout. `pin_rotation_in_progress: true` means submissions are paused —
do not build against a pin that is about to move.

Then cache the pool:

```bash
conjectures tasks sync
```

```json
{
  "cache": "~/Library/Caches/conjectures/https-conjectures-io-2749893a1315.tasks.json",
  "repository_commit": "8432eac998110a563e03df65a28c117e97c8c142",
  "submission_price_rao": 250000000,
  "tasks": 506
}
```

`250000000` rao is **0.25 τ**. Note that `tasks: 506` while the pinned repository contains 518
bundles and the catalogue lists 260 problems × 2 modes. The difference is the seven targets
with `bounty.available: false` — the validator stops serving both modes of a target once a
submission on it has been accepted. (`GET /v1/catalog/conjectures` is the authority on what
is live; the CLI cache and the pinned git checkout can each be a little stale.)

## 2. Pick a task

`list` and `show` read the cache, so they are instant and work offline. A unique prefix or
substring stands in for the full task id.

```bash
conjectures tasks list --filter erdos944
conjectures tasks show erdos944
```

Watch for this, which is a real output and a common stumble:

```json
{ "error": "'erdos944' matches 2 tasks:
    fc-8432eac9-erdos944-erdos-944-874ac96a8b-formalized-v1
    fc-8432eac9-erdos944-erdos-944-a89c65f892-counterexample-v1" }
```

Both modes share a slug. **Pin the mode explicitly.** Getting the mode backwards is a
refusal *after* the money has moved:

> The tool prints the mode you are answering back to you - getting that backwards is a refusal
> after the money has moved.

If you are attacking a defect or a counterexample, that is the `counterexample` id. Prove the
published statement, that is `formalized`.

## 3. Get the exact goal

```bash
conjectures tasks challenge erdos944 --dir challenges/
```

Writes `challenges/<task_id>/Challenge.lean` and prints what you are proving — in particular
`task_mode`. **Those are the same bytes that are hashed into `task_bundle_sha256`**, so do not
edit that file; it is the definition of the problem.

## 4. Write `Main.lean`

Declarations only. From the README:

> Your `Main.lean` holds the declarations only. It is inserted between a trusted header and
> footer that supply the imports and the `namespace`, so an `import` line of your own is a
> refusal, not a duplicate.

```lean
-- Main.lean  (formalized mode)
-- The header already imported the module and opened `namespace Bounty`.
theorem target : fcTypeOfName% "Erdos944.erdos_944" := by
  -- your proof
  ...

-- Main.lean  (counterexample mode)
theorem target : ¬ (fcTypeOfName% "Erdos944.erdos_944") := by
  ...
```

Refused: `sorry`, `admit`, `axiom`, `set_option`, `native_decide`, `instance`, attributes,
`macro`/`syntax`/`notation`, `unsafe`, `IO`, `#eval`, and any reference to the source theorem.

## 5. Configure keys — names only

```bash
conjectures config set wallet_name my-wallet
conjectures config set wallet_hotkey my-hotkey
```

> Names only. No key material belongs in the config file, the environment, or the bundle. The
> hotkey signs; the coldkey of the same wallet pays, and the validator checks on-chain that it
> owns the hotkey.

Precedence is `CLI flag → CONJECTURES_* env → user config file → default`. To see which layer
supplied each value:

```bash
conjectures config show --resolved
```

## 6. Build

Offline. Writes two files: `submission.zip`, **sealed once and never rebuilt**, and
`submission.plan.json`.

```bash
conjectures build --proof Main.lean --task erdos944
```

The plan records where the archive is, what it must hash to, a readable copy of its manifest,
and the payment slot that `pay` fills.

## 7. Verify locally — free, and this is the one that matters

```bash
conjectures verify --setup    # once: ~5 GB down, ~20 GB, 30-60 minutes
conjectures verify            # the sealed submission.zip, up to an hour
```

Linux only, x86_64 or aarch64; on Windows run inside WSL2. On Debian/Ubuntu:

```bash
sudo apt install -y git curl ca-certificates python3 python3-venv zstd
```

`verify` builds the validator's **own** verifier from source and runs your proof through it.
That is categorically different from `check`:

> `check` is a question about the envelope and never reads the proof: it is the zip, the
> manifest and the static policy scan. Only `verify` answers whether the proof is correct.

A local run uses a development sandbox, not the isolation a validator applies to a proof it
did not write — so it answers *is the proof correct*, which is the question you have.

Exit codes matter, and they are designed not to lie: for `verify`, `0` means the verifier
accepted and `1` means it rejected. **Every other code means no verdict was reached** — so
`verify && check` never mistakes a broken host or a retired task for a wrong proof.

## 8. Check the envelope — free, unauthenticated

```bash
conjectures check
```

Exits non-zero on a refusal, so `conjectures check && conjectures pay` is safe to write. It
runs the server's own admission and policy check before any money moves.

## 9. Pay

```bash
conjectures pay --dry-run    # every check, sends nothing
conjectures pay
```

`pay` takes the treasury address and the exact price **from the validator** — not from a
config file — asks the chain whether your coldkey owns the submitting hotkey, sends the
transfer, follows it to finality, and records the resolved reference on the plan.

A payment reference is a **position** (`block-extrinsic` or `block-extrinsic-event`), **not an
extrinsic hash**. A node can resolve a position; resolving a hash is an indexer's job, so the
validator cannot confirm a payment from a hash. `pay` resolves the position for you.

If you paid outside the tool:

```bash
conjectures pay reference --extrinsic 4821993-2 --plan submission.plan.json
```

**If the validator refuses a submission, the payment is not consumed** — no submission row is
written, so the same reference still works. The idempotency key is written to disk *before*
the request goes out, which is what makes a retry safe: reuse it and you get the original
outcome rather than a second charge. Every refusal prints whether the payment survived it.

## 10. Submit

```bash
conjectures submit          # shows what it is about to spend, then spends it
conjectures submit --yes    # skip the prompt
```

No `--payment-ref` — the plan already cites the payment.

## 11. Watch

Verification is asynchronous.

```bash
conjectures submissions show <id> --watch
conjectures submissions report <id>
```

The report is the verifier's immutable record: every gate, pass or fail. After Lean accepts,
the submission goes to manual review, which the FAQ measures **in hours rather than minutes**
and which has no published target time.

---

## Your account (optional)

Nothing above needs an account. `submissions show` proves control of a hotkey and reads what
that hotkey submitted; an **account** is a different thing and is what the website shows you.

```bash
conjectures auth register    # claim the account with your COLDKEY. Once, per machine with the coldkey
conjectures auth login       # sign a challenge with your HOTKEY, store the session token
conjectures auth status
conjectures submissions mine
```

The split is the security property, not an inconvenience: **a hotkey can never create an
account or attach itself to one.** Bittensor stores hotkeys unencrypted by design, so a leaked
hotkey is a way to *work* — submit, read status — and never a way *in*. Linking a hotkey,
repointing your payout and editing your profile are refused to a CLI token and accepted only
from a browser session, because open to a token they compose into account takeover from one
stolen file.

`register` opens a browser session with your coldkey, uses it for the one write it came to
make, and revokes it before returning — on the failure path too. Run it once where your
coldkey lives; run `login` on each rig.

---

## Rules to keep

1. **Never `pay` before `verify`.** The verifier is free; the fee is not.
2. **Never rebuild after `build`.** `submission.zip` is sealed once; editing `Main.lean` after
   building does not change what `submit` sends.
3. **Never reuse a payment reference on a target that has moved.** The plan is a local record
   of money that has moved; a plan that already cites a payment refuses a second `pay`.
4. **Pin the mode.** `erdos944` is ambiguous; the ambiguity is a paid mistake.
5. **Re-read the bounty quote immediately before paying.** It is live and it moves — see
   [`docs/04-economics.md`](04-economics.md).
6. **Nothing signs before it is read.** The CLI validates each challenge message (prefix,
   your address, your validator's domain) *before* unlocking your key, precisely so that a
   mistyped `--api` cannot collect a signature that links your hotkey to someone else's
   account. If you ever write your own client, keep that property.
