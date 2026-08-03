use std::io::Write;
use std::process::{Command, Output, Stdio};

fn run(arguments: &[&str], input: &[u8]) -> Output {
    let mut child = Command::new(env!("CARGO_BIN_EXE_peano-kernel-shadow"))
        .args(arguments)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child.stdin.take().unwrap().write_all(input).unwrap();
    child.wait_with_output().unwrap()
}

#[test]
fn accepted_closed_ha_artifact_has_the_exact_success_protocol() {
    let artifact = b"[\"peano-lab-v2\",32,[\"forall\",[\"eq\",[\"var\",0],[\"var\",0]]],[\"forall_intro\",[\"eq_refl\",[\"var\",0]]]]\n";
    let output = run(&[], artifact);
    assert_eq!(output.status.code(), Some(0));
    assert_eq!(output.stdout, b"ACCEPT\n");
    assert!(output.stderr.is_empty());
}

#[test]
fn logical_rejection_and_low_fuel_have_exit_one() {
    let wrong_proof = b"[\"peano-lab-v2\",2,[\"bot\"],[\"eq_refl\",[\"zero\"]]]\n";
    let output = run(&[], wrong_proof);
    assert_eq!(output.status.code(), Some(1));
    assert_eq!(output.stdout, b"REJECT\n");
    assert!(output.stderr.is_empty());

    let low_fuel =
        b"[\"peano-lab-v2\",0,[\"eq\",[\"zero\"],[\"zero\"]],[\"eq_refl\",[\"zero\"]]]\n";
    let output = run(&[], low_fuel);
    assert_eq!(output.status.code(), Some(1));
    assert_eq!(output.stdout, b"REJECT\n");
    assert!(output.stderr.is_empty());
}

#[test]
fn malformed_and_resource_rejections_have_the_distinct_exit_two() {
    let missing_lf =
        b"[\"peano-lab-v2\",2,[\"eq\",[\"zero\"],[\"zero\"]],[\"eq_refl\",[\"zero\"]]]";
    let output = run(&[], missing_lf);
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
    assert!(output.stderr.starts_with(b"ERROR: "));
    assert!(output.stderr.ends_with(b"\n"));

    let mut target = "[\"bot\"]".to_owned();
    for _ in 0..257 {
        target = format!("[\"forall\",{target}]");
    }
    let over_depth = format!("[\"peano-lab-v2\",300,{target},[\"hyp\",0]]\n");
    let output = run(&[], over_depth.as_bytes());
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
    assert!(
        output
            .stderr
            .starts_with(b"ERROR: artifact exceeds depth limit")
    );
    assert!(output.stderr.ends_with(b"\n"));
}

#[test]
fn help_identifies_the_non_authoritative_boundary() {
    let output = run(&["--help"], b"");
    assert_eq!(output.status.code(), Some(0));
    assert!(
        output
            .stdout
            .starts_with(b"Peano Lab native Rust shadow checker")
    );
    assert!(
        String::from_utf8(output.stdout)
            .unwrap()
            .contains("shadow-only; never grants QED")
    );
    assert!(output.stderr.is_empty());
}

#[test]
fn positional_arguments_are_usage_errors_not_proof_results() {
    let output = run(&["artifact.json"], b"");
    assert_eq!(output.status.code(), Some(64));
    assert!(output.stdout.is_empty());
    assert_eq!(
        output.stderr,
        b"usage: peano-kernel-shadow < CANONICAL_V2_ARTIFACT\n"
    );
}
