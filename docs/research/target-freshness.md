# Target freshness: is this problem still worth attacking?

*Operational appendix. Every endpoint below was fetched while writing this on
**2026-09-14**; the HTTP status shown is the status I actually got. Where a
source refused me, it says so.*

---

## 0. The short version

Before spending a submission, ask one question:

> **Does the live catalog say the bounty on this target is payable *right now*?**

Everything else is corroboration. There is exactly one authoritative source for
payability, it is unauthenticated, and it answers in a single field:

```bash
curl -s 'https://conjectures.io/v1/catalog/conjectures?limit=100' | \
  python3 -c 'import json,sys; [print(i["slug"], i["bounty"]["available"], i["bounty"]["reason"]) for i in json.load(sys.stdin)["items"]]'
```

Run the ready-made version instead:

```bash
python3 scripts/freshness_check.py erdos944 erdos196 green15
python3 scripts/freshness_check.py --list-retired
```

Why this matters more than any literature search: **`is_open` and
`bounty.available` are different fields, and they disagree.** As of 2026-09-14
all 260 catalog rows carry `is_open: true` and `category: "research open"`, but
**7 of them have `bounty.available: false` with `reason: "ALREADY_SOLVED"`**.
Read `is_open` and you will happily attack a target that cannot pay you.

The FAQ's own admission of the gap (hand-checked retirement, no watching agent
yet) is exactly why this check must be run *by you, on the day you submit* — the
ledger's `Already solved before this submission` and `Already formalized
elsewhere` rejections are that gap cashing out as lost fees.

---

## 1. `conjectures.io` — the live catalog API (authoritative)

This is not documented in the guide yet. It is the single most valuable
endpoint for this question, and it is unauthenticated.

| Endpoint | Status | Notes |
|---|---|---|
| `GET https://conjectures.io/v1/catalog/conjectures` | **200** | JSON. Default `limit` 25, `offset` 0 |
| `GET .../conjectures?limit=100&offset=0` | **200** | 145,600 bytes |
| `GET .../conjectures?limit=100&offset=100` | **200** | |
| `GET .../conjectures?limit=100&offset=200` | **200** | returns 60 items; `total: 260` |
| `GET .../conjectures?limit=200` | **400** | see below |
| `GET https://conjectures.io/v1/catalog/meta` | **200** | live fee, treasury, policy |

`limit` is capped at **100**. Asking for more is rejected with RFC-7807:

```json
{"type":"about:blank","title":"Malformed request","status":400,
 "detail":"request is missing or has malformed fields",
 "reason_code":"MALFORMED_REQUEST",
 "errors":[{"location":"query.limit",
            "message":"Input should be less than or equal to 100",
            "type":"less_than_equal"}]}
```

### What a row looks like

```json
{
  "slug": "erdos944-erdos-944",
  "display_title": "Erdős problem 944",
  "title_parts": {"collection": "erdos_problems", "collection_label": "Erdős problems",
                  "reference": "944", "qualifier": null},
  "title": "Erdos944.erdos_944",
  "statement": "True ↔ ...",
  "summary": "...",
  "category": "research open",
  "classification": "DIRECT_PROP",
  "task_modes": ["formalized", "counterexample"],
  "tier": "tier-1",
  "is_open": true,
  "reward_target_id": "fc-target:Erdos944.erdos_944",
  "tasks": [{"task_id": "fc-8432eac9-erdos944-...", "task_mode": "formalized", ...}, ...],
  "bounty": {"amount_rao": 5538694496348, "amount_usd": "3356.10",
             "policy_version": "linear-age-v3-locked",
             "available": true, "reason": "OPEN",
             "as_of": "2026-09-14T00:54:00Z", "locked": false},
  "attempts": 1
}
```

### The fields that decide it

- **`bounty.available`** — `true` / `false`. This is the payable verdict.
- **`bounty.reason`** — `"OPEN"` (253 rows) or `"ALREADY_SOLVED"` (7 rows) on
  2026-09-14. Only these two values were observed; treat any third value as new
  and investigate before paying.
- **`bounty.as_of`** — `"2026-09-14T00:54:00Z"` at first fetch, `01:07:00Z`
  thirteen minutes later. It refreshes continuously, so re-fetch; do not cache
  this across days.
- **`is_open`** — *upstream research-open status*, not payability. Do not use it
  as the verdict.
- **`bounty.amount_usd` / `amount_rao`** — `null` on unpayable rows.

### The seven unpayable rows on 2026-09-14

```
erdos196-erdos-196                         reason=ALREADY_SOLVED
erdos272-erdos-272-variants-szabo-strong   reason=ALREADY_SOLVED
erdos726-erdos-726                         reason=ALREADY_SOLVED
erdos96-erdos-96                           reason=ALREADY_SOLVED
green15-green-15                           reason=ALREADY_SOLVED
green47-green-47                           reason=ALREADY_SOLVED
green51-green-51-one-half                  reason=ALREADY_SOLVED
```

Two of these are **among the most attractive-looking targets in the pool**,
which is the whole point:

```
erdos196  ->  bounty.available=False  reason=ALREADY_SOLVED
green15   ->  bounty.available=False  reason=ALREADY_SOLVED
```

Both have `is_open: true`, `category: "research open"`, `attempts: 1`, and the
tracker still shows them open. **A miner who reads any source other than
`bounty.available` will attack them and lose the fee.**

### Live fee and treasury (`/v1/catalog/meta`)

```json
{"repository_commit":"8432eac998110a563e03df65a28c117e97c8c142",
 "bundle_format":"conjectures-submission/v1",
 "conjectures":260, "open_conjectures":260,
 "categories":[{"value":"research open","count":260}],
 "credit_price_rao":250000000, "credits_per_attempt":1,
 "treasury_address":"5Gn2SyG6PmBstAjiPD93CTuxADqYaYqf6fKeFuezKsX7Chf9",
 "max_bundle_bytes":12582912,
 "bounty":{"policy_version":"linear-age-v3-locked",
           "balance_rao":83971008893674, "balance_usd":"50881.10",
           "asset":"alpha", "open_targets":253, ...}}
```

**`credit_price_rao: 250000000` = 0.25 τ per attempt.** Note the disagreement
between sources: `conjectures.io/how-it-works` says 0.5 τ and the validator
`README.md` says 0.5 TAO, but the live API — the thing that charges you — says
0.25 τ. This document uses the API value; see `docs/04-economics.md` for the
full reconciliation. **`open_targets: 253` = 260 − 7**, which is an independent
confirmation of the unpayable set, straight from the subnet itself.

---

## 2. `erdosproblems.com` — the canonical tracker

Thomas Bloom's tracker. **There is no API, no RSS, and no Atom feed. You poll
HTML.**

### URL scheme

```
https://www.erdosproblems.com/944          # problem page (canonical)
https://www.erdosproblems.com/history/944  # revision history, dated
https://www.erdosproblems.com/latex/944    # LaTeX source of the statement
https://www.erdosproblems.com/forum/search?q=944        # forum search
https://www.erdosproblems.com/forum/thread/944          # per-problem thread
https://www.erdosproblems.com/forum/thread/944/proof-claims
https://www.erdosproblems.com/forum/discuss/944         # 302 -> /forum/thread/944
```

### What I actually fetched

| URL | Status | Bytes |
|---|---|---|
| `/` | **200** | 43,834 |
| `/944` | **200** | 33,322 |
| `/196` | **200** | 31,786 |
| `/1` | **200** | 54,288 |
| `/728` | **200** | 32,509 |
| `/3`, `/4`, `/7`, `/19`, `/23`, `/42`, `/474`, `/501` | **200** | ~30–50k each |
| `/history/944` | **200** | 29,690 |
| `/latex/944` | **200** | 26,773 |
| `/forum/thread/944` | **200** | 43,209 |
| `/forum/thread/944/proof-claims` | **200** | 41,176 |
| `/forum/search?q=944` | **200** | 1,033,065 |
| `/forum/search?q=944&page=2` | **200** | 24,634 |
| `/forum` | **308** | redirect |
| `/forum/discuss/944` | **302** | redirect to `/forum/thread/944` |
| `/prizes`, `/lists` | **200** | |
| `/feed` | **404** | |
| `/rss` | **404** | |
| `/atom.xml` | **404** | |
| `/feed.xml` | **404** | |
| `/sitemap.xml` | **404** | |
| `/api` | **404** | |
| `/problems.json` | **404** | |
| `/all` | **404** | |
| `/search?q=196` | **404** | (site search is `/forum/search`, not `/search`) |

So: **the feed hunt is a dead end.** `404` on every plausible feed path.

### `robots.txt` — read this before you scrape

`GET /robots.txt` → **200**, 1,836 bytes, Cloudflare-managed:

```
User-agent: *
Content-Signal: search=yes,ai-train=no,use=reference
Allow: /

User-agent: Amazonbot / Applebot-Extended / Bytespider / CCBot /
            ClaudeBot / CloudflareBrowserRenderingCrawler /
            Google-Extended / GPTBot / meta-externalagent
Disallow: /
```

`Allow: /` for `*`, and `Content-Signal: use=reference` explicitly permits
reference use. But **GPTBot, ClaudeBot, CCBot and Google-Extended are
disallowed**, so do not point an LLM crawler at it. The script in this repo uses
a plain identifying User-Agent, sequential requests, and no crawling beyond the
one page per target it needs. Keep it that way: one page per target, one
`/history` lookup, no loops. Getting rate-limited or blocked here costs you the
only free tracker there is.

### Status vocabulary — the `id` is binary, the tooltip is the truth

The status lives in the page as:

```html
<div class="problem-text" id="open">
  <div id="prize">
    <span class="tooltip">
OPEN
<span class="tooltiptext">
This is open, and cannot be resolved with a finite computation.
</span>
```

The `id` on `div.problem-text` is **only ever `open` or `solved`**. The real
vocabulary is in the tooltip. I fetched one problem of each kind to establish
this:

| Problem | `id` | Tooltip | Tracker DB `informal_status` |
|---|---|---|---|
| `/944` | `open` | This is open, and cannot be resolved with a finite computation. | `open` |
| `/196` | `open` | This is open, and cannot be resolved with a finite computation. | `open` |
| `/3` | `open` | This is open, and cannot be resolved with a finite computation. | `open` |
| `/7` | `open` | **Open, but could be proved with a finite example.** | `verifiable` |
| `/23` | `open` | **Open, but could be disproved with a finite counterexample.** | `falsifiable` |
| `/474` | `open` | Open in general, but there exist models of set theory where the result is false. | `not provable` |
| `/4` | `solved` | This has been solved in the affirmative. | `proved` |
| `/1` | `solved` | This has been solved in the negative **and the proof verified in Lean**. | `disproved` |
| `/728` | `solved` | This has been solved in the affirmative **and the proof verified in Lean**. | `proved (Lean)` |
| `/42` | `solved` | This has been resolved in some other way than a proof or disproof, and that resolution verified in Lean. | `solved` |
| `/19` | `solved` | Resolved up to a finite check. | `decidable` |
| `/501` | `solved` | Independent of the usual axioms of set theory (ZFC). | `independent` |

Two things to take from this:

1. **The `solved` id is a red flag, but the tooltip explains *how*.** "solved in
   the affirmative/negative, verified in Lean" means a solution exists and is
   machine-checked — no freshness left.
2. **`id="open"` is not one thing.** `falsifiable` and `verifiable` are open
   *and* have a cheap shape: an explicit counterexample or witness settles them.
   These are the best target shapes on the subnet, and my own first-draft script
   wrongly classified them as settled. Do not repeat that mistake: only
   `proved` / `disproved` / `solved` / `independent` are settled.

### The Lean / formalized annotations

Two *separate* things get called "formalized", and conflating them is a trap:

- **"Formalised statement? Yes"** on the problem page — links to
  `github.com/google-deepmind/formal-conjectures/blob/main/FormalConjectures/ErdosProblems/<N>.lean`.
  This means *the statement* is in Lean. It says nothing about whether the
  problem is solved. `erdos944` has this set to **Yes** and is wide open.
- **`(Lean)` in the status** — e.g. `proved (Lean)` — means *a solution* has
  been formalized. This one means the problem is done.

In the database these are the `formalized.state` and `formal_status.state`
fields respectively (see §3).

### Polling it programmatically

No API, so: fetch `https://www.erdosproblems.com/<N>`, regex the
`div.problem-text` id and the tooltip. That is what the script does. Two
additional signals worth harvesting from the same page:

- **`Proof claims (n)`** → `href="/forum/thread/<N>/proof-claims"`. `erdos944`
  shows **`Proof claims (1)`** — someone has claimed a proof. The tracker still
  says open; the mechanism that retires it has not caught up. Under the FAQ's
  own description of the gap, that is a live risk of an
  `Already solved before this submission` rejection.
- **`/history/<N>`** gives dated revisions. `erdos942`'s newest is
  `2026-06-15T08:27:00Z`; `erdos4`'s is `2026-08-31T12:00:23Z` — a recent
  revision of a `solved` problem. A *recent history date on an open problem* is
  worth a look; it usually means the statement was corrected or a partial result
  was added.

---

## 3. The machine-readable Erdős database (`teorth/erdosproblems`)

This is the one machine-readable endpoint for the whole tracker, and the
website itself points at it as "the external database". It is **far better than
scraping**.

| URL | Status | Bytes |
|---|---|---|
| `https://api.github.com/repos/teorth/erdosproblems` | **200** | `"A community database for the problems on the erdosproblems.com site"`, `pushed_at 2026-09-09` |
| `https://raw.githubusercontent.com/teorth/erdosproblems/main/data/problems.yaml` | **200** | 401,189 — **1,217 entries** |
| `.../main/schema/problems.schema.json` | **200** | 2,584 |
| `.../main/scripts/derive_status.py` | **200** | 8,881 |
| `.../main/data/statistics_history.csv` | **200** | 192,875 |

Per-problem shape:

```yaml
- number: "1"
  prize: "$500"
  informal_status: {state: "disproved", last_update: "2025-08-31"}
  formal_status:   {state: "Lean",      last_update: "2026-09-03"}
  status:          {state: "disproved (Lean)", last_update: "2026-09-03"}
  oeis: ["A276661"]
  formalized:      {state: "yes",       last_update: "2025-08-31"}
  tags: ["number theory", "additive combinatorics"]
```

The schema is explicit that these are two independent axes:

- `informal_status.state` — *"The human/mathematical status of the problem,
  ignoring formalization."* Enum: `open`, `proved`, `disproved`, `solved`,
  `falsifiable`, `verifiable`, `decidable`, `not provable`, `not disprovable`,
  `independent`.
- `formal_status.state` — *"Whether a **solution** to the problem has been
  formalized in a proof assistant."* Enum: `unformalized`, `Lean`.
- `formalized.state` — *"Whether the problem **statement** is formalized in the
  formal-conjectures repository."* `yes` / `no`.
- `status.state` — derived by `scripts/derive_status.py`; `informal` with
  `" (Lean)"` appended when a formal solution exists. *"do not edit by hand."*

Distribution across all 1,217 entries on 2026-09-14:

```
open 591 | proved 334 | disproved 139 | solved 101 | falsifiable 25
decidable 9 | verifiable 7 | independent 4 | not disprovable 4 | not provable 3
```

**561 settled vs 656 live** — so roughly 46% of the Erdős corpus is already
dead for bounty purposes. That is the base rate you are fighting.

This is also the source the subnet itself pins: `selection-audit.json` declares

```json
{"family": "erdos",
 "locator": "teorth/erdosproblems",
 "revision": "5308c57c700559416b9f205df274b136784203e7"}
```

`https://api.github.com/repos/teorth/erdosproblems/commits/5308c57c700559416b9f205df274b136784203e7`
→ **200**, dated `2026-09-07T15:33:54Z`. So you can diff the pinned revision
against `main` and see exactly what moved since the pool was audited. That is
the cheapest "has anything changed?" check there is:

```bash
curl -s https://raw.githubusercontent.com/teorth/erdosproblems/main/data/problems.yaml \
  | python3 scripts/freshness_check.py --no-arxiv --from-catalog data/targets.json
```

⚠️ `data/problems.yaml` is YAML, not JSON, and it has **no front matter and no
`---` document separator** — a plain `yaml.safe_load` on the whole file works,
but the script here parses it with a small fixed-shape regex reader to avoid the
PyYAML dependency.

### Green's Open Problems are *not* in this database

`greens_open_problems` targets have no tracker page and no database row. The
subnet's declared status source for that family is the PDF itself:

```json
{"family": "greens-open-problems",
 "locator": "https://people.maths.ox.ac.uk/greenbj/papers/open-problems.pdf",
 "revision": "2026-01"}
```

`GET https://people.maths.ox.ac.uk/greenbj/papers/open-problems.pdf` → **200**,
`application/pdf`, 839,479 bytes. A dated PDF revision is a weak freshness
signal — it changes rarely. For Green's targets the catalog's
`bounty.available` matters even more, because the corroborating sources are
thinner. (Which is exactly how `green15` and `green47` sit unpayable with no
tracker page to warn you.)

---

## 4. `formal-conjectures` — has the statement acquired a proof or a correction?

Two repos:

- **`github.com/google-deepmind/formal-conjectures`** — upstream. `GET /repos/...`
  → **200**, 1,265 stars, 479 forks, `open_issues_count: 1251`, Lean, Apache-2.0.
- **`github.com/conjectures-io/formal-conjectures`** — the subnet's fork.
  `GET /repos/conjectures-io/formal-conjectures` → **200**, `"fork": true`,
  `"parent": {..."full_name": "google-deepmind/formal-conjectures"}`,
  `pushed_at: 2026-08-05` (i.e. it tracks upstream and is ~5 weeks stale against
  upstream's `2026-09-13`).

### The pin does not resolve. This is a real finding.

The pool's pinned commit is **`8432eac998110a563e03df65a28c117e97c8c142`**. I
tried every public route to it:

| Attempt | Status |
|---|---|
| `api.github.com/repos/google-deepmind/formal-conjectures/commits/8432eac9…` | **422** `No commit found for SHA: 8432eac998110a563e03df65a28c117e97c` |
| `github.com/google-deepmind/formal-conjectures/commit/8432eac9….patch` | **404** |
| `api.github.com/…/compare/7d1a8c99…8432eac9…` | **404** |
| `api.github.com/repos/conjectures-io/formal-conjectures/commits/8432eac9…` | **422** |
| `github.com/conjectures-io/formal-conjectures/commit/8432eac9….patch` | **404** |
| `api.github.com/repos/conjectures-io/conjectures-tasks/commits/8432eac9…` | **422** |
| `api.github.com/repos/conjectures-io/conjectures-validator/commits/8432eac9…` | **422** |

**The pinned commit is not publicly resolvable.** Yet it is not fictitious
either — it is the value `/v1/catalog/meta` and every task manifest publish as
`repository_commit`, and it is baked into every task id
(`fc-8432eac9-erdos944-…`). The honest reading: it is an internal pin, so
**you cannot diff the pool against the exact audited state via GitHub.** Plan
around it.

Two references *do* resolve, and they are the useful substitutes:

| Commit | Status | Date | What it is |
|---|---|---|---|
| `7d1a8c9912747679d0093f6d1216420c33ee5ffa` | **200** | 2026-09-01 | the `base_commit` in `lean-source.json`, and the "2026-09-02 repin" named in `POOL.md` |
| `2c817e975be7a95478b72a8429155ca568e1a3de` | **200** | 2026-09-07 | `source_main_commit` in `selection-audit.json` |

Use `7d1a8c99` for drift checks. `scripts/freshness_check.py` does exactly that,
and says so in its output rather than silently comparing `HEAD` to `HEAD`.

```bash
# Does the statement I want to attack still look the way it did at the pin?
for REF in 7d1a8c9912747679d0093f6d1216420c33ee5ffa HEAD; do
  curl -s "https://raw.githubusercontent.com/google-deepmind/formal-conjectures/$REF/FormalConjectures/ErdosProblems/944.lean" \
    | shasum -a 256
done
```

### Finding proof / correction PRs against a statement

The pool's own audit counts `github_open_pr_count: 359` and rechecks specific
PRs by hand. You can do the same in one call — **search PR titles for the
problem number**:

```bash
gh api -X GET 'search/issues' \
  -f q='repo:google-deepmind/formal-conjectures is:pr 944 in:title' \
  -f per_page=20 -f sort=created -f order=desc \
  --jq '.total_count, (.items[] | "\(.number)\t\(.state)\t\(.created_at[:10])\t\(.title)")'
```

or without `gh`:

```bash
curl -sG https://api.github.com/search/issues \
  --data-urlencode 'q=repo:google-deepmind/formal-conjectures is:pr 944 in:title' \
  --data-urlencode 'per_page=20' | \
  python3 -c 'import json,sys; d=json.load(sys.stdin); print("total:",d["total_count"]); [print(i["number"], i["state"], i["created_at"][:10], i["title"]) for i in d["items"]]'
```

Real result for **944** (HTTP **200**, `total_count: 6`):

```
5467  open    2026-09-10  Mark Erdős 944 Dirac conjecture and k = 4 case as solved
4237  open    2026-06-11  Erdős 944: machine-checked cores for the k=4, r=1 six-regular subproblem
1156  closed  2025-10-28  fix: missing quantification in `944.lean`
3075  closed  2026-03-03  solve(ErdosProblems): formally solved Dirac conjecture variants in 944
2550  closed  2026-03-03  solve(ErdosProblems): formally solved Dirac conjecture variants in 944
```

**PR #5467 is the finding that should stop you.** `GET /pulls/5467` → **200**:

> *"This PR marks both `erdos_944.variants.dirac_conjecture` and
> `erdos_944.variants.dirac_conjecture.k_eq_four` as solved, changing their
> answers from `answer(sorry)` to `answer(True)`. The Lean proof here for `k =
> 4`, together with Jensen's result for every `k ≥ 5`, completes Dirac's
> conjecture for all `k ≥ 4`."* — opened 2026-09-10 by `KitaKen1`

`GET /pulls/5467/files` → **200**: one file changed,
`FormalConjectures/ErdosProblems/944.lean`, `+6 −4`.

Neither PR is merged, and the catalog still pays `$3356.35` on 944 — so 944 is
currently *payable but contested*. That is a much more precise statement than
"open" or "closed", and it is the kind of thing you want to know before sinking
a week.

Also useful, for the whole family at once:

```bash
curl -sG https://api.github.com/search/issues \
  --data-urlencode 'q=repo:google-deepmind/formal-conjectures is:pr is:open Erdos' \
  --data-urlencode 'per_page=3'
# HTTP 200, total_count: 185
```

Unauthenticated GitHub search is rate-limited to ~10 requests/minute. The
script spaces its calls and reports the status when it is refused.

### Checking the statement itself

```bash
curl -s https://raw.githubusercontent.com/google-deepmind/formal-conjectures/main/FormalConjectures/ErdosProblems/944.lean
# HTTP 200, 4070 bytes
```

If that file's sha256 differs between `7d1a8c99` and `HEAD`, the statement moved
upstream and the target's `type_hash` may no longer describe what you are
attacking. `erdos479` is the documented precedent — it was restated from
`ℕ`/`Nat.ModEq` with `k > 1` to `ℤ`/`Int.ModEq`, and the pool kept it *as a new
task identity*.

---

## 5. arXiv, MathOverflow, and the forum

### arXiv — the API exists, and it is throttled

Endpoint: **`https://export.arxiv.org/api/query`** (Atom XML, no key).

```bash
curl -sG https://export.arxiv.org/api/query \
  --data-urlencode 'search_query=all:"Erdos problem 944"' \
  --data-urlencode 'start=0' --data-urlencode 'max_results=20' \
  --data-urlencode 'sortBy=submittedDate' --data-urlencode 'sortOrder=descending'
```

**Honest reporting of what I observed.** Over ~30 minutes of attempts from this
host:

| Endpoint | Observed |
|---|---|
| `http://export.arxiv.org/api/query?...` | **301** → `https://` (`Location: https://export.arxiv.org/api/query?…`) |
| `https://export.arxiv.org/api/query?...` | **429** on ~8 of 9 attempts; body is 14 bytes: `Rate exceeded.` Once, **200** (on `all:test`) |
| `https://arxiv.org/search/?searchtype=all&query=…` | **429**, 14 bytes — every attempt |
| `https://arxiv.org/abs/<id>` | **200**, 40,981 bytes |
| `https://arxiv.org/list/math.CO/recent` | **200** |

So the throttle is on arXiv's **search** services specifically, not on arXiv as
a whole, and it is intermittent rather than a permanent block. Practical
consequences:

- Always use `-L` / follow the `301`; the `http://` host is legacy.
- Space requests. One request per target, not a loop.
- **Treat a 429 as UNKNOWN, never as "nothing published".** The script refuses to
  return a negative result from a failed fetch and prints the manual URL instead.
  `--no-arxiv` records it as an explicit caveat rather than stalling your run on
  a 20-second timeout per target.

**Limitations that matter even when it works:**

- It searches **metadata only** — title, abstract, authors, comments, journal
  ref. It does **not** index full text. A paper that proves Erdős 944 in §4
  without putting "Erdős 944" in the abstract is invisible to it.
- `all:"Erdos problem 944"` is a phrase match, so it will miss the many spellings
  in the wild (`Erdős 944`, `Dirac's conjecture`, `problem 91 of the graph
  problems collection` — which is how 944 is actually catalogued in the graph
  collection). Search several phrasings, plus the *subject matter*.
- The real risk is not a paper titled after the problem; it is a paper about the
  *mathematics* that happens to settle it. For 944 the dangerous query is
  `"vertex-critical" AND "chromatic number"`, not the number.

Recommended manual pass, in order: the number, then the mathematical statement's
keywords, then the problem's `tags` from `problems.yaml`.

### MathOverflow / Math StackExchange — a real API

`https://api.stackexchange.com/2.3/search/advanced` — no key needed for
moderate use (300 requests/day/IP; the responses carry
`quota_remaining`).

```bash
curl -sG https://api.stackexchange.com/2.3/search/advanced \
  --data-urlencode 'order=desc' --data-urlencode 'sort=relevance' \
  --data-urlencode 'intitle=Erdos problem' \
  --data-urlencode 'site=mathoverflow' \
  --data-urlencode 'pagesize=10' --data-urlencode 'filter=default'
# HTTP 200, application/json, quota_remaining: 298
```

Real hits for `intitle=Erdos problem` on `mathoverflow`:

```
On Erdős Problem #598                        https://mathoverflow.net/questions/511508/on-erd%C5%91s-problem-598
$1$-dimension reduction of Erdős Problem 86  https://mathoverflow.net/questions/508336/1-dimension-reduction-of-erd%C5%91s-problem-86
A conjecture related to Erdős Problem 86     https://mathoverflow.net/questions/507835/a-conjecture-related-to-erd%C5%91s-problem-86
```

**Two caveats I hit in practice:**

1. **`intitle=` is a loose, OR-ish match.** `intitle=Erdos 944` returned five
   questions about matrix cofactors and polygon geometry — terms matched
   independently, not as a phrase. Post-filter for the number *and* a
   conjecture word, or you will chase noise. The script does this.
2. **Title-scoped only.** Answers and body mentions are invisible. A definitive
   MathOverflow answer to a question titled something else will not appear.

`q=` (body/answer search) also works — `q='"Erdos problem 196"'` → HTTP **200**,
0 items — but it is stricter about phrases and has the same quota.

Manual equivalents, worth using because they search bodies:

- `https://mathoverflow.net/search?q=Erdos+944`
- `https://math.stackexchange.com/search?q=Erdos+944`
- `https://www.erdosproblems.com/forum/search?q=944` — the tracker's own forum
  search. HTTP **200**, 1,033,065 bytes for `q=944`, paginated with `&page=N`.

### The tracker forum is the highest-signal source for *this* subnet

Because the tracker's database lags reality. Searching the forum for `944`
returns **35 results**, and the top ones are decisive:

- `/forum/thread/proof-claim:9e89c3dc2e41415d99a282a4691a5d85` — posted
  **2026-09-11 14:21**
- `/forum/thread/944#post-8949` — posted **2026-09-10 12:09**

The content of the first is the reason to read this page before you commit:

> *"Congratulations — this appears to be an independent Lean formalization
> obtained at almost the same time. I also submitted a Lean proof of the
> remaining k=4 case on 10 September 2026: Formal Conjectures PR #5467 …
> The constructions are different: mine uses a graph on 48 vertices, while yours
> uses a graph on 60 vertices. My final axiom audit reports only propext,
> Classical.choice, and Quot.sound. It is also interesting that both projects
> were AI-assisted through different systems…"*

**Two independent Lean solutions to the k=4 case of Erdős 944 landed within days
of each other in September 2026, and on 2026-09-14 the catalog still pays
`$3356.35` on 944.** That is precisely the window the FAQ describes as "real and
on us". If you were about to spend a week on 944, this is the paragraph that
should change your mind — and neither the tracker status, nor `problems.yaml`,
nor `is_open` would have told you.

---

## 6. The script: `scripts/freshness_check.py`

Stdlib only (`urllib`, `json`, `re`, `argparse`, `hashlib`, `textwrap`); uses
`requests` only if it happens to be installed. No keys required.

```bash
python3 scripts/freshness_check.py erdos944 erdos196 green15
python3 scripts/freshness_check.py --no-arxiv erdos942 erdos944 erdos196 green15
python3 scripts/freshness_check.py --json erdos944
python3 scripts/freshness_check.py --list-retired
python3 scripts/freshness_check.py --from-catalog data/targets.json
```

Exit codes: `0` all clear · `1` at least one target is not payable · `2` at least
one target could not be decided.

### Design

1. **The catalog API is the only verdict.** Every other source is evidence. If
   the catalog says `bounty.available: false`, the verdict is `DO NOT ATTACK`
   regardless of what anything else says.
2. **No source may lie.** A fetch that fails, 429s, times out, or parses into
   something unrecognised yields `UNKNOWN` **with the HTTP status and reason**.
   A failed arXiv fetch never becomes "no paper found".
3. **`UNKNOWN` is not `open`,** and the verdict says so in those words. But three
   kinds of unknown are distinguished so the verdict stays useful: `blocked`
   (arXiv throttling — a caveat, not evidence against freshness), `out_of_scope`
   (Green's problems have no tracker page), and a genuine inconclusive gap that
   forces an overall `UNKNOWN`.

### The sources it checks, per target

| # | Source | Signal | Fails to |
|---|---|---|---|
| 1 | `conjectures.io/v1/catalog/conjectures` | `bounty.available`, `bounty.reason`, `bounty.as_of`, `attempts` | UNKNOWN |
| 2 | `erdosproblems.com/<N>` | `div.problem-text` id, tooltip→`informal_status`, proof-claim count, comment count | UNKNOWN |
| 3 | `erdosproblems.com/history/<N>` | newest revision date | (skipped) |
| 4 | `formal-conjectures` via GitHub API | open PRs matching `<N> in:title`; sha256 drift `7d1a8c99` vs `HEAD` | UNKNOWN |
| 5 | `teorth/erdosproblems` `data/problems.yaml` | `informal_status` / `formal_status` | UNKNOWN |
| 6 | `export.arxiv.org/api/query` | recent hits | UNKNOWN (`blocked`) |
| 7 | `api.stackexchange.com/2.3/search/advanced` | MathOverflow + Math.SE, post-filtered | UNKNOWN |

### Verdicts

- **`DO NOT ATTACK`** — catalog not payable, *or* not offered at all, *or* the
  tracker shows it solved.
- **`LIKELY OPEN`** — every applicable source agrees it is open.
- **`OPEN, BUT CHECK THE FLAGS`** — nothing contradicts openness, but something
  raised a warning: an open PR claiming a solution, a proof claim on the forum,
  or statement drift. *This is the verdict that most needs your attention.*
- **`UNKNOWN`** — a source that should have answered did not.

---

## 7. Real output

Command:

```bash
python3 scripts/freshness_check.py --no-arxiv erdos23 erdos942 erdos944 erdos196 green15
```

Exit code `1`. Verbatim, 2026-09-14:

```
==============================================================================
TARGET FRESHNESS REPORT
  generated : 2026-09-14T01:07:27+00:00
  pool pin  : 8432eac998110a563e03df65a28c117e97c8c142
  catalog as_of: 2026-09-14T01:07:00Z
  cost/attempt : 0.25 tau (250000000 rao) -- live from /v1/catalog/meta
==============================================================================

##############################################################################
# erdos23  ->  OPEN, BUT CHECK THE FLAGS
##############################################################################
  WHY: no source contradicts openness, but at least one raised a warning
  (open PR, proof claim, or literature hits). Read the evidence before
  spending the fee. Caveat -- could not verify: arXiv.

  [OK] conjectures.io catalog API
        matched by title namespace erdos23; slug=erdos23-erdos-23;
        is_open=True; category=research open; attempts=0;
        bounty.available=True; bounty.reason=OPEN; bounty=3837.90 USD (as_of
        2026-09-14T01:07:00Z)
        -> https://conjectures.io/problems/erdos23-erdos-23
        -> https://conjectures.io/v1/catalog/conjectures

  [OK] erdosproblems.com tracker
        div.problem-text id="open"; tracker informal_status=falsifiable
        (open, and a single explicit counterexample disproves it -- the
        cheapest target shape on the subnet); tooltip: Open, but could be
        disproved with a finite counterexample.; proof claims: 0 ->
        /forum/thread/23/proof-claims; comments: 3 -> /forum/discuss/23;
        formalised statement: Yes -> https://github.com/google-
        deepmind/formal-
        conjectures/blob/main/FormalConjectures/ErdosProblems/23.lean;
        history revisions seen: 1; newest 2025-10-20T00:00:00Z
        -> https://www.erdosproblems.com/23
        -> https://www.erdosproblems.com/history/23

  [WARN] formal-conjectures upstream
        PR search total_count=16; open matches in title=2; OPEN PR #5349
        (2026-09-08) feat(ErdosProblems/23): weighted cycle background
        special case -> https://github.com/google-deepmind/formal-
        conjectures/pull/5349; OPEN PR #4118 (2026-05-30) ErdosProblems/1
        least_N_6: prove via {11,17,20,22,23,24} witness ->
        https://github.com/google-deepmind/formal-conjectures/pull/4118;
        statement file byte-identical between 7d1a8c99 and HEAD (sha256
        fd51a26b2790f5bb...); file: https://github.com/google-
        deepmind/formal-conjectures/blob/7d1a8c9912747679d0093f6d1216420c33e
        e5ffa/FormalConjectures/ErdosProblems/23.lean
        -> https://github.com/google-deepmind/formal-conjectures/pull/5349
        -> https://github.com/google-deepmind/formal-conjectures/pull/4118
        -> https://github.com/google-deepmind/formal-conjectures/blob/7d1a8c9912747679d0093f6d1216420c33ee5ffa/FormalConjectures/ErdosProblems/23.lean

  [OK] teorth/erdosproblems database
        status.state='falsifiable' (last_update 2025-08-31);
        informal_status.state='falsifiable';
        formal_status.state='unformalized'; formalized.state='yes'; open
        target, and a single explicit counterexample disproves it
        -> https://github.com/teorth/erdosproblems/blob/main/data/problems.yaml
        -> https://www.erdosproblems.com/23

  [UNKNOWN] arXiv
        skipped by --no-arxiv. arXiv's search services return HTTP 429 'Rate
        exceeded' (or hang) from many hosts, so it is often more useful to
        run this check by hand:
        https://arxiv.org/search/?searchtype=all&query=erdos23
        -> https://arxiv.org/search/?searchtype=all&query=erdos23

  [OK] Stack Exchange API (MathOverflow / Math.SE)
        mathoverflow: 10 raw intitle hit(s), 0 on-topic,
        quota_remaining=226; math: 10 raw intitle hit(s), 0 on-topic,
        quota_remaining=225; no on-topic question found (weak negative:
        search is title-scoped, so answers and body mentions are invisible)
        -> https://mathoverflow.net/search?q=Erdos%2023
        -> https://math.stackexchange.com/search?q=Erdos%2023
```

The `erdos944`, `erdos196` and `green15` blocks of the same run, **abridged**
(`…` marks elided lines; the `erdos23` block above is complete and unedited):

```
##############################################################################
# erdos944  ->  OPEN, BUT CHECK THE FLAGS
##############################################################################
  WHY: no source contradicts openness, but at least one raised a warning
  (open PR, proof claim, or literature hits). Read the evidence before
  spending the fee. Caveat -- could not verify: arXiv.

  [OK] conjectures.io catalog API
        matched by title namespace erdos944; slug=erdos944-erdos-944;
        is_open=True; category=research open; attempts=1;
        bounty.available=True; bounty.reason=OPEN; bounty=3356.35 USD (as_of
        2026-09-14T01:07:00Z)
        -> https://conjectures.io/problems/erdos944-erdos-944
        -> https://conjectures.io/v1/catalog/conjectures

  [WARN] erdosproblems.com tracker
        div.problem-text id="open"; tracker informal_status=open (fully
        open); tooltip: This is open, and cannot be resolved with a finite
        computation.; proof claims: 1 ->
        /forum/thread/944/proof-claims; comments: 3 -> /forum/discuss/944;
        formalised statement: Yes -> https://github.com/google-
        deepmind/formal-
        conjectures/blob/main/FormalConjectures/ErdosProblems/944.lean;
        history revisions seen: 1; newest 2025-10-20T00:00:00Z; NOTE: an
        open proof claim on the tracker is a freshness risk
        -> https://www.erdosproblems.com/944
        -> https://www.erdosproblems.com/history/944

  [WARN] formal-conjectures upstream
        PR search total_count=6; open matches in title=2; OPEN PR #5467
        (2026-09-10) Mark Erdős 944 Dirac conjecture and k = 4 case as
        solved -> https://github.com/google-deepmind/formal-
        conjectures/pull/5467; OPEN PR #4237 (2026-06-11) Erdős 944:
        machine-checked cores for the k=4, r=1 six-regular subproblem ->
        https://github.com/google-deepmind/formal-conjectures/pull/4237;
        statement file byte-identical between 7d1a8c99 and HEAD (sha256
        73d02fcfcf60c128...); ...
    [also: teorth database OK, arXiv UNKNOWN, Stack Exchange OK]
```

```
##############################################################################
# erdos196  ->  DO NOT ATTACK
##############################################################################
  WHY: the live catalog says the bounty is not payable
  (reason=ALREADY_SOLVED). Submitting cannot be paid; the 0.25 tau fee is a
  straight loss.

  [BAD] conjectures.io catalog API
        matched by title namespace erdos196; slug=erdos196-erdos-196;
        is_open=True; category=research open; attempts=1;
        bounty.available=False; bounty.reason=ALREADY_SOLVED; bounty=None
        USD (as_of 2026-09-14T01:07:00Z)
        -> https://conjectures.io/problems/erdos196-erdos-196
        -> https://conjectures.io/v1/catalog/conjectures

  [OK] erdosproblems.com tracker
        div.problem-text id="open"; tracker informal_status=open (fully
        open); tooltip: This is open, and cannot be resolved with a finite
        computation.; proof claims: 0 -> ...
```

Note that `erdos196`'s tracker block is a clean `OK` while the catalog is `BAD`.
**This is the lag, caught in the act**: the canonical tracker still shows 196 as
fully open on 2026-09-14, and the subnet has already stopped paying on it.

```
##############################################################################
# green15  ->  DO NOT ATTACK
##############################################################################
  WHY: the live catalog says the bounty is not payable
  (reason=ALREADY_SOLVED). Submitting cannot be paid; the 0.25 tau fee is a
  straight loss.

  [BAD] conjectures.io catalog API
        matched by title namespace green15; slug=green15-green-15;
        is_open=True; category=research open; attempts=1;
        bounty.available=False; bounty.reason=ALREADY_SOLVED; bounty=None
        USD (as_of 2026-09-14T01:07:00Z)

  [UNKNOWN] erdosproblems.com tracker
        not applicable: Green's Open Problems is a PDF, not a database. No
        per-problem tracker page exists (the tracker covers the Erdős
        problems only).
        -> https://people.maths.ox.ac.uk/greenbj/papers/open-problems.pdf
```

Footer:

```
==============================================================================
  5 target(s): 3 clear, 2 DO NOT ATTACK, 0 UNKNOWN
==============================================================================
```

### `--list-retired`

```
7 of 260 catalog rows are not payable (as_of 2026-09-14T01:02:00Z):
  erdos196-erdos-196                           reason=ALREADY_SOLVED
  erdos272-erdos-272-variants-szabo-strong     reason=ALREADY_SOLVED
  erdos726-erdos-726                           reason=ALREADY_SOLVED
  erdos96-erdos-96                             reason=ALREADY_SOLVED
  green15-green-15                             reason=ALREADY_SOLVED
  green47-green-47                             reason=ALREADY_SOLVED
  green51-green-51-one-half                    reason=ALREADY_SOLVED

cost per attempt: 250000000 rao = 0.25 tau (live from /v1/catalog/meta)
```

### `--json`

```json
{"generated_at": "2026-09-14T01:02:52+00:00",
 "pinned_commit": "8432eac998110a563e03df65a28c117e97c8c142",
 "meta": {"credit_price_rao": 250000000, "credit_price_tau": 0.25,
          "open_targets": 253, "treasury_balance_rao": 83971008893674,
          "repository_commit": "8432eac998110a563e03df65a28c117e97c8c142"},
 "targets": [{"slug": "erdos944", "verdict": "OPEN, BUT CHECK THE FLAGS", ...}]}
```

---

## 8. What I could not verify

Stated plainly, so nobody mistakes absence of evidence for evidence:

- **arXiv search never returned a result to me.** `429 Rate exceeded` on ~8 of 9
  `export.arxiv.org/api/query` calls and on every `arxiv.org/search/` call, over
  ~30 minutes. One `200` did come back (on the trivial `all:test`), so it is
  throttling, not a permanent block — but **I have never seen this endpoint
  return a real search result from this host**, and the script therefore reports
  arXiv as UNKNOWN. Do the literature pass by hand.
- **The pinned commit `8432eac9…` is not resolvable publicly** (422/404 on seven
  different routes across three repos). I used `7d1a8c99` and `2c817e97` as
  substitutes; I did not verify that they are byte-identical to what the pool was
  audited against. They are the references the repo's own `lean-source.json`,
  `POOL.md` and `selection-audit.json` name, and nothing better is published.
- **`conjectures-io/conjectures-subnet` does not exist** (HTTP 404); the org has
  five public repos (validator, tasks, miner, formal-conjectures,
  contribution).
- **The fee discrepancy is unresolved at the level of the website.**
  `how-it-works` says 0.5 τ, the validator README says 0.5 TAO, SubnetAlpha says
  0.5 TAO, and the live API says `credit_price_rao: 250000000` = 0.25 τ. I used
  the API number because it is the one that charges you, and it agrees with the
  rest of this guide — but I did not observe an actual charge.
- **`is_open` is true on all 260 rows even where `bounty.available` is false.**
  I could not find documentation explaining the semantics of `is_open`; my
  reading (upstream research-open status, distinct from payability) is inferred
  from the two fields disagreeing on exactly the seven `ALREADY_SOLVED` rows.
- **The tracker's `proof claims` count is a floor, not a total.** It counts
  claims filed on the tracker, not proofs posted on arXiv, GitHub, or
  elsewhere — which is the entire failure mode this document exists to work
  around.
- **Nothing here is financial or legal advice,** and no check replaces reading
  the actual statement at the pinned revision. `freshness_check.py` tells you
  whether the bounty is live; it cannot tell you whether the target is easy, and
  it cannot tell you whether the *statement you are attacking* is faithful to
  the informal problem.

---

## 9. The procedure

Run this on the day you submit, not on the day you start.

1. `python3 scripts/freshness_check.py <slug>` — read the verdict.
2. If **`DO NOT ATTACK`**: stop. You have saved 0.25 τ and a week.
3. If **`UNKNOWN`**: resolve the named source by hand before proceeding. Do not
   read it as open.
4. If **`LIKELY OPEN`**: proceed, but re-run immediately before `conjectures pay`
   — `bounty.as_of` moves by the minute.
5. If **`OPEN, BUT CHECK THE FLAGS`**: open every evidence link. An open PR
   titled "…as solved" is the single best predictor of an
   `Already solved before this submission` rejection, and it is invisible to
   every other check in this guide.
6. Do the arXiv pass manually (`--no-arxiv` plus a browser), searching the
   *mathematics* and not just the problem number.
7. Build the verifier locally and run `conjectures verify` — it is free — before
   `conjectures pay`.

```bash
# the whole thing, end to end
python3 scripts/freshness_check.py --no-arxiv "$SLUG" && \
  conjectures verify && conjectures pay
```
