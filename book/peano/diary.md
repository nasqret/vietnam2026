# Implementation diary

Short, dated notes on design decisions taken during implementation — the raw material for this
book part. Keep it as you go, not retroactively.

## 2026-07-26 — project start

Branch created; design document and milestone plan written. Decisions D1–D4 (staged logic,
proof terms + independent checker over LCF, trace format designed up front, intuitionistic core
with a classical toggle) recorded in `docs/PEANO_LAB_DESIGN.md` §0.

## 2026-07-27 — M0 representation choices

- The pinned parser API returns only a de Bruijn tree, not the surface free-name table.  Free
  names therefore receive indices in deterministic first-occurrence order; companion parsing
  helpers retain that table for the future UI.  Bound variables still use ordinary de Bruijn
  depth.  The canonical printer uses Unicode logical symbols and fresh deterministic binder names.
- `subst_term` and `subst_formula` mean *binder-opening* substitution: the selected slot is
  replaced, larger indices close the gap, and replacements shift under binders.  An internal/public
  `shift_formula` companion is necessary to express the quantifier and induction rules without
  capture.  Tests include the classic free-variable-under-`forall` counterexample.
- The certificate checker is bidirectional: introduction forms are checked against a target and
  elimination/equality forms synthesize their result.  This preserves the pinned unannotated proof
  constructors and keeps the trusted code small; certificates are kept in checkable normal form.
- Two architecture tensions are recorded rather than silently hidden.  `EqSubst` remains a kernel
  primitive because the API stub explicitly requires it, although design §1 also calls Leibniz
  substitution “derived”.  The required IND certificate for `forall x. x + 0 = x` deliberately
  exercises the schema but is logically redundant because PA3 is exactly that formula.
- **Objection for M3 review:** the binding design requires a classical DNE toggle, but the pinned
  kernel certificate language names only PA1–PA6 and has no DNE constructor.  The tactic layer
  cannot soundly add DNE by itself.  M3 will need an explicit, labeled kernel certificate form (and
  a checker mode or premise) before `classical on` can close any new theorem.
- An adversarial review found that Python subclasses could override an AST node's equality and fool
  an `isinstance`-based trusted recursion.  The checker now admits only the *exact* frozen kernel
  constructor classes at every boundary.  The concrete forged-`Zero`, forged-formula, and
  forged-proof attacks are permanent regression tests; this is a useful Python-specific extension
  of the De Bruijn criterion.
