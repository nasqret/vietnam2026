# Independent Lean Live inspection

For the shared current theorem/definition DAG and Hydra's next development
milestone, see [`HYDRA_PRODUCT_ROADMAP.md`](HYDRA_PRODUCT_ROADMAP.md).

Hydra can turn a complete, already generated, **readable-only named proof
strand** into one standalone Lean 4 source file. The source contains every
named prerequisite in dependency order, exactly the conservative definitions
the proof actually uses, and proofs of any required arithmetic foundations.
**The generated file has no import statements whatsoever.** Lean's implicit
standard Prelude supplies the constructive natural-number facts and tactics.

The file does not import Lean modules, `PeanoLab.Codec`, another `PeanoLab`
module, Mathlib, an external package, or a private companion checkout. It
never uses `sorry`, `native_decide`, or a new arithmetic axiom. Compiling it
reconstructs the claimed theorem in Lean; metadata, a source hash, and a share
link are not substitute proof checkers.

## What Lean Live actually provides

The official [Lean Web project](https://github.com/leanprover-community/lean4web)
states that Lean runs **on the playground server**, not inside the browser. It
describes the service as appropriate for small snippets, and explicitly treats
large projects as out of scope. Its
[official URL-argument documentation](https://github.com/leanprover-community/lean4web/blob/main/doc/Usage.md)
recognizes these fragment forms:

```text
https://live.lean-lang.org/#code=<percent-encoded Lean source>
https://live.lean-lang.org/#codez=<LZ-string-compressed Lean source>
https://live.lean-lang.org/#url=<percent-encoded publicly reachable source URL>
```

Hydra generates both documented self-contained source forms, selects the
shorter exact URL, and emits it only when the **complete UTF-8 URL** fits its
default 524,288-byte (512 KiB) campaign-proof limit:

- `#code=` contains the exact percent-encoded standalone source.
- `#codez=` contains that same source compressed with
  [`LZString.compressToBase64`](https://github.com/pieroxy/lz-string/blob/master/src/base64/compressToBase64.ts),
  with its trailing `=` padding removed. This is the exact format selected and
  decoded by [Lean Live's own editor](https://github.com/leanprover-community/lean4web/blob/main/client/src/editor/code-atoms.ts).
  Hydra implements its exact UTF-16 code-unit and standard six-bit Base64
  alphabet in deterministic, bounded, dependency-free Python.

The distinction from `compressToEncodedURIComponent` is essential: standard
Base64 uses `/` for alphabet index 63, while LZ-string's URI variant uses `-`.
Lean Live always applies `decompressFromBase64` to `#codez`; passing the URI
variant silently corrupts any proof containing that differing symbol. Hydra
therefore accepts only canonical, unpadded `[A-Za-z0-9+/]+` payloads, escapes
their reserved `+` and `/` characters as `%2B` and `%2F` in the URL fragment,
and tests them against the upstream JavaScript implementation.

A strict bounded decoder rejects malformed, truncated, noncanonical, or
expansion-bomb payloads. The hosted service compares decoded bytes against the
actual locally compiled source and its SHA-256 before offering a link. The
reviewed server does not emit `#url=`, expose private companion source, invent
an undocumented upload API, claim to have contacted the remote compiler, or
construct a huge nonfunctional link. The official service can change its Lean
version, resource policy, and available packages independently of the local
pinned toolchain.

Opening a link sends the proof source to an external Lean server. This is a
deliberately public sharing action; it does not grant publication, training,
public admission, release approval, or FINAL-evaluation authority.

## Generate one standalone source

```bash
python3 scripts/export_peano_lean.py add_comm \
  --format live \
  --output /tmp/add_comm.lean
```

The command prints the standalone source path and, when it fits, its exact
Lean Live URL. `--verify` performs an actual bounded **local** Lean compile:

```bash
python3 scripts/export_peano_lean.py mul_comm \
  --format live \
  --verify \
  --max-memory-mib 1024 \
  --max-verify-seconds 60 \
  --output /tmp/mul_comm.lean
```

The ordinary Lean proofs remain the complete dependency chain. The exporter
extracts them from exact authenticated source intervals and matches each
generated module against its manifest SHA-256. It does not replay the closed
root theorem or reconstruct a second proof artifact.

Representative measured examples, using the current local release:

| Root | Named theorem nodes | Standalone imports | Source bytes | Compressed URL bytes | Local Lean check |
| --- | ---: | ---: | ---: | ---: | --- |
| `add_comm` | 3 | 0 | 1,781 | 1,324 | Passed |
| `mul_succ_left` (`PA000G`) | 5 | 0 | 2,685 | 1,754 | Passed |
| `mul_comm` | 7 | 0 | 3,386 | 2,041 | Passed |
| Alpha `pythagorean_double_product` | 9 | 0 | 4,316 | 2,610 | Passed |
| Alpha-v21 `euclidean_division_step_exists` | 6 | 0 | 6,575 | 3,792 | Passed |
| Alpha `prime_inverse_prefix_fixed_cases` | 66 | 0 | 90,110 | 35,565 | Passed |
| Alpha `prime_choose_unused_nonendpoint_orbit` | 159 | 0 | 398,596 | 129,151 | Passed |

These complete import-free examples were independently compiled through the
real browser service under the existing 1,024-MiB internal Lean memory setting;
the audited standalone axiom reports contained `propext`. Lean's `-M` option
is an internal runtime limit, **not** an operating-system process-tree RSS
guarantee. Other examples become locally verified only after their exact
standalone source has also completed the bounded compiler check.

## Generate a verified package and its Live source together

A hosted job can retain the full modular proof package and obtain a standalone
download from the **same generation**, with no second proof replay:

```bash
python3 scripts/export_peano_lean.py add_comm \
  --format strand \
  --package-dir /tmp/hydra-add/package \
  --verify \
  --max-memory-mib 1024 \
  --max-verify-seconds 60 \
  --live-lean-output /tmp/hydra-add/live.lean \
  --progress-json
```

This creates:

```text
/tmp/hydra-add/package/manifest.json
/tmp/hydra-add/package/PeanoLab/...
/tmp/hydra-add/live.lean
/tmp/hydra-add/live.json
```

The package modules are checked sequentially. If `--verify` was requested,
the standalone file is also independently compiled, sequentially, within the
same remaining overall verification deadline and memory policy. The sidecar
records, among other facts:

```json
{
  "schema": "peano-lab-lean-live-v1",
  "theorem": "add_comm",
  "source_sha256": "...",
  "source_bytes": 1781,
  "self_contained": true,
  "core_imports": [],
  "external_import_count": 0,
  "share_url": "https://live.lean-lang.org/#codez=...",
  "share_encoding": "codez",
  "share_status": "ready",
  "share_url_max_bytes": 524288,
  "local_source_verified": true,
  "remote_compilation": "not_run"
}
```

The displayed byte count is illustrative. Always trust the generated sidecar,
which binds the exact source bytes and digest. `local_source_verified` means the
local Lean compiler accepted the standalone file; `remote_compilation` remains
`not_run` until a human actually opens and uses Lean Live.

If the complete proof source is safe to download but its encoded URL exceeds
the configured bound, the sidecar sets `share_status` to `oversized` and
`share_url` to `null`. The standalone file remains available. Adjust
`--max-live-url-bytes` only within the hard reviewed ceiling of 1,048,576 bytes
(1 MiB). Standalone source defaults to a separately enforced 1 MiB and can be
explicitly raised to at most 4 MiB with `--max-live-source-kib`. A large URL is
retained in its authenticated sidecar and browser receipt rather than copied
into every bounded progress event.

If any named node required its independently checked **local certificate
fallback**, that node depends on the separately installed private companion.
Direct `--format live` rejects it. A normal verified strand with
`--live-lean-output` still succeeds, but reports Lean Live as unavailable and
does not fabricate a standalone file or share link.

## Campaign-scale theorem proofs

The browser defaults to at most 1,024 named prerequisite theorems, 1 MiB of
standalone source, and a 512 KiB exact Lean Live URL. Current Alpha v25 contains
2,080 checked theorems and 6,633 proof-dependency edges; their dependency
closures all fit the node budget. The largest is the 557-theorem
quadratic-reciprocity closure; 90 closures exceed 256 nodes, nine exceed 512,
and none exceed 1,024. Raising the node
budget does not start any proof automatically: a selected theorem is compiled
only after a human explicitly clicks **Build Lean proof**, and the service
still permits just one bounded Lean worker.

The real 159-theorem `prime_choose_unused_nonendpoint_orbit` campaign strand
contains 5,584 original proof decisions and independently compiles into 398,596
bytes of import-free Lean. Its exact 129,151-byte compressed Lean Live URL is
well within the default limit. Reproduce the complete browser acceptance
check without changing another already-running service by choosing a free port:

```bash
make lean-browser-check \
  PEANO_LEAN_BROWSER_PORT=8902 \
  PEANO_LEAN_BROWSER_CHECK_ARGS="--theorem prime_choose_unused_nonendpoint_orbit --edition alpha"
```

For an unusually large checked strand, an operator may explicitly increase the
source and compressed-URL bounds without enabling hosted source handoff:

```bash
make lean-browser \
  PEANO_LEAN_BROWSER_ARGS="--max-live-source-kib 4096 --max-live-url-bytes 1048576"
```

These are hard reviewed ceilings of 4 MiB decoded source and 1 MiB encoded URL.
The service continues to check the exact decoded source, SHA-256, zero imports,
zero unchecked placeholders, and a real bounded Lean compile. Very large
campaign roots may still exceed a proof-size limit or the external playground's
independently controlled compiler resources; a local verified package remains
available, and no unchecked Lean Live link is fabricated.

## Oversized proofs and private dependencies

The reviewed server never uploads a generated proof, offers the official
`#url=` source-fetch mode, or exposes the private sibling Lean companion. A
proof whose complete direct and compressed links both exceed the reviewed URL
bound remains available only as its bounded downloadable standalone source.
Mixed readable/certificate strands retain their honest companion requirement
and cannot be represented as self-contained Lean Live links.

## Accurate progress and cancellation

`--progress-json` emits one flushed JSON object per factual progress transition
on **stderr**; theorem source and previews remain on stdout. Its stable shape
is:

```json
{
  "kind": "lean_strand_progress",
  "stage": "translate",
  "completed": 2,
  "total": 3,
  "theorem": "add_succ_left"
}
```

Stages are `plan`, `translate`, `certificate`, `package`, `compile`, `repair`,
and `complete`. Optional fields identify the theorem, compiled module, message,
share URL, share status, local standalone check, and unchanged remote status.
Certificate events refer only to the explicitly named dependency-relative
fallback, never to a silently replayed closed-root proof.

The Lean compiler runs in its own process group. When a hosted job sends
`SIGTERM` to the exporter, structured-progress mode forwards cancellation into
that nested group, waits briefly, and escalates to `SIGKILL` if necessary.
The service should allow at least four seconds before force-killing the outer
exporter group, so no unbounded Lean descendant remains running.
