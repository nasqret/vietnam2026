# Local Peano Model Lab

The native Model Lab keeps the frozen Qwen3-1.7B Peano policy resident on an
Apple-silicon laptop. At the `pa>` prompt, run:

```text
pa prove-model forall n. (n + 0) + 0 = n
```

The terminal displays the canonical prompt state, decoded tactic candidates,
each surface compilation and fresh replay, resulting goals, the search-time
kernel check, and the final independent replay. A proof is written only after
both checks accept the exact route against the original theorem.

This launcher is deliberately marked **diagnostic / not production**. It is
bound to the frozen morning adapter and cannot be redirected to arbitrary
weights or a different model cache.

## Unified launcher modes

The installed `pa` command now has two explicit, process-isolated modes:

```text
pa native    # current model-free 384-theorem arithmetic worktree
pa model     # frozen 247-theorem diagnostic model shell
pa           # backward-compatible alias for `pa model`
```

Native mode dispatches before model environment setup, base/adapter seal
hashing, or weight loading. Its `use THEOREM` tactic replays and kernel-checks
the selected current theorem on demand. Model mode remains byte-bound to the
older 247-theorem source identity used during training; the 384-theorem tree
is never placed on that process's import path.

The selector must be the first argument: use `pa model --live full`, not
`pa --live full model`. By default the native worktree is the sibling
`../vietnam2026-arithmetic`; a checkout in another layout can set
`PEANO_NATIVE_LAB_ROOT` to that repository root.
Native mode requires Python 3.10 or newer and fails before importing Peano Lab
when only an older interpreter is available.

## One-time installation on this Mac

From the repository root:

```bash
scripts/bootstrap_peano_model_lab_macos.sh
scripts/sync_peano_morning_adapter.sh
```

The bootstrap creates `.venv/peano-model-macos`, installs a complete
hash-locked arm64 stack, checks MPS BF16 causal attention, and downloads only
`Qwen/Qwen3-1.7B-Base` commit
`ea980cb0a6c2ae4b936e82123acc929f1cec04c1`. It then verifies the
3,441,185,608-byte safetensors file and its SHA-256 seal. The adapter transfer
uses a hidden staging directory and publishes only after verifying its exact
14-file tree, closed adapter/tokenizer manifests, diagnostic authority, and
successful reload probe. Neither script overwrites an existing installation.
The offline base seal also covers the exact architecture and generation
configuration files consumed by Transformers.

After setup, the `./pa` launcher is offline: it sets the Hub and Transformers
offline flags and reads the pinned repo-local cache. Before loading weights it
rechecks both the 3.44-GB base seal and the complete diagnostic-adapter seal;
`--help` remains lightweight and skips model verification/loading.

To make the command available from every directory, link this checkout's
launcher into a directory already on `PATH`:

```bash
ln -s "$PWD/pa" ~/.local/bin/pa
```

The launcher resolves that symlink back to the repository. On this laptop the
link is already installed, so `pa` and `./pa` select the same frozen runtime.

## Start the persistent shell

```bash
pa
```

Example session:

```text
[startup 1/3] Verifying frozen 3.44 GB base-model seal…
[startup 2/3] Verifying frozen 158 MB adapter seal…
PEANO MODEL LAB — DIAGNOSTIC / NOT PRODUCTION
[startup 3/3] Validating the sealed prompt identity and mapping the 1.7B model ...
Input begins only when the `pa>` prompt appears.
Model ready in ...s · device=mps · base dtype=bfloat16 · adapter artifact=torch.float32×392
pa> pa prove-model forall n. (n + 0) + 0 = n
[request] forall n. (n + 0) + 0 = n
[search] started
[prompt #1] · 7905 chars · requesting 1
  Goal 1: ⊢ ∀ x. x + 0 + 0 = x
[model] 1 valid candidate(s)
  Candidate 1: use add_assoc
[compile + fresh replay] accepted: use add_assoc
  Goal 1: add_assoc : ... ⊢ ∀ x. x + 0 + 0 = x
[prompt #2] · 8211 chars · requesting 1
[model] 1 valid candidate(s)
  Candidate 1: simp [add_assoc]
[compile + fresh replay] accepted: simp [add_assoc]
...
[independent replay] independent_replay_finished · status=accepted
KERNEL-CHECKED PROOF
pa prove ∀ x. x + 0 + 0 = x
use add_assoc
simp [add_assoc]
qed
```

The model loads once per shell, while its candidate counters and deterministic
seed schedule reset for each theorem. Ordinary Peano Lab commands still work,
including manual `pa prove`, `pa eval`, `pa lib`, `pa tactic`, and `kb`. An
active manual proof or tutorial owns every raw input line before
`pa prove-model` is considered. Exit with `quit`, `exit`, `:q`, or Ctrl-D.
Wait for the literal `pa>` prompt before typing. Text entered earlier is only
terminal typeahead because the model process has not begun reading commands.

For a one-shot attempt:

```bash
pa prove-model 'forall n. (n + 0) + 0 = n'
```

## Live display and laptop-safe search

The default `--live concise` view shows goal states and the complete
model/compile/check cycle. To see the exact attested prompt and all event
metadata:

```bash
./pa --live full
```

To suppress the event stream while retaining all checking:

```bash
./pa --live off
```

Defaults are intentionally conservative for 16 GB unified memory:

- one generated candidate per state;
- beam width one;
- 64 new tokens per tactic;
- depth 16, at most 32 physical model calls, and 256 states.

Bounds can be raised explicitly, for example `./pa --beam 2 --candidates 2`,
but multiple deterministic candidates use decoder beam search and increase
activation/KV memory. `--device mps --dtype bfloat16` makes accelerator
selection explicit; an unavailable explicit placement fails instead of
silently falling back.

## What “feedback” means

The adapter's audited prompt contract contains only the current canonical PA
goals. Peano Lab therefore does not append invented compiler-error prose to
the prompt. Instead, the host executes every candidate, rejects failed lines,
tries authorized siblings, and sends each accepted successor's canonical
goals to the next model call. The terminal shows rejection diagnostics to the
human. This preserves the exact training/inference contract while providing a
real model → surface execution → verifier state → model loop.

Each candidate path is reconstructed from the original theorem in a fresh
`ProofSession`; the display says “compile + fresh replay” for this reason.
Closing a branch triggers an internal certificate check. The selected whole
route is then independently replayed once more before the `.pa` and JSON files
are published under `results/peano-policy/interactive-local/`.

The live terminal is the detailed event transcript. The saved JSON records
the runtime/model identities, aggregate generation counters, search
diagnostics, selected route, and independent replay receipt; it does not claim
to preserve every raw prompt or rejected decoder string from the live stream.

## Verified local receipt — 2026-07-31

The installed arm64 CPython 3.12.2 runtime completed both a one-shot proof and
two requests in one resident shell on MPS. The fixed deterministic diagnostic
produced:

- `simp` for `0 * 0 + 3 + (0 * 1 + 1) + (3 + 0) = 7`, checked at 78
  certificate nodes in one model call;
- `use add_assoc` followed by `simp [add_assoc]` for
  `forall n. (n + 0) + 0 = n`, checked at 44 nodes in two model calls.

Both routes passed the search-time kernel check and the independent replay.
The base weight seal is
`6df85b39330e5a425ee36253d0f894e4387e4f0a15b9c53cb467d668e6b3a841`;
the adapter seal is
`817e4f4bf8edb9d47511533c6ef1a9810aa9f0f2353fd4de57af97c82e632324`.

Interactive startup validates the exact theorem source and catalog against
their frozen source, ordered-root, and full-identity hashes; it does not replay
all 247 certificates before every model load. Full certificate reconstruction
and independent checking remain the training/release audit. Whenever a model
route actually invokes `use THEOREM`, that theorem's certificate is still
reconstructed and kernel-checked, and the completed user proof still receives
both final checks described above.

## Verification and troubleshooting

Verify the installed inputs without network access:

```bash
.venv/peano-model-macos/bin/python scripts/prefetch_peano_base_model.py --verify-only
.venv/peano-model-macos/bin/python scripts/verify_peano_morning_adapter.py \
  results/peano-policy/diagnostics/qwen3-1.7b-lora-v3-morning-diagnostic-20260731-r1
```

If MPS is reported unavailable, run the bootstrap from an ordinary macOS
Terminal rather than a restricted sandbox. This Apple-silicon distribution
requires that MPS bootstrap probe to pass; it checks a real allocation and
BF16 causal attention. After a successful bootstrap, CPU remains available as
a much slower runtime option with `./pa --device cpu --dtype float32`.
