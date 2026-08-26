# Model-v3 paired launch smoke — 2026-08-02

This directory preserves the immutable evidence for one four-goal, `k=1`
Peano Lab launch smoke. The byte-pinned producer records report:

- trained Qwen3-1.7B LoRA adapter: 3/4 goals solved;
- revision/configuration-pinned Qwen3-1.7B pretrained comparison, with no
  PEFT adapter reported: 0/4 goals solved;
- identical frozen goals, prompt authority, seed, decoding policy, and
  depth-32/beam-16/eight-candidate search limits.

The admitted interpretation is intentionally narrow. This is a four-item
infrastructure smoke, not a statistical capability benchmark. The trained
run solved three shallow goals, while the induction-heavy consecutive-product
goal remained unsolved. No broad PA, induction, or causal-training-effect
claim follows.

## Final admission

`paired-launch-smoke-attestation.json` is the final composition record. Its
embedded canonical attestation SHA-256 is
`9b33b4e488f14e38fc7c5a122410d53e9e1123409dcccafdc73e0a8ab1a14bae`.
It cross-binds:

- training job `217859`, trained evaluation `218171`, and pretrained
  comparison `218172`;
- source commit `4d44609ee32d5d28726c082ef7b5649c0a1107a6`;
- the exact training manifest, adapter and tokenizer trees, dataset,
  environment, held-out goals, seed, and search limits;
- the final trained and pretrained producer attestations;
- all declared historical source maps against Git blobs at the pinned commit:
  36/36 evaluator-semantic maps, 61 trained-evaluation files, 62
  pretrained-evaluation files, 62 unique blobs total, and both Slurm scripts
  plus their shared support script.

The trained producer attestation independently replayed the three claimed
scripts through Peano Lab's kernel against their original goals:

| Goal | Script | Certificate nodes |
|---|---|---:|
| closed arithmetic | `norm_num` | 98 |
| existential witness | `exists 5`; `norm_num` | 29 |
| universal right-zero calculation | `intro n`; `rewrite PA3`; `simp` | 10 |

The pretrained producer attestation contains no proof claims and validates
the reported 0/4 search accounting.

## Evidence limits

Two facts cannot be reconstructed from the historical reports:

1. The pretrained base is bound by Hugging Face revision and configuration,
   and the producer records no attached PEFT adapter, but the base-model
   weight shards were not content-hashed before and after evaluation. This is
   not a bit-for-bit base-weight attestation.
2. Complete raw model-output transcripts were not retained. The paired layer
   therefore trusts the byte-pinned historical producer/source/job records
   for model attribution and does not replay every generated candidate. The
   three final proof scripts themselves are independently kernel-checked.

Future stronger benchmarks must seal base-weight or verified LFS identities
and record each model call's state hash, seed, raw decoded-output hashes,
extraction result, executed tactic edge, and verifier result.

## Files

- `training-manifest.json`: exact completed 649/649-step training manifest.
- `trained-report.json`: immutable trained evaluator output.
- `trained-compatibility-replay.json`: version-pinned trained-report replay;
  embedded SHA-256
  `e900a10241db0451992313eb2a7b0341911a7a71cd8af91e831a279874afda56`.
- `pretrained-base-report.json`: immutable pretrained comparison output.
- `pretrained-base-replay.json`: dedicated comparison admission; embedded
  SHA-256
  `056519bc3598a390526fdf9054aa38090d499f7f837af0a2ace7af8caaa560e7`.
- `scheduler-accounting.json`: a read-only `sacct` observation. It is useful
  operational evidence, not a cryptographically authenticated scheduler
  statement.
- `*.out` / `*.err`: copied WMI producer logs. The evaluation stderr files
  are empty; all copied log bytes are listed in `SHA256SUMS`.

The ordinary trained-report replayer remains unchanged and still rejects the
historical trained report's incomplete nested environment identity. The
separate compatibility replay does not weaken that gate or edit the report.
