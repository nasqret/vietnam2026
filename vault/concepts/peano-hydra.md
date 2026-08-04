---
title: Peano Hydra
tags: [peano-lab, neuro-symbolic, theorem-proving, research-protocol]
---

# Peano Hydra

**Peano Hydra** is both a living native-PA workshop and a falsifiable campaign.
The workshop grows a reviewed arithmetic library and uses a
[[peano-authoring-assistant]] to turn accepted prose into checked, documented
artifacts. The campaign tests whether sparse LLM guidance improves a strong
proof-producing native/[[vampire-reconstruction|Vampire]] prover for Peano Lab
under matched resources.

Its many search components are untrusted: native closure, theorem retrieval,
clause ranking, role-separated Qwen LoRA policies and explanation drafts,
Codex teacher proposals,
Vampire, translations, and proof reconstruction. Every positive result becomes
a theorem only after the [[trusted-kernel]] checks a self-contained
[[proof-certificate]] against the original goal.

Hydra is a sound theorem prover unless [[decidable-proof-fragment|an exact
restricted fragment]] also has independently justified negative evidence.
Standard full Heyting arithmetic is not described as decidable.

The campaign is organized as H0–H6: freeze semantics, seal a library epoch and
benchmark, construct the strongest symbolic baseline, build checked macro
data, run the model/ablation ladder, execute one matched-compute final, and
release enough evidence for independent reproduction.

H0 completed on 2026-08-04. Its retained report is
`artifacts/peano-hydra/h0-validation-v2.json`, SHA-256
`55c60502b2229f4420bd4557058842bebb582f491739e82a6dae06de5b803fdb`.
The earlier v1 is provisional H0.1/H0.2 evidence and is superseded for the
complete-H0 claim.
H1 remains open; no sealed benchmark or LLM-advantage result exists. Its first
executable slices are the 28-test canonical [[peano-authoring-assistant]]
contract and the 38-test [[library-epoch]] transition protocol. The historical
epoch fixture remains provenance-only, but a subordinate replay-complete
candidate pack now carries and fresh-worker kernel-replays all 384 canonical
certificates in an import-guarded
`python -I -S -X pycache_prefix=<fresh-dir>` worker. Its manifest root is
`fe6718465fbb5e89154ccfce5c511b51ee296b21568d1759a00dda8a21f8a25d`
and its theorem replay root is
`88e39a886949e2ef31220397e529871bc907f9cd9311c27dc97710d12ef1e3ba`.
This closes only the replay-transport subgate: both production review
registries are empty, the pack is evaluation-ineligible, and dependency views,
documentation/definition receipts, lineage, independent deposit, and benchmark
sealing remain absent. It is not an A0/H1 or production-$L_0$ completion claim.

Peano Lab remains the sole object language. Under [[peano-logic-profiles]],
constructive PA is the default and classical PA+DNE is separately labeled. Living
`authoring-live` HEAD and frozen `research-eval` epochs are physically
separated. The native/WASM checker stays a shadow until the
[[verified-rust-kernel]] refinement gates pass.

H0 freezes the [[peano-hydra-semantic-profile]]: closed intuitionistic PA,
PA1--PA6, unrestricted induction, no classical checker, no decision fragment,
and only `proved | unknown`. Exact [[peano-hydra-result-evidence]] requires a
fresh kernel check against the original target and content-addresses every hash
preimage. The [[peano-hydra-conformance-campaign]] tests 1,024 positive formulas,
wrong-target certificate reuse, semantic mutations, two cold library replays,
and agreement with an exactly pinned independent Lean reference.

The functional bootstrap composes fixed symbolic
and recorded-transcript heads through exact quotas and
[[critical-proof-frontier|critical-state]] gates. Every imported trace receives
a fresh profile-bound replay, and every discovered route is freshly traced and
kernel replayed again before publication. Its teacher-oracle pilot reproduces
one known 13-command/180-node proof; because the structural route and
contextual hint were selected from known work, it is plumbing evidence only,
not a model result. The structured [[macro-proof-action]] protocol now exists
separately: typed actions compile to public tactics, `Dispatch` is isolated and
untrusted, failure rolls back exactly, and every accepted trace is replay-aware.
Historical surface-macro-v0 rows remain schema-incomplete and comparison-
ineligible; H0 completion does not retroactively promote them.

## Related

- [[critical-proof-frontier]]
- [[peano-hydra-semantic-profile]]
- [[peano-hydra-result-evidence]]
- [[peano-hydra-conformance-campaign]]
- [[macro-proof-action]]
- [[library-epoch]]
- [[sealed-theorem-benchmark]]
- [[matched-compute-proof-evaluation]]
- [[peano-authoring-assistant]]
- [[peano-logic-profiles]]
- [[vampire-reconstruction]]
- [[verified-rust-kernel]]
- [[kernel-guided-policy-training]]
- [[peano-lab-moc]]
