#!/usr/bin/env python3
"""Focused scan for Green 12 in the regime where the bound is tight.

`green12_search.py` sweeps every subset, which is exponential and slow. This
sweeps the regime that actually matters instead.

Theory (proved in `_scratch/green12_partial.lean`):
    count >= N * k^5,   bound = k^15 / N^5
so the bound is unconditionally met whenever  k <= N^(3/5).  A counterexample
therefore needs  k > N^(3/5)  -- high density.  And at k = N the two sides are
equal (count = N^10 = bound), so the interesting window is

    N^(3/5) < k < N,   comfortably inside it: k ~ 0.75N .. 0.95N

This script samples that window for N up to ~20, including structured sets
(subgroups, intervals, complements) because a counterexample, if one exists, is
more likely to be structured than random.
"""

from __future__ import annotations

import json
import random
import sys
from fractions import Fraction

from green12_search import count_fast


def structured_sets(n: int, k: int, rng: random.Random):
    """Yield A of size k from a mix of structured and random constructions."""
    elems = list(range(n))
    seen = set()

    def emit(A):
        key = tuple(sorted(A))
        if len(A) == k and key not in seen:
            seen.add(key)
            return key
        return None

    cands = []
    cands.append(list(range(k)))                       # interval [0,k)
    cands.append([(i + n - k // 2) % n for i in range(k)])  # centred interval
    for d in range(1, n):                              # arithmetic progressions
        if n % d == 0 and d <= k:
            cands.append([(i * d) % n for i in range(k)])
    cands.append([i for i in elems if i % 2 == 0][:k])
    cands.append(sorted(set(range(n)) - set(range(n - k))))  # top k
    for _ in range(60):
        cands.append(rng.sample(elems, k))

    out = []
    for c in cands:
        c = sorted(set(c))
        if len(c) != k:
            continue
        t = tuple(c)
        if t in seen:
            continue
        seen.add(t)
        out.append(c)
    return out


def scan(n: int, rng: random.Random, ks: list[int]) -> list[dict]:
    rows = []
    for k in ks:
        bound = Fraction(k ** 15, n ** 5)
        best = None
        for A in structured_sets(n, k, rng):
            got = count_fast(n, set(A))
            ratio = Fraction(got, 1) / bound if bound else None
            if ratio is not None and (best is None or ratio < best[0]):
                best = (ratio, A, got)
        if best:
            rows.append({"n": n, "k": k, "min_ratio": float(best[0]),
                         "count": best[2], "bound": float(bound), "A": best[1],
                         "fail": best[2] < bound})
    return rows


def main() -> int:
    max_n = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    rng = random.Random(20260914)
    allrows = []
    fails = []
    for n in range(2, max_n + 1):
        # window: strictly above N^(3/5), strictly below N
        lo = max(1, int(n ** 0.6) + 1)
        ks = sorted({k for k in range(lo, n)} )
        if not ks:
            continue
        rows = scan(n, rng, ks)
        allrows.extend(rows)
        worst = min(rows, key=lambda r: r["min_ratio"])
        mark = ""
        if any(r["fail"] for r in rows):
            mark = "   <<< COUNTEREXAMPLE"
            fails.extend(r for r in rows if r["fail"])
        print(f"Z/{n}Z  k in [{lo},{n-1}]  min(count/bound) = {worst['min_ratio']:.4f} "
              f"at k={worst['k']}  (count={worst['count']}, bound={worst['bound']:.1f}){mark}")

    out = {"rows": allrows, "fails": fails, "any_counterexample": bool(fails)}
    with open("green12_focus.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print()
    print("wrote green12_focus.json")
    print("counterexample found:", bool(fails))
    for f in fails[:5]:
        print("  ->", json.dumps(f))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
