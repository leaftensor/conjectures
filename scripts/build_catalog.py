#!/usr/bin/env python3
"""Build the master target catalog for conjectures.io (Bittensor Subnet 66).

Joins three sources into one table:

  1. THE LIVE CATALOG API -- `GET https://conjectures.io/v1/catalog/conjectures`.
     Unauthenticated, and the authority on what is currently offered. Each row
     carries the exact Lean target (`statement`), the informal problem (`summary`),
     AMS subjects, both task ids with their bundle digests and attempt counts, and
     a live `bounty` quote in alpha rao. This is the source to trust for anything
     that decides whether to spend money.

  2. THE PINNED TASK POOL -- `conjectures-io/conjectures-tasks`. Adds what the API
     does not publish: which targets have left the pool and *why*
     (`RETIREMENTS.md`), and the frozen `source-metadata.json` per bundle.

  3. THE WEBSITE CARD DUMP -- `data/cards.json`, optional. Used only as a
     cross-check that the rendered page agrees with the API.

Usage
-----
    scripts/sync_pool.sh                      # clone the task pool
    python3 scripts/build_catalog.py          # -> data/{targets,retirements,summary}

Outputs
-------
    data/targets.json      full records, one per reward target
    data/targets.csv       flat table for spreadsheets and grep
    data/retirements.json  every retirement with its published reason
    data/summary.json      counts, bounty distribution, treasury overhang
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

# --------------------------------------------------------------------------
# The defect taxonomy, learned from the published retirement log and from the
# validator's own reward-review decisions.
#
# Every pattern below has ALREADY cost the subnet a target -- a miner was paid a
# formalization-defect award for it, or it forced a retirement. These heuristics
# are a triage filter for what a human should read closely, never a verdict.
# `docs/03-attack-vectors.md` explains how each one is used.
# --------------------------------------------------------------------------

DEFECT_SIGNS: list[tuple[str, str, str]] = [
    ("rational_domain", r"ℚ|\bRat\b|Rational",
     "Type quantifies over ℚ where the informal problem means ℝ. Erdős 15 was retired on this: "
     "failure of ℚ-summability is not real divergence, and the miner who said so was paid."),
    ("summable", r"Summable",
     "Summability is domain-sensitive. Check the Lean domain against the informal one before "
     "assuming the statement means what the docstring says."),
    ("affine_independent", r"Affine\.Triangle|AffinelyIndependent",
     "`Affine.Triangle` means affinely *independent* points only. Green 77 was retired because "
     "collinear-heavy configurations were excluded, which refuted the formalized claim."),
    ("nat_domain", r"ℕ|\bNat\b",
     "ℕ-domain statements can be vacuous or trivially satisfiable at 0 and 1. Erdős 939 fell "
     "this way: `Nat.Full` is vacuous there, so the r = 4 case was discharged by {0, 1}."),
    ("smoothness_convention", r"[Ss]mooth",
     "Smoothness conventions differ (primes < k vs primes ≤ k). Erdős 1093 part ii was retired "
     "as SOURCE_MISMATCH for exactly this."),
    ("measure_or_integral", r"Measure|∫|Integral|MeasureTheory",
     "Null-set tricks recur. Green 42 was retired because `SatisfiesCohnElkiesScheme` omitted "
     "continuity, so f could be altered at a single point. A *missing* continuity hypothesis "
     "in the type is the candidate, not the presence of measure theory."),
    ("asymptotic", r"Tendsto|IsBigO|IsLittleO|≪|=O\(|Filter\.atTop|~",
     "Asymptotic statements are frequent; verify the direction of the bound and that the filter "
     "is `atTop` on the intended domain."),
    ("bounded_finite_range", r"Finset\.range|Finset\.Icc|Finset\.Ico|Finset\.filter",
     "Bounded finite ranges can make a statement true for reasons the informal problem does not "
     "intend, or vacuous below a threshold."),
    ("graph", r"SimpleGraph|chromaticNumber|Clique|Coloring",
     "Graph targets are the most quotable into refutation form. Check whether the graph is "
     "required to be finite and simple, and whether loops matter."),
    ("existential", r"∃",
     "Existential targets accept a single explicit witness — the shape of every recent "
     "AI counterexample result."),
]

# Ranking within the pool's own admission bias. POOL.md requires each admitted
# target to carry "at least one recorded feasibility signal: a compact target,
# discrete domain, finite or finitary structure, partial results in the same
# source, or a standard Mathlib surface." This ranks within that set.
TRACTABILITY_SIGNS: list[tuple[str, str, float, str]] = [
    ("finite_or_decidable", r"Finset|Fin \d|Decidable|Fintype", 2.0,
     "Finite or decidable domain: a counterexample may be reachable by brute force."),
    ("explicit_witness", r"∃", 1.5,
     "Existential: one explicit witness settles it."),
    ("graph", r"SimpleGraph", 1.0,
     "Graph-theoretic existentials are often computationally searchable."),
    ("arith_quantified", r"∀.*ℕ.*(∃|¬)", 0.5,
     "Quantified arithmetic claims sometimes yield to bounded search plus a covering argument."),
]

# Tokens that appear in one naming scheme but not the other.
_SLUG_STOP = {"problem", "open", "the", "a", "an", "of", "s",
              "variant", "variants", "part", "parts"}


def canonical_key(text: str) -> str:
    """Reduce either naming scheme to one key.

    Both of these describe the same target and must produce 'erdos944':
        theorem:  Erdos944.erdos_944
        title:    Erdős problem 944
    And these must both produce 'erdos10-grechuk':
        theorem:  Erdos10.erdos_10.variants.grechuk
        title:    Erdős problem 10 - grechuk
    """
    # The website splits camelCase into words ("EHSNumbers" -> "ehs numbers")
    # while theorem names keep it glued. Split before lowercasing.
    t = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    t = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", t)
    t = t.lower().replace("erdős", "erdos").replace("ő", "o")
    t = t.replace("green's", "green").replace("green’s", "green")
    m = re.search(r"(erdos|green)\D*(\d+)", t)
    if not m:
        return re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    family, number = m.group(1), m.group(2)
    rest = [tok for tok in re.split(r"[^a-z0-9]+", t[m.end():])
            if tok and tok not in _SLUG_STOP]
    while rest and (rest[0] == number or re.fullmatch(rf"{family}\d*", rest[0])):
        rest.pop(0)
    return "-".join([f"{family}{number}"] + rest)


def scan_type(lean_type: str) -> list[dict]:
    return [{"sign": name, "why": why}
            for name, pattern, why in DEFECT_SIGNS
            if pattern and re.search(pattern, lean_type)]


def tractability(lean_type: str) -> tuple[float, list[str]]:
    score, reasons = 0.0, []
    for _name, pattern, weight, why in TRACTABILITY_SIGNS:
        if pattern and re.search(pattern, lean_type):
            score += weight
            if why:
                reasons.append(why)
    if len(lean_type) < 120:
        score += 1.0
        reasons.append("Short target type: the pool's own admission policy counts a compact "
                       "target as a feasibility signal.")
    return score, reasons


def load_json(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_retirements(tiers: Path) -> tuple[set[str], dict[str, str]]:
    """Returns (retired theorem names, theorem -> published reason)."""
    retired: set[str] = set()
    rp = tiers / "retired-source-theorems.json"
    if rp.exists():
        retired = set(load_json(rp).get("source_theorems", []))

    reasons: dict[str, str] = {}
    md = tiers / "RETIREMENTS.md"
    if md.exists():
        for line in md.read_text(encoding="utf-8").splitlines():
            m = re.match(r"-\s+`([^`]+)`\s+—\s+(\S+)\s+—\s+`([^`]+)`", line.strip())
            if m:
                reasons[m.group(1)] = m.group(3)
    return retired, reasons


def build(live_path: Path, tasks_root: Path | None, out_dir: Path) -> dict:
    live = load_json(live_path)

    retired: set[str] = set()
    reasons: dict[str, str] = {}
    if tasks_root and (tasks_root / "allowlist.json").exists():
        retired, reasons = load_retirements(tasks_root / "tiers" / "tier-1")

    records = []
    for row in live:
        theorem = row["title"]
        stmt = row.get("statement") or ""
        tscore, treason = tractability(stmt)
        bounty = row.get("bounty") or {}
        tasks = {t["task_mode"]: t for t in row.get("tasks", [])}

        records.append({
            "slug": row["slug"],
            "theorem": theorem,
            "display_title": row.get("display_title"),
            "reward_target_id": row.get("reward_target_id"),
            "source_family": ("greens-open-problems"
                              if theorem.startswith("Green") else "erdos"),
            "ams_subjects": row.get("ams_subjects", []),
            "category": row.get("category"),
            "classification": row.get("classification"),
            "is_open_per_api": row.get("is_open"),
            "docstring": (row.get("summary") or "").strip(),
            "lean_type": stmt,
            "supported_modes": row.get("task_modes", []),
            "bounty_rao": bounty.get("amount_rao"),
            "bounty_alpha": round(bounty["amount_rao"] / 1e9, 6) if bounty.get("amount_rao") else None,
            "bounty_usd": float(bounty["amount_usd"]) if bounty.get("amount_usd") else None,
            "bounty_available": bounty.get("available"),
            "bounty_reason": bounty.get("reason"),
            "bounty_policy_version": bounty.get("policy_version"),
            "bounty_as_of": bounty.get("as_of"),
            "attempts": row.get("attempts"),
            "formalized_task_id": (tasks.get("formalized") or {}).get("task_id"),
            "counterexample_task_id": (tasks.get("counterexample") or {}).get("task_id"),
            "formalized_bundle_sha256": (tasks.get("formalized") or {}).get("task_bundle_sha256"),
            "counterexample_bundle_sha256": (tasks.get("counterexample") or {}).get("task_bundle_sha256"),
            "url": f"https://conjectures.io/problems/{row['slug']}",
            "retired_from_pool": theorem in retired,
            "retirement_reason": reasons.get(theorem),
            "tractability": round(tscore, 2),
            "tractability_reasons": treason,
            "defect_signs": scan_type(stmt),
        })

    retirements = [{"theorem": t,
                    "slug": canonical_key(t),
                    "reason": reasons.get(t, ""),
                    "reason_code": reasons.get(t, "").split("(")[0].strip().rstrip("+ ").strip(),
                    "has_published_reason": t in reasons}
                   for t in sorted(retired)]

    # ---- summary -------------------------------------------------------------
    bounties = [r["bounty_rao"] for r in records if r["bounty_rao"]]
    tiers_alpha = Counter(round(b / 1e9, 2) for b in bounties)
    meta_realised_usd = sum(r["bounty_usd"] or 0 for r in records)

    summary = {
        "generated_for_audit_date": max((r["bounty_as_of"] or "" for r in records), default=""),
        "targets_total": len(records),
        "targets_with_live_bounty": len(bounties),
        "targets_bounty_unavailable": len(records) - len(bounties),
        "bounty_unavailable_reasons": dict(Counter(r["bounty_reason"] for r in records
                                                    if not r["bounty_available"])),
        "bounty_policy_version": records[0]["bounty_policy_version"] if records else None,
        "bounty_tiers_alpha": {str(k): v for k, v in sorted(tiers_alpha.items(), reverse=True)},
        "sum_of_advertised_bounties_alpha": round(sum(bounties) / 1e9, 2),
        "sum_of_advertised_bounties_usd": round(meta_realised_usd, 2),
        "both_modes_available": sum(1 for r in records if len(r["supported_modes"]) == 2),
        "by_family": dict(Counter(r["source_family"] for r in records)),
        "ams_subjects": dict(sorted(Counter(a for r in records
                                            for a in r["ams_subjects"]).items())),
        "targets_with_zero_attempts": sum(1 for r in records if (r["attempts"] or 0) == 0),
        "targets_with_defect_signs": sum(1 for r in records if r["defect_signs"]),
        "median_tractability": statistics.median([r["tractability"] for r in records]),
        "retired_from_pool_total": len(retirements),
        "retired_with_published_reason": sum(1 for x in retirements if x["has_published_reason"]),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "targets.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out_dir / "retirements.json").write_text(
        json.dumps(retirements, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    with (out_dir / "targets.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["slug", "theorem", "display_title", "family", "bounty_usd", "bounty_alpha",
                    "bounty_available", "attempts", "tractability", "defect_signs", "ams",
                    "url", "lean_type", "formalized_task_id", "counterexample_task_id"])
        for r in sorted(records, key=lambda x: (-(x["bounty_usd"] or 0), -(x["tractability"] or 0), x["slug"])):
            w.writerow([r["slug"], r["theorem"], r["display_title"], r["source_family"],
                        r["bounty_usd"], r["bounty_alpha"], r["bounty_available"],
                        r["attempts"], r["tractability"],
                        "|".join(f["sign"] for f in r["defect_signs"]),
                        "|".join(str(a) for a in r["ams_subjects"]),
                        r["url"], r["lean_type"],
                        r["formalized_task_id"], r["counterexample_task_id"]])

    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--live", default="data/catalog_live.json",
                    help="dump of GET /v1/catalog/conjectures (see scripts/sync_pool.sh)")
    ap.add_argument("--tasks", default="_research/conjectures-tasks",
                    help="optional path to a conjectures-tasks checkout, for retirement reasons")
    ap.add_argument("--out", default="data", help="output directory")
    args = ap.parse_args()

    live_path = Path(args.live)
    if not live_path.exists():
        print(f"error: {live_path} not found.\n"
              f"       run scripts/sync_pool.sh to fetch the live catalog and the task pool.",
              file=sys.stderr)
        return 2

    tasks_root = Path(args.tasks)
    if not (tasks_root / "allowlist.json").exists():
        print(f"note: {tasks_root} is not a conjectures-tasks checkout; "
              f"retirement reasons will be omitted.", file=sys.stderr)
        tasks_root = None

    print(json.dumps(build(live_path, tasks_root, Path(args.out)), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
