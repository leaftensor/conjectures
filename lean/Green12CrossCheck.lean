/-
Scratch file: recompute Green 12's `valid_tuples.card` the way Lean does, so the
Python search's optimised count can be cross-checked against the kernel's own
reduction. Not a submission -- it uses `#eval`, which submissions forbid.

Run with:  lake env lean _scratch/green12_check.lean
-/
import FormalConjectures.GreensOpenProblems.«12»

open Finset Green12

/-- The published `valid_tuples` predicate, factored out so we can evaluate it. -/
def vt {G : Type*} [AddCommGroup G] [Fintype G] [DecidableEq G] (A : Finset G) :
    Finset ((Fin 5 → G) × (Fin 5 → G)) :=
  Finset.univ.filter (fun t =>
    ∀ i : Fin 5, ∀ j ∈ ({i, i + 1, i + 2} : Finset (Fin 5)), t.1 i + t.2 j ∈ A)

/-- Cardinality for `ZMod n` with a chosen `A`, as an exact natural number. -/
def countZMod (n : ℕ) [NeZero n] (A : Finset (ZMod n)) : ℕ :=
  (vt A).card

-- ZMod 2, A = {0}
#eval countZMod 2 ({0} : Finset (ZMod 2))
-- ZMod 2, A = univ
#eval countZMod 2 (Finset.univ : Finset (ZMod 2))
-- ZMod 2, A = {} 
#eval countZMod 2 (∅ : Finset (ZMod 2))

-- ZMod 3, A = {0}
#eval countZMod 3 ({0} : Finset (ZMod 3))
-- ZMod 3, A = {0,1}
#eval countZMod 3 ({0, 1} : Finset (ZMod 3))
-- ZMod 3, A = univ
#eval countZMod 3 (Finset.univ : Finset (ZMod 3))

-- ZMod 4, a few sets
#eval countZMod 4 ({0} : Finset (ZMod 4))
#eval countZMod 4 ({0, 1} : Finset (ZMod 4))
#eval countZMod 4 ({0, 2} : Finset (ZMod 4))
#eval countZMod 4 ({0, 1, 2} : Finset (ZMod 4))

-- ZMod 5 (5^10 tuples: slow, uncomment if you have time)
-- #eval countZMod 5 ({0} : Finset (ZMod 5))
-- #eval countZMod 5 ({0, 1} : Finset (ZMod 5))
