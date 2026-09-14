#!/usr/bin/env python3
"""Triage the live conjectures.io pool for formalization defects.

Five miners have been paid a `FORMALIZATION_DEFECT_AWARD` (USD 750 or the locked
bounty, whichever is less) for proving that a published Lean statement does not
mean what its informal conjecture means. This script applies the seven bug shapes
those awards were actually paid for, as filters, so a human reads the dozen
candidates that look like history instead of all 260 targets.

WHAT THIS IS NOT
----------------
It cannot certify a defect. Every rule here is a *heuristic on the Lean text*,
and the Lean text is exactly what is not the problem: the defect is the gap
between the Lean text and the prose. A high score means "read this one against
erdosproblems.com", never "this one is defective". Publishing a scan result as a
finding without doing the semantic read is how you waste a 0.25 tau submission.

The seven precedents, and where each one is encoded below, are documented in
`docs/03-attack-vectors.md`.

Usage
-----
    ./scripts/sync_pool.sh
    python3 scripts/defect_scan.py                       # top 25 candidates
    python3 scripts/defect_scan.py --min-score 6 --json  # machine-readable
    python3 scripts/defect_scan.py --only erdos15 erdos939
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Rule set. Each rule is (id, precedents, weight, pattern, what to check).
#
# Weight is a rough severity: 3 for a shape that produced a paid award on its
# own, 2 for a shape that contributed to one, 1 for a weak signal that is only
# meaningful in combination.
# ---------------------------------------------------------------------------

RULES = [
    (
        "ratio_vs_real",
        "Erdos15",
        3,
        r"ℚ|\bRat\b|Rational",
        "The type computes over the rationals. Erdős 15 was paid out because the informal "
        "problem asks for REAL convergence and the Lean statement used `Summable` over ℚ, "
        "so failing ℚ-summability proved nothing about the series. Compare the numeric domain "
        "in the type against the domain in the docstring and on erdosproblems.com.",
    ),
    (
        "unbounded_arithmetic_no_positivity",
        "Erdos939",
        3,
        # An arithmetic predicate over ℕ/ℤ with no positivity guard anywhere in the type.
        # This is the Erdős 939 shape and only that shape: the rule deliberately requires a
        # named number-theoretic predicate, because "quantifies over ℕ" describes most of
        # the pool and flags nothing.
        r"(?=.*(Prime|powerful|totient|factorial|Squarefree|Smooth|smoothNumber|gcd|Coprime|nth|divisor|Divisor|Perfect|Abundant|primorial))"
        r"(?!.*(0 <|≠ 0|0 <|Nat.Positive|NeZero))",
        "An unbounded number-theoretic predicate over ℕ/ℤ with no positivity or "
        "nontriviality guard in the type. Erdős 939 was paid out because `Erdos939Sums` "
        "omitted positivity and `Nat.Full` is vacuous at 0 and 1, so the case with no known "
        "example fell to the degenerate set {0, 1}. Substitute 0 and 1 and see whether the "
        "predicate is vacuously true, and check whether the prose excludes them in words.",
    ),
    (
        "coercion_ascription",
        "Erdos726",
        3,
        # Two renderings of the same bug, because they differ between the raw
        # source and the API.
        #
        #   raw source:  (n % p : ℝ)        <- the ascription form
        #   API's `type_pretty`:  ↑n % ↑p   <- the ascription is resolved away
        #
        # The API rewrite means a scan against `type_pretty` alone would MISS the
        # bug in its original form, and a scan against the source alone would miss
        # nothing. Take both. As a check: this rule fires on exactly one target in
        # the live pool -- `erdos726-erdos-726`, the one that was actually paid a
        # defect award for it. 1/1 on the known case.
        r"\([^()]*(?:%|/)[^()]*:\s*(?:ℝ|ℚ|ℂ)[^()]*\)"      # (n % p : ℝ)
        r"|↑[^\s,()]*\s*%\s*↑",                              # ↑n % ↑p
        "A modulo between values coerced into a field. Erdős 726 was paid out because the frozen "
        "source read `(n % p : ℝ)`, which elaborates as REAL-FIELD modulo `(n : ℝ) % (p : ℝ)` and "
        "which `Field.mod_eq` reduces to `n - p * (n / p) = 0` for every prime p — so the filter "
        "`p/2 < 0` was impossible and the whole sum was identically zero. The submitted proof "
        "refuted that degenerate statement in 1 min 25 s and collected $750. Check every "
        "`: ℝ`/`: ℚ`/`: ℂ` ascription and every `↑`: does it cast the RESULT of an integer "
        "operation, or does it reinterpret the operation itself? "
        "`set_option pp.all true in #check <expr>` answers it.",
    ),
    (
        "missing_continuity",
        "Green42",
        3,
        r"(Measure|Integral|∫|MeasureTheory|Lattice|CohnElkies|Scheme|Packing)",
        "An analytic or variational statement whose type carries no `Continuous` / "
        "`ContDiff` / `ContinuousOn` hypothesis. Green 42 was paid out because "
        "`SatisfiesCohnElkiesScheme` dropped continuity and the winning witness was a Gaussian "
        "altered at one point. Check every ambient regularity condition the prose assumes.",
    ),
    (
        "wrong_named_object",
        "Erdos567.parts.i",
        3,
        r"(Ramsey|sizeRamsey|smoothNumber|totient|density|Density|Chromatic|chromaticNumber)",
        "The type names a specific library definition. Erdős 567 part i was paid out because "
        "the prose asks for the ordinary Ramsey number R(Q₃,H) and the Lean target states "
        "`SimpleGraph.sizeRamsey Q₃ H` — a different invariant. Erdős 1093 part ii was retired "
        "because `Nat.smoothNumbers k` means primes < k while the source defines k-smooth as "
        "primes ≤ k. Open the definition in Mathlib or the source namespace and check it means "
        "what the prose means.",
    ),
    (
        "restricted_witness_class",
        "Green77",
        3,
        r"Affine\.Triangle|AffinelyIndependent|ConvexHull|Metric\.diam|interior",
        "The type quantifies over a structurally restricted class. Green 77 was retired because "
        "`Affine.Triangle` means affinely INDEPENDENT points, which excluded exactly the "
        "collinear-heavy configurations that refute the claim. Ask whether the restriction is "
        "one the informal problem intends or one the formalization introduced.",
    ),
    (
        "dimension_mismatch",
        "Green54",
        2,
        r"ℝ\s*\(\s*Fin\s+\d|EuclideanSpace|infinitePi|Measure\.infinitePi",
        "A statement about a fixed finite dimension is not a statement about all dimensions, "
        "and a statement over `ℕ → ℝ` with a product measure is not a statement about ℝⁿ. "
        "Green 54 was retired as non-equivalent on exactly this. Check whether the prose "
        "quantifies the dimension the way the type does.",
    ),
    (
        "asymptotic_direction",
        "Green72,Erdos126",
        2,
        r"(IsBigO|IsLittleO|=O\(|≪|≫|Tendsto|Filter\.atTop|~|[→⇀])",
        "Asymptotic statements invert silently. Green 72 was withdrawn because the published "
        "target asserted a set size for EVERY N ≥ 3 while the informal question asks whether "
        "such sets become impossible for LARGE N — and both cited references expect the "
        "published direction to fail. Check the direction of the bound and the filter "
        "(`atTop` on which variable, and over which domain).",
    ),
    (
        "bounded_finite_scope",
        "Erdos939,Green77",
        1,
        r"Finset\.(range|Icc|Ico|filter)|Fintype|Fin\s+\d",
        "Bounded or finite scope can make a universal claim vacuous, or true only for the "
        "reason the bound exists. Weak signal on its own — it matters when combined with a "
        "query about a degenerate case.",
    ),
    (
        "negation_lives_in_counterexample_mode",
        "",
        1,
        r"¬",
        "The type is already negated. For counterexample mode the challenge is "
        "`¬ (fcTypeOfName% \"...\")`, so push the negation through by hand and confirm the "
        "negated form is the thing the informal problem actually asks you to refute. "
        "`¬∀` is `∃¬`; the quantifier order after negation is the usual trap.",
    ),
]

# Machine-ineligible targets: the pool's own admission policy excludes these, so
# a submission against one cannot be paid no matter how good it is.
HARD_BLOCKERS = [
    (r"sorryAx|answer\(", "type depends on sorryAx / answer wrapper"),
]


def score_target(row: dict) -> dict:
    lean = row.get("lean_type") or ""
    doc = row.get("docstring") or ""

    hits, total = [], 0
    for rid, precedents, weight, pattern, guidance in RULES:
        if re.search(pattern, lean):
            total += weight
            hits.append({"rule": rid, "precedents": precedents,
                         "weight": weight, "check": guidance})

    # A docstring that is much longer than the type is usually a statement with
    # prose conditions the formalization may or may not have carried over.
    if doc and lean and len(doc) > 2.2 * len(lean):
        total += 1
        hits.append({
            "rule": "prose_heavier_than_type",
            "precedents": "general",
            "weight": 1,
            "check": "The informal statement carries far more prose than the Lean type has "
                     "structure. That gap is where ambient conditions get dropped. Read the "
                     "docstring clause by clause and tick off which clauses are hypotheses in "
                     "the type.",
        })

    blockers = [msg for pat, msg in HARD_BLOCKERS
                if re.search(pat, lean) or re.search(pat, row.get("bounty_policy_version") or "")]

    return {
        "slug": row["slug"],
        "theorem": row["theorem"],
        "display_title": row.get("display_title"),
        "url": row.get("url"),
        "bounty_usd": row.get("bounty_usd"),
        "bounty_available": row.get("bounty_available"),
        "attempts": row.get("attempts"),
        "score": total,
        "hits": hits,
        "blockers": blockers,
        "lean_type": lean,
        "docstring": doc,
    }


def render(rows: list[dict], limit: int) -> str:
    out = []
    shown = [r for r in rows if not r["blockers"]][:limit]
    out.append(f"{len(rows)} candidates of the pool scored > 0; showing {len(shown)}.\n")
    for r in shown:
        out.append("=" * 78)
        out.append(f"[score {r['score']:>2}] {r['display_title']}  ({r['theorem']})")
        out.append(f"         bounty ${r['bounty_usd']}   attempts {r['attempts']}   "
                   f"available {r['bounty_available']}")
        out.append(f"         {r['url']}")
        out.append("")
        out.append("  Lean type:")
        for line in (r["lean_type"] or "").splitlines()[:14]:
            out.append(f"    {line}")
        if r["docstring"]:
            out.append("")
            out.append("  Informal problem (docstring):")
            for line in r["docstring"].splitlines()[:8]:
                out.append(f"    {line}")
        out.append("")
        out.append("  What to check:")
        for h in r["hits"]:
            tag = f" [{h['precedents']}]" if h["precedents"] else ""
            out.append(f"    - {h['rule']}{tag}")
            out.append(f"      {h['check']}")
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--targets", default="data/targets.json")
    ap.add_argument("--limit", type=int, default=25, help="how many to render")
    ap.add_argument("--min-score", type=int, default=4,
                    help="only render candidates at or above this score")
    ap.add_argument("--only", nargs="*", help="restrict to these slugs")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of prose")
    ap.add_argument("--include-closed", action="store_true",
                    help="include targets whose bounty is no longer available")
    args = ap.parse_args()

    path = Path(args.targets)
    if not path.exists():
        print(f"error: {path} not found. Run ./scripts/sync_pool.sh first.", file=sys.stderr)
        return 2

    rows = json.loads(path.read_text(encoding="utf-8"))
    if args.only:
        want = {s.lower() for s in args.only}
        rows = [r for r in rows if r["slug"].lower() in want]
    elif not args.include_closed:
        rows = [r for r in rows if r.get("bounty_available")]

    scored = [score_target(r) for r in rows]
    scored = [r for r in scored if r["score"] >= args.min_score]
    scored.sort(key=lambda r: (-r["score"], r["slug"]))

    if args.json:
        print(json.dumps(scored, indent=2, ensure_ascii=False))
    else:
        print(render(scored, args.limit))
        print("=" * 78)
        print("Reminder: this is triage, not a verdict. The output above ranks what a human")
        print("should READ. Every paid defect award so far needed a semantic comparison of")
        print("the Lean statement against the informal problem — never a regex.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
