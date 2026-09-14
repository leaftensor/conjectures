/-
Scratch: a machine-checked partial result for Green's Open Problem 12.

The published target, as frozen in the pool, is

    ∀ {G} [AddCommGroup G] [Fintype G] [DecidableEq G] (A : Finset G),
      let N := Fintype.card G; let α := A.card / N
      (#{t : (Fin 5 → G) × (Fin 5 → G) | ∀ i, ∀ j ∈ {i,i+1,i+2}, t.1 i + t.2 j ∈ A} : ℝ)
        ≥ α ^ 15 * N ^ 10

Theorem proved here: the count is at least  N * |A|^5.

Consequence. Since  N * |A|^5 ≥ |A|^15 / N^5  ⟺  |A| ≤ N^(3/5), the target is
settled whenever |A| ≤ N^(3/5). That is a partial result and not a solution of
Green's problem: the high-density regime stays open.

The proof is the constant-tuple argument. For x = (a,a,a,a,a) a tuple y is valid
iff a + y_j ∈ A for every j, i.e. y_j ∈ A - a; so x contributes exactly |A|^5
valid y. Distinct a give distinct x, hence the count is at least N * |A|^5.

Run:  lake env lean _scratch/green12_partial.lean
-/
import FormalConjectures.GreensOpenProblems.«12»

/-!
# Green 12: the constant-tuple partial result

See the header comment above for the statement and the argument.
-/

open Finset

namespace Green12Scratch

variable {G : Type*} [AddCommGroup G] [Fintype G] [DecidableEq G]

/-- The published `valid_tuples` predicate, as a standalone definition. -/
def validTuples (A : Finset G) : Finset ((Fin 5 → G) × (Fin 5 → G)) :=
  Finset.univ.filter fun t =>
    ∀ i : Fin 5, ∀ j ∈ ({i, i + 1, i + 2} : Finset (Fin 5)), t.1 i + t.2 j ∈ A

/-- **The partial result.** `N * |A|^5 ≤ #{valid tuples}`. -/
theorem card_validTuples_ge (A : Finset G) :
    Fintype.card G * A.card ^ 5 ≤ (validTuples A).card := by
  -- The constant-tuple map  (a, y) ↦ ((a,a,a,a,a), y - a).
  let f : G × (Fin 5 → A) → {t : (Fin 5 → G) × (Fin 5 → G) // t ∈ validTuples A} :=
    fun p => ⟨(fun _ => p.1, fun j => (p.2 j : G) - p.1), by
      rw [validTuples, Finset.mem_filter]
      refine ⟨Finset.mem_univ _, ?_⟩
      intro i j _
      have h : (p.1 + ((p.2 j : G) - p.1)) = (p.2 j : G) := by abel
      rw [h]
      exact (p.2 j).2⟩
  have hinj : Function.Injective f := by
    intro p q h
    have h1 : p.1 = q.1 := by
      have := congrArg (fun x => x.1.1 0) h
      simpa [f] using this
    have h2 : p.2 = q.2 := by
      funext j
      apply Subtype.ext
      have hcoord := congrFun (congrArg (fun x => x.1.2) h) j
      simp only [f] at hcoord
      rw [h1] at hcoord
      have := congrArg (fun z : G => z + q.1) hcoord
      simpa [sub_add_cancel] using this
    exact Prod.ext h1 h2
  calc Fintype.card G * A.card ^ 5
      = Fintype.card (G × (Fin 5 → A)) := by
        simp [Fintype.card_prod, Fintype.card_fin]
    _ ≤ Fintype.card {t : (Fin 5 → G) × (Fin 5 → G) // t ∈ validTuples A} :=
        Fintype.card_le_of_injective f hinj
    _ = (validTuples A).card := by simp

/--
The consequence, stated exactly as the pooled target's inequality: whenever
`|A|^5 ≤ N^3` — i.e. `|A| ≤ N^(3/5)` — the published bound holds.

This is the real-valued form the target asks for, so together with
`card_validTuples_ge` it is a machine-checked proof of Green's Open Problem 12
in the regime `|A| ≤ N^(3/5)`. The regime itself is not the whole problem.
-/
theorem bound_of_small_card (A : Finset G)
    (h : (A.card : ℝ) ^ 5 ≤ (Fintype.card G : ℝ) ^ 3) :
    ((validTuples A).card : ℝ)
      ≥ ((A.card : ℝ) / (Fintype.card G : ℝ)) ^ 15 * (Fintype.card G : ℝ) ^ 10 := by
  have hN : (0 : ℝ) < (Fintype.card G : ℝ) := by exact_mod_cast Fintype.card_pos
  have hk : (0 : ℝ) ≤ (A.card : ℝ) := by positivity
  have hcount : (Fintype.card G : ℝ) * (A.card : ℝ) ^ 5 ≤ ((validTuples A).card : ℝ) := by
    exact_mod_cast card_validTuples_ge A
  have hkey : ((A.card : ℝ) / (Fintype.card G : ℝ)) ^ 15 * (Fintype.card G : ℝ) ^ 10
      = (A.card : ℝ) ^ 15 / (Fintype.card G : ℝ) ^ 5 := by
    field_simp
  rw [hkey]
  -- k^5 ≤ N^3  ⟹  k^15 / N^5 ≤ N * k^5
  have hpow : (A.card : ℝ) ^ 15 / (Fintype.card G : ℝ) ^ 5
      ≤ (Fintype.card G : ℝ) * (A.card : ℝ) ^ 5 := by
    rw [div_le_iff₀ (by positivity : (0:ℝ) < (Fintype.card G : ℝ) ^ 5)]
    -- square the hypothesis to get k^10 ≤ N^6
    have h10 : (A.card : ℝ) ^ 10 ≤ (Fintype.card G : ℝ) ^ 6 := by
      have hk5 : (0 : ℝ) ≤ (A.card : ℝ) ^ 5 := by positivity
      have hN3 : (0 : ℝ) ≤ (Fintype.card G : ℝ) ^ 3 := by positivity
      have hmul : (A.card : ℝ) ^ 5 * (A.card : ℝ) ^ 5
          ≤ (Fintype.card G : ℝ) ^ 3 * (Fintype.card G : ℝ) ^ 3 :=
        mul_le_mul h h hk5 hN3
      nlinarith [hmul]
    have hprod := mul_le_mul_of_nonneg_right h10 (by positivity : (0:ℝ) ≤ (A.card : ℝ) ^ 5)
    nlinarith [hprod]
  linarith

end Green12Scratch

/- ## Axiom audit

The pool's machine contract permits exactly `propext`, `Quot.sound` and
`Classical.choice`, and refuses `sorryAx`. These must print only permitted axioms.
-/

#print axioms Green12Scratch.card_validTuples_ge
#print axioms Green12Scratch.bound_of_small_card
