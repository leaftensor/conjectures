#!/usr/bin/env python3
"""freshness_check.py -- is a conjectures.io target still worth attacking?

Answers, with evidence links, the one question that decides whether a 0.25 tau
submission fee (0.25 tau, read live from the catalog API) is worth spending:
*is the bounty on this target still payable,
as of today?*

Design rules
------------
1. The conjectures.io catalog API is the ONLY authority on bounty payability.
   It publishes a per-target `bounty.available` flag and a `bounty.reason`.
   Everything else in this script is corroborating evidence, never the verdict.
2. No source is allowed to lie. If a source is unreachable, rate-limited, or
   returns something we cannot parse, the check reports UNKNOWN for that source
   and the reason (HTTP status / exception). It never guesses "open".
3. Dependency-light: stdlib only (`urllib`, `json`, `re`, `argparse`, ...).
   `requests` is used only if it happens to be importable.

Usage
-----
    python3 scripts/freshness_check.py erdos944 erdos196 green15
    python3 scripts/freshness_check.py --json erdos944
    python3 scripts/freshness_check.py --from-catalog data/targets.json
    python3 scripts/freshness_check.py --list-retired

Target slug forms accepted
--------------------------
    erdos944        -> ErdosProblems/944.lean      (tracker page /944)
    erdos196        -> ErdosProblems/196.lean      (tracker page /196)
    green15         -> GreensOpenProblems/15.lean  (no tracker page: Green's
                       Open Problems is a PDF, not a database)

Exit codes
----------
    0  every target is OK to attack (catalog says the bounty is payable)
    1  at least one target is NOT payable / looks settled
    2  at least one target could not be decided (source unreachable)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# --------------------------------------------------------------------------
# Constants -- every endpoint below was fetched for real while writing this.
# --------------------------------------------------------------------------

UA = "conjectures-freshness-check/1.0 (+miner pre-flight; contact: local)"

#: Live catalog. Unauthenticated. THE authority on bounty payability.
#: `limit` is capped at 100; asking for more returns HTTP 400 with an
#: RFC-7807 body: {"title":"Malformed request","errors":[{"location":
#: "query.limit","message":"Input should be less than or equal to 100"}]}.
CATALOG_URL = "https://conjectures.io/v1/catalog/conjectures"
CATALOG_PAGE_LIMIT = 100  # hard server-side maximum

#: Catalog metadata: the live submission price and treasury state. Observed
#: 2026-09-14 HTTP 200. `credit_price_rao: 250000000` -> 0.25 tau per attempt.
#: (The website's how-it-works page says 0.5 tau and the validator README says
#: 0.5 TAO; the API is what actually charges you, so we report what it says.)
CATALOG_META_URL = "https://conjectures.io/v1/catalog/meta"

#: Thomas Bloom's canonical tracker. One HTML page per problem. No API, no
#: RSS/Atom (all of /feed, /rss, /atom.xml, /feed.xml, /sitemap.xml, /api
#: return HTTP 404). We poll HTML.
TRACKER_PROBLEM = "https://www.erdosproblems.com/{n}"
TRACKER_HISTORY = "https://www.erdosproblems.com/history/{n}"
TRACKER_FORUM_SEARCH = "https://www.erdosproblems.com/forum/search?q={q}"

#: The subnet's own declared status sources, from
#: conjectures-tasks/tiers/tier-1/selection-audit.json -> source_status_sources
ERDOS_DB_RAW = (
    "https://raw.githubusercontent.com/teorth/erdosproblems/main/data/problems.yaml"
)
GREEN_PDF = "https://people.maths.ox.ac.uk/greenbj/papers/open-problems.pdf"

#: Upstream statement repo + the subnet mirror.
FC_REPO = "google-deepmind/formal-conjectures"
GH_API = "https://api.github.com"

#: The commit the pool was pinned to. NOTE: it does NOT resolve on public
#: GitHub (HTTP 422 "No commit found for SHA" from api.github.com, HTTP 404
#: from github.com/.../commit/<sha>.patch). It is the value the catalog API
#: itself publishes as `repository_commit`, so we keep it for printing and
#: use a resolvable fallback for actual diffs.
PINNED_COMMIT = "8432eac998110a563e03df65a28c117e97c8c142"
#: Resolvable substitutes. `7d1a8c99` is the 2026-09-02 repin named in the
#: task pool's POOL.md; `2c817e97` is selection-audit.json's
#: `source_main_commit`. Both resolve on api.github.com (HTTP 200).
PIN_FALLBACKS = [
    "7d1a8c9912747679d0093f6d1216420c33ee5ffa",
    "2c817e975be7a95478b72a8429155ca568e1a3de",
]

SE_API = "https://api.stackexchange.com/2.3/search/advanced"
ARXIV_API = "https://export.arxiv.org/api/query"

TIMEOUT = 30
OK, WARN, BAD, UNKNOWN = "OK", "WARN", "BAD", "UNKNOWN"


# --------------------------------------------------------------------------
# HTTP helper -- never raises; returns (status, text, error)
# --------------------------------------------------------------------------

try:  # optional
    import requests  # type: ignore

    _HAVE_REQUESTS = True
except Exception:  # pragma: no cover
    _HAVE_REQUESTS = False


def http_get(url, accept="text/html,*/*", timeout=TIMEOUT, params=None):
    """GET `url`. Returns (status:int|None, text:str, err:str|None).

    Never raises. On failure status is None and err explains why, so callers
    can report UNKNOWN honestly instead of fabricating a result.
    """
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    headers = {"User-Agent": UA, "Accept": accept}
    if _HAVE_REQUESTS:
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            return r.status_code, r.text, None
        except Exception as e:  # noqa: BLE001
            return None, "", f"{type(e).__name__}: {e}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return r.status, raw.decode("utf-8", "replace"), None
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            body = ""
        return e.code, body, None
    except Exception as e:  # noqa: BLE001
        return None, "", f"{type(e).__name__}: {e}"


def http_get_json(url, **kw):
    st, txt, err = http_get(url, accept="application/json", **kw)
    if err:
        return st, None, err
    if st != 200:
        return st, None, f"HTTP {st}"
    try:
        return st, json.loads(txt), None
    except Exception as e:  # noqa: BLE001
        return st, None, f"non-JSON body: {type(e).__name__}"


# --------------------------------------------------------------------------
# Target slug parsing
# --------------------------------------------------------------------------

FAMILY_PATTERNS = [
    # (family,   regex,                     tracker-number group)
    ("erdos", re.compile(r"^erdos0*(\d+)(?:[-_].*)?$", re.I), 1),
    ("green", re.compile(r"^green0*(\d+)(?:[-_].*)?$", re.I), 1),
]


def parse_target(slug):
    """'erdos944' -> dict(family='erdos', number='944', tracker_n='944', ...)."""
    s = slug.strip()
    for family, rx, _ in FAMILY_PATTERNS:
        m = rx.match(s)
        if m:
            num = m.group(1)
            if family == "erdos":
                path = f"FormalConjectures/ErdosProblems/{num}.lean"
                tracker = f"https://www.erdosproblems.com/{num}"
            else:
                path = f"FormalConjectures/GreensOpenProblems/{num}.lean"
                tracker = None  # Green's problems are not in the tracker DB
            return {
                "slug": s,
                "family": family,
                "number": num,
                "source_path": path,
                "tracker_url": tracker,
            }
    return {
        "slug": s,
        "family": "unknown",
        "number": None,
        "source_path": None,
        "tracker_url": None,
    }


# --------------------------------------------------------------------------
# Source 1: conjectures.io live catalog  (THE verdict)
# --------------------------------------------------------------------------


def fetch_catalog(verbose=True):
    """Return (items, meta, error). Pages the API at limit=100."""
    items, offset, meta = [], 0, {}
    while True:
        st, d, err = http_get_json(
            CATALOG_URL, params={"limit": CATALOG_PAGE_LIMIT, "offset": offset}
        )
        if err:
            if offset == 0:
                return [], {}, f"catalog unreachable: {err}"
            return items, meta, f"catalog page {offset} failed: {err}"
        if not isinstance(d, dict) or "items" not in d:
            return items, meta, "catalog returned an unexpected shape"
        meta = {
            "total": d.get("total"),
            "repository_commit": d.get("repository_commit"),
            "as_of": (d["items"][0]["bounty"].get("as_of") if d["items"] else None),
        }
        items.extend(d["items"])
        if verbose:
            print(
                f"    catalog: offset={offset} +{len(d['items'])} "
                f"of {d.get('total')}",
                file=sys.stderr,
            )
        if offset + CATALOG_PAGE_LIMIT >= (d.get("total") or 0):
            break
        offset += CATALOG_PAGE_LIMIT
        time.sleep(0.3)
    return items, meta, None


def fetch_meta():
    """Live submission price + treasury, from GET /v1/catalog/meta.

    Returns (meta:dict, error). This is the number that actually decides
    whether a check is worth running: cost per attempt vs bounty on offer.
    """
    st, d, err = http_get_json(CATALOG_META_URL)
    if err or not isinstance(d, dict):
        return {}, f"meta unreachable: {err or st}"
    return d, None


def catalog_lookup(items, target):
    """Match a target slug to a catalog row.

    The catalog's public `slug` is '<theorem-lowercased-with-dashes>' e.g.
    'erdos196-erdos-196', not the short 'erdos196' used in the task pool.
    We therefore match on the `title` field ('Erdos196.erdos_196'), whose
    first dotted component is exactly the pool's short slug.
    """
    want = target["slug"].lower().replace("_", "-")
    fam, num = target["family"], target["number"]

    # 1. exact public slug
    for it in items:
        if it.get("slug", "").lower() == want:
            return it, "exact slug"
    # 2. title's namespace component, e.g. 'Erdos196.erdos_196' -> 'erdos196'
    if fam in ("erdos", "green"):
        for it in items:
            ns = (it.get("title") or "").split(".")[0].lower()
            if ns == f"{fam}{num}":
                return it, f"title namespace {ns}"
    # 3. no reliable match -> report candidates rather than guess
    if fam in ("erdos", "green"):
        cands = [
            it["slug"]
            for it in items
            if it.get("slug", "").lower().startswith(f"{fam}{num}")
        ][:5]
        return None, ("no row; similar slugs: " + ", ".join(cands)) if cands else "no row"
    return None, "unknown family; cannot match"


def check_catalog(target, items, meta, err):
    if err:
        return {
            "source": "conjectures.io catalog API",
            "status": UNKNOWN,
            "detail": err,
            "evidence": [CATALOG_URL],
        }
    it, how = catalog_lookup(items, target)
    if it is None:
        return {
            "source": "conjectures.io catalog API",
            "status": BAD,
            "detail": (
                f"target NOT offered by the live catalog ({how}) -- either "
                "retired or the slug is wrong. If it is not offered you "
                "cannot be paid on it."
            ),
            "evidence": [CATALOG_URL],
        }
    b = it.get("bounty") or {}
    avail = b.get("available")
    reason = b.get("reason")
    detail = (
        f"matched by {how}; slug={it.get('slug')}; is_open={it.get('is_open')}; "
        f"category={it.get('category')}; attempts={it.get('attempts')}; "
        f"bounty.available={avail}; bounty.reason={reason}; "
        f"bounty={b.get('amount_usd')} USD (as_of {b.get('as_of')})"
    )
    return {
        "source": "conjectures.io catalog API",
        "status": OK if avail else BAD,
        "detail": detail,
        "evidence": [f"https://conjectures.io/problems/{it.get('slug')}", CATALOG_URL],
        "bounty_available": avail,
        "bounty_reason": reason,
        "bounty_usd": b.get("amount_usd"),
        "catalog_slug": it.get("slug"),
        "catalog_as_of": b.get("as_of"),
    }


# --------------------------------------------------------------------------
# Source 2: erdosproblems.com tracker page (HTML poll; no API exists)
# --------------------------------------------------------------------------

# Observed markup (problem 944, fetched 2026-09-14):
#   <div class="problem-text" id="open">
#     <div id="prize">
#       <span class="tooltip">OPEN
#         <span class="tooltiptext">This is open, and cannot be resolved
#                                with a finite computation.</span>
#
# The `id` on `div.problem-text` IS the status. Values seen in the wild:
#   id="open"    tooltip "... is open, and cannot be resolved ..."
#   id="solved"  tooltip "This has been solved in the affirmative and the
#                proof verified in Lean."  (problem 728)
#   id="solved"  tooltip "This has been solved in the negative and the
#                proof verified in Lean."  (problem 1)
RE_STATUS_ID = re.compile(r'<div class="problem-text" id="([^"]+)"')
RE_TOOLTIP = re.compile(r'<span class="tooltiptext">\s*(.*?)\s*</span>', re.S)
RE_PROOF_CLAIMS = re.compile(
    r'href="/forum/thread/([^"/]+)/proof-claims"[^>]*>\s*'
    r"<span>Proof claims \((\d+)\)</span>"
)
RE_COMMENTS = re.compile(
    r'href="/forum/discuss/([^"]+)"[^>]*>\s*<span>Comments \((\d+)\)</span>'
)
RE_FORMALISED = re.compile(
    r'<span class="problem-info-label">Formalised statement\?</span>\s*<span>\s*'
    r'(?:<a href="([^"]+)"[^>]*>\s*(Yes|No)\s*</a>|(\w+))',
    re.S,
)
# /history/<n> lists revisions, newest first, each headed by an ISO timestamp.
RE_HIST_DATE = re.compile(r">\s*(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})\s*<")

#: Observed status vocabulary of erdosproblems.com (all fetched 2026-09-14).
#: The `id` on div.problem-text is only ever "open" or "solved" -- the nuance
#: lives in the tooltip text. Mapping tooltip -> the tracker database's
#: informal_status vocabulary (schema/problems.schema.json). The `solved`
#: column means "the site is done with it, so no freshness left to win".
TRACKER_VOCAB = [
    # (tooltip substring, informal_status, div id, note)
    ("cannot be resolved with a finite computation", "open", "open",
     "fully open"),
    ("could be proved with a finite example", "verifiable", "open",
     "open, but a finite witness would settle it -- this is the counterexample/"
     "formalized mode's sweet spot"),
    ("could be disproved with a finite counterexample", "falsifiable", "open",
     "open, and a single explicit counterexample disproves it -- the cheapest "
     "target shape on the subnet"),
    ("there exist models of set theory where the result is false",
     "not provable", "open", "open in ZFC but false in some models"),
    ("Independent of the usual axioms of set theory", "independent", "solved",
     "independent of ZFC -- retired"),
    ("Resolved up to a finite check", "decidable", "solved",
     "resolved up to a finite check -- retired"),
    ("resolved in some other way than a proof or disproof", "solved", "solved",
     "resolved by other means, verified in Lean -- retired"),
    ("solved in the affirmative", "proved", "solved", "proved -- retired"),
    ("solved in the negative", "disproved", "solved", "disproved -- retired"),
]


def classify_tooltip(tip):
    """tooltip text -> (informal_status, note). Falls back honestly."""
    t = (tip or "").lower()
    for frag, state, _id, note in TRACKER_VOCAB:
        if frag.lower() in t:
            return state, note
    return None, "unrecognised tooltip -- read the page by hand"


def check_tracker(target):
    if not target["tracker_url"]:
        return {
            "source": "erdosproblems.com tracker",
            "status": UNKNOWN,
            "out_of_scope": True,
            "detail": (
                "not applicable: Green's Open Problems is a PDF, not a database. "
                "No per-problem tracker page exists (the tracker covers the "
                "Erdős problems only)."
            ),
            "evidence": [GREEN_PDF],
        }
    url = target["tracker_url"]
    st, html, err = http_get(url)
    if err or st != 200:
        return {
            "source": "erdosproblems.com tracker",
            "status": UNKNOWN,
            "detail": f"HTTP {st} {err or ''}".strip(),
            "evidence": [url],
        }
    m_id = RE_STATUS_ID.search(html)
    if not m_id:
        return {
            "source": "erdosproblems.com tracker",
            "status": UNKNOWN,
            "detail": (
                "page fetched but the status div "
                "(<div class=\"problem-text\" id=\"...\">) was not found -- "
                "the markup may have changed; inspect by hand."
            ),
            "evidence": [url],
        }
    state = m_id.group(1).strip().lower()
    tip = RE_TOOLTIP.search(html)
    tip = re.sub(r"\s+", " ", tip.group(1)).strip() if tip else ""
    pc = RE_PROOF_CLAIMS.search(html)
    cc = RE_COMMENTS.search(html)
    fo = RE_FORMALISED.search(html)

    bits = [f'div.problem-text id="{state}"']
    informal, vocab_note = classify_tooltip(tip)
    if informal:
        bits.append(f"tracker informal_status={informal} ({vocab_note})")
    elif tip:
        bits.append(f"UNRECOGNISED tooltip ({vocab_note})")
    if tip:
        bits.append(f"tooltip: {tip}")
    if pc:
        bits.append(f"proof claims: {pc.group(2)} -> /forum/thread/{pc.group(1)}/proof-claims")
    if cc:
        bits.append(f"comments: {cc.group(2)} -> /forum/discuss/{cc.group(1)}")
    if fo:
        if fo.group(1):
            bits.append(f"formalised statement: {fo.group(2)} -> {fo.group(1)}")
        elif fo.group(3):
            bits.append(f"formalised statement: {fo.group(3)}")

    # newest revision date, a proxy for "when did the tracker last move?"
    hst, hhtml, herr = http_get(TRACKER_HISTORY.format(n=target["number"]))
    if not herr and hst == 200:
        dates = sorted({f"{a}T{b}Z" for a, b in RE_HIST_DATE.findall(hhtml)})
        if dates:
            bits.append(f"history revisions seen: {len(dates)}; newest {dates[-1]}")

    # 'open' is the only id that means genuinely open. Anything else
    # (solved, disproved, ...) is a red flag.
    status = OK if state == "open" else BAD
    if pc and int(pc.group(2)) > 0:
        status = WARN if status == OK else status
        bits.append("NOTE: an open proof claim on the tracker is a freshness risk")
    return {
        "source": "erdosproblems.com tracker",
        "status": status,
        "detail": "; ".join(bits),
        "evidence": [url, TRACKER_HISTORY.format(n=target["number"])],
    }


# --------------------------------------------------------------------------
# Source 3: upstream formal-conjectures -- PRs, file drift
# --------------------------------------------------------------------------


def check_upstream(target, pinned_ok):
    """Look for open PRs touching this statement, and for file drift."""
    if not target["source_path"]:
        return {
            "source": "formal-conjectures upstream",
            "status": UNKNOWN,
            "detail": "unrecognised slug; cannot derive a source_path",
            "evidence": [],
        }
    num = target["number"]
    fam = target["family"]
    bits, ev, status = [], [], OK

    # (a) open PRs mentioning the problem number. Search is title-scoped
    #     because body search would match every PR that merely cites /N.
    q = f"repo:{FC_REPO} is:pr {num} in:title"
    st, d, err = http_get_json(
        f"{GH_API}/search/issues",
        params={"q": q, "per_page": 20, "sort": "created", "order": "desc"},
    )
    if err:
        key = f"open PRs titled '{num}'"
        bits.append(f"{key}: UNKNOWN ({err})")
        status = UNKNOWN
    else:
        found = [
            it
            for it in (d.get("items") or [])
            if it.get("state") == "open" and re.search(rf"\b{num}\b", it.get("title", ""))
        ]
        if d.get("total_count") is not None:
            bits.append(
                f"PR search total_count={d['total_count']}; "
                f"open matches in title={len(found)}"
            )
        for it in found[:5]:
            bits.append(
                f"OPEN PR #{it['number']} ({it.get('created_at','')[:10]}) "
                f"{it.get('title','')[:90]} -> {it.get('html_url')}"
            )
            ev.append(it.get("html_url"))
        if found:
            status = WARN  # an open PR claiming a solution is a real risk

    # (b) file drift: is the statement unchanged since the pin?
    #     The documented pin does not resolve publicly, so fall back to the
    #     resolvable repin commit rather than to HEAD (comparing HEAD with
    #     HEAD would be a vacuous check that always passes).
    ref = PINNED_COMMIT if pinned_ok else PIN_FALLBACKS[0]
    raw = (
        f"https://raw.githubusercontent.com/{FC_REPO}/{ref}/{target['source_path']}"
    )
    st2, txt_pin, err2 = http_get(raw, accept="text/plain")
    if err2 or st2 != 200:
        bits.append(f"pinned source fetch @{ref[:8]}: HTTP {st2} {err2 or ''}".strip())
        status = UNKNOWN if status == OK else status
    else:
        import hashlib

        h_pin = hashlib.sha256(txt_pin.encode()).hexdigest()
        raw_head = (
            f"https://raw.githubusercontent.com/{FC_REPO}/HEAD/{target['source_path']}"
        )
        st3, txt_head, err3 = http_get(raw_head, accept="text/plain")
        if err3 or st3 != 200:
            bits.append(f"HEAD source fetch: HTTP {st3} {err3 or ''}".strip())
        else:
            h_head = hashlib.sha256(txt_head.encode()).hexdigest()
            if h_pin == h_head:
                bits.append(
                    f"statement file byte-identical between {ref[:8]} and HEAD "
                    f"(sha256 {h_head[:16]}...)"
                )
            else:
                bits.append(
                    f"STATEMENT CHANGED upstream: {ref[:8]} sha256 {h_pin[:16]}... "
                    f"!= HEAD sha256 {h_head[:16]}... -- re-read the statement "
                    "before attacking"
                )
                status = WARN if status == OK else status
        bits.append(
            f"file: https://github.com/{FC_REPO}/blob/{ref}/"
            f"{target['source_path']}"
        )
        ev.append(
            f"https://github.com/{FC_REPO}/blob/{ref}/{target['source_path']}"
        )

    return {
        "source": "formal-conjectures upstream",
        "status": status,
        "detail": "; ".join(bits),
        "evidence": ev,
        "prs_open": [
            x for x in ev if "/pull/" in x
        ],
    }


def resolve_pin():
    """Does the documented pinned commit resolve on public GitHub?

    Observed 2026-09-14: NO. api.github.com -> HTTP 422 "No commit found for
    SHA"; github.com/<sha>.patch -> HTTP 404; the compare endpoint -> HTTP 404.
    The fallbacks do resolve (HTTP 200), so we use them for drift checks.
    """
    st, d, err = http_get_json(f"{GH_API}/repos/{FC_REPO}/commits/{PINNED_COMMIT}")
    if err or st != 200:
        return False, f"pinned commit {PINNED_COMMIT[:12]} does not resolve: {err or st}"
    return True, "pinned commit resolves"


# --------------------------------------------------------------------------
# Source 4: teorth/erdosproblems database (machine-readable status)
# --------------------------------------------------------------------------


def fetch_erdos_db(verbose=True):
    """Return (by_number, error). The file is YAML; we parse it minimally.

    `data/problems.yaml` is the machine-readable form of the tracker database
    (1217 entries as of 2026-09-14), maintained by teorth/erdosproblems and
    refreshed from the site. Per entry we read:
        informal_status.state  -- human mathematical status  (open/proved/...)
        formal_status.state    -- "unformalized" | "Lean"   (solution formalized?)
        status.state           -- derived: informal, with " (Lean)" appended
        formalized.state       -- is the *statement* in formal-conjectures?
    """
    st, txt, err = http_get(ERDOS_DB_RAW, accept="text/plain", timeout=60)
    if err or st != 200:
        return {}, f"HTTP {st} {err or ''}".strip()
    by_number = _parse_erdos_yaml(txt)
    if verbose:
        print(f"    erdos db: {len(by_number)} entries", file=sys.stderr)
    return by_number, None


def _parse_erdos_yaml(txt):
    """Minimal YAML reader for data/problems.yaml (fixed 2-space shape)."""
    out = {}
    cur = None
    section = None
    for raw in txt.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = re.match(r'^-\s*number:\s*"?([0-9\-]+)"?', raw)
        if m:
            cur = {"number": m.group(1)}
            out[m.group(1)] = cur
            section = None
            continue
        if cur is None:
            continue
        m = re.match(r"^(\s+)([a-z_]+):\s*(.*)$", raw)
        if not m:
            continue
        indent, key, val = len(m.group(1)), m.group(2), m.group(3).strip()
        if indent == 2:
            if val == "":
                section = key  # e.g. informal_status / status / formal_status
                cur.setdefault(section, {})
            else:
                cur[key] = val.strip('"')
                section = None
        elif indent >= 4 and section:
            cur.setdefault(section, {})[key] = val.strip('"')
    return out


#: informal_status values that mean "the site is done with this problem".
#: Everything else in the schema's vocabulary is still a live target:
#: open (591), proved (334), disproved (139), solved (101), falsifiable (25),
#: decidable (9), verifiable (7), independent (4), not disprovable (4),
#: not provable (3)   <- distribution as of 2026-09-14.
SETTLED_STATES = {"proved", "disproved", "solved", "independent"}
#: states that are open AND have a cheap shape -- worth surfacing by name.
OPEN_SHAPES = {
    "falsifiable": "a single explicit counterexample disproves it",
    "verifiable": "a single explicit witness proves it",
    "decidable": "resolvable by a finite computation",
    "not provable": "not provable in ZFC, but false in some models",
    "not disprovable": "not disprovable in ZFC",
    "open": "plain open problem",
}


def check_erdos_db(target, db, err):
    if err:
        return {
            "source": "teorth/erdosproblems database",
            "status": UNKNOWN,
            "detail": err,
            "evidence": [ERDOS_DB_RAW],
        }
    if target["family"] != "erdos":
        return {
            "source": "teorth/erdosproblems database",
            "status": UNKNOWN,
            "out_of_scope": True,
            "detail": (
                "not applicable: this database holds the Erdős problems only. "
                "The subnet's declared status source for Green's Open Problems "
                f"is the PDF itself ({GREEN_PDF}, revision 2026-01 per "
                "selection-audit.json)."
            ),
            "evidence": [ERDOS_DB_RAW, GREEN_PDF],
        }
    rec = db.get(target["number"])
    if not rec:
        return {
            "source": "teorth/erdosproblems database",
            "status": UNKNOWN,
            "detail": f"problem {target['number']} not present in problems.yaml",
            "evidence": [ERDOS_DB_RAW],
        }
    status_block = rec.get("status") or {}
    informal = rec.get("informal_status") or {}
    formal = rec.get("formal_status") or {}
    formalized = rec.get("formalized") or {}
    state = status_block.get("state") or informal.get("state")
    detail = (
        f"status.state={state!r} (last_update {status_block.get('last_update')}); "
        f"informal_status.state={informal.get('state')!r}; "
        f"formal_status.state={formal.get('state')!r}; "
        f"formalized.state={formalized.get('state')!r}"
    )
    # informal_status is the human/mathematical truth we care about. Only the
    # SETTLED_STATES mean the site is done with it; 'falsifiable'/'verifiable'
    # and friends are still live targets with a cheap shape.
    inf = (informal.get("state") or "").lower()
    if inf in SETTLED_STATES:
        st = BAD
        detail += f"; '{inf}' is a settled state -- no freshness left to win"
    elif inf in OPEN_SHAPES:
        st = OK
        detail += f"; open target, and {OPEN_SHAPES[inf]}"
    else:
        st = UNKNOWN
        detail += f"; unrecognised informal_status {inf!r} -- read the page"
    if formal.get("state") and formal.get("state") != "unformalized":
        detail += (
            f"; note: a {formal['state']} solution proof already exists "
            f"({formal.get('url', 'no url')}) -- a solution is known, only the "
            "bounty state in the catalog is authoritative"
        )
    return {
        "source": "teorth/erdosproblems database",
        "status": st,
        "detail": detail,
        "evidence": [
            "https://github.com/teorth/erdosproblems/blob/main/data/problems.yaml",
            f"https://www.erdosproblems.com/{target['number']}",
        ],
    }


# --------------------------------------------------------------------------
# Source 5: arXiv (metadata only; full text NOT indexed)
# --------------------------------------------------------------------------


def check_arxiv(target, lookback_days):
    if target["family"] == "erdos":
        term = f'Erdos problem {target["number"]}'
    elif target["family"] == "green":
        term = f"Green open problem {target['number']}"
    else:
        term = target["slug"]
    params = {
        "search_query": f'all:"{term}"',
        "start": 0,
        "max_results": 10,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    # Short timeout on purpose: when arXiv throttles the search services it
    # does so by hanging or 429ing, and we would rather report UNKNOWN than
    # stall the whole run for every target.
    st, txt, err = http_get(
        ARXIV_API, accept="application/atom+xml", params=params, timeout=20
    )
    if err or st != 200:
        # Observed 2026-09-14 from this host: HTTP 429 "Rate exceeded." for
        # every call, on /api/query AND on the /search HTML page, while
        # /abs/<id> and /list/<cat>/recent return 200. arXiv throttles the
        # *search* services; it is not a permanent block.
        return {
            "source": "arXiv",
            "status": UNKNOWN,
            "detail": (
                f"HTTP {st} {err or ''} -- arXiv search is rate-limited/"
                "blocked from this host. NOT a statement that nothing was "
                "published. Check by hand: "
                "https://arxiv.org/search/?searchtype=all&query="
                + urllib.parse.quote(term)
            ),
            "evidence": [f"https://arxiv.org/search/?searchtype=all&query={urllib.parse.quote(term)}"],
            "blocked": True,
        }
    titles = re.findall(r"<title>(.*?)</title>", txt, re.S)
    entries = re.findall(r"<entry>(.*?)</entry>", txt, re.S)
    hits = []
    for e in entries:
        t = re.search(r"<title>(.*?)</title>", e, re.S)
        p = re.search(r"<published>(.*?)</published>", e, re.S)
        i = re.search(r"<id>(.*?)</id>", e, re.S)
        if t:
            hits.append(
                {
                    "title": re.sub(r"\s+", " ", t.group(1)).strip(),
                    "published": (p.group(1)[:10] if p else ""),
                    "url": (i.group(1) if i else ""),
                }
            )
    detail = (
        f"query=all:\"{term}\" (metadata-only search: arXiv does NOT index "
        f"full text, so a paper that proves the result without naming the "
        f"problem number will be missed); {len(hits)} hit(s)"
    )
    for h in hits[:5]:
        detail += f"; {h['published']} {h['title'][:80]} {h['url']}"
    return {
        "source": "arXiv",
        "status": WARN if hits else OK,
        "detail": detail,
        "evidence": [h["url"] for h in hits[:5]]
        or [f"http://export.arxiv.org/api/query?search_query=all:%22{urllib.parse.quote(term)}%22"],
    }


# --------------------------------------------------------------------------
# Source 6: MathOverflow / Math.SE via the Stack Exchange API
# --------------------------------------------------------------------------


def check_stackexchange(target):
    """Search MathOverflow / Math.SE through the Stack Exchange API.

    Caveat observed in practice: `intitle=` is a loose match. Querying
    intitle="Erdos 944" returns unrelated questions about matrix cofactors,
    because the terms are OR-matched. We therefore post-filter for a hit that
    actually contains the problem number as a token AND a conjecture word.
    """
    if target["family"] == "erdos":
        term = f"Erdos {target['number']}"
        num_re = re.compile(rf"\b{re.escape(target['number'])}\b")
    elif target["family"] == "green":
        term = f"Green {target['number']}"
        num_re = re.compile(rf"\b{re.escape(target['number'])}\b")
    else:
        term = target["slug"]
        num_re = re.compile(r"$^")  # never matches

    keyword_re = re.compile(r"erd[oő]s|conjecture|problem|green", re.I)

    lines, relevant, blocked = [], [], False
    for site in ("mathoverflow", "math"):
        st, d, err = http_get_json(
            SE_API,
            params={
                "order": "desc",
                "sort": "relevance",
                "intitle": term,
                "site": site,
                "pagesize": 10,
                "filter": "default",
            },
        )
        if err:
            blocked = True
            lines.append(f"{site}: UNKNOWN ({err})")
            continue
        items = (d or {}).get("items") or []
        hits = [
            it for it in items
            if num_re.search(it.get("title", "")) and keyword_re.search(it.get("title", ""))
        ]
        lines.append(
            f"{site}: {len(items)} raw intitle hit(s), {len(hits)} on-topic, "
            f"quota_remaining={(d or {}).get('quota_remaining')}"
        )
        for it in hits[:4]:
            lines.append(f"  {it.get('title','')[:80]} -> {it.get('link')}")
            relevant.append(it.get("link"))
    if blocked:
        status = UNKNOWN
    elif relevant:
        status = WARN
    else:
        status = OK
        lines.append("no on-topic question found (weak negative: search is "
                     "title-scoped, so answers and body mentions are invisible)")
    return {
        "source": "Stack Exchange API (MathOverflow / Math.SE)",
        "status": status,
        "detail": "; ".join(lines),
        "evidence": relevant[:5]
        or [
            f"https://mathoverflow.net/search?q={urllib.parse.quote(term)}",
            f"https://math.stackexchange.com/search?q={urllib.parse.quote(term)}",
        ],
    }


# --------------------------------------------------------------------------
# Verdict
# --------------------------------------------------------------------------

ORDER = {OK: 0, WARN: 1, UNKNOWN: 2, BAD: 3}


def verdict(checks):
    """Collapse per-source results into (verdict, why).

    BAD always wins: the catalog saying 'bounty not payable', or the tracker
    saying 'solved', is decisive. Unknowns are reported, never silently
    rounded to OK -- but we distinguish three kinds of UNKNOWN so the verdict
    stays useful:

      * `blocked`      -- the host is rate-limited (arXiv); a real gap, listed
                          as a caveat, but not evidence against freshness.
      * `out_of_scope` -- the source does not cover this problem family at all
                          (Green's problems are not in the Erdős database).
      * neither        -- an inconclusive gap. This forces UNKNOWN, because we
                          genuinely could not tell.
    """
    cat = next((c for c in checks if c["source"].startswith("conjectures.io")), None)
    trk = next((c for c in checks if c["source"].startswith("erdosproblems.com")), None)

    if cat and cat["status"] == BAD:
        if cat.get("bounty_available") is False:
            return (
                "DO NOT ATTACK",
                f"the live catalog says the bounty is not payable "
                f"(reason={cat.get('bounty_reason')}). Submitting cannot be "
                f"paid; the 0.25 tau fee is a straight loss.",
            )
        return ("DO NOT ATTACK", "target is not offered by the live catalog: "
                                 "retired, or the slug is wrong.")
    if trk and trk["status"] == BAD:
        return (
            "DO NOT ATTACK",
            "the canonical tracker no longer shows this problem as open.",
        )

    inconclusive = [
        c for c in checks
        if c["status"] == UNKNOWN
        and not c.get("blocked")
        and not c.get("out_of_scope")
    ]
    caveats = [c["source"] for c in checks if c.get("blocked") or c.get("out_of_scope")]

    if inconclusive:
        tail = (
            " Could not check: " + ", ".join(caveats) + "."
            if caveats else ""
        )
        return (
            "UNKNOWN",
            "a source that should have answered did not, so freshness is "
            "NOT established. Do not read UNKNOWN as 'open'." + tail,
        )

    worst = max(
        (ORDER[c["status"]] for c in checks
         if not c.get("out_of_scope") and not c.get("blocked")),
        default=OK,
    )
    name = {v: k for k, v in ORDER.items()}[worst]
    tail = (" Caveat -- could not verify: " + ", ".join(caveats) + ".") if caveats else ""
    if name == OK:
        return (
            "LIKELY OPEN",
            "every source that applied to this target agrees it is open." + tail,
        )
    if name == WARN:
        return (
            "OPEN, BUT CHECK THE FLAGS",
            "no source contradicts openness, but at least one raised a warning "
            "(open PR, proof claim, or literature hits). Read the evidence "
            "before spending the fee." + tail,
        )
    return (
        "UNKNOWN",
        "at least one source was unreachable or unparseable, so freshness is "
        "NOT established. Do not read UNKNOWN as 'open'." + tail,
    )


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

COLORS = {
    "OK": "\033[32m", "WARN": "\033[33m", "BAD": "\033[31m",
    "UNKNOWN": "\033[90m", "reset": "\033[0m",
}


def paint(s, k):
    if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
        return s
    return f"{COLORS.get(k,'')}{s}{COLORS['reset']}"


def run(slugs, as_json=False, lookback_days=90, from_catalog=None, need_catalog=True,
        skip_arxiv=False):
    if from_catalog:
        with open(from_catalog) as fh:
            data = json.load(fh)
        slugs = [row.get("slug") or row.get("theorem", "").split(".")[0] for row in data]
        slugs = [s for s in slugs if s]

    targets = [parse_target(s) for s in slugs]

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pinned_commit": PINNED_COMMIT,
        "meta": {},
        "targets": [],
    }

    catalog_items, catalog_meta, catalog_err = ([], {}, "skipped")
    meta, meta_err = ({}, "skipped")
    pin_ok, pin_msg = False, "not checked"
    db, db_err = ({}, "skipped")

    if need_catalog:
        print("Pre-flight: fetching the live conjectures.io catalog ...", file=sys.stderr)
        catalog_items, catalog_meta, catalog_err = fetch_catalog()
        if catalog_err:
            print(f"  !! catalog: {catalog_err}", file=sys.stderr)
        else:
            print(
                f"  catalog OK: {len(catalog_items)} rows, "
                f"total={catalog_meta.get('total')}, "
                f"as_of={catalog_meta.get('as_of')}, "
                f"repository_commit={catalog_meta.get('repository_commit')}",
                file=sys.stderr,
            )
        meta, meta_err = fetch_meta()
        if meta_err:
            print(f"  !! meta: {meta_err}", file=sys.stderr)
        else:
            rao = meta.get("credit_price_rao")
            print(
                f"  meta OK: credit_price_rao={rao} "
                f"({None if rao is None else rao / 1e9} tau per attempt), "
                f"open_targets={(meta.get('bounty') or {}).get('open_targets')}",
                file=sys.stderr,
            )
            report["meta"] = {
                "credit_price_rao": rao,
                "credit_price_tau": (rao / 1e9 if isinstance(rao, (int, float)) else None),
                "open_targets": (meta.get("bounty") or {}).get("open_targets"),
                "treasury_balance_rao": (meta.get("bounty") or {}).get("balance_rao"),
                "repository_commit": meta.get("repository_commit"),
            }
        pin_ok, pin_msg = resolve_pin()
        print(f"  pin: {pin_msg}", file=sys.stderr)
        print("Pre-flight: fetching the Erdős problems database ...", file=sys.stderr)
        db, db_err = fetch_erdos_db()
        if db_err:
            print(f"  !! erdos db: {db_err}", file=sys.stderr)

    for t in targets:
        print(f"\n--- {t['slug']} ---", file=sys.stderr)
        checks = []
        checks.append(check_catalog(t, catalog_items, catalog_meta, catalog_err))
        checks.append(check_tracker(t))
        checks.append(check_upstream(t, pin_ok))
        checks.append(check_erdos_db(t, db, db_err))
        if skip_arxiv:
            checks.append({
                "source": "arXiv",
                "status": UNKNOWN,
                "blocked": True,
                "detail": (
                    "skipped by --no-arxiv. arXiv's search services return "
                    "HTTP 429 'Rate exceeded' (or hang) from many hosts, so it "
                    "is often more useful to run this check by hand: "
                    "https://arxiv.org/search/?searchtype=all&query="
                    + urllib.parse.quote(t["slug"])
                ),
                "evidence": [
                    "https://arxiv.org/search/?searchtype=all&query="
                    + urllib.parse.quote(t["slug"])
                ],
            })
        else:
            checks.append(check_arxiv(t, lookback_days))
        checks.append(check_stackexchange(t))
        v, why = verdict(checks)
        report["targets"].append(
            {"slug": t["slug"], "family": t["family"], "number": t["number"],
             "verdict": v, "why": why, "checks": checks}
        )

    if as_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return _exit_code(report)

    print("=" * 78)
    print("TARGET FRESHNESS REPORT")
    print(f"  generated : {report['generated_at']}")
    print(f"  pool pin  : {PINNED_COMMIT}")
    if catalog_meta.get("as_of"):
        print(f"  catalog as_of: {catalog_meta['as_of']}")
    if report["meta"].get("credit_price_tau") is not None:
        print(
            f"  cost/attempt : {report['meta']['credit_price_tau']} tau "
            f"({report['meta']['credit_price_rao']} rao) -- live from "
            f"/v1/catalog/meta"
        )
    print("=" * 78)
    import textwrap

    for r in report["targets"]:
        tag = r["verdict"].split()[0]
        print(f"\n{'#' * 78}\n# {r['slug']}  ->  {paint(r['verdict'], tag)}\n{'#' * 78}")
        for line in textwrap.wrap("WHY: " + r["why"], 74):
            print(f"  {line}")
        for c in r["checks"]:
            print(f"\n  [{paint(c['status'], c['status'])}] {c['source']}")
            for line in textwrap.wrap(c["detail"], 68):
                print(f"        {line}")
            for e in c["evidence"][:6]:
                print(f"        -> {e}")
    print("\n" + "=" * 78)
    bad = [r for r in report["targets"] if r["verdict"].startswith("DO NOT")]
    unk = [r for r in report["targets"] if r["verdict"] == "UNKNOWN"]
    print(
        f"  {len(report['targets'])} target(s): "
        f"{len(report['targets']) - len(bad) - len(unk)} clear, "
        f"{len(bad)} DO NOT ATTACK, {len(unk)} UNKNOWN"
    )
    print("=" * 78)
    return _exit_code(report)


def _exit_code(report):
    if any(r["verdict"].startswith("DO NOT") for r in report["targets"]):
        return 1
    if any(r["verdict"] == "UNKNOWN" for r in report["targets"]):
        return 2
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Check whether conjectures.io targets are still worth attacking.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("slugs", nargs="*", help="target slugs, e.g. erdos944 green15")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--from-catalog", metavar="PATH",
                    help="read slugs from data/targets.json")
    ap.add_argument("--lookback-days", type=int, default=90,
                    help="literature lookback window (default 90)")
    ap.add_argument("--no-catalog", action="store_true",
                    help="skip the catalog API (offline-ish; verdicts become weaker)")
    ap.add_argument("--no-arxiv", action="store_true",
                    help="skip arXiv (its search API rate-limits most hosts); "
                         "records it as an explicit caveat instead of stalling")
    ap.add_argument("--list-retired", action="store_true",
                    help="just list every catalog row whose bounty is not payable")
    args = ap.parse_args(argv)

    if args.list_retired:
        items, meta, err = fetch_catalog()
        if err:
            print(f"catalog unreachable: {err}", file=sys.stderr)
            return 2
        m, m_err = fetch_meta()
        rao = m.get("credit_price_rao")
        bad = [i for i in items if not (i.get("bounty") or {}).get("available")]
        print(f"{len(bad)} of {len(items)} catalog rows are not payable "
              f"(as_of {meta.get('as_of')}):")
        for i in bad:
            b = i["bounty"]
            print(f"  {i['slug']:44} reason={b.get('reason')}")
        if rao:
            print(f"\ncost per attempt: {rao} rao = {rao / 1e9} tau "
                  f"({m_err or 'live from /v1/catalog/meta'})")
        return 1 if bad else 0

    if not args.slugs and not args.from_catalog:
        ap.print_help()
        return 0
    return run(
        args.slugs,
        as_json=args.json,
        lookback_days=args.lookback_days,
        from_catalog=args.from_catalog,
        need_catalog=not args.no_catalog,
        skip_arxiv=args.no_arxiv,
    )


if __name__ == "__main__":
    sys.exit(main())
