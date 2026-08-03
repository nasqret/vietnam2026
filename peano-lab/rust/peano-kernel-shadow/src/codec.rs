//! Strict canonical `peano-lab-v2` certificate interchange.
//!
//! The wire language is deliberately smaller than JSON: exact-arity tagged
//! arrays, fixed unescaped ASCII strings, and canonical non-negative decimal
//! integers.  Parsing this language directly means whitespace, escapes,
//! objects, alternate number spellings, references, and trailing input are
//! rejected rather than normalized.  Every accepted artifact therefore has
//! exactly one byte representation.

use std::fmt;

use crate::checker::check_closed_with_fuel_and_step_limit;
use crate::syntax::{AxiomName, Formula, Proof, Term};

/// The only accepted artifact format tag.
pub const FORMAT_TAG: &str = "peano-lab-v2";

/// Hard ceilings keep recursive decoding and later checking within a bounded
/// native or WebAssembly stack and memory envelope.
pub const HARD_MAX_BYTES: usize = 512 * 1024 * 1024;
pub const HARD_MAX_NODES: usize = 4_000_000;
pub const HARD_MAX_DEPTH: usize = 256;
/// Fixed-width ceiling keeps native and `wasm32` decoding decisions identical.
pub const MAX_WIRE_NAT: usize = u32::MAX as usize;
/// Global checker-work ceiling for a single decoded shadow artifact.
pub const HARD_MAX_CHECK_STEPS: usize = 256_000_000;
pub const DEFAULT_MAX_CHECK_STEPS: usize = 64_000_000;

/// Resource limits applied before an inert artifact can reach the checker.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct CodecLimits {
    max_bytes: usize,
    max_nodes: usize,
    max_depth: usize,
}

impl CodecLimits {
    /// Construct limits no larger than the crate's stack and memory ceilings.
    pub fn new(max_bytes: usize, max_nodes: usize, max_depth: usize) -> Result<Self, CodecError> {
        if max_bytes == 0 || max_bytes > HARD_MAX_BYTES {
            return Err(CodecError::new(0, "invalid byte limit"));
        }
        if max_nodes == 0 || max_nodes > HARD_MAX_NODES {
            return Err(CodecError::new(0, "invalid node limit"));
        }
        if max_depth == 0 || max_depth > HARD_MAX_DEPTH {
            return Err(CodecError::new(0, "invalid depth limit"));
        }
        Ok(Self {
            max_bytes,
            max_nodes,
            max_depth,
        })
    }

    #[must_use]
    pub fn max_bytes(self) -> usize {
        self.max_bytes
    }

    #[must_use]
    pub fn max_nodes(self) -> usize {
        self.max_nodes
    }

    #[must_use]
    pub fn max_depth(self) -> usize {
        self.max_depth
    }
}

impl Default for CodecLimits {
    fn default() -> Self {
        Self {
            max_bytes: HARD_MAX_BYTES,
            max_nodes: HARD_MAX_NODES,
            max_depth: HARD_MAX_DEPTH,
        }
    }
}

/// Complete resource envelope for strict decoding followed by HA checking.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct ShadowLimits {
    codec: CodecLimits,
    max_check_steps: usize,
}

impl ShadowLimits {
    pub fn new(codec: CodecLimits, max_check_steps: usize) -> Result<Self, CodecError> {
        if max_check_steps == 0 || max_check_steps > HARD_MAX_CHECK_STEPS {
            return Err(CodecError::new(0, "invalid checker step limit"));
        }
        Ok(Self {
            codec,
            max_check_steps,
        })
    }

    #[must_use]
    pub fn codec(self) -> CodecLimits {
        self.codec
    }

    #[must_use]
    pub fn max_check_steps(self) -> usize {
        self.max_check_steps
    }
}

impl Default for ShadowLimits {
    fn default() -> Self {
        Self {
            codec: CodecLimits::default(),
            max_check_steps: DEFAULT_MAX_CHECK_STEPS,
        }
    }
}

/// A decoded inert artifact.  The bounded HA shadow gate consumes `fuel` with
/// the same path semantics as the verified Lean endpoint.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Artifact {
    pub fuel: usize,
    pub target: Formula,
    pub proof: Proof,
}

/// A fail-closed codec error with the byte offset at which it was detected.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CodecError {
    pub offset: usize,
    pub message: &'static str,
}

impl CodecError {
    const fn new(offset: usize, message: &'static str) -> Self {
        Self { offset, message }
    }
}

impl fmt::Display for CodecError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{} at byte {}", self.message, self.offset)
    }
}

impl std::error::Error for CodecError {}

struct Decoder<'a> {
    input: &'a [u8],
    position: usize,
    nodes: usize,
    limits: CodecLimits,
}

impl<'a> Decoder<'a> {
    fn new(input: &'a [u8], limits: CodecLimits) -> Result<Self, CodecError> {
        if input.len() > limits.max_bytes {
            return Err(CodecError::new(0, "artifact exceeds byte limit"));
        }
        Ok(Self {
            input,
            position: 0,
            nodes: 0,
            limits,
        })
    }

    fn error(&self, message: &'static str) -> CodecError {
        CodecError::new(self.position, message)
    }

    fn expect(&mut self, expected: u8) -> Result<(), CodecError> {
        if self.input.get(self.position) != Some(&expected) {
            return Err(self.error("unexpected byte"));
        }
        self.position += 1;
        Ok(())
    }

    fn token(&mut self) -> Result<&'a str, CodecError> {
        self.expect(b'"')?;
        let start = self.position;
        while let Some(byte) = self.input.get(self.position).copied() {
            if byte == b'"' {
                if self.position == start {
                    return Err(self.error("empty tag"));
                }
                let bytes = &self.input[start..self.position];
                self.position += 1;
                return std::str::from_utf8(bytes)
                    .map_err(|_| CodecError::new(start, "tag is not ASCII"));
            }
            if !(byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-')) {
                return Err(self.error("tag contains a forbidden byte"));
            }
            self.position += 1;
        }
        Err(self.error("unterminated tag"))
    }

    fn nat(&mut self) -> Result<usize, CodecError> {
        let start = self.position;
        let first = self
            .input
            .get(self.position)
            .copied()
            .ok_or_else(|| self.error("expected a non-negative integer"))?;
        if !first.is_ascii_digit() {
            return Err(self.error("expected a non-negative integer"));
        }
        if first == b'0' {
            self.position += 1;
            if self
                .input
                .get(self.position)
                .is_some_and(u8::is_ascii_digit)
            {
                return Err(CodecError::new(start, "integer has a leading zero"));
            }
            return Ok(0);
        }

        let mut value = 0usize;
        while let Some(byte) = self.input.get(self.position).copied() {
            if !byte.is_ascii_digit() {
                break;
            }
            value = value
                .checked_mul(10)
                .and_then(|number| number.checked_add(usize::from(byte - b'0')))
                .ok_or_else(|| CodecError::new(start, "integer overflows usize"))?;
            self.position += 1;
        }
        if value > MAX_WIRE_NAT {
            return Err(CodecError::new(
                start,
                "integer exceeds portable wire limit",
            ));
        }
        Ok(value)
    }

    fn node(&mut self, depth: usize) -> Result<(), CodecError> {
        if depth > self.limits.max_depth {
            return Err(self.error("artifact exceeds depth limit"));
        }
        self.nodes = self
            .nodes
            .checked_add(1)
            .ok_or_else(|| self.error("artifact node count overflow"))?;
        if self.nodes > self.limits.max_nodes {
            return Err(self.error("artifact exceeds node limit"));
        }
        Ok(())
    }

    fn term(&mut self, depth: usize) -> Result<Term, CodecError> {
        self.node(depth)?;
        self.expect(b'[')?;
        let tag = self.token()?;
        let term = match tag {
            "var" => {
                self.expect(b',')?;
                Term::Var(self.nat()?)
            }
            "zero" => Term::Zero,
            "succ" => {
                self.expect(b',')?;
                Term::succ(self.term(depth + 1)?)
            }
            "add" | "mul" => {
                self.expect(b',')?;
                let left = self.term(depth + 1)?;
                self.expect(b',')?;
                let right = self.term(depth + 1)?;
                if tag == "add" {
                    Term::plus(left, right)
                } else {
                    Term::times(left, right)
                }
            }
            _ => return Err(self.error("unknown term tag")),
        };
        self.expect(b']')?;
        Ok(term)
    }

    fn formula(&mut self, depth: usize) -> Result<Formula, CodecError> {
        self.node(depth)?;
        self.expect(b'[')?;
        let tag = self.token()?;
        let formula = match tag {
            "eq" => {
                self.expect(b',')?;
                let left = self.term(depth + 1)?;
                self.expect(b',')?;
                Formula::eq(left, self.term(depth + 1)?)
            }
            "bot" => Formula::Bot,
            "imp" | "and" | "or" => {
                self.expect(b',')?;
                let left = self.formula(depth + 1)?;
                self.expect(b',')?;
                let right = self.formula(depth + 1)?;
                match tag {
                    "imp" => Formula::imp(left, right),
                    "and" => Formula::and(left, right),
                    _ => Formula::or(left, right),
                }
            }
            "forall" | "exists" => {
                self.expect(b',')?;
                let body = self.formula(depth + 1)?;
                if tag == "forall" {
                    Formula::forall(body)
                } else {
                    Formula::exists(body)
                }
            }
            _ => return Err(self.error("unknown formula tag")),
        };
        self.expect(b']')?;
        Ok(formula)
    }

    fn axiom_name(&mut self) -> Result<AxiomName, CodecError> {
        match self.token()? {
            "PA1" => Ok(AxiomName::PA1),
            "PA2" => Ok(AxiomName::PA2),
            "PA3" => Ok(AxiomName::PA3),
            "PA4" => Ok(AxiomName::PA4),
            "PA5" => Ok(AxiomName::PA5),
            "PA6" => Ok(AxiomName::PA6),
            _ => Err(self.error("unknown axiom name")),
        }
    }

    fn proof(&mut self, depth: usize) -> Result<Proof, CodecError> {
        self.node(depth)?;
        self.expect(b'[')?;
        let tag = self.token()?;
        let proof = match tag {
            "hyp" => {
                self.expect(b',')?;
                Proof::Hyp(self.nat()?)
            }
            "imp_intro" | "and_elim_l" | "and_elim_r" | "or_intro_l" | "or_intro_r"
            | "bot_elim" | "forall_intro" | "eq_sym" | "cong_s" => {
                self.expect(b',')?;
                let child = Box::new(self.proof(depth + 1)?);
                match tag {
                    "imp_intro" => Proof::ImpIntro(child),
                    "and_elim_l" => Proof::AndElimL(child),
                    "and_elim_r" => Proof::AndElimR(child),
                    "or_intro_l" => Proof::OrIntroL(child),
                    "or_intro_r" => Proof::OrIntroR(child),
                    "bot_elim" => Proof::BotElim(child),
                    "forall_intro" => Proof::ForallIntro(child),
                    "eq_sym" => Proof::EqSym(child),
                    _ => Proof::CongS(child),
                }
            }
            "imp_elim" | "and_intro" | "exists_elim" | "eq_trans" | "cong_add" | "cong_mul" => {
                self.expect(b',')?;
                let left = Box::new(self.proof(depth + 1)?);
                self.expect(b',')?;
                let right = Box::new(self.proof(depth + 1)?);
                match tag {
                    "imp_elim" => Proof::ImpElim(left, right),
                    "and_intro" => Proof::AndIntro(left, right),
                    "exists_elim" => Proof::ExistsElim(left, right),
                    "eq_trans" => Proof::EqTrans(left, right),
                    "cong_add" => Proof::CongAdd(left, right),
                    _ => Proof::CongMul(left, right),
                }
            }
            "cut" => {
                self.expect(b',')?;
                let proposition = self.formula(depth + 1)?;
                self.expect(b',')?;
                let conclusion = self.formula(depth + 1)?;
                self.expect(b',')?;
                let lemma = Box::new(self.proof(depth + 1)?);
                self.expect(b',')?;
                let body = Box::new(self.proof(depth + 1)?);
                Proof::Cut {
                    proposition,
                    conclusion,
                    lemma,
                    body,
                }
            }
            "or_elim" => {
                self.expect(b',')?;
                let disjunction = Box::new(self.proof(depth + 1)?);
                self.expect(b',')?;
                let left_case = Box::new(self.proof(depth + 1)?);
                self.expect(b',')?;
                let right_case = Box::new(self.proof(depth + 1)?);
                Proof::OrElim {
                    disjunction,
                    left_case,
                    right_case,
                }
            }
            "forall_elim" => {
                self.expect(b',')?;
                let universal = Box::new(self.proof(depth + 1)?);
                self.expect(b',')?;
                Proof::ForallElim(universal, self.term(depth + 1)?)
            }
            "exists_intro" => {
                self.expect(b',')?;
                let term = self.term(depth + 1)?;
                self.expect(b',')?;
                Proof::ExistsIntro(term, Box::new(self.proof(depth + 1)?))
            }
            "eq_refl" => {
                self.expect(b',')?;
                Proof::EqRefl(self.term(depth + 1)?)
            }
            "eq_subst" => {
                self.expect(b',')?;
                let motive = self.formula(depth + 1)?;
                self.expect(b',')?;
                let equation = Box::new(self.proof(depth + 1)?);
                self.expect(b',')?;
                let body = Box::new(self.proof(depth + 1)?);
                Proof::EqSubst {
                    motive,
                    equation,
                    body,
                }
            }
            "dne" => {
                self.expect(b',')?;
                Proof::DNE(self.formula(depth + 1)?)
            }
            "axiom" => {
                self.expect(b',')?;
                Proof::Axiom(self.axiom_name()?)
            }
            "ind" => {
                self.expect(b',')?;
                let motive = self.formula(depth + 1)?;
                self.expect(b',')?;
                let base = Box::new(self.proof(depth + 1)?);
                self.expect(b',')?;
                let step = Box::new(self.proof(depth + 1)?);
                Proof::Ind { motive, base, step }
            }
            _ => return Err(self.error("unknown proof tag")),
        };
        self.expect(b']')?;
        Ok(proof)
    }

    fn artifact(mut self) -> Result<Artifact, CodecError> {
        self.expect(b'[')?;
        if self.token()? != FORMAT_TAG {
            return Err(self.error("wrong artifact format tag"));
        }
        self.expect(b',')?;
        let fuel = self.nat()?;
        self.expect(b',')?;
        let target = self.formula(1)?;
        self.expect(b',')?;
        let proof = self.proof(1)?;
        self.expect(b']')?;
        self.expect(b'\n')?;
        if self.position != self.input.len() {
            return Err(self.error("trailing input"));
        }
        Ok(Artifact {
            fuel,
            target,
            proof,
        })
    }
}

/// Decode the unique canonical representation using the hard default limits.
pub fn decode_canonical(input: &[u8]) -> Result<Artifact, CodecError> {
    decode_canonical_with_limits(input, CodecLimits::default())
}

/// Decode the unique canonical representation using stricter caller limits.
pub fn decode_canonical_with_limits(
    input: &[u8],
    limits: CodecLimits,
) -> Result<Artifact, CodecError> {
    Decoder::new(input, limits)?.artifact()
}

/// Decode and boundedly shadow-check a closed intuitionistic artifact.
///
/// The artifact's own fuel is consumed with the same mutually recursive path
/// semantics as the verified Lean checker.  A zero/insufficient fuel value, a
/// free original target, exhausted global work, or an unexpected unwinding
/// decoder/checker panic all produce `Ok(false)`.  Syntax and resource-boundary
/// failures are returned as codec errors.  This shadow verdict never grants
/// Peano Lab QED.
pub fn check_canonical_ha(input: &[u8]) -> Result<bool, CodecError> {
    check_canonical_ha_with_limits(input, ShadowLimits::default())
}

/// Decode and boundedly shadow-check using stricter caller limits.
pub fn check_canonical_ha_with_limits(
    input: &[u8],
    limits: ShadowLimits,
) -> Result<bool, CodecError> {
    match std::panic::catch_unwind(std::panic::AssertUnwindSafe(
        || -> Result<bool, CodecError> {
            let artifact = decode_canonical_with_limits(input, limits.codec)?;
            Ok(check_closed_with_fuel_and_step_limit(
                &artifact.proof,
                &artifact.target,
                artifact.fuel,
                limits.max_check_steps,
            ))
        },
    )) {
        Ok(result) => result,
        Err(_) => Ok(false),
    }
}

struct Encoder {
    output: String,
    nodes: usize,
    limits: CodecLimits,
}

impl Encoder {
    fn new(limits: CodecLimits) -> Self {
        Self {
            output: String::new(),
            nodes: 0,
            limits,
        }
    }

    fn push(&mut self, text: &str) -> Result<(), CodecError> {
        let next = self
            .output
            .len()
            .checked_add(text.len())
            .ok_or_else(|| CodecError::new(self.output.len(), "encoded size overflow"))?;
        if next > self.limits.max_bytes {
            return Err(CodecError::new(
                self.output.len(),
                "artifact exceeds byte limit",
            ));
        }
        self.output.push_str(text);
        Ok(())
    }

    fn nat(&mut self, value: usize) -> Result<(), CodecError> {
        if value > MAX_WIRE_NAT {
            return Err(CodecError::new(
                self.output.len(),
                "integer exceeds portable wire limit",
            ));
        }
        self.push(&value.to_string())
    }

    fn node(&mut self, depth: usize) -> Result<(), CodecError> {
        if depth > self.limits.max_depth {
            return Err(CodecError::new(
                self.output.len(),
                "artifact exceeds depth limit",
            ));
        }
        self.nodes = self
            .nodes
            .checked_add(1)
            .ok_or_else(|| CodecError::new(self.output.len(), "artifact node count overflow"))?;
        if self.nodes > self.limits.max_nodes {
            return Err(CodecError::new(
                self.output.len(),
                "artifact exceeds node limit",
            ));
        }
        Ok(())
    }

    fn term(&mut self, term: &Term, depth: usize) -> Result<(), CodecError> {
        self.node(depth)?;
        match term {
            Term::Var(index) => {
                self.push("[\"var\",")?;
                self.nat(*index)?;
                self.push("]")
            }
            Term::Zero => self.push("[\"zero\"]"),
            Term::Succ(inner) => {
                self.push("[\"succ\",")?;
                self.term(inner, depth + 1)?;
                self.push("]")
            }
            Term::Add(left, right) | Term::Mul(left, right) => {
                if matches!(term, Term::Add(_, _)) {
                    self.push("[\"add\",")?;
                } else {
                    self.push("[\"mul\",")?;
                }
                self.term(left, depth + 1)?;
                self.push(",")?;
                self.term(right, depth + 1)?;
                self.push("]")
            }
        }
    }

    fn formula(&mut self, formula: &Formula, depth: usize) -> Result<(), CodecError> {
        self.node(depth)?;
        match formula {
            Formula::Eq(left, right) => {
                self.push("[\"eq\",")?;
                self.term(left, depth + 1)?;
                self.push(",")?;
                self.term(right, depth + 1)?;
                self.push("]")
            }
            Formula::Bot => self.push("[\"bot\"]"),
            Formula::Imp(left, right) | Formula::And(left, right) | Formula::Or(left, right) => {
                match formula {
                    Formula::Imp(_, _) => self.push("[\"imp\",")?,
                    Formula::And(_, _) => self.push("[\"and\",")?,
                    _ => self.push("[\"or\",")?,
                }
                self.formula(left, depth + 1)?;
                self.push(",")?;
                self.formula(right, depth + 1)?;
                self.push("]")
            }
            Formula::Forall(body) | Formula::Exists(body) => {
                if matches!(formula, Formula::Forall(_)) {
                    self.push("[\"forall\",")?;
                } else {
                    self.push("[\"exists\",")?;
                }
                self.formula(body, depth + 1)?;
                self.push("]")
            }
        }
    }

    fn proof(&mut self, proof: &Proof, depth: usize) -> Result<(), CodecError> {
        self.node(depth)?;
        match proof {
            Proof::Hyp(index) => {
                self.push("[\"hyp\",")?;
                self.nat(*index)?;
                self.push("]")
            }
            Proof::ImpIntro(body)
            | Proof::AndElimL(body)
            | Proof::AndElimR(body)
            | Proof::OrIntroL(body)
            | Proof::OrIntroR(body)
            | Proof::BotElim(body)
            | Proof::ForallIntro(body)
            | Proof::EqSym(body)
            | Proof::CongS(body) => {
                let tag = match proof {
                    Proof::ImpIntro(_) => "[\"imp_intro\",",
                    Proof::AndElimL(_) => "[\"and_elim_l\",",
                    Proof::AndElimR(_) => "[\"and_elim_r\",",
                    Proof::OrIntroL(_) => "[\"or_intro_l\",",
                    Proof::OrIntroR(_) => "[\"or_intro_r\",",
                    Proof::BotElim(_) => "[\"bot_elim\",",
                    Proof::ForallIntro(_) => "[\"forall_intro\",",
                    Proof::EqSym(_) => "[\"eq_sym\",",
                    _ => "[\"cong_s\",",
                };
                self.push(tag)?;
                self.proof(body, depth + 1)?;
                self.push("]")
            }
            Proof::ImpElim(left, right)
            | Proof::AndIntro(left, right)
            | Proof::ExistsElim(left, right)
            | Proof::EqTrans(left, right)
            | Proof::CongAdd(left, right)
            | Proof::CongMul(left, right) => {
                let tag = match proof {
                    Proof::ImpElim(_, _) => "[\"imp_elim\",",
                    Proof::AndIntro(_, _) => "[\"and_intro\",",
                    Proof::ExistsElim(_, _) => "[\"exists_elim\",",
                    Proof::EqTrans(_, _) => "[\"eq_trans\",",
                    Proof::CongAdd(_, _) => "[\"cong_add\",",
                    _ => "[\"cong_mul\",",
                };
                self.push(tag)?;
                self.proof(left, depth + 1)?;
                self.push(",")?;
                self.proof(right, depth + 1)?;
                self.push("]")
            }
            Proof::Cut {
                proposition,
                conclusion,
                lemma,
                body,
            } => {
                self.push("[\"cut\",")?;
                self.formula(proposition, depth + 1)?;
                self.push(",")?;
                self.formula(conclusion, depth + 1)?;
                self.push(",")?;
                self.proof(lemma, depth + 1)?;
                self.push(",")?;
                self.proof(body, depth + 1)?;
                self.push("]")
            }
            Proof::OrElim {
                disjunction,
                left_case,
                right_case,
            } => {
                self.push("[\"or_elim\",")?;
                self.proof(disjunction, depth + 1)?;
                self.push(",")?;
                self.proof(left_case, depth + 1)?;
                self.push(",")?;
                self.proof(right_case, depth + 1)?;
                self.push("]")
            }
            Proof::ForallElim(universal, term) => {
                self.push("[\"forall_elim\",")?;
                self.proof(universal, depth + 1)?;
                self.push(",")?;
                self.term(term, depth + 1)?;
                self.push("]")
            }
            Proof::ExistsIntro(term, body) => {
                self.push("[\"exists_intro\",")?;
                self.term(term, depth + 1)?;
                self.push(",")?;
                self.proof(body, depth + 1)?;
                self.push("]")
            }
            Proof::EqRefl(term) => {
                self.push("[\"eq_refl\",")?;
                self.term(term, depth + 1)?;
                self.push("]")
            }
            Proof::EqSubst {
                motive,
                equation,
                body,
            } => {
                self.push("[\"eq_subst\",")?;
                self.formula(motive, depth + 1)?;
                self.push(",")?;
                self.proof(equation, depth + 1)?;
                self.push(",")?;
                self.proof(body, depth + 1)?;
                self.push("]")
            }
            Proof::DNE(proposition) => {
                self.push("[\"dne\",")?;
                self.formula(proposition, depth + 1)?;
                self.push("]")
            }
            Proof::Axiom(name) => {
                let name = match name {
                    AxiomName::PA1 => "PA1",
                    AxiomName::PA2 => "PA2",
                    AxiomName::PA3 => "PA3",
                    AxiomName::PA4 => "PA4",
                    AxiomName::PA5 => "PA5",
                    AxiomName::PA6 => "PA6",
                };
                self.push("[\"axiom\",\"")?;
                self.push(name)?;
                self.push("\"]")
            }
            Proof::Ind { motive, base, step } => {
                self.push("[\"ind\",")?;
                self.formula(motive, depth + 1)?;
                self.push(",")?;
                self.proof(base, depth + 1)?;
                self.push(",")?;
                self.proof(step, depth + 1)?;
                self.push("]")
            }
        }
    }

    fn artifact(mut self, artifact: &Artifact) -> Result<String, CodecError> {
        self.push("[\"")?;
        self.push(FORMAT_TAG)?;
        self.push("\",")?;
        self.nat(artifact.fuel)?;
        self.push(",")?;
        self.formula(&artifact.target, 1)?;
        self.push(",")?;
        self.proof(&artifact.proof, 1)?;
        self.push("]\n")?;
        Ok(self.output)
    }
}

/// Encode an artifact in its unique canonical representation.
pub fn encode_artifact(artifact: &Artifact) -> Result<String, CodecError> {
    encode_artifact_with_limits(artifact, CodecLimits::default())
}

/// Encode an artifact while enforcing stricter caller resource limits.
pub fn encode_artifact_with_limits(
    artifact: &Artifact,
    limits: CodecLimits,
) -> Result<String, CodecError> {
    Encoder::new(limits).artifact(artifact)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{check_closed, check_closed_classical};

    fn bx(proof: Proof) -> Box<Proof> {
        Box::new(proof)
    }

    fn zero_eq_zero() -> Formula {
        Formula::eq(Term::Zero, Term::Zero)
    }

    fn forall_refl() -> Artifact {
        Artifact {
            fuel: 32,
            target: Formula::forall(Formula::eq(Term::Var(0), Term::Var(0))),
            proof: Proof::ForallIntro(bx(Proof::EqRefl(Term::Var(0)))),
        }
    }

    fn cut_refl() -> Artifact {
        let target = zero_eq_zero();
        Artifact {
            fuel: 64,
            target: target.clone(),
            proof: Proof::Cut {
                proposition: target.clone(),
                conclusion: target,
                lemma: bx(Proof::EqRefl(Term::Zero)),
                body: bx(Proof::Hyp(0)),
            },
        }
    }

    #[test]
    fn matches_the_two_verified_lean_v2_fixtures_byte_for_byte() {
        let forall_bytes = "[\"peano-lab-v2\",32,[\"forall\",[\"eq\",[\"var\",0],[\"var\",0]]],[\"forall_intro\",[\"eq_refl\",[\"var\",0]]]]\n";
        let cut_bytes = "[\"peano-lab-v2\",64,[\"eq\",[\"zero\"],[\"zero\"]],[\"cut\",[\"eq\",[\"zero\"],[\"zero\"]],[\"eq\",[\"zero\"],[\"zero\"]],[\"eq_refl\",[\"zero\"]],[\"hyp\",0]]]\n";

        assert_eq!(encode_artifact(&forall_refl()).unwrap(), forall_bytes);
        assert_eq!(
            decode_canonical(forall_bytes.as_bytes()).unwrap(),
            forall_refl()
        );
        assert!(check_canonical_ha(forall_bytes.as_bytes()).unwrap());
        assert_eq!(encode_artifact(&cut_refl()).unwrap(), cut_bytes);
        let decoded = decode_canonical(cut_bytes.as_bytes()).unwrap();
        assert_eq!(decoded, cut_refl());
        assert!(check_closed(&decoded.proof, &decoded.target));
        assert!(check_canonical_ha(cut_bytes.as_bytes()).unwrap());
    }

    #[test]
    fn every_term_formula_and_proof_tag_round_trips() {
        let z = Term::Zero;
        let v = Term::Var(7);
        let terms = Term::plus(Term::succ(v.clone()), Term::times(z.clone(), v.clone()));
        let atom = Formula::eq(terms, z.clone());
        let formulas = Formula::imp(
            Formula::and(Formula::Bot, atom.clone()),
            Formula::or(Formula::forall(atom.clone()), Formula::exists(atom.clone())),
        );
        let leaf = || bx(Proof::Hyp(7));
        let mut proofs = vec![
            Proof::Hyp(7),
            Proof::ImpIntro(leaf()),
            Proof::ImpElim(leaf(), leaf()),
            Proof::Cut {
                proposition: formulas.clone(),
                conclusion: atom.clone(),
                lemma: leaf(),
                body: leaf(),
            },
            Proof::AndIntro(leaf(), leaf()),
            Proof::AndElimL(leaf()),
            Proof::AndElimR(leaf()),
            Proof::OrIntroL(leaf()),
            Proof::OrIntroR(leaf()),
            Proof::OrElim {
                disjunction: leaf(),
                left_case: leaf(),
                right_case: leaf(),
            },
            Proof::BotElim(leaf()),
            Proof::ForallIntro(leaf()),
            Proof::ForallElim(leaf(), z.clone()),
            Proof::ExistsIntro(v, leaf()),
            Proof::ExistsElim(leaf(), leaf()),
            Proof::EqRefl(z),
            Proof::EqSym(leaf()),
            Proof::EqTrans(leaf(), leaf()),
            Proof::CongS(leaf()),
            Proof::CongAdd(leaf(), leaf()),
            Proof::CongMul(leaf(), leaf()),
            Proof::EqSubst {
                motive: formulas.clone(),
                equation: leaf(),
                body: leaf(),
            },
            Proof::DNE(atom.clone()),
            Proof::Ind {
                motive: atom,
                base: leaf(),
                step: leaf(),
            },
        ];
        proofs.extend(
            [
                AxiomName::PA1,
                AxiomName::PA2,
                AxiomName::PA3,
                AxiomName::PA4,
                AxiomName::PA5,
                AxiomName::PA6,
            ]
            .map(Proof::Axiom),
        );

        for proof in proofs {
            let artifact = Artifact {
                fuel: MAX_WIRE_NAT,
                target: formulas.clone(),
                proof,
            };
            let encoded = encode_artifact(&artifact).unwrap();
            assert_eq!(decode_canonical(encoded.as_bytes()).unwrap(), artifact);
        }
    }

    #[test]
    fn every_v2_tag_and_argument_order_is_pinned_by_canonical_literals() {
        let terms = [
            "[\"var\",0]",
            "[\"zero\"]",
            "[\"succ\",[\"zero\"]]",
            "[\"add\",[\"zero\"],[\"var\",0]]",
            "[\"mul\",[\"var\",0],[\"zero\"]]",
        ];
        for term in terms {
            let text = format!("[\"peano-lab-v2\",1,[\"eq\",{term},{term}],[\"hyp\",0]]\n");
            let artifact = decode_canonical(text.as_bytes()).unwrap();
            assert_eq!(encode_artifact(&artifact).unwrap(), text);
        }

        let formulas = [
            "[\"eq\",[\"zero\"],[\"zero\"]]",
            "[\"bot\"]",
            "[\"imp\",[\"bot\"],[\"bot\"]]",
            "[\"and\",[\"bot\"],[\"bot\"]]",
            "[\"or\",[\"bot\"],[\"bot\"]]",
            "[\"forall\",[\"bot\"]]",
            "[\"exists\",[\"bot\"]]",
        ];
        for formula in formulas {
            let text = format!("[\"peano-lab-v2\",1,{formula},[\"hyp\",0]]\n");
            let artifact = decode_canonical(text.as_bytes()).unwrap();
            assert_eq!(encode_artifact(&artifact).unwrap(), text);
        }

        let h = "[\"hyp\",0]";
        let z = "[\"zero\"]";
        let bot = "[\"bot\"]";
        let proofs = [
            h.to_owned(),
            format!("[\"imp_intro\",{h}]"),
            format!("[\"imp_elim\",{h},{h}]"),
            format!("[\"cut\",{bot},{bot},{h},{h}]"),
            format!("[\"and_intro\",{h},{h}]"),
            format!("[\"and_elim_l\",{h}]"),
            format!("[\"and_elim_r\",{h}]"),
            format!("[\"or_intro_l\",{h}]"),
            format!("[\"or_intro_r\",{h}]"),
            format!("[\"or_elim\",{h},{h},{h}]"),
            format!("[\"bot_elim\",{h}]"),
            format!("[\"forall_intro\",{h}]"),
            format!("[\"forall_elim\",{h},{z}]"),
            format!("[\"exists_intro\",{z},{h}]"),
            format!("[\"exists_elim\",{h},{h}]"),
            format!("[\"eq_refl\",{z}]"),
            format!("[\"eq_sym\",{h}]"),
            format!("[\"eq_trans\",{h},{h}]"),
            format!("[\"cong_s\",{h}]"),
            format!("[\"cong_add\",{h},{h}]"),
            format!("[\"cong_mul\",{h},{h}]"),
            format!("[\"eq_subst\",{bot},{h},{h}]"),
            format!("[\"dne\",{bot}]"),
            format!("[\"ind\",{bot},{h},{h}]"),
        ];
        for proof in proofs {
            let text = format!("[\"peano-lab-v2\",1,{bot},{proof}]\n");
            let artifact = decode_canonical(text.as_bytes()).unwrap();
            assert_eq!(encode_artifact(&artifact).unwrap(), text);
        }
        for name in ["PA1", "PA2", "PA3", "PA4", "PA5", "PA6"] {
            let text = format!("[\"peano-lab-v2\",1,{bot},[\"axiom\",\"{name}\"]]\n");
            let artifact = decode_canonical(text.as_bytes()).unwrap();
            assert_eq!(encode_artifact(&artifact).unwrap(), text);
        }
    }

    #[test]
    fn ha_gate_rejects_decoded_dne_while_classical_gate_accepts_it() {
        let proposition = zero_eq_zero();
        let target = Formula::imp(
            Formula::imp(
                Formula::imp(proposition.clone(), Formula::Bot),
                Formula::Bot,
            ),
            proposition.clone(),
        );
        let artifact = Artifact {
            fuel: 32,
            target,
            proof: Proof::DNE(proposition),
        };
        let encoded = encode_artifact(&artifact).unwrap();
        let decoded = decode_canonical(encoded.as_bytes()).unwrap();
        assert!(!check_closed(&decoded.proof, &decoded.target));
        assert!(check_closed_classical(&decoded.proof, &decoded.target));
        assert!(!check_canonical_ha(encoded.as_bytes()).unwrap());
    }

    #[test]
    fn bounded_artifact_gate_uses_wire_fuel_closure_and_global_steps() {
        let mut artifact = forall_refl();
        artifact.fuel = 0;
        let zero_fuel = encode_artifact(&artifact).unwrap();
        assert!(!check_canonical_ha(zero_fuel.as_bytes()).unwrap());
        artifact.fuel = 2;
        let insufficient_fuel = encode_artifact(&artifact).unwrap();
        assert!(!check_canonical_ha(insufficient_fuel.as_bytes()).unwrap());
        artifact.fuel = 3;
        let sufficient_fuel = encode_artifact(&artifact).unwrap();
        assert!(check_canonical_ha(sufficient_fuel.as_bytes()).unwrap());

        let reflexivity = Artifact {
            fuel: 2,
            target: zero_eq_zero(),
            proof: Proof::EqRefl(Term::Zero),
        };
        let reflexivity = encode_artifact(&reflexivity).unwrap();
        let one_step = ShadowLimits::new(CodecLimits::default(), 1).unwrap();
        let two_steps = ShadowLimits::new(CodecLimits::default(), 2).unwrap();
        assert!(!check_canonical_ha_with_limits(reflexivity.as_bytes(), one_step).unwrap());
        assert!(check_canonical_ha_with_limits(reflexivity.as_bytes(), two_steps).unwrap());

        let open = Artifact {
            fuel: 2,
            target: Formula::eq(Term::Var(0), Term::Var(0)),
            proof: Proof::EqRefl(Term::Var(0)),
        };
        let open = encode_artifact(&open).unwrap();
        assert!(!check_canonical_ha(open.as_bytes()).unwrap());
        assert!(check_canonical_ha(b"not an artifact").is_err());
        assert!(ShadowLimits::new(CodecLimits::default(), 0).is_err());
        assert!(ShadowLimits::new(CodecLimits::default(), HARD_MAX_CHECK_STEPS + 1).is_err());
    }

    #[test]
    fn rejects_noncanonical_or_non_tree_bytes() {
        let canonical = encode_artifact(&forall_refl()).unwrap();
        let mutations = [
            canonical.trim_end().to_owned(),
            format!(" {canonical}"),
            canonical.replace(",32,", ", 32,"),
            canonical.replace(",32,", ",032,"),
            canonical.replace(",32,", ",-1,"),
            canonical.replace("peano-lab-v2", "peano-lab-v1"),
            canonical.replace("peano-lab-v2", "peano\\u002dlab-v2"),
            canonical.replace("[\"forall\"", "{\"forall\":"),
            canonical.replace("[\"var\",0]", "[\"ref\",0]"),
            canonical.replace("[\"eq_refl\"", "[\"unknown\""),
            canonical.replace("[\"var\",0]", "[\"var\",0,0]"),
            canonical.replace("[\"eq\",", "[\"eq\",[\"zero\"],"),
            canonical.replacen("[\"peano-lab-v2\",32,", "[\"peano-lab-v2\",32,0,", 1),
            format!("{canonical}\n"),
            format!("{canonical}junk"),
        ];
        for mutation in mutations {
            assert!(
                decode_canonical(mutation.as_bytes()).is_err(),
                "accepted mutation: {mutation:?}"
            );
        }

        assert!(decode_canonical(b"{}\n").is_err());
        assert!(decode_canonical(b"[]\n").is_err());
        assert!(decode_canonical(b"[\"peano-lab-v2\",true,[\"bot\"],[\"hyp\",0]]\n").is_err());
        assert!(decode_canonical(b"[\"peano-lab-v2\",1,[\"bot\"],[\"axiom\",\"PA7\"]]\n").is_err());
        assert!(decode_canonical(&[0xff, b'\n']).is_err());
    }

    #[test]
    fn every_truncation_and_whitespace_insertion_is_rejected() {
        let canonical = encode_artifact(&cut_refl()).unwrap();
        for end in 0..canonical.len() {
            assert!(decode_canonical(&canonical.as_bytes()[..end]).is_err());
        }
        for position in 0..=canonical.len() {
            for whitespace in [b' ', b'\t', b'\r', b'\n'] {
                let mut mutation = canonical.as_bytes().to_vec();
                mutation.insert(position, whitespace);
                assert!(
                    decode_canonical(&mutation).is_err(),
                    "accepted whitespace byte {whitespace:?} at {position}"
                );
            }
        }
    }

    #[test]
    fn rejects_integer_overflow_for_every_numeric_field_kind() {
        let overflow = format!("{}0", usize::MAX);
        let samples = [
            format!("[\"peano-lab-v2\",{overflow},[\"bot\"],[\"hyp\",0]]\n"),
            format!("[\"peano-lab-v2\",1,[\"eq\",[\"var\",{overflow}],[\"zero\"]],[\"hyp\",0]]\n"),
            format!("[\"peano-lab-v2\",1,[\"bot\"],[\"hyp\",{overflow}]]\n"),
        ];
        for sample in samples {
            assert!(decode_canonical(sample.as_bytes()).is_err());
        }

        let nonportable = u64::from(u32::MAX) + 1;
        let sample = format!("[\"peano-lab-v2\",{nonportable},[\"bot\"],[\"hyp\",0]]\n");
        assert!(decode_canonical(sample.as_bytes()).is_err());
        if let Some(fuel) = MAX_WIRE_NAT.checked_add(1) {
            let artifact = Artifact {
                fuel,
                target: Formula::Bot,
                proof: Proof::Hyp(0),
            };
            assert!(encode_artifact(&artifact).is_err());
        }
    }

    #[test]
    fn byte_node_and_depth_limits_fail_closed_for_decode_and_encode() {
        let artifact = forall_refl();
        let encoded = encode_artifact(&artifact).unwrap();
        let byte_limit = CodecLimits::new(encoded.len() - 1, 100, 20).unwrap();
        let node_limit = CodecLimits::new(1_000, 2, 20).unwrap();
        let depth_limit = CodecLimits::new(1_000, 100, 2).unwrap();

        for limits in [byte_limit, node_limit, depth_limit] {
            assert!(decode_canonical_with_limits(encoded.as_bytes(), limits).is_err());
            assert!(encode_artifact_with_limits(&artifact, limits).is_err());
        }
        assert!(CodecLimits::new(0, 1, 1).is_err());
        assert!(CodecLimits::new(1, HARD_MAX_NODES + 1, 1).is_err());
        assert!(CodecLimits::new(1, 1, HARD_MAX_DEPTH + 1).is_err());
    }
}
