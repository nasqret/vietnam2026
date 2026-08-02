---
title: Verifier-guided policy evaluation and search
tags: [peano-lab, llm, evaluation, search, soundness]
---

# Verifier-guided policy evaluation and search

**Verifier-guided policy evaluation** executes model-proposed tactic lines transactionally and
counts success only after [[kernel-judged-evaluation]] accepts the final certificate against the
original theorem and exact logic mode. Peano Lab's implemented evaluator supports deterministic
independent rollouts, fixed step budgets, pass@k reports, policy and goal-set identities, and a
capability-scoped held-out environment. The target theorem is not importable, and `auto` is not an
unreported escape hatch.

The implemented model-v2 layer is bounded verifier-guided beam search. A policy proposes up to a
fixed number of complete tactic lines at each state; the ordinary public surface either rejects an
action without changing its parent or returns a successor. Every edge is reconstructed from the
root in a fresh session, so siblings cannot share mutable proof state. Complete canonical goal
renderings deduplicate successors, and a documented deterministic priority prefers fewer and
smaller obligations before policy rank. Hard depth, beam, model-call, candidate, and unique-state
budgets bound the run. The registered benchmark uses depth 32 because all four sealed reference
routes replay within 23 actions under exactly the model-v2 authority.

Only final kernel-checked trajectories may feed [[kernel-guided-policy-training|expert iteration]].
The first model-v1 measurement remains 0/4 at pass@4, while one fresh shallow goal had one successful
rollout out of eight. Model-v2 search and its persistent REPL are implemented, but **their learned
solve rate and any expert-iteration result remain pending** until the heavy adapter exists.

The frozen model-v3 launch smoke fixes depth 32, beam width 16, eight candidates per state, 512
model calls, 4,096 discovered states, and 256 generated tokens per candidate for each of four
goals. Evaluation remains untrusted: a separate model-free reader validates the evaluator-v4
authority and all search accounting, then independently kernel-replays every attempt reported as a
proof. The four formulas calibrate infrastructure and include one multistep induction theorem; they
are not a statistically sufficient claim of general PA capability.

The first paired search completed on 2026-08-02. At raw `k=1`, trained job `218171` reported 3/4
and revision/configuration-pinned pretrained job `218172`, reporting no PEFT adapter, reported 0/4.
The three trained tactic scripts independently
kernel-replay with 98, 29, and 10 nodes; the induction-heavy goal was unsolved, and the base's 32
sequences were malformed before tactic execution. Canonical whole-report replay rejected the
trained report because its nested environment omitted four required library-prefix identity
fields. The ordinary verifier remains unchanged. A separately version-pinned historical
attestation has now passed and replayed all 3/3 claims, while a dedicated pretrained attestation
passed declared identity/provenance/search-accounting validation with zero claims. A paired
cross-binding records `paired_launch_smoke_admitted`. Thus the narrow four-goal
`k=1` launch smoke is admitted as 3/4 versus 0/4. It remains too small for statistical inference,
and the unsolved induction theorem prevents an induction-capability claim. Base weight shards and
complete raw generation/extraction/executed-edge transcripts were not attested, so neither
bit-for-bit base identity nor raw-output replay is claimed. The episode illustrates why kernel-valid
proof payloads and a valid experiment identity are separate requirements.

## Related

[[compact-headless-proof-runner]] · [[genealogy-safe-proof-data-split]] · [[pass-at-k]] ·
[[proof-trace-corpus]] · [[peano-lab-moc|Peano Lab MOC]]
