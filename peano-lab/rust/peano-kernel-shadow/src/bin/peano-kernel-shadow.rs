//! Minimal native process boundary for the Peano Lab Rust shadow checker.

use std::ffi::OsString;
use std::io::{self, Read, Write};
use std::process::ExitCode;

use peano_kernel_shadow::check_canonical_ha;
use peano_kernel_shadow::codec::HARD_MAX_BYTES;

const ACCEPTED: u8 = 0;
const LOGICAL_REJECTION: u8 = 1;
const INPUT_REJECTION: u8 = 2;
const IO_FAILURE: u8 = 3;
const USAGE_FAILURE: u8 = 64;

const HELP: &str = "Peano Lab native Rust shadow checker (shadow-only; never grants QED)\n\
Usage: peano-kernel-shadow < CANONICAL_V2_ARTIFACT\n\
\n\
Reads exactly one canonical peano-lab-v2 artifact from standard input.\n\
Exit 0: ACCEPT; exit 1: well-formed logical REJECT; exit 2: malformed/resource ERROR.\n";

fn read_bounded<R: Read>(reader: R, max_bytes: usize) -> io::Result<Option<Vec<u8>>> {
    let read_limit = max_bytes.saturating_add(1);
    let mut bytes = Vec::new();
    reader.take(read_limit as u64).read_to_end(&mut bytes)?;
    Ok((bytes.len() <= max_bytes).then_some(bytes))
}

fn write_stdout(bytes: &[u8]) -> Result<(), ()> {
    io::stdout().lock().write_all(bytes).map_err(|_| ())
}

fn error(message: &str, status: u8) -> ExitCode {
    let mut stderr = io::stderr().lock();
    let written = stderr.write_all(b"ERROR: ").and_then(|()| {
        stderr
            .write_all(message.as_bytes())
            .and_then(|()| stderr.write_all(b"\n"))
    });
    if written.is_ok() {
        ExitCode::from(status)
    } else {
        ExitCode::from(IO_FAILURE)
    }
}

fn verdict(word: &[u8], status: u8) -> ExitCode {
    if write_stdout(word).is_err() {
        ExitCode::from(IO_FAILURE)
    } else {
        ExitCode::from(status)
    }
}

fn arguments() -> Vec<OsString> {
    std::env::args_os().skip(1).collect()
}

fn main() -> ExitCode {
    let arguments = arguments();
    if arguments.len() == 1 && matches!(arguments[0].to_str(), Some("-h" | "--help")) {
        return if write_stdout(HELP.as_bytes()).is_ok() {
            ExitCode::SUCCESS
        } else {
            ExitCode::from(IO_FAILURE)
        };
    }
    if !arguments.is_empty() {
        let _ = io::stderr()
            .lock()
            .write_all(b"usage: peano-kernel-shadow < CANONICAL_V2_ARTIFACT\n");
        return ExitCode::from(USAGE_FAILURE);
    }

    let input = match read_bounded(io::stdin().lock(), HARD_MAX_BYTES) {
        Ok(Some(bytes)) => bytes,
        Ok(None) => return error("artifact exceeds byte limit", INPUT_REJECTION),
        Err(_) => return error("failed to read standard input", IO_FAILURE),
    };
    match check_canonical_ha(&input) {
        Ok(true) => verdict(b"ACCEPT\n", ACCEPTED),
        Ok(false) => verdict(b"REJECT\n", LOGICAL_REJECTION),
        Err(codec_error) => error(&codec_error.to_string(), INPUT_REJECTION),
    }
}

#[cfg(test)]
mod tests {
    use std::io::Cursor;

    use super::read_bounded;

    #[test]
    fn bounded_reader_stops_after_the_sentinel_byte() {
        assert_eq!(
            read_bounded(Cursor::new(b"abcd"), 4).unwrap(),
            Some(b"abcd".to_vec())
        );
        assert_eq!(read_bounded(Cursor::new(b"abcde"), 4).unwrap(), None);
        assert_eq!(read_bounded(Cursor::new(b"abcdefghi"), 4).unwrap(), None);
    }
}
