# Independent Lean Live inspection

Hydra can turn a complete, already generated, **readable-only named proof
strand** into one standalone Lean 4 source file. The source contains every
named prerequisite in dependency order, exactly the conservative definitions
the proof actually uses, and proofs of any required arithmetic foundations.
Its only import is the Lean-distributed core tactic module:

```lean
import Lean.Elab.Tactic
```

The file does not import `PeanoLab.Codec`, another `PeanoLab` module, Mathlib,
or a private companion checkout. It never uses `sorry`, `native_decide`, or a
new arithmetic axiom. Compiling it reconstructs the claimed theorem in Lean;
metadata, a source hash, and a share link are not substitute proof checkers.

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

Hydra emits the documented `#code=` form only when the **complete UTF-8 URL**
fits its default 8,192-byte limit. It does not invent an undocumented HTTP
upload API, claim to have contacted the remote compiler, or construct a huge
nonfunctional link. The official service can change its installed project,
Lean version, resource policy, and available packages independently of the
local pinned toolchain.

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

| Root | Named theorem nodes | Share-link result |
| --- | ---: | --- |
| `add_comm` | 3 | Actual URL below 8 KiB; locally Lean-checked |
| `mul_comm` | 7 | Actual URL below 8 KiB; locally Lean-checked |

Both standalone examples were independently compiled under the existing
1,024-MiB internal Lean memory setting, and their final axiom reports contained
`propext`. Lean's `-M` option is an internal runtime limit, **not** an
operating-system process-tree RSS guarantee.

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
  "source_bytes": 1805,
  "share_url": "https://live.lean-lang.org/#code=...",
  "share_status": "ready",
  "share_url_max_bytes": 8192,
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
`--max-live-url-bytes` only within the hard reviewed ceiling of 16,384 bytes;
larger source files are bounded separately by `--max-live-source-kib`.

If any named node required its independently checked **local certificate
fallback**, that node depends on the separately installed private companion.
Direct `--format live` rejects it. A normal verified strand with
`--live-lean-output` still succeeds, but reports Lean Live as unavailable and
does not fabricate a standalone file or share link.

## Large publicly hosted source files

The library function `live_hosted_url(public_https_lean_url)` can construct the
official `#url=` handoff for an **already publicly reachable HTTPS `.lean`
file**. It does not host, upload, expose, or verify the URL. Localhost,
credentials, non-HTTPS URLs, fragments, and non-Lean paths are rejected.

Lean Live must itself be able to fetch that public source, which may require a
suitable CORS configuration; a local `http://127.0.0.1` development server is
not a valid handoff. The playground's small-snippet policy and version drift
still apply even when its URL is short.

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
