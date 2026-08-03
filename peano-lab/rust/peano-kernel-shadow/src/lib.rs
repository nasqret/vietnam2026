#![forbid(unsafe_code)]

//! A small, dependency-free shadow checker for Peano Lab certificates.
//!
//! This crate deliberately contains only immutable syntax, capture-avoiding
//! de Bruijn operations, the checking judgment, and a strict inert artifact
//! boundary.  Tactics, browser bindings, and proof search remain outside the
//! trusted core.  This checker is shadow-only: Python remains the QED authority.

pub mod checker;
pub mod codec;
pub mod subst;
pub mod syntax;

pub use checker::{
    axiom_formula, check, check_classical, check_classical_with_fuel_and_step_limit, check_closed,
    check_closed_classical, check_closed_with_fuel_and_step_limit, check_with_fuel_and_step_limit,
};
pub use codec::{
    Artifact, CodecError, CodecLimits, ShadowLimits, check_canonical_ha,
    check_canonical_ha_with_limits, decode_canonical, decode_canonical_with_limits,
    encode_artifact, encode_artifact_with_limits,
};
pub use subst::{shift_formula, shift_term, subst_formula, subst_term};
pub use syntax::{AxiomName, Formula, Proof, Term};
