//! Immutable abstract syntax accepted by the shadow kernel.

/// First-order Peano-arithmetic terms, using de Bruijn indices for variables.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub enum Term {
    Var(usize),
    Zero,
    Succ(Box<Term>),
    Add(Box<Term>, Box<Term>),
    Mul(Box<Term>, Box<Term>),
}

impl Term {
    #[must_use]
    pub fn succ(term: Self) -> Self {
        Self::Succ(Box::new(term))
    }

    #[must_use]
    pub fn plus(left: Self, right: Self) -> Self {
        Self::Add(Box::new(left), Box::new(right))
    }

    #[must_use]
    pub fn times(left: Self, right: Self) -> Self {
        Self::Mul(Box::new(left), Box::new(right))
    }

    /// Whether every variable is bound at the supplied binder depth.
    #[must_use]
    pub fn well_scoped(&self, depth: usize) -> bool {
        match self {
            Self::Var(index) => *index < depth,
            Self::Zero => true,
            Self::Succ(term) => term.well_scoped(depth),
            Self::Add(left, right) | Self::Mul(left, right) => {
                left.well_scoped(depth) && right.well_scoped(depth)
            }
        }
    }
}

/// Formulas of first-order intuitionistic Peano arithmetic.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub enum Formula {
    Eq(Term, Term),
    Bot,
    Imp(Box<Formula>, Box<Formula>),
    And(Box<Formula>, Box<Formula>),
    Or(Box<Formula>, Box<Formula>),
    Forall(Box<Formula>),
    Exists(Box<Formula>),
}

impl Formula {
    #[must_use]
    pub fn eq(left: Term, right: Term) -> Self {
        Self::Eq(left, right)
    }

    #[must_use]
    pub fn imp(left: Self, right: Self) -> Self {
        Self::Imp(Box::new(left), Box::new(right))
    }

    #[must_use]
    pub fn and(left: Self, right: Self) -> Self {
        Self::And(Box::new(left), Box::new(right))
    }

    #[must_use]
    pub fn or(left: Self, right: Self) -> Self {
        Self::Or(Box::new(left), Box::new(right))
    }

    #[must_use]
    pub fn forall(body: Self) -> Self {
        Self::Forall(Box::new(body))
    }

    #[must_use]
    pub fn exists(body: Self) -> Self {
        Self::Exists(Box::new(body))
    }

    /// Whether every term variable is bound at the supplied binder depth.
    #[must_use]
    pub fn well_scoped(&self, depth: usize) -> bool {
        match self {
            Self::Eq(left, right) => left.well_scoped(depth) && right.well_scoped(depth),
            Self::Bot => true,
            Self::Imp(left, right) | Self::And(left, right) | Self::Or(left, right) => {
                left.well_scoped(depth) && right.well_scoped(depth)
            }
            Self::Forall(body) | Self::Exists(body) => depth
                .checked_add(1)
                .is_some_and(|inner_depth| body.well_scoped(inner_depth)),
        }
    }
}

/// The six fixed arithmetic axiom constants.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum AxiomName {
    PA1,
    PA2,
    PA3,
    PA4,
    PA5,
    PA6,
}

/// Proof certificates.  Constructors are inert; only the checker makes a theorem.
#[derive(Clone, Debug, PartialEq, Eq, Hash)]
pub enum Proof {
    Hyp(usize),
    ImpIntro(Box<Proof>),
    ImpElim(Box<Proof>, Box<Proof>),
    Cut {
        proposition: Formula,
        conclusion: Formula,
        lemma: Box<Proof>,
        body: Box<Proof>,
    },
    AndIntro(Box<Proof>, Box<Proof>),
    AndElimL(Box<Proof>),
    AndElimR(Box<Proof>),
    OrIntroL(Box<Proof>),
    OrIntroR(Box<Proof>),
    OrElim {
        disjunction: Box<Proof>,
        left_case: Box<Proof>,
        right_case: Box<Proof>,
    },
    BotElim(Box<Proof>),
    ForallIntro(Box<Proof>),
    ForallElim(Box<Proof>, Term),
    ExistsIntro(Term, Box<Proof>),
    ExistsElim(Box<Proof>, Box<Proof>),
    EqRefl(Term),
    EqSym(Box<Proof>),
    EqTrans(Box<Proof>, Box<Proof>),
    CongS(Box<Proof>),
    CongAdd(Box<Proof>, Box<Proof>),
    CongMul(Box<Proof>, Box<Proof>),
    EqSubst {
        motive: Formula,
        equation: Box<Proof>,
        body: Box<Proof>,
    },
    DNE(Formula),
    Axiom(AxiomName),
    Ind {
        motive: Formula,
        base: Box<Proof>,
        step: Box<Proof>,
    },
}
