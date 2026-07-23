(* ────────────────────────────────────────────────────────────────────
   Statement 5 — √2 is irrational, in Rocq (CIC), by infinite descent.
   Companion to ../lean/Artifacts/Sqrt2.lean. Rocq's `nia` (nonlinear
   integer arithmetic) discharges the algebra, so this is tighter than the
   hand-rolled Lean-core version.

   Check:  rocq compile Sqrt2.v   (or coqc Sqrt2.v)
   ──────────────────────────────────────────────────────────────────── *)

Require Import Arith Lia Wf_nat.   (* portable across Coq 8.x / Rocq 9.x *)

Module Sqrt2Descent.

(* A square is even iff its root is — the engine of the descent. *)
Lemma even_sq (n : nat) : Nat.Even (n * n) -> Nat.Even n.
Proof.
  intro H.
  destruct (Nat.Even_or_Odd n) as [He | Ho]; [exact He |].
  exfalso. destruct Ho as [k Hk]. destruct H as [m Hm]. subst n. nia.
Qed.

(* No positive solution to p² = 2·q²: any solution has q = 0. *)
Theorem no_sqrt2 : forall p q, p * p = 2 * (q * q) -> q = 0.
Proof.
  intro p.
  induction p as [p IH] using (well_founded_ind lt_wf).
  intros q H.
  assert (Hpe : Nat.Even (p * p)) by (exists (q * q); lia).
  apply even_sq in Hpe. destruct Hpe as [r Hr]. subst p.
  assert (Hq2 : q * q = 2 * (r * r)) by nia.
  assert (Hqe : Nat.Even (q * q)) by (exists (r * r); lia).
  apply even_sq in Hqe. destruct Hqe as [s Hs]. subst q.
  assert (Hr2 : r * r = 2 * (s * s)) by nia.
  destruct (Nat.eq_dec r 0) as [Hr0 | Hr0].
  - subst r. nia.
  - assert (Hlt : r < 2 * r) by lia.
    assert (Hs0 : s = 0) by exact (IH r Hlt s Hr2).
    subst s. lia.
Qed.

Theorem no_pos_sqrt2 : forall p q, q <> 0 -> p * p <> 2 * (q * q).
Proof. intros p q Hq H. apply Hq. exact (no_sqrt2 p q H). Qed.

End Sqrt2Descent.
