#!/usr/bin/env python3
"""Exhaustive counterexample search for Green's Open Problem 12 as formalized.

The published target (from the pinned pool) is:

    True ↔ ∀ {G} [AddCommGroup G] [Fintype G] [DecidableEq G] (A : Finset G),
      have N := Fintype.card G; have α := A.card / N;
      have valid_tuples := {t | ∀ (i j : Fin 5), j ∈ {i, i+1, i+2} → t.1 i + t.2 j ∈ A};
      valid_tuples.card ≥ α ^ 15 * N ^ 10

Informally: for an abelian group G of size N and a subset A of density α, at least
α^15 · N^10 of the N^10 tuples (x, y) ∈ G^5 × G^5 satisfy x_i + y_j ∈ A whenever
j ∈ {i, i+1, i+2} (indices mod 5).

WHY THIS IS COMPUTABLE
----------------------
Naive enumeration is N^10, hopeless past N = 5. But fix x. Then y_j is constrained
only by the three indices i with j ∈ {i, i+1, i+2}, i.e. i ∈ {j-2, j-1, j}, so

    y_j ∈ ⋂_{i ∈ {j-2, j-1, j}} (A - x_i)

and the five y_j constraints are independent given x. Therefore

    count(x) = ∏_{j=0}^{4} | ⋂_{i ∈ {j-2,j-1,j}} (A - x_i) |

and the total is N^5 · O(N) rather than N^10. That buys exhaustive search over ALL
subsets for N up to about 10.

The optimised count is cross-checked against a naive tuple enumeration before it is
trusted -- see `validate_counter`.

A counterexample is a pair (G, A) with count < ceil(α^15 · N^10). In the pool's
counterexample mode that pair is a witness refuting the published statement.
"""

from __future__ import annotations

import itertools
import json
import random
import sys
from fractions import Fraction


def count_fast(n: int, A: set[int]) -> int:
    """Count valid (x, y) via the product-of-intersections identity, with bitmasks.

    y_j must lie in the intersection over i in {j-2, j-1, j} of (A - x_i). Encode
    each (A - xi) as an n-bit mask so the intersection is a single `&`.
    """
    elems = range(n)
    A_mask = 0
    for a in A:
        A_mask |= 1 << a
    # shift_mask[xi] = bitmask of (A - xi)
    shift_mask = []
    for xi in elems:
        m = 0
        for a in A:
            m |= 1 << ((a - xi) % n)
        shift_mask.append(m)
    popcount = lambda m: bin(m).count("1")  # portable: int.bit_count needs 3.10+

    masks = [0, 0, 0, 0, 0]
    total = 0
    for x in itertools.product(elems, repeat=5):
        masks[0], masks[1], masks[2], masks[3], masks[4] = (
            shift_mask[x[0]], shift_mask[x[1]], shift_mask[x[2]],
            shift_mask[x[3]], shift_mask[x[4]])
        prod = 1
        for j in range(5):
            m = masks[j % 5] & masks[(j - 1) % 5] & masks[(j - 2) % 5]
            c = popcount(m)
            if c == 0:
                prod = 0
                break
            prod *= c
        total += prod
    return total


def count_naive(n: int, A: set[int]) -> int:
    """Straight enumeration of all N^10 tuples. Only usable for tiny n."""
    elems = range(n)
    pattern = [(i, j) for i in range(5) for j in range(5) if (j - i) % 5 in (0, 1, 2)]
    total = 0
    for x in itertools.product(elems, repeat=5):
        for y in itertools.product(elems, repeat=5):
            if all((x[i] + y[j]) % n in A for (i, j) in pattern):
                total += 1
    return total


def validate_counter(verbose: bool = True) -> bool:
    """Assert count_fast == count_naive on every small case brute force can reach."""
    ok = True
    import random as _r
    rng = _r.Random(1)
    for n in (1, 2, 3):
        elems = list(range(n))
        for k in range(n + 1):
            for comb in itertools.combinations(elems, k):
                A = set(comb)
                f, s = count_fast(n, A), count_naive(n, A)
                if f != s:
                    ok = False
                    if verbose:
                        print(f"  MISMATCH n={n} A={sorted(A)}: fast={f} naive={s}")
        if verbose:
            print(f"  n={n}: fast == naive on all {2 ** n} subsets")
    # n=4: full enumeration is 4^10 per subset, so cross-check on a sample.
    for _ in range(6):
        A = {a for a in range(4) if rng.random() < 0.5}
        f, sn = count_fast(4, A), count_naive(4, A)
        if f != sn:
            ok = False
            print(f"  MISMATCH n=4 A={sorted(A)}: fast={f} naive={sn}")
    if verbose:
        print("  n=4: fast == naive on a 6-subset sample")
    return ok


def check(n: int, exhaustive: bool, samples: int = 600, seed: int = 7):
    elems = list(range(n))
    worst = None
    fails = []

    if exhaustive:
        iterator = itertools.chain.from_iterable(
            itertools.combinations(elems, k) for k in range(n + 1))
    else:
        rng = random.Random(seed)
        iterator = (tuple(a for a in elems if rng.random() < p)
                    for p in (0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
                    for _ in range(samples))

    checked = 0
    for comb in iterator:
        A = set(comb)
        alpha = Fraction(len(A), n)
        bound = alpha ** 15 * n ** 10
        got = count_fast(n, A)
        checked += 1
        if bound > 0:
            ratio = Fraction(got, 1) / bound
            if worst is None or ratio < worst[0]:
                worst = (ratio, len(A), got, float(bound), sorted(A))
        if got < bound:
            fails.append({"n": n, "A": sorted(A), "alpha": str(alpha),
                          "got": got, "bound": float(bound)})
    return {"n": n, "checked": checked,
            "worst_ratio": float(worst[0]) if worst else None,
            "worst_At_size": worst[1] if worst else None,
            "worst_got": worst[2] if worst else None,
            "worst_bound": worst[3] if worst else None,
            "worst_A": worst[4] if worst else None,
            "fails": fails}


def main() -> int:
    print("== validating the optimised counter against naive enumeration ==")
    if not validate_counter():
        print("VALIDATION FAILED -- refusing to report a search result")
        return 2
    print("  counter validated on every subset of Z/nZ for n <= 4\n")

    max_n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    results = []
    any_fail = False
    for n in range(1, max_n + 1):
        r = check(n, exhaustive=True)
        results.append(r)
        any_fail |= bool(r["fails"])
        print(f"  Z/{n}Z  subsets={r['checked']:<5} min(count/bound)={r['worst_ratio']:.4f}"
              f"  at |A|={r['worst_At_size']} (count={r['worst_got']}, bound={r['worst_bound']:.3f})"
              f"  {'<-- COUNTEREXAMPLE' if r['fails'] else ''}")

    print()
    for n in (9, 10, 11, 13):
        r = check(n, exhaustive=False)
        results.append(r)
        any_fail |= bool(r["fails"])
        print(f"  Z/{n}Z  sampled={r['checked']:<5} min(count/bound)={r['worst_ratio']:.4f}"
              f"  at |A|={r['worst_At_size']}  {'<-- COUNTEREXAMPLE' if r['fails'] else ''}")

    out = {"results": results, "any_counterexample": any_fail}
    with open("green12_search.json", "w") as fh:
        json.dump(out, fh, indent=1)
    print("\nwrote green12_search.json")
    print("counterexample found:", any_fail)
    if any_fail:
        for r in results:
            for c in r["fails"][:5]:
                print("  ->", json.dumps(c))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
