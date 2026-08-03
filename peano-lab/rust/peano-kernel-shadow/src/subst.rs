//! Capture-avoiding shifting and opening substitution for de Bruijn syntax.

use crate::syntax::{Formula, Term};

/// Shift variables at or above `cutoff` by `by`.
///
/// A negative shift or arithmetic overflow returns `None`, so malformed input
/// fails closed at the checker boundary.
#[must_use]
pub fn shift_term(term: &Term, by: isize, cutoff: usize) -> Option<Term> {
    match term {
        Term::Var(index) if *index >= cutoff => index.checked_add_signed(by).map(Term::Var),
        Term::Var(index) => Some(Term::Var(*index)),
        Term::Zero => Some(Term::Zero),
        Term::Succ(inner) => Some(Term::succ(shift_term(inner, by, cutoff)?)),
        Term::Add(left, right) => Some(Term::plus(
            shift_term(left, by, cutoff)?,
            shift_term(right, by, cutoff)?,
        )),
        Term::Mul(left, right) => Some(Term::times(
            shift_term(left, by, cutoff)?,
            shift_term(right, by, cutoff)?,
        )),
    }
}

/// Shift free term variables in a formula, respecting quantifier binders.
#[must_use]
pub fn shift_formula(formula: &Formula, by: isize, cutoff: usize) -> Option<Formula> {
    match formula {
        Formula::Eq(left, right) => Some(Formula::eq(
            shift_term(left, by, cutoff)?,
            shift_term(right, by, cutoff)?,
        )),
        Formula::Bot => Some(Formula::Bot),
        Formula::Imp(left, right) => Some(Formula::imp(
            shift_formula(left, by, cutoff)?,
            shift_formula(right, by, cutoff)?,
        )),
        Formula::And(left, right) => Some(Formula::and(
            shift_formula(left, by, cutoff)?,
            shift_formula(right, by, cutoff)?,
        )),
        Formula::Or(left, right) => Some(Formula::or(
            shift_formula(left, by, cutoff)?,
            shift_formula(right, by, cutoff)?,
        )),
        Formula::Forall(body) => Some(Formula::forall(shift_formula(
            body,
            by,
            cutoff.checked_add(1)?,
        )?)),
        Formula::Exists(body) => Some(Formula::exists(shift_formula(
            body,
            by,
            cutoff.checked_add(1)?,
        )?)),
    }
}

fn subst_term_at(term: &Term, index: usize, replacement: &Term, depth: usize) -> Option<Term> {
    match term {
        Term::Var(found) => {
            let sought = index.checked_add(depth)?;
            if *found == sought {
                let lift = isize::try_from(depth).ok()?;
                shift_term(replacement, lift, 0)
            } else if *found > sought {
                found.checked_sub(1).map(Term::Var)
            } else {
                Some(Term::Var(*found))
            }
        }
        Term::Zero => Some(Term::Zero),
        Term::Succ(inner) => Some(Term::succ(subst_term_at(inner, index, replacement, depth)?)),
        Term::Add(left, right) => Some(Term::plus(
            subst_term_at(left, index, replacement, depth)?,
            subst_term_at(right, index, replacement, depth)?,
        )),
        Term::Mul(left, right) => Some(Term::times(
            subst_term_at(left, index, replacement, depth)?,
            subst_term_at(right, index, replacement, depth)?,
        )),
    }
}

/// Open variable slot `index` in a term with `replacement`.
#[must_use]
pub fn subst_term(term: &Term, index: usize, replacement: &Term) -> Option<Term> {
    subst_term_at(term, index, replacement, 0)
}

fn subst_formula_at(
    formula: &Formula,
    index: usize,
    replacement: &Term,
    depth: usize,
) -> Option<Formula> {
    match formula {
        Formula::Eq(left, right) => Some(Formula::eq(
            subst_term_at(left, index, replacement, depth)?,
            subst_term_at(right, index, replacement, depth)?,
        )),
        Formula::Bot => Some(Formula::Bot),
        Formula::Imp(left, right) => Some(Formula::imp(
            subst_formula_at(left, index, replacement, depth)?,
            subst_formula_at(right, index, replacement, depth)?,
        )),
        Formula::And(left, right) => Some(Formula::and(
            subst_formula_at(left, index, replacement, depth)?,
            subst_formula_at(right, index, replacement, depth)?,
        )),
        Formula::Or(left, right) => Some(Formula::or(
            subst_formula_at(left, index, replacement, depth)?,
            subst_formula_at(right, index, replacement, depth)?,
        )),
        Formula::Forall(body) => Some(Formula::forall(subst_formula_at(
            body,
            index,
            replacement,
            depth.checked_add(1)?,
        )?)),
        Formula::Exists(body) => Some(Formula::exists(subst_formula_at(
            body,
            index,
            replacement,
            depth.checked_add(1)?,
        )?)),
    }
}

/// Open free variable slot `index` in a formula with `replacement`.
#[must_use]
pub fn subst_formula(formula: &Formula, index: usize, replacement: &Term) -> Option<Formula> {
    subst_formula_at(formula, index, replacement, 0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shifts_respect_cutoffs_and_reject_underflow() {
        let term = Term::plus(Term::Var(0), Term::Var(2));
        assert_eq!(
            shift_term(&term, 2, 1),
            Some(Term::plus(Term::Var(0), Term::Var(4)))
        );
        assert_eq!(shift_term(&Term::Var(0), -1, 0), None);
        assert_eq!(shift_term(&Term::Var(usize::MAX), 1, 0), None);
    }

    #[test]
    fn substitution_avoids_capture_below_a_quantifier() {
        // Open free slot zero in forall y. x = y with free variable z.  The
        // replacement is lifted beneath forall, so z remains free (index 1).
        let formula = Formula::forall(Formula::eq(Term::Var(1), Term::Var(0)));
        assert_eq!(
            subst_formula(&formula, 0, &Term::Var(0)),
            Some(Formula::forall(Formula::eq(Term::Var(1), Term::Var(0))))
        );
    }

    #[test]
    fn opening_decrements_variables_above_the_removed_slot() {
        let term = Term::plus(Term::Var(0), Term::Var(2));
        assert_eq!(
            subst_term(&term, 0, &Term::Zero),
            Some(Term::plus(Term::Zero, Term::Var(1)))
        );
    }
}
