//! Independent eager-context HA checker with an explicitly gated DNE extension.

use crate::subst::{shift_formula, subst_formula};
use crate::syntax::{AxiomName, Formula, Proof, Term};

#[derive(Clone, Copy)]
enum Logic {
    Heyting,
    Classical,
}

#[derive(Clone, Copy)]
enum Fuel {
    Unbounded,
    Bounded(usize),
}

impl Fuel {
    fn descend(self) -> Option<Self> {
        match self {
            Self::Unbounded => Some(Self::Unbounded),
            Self::Bounded(0) => None,
            Self::Bounded(remaining) => Some(Self::Bounded(remaining - 1)),
        }
    }
}

struct WorkBudget {
    remaining: Option<usize>,
}

impl WorkBudget {
    const fn unbounded() -> Self {
        Self { remaining: None }
    }

    const fn bounded(steps: usize) -> Self {
        Self {
            remaining: Some(steps),
        }
    }

    fn consume(&mut self) -> bool {
        match self.remaining {
            None => true,
            Some(0) => false,
            Some(remaining) => {
                self.remaining = Some(remaining - 1);
                true
            }
        }
    }
}

/// Return the closed formula denoted by a fixed PA axiom constant.
#[must_use]
pub fn axiom_formula(name: AxiomName) -> Formula {
    let zero = Term::Zero;
    let x = Term::Var(1);
    let y = Term::Var(0);
    match name {
        AxiomName::PA1 => Formula::forall(Formula::imp(
            Formula::eq(Term::succ(Term::Var(0)), zero),
            Formula::Bot,
        )),
        AxiomName::PA2 => Formula::forall(Formula::forall(Formula::imp(
            Formula::eq(Term::succ(x.clone()), Term::succ(y.clone())),
            Formula::eq(x, y),
        ))),
        AxiomName::PA3 => {
            Formula::forall(Formula::eq(Term::plus(Term::Var(0), zero), Term::Var(0)))
        }
        AxiomName::PA4 => Formula::forall(Formula::forall(Formula::eq(
            Term::plus(x.clone(), Term::succ(y.clone())),
            Term::succ(Term::plus(x, y)),
        ))),
        AxiomName::PA5 => {
            Formula::forall(Formula::eq(Term::times(Term::Var(0), zero.clone()), zero))
        }
        AxiomName::PA6 => Formula::forall(Formula::forall(Formula::eq(
            Term::times(x.clone(), Term::succ(y.clone())),
            Term::plus(Term::times(x.clone(), y), x),
        ))),
    }
}

fn extend(context: &[Formula], proposition: &Formula) -> Vec<Formula> {
    let mut extended = Vec::with_capacity(context.len() + 1);
    extended.push(proposition.clone());
    extended.extend_from_slice(context);
    extended
}

fn under_term_binder(context: &[Formula]) -> Option<Vec<Formula>> {
    context
        .iter()
        .map(|formula| shift_formula(formula, 1, 0))
        .collect()
}

fn successor_instance(motive: &Formula) -> Option<Formula> {
    let lifted = shift_formula(motive, 1, 1)?;
    subst_formula(&lifted, 0, &Term::succ(Term::Var(0)))
}

fn infer(
    context: &[Formula],
    proof: &Proof,
    logic: Logic,
    fuel: Fuel,
    work: &mut WorkBudget,
) -> Option<Formula> {
    if !work.consume() {
        return None;
    }
    let fuel = fuel.descend()?;
    match proof {
        Proof::Hyp(index) => context.get(*index).cloned(),
        Proof::Axiom(name) => Some(axiom_formula(*name)),
        Proof::EqRefl(term) => Some(Formula::eq(term.clone(), term.clone())),
        Proof::DNE(proposition) if matches!(logic, Logic::Classical) => {
            let negation = Formula::imp(proposition.clone(), Formula::Bot);
            Some(Formula::imp(
                Formula::imp(negation, Formula::Bot),
                proposition.clone(),
            ))
        }
        Proof::DNE(_) => None,
        Proof::Cut {
            proposition,
            conclusion,
            lemma,
            body,
        } => {
            let body_context = extend(context, proposition);
            (check_with_logic(context, lemma, proposition, logic, fuel, work)
                && check_with_logic(&body_context, body, conclusion, logic, fuel, work))
            .then(|| conclusion.clone())
        }
        Proof::ImpElim(function, argument) => {
            let Formula::Imp(domain, codomain) = infer(context, function, logic, fuel, work)?
            else {
                return None;
            };
            check_with_logic(context, argument, &domain, logic, fuel, work).then_some(*codomain)
        }
        Proof::AndElimL(pair) => {
            let Formula::And(left, _) = infer(context, pair, logic, fuel, work)? else {
                return None;
            };
            Some(*left)
        }
        Proof::AndElimR(pair) => {
            let Formula::And(_, right) = infer(context, pair, logic, fuel, work)? else {
                return None;
            };
            Some(*right)
        }
        Proof::ForallElim(universal, term) => {
            let Formula::Forall(body) = infer(context, universal, logic, fuel, work)? else {
                return None;
            };
            subst_formula(&body, 0, term)
        }
        Proof::EqSym(proof) => {
            let Formula::Eq(left, right) = infer(context, proof, logic, fuel, work)? else {
                return None;
            };
            Some(Formula::eq(right, left))
        }
        Proof::EqTrans(first, second) => {
            let Formula::Eq(first_left, first_right) = infer(context, first, logic, fuel, work)?
            else {
                return None;
            };
            let Formula::Eq(second_left, second_right) = infer(context, second, logic, fuel, work)?
            else {
                return None;
            };
            (first_right == second_left).then(|| Formula::eq(first_left, second_right))
        }
        Proof::CongS(proof) => {
            let Formula::Eq(left, right) = infer(context, proof, logic, fuel, work)? else {
                return None;
            };
            Some(Formula::eq(Term::succ(left), Term::succ(right)))
        }
        Proof::CongAdd(left, right) | Proof::CongMul(left, right) => {
            let Formula::Eq(left_source, left_target) = infer(context, left, logic, fuel, work)?
            else {
                return None;
            };
            let Formula::Eq(right_source, right_target) = infer(context, right, logic, fuel, work)?
            else {
                return None;
            };
            if matches!(proof, Proof::CongAdd(_, _)) {
                Some(Formula::eq(
                    Term::plus(left_source, right_source),
                    Term::plus(left_target, right_target),
                ))
            } else {
                Some(Formula::eq(
                    Term::times(left_source, right_source),
                    Term::times(left_target, right_target),
                ))
            }
        }
        Proof::EqSubst {
            motive,
            equation,
            body,
        } => {
            let Formula::Eq(source_term, target_term) =
                infer(context, equation, logic, fuel, work)?
            else {
                return None;
            };
            let source = subst_formula(motive, 0, &source_term)?;
            check_with_logic(context, body, &source, logic, fuel, work)
                .then(|| subst_formula(motive, 0, &target_term))?
        }
        Proof::Ind { motive, base, step } => {
            let base_target = subst_formula(motive, 0, &Term::Zero)?;
            let step_target =
                Formula::forall(Formula::imp(motive.clone(), successor_instance(motive)?));
            (check_with_logic(context, base, &base_target, logic, fuel, work)
                && check_with_logic(context, step, &step_target, logic, fuel, work))
            .then(|| Formula::forall(motive.clone()))
        }
        Proof::ImpIntro(_)
        | Proof::AndIntro(_, _)
        | Proof::OrIntroL(_)
        | Proof::OrIntroR(_)
        | Proof::OrElim { .. }
        | Proof::BotElim(_)
        | Proof::ForallIntro(_)
        | Proof::ExistsIntro(_, _)
        | Proof::ExistsElim(_, _) => None,
    }
}

fn check_with_logic(
    context: &[Formula],
    proof: &Proof,
    target: &Formula,
    logic: Logic,
    fuel: Fuel,
    work: &mut WorkBudget,
) -> bool {
    if !work.consume() {
        return false;
    }
    let Some(fuel) = fuel.descend() else {
        return false;
    };
    if let Some(inferred) = infer(context, proof, logic, fuel, work) {
        return inferred == *target;
    }

    match (proof, target) {
        (Proof::ImpElim(function, argument), _) => {
            let Some(argument_type) = infer(context, argument, logic, fuel, work) else {
                return false;
            };
            check_with_logic(
                context,
                function,
                &Formula::imp(argument_type.clone(), target.clone()),
                logic,
                fuel,
                work,
            ) && check_with_logic(context, argument, &argument_type, logic, fuel, work)
        }
        (Proof::ImpIntro(body), Formula::Imp(domain, codomain)) => {
            check_with_logic(&extend(context, domain), body, codomain, logic, fuel, work)
        }
        (Proof::AndIntro(left, right), Formula::And(left_target, right_target)) => {
            check_with_logic(context, left, left_target, logic, fuel, work)
                && check_with_logic(context, right, right_target, logic, fuel, work)
        }
        (Proof::OrIntroL(proof), Formula::Or(left, _)) => {
            check_with_logic(context, proof, left, logic, fuel, work)
        }
        (Proof::OrIntroR(proof), Formula::Or(_, right)) => {
            check_with_logic(context, proof, right, logic, fuel, work)
        }
        (
            Proof::OrElim {
                disjunction,
                left_case,
                right_case,
            },
            _,
        ) => {
            let Some(Formula::Or(left, right)) = infer(context, disjunction, logic, fuel, work)
            else {
                return false;
            };
            check_with_logic(
                &extend(context, &left),
                left_case,
                target,
                logic,
                fuel,
                work,
            ) && check_with_logic(
                &extend(context, &right),
                right_case,
                target,
                logic,
                fuel,
                work,
            )
        }
        (Proof::BotElim(absurdity), _) => {
            check_with_logic(context, absurdity, &Formula::Bot, logic, fuel, work)
        }
        (Proof::ForallIntro(body), Formula::Forall(target_body)) => {
            let Some(lifted_context) = under_term_binder(context) else {
                return false;
            };
            check_with_logic(&lifted_context, body, target_body, logic, fuel, work)
        }
        (Proof::ExistsIntro(term, proof), Formula::Exists(body)) => {
            let Some(instance) = subst_formula(body, 0, term) else {
                return false;
            };
            check_with_logic(context, proof, &instance, logic, fuel, work)
        }
        (Proof::ExistsElim(existential, body), _) => {
            let Some(Formula::Exists(source_body)) = infer(context, existential, logic, fuel, work)
            else {
                return false;
            };
            let Some(mut lifted_context) = under_term_binder(context) else {
                return false;
            };
            lifted_context.insert(0, *source_body);
            let Some(lifted_target) = shift_formula(target, 1, 0) else {
                return false;
            };
            check_with_logic(&lifted_context, body, &lifted_target, logic, fuel, work)
        }
        _ => false,
    }
}

fn run_check(
    context: &[Formula],
    proof: &Proof,
    original_target: &Formula,
    logic: Logic,
    fuel: Fuel,
    max_steps: Option<usize>,
) -> bool {
    let mut work = match max_steps {
        Some(steps) => WorkBudget::bounded(steps),
        None => WorkBudget::unbounded(),
    };
    check_with_logic(context, proof, original_target, logic, fuel, &mut work)
}

/// Check an HA certificate against the caller's explicit original target.
#[must_use]
pub fn check(context: &[Formula], proof: &Proof, original_target: &Formula) -> bool {
    run_check(
        context,
        proof,
        original_target,
        Logic::Heyting,
        Fuel::Unbounded,
        None,
    )
}

/// Check a certificate in the explicitly labeled PA+DNE extension.
#[must_use]
pub fn check_classical(context: &[Formula], proof: &Proof, original_target: &Formula) -> bool {
    run_check(
        context,
        proof,
        original_target,
        Logic::Classical,
        Fuel::Unbounded,
        None,
    )
}

/// Check HA with Lean-compatible path fuel and a global invocation work cap.
///
/// Each mutually recursive `check` or `infer` call consumes one unit of path
/// fuel, exactly as in the verified Lean checker.  Every such call also
/// consumes one global step, preventing adversarial re-checking from turning a
/// bounded wire artifact into unbounded work.
#[must_use]
pub fn check_with_fuel_and_step_limit(
    context: &[Formula],
    proof: &Proof,
    original_target: &Formula,
    fuel: usize,
    max_steps: usize,
) -> bool {
    run_check(
        context,
        proof,
        original_target,
        Logic::Heyting,
        Fuel::Bounded(fuel),
        Some(max_steps),
    )
}

/// Check PA+DNE with Lean-compatible path fuel and a global work cap.
#[must_use]
pub fn check_classical_with_fuel_and_step_limit(
    context: &[Formula],
    proof: &Proof,
    original_target: &Formula,
    fuel: usize,
    max_steps: usize,
) -> bool {
    run_check(
        context,
        proof,
        original_target,
        Logic::Classical,
        Fuel::Bounded(fuel),
        Some(max_steps),
    )
}

/// Check a closed HA theorem, rejecting an original target with free variables.
#[must_use]
pub fn check_closed(proof: &Proof, original_target: &Formula) -> bool {
    original_target.well_scoped(0) && check(&[], proof, original_target)
}

/// Check a closed PA+DNE theorem, rejecting a target with free variables.
#[must_use]
pub fn check_closed_classical(proof: &Proof, original_target: &Formula) -> bool {
    original_target.well_scoped(0) && check_classical(&[], proof, original_target)
}

/// Bounded closed HA gate used by decoded shadow artifacts.
#[must_use]
pub fn check_closed_with_fuel_and_step_limit(
    proof: &Proof,
    original_target: &Formula,
    fuel: usize,
    max_steps: usize,
) -> bool {
    original_target.well_scoped(0)
        && check_with_fuel_and_step_limit(&[], proof, original_target, fuel, max_steps)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn bx(proof: Proof) -> Box<Proof> {
        Box::new(proof)
    }

    fn zero_eq_zero() -> Formula {
        Formula::eq(Term::Zero, Term::Zero)
    }

    fn one() -> Term {
        Term::succ(Term::Zero)
    }

    fn two() -> Term {
        Term::succ(one())
    }

    #[test]
    fn hypotheses_implication_and_cut_rules_check() {
        let a = zero_eq_zero();
        let b = Formula::eq(one(), one());

        assert!(check(std::slice::from_ref(&a), &Proof::Hyp(0), &a));
        assert!(!check(std::slice::from_ref(&a), &Proof::Hyp(1), &a));

        let identity = Proof::ImpIntro(bx(Proof::Hyp(0)));
        assert!(check_closed(&identity, &Formula::imp(a.clone(), a.clone())));

        let application = Proof::ImpElim(bx(Proof::Hyp(0)), bx(Proof::Hyp(1)));
        assert!(check(
            &[Formula::imp(a.clone(), b.clone()), a.clone()],
            &application,
            &b
        ));

        // Exercises the checking fallback for an introduction in function position.
        let beta = Proof::ImpElim(
            bx(Proof::ImpIntro(bx(Proof::Hyp(0)))),
            bx(Proof::EqRefl(Term::Zero)),
        );
        assert!(check_closed(&beta, &a));

        let cut = Proof::Cut {
            proposition: a.clone(),
            conclusion: a.clone(),
            lemma: bx(Proof::EqRefl(Term::Zero)),
            body: bx(Proof::Hyp(0)),
        };
        assert!(check_closed(&cut, &a));

        let mutated_cut = Proof::Cut {
            proposition: b,
            conclusion: a.clone(),
            lemma: bx(Proof::EqRefl(Term::Zero)),
            body: bx(Proof::Hyp(0)),
        };
        assert!(!check_closed(&mutated_cut, &a));
        assert!(!check_closed(&cut, &Formula::Bot));
    }

    #[test]
    fn conjunction_disjunction_and_bottom_rules_check() {
        let a = zero_eq_zero();
        let b = Formula::eq(one(), one());
        let pair_target = Formula::and(a.clone(), b.clone());
        let pair = Proof::AndIntro(bx(Proof::EqRefl(Term::Zero)), bx(Proof::EqRefl(one())));
        assert!(check_closed(&pair, &pair_target));
        assert!(check(
            std::slice::from_ref(&pair_target),
            &Proof::AndElimL(bx(Proof::Hyp(0))),
            &a
        ));
        assert!(check(
            std::slice::from_ref(&pair_target),
            &Proof::AndElimR(bx(Proof::Hyp(0))),
            &b
        ));

        let either = Formula::or(a.clone(), b.clone());
        assert!(check_closed(
            &Proof::OrIntroL(bx(Proof::EqRefl(Term::Zero))),
            &either
        ));
        assert!(check_closed(
            &Proof::OrIntroR(bx(Proof::EqRefl(one()))),
            &either
        ));
        let cases = Proof::OrElim {
            disjunction: bx(Proof::Hyp(0)),
            left_case: bx(Proof::OrIntroL(bx(Proof::Hyp(0)))),
            right_case: bx(Proof::OrIntroR(bx(Proof::Hyp(0)))),
        };
        assert!(check(std::slice::from_ref(&either), &cases, &either));
        assert!(check(
            &[Formula::Bot],
            &Proof::BotElim(bx(Proof::Hyp(0))),
            &a
        ));
    }

    #[test]
    fn quantifier_rules_shift_eager_context_without_capture() {
        let reflexive = Formula::forall(Formula::eq(Term::Var(0), Term::Var(0)));
        let universal_intro = Proof::ForallIntro(bx(Proof::EqRefl(Term::Var(0))));
        assert!(check_closed(&universal_intro, &reflexive));

        let universal_elim = Proof::ForallElim(bx(Proof::Hyp(0)), one());
        assert!(check(
            std::slice::from_ref(&reflexive),
            &universal_elim,
            &Formula::eq(one(), one())
        ));

        // An outer free variable moves from 0 to 1 below the new binder.
        let outer = Formula::eq(Term::Var(0), Term::Var(0));
        let captured_wrongly = Formula::forall(Formula::eq(Term::Var(0), Term::Var(0)));
        let shifted_correctly = Formula::forall(Formula::eq(Term::Var(1), Term::Var(1)));
        let from_context = Proof::ForallIntro(bx(Proof::Hyp(0)));
        assert!(check(
            std::slice::from_ref(&outer),
            &from_context,
            &shifted_correctly
        ));
        assert!(!check(
            std::slice::from_ref(&outer),
            &from_context,
            &captured_wrongly
        ));

        let existential = Formula::exists(Formula::eq(Term::Var(0), Term::Var(0)));
        let exists_intro = Proof::ExistsIntro(Term::Zero, bx(Proof::EqRefl(Term::Zero)));
        assert!(check_closed(&exists_intro, &existential));

        let exists_elim = Proof::ExistsElim(bx(Proof::Hyp(0)), bx(Proof::EqRefl(Term::Zero)));
        assert!(check(
            std::slice::from_ref(&existential),
            &exists_elim,
            &zero_eq_zero()
        ));

        // Existing hypotheses cross the fresh witness binder and must shift.
        // The existential's body, by contrast, already lives below that
        // binder and must be inserted without another shift.
        let outer = Formula::eq(Term::Var(0), Term::Var(0));
        let source = Formula::exists(Formula::eq(Term::Var(1), Term::Var(1)));
        let use_old_context = Proof::ExistsElim(bx(Proof::Hyp(0)), bx(Proof::Hyp(2)));
        assert!(check(
            &[source.clone(), outer.clone()],
            &use_old_context,
            &outer
        ));
        assert!(!check(
            &[source.clone(), outer.clone()],
            &Proof::ExistsElim(bx(Proof::Hyp(0)), bx(Proof::Hyp(1))),
            &outer
        ));

        let use_source_body = Proof::ExistsElim(bx(Proof::Hyp(0)), bx(Proof::Hyp(0)));
        assert!(check(
            std::slice::from_ref(&source),
            &use_source_body,
            &outer
        ));
        let captured_source = Formula::exists(Formula::eq(Term::Var(0), Term::Var(0)));
        assert!(!check(
            std::slice::from_ref(&captured_source),
            &use_source_body,
            &outer
        ));
    }

    #[test]
    fn equality_and_congruence_rules_check_and_mutations_fail() {
        let zero_one = Formula::eq(Term::Zero, one());
        let one_two = Formula::eq(one(), two());
        let context = [zero_one.clone(), one_two];

        assert!(check_closed(&Proof::EqRefl(Term::Zero), &zero_eq_zero()));
        assert!(check(
            &context,
            &Proof::EqSym(bx(Proof::Hyp(0))),
            &Formula::eq(one(), Term::Zero)
        ));
        assert!(check(
            &context,
            &Proof::EqTrans(bx(Proof::Hyp(0)), bx(Proof::Hyp(1))),
            &Formula::eq(Term::Zero, two())
        ));
        assert!(!check(
            &[zero_one.clone(), Formula::eq(two(), two())],
            &Proof::EqTrans(bx(Proof::Hyp(0)), bx(Proof::Hyp(1))),
            &Formula::eq(Term::Zero, two())
        ));
        assert!(check(
            std::slice::from_ref(&zero_one),
            &Proof::CongS(bx(Proof::Hyp(0))),
            &Formula::eq(one(), two())
        ));

        let two_equations = [zero_one.clone(), zero_one.clone()];
        assert!(check(
            &two_equations,
            &Proof::CongAdd(bx(Proof::Hyp(0)), bx(Proof::Hyp(1))),
            &Formula::eq(Term::plus(Term::Zero, Term::Zero), Term::plus(one(), one()))
        ));
        assert!(check(
            &two_equations,
            &Proof::CongMul(bx(Proof::Hyp(0)), bx(Proof::Hyp(1))),
            &Formula::eq(
                Term::times(Term::Zero, Term::Zero),
                Term::times(one(), one())
            )
        ));

        let motive = Formula::eq(Term::Var(0), Term::Var(0));
        let subst = Proof::EqSubst {
            motive,
            equation: bx(Proof::Hyp(0)),
            body: bx(Proof::EqRefl(Term::Zero)),
        };
        assert!(check(
            std::slice::from_ref(&zero_one),
            &subst,
            &Formula::eq(one(), one())
        ));
    }

    #[test]
    fn every_fixed_axiom_has_its_exact_closed_formula() {
        for name in [
            AxiomName::PA1,
            AxiomName::PA2,
            AxiomName::PA3,
            AxiomName::PA4,
            AxiomName::PA5,
            AxiomName::PA6,
        ] {
            let target = axiom_formula(name);
            assert!(target.well_scoped(0));
            assert!(check_closed(&Proof::Axiom(name), &target));
            assert!(!check_closed(&Proof::Axiom(name), &Formula::Bot));
        }
    }

    #[test]
    fn induction_schema_checks_and_rejects_a_mutated_step() {
        let motive = Formula::eq(Term::Var(0), Term::Var(0));
        let target = Formula::forall(motive.clone());
        let valid = Proof::Ind {
            motive: motive.clone(),
            base: bx(Proof::EqRefl(Term::Zero)),
            step: bx(Proof::ForallIntro(bx(Proof::ImpIntro(bx(Proof::EqRefl(
                Term::succ(Term::Var(0)),
            )))))),
        };
        assert!(check_closed(&valid, &target));

        let mutated = Proof::Ind {
            motive,
            base: bx(Proof::EqRefl(Term::Zero)),
            step: bx(Proof::ForallIntro(bx(Proof::ImpIntro(bx(Proof::EqRefl(
                Term::Var(0),
            )))))),
        };
        assert!(!check_closed(&mutated, &target));

        // A free outer parameter must stay free while the induction variable
        // becomes the step's bound n.  This catches an off-by-one in either
        // the cutoff lift or the opening substitution.
        let parameterized_motive = Formula::eq(
            Term::plus(Term::Var(0), Term::Var(1)),
            Term::plus(Term::Var(0), Term::Var(1)),
        );
        let parameterized_target = Formula::forall(parameterized_motive.clone());
        let parameterized = Proof::Ind {
            motive: parameterized_motive,
            base: bx(Proof::EqRefl(Term::plus(Term::Zero, Term::Var(0)))),
            step: bx(Proof::ForallIntro(bx(Proof::ImpIntro(bx(Proof::EqRefl(
                Term::plus(Term::succ(Term::Var(0)), Term::Var(1)),
            )))))),
        };
        assert!(check(&[], &parameterized, &parameterized_target));
        assert!(!check_closed(&parameterized, &parameterized_target));
    }

    #[test]
    fn dne_is_rejected_by_ha_and_admitted_only_by_classical_checker() {
        let proposition = zero_eq_zero();
        let target = Formula::imp(
            Formula::imp(
                Formula::imp(proposition.clone(), Formula::Bot),
                Formula::Bot,
            ),
            proposition.clone(),
        );
        let proof = Proof::DNE(proposition);
        assert!(!check_closed(&proof, &target));
        assert!(check_closed_classical(&proof, &target));
        assert!(!check_closed_classical(&proof, &Formula::Bot));
    }

    #[test]
    fn closed_boundary_rejects_a_free_original_goal() {
        let open = Formula::eq(Term::Var(0), Term::Var(0));
        assert!(check(&[], &Proof::EqRefl(Term::Var(0)), &open));
        assert!(!check_closed(&Proof::EqRefl(Term::Var(0)), &open));
    }

    #[test]
    fn bounded_gate_consumes_lean_style_path_fuel_and_global_work() {
        let target = zero_eq_zero();
        let proof = Proof::EqRefl(Term::Zero);

        assert!(!check_with_fuel_and_step_limit(
            &[],
            &proof,
            &target,
            0,
            100
        ));
        assert!(!check_with_fuel_and_step_limit(
            &[],
            &proof,
            &target,
            1,
            100
        ));
        assert!(check_with_fuel_and_step_limit(&[], &proof, &target, 2, 100));
        assert!(!check_with_fuel_and_step_limit(&[], &proof, &target, 2, 0));
        assert!(!check_with_fuel_and_step_limit(&[], &proof, &target, 2, 1));
        assert!(check_with_fuel_and_step_limit(&[], &proof, &target, 2, 2));

        let forall_target = Formula::forall(Formula::eq(Term::Var(0), Term::Var(0)));
        let forall_proof = Proof::ForallIntro(bx(Proof::EqRefl(Term::Var(0))));
        assert!(!check_with_fuel_and_step_limit(
            &[],
            &forall_proof,
            &forall_target,
            2,
            100
        ));
        assert!(check_with_fuel_and_step_limit(
            &[],
            &forall_proof,
            &forall_target,
            3,
            100
        ));
    }
}
