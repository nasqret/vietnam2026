//! Minimal WebAssembly ABI for the dependency-free Peano Lab shadow checker.
//!
//! This crate deliberately owns only an input buffer and delegates syntax and
//! proof checking to `peano-kernel-shadow`.  It never grants QED: the browser
//! treats every result as a diagnostic after the Python kernel has accepted
//! the original goal.

#![deny(unsafe_op_in_unsafe_fn)]

use std::cell::RefCell;
use std::panic::{AssertUnwindSafe, catch_unwind};

use peano_kernel_shadow::{
    CodecLimits, Formula, Proof, Term, check_classical_with_fuel_and_step_limit,
    check_with_fuel_and_step_limit, decode_canonical_with_limits,
};

/// Version of the raw WebAssembly ABI described in this crate's README.
pub const ABI_VERSION: u32 = 1;

/// The browser may transfer at most 16 MiB for one shadow check.
pub const MAX_INPUT_BYTES: usize = 16 * 1024 * 1024;
/// The strict codec may construct at most one million syntax/proof nodes.
pub const MAX_ARTIFACT_NODES: usize = 1_000_000;
/// The strict codec rejects syntax deeper than this ceiling.
pub const MAX_ARTIFACT_DEPTH: usize = 192;
/// The proof checker may perform at most this many recursive invocations.
pub const MAX_CHECK_STEPS: usize = 64_000_000;
/// Leave fixed-width headroom for every checker-side binder shift.  The codec
/// already pins wire naturals to `u32`; this stricter browser boundary keeps
/// all later index arithmetic identical on native and `wasm32` targets.
pub const MAX_PORTABLE_INDEX: usize = u32::MAX as usize - 256;

/// Input is a closed intuitionistic (HA) certificate.
pub const LOGIC_HA: u32 = 0;
/// Input is a closed certificate in the explicitly labeled PA+DNE extension.
pub const LOGIC_CLASSICAL: u32 = 1;

/// The decoded certificate is accepted by the requested shadow checker.
pub const RESULT_ACCEPT: u32 = 1;
/// The artifact decoded, but it did not establish its original target.
pub const RESULT_LOGICAL_REJECT: u32 = 2;
/// The artifact was malformed or crossed a codec/resource boundary.
pub const RESULT_MALFORMED_OR_RESOURCE: u32 = 3;
/// The caller violated the ABI or the wrapper encountered an internal panic.
pub const RESULT_BAD_CALL_OR_INTERNAL: u32 = 4;

thread_local! {
    /// One browser worker owns one prepared input.  Moving a `Vec` does not
    /// move its allocation, so the pointer returned by `prepare` remains valid
    /// until `check`, `reset`, or another `prepare` call.
    static PENDING_INPUT: RefCell<Option<Vec<u8>>> = const { RefCell::new(None) };
}

fn clear_pending() -> bool {
    PENDING_INPUT
        .try_with(|slot| {
            let Ok(mut pending) = slot.try_borrow_mut() else {
                return false;
            };
            *pending = None;
            true
        })
        .unwrap_or(false)
}

fn prepare_input(length: usize) -> usize {
    if length == 0 || length > MAX_INPUT_BYTES {
        clear_pending();
        return 0;
    }

    PENDING_INPUT
        .try_with(|slot| {
            let Ok(mut pending) = slot.try_borrow_mut() else {
                return 0;
            };
            // A failed preparation always destroys any older capability.
            *pending = None;

            let mut bytes = Vec::new();
            if bytes.try_reserve_exact(length).is_err() {
                return 0;
            }
            bytes.resize(length, 0);
            let address = bytes.as_mut_ptr() as usize;
            if address == 0 {
                return 0;
            }
            *pending = Some(bytes);
            address
        })
        .unwrap_or(0)
}

fn take_input(expected_length: usize) -> Result<Vec<u8>, ()> {
    PENDING_INPUT
        .try_with(|slot| {
            let Ok(mut pending) = slot.try_borrow_mut() else {
                return Err(());
            };
            // `take` makes checking one-shot even when validation fails.
            let bytes = pending.take().ok_or(())?;
            if bytes.len() != expected_length {
                return Err(());
            }
            Ok(bytes)
        })
        .unwrap_or(Err(()))
}

fn term_indices_are_portable(term: &Term) -> bool {
    match term {
        Term::Var(index) => *index <= MAX_PORTABLE_INDEX,
        Term::Zero => true,
        Term::Succ(inner) => term_indices_are_portable(inner),
        Term::Add(left, right) | Term::Mul(left, right) => {
            term_indices_are_portable(left) && term_indices_are_portable(right)
        }
    }
}

fn formula_indices_are_portable(formula: &Formula) -> bool {
    match formula {
        Formula::Eq(left, right) => {
            term_indices_are_portable(left) && term_indices_are_portable(right)
        }
        Formula::Bot => true,
        Formula::Imp(left, right) | Formula::And(left, right) | Formula::Or(left, right) => {
            formula_indices_are_portable(left) && formula_indices_are_portable(right)
        }
        Formula::Forall(body) | Formula::Exists(body) => formula_indices_are_portable(body),
    }
}

fn proof_indices_are_portable(proof: &Proof) -> bool {
    match proof {
        Proof::Hyp(index) => *index <= MAX_PORTABLE_INDEX,
        Proof::ImpIntro(body)
        | Proof::AndElimL(body)
        | Proof::AndElimR(body)
        | Proof::OrIntroL(body)
        | Proof::OrIntroR(body)
        | Proof::BotElim(body)
        | Proof::ForallIntro(body)
        | Proof::EqSym(body)
        | Proof::CongS(body) => proof_indices_are_portable(body),
        Proof::ImpElim(left, right)
        | Proof::AndIntro(left, right)
        | Proof::ExistsElim(left, right)
        | Proof::EqTrans(left, right)
        | Proof::CongAdd(left, right)
        | Proof::CongMul(left, right) => {
            proof_indices_are_portable(left) && proof_indices_are_portable(right)
        }
        Proof::Cut {
            proposition,
            conclusion,
            lemma,
            body,
        } => {
            formula_indices_are_portable(proposition)
                && formula_indices_are_portable(conclusion)
                && proof_indices_are_portable(lemma)
                && proof_indices_are_portable(body)
        }
        Proof::OrElim {
            disjunction,
            left_case,
            right_case,
        } => {
            proof_indices_are_portable(disjunction)
                && proof_indices_are_portable(left_case)
                && proof_indices_are_portable(right_case)
        }
        Proof::ForallElim(body, term) => {
            proof_indices_are_portable(body) && term_indices_are_portable(term)
        }
        Proof::ExistsIntro(term, body) => {
            term_indices_are_portable(term) && proof_indices_are_portable(body)
        }
        Proof::EqRefl(term) => term_indices_are_portable(term),
        Proof::EqSubst {
            motive,
            equation,
            body,
        } => {
            formula_indices_are_portable(motive)
                && proof_indices_are_portable(equation)
                && proof_indices_are_portable(body)
        }
        Proof::DNE(proposition) => formula_indices_are_portable(proposition),
        Proof::Axiom(_) => true,
        Proof::Ind { motive, base, step } => {
            formula_indices_are_portable(motive)
                && proof_indices_are_portable(base)
                && proof_indices_are_portable(step)
        }
    }
}

fn check_input(bytes: &[u8], logic: u32) -> u32 {
    if !matches!(logic, LOGIC_HA | LOGIC_CLASSICAL) {
        return RESULT_BAD_CALL_OR_INTERNAL;
    }

    let codec_limits =
        match CodecLimits::new(MAX_INPUT_BYTES, MAX_ARTIFACT_NODES, MAX_ARTIFACT_DEPTH) {
            Ok(limits) => limits,
            Err(_) => return RESULT_BAD_CALL_OR_INTERNAL,
        };
    let artifact = match decode_canonical_with_limits(bytes, codec_limits) {
        Ok(artifact) => artifact,
        Err(_) => return RESULT_MALFORMED_OR_RESOURCE,
    };

    if !formula_indices_are_portable(&artifact.target)
        || !proof_indices_are_portable(&artifact.proof)
    {
        return RESULT_MALFORMED_OR_RESOURCE;
    }

    if !artifact.target.well_scoped(0) {
        return RESULT_LOGICAL_REJECT;
    }
    let accepted = if logic == LOGIC_HA {
        check_with_fuel_and_step_limit(
            &[],
            &artifact.proof,
            &artifact.target,
            artifact.fuel,
            MAX_CHECK_STEPS,
        )
    } else {
        check_classical_with_fuel_and_step_limit(
            &[],
            &artifact.proof,
            &artifact.target,
            artifact.fuel,
            MAX_CHECK_STEPS,
        )
    };
    if accepted {
        RESULT_ACCEPT
    } else {
        RESULT_LOGICAL_REJECT
    }
}

/// Return the ABI version expected by the browser worker.
#[unsafe(no_mangle)]
pub extern "C" fn peano_shadow_abi_version() -> u32 {
    ABI_VERSION
}

/// Return the maximum permitted byte length for one input artifact.
#[unsafe(no_mangle)]
pub extern "C" fn peano_shadow_max_input_bytes() -> u32 {
    u32::try_from(MAX_INPUT_BYTES).unwrap_or(0)
}

/// Allocate and zero an owned, exact-length one-shot input buffer.
///
/// On `wasm32` the return value is an offset into the module's exported linear
/// memory.  Zero means failure.  Calling this again invalidates the prior
/// offset.  No Rust code dereferences a caller-controlled pointer.
#[unsafe(no_mangle)]
pub extern "C" fn peano_shadow_prepare(length: u32) -> usize {
    catch_unwind(AssertUnwindSafe(|| prepare_input(length as usize))).unwrap_or(0)
}

/// Consume the prepared buffer and return one of the four `RESULT_*` codes.
///
/// `expected_length` must exactly match the preceding `prepare` call.  `logic`
/// is `LOGIC_HA` or `LOGIC_CLASSICAL`.  Every path consumes the capability.
#[unsafe(no_mangle)]
pub extern "C" fn peano_shadow_check(expected_length: u32, logic: u32) -> u32 {
    let bytes = match take_input(expected_length as usize) {
        Ok(bytes) => bytes,
        Err(()) => return RESULT_BAD_CALL_OR_INTERNAL,
    };
    catch_unwind(AssertUnwindSafe(|| check_input(&bytes, logic)))
        .unwrap_or(RESULT_BAD_CALL_OR_INTERNAL)
}

/// Explicitly discard any prepared input.  Returns `1` on success and `4` if
/// the thread-local state was unexpectedly inaccessible or already borrowed.
#[unsafe(no_mangle)]
pub extern "C" fn peano_shadow_reset() -> u32 {
    if clear_pending() {
        RESULT_ACCEPT
    } else {
        RESULT_BAD_CALL_OR_INTERNAL
    }
}

#[cfg(test)]
mod tests {
    use peano_kernel_shadow::{Artifact, Formula, Proof, Term, encode_artifact};

    use super::*;

    fn zero_eq_zero_artifact() -> Vec<u8> {
        encode_artifact(&Artifact {
            fuel: 8,
            target: Formula::eq(Term::Zero, Term::Zero),
            proof: Proof::EqRefl(Term::Zero),
        })
        .expect("test artifact must encode")
        .into_bytes()
    }

    fn classical_dne_artifact() -> Vec<u8> {
        let proposition = Formula::eq(Term::Zero, Term::Zero);
        let negation = Formula::imp(proposition.clone(), Formula::Bot);
        encode_artifact(&Artifact {
            fuel: 8,
            target: Formula::imp(Formula::imp(negation, Formula::Bot), proposition.clone()),
            proof: Proof::DNE(proposition),
        })
        .expect("test artifact must encode")
        .into_bytes()
    }

    fn rejected_artifact() -> Vec<u8> {
        encode_artifact(&Artifact {
            fuel: 8,
            target: Formula::eq(Term::Zero, Term::succ(Term::Zero)),
            proof: Proof::EqRefl(Term::Zero),
        })
        .expect("test artifact must encode")
        .into_bytes()
    }

    fn install(bytes: &[u8]) {
        let installed = PENDING_INPUT.with(|slot| {
            let mut pending = slot.borrow_mut();
            *pending = Some(bytes.to_vec());
            true
        });
        assert!(installed);
    }

    fn check_bytes(bytes: &[u8], logic: u32) -> u32 {
        install(bytes);
        peano_shadow_check(u32::try_from(bytes.len()).expect("small fixture"), logic)
    }

    #[test]
    fn abi_constants_are_pinned() {
        assert_eq!(peano_shadow_abi_version(), 1);
        assert_eq!(peano_shadow_max_input_bytes(), 16 * 1024 * 1024);
        assert_eq!(MAX_ARTIFACT_NODES, 1_000_000);
        assert_eq!(MAX_ARTIFACT_DEPTH, 192);
        assert_eq!(MAX_CHECK_STEPS, 64_000_000);
        assert_eq!(MAX_PORTABLE_INDEX, u32::MAX as usize - 256);
        assert_eq!(
            [
                RESULT_ACCEPT,
                RESULT_LOGICAL_REJECT,
                RESULT_MALFORMED_OR_RESOURCE,
                RESULT_BAD_CALL_OR_INTERNAL,
            ],
            [1, 2, 3, 4]
        );
    }

    #[test]
    fn ha_accepts_a_valid_closed_certificate() {
        assert_eq!(
            check_bytes(&zero_eq_zero_artifact(), LOGIC_HA),
            RESULT_ACCEPT
        );
    }

    #[test]
    fn logical_failure_is_distinct_from_malformed_input() {
        assert_eq!(
            check_bytes(&rejected_artifact(), LOGIC_HA),
            RESULT_LOGICAL_REJECT
        );
        assert_eq!(
            check_bytes(b"not-an-artifact\n", LOGIC_HA),
            RESULT_MALFORMED_OR_RESOURCE
        );
    }

    #[test]
    fn classical_mode_is_explicit_and_does_not_leak_into_ha() {
        let artifact = classical_dne_artifact();
        assert_eq!(check_bytes(&artifact, LOGIC_HA), RESULT_LOGICAL_REJECT);
        assert_eq!(check_bytes(&artifact, LOGIC_CLASSICAL), RESULT_ACCEPT);
    }

    #[test]
    fn invalid_logic_is_a_bad_call_and_still_consumes_input() {
        let artifact = zero_eq_zero_artifact();
        install(&artifact);
        assert_eq!(
            peano_shadow_check(artifact.len() as u32, 27),
            RESULT_BAD_CALL_OR_INTERNAL
        );
        assert_eq!(
            peano_shadow_check(artifact.len() as u32, LOGIC_HA),
            RESULT_BAD_CALL_OR_INTERNAL
        );
    }

    #[test]
    fn check_is_one_shot_on_success_and_failure() {
        let artifact = zero_eq_zero_artifact();
        install(&artifact);
        assert_eq!(
            peano_shadow_check(artifact.len() as u32, LOGIC_HA),
            RESULT_ACCEPT
        );
        assert_eq!(
            peano_shadow_check(artifact.len() as u32, LOGIC_HA),
            RESULT_BAD_CALL_OR_INTERNAL
        );

        install(&artifact);
        assert_eq!(
            peano_shadow_check((artifact.len() - 1) as u32, LOGIC_HA),
            RESULT_BAD_CALL_OR_INTERNAL
        );
        assert_eq!(
            peano_shadow_check(artifact.len() as u32, LOGIC_HA),
            RESULT_BAD_CALL_OR_INTERNAL
        );
    }

    #[test]
    fn reset_discards_a_prepared_input() {
        install(&zero_eq_zero_artifact());
        assert_eq!(peano_shadow_reset(), RESULT_ACCEPT);
        assert_eq!(peano_shadow_check(1, LOGIC_HA), RESULT_BAD_CALL_OR_INTERNAL);
        assert_eq!(peano_shadow_reset(), RESULT_ACCEPT);
    }

    #[test]
    fn prepare_rejects_zero_and_oversize_and_clears_old_input() {
        install(&zero_eq_zero_artifact());
        assert_eq!(peano_shadow_prepare(0), 0);
        assert_eq!(peano_shadow_check(1, LOGIC_HA), RESULT_BAD_CALL_OR_INTERNAL);

        install(&zero_eq_zero_artifact());
        assert_eq!(peano_shadow_prepare((MAX_INPUT_BYTES + 1) as u32), 0);
        assert_eq!(peano_shadow_check(1, LOGIC_HA), RESULT_BAD_CALL_OR_INTERNAL);
    }

    #[test]
    fn prepare_allocates_exactly_the_maximum_and_reset_releases_it() {
        assert_ne!(peano_shadow_prepare(MAX_INPUT_BYTES as u32), 0);
        let length = PENDING_INPUT.with(|slot| {
            slot.borrow()
                .as_ref()
                .map(Vec::len)
                .expect("input must be prepared")
        });
        assert_eq!(length, MAX_INPUT_BYTES);
        assert_eq!(peano_shadow_reset(), RESULT_ACCEPT);
    }

    #[test]
    fn a_new_prepare_invalidates_the_previous_capability() {
        assert_ne!(peano_shadow_prepare(8), 0);
        assert_ne!(peano_shadow_prepare(4), 0);
        assert_eq!(peano_shadow_check(8, LOGIC_HA), RESULT_BAD_CALL_OR_INTERNAL);
        assert_eq!(peano_shadow_check(4, LOGIC_HA), RESULT_BAD_CALL_OR_INTERNAL);
    }

    #[test]
    fn free_original_target_is_a_logical_rejection() {
        let bytes = encode_artifact(&Artifact {
            fuel: 8,
            target: Formula::eq(Term::Var(0), Term::Var(0)),
            proof: Proof::EqRefl(Term::Var(0)),
        })
        .expect("test artifact must encode")
        .into_bytes();
        assert_eq!(check_bytes(&bytes, LOGIC_HA), RESULT_LOGICAL_REJECT);
    }

    #[test]
    fn insufficient_artifact_fuel_is_a_logical_rejection() {
        let bytes = encode_artifact(&Artifact {
            fuel: 0,
            target: Formula::eq(Term::Zero, Term::Zero),
            proof: Proof::EqRefl(Term::Zero),
        })
        .expect("test artifact must encode")
        .into_bytes();
        assert_eq!(check_bytes(&bytes, LOGIC_HA), RESULT_LOGICAL_REJECT);
    }

    #[test]
    fn portable_index_ceiling_is_inclusive_and_reserves_shift_headroom() {
        assert!(term_indices_are_portable(&Term::Var(MAX_PORTABLE_INDEX)));
        assert!(!term_indices_are_portable(&Term::Var(
            MAX_PORTABLE_INDEX + 1
        )));
        assert!(proof_indices_are_portable(&Proof::Hyp(MAX_PORTABLE_INDEX)));
        assert!(!proof_indices_are_portable(&Proof::Hyp(
            MAX_PORTABLE_INDEX + 1
        )));
    }

    #[test]
    fn oversized_wire_index_is_rejected_before_the_checker() {
        let bytes = encode_artifact(&Artifact {
            fuel: 8,
            target: Formula::eq(Term::Zero, Term::Zero),
            proof: Proof::EqRefl(Term::Var(MAX_PORTABLE_INDEX + 1)),
        })
        .expect("the core wire ceiling still admits this boundary fixture")
        .into_bytes();
        assert_eq!(check_bytes(&bytes, LOGIC_HA), RESULT_MALFORMED_OR_RESOURCE);
    }
}
