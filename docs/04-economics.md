# Economics

What things cost, what they pay, and the two ways the advertised number misleads you.
Every figure here was read from a live endpoint on **14 September 2026** and the commands
that produce it are at the bottom, so you can re-run it.

---

## The headline numbers

| | |
|---|---|
| Submission fee | **0.25 τ** (250,000,000 rao) |
| Treasury balance | **83,971.01 α** = **$50,663.67** |
| Live bounty quotes | **253** targets, in exactly **two** tiers |
| …tier 1 | 6,314.50 α = **$3,809.84** — 197 targets |
| …tier 2 | 5,538.46 α = **$3,341.58** — 56 targets |
| Sum of all advertised bounties | **1,554,110.52 α** = **$937,668.64** |
| Targets with no payable quote | **7** (`reason: ALREADY_SOLVED`) |
| Defect award | **min($750, locked bounty)** |
| Display rate | ≈ **$0.603 / α** |

Sources: `GET /v1/catalog/conjectures` and `GET /v1/catalog/meta`. The α/USD rate is not a
constant you set — it is recomputed per request, and `amount_usd` is documented as a
**display-only** conversion of `amount_rao`. **The alpha amount is the contract.**
The dollar figures will move; the rao will not.

---

## Misleading thing #1 — the overhang

Divide one number by the other:

```
sum of advertised bounties   1,554,110.52 α     $937,668.64
-----------------------------  ---------------  =  -------------  = 18.5x
treasury balance                  83,971.01 α     $50,663.67
```

The pool advertises **18.5× more money than it holds.** These quotes are not receivables and
they cannot all be paid. The policy is explicit about what they are — from
[`PUBLIC_API.md`](https://github.com/conjectures-io/conjectures-validator/blob/main/docs/PUBLIC_API.md):

> each quote starts at 1/10 of uncommitted funds and increases linearly to 1/8 after 1296000
> elapsed seconds (15 days)

So a quote is `share × uncommitted funds`, where `share ∈ [1/10, 1/8]`. Every target is
quoting against **the same pot**, and the pot is 5% of what the quotes add up to. The
practical consequences:

- **Solving a problem raises everyone else's quote** (the FAQ says this and it is true) —
  because the treasury grows from emissions while the number of open targets falls.
- **The dollar figure is a share-of-pool promise, not a balance.** If six people solved six
  problems at once, they would be paid whatever the treasury could cover, not $3,800 each.
- Payouts are signed by a 2-of-3 multisig, **manually**. Treat the quote as an offer, not a
  settlement.

This is not an accusation of bad faith — it is how a share-of-pool bounty is defined, and the
FAQ explains the mechanism openly. It is a reason to size your effort against ~$750–$3,800
*if the treasury is there when you win*, rather than against a guaranteed sum.

---

## Misleading thing #2 — the quote you actually get

The catalogue figure and the amount recorded against a real submission are **not the same
number.** Here is the one case where both are public for the same target:

| | α | USD at $0.603/α |
|---|---|---|
| Erdős 944, live catalogue quote on 14 Sept | 5,538.46 α | $3,341.58 |
| Erdős 944, **locked** for the submission accepted 11 Sept | **1,130.78 α** | **$682** |

**A 4.9× difference, three days apart.**

The mechanism is in the same documentation:

> Acceptance takes a serialized fresh quote, **subtracting outstanding locks** from the
> treasury balance, and fixes that amount for the submission.

Uncommitted funds is `balance − everyone's outstanding locks`. On 11 September there were
eight submissions pending, whose recorded locks sum to about **68,092 α** against a treasury
of 83,971 α — so the fresh quote had almost nothing to work with and collapsed to 1,130.78 α.
By 14 September those submissions had cleared and the quote had recovered to 5,538.46 α.

The arithmetic is consistent, but I could not reconstruct the exact quote for an arbitrary
past minute from public endpoints, because the outstanding-lock set at that minute is not
published. **So treat this as a well-supported mechanism, not a formula you should trust to
the rao.**

### What this means for you

- **Your bounty is pro-cyclical, and it is anti-correlated with other people's pending work.**
  Submitting into an empty queue gets a materially larger quote than submitting into a busy
  one, for the same problem.
- **Re-read the quote immediately before you pay.** It is live, it is free to fetch, and you
  are not committing to anything by looking.
- The locked amount is what the review policy means when it caps a defect award at "the task
  bounty locked for the submission". So a defect found during a busy week pays less.

```bash
curl -s https://conjectures.io/v1/catalog/conjectures/erdos944-erdos-944 \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["bounty"])'
```

---

## What a win is worth, net

At TAO ≈ $233 (CoinGecko and Binance agreed to within 0.1% on the day) the fee is
**≈ $58.25**. There is no refund path: credits are explicitly non-refundable to TAO.

| Outcome | Gross | Less fee | Notes |
|---|---|---|---|
| Full bounty approved | $3,341.58 – $3,809.84 | **≈ $3,283 – $3,752** | 8 paid to date |
| Formalization defect | **$750** (or the locked bounty, if lower) | **≈ $692** | 6 paid to date; capped at the lock under `v3`, so it can be much less |
| Rejected (`NOT_NOVEL`, duplicate, …) | $0 | **−$58.25** | 4 to date |
| Lean rejects your proof | $0 | **−$58.25** | 5 to date |
| You never submit | $0 | $0 | **246 of 260 targets are in this state** |

Read the bottom two rows together. **Running the local verifier before you pay is the single
highest-return action available to you**, and it is free:

```bash
conjectures verify --setup   # once, ~5 GB down, 30-60 min
conjectures verify           # checks the exact sealed upload, free
conjectures check            # envelope + policy scan, free
conjectures pay              # only now
```

`check` never reads your proof — it only validates the bundle and the static policy scan.
Only `verify` answers whether the proof is correct. Both are free, and the CLI is built so
`conjectures check && conjectures pay` is safe to write.

---

## Is the whole thing worth doing at all

Two honest framings.

**As a job**, the arithmetic is poor. A £750 defect award, found once, on a pool that has
been audited three times and where the five known defects are already retired, is an
afternoon's work if you find one and nothing if you do not. As a rate it does not compete
with a salaried position.

**As a lottery ticket with favourable structure**, it is unusually good:

- The verifier is free and local, so the only capital at risk per attempt is $58.
- The failure mode is bounded and known; you cannot lose more than the fee.
- 246 of 260 targets have never been attempted — the field is not crowded.
- The review policy resolves unresolved doubt **in your favour** ("Unresolved uncertainty
  favors `REVIEW_APPROVED`"), and requires a reviewer to demonstrate a *concrete
  correspondence* before rejecting for prior publication.
- The work product — a Lean proof — is yours regardless of outcome, and is a real artefact
  in a field where those are scarce.

And the honest tail: the subnet earned **~0% emission** in the price-based model as of
September 2026 per third-party trackers, which means the chain is not currently funding it.
Rewards come from a treasury of ~$50k. Plan accordingly; do not plan on $3,800.

---

## Reproducing every number above

```bash
./scripts/sync_pool.sh
python3 - <<'PY'
import json
t = json.load(open("data/targets.json"))
meta = json.load(open("data/catalog_meta.json"))
b = [r for r in t if r["bounty_rao"]]
print("targets          ", len(t))
print("with live quote  ", len(b))
print("tiers (alpha)    ", {round(x["bounty_alpha"], 2) for x in b})
print("sum alpha        ", sum(x["bounty_rao"] for x in b) / 1e9)
print("sum usd          ", round(sum(x["bounty_usd"] for x in b), 2))
print("treasury alpha   ", meta["bounty"]["balance_rao"] / 1e9)
print("overhang         ", round(sum(x["bounty_rao"] for x in b) / meta["bounty"]["balance_rao"], 2))
print("fee rao          ", meta["credit_price_rao"])
PY
```

## Caveats I am carrying

- The `$750` defect figure is read from policy `v3` and the validator's database
  constraints. Submissions accepted under policy `v1`/`v2` keep a fixed $750 with **no cap**;
  `v3` caps at the locked bounty. The five August awards were under `v1`; the Erdős 726 award
  (13 Aug) was under `v2` and, with no cap in force, came to 1,257.22 α against a displayed
  bounty of 935.20 α — **the defect award exceeded the bounty it replaced.**
- The 1,130.78 α figure comes from the public results page for that submission, not from an
  API. I did not independently re-verify it against chain state.
- The treasury balance is the API's own `bounty.balance_rao`. It is not a chain read. It
  should be close, but I did not verify it against the treasury coldkey
  `5HMqFHmvUpzuAjEnse3hzMKS5LsFL428hffCfenF2smuGNhs`.
- The subnet's own documents disagree about the fee: the validator `README.md` says 0.5 TAO,
  the website says 0.5 τ, a third-party write-up says 0.25 τ. **The live API says
  250,000,000 rao = 0.25 τ**, and the live API is what charges you.
