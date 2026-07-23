(* ────────────────────────────────────────────────────────────────────
   Course artifacts — Rocq (formerly Coq)
   Foundation: the Calculus of Inductive Constructions (CIC) — the same
   family as Lean. VIASM mini-course "An Introduction to Automatic
   Theorem Proving". Same statements as ../lean/Artifacts.lean.

   Like Agda (and unlike Lean), Rocq's `+` on `nat` recurses on its FIRST
   argument, so `0 + n = n` is definitional and `n + 0` needs induction.

   Check:  rocq compile Artifacts.v   (or coqc; authored, verified in CI).
   ──────────────────────────────────────────────────────────────────── *)

(* ── Statement 1: the S combinator (propositions-as-types) ── *)

Definition S_comb {P Q R : Prop} (f : P -> Q -> R) (g : P -> Q) (x : P) : R :=
  f x (g x).

Definition S {A B C : Type} (f : A -> B -> C) (g : A -> B) (x : A) : C := f x (g x).
Definition K {A B : Type} (x : A) (_ : B) : A := x.
Definition I {A : Type} (x : A) : A := x.

Example K_computes {A B : Type} (x : A) (y : B) : K x y = x := eq_refl.
Example I_computes {A : Type} (x : A) : I x = x := eq_refl.

(* ── Statement 2/3: Peano addition on nat ── *)

Theorem zero_add (n : nat) : 0 + n = n.
Proof. reflexivity. Qed.

Theorem add_zero (n : nat) : n + 0 = n.
Proof.
  induction n as [| n IH]; simpl.
  - reflexivity.
  - rewrite IH. reflexivity.
Qed.

Theorem add_succ (m n : nat) : m + S n = S (m + n).
Proof.
  induction m as [| m IH]; simpl.
  - reflexivity.
  - rewrite IH. reflexivity.
Qed.

Theorem add_comm (n m : nat) : n + m = m + n.
Proof.
  induction n as [| n IH]; simpl.
  - rewrite add_zero. reflexivity.
  - rewrite add_succ. rewrite IH. reflexivity.
Qed.

(* Sanity checks *)
Example two_plus_three : 2 + 3 = 3 + 2 := add_comm 2 3.

(* ── Statement 4: a tiny expression evaluator (EML in miniature) ── *)

Inductive Tm : Type :=
  | lit  : nat -> Tm
  | add_ : Tm -> Tm -> Tm
  | mul_ : Tm -> Tm -> Tm.

Fixpoint eval (t : Tm) : nat :=
  match t with
  | lit n    => n
  | add_ a b => eval a + eval b
  | mul_ a b => eval a * eval b
  end.

Example eval_one_plus_one : eval (add_ (lit 1) (lit 1)) = 2 := eq_refl.

Theorem eval_add (a b : Tm) : eval (add_ a b) = eval a + eval b.
Proof. reflexivity. Qed.

Theorem eval_add_comm (a b : Tm) : eval (add_ a b) = eval (add_ b a).
Proof. simpl. apply add_comm. Qed.
