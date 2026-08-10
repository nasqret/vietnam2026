# Peano Hydra: a living arithmetic workshop with many proof explorers

Peano Hydra is a living arithmetic workshop and a controlled experiment, not a
new trust assumption. Its permanent job is to help authors grow an unusually
careful elementary-number-theory library in the one curated Peano Lab
language: precise statements, exact direct dependencies, readable proofs,
efficient certificates, and documentation generated from those same checked
artifacts. Its experimental job is to combine a proof-producing arithmetic
prover with a small language model and ask a narrow, measurable question:

> Under the same inference budget, can the language model help solve more new
> problems than the strongest system that does not generate language-model
> actions?

The adjective *new* matters. The phrase *same budget* matters. Most of all,
*solve* means that Peano Lab's independent kernel checks a complete certificate
against the original formula. A model, a tactic, and an external prover may
suggest a route; none may declare the theorem.

The campaign's normative protocol is
[the binding design](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/PEANO_HYDRA_DESIGN.md), and the executable
milestone gates are in
[the campaign plan](https://github.com/nasqret/vietnam2026/blob/peano-lab/PLAN/11_peano_hydra.md). This chapter explains
why those rules exist.

## First correct the logical claim

Peano Lab uses an intuitionistic proof calculus for first-order arithmetic.
Standard first-order Heyting arithmetic is not a decidable theory: there is no
terminating algorithm that correctly labels every sentence theorem or
non-theorem. A finite website, a bounded search, or a decidable collection of
exercises does not change that fact.

There are therefore two honest goals:

1. build a **sound theorem prover** that returns a checked proof or `unknown`;
2. separately identify a **restricted decidable fragment**, state its exact
   grammar and semantics, and supply evidence for both positive and negative
   answers.

The second claim is stronger. Positive proof certificates are already natural:

\[
  K(\Gamma, p, A)=\mathsf{accept}
\]

says that the small kernel checked certificate $p$ as a derivation of $A$ from
$\Gamma$. A timeout cannot play the corresponding role for non-theorems. To
call a fragment decidable we need a terminating procedure and either
independently checkable negative certificates or agreement with a genuinely
independent reference decision procedure. Until then Hydra is a sound prover,
not a decider.

## One language and two visible logic modes

Hydra does not introduce a “solver language” or an “AI language.” Authors see
Peano Lab formulas, defined notation with conservative expansion receipts,
proof states, tactics, dependencies, and certificates. TPTP, Vampire clauses,
model tokens, Lean definitions, and Rust bytes are internal transport formats.
This is important pedagogically: the library remains readable without knowing
which tool happened to discover a proof.

The default profile is constructive: intuitionistic first-order logic,
PA1–PA6, and unrestricted formula induction. Classical arithmetic is a
different, visibly labeled profile using Peano Lab's existing double-negation-
elimination rule. In that profile we may derive and offer excluded middle,

\[
  A \lor \neg A,
\]

as a convenient theorem or tactic. We do not add excluded middle as a second
primitive merely because it is familiar. DNE and excluded middle are
equivalent over the surrounding intuitionistic logic, and two primitive paths
would obscure which assumption a certificate used. Constructive theorems are
safe imports into a classical session; a DNE-dependent theorem is never an
import into a constructive session.

## From a sentence to a documented theorem

This section specifies the A1–A5 target workflow; the current implementation
is only the A0 protocol slice described later in this chapter. The planned live
assistant will separate three kinds of acceptance that ordinary coding
assistants often blur:

1. **Meaning:** the author accepts one proposed formal reading of the prose.
2. **Derivation:** the kernel accepts a certificate for exactly that reading.
3. **Publication:** a reviewer accepts the complete library artifact.

Suppose an author scribbles, “Every prime dividing a product divides one of
the factors.” Before searching for a proof, the workbench will keep the
verbatim sentence and revision, classify it as a claim, and show one or more
candidate formulas. Each candidate includes a binder table, assumptions,
readable defined notation, its primitive expansion, and a structural read-back
in ordinary language. If primality, nonzero assumptions, or the direction of
divisibility is ambiguous, the assistant says so and identifies whether the
observation came from the parser, definition expander, library graph, bounded
evaluation, kernel, Vampire, a model, or a human reviewer.

This authority label changes the meaning of a diagnostic. A parser can prove
that syntax is malformed. A kernel can prove that a supplied certificate does
not derive the target. A bounded evaluator can exhibit a concrete checked
counterexample within its stated range. Vampire or Qwen can only propose that
something looks wrong or that search stalled. Exhaustion is `unknown`, never
“false.” Most importantly, a proof of a nearby formula does not show that a
candidate captured the author's sentence.

Once the author explicitly accepts a reading, Peano Lab will open the ordinary
interactive proof workspace. Native closure will run first; bounded Vampire
hints and sparse Qwen or teacher proposals will appear only where useful. A completed
certificate is checked against the owner-held original target. The resulting
theorem proposal includes exact dependencies, a readable script, a best-known
optimized certificate, proof metrics, provenance, mutation evidence,
explanation, and previews for the Book, Obsidian vault, and proof explorer.
Only explicit review and export can create a patch or pull request.

The planned workspace will be revisioned and append-only. Every asynchronous
result will carry the document revision, source-unit identity, logic profile, library epoch, and
proof-state precondition it observed. If the author edits while a model is
thinking, the late response becomes `stale`; it cannot silently rewrite the
new document. Training consent defaults to deny, prompt text cannot execute
proof or Git commands, and provider failure changes no accepted state.

There will also be two tempos of library use. `authoring-live` will follow the
newest reviewed library and benefit immediately from new number theory.
`research-eval` will use a physically copied, content-addressed epoch and a fixed
lineage mask. The first makes the product useful; the second prevents a growing
quadratic-reciprocity development from leaking answers into an experiment.

## One authority, many fallible explorers

Hydra deliberately has many ways to be clever and one way to be right.

```text
original goal -> deterministic symbolic closure -> certificate -> kernel
                         |
                         | critical frontier
                         v
                  typed macro proposal
                   /      |      \
          native search   Qwen      Vampire hints
                   \      |      /
                    transactional engine
                         |
                  symbolic closure resumes
                         |
              original-goal kernel replay
                    /             \
            checked theorem     rejection
```

The kernel is the sole positive authority. Everything else is untrusted:

- native normalization, rewriting, connection or focused search;
- theorem retrieval and clause ranking;
- separate Qwen LoRA roles for formalization, retrieval, macro policy,
  value/ranking, critique, and explanation drafting from checked artifacts;
- Codex as a TRAIN/DEV teacher, formalizer, critic, and data generator;
- Vampire as the initial external search assistant; and
- translators and proof reconstruction code.

This is especially important for Vampire. Vampire is the only first-class
external prover in the initial portfolio and is a powerful classical
first-order prover, while Peano Lab's default logic is intuitionistic. A raw
Vampire success is not automatically a proof in Heyting arithmetic. We may use
it on a separately justified validity-preserving translation, or ask it for
premise bundles, instantiations, witnesses, cuts, rewrites, and skeletons. The
final result still has to be reconstructed into ordinary Peano proof terms and
replayed. There is no trusted `vampire_proved` rule. E and SMT are deferred
comparison tools, not unnamed fallback authorities.

### What the first executable Vampire slices prove

A3 makes the trust boundary executable without pretending that a solver status
is a Peano proof. It accepts one **closed** primitive Peano goal and an
explicitly allowed premise set, emits deterministic classical TPTP FOF bytes,
and records which internal TPTP symbol came from which Peano source. No ambient
theorem catalog can leak an extra premise into that problem.

The data path is deliberately asymmetric:

```text
closed Peano goal + explicitly selected premises
        -> deterministic TPTP problem
        -> untrusted executable and raw SZS bytes
        -> small deterministic public-command reconstruction
        -> transactional Peano execution
        -> fresh original-goal kernel replay
```

Reconstruction v3 has only three small families. Top-level reflexivity may
produce `refl`. One selected PA axiom may produce `apply NAME`; one selected
public theorem may produce `use NAME` and `apply NAME`. A top-level conjunction
with exactly two selected PA axioms may produce `split`, `apply NAME1`, and
`apply NAME2` in branch order. Other multi-premise cases are commandless. Raw
SZS bytes are never interpreted as tactic text. Swapped or irrelevant premises
therefore produce ordinary failing tactics and exact transactional rollback.
Even a plan that closes all goals reaches QED only through fresh replay by the
independent kernel against the owner-held original target.

Fake executables remain valuable: they reproducibly exercise deterministic
problem bytes, exact arguments, copy-and-rehash provenance, no-shell execution,
wall and output ceilings, malformed responses, and forced kernel rejection.
A3.1 separately asked whether those same narrow paths work with real Vampire.
The [official Vampire 5.0.1 release](https://github.com/vprover/vampire/releases/tag/v5.0.1)
for macOS ARM64 was downloaded into a temporary directory only. Its ZIP
SHA-256 was
`8c92e649fe7bc622a70000afbdf5a5c51007b384e2d8b8235c95474cc7a68f35`;
the extracted executable SHA-256 was
`b5168c690e0293cdac78f16d8418d7eeabcd6708f90a60cd2bf45313b6d98699`.
Nothing was vendored or installed.

For the real direct diagnostic `0 + 0 = 0` with only `PA3` disclosed,
Vampire returned inert `SZS Theorem`. Offline reconstruction proposed the
ordinary command `apply PA3`. Fresh kernel replay accepted its canonical
2-node, depth-2 proof term. The `encode_proof` SHA-256 was
`25b6f555180e9737fe4aeb0e51f1f9e97911ed9ffc41c6a80ef97088930711cd`;
the complete `peano-lab-v2` artifact SHA-256 was
`3c65761490733d3382932780f26ff2fb382f82eb536a45af41840b172be7efca`.
The conjunction `1 + 0 = 1 ∧ 1 · 0 = 0` with selected premises `PA3`, `PA5`
had TPTP SHA-256
`60b2666d452d253bd982170cc8c3d586c2be836ee72355a4fc108d313d403f96`.
Its real result returned inert `SZS Theorem` and reconstructed
`split; apply PA3; apply PA5`; fresh replay
accepted a 5-node, depth-3 proof term. The `encode_proof` SHA-256 was
`3d47f7636f578cbcaf638006942e19c8ff9c565359967d44b32d20668ef5f812`;
the complete `peano-lab-v2` artifact SHA-256 was
`cc520fd2f72148dc05450c414151a55cca4a18ce528e15bb150d9ea89e493d68`.

WMI provided an independent architecture check with the official x86-64
binary, SHA-256
`81532e088c4ee1238d7ea1d8e868a2dccf8d358ad4d2126d257b4dda7f2e6bd9`.
On the same conjunction, a real `--mode vampire` invocation returned
`SZS Theorem`; Vampire reported 0.001 seconds and 8 MB. These are diagnostic
solver-reported observations, not campaign-grade host resource attestations
and not evidence that Vampire outperforms another method.

The diagnostic is usable now through a one-shot command (replace the binary
path with the exact local Vampire executable):

```bash
python3 scripts/peano_hydra_vampire_assist.py \
  '1 + 0 = 1 ∧ 1 · 0 = 0' \
  --premise PA3 --premise PA5 \
  --vampire /absolute/path/to/vampire \
  --wall-time-ms 5000 --output-bytes 65536
```

The program prints one canonical JSON result and creates no file by default.
For this goal its reconstructed command list is `split`, `apply PA3`,
`apply PA5`; `status = accepted` is emitted only after fresh public replay and
the independent kernel check. The same result explicitly says that H0 host
containment, live Dispatch registration, and every campaign/training/
retrieval/evaluation/publication eligibility flag are false.

There is still a useful systems lesson. Frozen H0 `Dispatch` permits exactly
one adapter process. A source broker cannot occupy that process and then spawn
a second Vampire process. The diagnostics used direct `run_vampire` followed
by offline reconstruction; they were not a live registered `Dispatch` route.
Production integration still needs a reviewed host-protocol amendment or one
self-contained linked executable. Native closure, portfolio scheduling,
solve/resource AUC, and any Vampire capability advantage remain open A3/H2
work.

### The first interactive Hydra loop

A3.2 and A4.0 now join the pieces into a small terminal experiment. This is
the first place where a person can alternate ordinary Peano tactics, a typed
Qwen proposal, and a direct Vampire attempt while keeping one immutable proof
owner. It is intentionally a preview rather than the browser assistant.

The join lives in three modules. `interactive_assistant.py` owns the session
and its transitions. `qwen_hydra_bridge.py` turns a canonical goal plus an
explicit retrieved premise list into a bounded prompt and parses a strict
proposal. `vampire_live.py` lets the host start one pinned Vampire executable
as its sole child, then sends only reconstructed public Peano commands back to
the proof owner. The terminal front end is
`scripts/peano_hydra_assistant_repl.py`.

The key distinction is between **proposing** and **committing**. A Qwen request
contains the current canonical goal, visible `name : statement` pairs, and
finite allow-lists. The terminal accepts a strict JSON response with exactly
four fields:

```json
{"format":"peano-hydra-qwen-proposal","macros":[],"premises":["PA3","PA5"],"v":1}
```

Parsing that object proves only that it is well formed and respects those
allow-lists. It does not run a tactic and does not change the proof owner. The
user must explicitly choose `:accept` for typed macros or `:resolve` to hand
the selected premises to Vampire. A later manual step makes an old proposal
stale. The session retains the exact model-response bytes and re-parses them
before execution, so constructing a look-alike Python proposal object does not
grant premise-selection provenance. Extra JSON fields, duplicated keys,
Markdown fences, unknown names, masked operations, and free-form tactic text
are rejected rather than repaired.

For small programmatic experiments the Python bridge also recognizes a
bounded canonical line form containing only `premises:` and `macro:` records.
It produces the same validated proposal object and gains no extra authority;
the terminal's `:model` command deliberately remains JSON-only.

Vampire receives no authority from that selection. The host owns an absolute
binary path, its expected SHA-256, exact arguments, and wall/CPU/memory/output
bounds. It copies and rehashes the executable, runs it without a shell as the
only child, and treats all SZS output as inert bytes. In this first preview the
focused goal must be closed and have no local context. The small v3
reconstructor may then propose ordinary commands. They execute on a temporary
owner. Failure at any phase returns the exact prior session; if the commands
close the theorem, a fresh replay against the original goal must pass the
independent kernel. The closed session retains that checked-certificate
receipt; no goal plus no receipt is not displayed as QED. Checked open
progress may be kept, but is not called QED.

To run the terminal without Vampire:

```bash
python3 scripts/peano_hydra_assistant_repl.py \
  --theorem '0 + 0 = 0'
```

Every non-command line is one manual tactic. Useful session commands are:

```text
:goals                 show the checked state
:script                print the replayable Peano Lab script
:qwen NAME...          print an exact proposal prompt
:model STRICT_JSON     attach an inert proposal
:accept                transact its typed macros
:resolve               send its selected premises to Vampire
:vampire NAME...       call Vampire with an explicit premise list
:discard               drop pending Qwen data
:undo                  restore the preceding immutable session
:help                  show all commands
:quit                  leave without claiming an unfinished theorem
```

With a locally pinned Vampire, pass both its absolute path and digest:

```bash
python3 scripts/peano_hydra_assistant_repl.py \
  --theorem '1 + 0 = 1 ∧ 1 · 0 = 0' \
  --vampire /absolute/path/to/vampire \
  --vampire-sha256 HEX64
```

Then either ask directly:

```text
:vampire PA3 PA5
:script
```

or exercise the Qwen-selection seam without granting the model execution
rights:

```text
:qwen PA3 PA5
:model {"format":"peano-hydra-qwen-proposal","macros":[],"premises":["PA3","PA5"],"v":1}
:resolve
:script
```

An unretained diagnostic run with the real Vampire 5.0.1 conjunction binary
returned inert theorem status. The
reconstructor emitted exactly `split`, `apply PA3`, and `apply PA5`; fresh
original-goal replay accepted the resulting certificate. This demonstrates
the joined data path, not superiority over native tactics or a retained
campaign receipt.

There was deliberately no trained-Qwen live result in this integration. The
current model-v3 checkpoint was trained for the older next-tactic contract,
whereas this bridge expects premise selection plus typed macros. WMI was
also unreachable during the integration session. We therefore retained the
model boundary and used an explicit JSON proposal rather than silently
translating incompatible output or claiming a model result. A real service
must additionally put wall-time, memory, process, and network containment
around its model transport; the bridge itself bounds only prompt and response
bytes.

This preview does not modify frozen H0 `Dispatch`, run in the browser, provide
the asynchronous A5 service, or establish any Qwen or Vampire capability
advantage. Those are later gates. What it establishes is smaller and useful:
the proposed human--model--resolution loop can already end only in ordinary
Peano commands and a fresh independent-kernel decision.

For this slice, the disjoint terminal/Qwen/session/CI tests passed 59 cases,
and the direct-child Vampire/reconstructor/frozen-macro tests passed 91 cases.
Ten focused Book tests and the Book command-replay check passed too.

## The critical frontier

Calling a transformer for every tiny rewrite would be slow and scientifically
uninteresting. Symbolic code is excellent when the next move follows from a
dense local calculation. Language models are most plausible where search must
make a sparse semantic choice.

Hydra therefore runs cheap deterministic closure until it reaches a fixed
point. The **critical frontier** is a stalled state at which there is no
uniquely justified cheap continuation within the current bounds. Examples are:

- choosing an existential witness;
- inventing an intermediate lemma;
- selecting an induction variable and motive;
- selecting a useful case split;
- retrieving a small premise bundle from hundreds of theorems; or
- deciding which bounded solver should explore which subgoal.

Only then is the generative model called. After one valid high-level choice,
symbolic closure resumes. This leads to the testable decomposition

\[
  \text{proof search}
  = \text{cheap closure}^{*}
    ;\ \text{sparse macro choice}
    ;\ \text{cheap closure}^{*}.
\]

A cheap graph or state ranker may score the high-frequency inner loop. Qwen
should earn its more expensive call by resolving ambiguity that the cheaper
systems do not.

## A macro protocol, not a second proof language

The model does not emit kernel constructors. It proposes a small typed action:

```text
Use(name, specializations*)
Cut(kind = have | suffices, name, formula)
Witness(term)
Induct(variable, motive)
Rewrite(source, direction, location)
Split(kind)
Dispatch(solver, premises, bounds)
```

Each action has one canonical serialization and compiles deterministically to
existing Peano Lab commands. For example, `Witness(t)` becomes the public
`exists t` action; a `Cut` becomes ordinary `have` or `suffices`. `Dispatch`
starts a bounded untrusted search and may return hints or a reconstructable
derivation, but never closes a goal merely because a solver printed “theorem.”

Compilation and execution are transactional. If parsing, specialization,
rewriting, or reconstruction fails, the proof state and undo history remain
exactly unchanged. The trace retains the raw model text, parsed action,
compiled commands, intermediate states, solver transcript, resource use, and
kernel result. This makes it possible to distinguish model failure, interface
failure, search failure, and certificate failure.

The first executable plumbing test uses a deliberately smaller compatibility
format: one complete public Peano line with a structural head. It accepts such
actions as `have`, `induction`, `exists`, `cases`, and `rewrite`, while
rejecting `simp`, `ring`, `compact_arith`, tactical wrappers, session commands,
and multiline scripts. This is enough to test the trust boundary and the
symbolic/model hand-off. It is not yet the structured version-1 action schema
above, and it is not training evidence. Recorded teacher routes require a
complete kernel-checked QED by default; an open trace can enter only through an
explicit partial-evidence option and never becomes a positive proof label.

## Why the library must have epochs

The source-bound model-v3 training epoch contains 247 independently checked
runtime theorems, including a constructive, conservatively encoded Fundamental
Theorem of Arithmetic. It is a powerful training source. It is not a fair test
of whether a model can prove the same theorems after reading their proofs.

At the start of a campaign we freeze an ordered epoch $L_0$. Its content root
commits to each theorem's canonical statement, dependencies, source and script,
certificate, proof size and depth, and declaration order. A model can train on
eligible $L_0$ material. The final benchmark is lineage-disjoint from it.

If the mathematical library later grows, those theorems enter $L_1$. They
cannot silently appear in retrieval or prompts for the $L_0$ experiment. A
new epoch needs a newly sealed benchmark. This rule avoids a surprisingly easy
mistake: improving the prover by adding the answer to its library and then
reporting the improvement as search intelligence.

## Leakage follows mathematical ancestry

Randomly splitting tactic rows is not enough. One authored proof can produce
hundreds of state/action rows, and two differently worded statements can be
the same mathematical problem. Hydra partitions *before* row expansion.

Every target and artifact receives a lineage identity. The separation graph
contains at least:

- proof dependencies and reverse dependencies;
- equivalent or stronger reformulations;
- shared problem-family and generator ancestry;
- generator seed and template relationships; and
- authored, symbolic, teacher, and student provenance.

For a sealed theorem $T$, training and run-time retrieval mask $T$, equivalent
forms, its family, proof and trace, generator seed, stronger capstones,
descendants that reveal it, and any theorem whose certificate depends on a
masked node. The connected components are split first; only then are prompts,
actions, negatives, or paraphrases produced.

This is stricter than matching statement strings. It should be. A theorem
prover that retrieves a disguised copy of the target is demonstrating lookup,
not discovery.

## Quadratic reciprocity as a sealed experiment

Quadratic reciprocity is a demanding stress test because its formal development
requires a long dependency chain and several useful choices of representation.
The current 384-theorem library contains 137 checked reciprocity-infrastructure
certificates, but the reciprocity law itself is not admitted.

For a reciprocity endpoint $Q$ to serve as a test, we must deposit its statement
before its proof enters the library. We then mask
the whole $Q$ lineage: definitions introduced only for the route,
residue-theory lemmas, generated variants, equivalent formulations, authored
scripts, teacher sketches, stronger consequences, and retrieval records whose
proofs use them. The split must use lineage IDs and the dependency graph,
not theorem names.

If instead we first publish the complete development, it becomes excellent
training data for the *next* questions, but it can no longer be clean headline
evidence for proving quadratic reciprocity itself. Both choices are useful;
they answer different questions.

## The teacher experiment is only an interface test

Before spending GPU time, a strong teacher such as Codex may attempt the
symbolic system's unsolved DEV frontier using only the frozen macro interface.
This answers:

> Does the interface expose actions that could bridge the symbolic gaps?

If the teacher cannot solve even 10% of those cases, the likely bottleneck is
the action space, observation, or symbolic backend—not the size of Qwen. If it
solves at least 20%, we have useful headroom for distillation.

But the teacher's score is not a student score. Its outputs may seed tagged
training examples after kernel replay, provided their lineages do not intersect
the final set. It must never see the final benchmark. A spectacular teacher
pilot still does not show that Qwen learned the behavior or that Hydra beats a
symbolic baseline.

The earlier model-v3 four-goal run illustrates the same restraint. The trained
adapter solved three shallow goals at $k=1$, while a revision/configuration-
pinned pretrained comparison solved none; the induction-heavy goal remained
unsolved. Those three scripts kernel-check. Four goals, however, are a launch
smoke, not a statistically defensible capability result and not evidence for
Hydra's new architecture.

### Freeze semantics before optimizing search

Hydra H0.1a begins with a deliberately unglamorous question: *what exact
judgment will every later solver, dataset, prompt, and score mean?* The answer
is now the canonical machine-readable profile
`training/peano_hydra/semantic-profile-v1.json`:

```text
format = peano-hydra-semantic-profile
version = 1
id = peano-lab-ha-intuitionistic-v1
sha256 = 058b1644b066967919dae092e5e562b8845e4dd8415fff31d7cd209d51bc9e43
```

That digest is over compact sorted-key UTF-8 JSON, not the indented display
file. Whitespace may therefore change the file hash without changing the
semantic object, while changing one rule, axiom, translation, or evidence
condition necessarily changes the semantic digest.

The accepted source boundary is part of that object too. Profile v1 records
the complete pre-parser contract: nonempty one-line text with no outer
whitespace, no unsafe Unicode category or explicit `#`, at most 8,192 Unicode
code points, and decimal numerals at most 256. These are operational safeguards
against parser and certificate blowups, not a terminating decision budget.
Accordingly the profile says `decision_claim = false` here and retains
`decision_resource_bounds = null` in its theoremhood claim.

The profile freezes the five term constructors, seven formula constructors,
de Bruijn binding and alpha convention, capture-avoiding substitution, every
intuitionistic proof rule, PA1--PA6, and unrestricted induction over a
well-scoped formula motive. The loader compares its recorded axiom formulas
and proof-constructor inventory with the live kernel. `DNE` and the classical
checker are outside the profile. No external-solver translation is registered.

The target boundary closes a subtle representation loophole. The ordinary
parser reports named free variables, so the early Hydra check rejected
`n = n`. Diagnostic syntax also accepts explicit de Bruijn indices, however;
`#0 = #0` had an empty *name* table even though it was not closed at top-level
binder depth zero. Reflexivity could kernel-check it under an open-variable
reading. This was not a false kernel theorem, but it violated Hydra's claimed
closed-target normal form. Admission now checks de Bruijn scope structurally
and forbids explicit `#k` target syntax.

Profile v1 is intentionally a sound theorem-prover profile, not a decision
procedure. It registers no decidable subfragment and no negative witness.
`proved` means that an ordinary self-contained certificate passed the
intuitionistic kernel against the original closed goal; exhaustion, limits,
timeouts, and all other failures are `unknown`. Publishing `not_theorem` is
forbidden.

The same review separated a *claim boundary* from a complete evidence schema.
Profile v1 says which outcomes are legal and lists the fields a future result
will need, but it now labels that block `required-field-draft`. It does not yet
freeze field types, additional-field policy, or the non-self-referential hash
preimages for theorem, kernel, replay, and run evidence. Calling that sketch a
closed schema would make independent implementations guess. Exact evidence is
therefore H0.1b rather than an invisible assumption.

Hydra policy, runner, and pilot schemas moved to version 2. The semantic digest
appears in every environment, head identity, proposal row, recorded state,
run, source artifact, replay binding, and outcome table produced by this
bootstrap. Importing a legacy batch trace causes a fresh profile-bound replay;
it is not merely relabeled. Serializing a successful run replays the physical
tactic route again and rejects a mutated retained trace. An older Qwen prompt
contract that does not expose the profile identity is rejected before a model
call; a future Hydra-aware prompt version must add that observation honestly.

A second adversarial audit then tried to relabel an already constructed run.
Python's frozen dataclass did not freeze dictionaries nested inside it: provider
metadata, proposal rows, and resource limits could be edited before
serialization, and a copied bootstrap result could even be marked comparison
eligible. Runner v2 now retains a private canonical binding of all publication
fields, revalidates policy heads and proposal rows, reconstructs limits and
degradation from evidence, admits only `proof | exhausted | limit`, and
hard-codes `surface-macro-v0` as comparison-ineligible. Head hashes bind the
complete head declaration and capability environment. Oversized theorems are
rejected before semantic parsing. None of these checks makes the policy trusted;
they prevent a sound proof from carrying false experimental provenance.

At the H0.1a freeze this was not yet H0: H0.1b still had to close the exact
result schema, while H0.2 reference/conformance work and H0.3 typed macros
remained open. The pilot also lacked certificate hashes and depths, kernel
identity, closed evidence hashes, raw provider calls, and resource records.
The following sections describe how those H0 gates were closed; the historical
pilot itself remains comparison-ineligible.

### Closing the evidence boundary

H0.1b turns the earlier claim sketch into an exact transport contract. The
active successor profile is `peano-lab-ha-intuitionistic-v2`, with semantic
SHA-256
`4f2713e6a21e6261bbefe5991ef545e6356807e7042c6b2c7c07183e142c3b4b`.
It does not change the object language, logic, PA axioms, induction rule, or
theoremhood claim. It changes the evidence block from a draft into a reference
to `peano-hydra-result-v1`, whose semantic SHA-256 is
`cf1caf1c867ddfbe3c247e42a18b730ea6790269718170a51f9733d5a7a36b26`.
Profile v1 remains a separately registered historical object; no published
digest is reinterpreted.

The result schema has only two disjoint variants. A `proved` result carries the
canonical original theorem, a bounded `peano-lab-v2` certificate artifact,
certificate size and depth, the exact intuitionistic-kernel identity, replay
evidence, run evidence, and the literal Boolean `kernel_accepted = true`. Its
public constructor accepts a parsed `Formula` and `Proof`, checks that proof
twice against the original formula, derives every metric and hash, and only
then emits the record. An `unknown` result carries a small reason enum and run
evidence. It has no certificate, kernel acceptance bit, negative witness, or
solver status. Extra fields are rejected in both variants.

Every digest has a domain-separated, non-self-referential preimage. The
preimage is compact sorted-key UTF-8 JSON containing its format, version,
domain name, and payload. Kernel, replay, and run evidence are separate exact
objects, and each object is forbidden from containing the digest that will be
computed from it. This makes the statement “these hashes agree” independently
testable rather than an appeal to the producer.

Two audit failures explain why this ceremony matters. The first draft exposed
a builder that accepted theorem text and a caller-supplied acceptance Boolean;
that made a checked-looking record forgeable without a `Proof`. The replacement
builder owns parsing-independent formula and certificate objects and invokes
the kernel itself. A later audit found that forbidding the token
`not_theorem` was not enough: identifiers such as `not-theorem` and
`not.theorem` crossed the same semantic boundary. Safe identifiers now reject
separator-equivalent negative vocabulary too.

Versioning must freeze executable interpretation as well as JSON bytes. The
first registry mapped both historical profile versions to the current browser
parser, printer, and input limits. A future UI change could therefore make an
old profile unloadable while its file hash remained unchanged. H0 now includes
a small frozen v1 compatibility canonicalizer for the shared grammar,
admission boundary, scope check, and printer. It agrees with the original live
canonicalization on all 384 current public statements, and historical loading
still works when tests deliberately replace the live parser, printer, or
limits. A separate active-alignment check detects real implementation drift.

### What a typed macro is—and is not

The typed protocol was designed by repeatedly asking where a language model or
external solver could accidentally acquire proof authority. The answer is:
nowhere. A macro is an inert request for ordinary public Peano Lab operations.
Its canonical `peano-hydra-macro-v1` semantic SHA-256 is
`b5fef1ea1b85251ab7f0b8c111cb37e789f96f20771665b4f0dc8b746400552c`.
The version-1 compilation map is deliberately small:

| Typed action | Deterministic public effect |
| --- | --- |
| `Use(name, specializations)` | `use name`, followed by bounded `specialize` lines |
| `Cut(have, name, formula)` | one canonical `have name : formula` line |
| `Cut(suffices, name, formula)` | one canonical `suffices name : formula` line |
| `Witness(term)` | one canonical `exists term` line |
| `Induct(variable, motive)` | `induction variable`; the engine-derived motive must equal the transported motive |
| `Rewrite(source, direction, location)` | one canonical `rewrite` line |
| `Split(kind)` | exactly `split`, `left`, or `right` |
| `Dispatch(...)` | one bounded untrusted process call whose returned lines must re-enter this same public surface |

The motive check on `Induct` is a useful example. The macro transports a motive
so a dataset records the choice the policy intended to make, but compilation
does not trust that text. After the public induction tactic runs, the host
derives the actual motive from the proof state and requires equality. The
transport therefore remains informative without becoming a second induction
rule.

Execution is one transaction. The runner snapshots the immutable owner,
capability declaration, semantic profile, original theorem, replay prefix, and
available solver identities. It parses and compiles the proposal, then runs
each public command against a temporary owner with browser tracing disabled.
Only complete success publishes the successor. Any parse, capability, solver,
tactic, or finalization failure returns the identical original owner. If the
temporary state closes, the runner starts again from the original theorem,
replays the complete public route, and calls the independent intuitionistic
kernel. A solver status never closes a goal.

`Dispatch` was the difficult action. An early implementation registered an
in-process Python callback. A callback could retain a reference to the owner,
mutate its trace logger, ignore the declared timeout, alter globals, or simply
never return. A frozen dataclass did not help: `object.__setattr__` can bypass
that convention, and nested mutable objects remain mutable. The accepted
design therefore has no callback registration API. It registers one bounded,
content-addressed executable plus canonical configuration and invokes a copied
artifact in a fresh process. The child receives detached canonical JSON on
stdin; stdout remains inert bytes until the process terminates under the host
envelope. Returned commands are reparsed, capability-checked, executed through
the public tactic surface, and included in the fresh original-goal replay.

The resource record distinguishes authority from observation. Wall time,
output, file descriptors, process count, and—on the campaign Linux host—hard
address/data limits are host constraints. `steps_used` is explicitly an
untrusted adapter report which must fit the requested value before its response
is considered, but it is not advertised as a host counter. macOS RSS sampling
is useful diagnostic evidence, not a certified peak-memory ceiling; a retained
campaign-grade dispatch requires the registered non-root Linux isolation
envelope. This distinction was discovered by trying to falsify the resource
claims, not by inspecting a successful example.

### A trace must replay, not merely look plausible

The canonical JSONL trace records the profile and macro-protocol identities,
original theorem and hash, exact command/theorem capabilities, registered
adapter identities, raw proposal, parse result, deterministic compilation,
state before, every intermediate state, solver call and raw response, resource
usage, state after, rollback or acceptance, and fresh kernel outcome. Size,
line, command-count, replay-length, diagnostic, and artifact limits are part of
the protocol document.

Shape validation was not enough. An adversarial review constructed records
with internally consistent fake hashes, changed capability environments,
invented states, false host measurements, and fabricated final certificate
metrics. `MacroTrace.from_record` therefore performs semantic replay. It
reparses the raw proposal, recompiles it under the recorded capabilities,
reconstructs the owner prefix, resolves dispatch premises from that state,
replays every claimed intermediate command, and independently repeats any
claimed final kernel check and certificate encoding. The exact adapter
configuration and child-call preimage are retained so a standalone validator
does not have to guess what the external program received.

Several small audit discoveries became permanent tests: a forged exact
registration must be reconstructed through its constructor; all error strings
obey both character and UTF-8 byte limits; observed resource values must fit
their declared bounds; malformed solver output must retain bounded raw and host
evidence; the global output-limit rejection must itself fit in a trace; and
the runner's trace/adapter versions must equal the versions frozen in the
protocol. This is the main pedagogical lesson of H0.3: a trace is evidence only
to the extent that an independent path can replay its claims.

### The H0 conformance experiment

H0.2 separates theorem proving from theoremhood decision. Its positive corpus
contains the 384 dependency-ordered public theorems and 640 deterministic
generated reflexive formulas, for 1,024 distinct kernel-accepted formulas.
Every positive certificate is also checked against one deliberately different
target and must be rejected. Those pairs are labeled `certificate_rejected`,
never “non-theorem”: reusing the wrong certificate says nothing about whether
another proof exists.

Targeted mutations exercise proof constructors, binder scope,
capture-avoiding equality substitution, induction motive and step, the
intuitionistic rejection of DNE, strict artifact decoding, the no-translation
profile boundary, and the ban on negative evidence. The authoritative Python
kernel and an independently implemented, exactly source-pinned Lean checker
must agree on every in-scope result. Native Rust and browser WASM shadows add
portable diagnostics; depth, wire, index, and checker-fuel exclusions are
recorded as explicit implementation-envelope results rather than semantic
disagreements.

Two fresh CPython workers replay the full 384-entry catalog from empty caches
and must produce byte-identical ordered rows and roots. The retained controller
also reruns kernel import-boundary, original-goal, and transactional-history
regressions. It binds the complete loaded implementation-source closure, the
reviewed Lean commit/source/toolchain/verifier identity, and the native/WASM
artifacts. It checks the repository again at the end, so a multi-hour run
cannot report the clean commit observed only at startup. Development flags may
produce diagnostics, but can never emit `validation_passed = true` or the word
`PASS`.

This is an H0 candidate-L0 semantic corpus, not H1's frozen experimental epoch.
H1 still owns lineage, dependency masks, benchmark partitions, and the rule
that later library growth cannot leak into the campaign. H0 proves that the
meaning and proof boundary can be reproduced before those experimental choices
are sealed.

The retained run from clean commit
`26c2503b36c6884bfbfa6dabd1494bbda49d8926` passed. Both 384-theorem cold
replays produced root
`fae19fad55c416ae7b695107390c1c733d6740fe63d10cf0efed127f5801b9d2`.
The 1,024 positives, 1,024 wrong-target pairs, and ten artifact mutations form
2,058 cross-language cases; Lean agreed on all of them. Rust classified 2,047
as portable and eleven outside its envelope. WASM classified 1,790 as portable
and 268 outside its stricter envelope. No portable implementation disagreed.
The three translation/negative-evidence boundary mutations and all nine
kernel/original-goal/transaction regressions also passed. H0.3 contributes
seven content-rooted action fixtures; pinned deterministic accepted and
rollback traces; exact adapter, configuration, request, call, response, and
certificate preimages for a Dispatch that freshly proves the original goal;
and an exact 110-test transcript. The 3,484,230-byte canonical report is
`artifacts/peano-hydra/h0-validation-v2.json`, SHA-256
`55c60502b2229f4420bd4557058842bebb582f491739e82a6dae06de5b803fdb`.
Its RSS, wall-time, and pytest-duration observations are not stable semantic
identities. The older v1 file is provisional H0.1/H0.2 evidence, not a
complete-H0 report.

### The first functional plumbing test

The repository now contains a provider-neutral bootstrap in
`training/peano_hydra/` and a runnable pilot:

```console
python3 scripts/eval_peano_hydra.py --include-trace
```

It uses the checked consecutive-product script
`forall n. exists x. n * (n + 1) = 2 * x`. Both lanes receive the same fixed,
state-independent symbolic candidates, `compact_arith` and
`compact_arith [IH_witness]`, and the same three-slot, depth-13, beam-1 search
budget. The control's third slot is an identified null head. The hybrid's third
slot supplies the script's ten structural actions only at their ten exact
canonical states.

The control exhausts at the root. The hybrid reproduces the 13-command route,
then a fresh retained-trace replay checks its 180-node certificate against the
original formula. A related mutated statement activates none of the recorded
macro states and remains `unknown`; that is transcript non-reuse, not a
non-theorem certificate. The current profile-v2/result-schema-bound
deterministic evidence is committed as
`artifacts/peano-hydra/teacher-oracle-pilot-v3.json`. Historical v1 remains
byte-pinned as explicitly pre-profile evidence, and v2 remains the immutable
profile-v1 regression.

This result is useful and deliberately modest. It proves that portfolio
quotas, exact-state gating, public tactics, proposal provenance, independent
replay, and the kernel compose. The structural route came from the answer, and
the contextual symbolic candidate was human-selected for this example. No
Qwen or Codex was called, so the pilot measures neither model capability nor a
hybrid advantage.

The report also marks every lane comparison-ineligible. At this bootstrap
stage the ledger retains extracted tactic lines but not raw decoder text,
token and latency measurements, or a campaign provider attestation, and the
critical-state allowlist is copied from the teacher route rather than detected
as a symbolic fixed point. Clean execution therefore means “the plumbing ran
as specified,” not “this row may enter a model comparison.”

## Build the strongest baseline first

The LLM should not receive credit for work that a good algorithm already does.
Before model training, Hydra freezes a symbolic portfolio containing as much
of the following as the fragment permits:

- canonical normalization and equality rewriting;
- arithmetic closure and bounded witness enumeration;
- focused intuitionistic or connection/tableau search;
- induction-candidate enumeration;
- deterministic theorem retrieval; and
- bounded, reconstructed Vampire hints.

Each component is measured alone and in portfolio. Development-only scheduling
chooses the strongest solved-versus-resource envelope. That frozen system is
$S$, the real baseline.

Then we add increasingly expensive learned components:

\[
S \subset S+\mathrm{BM25} \subset S+R \subset S+C
  \subset S+P \subset S+P+V,
\]

where $R$ is learned retrieval, $C$ a cheap clause/state ranker, $P$ the macro
policy, and $V$ a value model for best-first or PUCT search. Shuffled scores,
random valid actions, no-retrieval, no-value, no-symbolic, and LLM-only runs
show which component caused an improvement. If cheap retrieval or ranking
captures the gain, increasing the transformer is the wrong engineering move.

## Training data must end in QED

A positive proof-policy row is admissible only when it lies on a complete trajectory
whose final certificate checks against the original goal. Partial progress,
an attractive lemma, a solver assertion, and a syntactically valid tactic are
useful diagnostic or negative data but not positive proof labels.

Prose data obeys a different authority. A positive formalization row requires
the human-approved source-to-statement pair and explicit training consent; it
does not require that the author already has a proof. Conversely, a kernel QED
shows derivability but cannot certify that a generated formula faithfully
translated a sentence. Keeping the corpora and adapter roles separate lets us
measure both tasks instead of hiding one inside the other.

The first curriculum target is deliberately large and balanced: at least
100,000 unique macro transitions from at least 20,000 checked QED roots, every
macro head represented, and at least 2,000 examples for each open-ended
frontier choice. Clean generation must be byte-for-byte reproducible. The
tokenizer must reject examples that do not fit; silent truncation changes the
task and can remove the answer.

The initial student stays modest—roughly 1.7–3 billion Qwen parameters, with a
hard initial family ceiling below 10 billion—until the data and search design
pass causal gates. Separate LoRA adapters or tagged tasks cover formalization,
retrieval, macro policy, value/ranking, critique, and checked-artifact
explanation drafting. Supervised proof training
must beat the identical pretrained model on DEV, solve a meaningful number of
registered frontier cases, and have a positive paired confidence bound.
Formalization has its own human semantic-accuracy and ambiguity-abstention
metrics. Value search and expert iteration have their own incremental gates.
Only newly discovered, independently checked QEDs enter proof expert
iteration.

## A faster kernel needs two proofs, not one

The readable Python checker remains the final QED authority today. The safe
Rust implementation already gives Hydra useful native and browser-WASM speed:
it can reject malformed candidates, filter rollouts, and cheaply test solver
reconstructions before the Python replay. Differential agreement across many
mutations is strong engineering evidence, but it is not the final theorem we
want.

There are two distinct Lean obligations:

\[
  \text{Lean checker accepts}
  \Longrightarrow
  \text{derivable}
  \Longrightarrow
  \text{true in the intended model},
\]

and

\[
  \text{exact committed Rust returns Accept}
  \Longrightarrow
  \text{Lean checker specification accepts}.
\]

The first proves the mathematical algorithm. The second is source refinement.
Writing the same-looking checker again in Lean establishes only the first;
finite tests cannot manufacture the second. Hydra therefore uses staged
K5–K11 gates: freeze a logic-carrying wire format and typed outcomes, measure,
harden Rust and resource accounting, prove the v3 specification, translate or
otherwise refine the exact safe-Rust accepted path, soak Rust and Python across
platforms, and only then review authority.

This also fixes an important error vocabulary. `InvalidCertificate`,
`MalformedInput`, `ResourceExhausted`, and `InternalError` are different
outcomes. Only `Accept` grants QED, but exhaustion says nothing about whether a
theorem exists. If exact Rust-source refinement fails, Rust remains an
excellent accelerator and Python or dual checking remains the authority. That
is a useful and honest engineering outcome.

## First H1 implementation: exact records before automation

The first H1 slice implements two deliberately narrow protocols. Authoring
schema v1 (semantic digest
`31a344bbc0b22cfacf5803c85d25a80a0234cf7387395283c5e1ab25ada80553`)
stores canonical documents, exact UTF-8 source units, alternative
formalizations, diagnostics, proof attempts, and draft or freshly checked
theorem proposals. It pins the existing defined-syntax registry rather than
inventing another notation layer. A generic model or solver can emit only an
explicitly untrusted diagnostic; kernel authority requires replay, and human
review/export authority requires an ordered source-reviewed event deposit.
Every event binds an actor, the single session owner, a sequence, its
predecessor, and a rolling prefix root. The production deposits are empty.

The review of this code produced a small but memorable example of why strict
serialization matters. In Python,

```python
False == 0  # True
True == 1   # True
```

so ordinary object equality is not exact JSON equality. An early epoch draft
could compare `false` in one root payload with `0` in another and call them
equal. The corrected validator compares canonical JSON bytes, type-checks
every version integer, and refuses to return a normalized object whose root or
preimage differs from the input commitment. The same version discipline now
applies to authoring records.

Library-epoch schema v1 (semantic digest
`f4695013ee4aeb660abf3a1e57a6334d86c990a8904c4435d94628694a2e875b`)
also distinguishes a living candidate from a frozen research epoch. Candidate
loading always rechecks current Git provenance and the complete 384-theorem
catalog. If relevant sources change after import, the service must restart;
new hashes cannot be paired with stale imported theorem objects. Evidence
reads are bounded and reject final symlinks, while packed path text is checked
without consulting the living repository.

That first protocol fixture is still not $L_0$. It contains the catalog,
semantic profile, and retained H0 report, but only certificate *hashes*. We did
not mutate that version to make the word “pack” retroactively mean something
stronger. Instead we introduced a subordinate replay-pack format whose claim
is smaller than an epoch freeze and can be tested directly.

## From certificate hashes to an offline replay pack

Replay-pack schema v1 has semantic digest
`d60b07fe68aa4ba023c9bb873e2df4190752f70252caca21da7e76dcd393f02d`.
Its candidate directory contains a canonical copy of that schema, the source
catalog, the constructive semantic profile, one manifest, and 384 raw
`peano-lab-v2` certificate artifacts. The certificate payload is 80,088,767
bytes; the largest artifact is 3,608,301 bytes. The ordered theorem replay root
is `88e39a886949e2ef31220397e529871bc907f9cd9311c27dc97710d12ef1e3ba`,
while the stronger manifest root—which also binds schema, catalog, profile,
resource declarations, paths, and verifier sources—is
`fe6718465fbb5e89154ccfce5c511b51ee296b21568d1759a00dda8a21f8a25d`.

The distinction between the builder and verifier is part of the lesson. The
builder is allowed to see authored scripts, replay the living catalog, measure
Python object sharing, and serialize certificates. The verifier is not. It is
loaded directly from one source file, imports only the kernel and standard
library, and runs in a new Python process with
`-I -S -X pycache_prefix=<fresh-dir>`. The cache's repository subtree must not
exist when verification starts, bytecode writes are then disabled, and only
the exact Peano package root is appended after standard-library paths. A
meta-path guard makes imports of the theorem library, tactic engine, UI,
training package, Torch, and Transformers fail. The worker records that none
was loaded. Its executed package initializers, kernel modules, decoder,
verifier, and CLI are themselves hashed into the manifest, checked immediately
after import, and checked again after the last theorem.

The order of work is intentionally defensive. The worker first validates the
complete manifest—exact JSON types, theorem count and order, prior-only
dependencies, content-addressed relative paths, aggregate resource ceilings,
root preimages, source identities, and the exact directory listing—before it
opens a single certificate. Root and certificate enumeration stop after their
declared bounds. Every artifact is opened with no-follow and nonblocking flags,
then required by descriptor metadata to be a stable bounded regular file; a
FIFO therefore fails without hanging the worker. The decoder accepts only
exact tagged constructors, exact arities and child sorts, nonnegative exact
integers, one canonical byte spelling, and explicit byte/node/depth/integer
limits. Decoding is inert: even a syntactically valid false proof or DNE node
gains no authority.

For theorem $i$, the verifier parses the catalog's statement independently,
requires it to be closed, and compares it structurally with the decoded target.
It recomputes canonical formula and proof hashes, the readable canonical
statement, tree nodes, depth, and Cut count. Only then does it ask

```python
check((), proof, original_target)
```

in intuitionistic mode. An adversarial test uses a DNE certificate that the
separate classical checker really does accept, reroots every local commitment,
and confirms that this worker rejects it. Other tests reroot wrong proofs,
wrong targets, Boolean-for-integer aliases, oversized resources, malformed
paths, bad dependencies, source drift, stale bytecode, symlinks, FIFOs,
unbounded directory inputs, missing/extra files, and mutated bytes. Report
destinations are checked both before and after replay using lexical, resolved,
Unicode-normalized, case-folded components. Thus a report cannot replace the
manifest through an APFS case alias. The report itself is written by flush,
file `fsync`, and atomic replacement outside the pack. Failure never becomes a
partial successful report.

There is a subtle serialization lesson here too. `peano-lab-v2` expands a
Python proof DAG into a tree. Tree occurrences, maximum depth, Cuts, encoded
bytes, and kernel acceptance are therefore reconstructable from the pack.
Python object identities are not. The manifest labels distinct objects, unique
edges, and reused references as source-stage observations, verifies their DAG
invariants, and binds them to the source catalog without claiming to rediscover
sharing from the bytes. Likewise, the historical Python `repr` hash is retained
as construction provenance but is not a portable theorem-authority condition.

The builder publishes the staging directory atomically only after that fresh
worker succeeds. The ordinary test suite repeats the complete 384-theorem
worker replay and requires its canonical report to be byte-identical to the
retained 828-byte report. The corrected replay-pack and bounded-decoder
selection passed 145 tests in 47.56 seconds. The report SHA-256 is
`35f5547978a4d58c5af30c33d253c92af494b94f6d6500a866a13f2fd1fa7f10`.

The wider release gates matter because the decoder is shipped in the browser
kernel package, not hidden in a research-only environment. The deterministic
full-suite shards covered every Peano test: 3,048 passed, 12 skipped, and two
environment controls were rerun successfully in isolation, yielding 3,050
passing non-skipped cases overall. Lambda Lab passed 360 tests plus 36
subtests. Browser build `2026-08-09b`, application `a-7fe525e910c8`, seals 150
Python sources in a 154-entry manifest and stages locally without a deployment
claim. The clean warning-as-error Book built all 46 sources, its integrity gate
found no broken or unsafe target, all 194 deep links and 287 commands replayed,
and the 490-note vault resolved all 4,981 links.

What did we earn? We may now say: **a replay-complete candidate-$L_0$ pack was
validated in an isolated fresh interpreter**. We may not say that production
$L_0$ is frozen. The schema itself enforces `status = candidate` and
`evaluation_eligible = false`. The dependency list is the current declared
publication list, not separately minimized readable and optimized vectors;
there is no leave-one-out receipt, complete definition/document bundle,
lineage mask, reviewed Git-state deposit, independent owner receipt, or sealed
benchmark. Those are the remaining H1.1 gates. The authoring side likewise
still needs the 200-unit adjudicated corpus and live browser/recovery behavior
before A0/H1.0 can close.

## Turning unknowns into a candidate epoch ledger

The replay pack answered one narrow question: can an isolated checker recover
and validate every certificate? An epoch freeze must answer a broader one:
what exactly do we know about every theorem, and which facts are still only
claims? H1.1a introduces a canonical metadata ledger to make that boundary
executable.

Its schema has semantic digest
`71995b59d4f5592a08a90dc354a91888f5f1f6f89ec4428be291aea19e76062c`
and exact document SHA-256
`9867378c8802501d2120ad4d94a86378815cf90b003eafc92b164685da61c956`.
The distinction matters: the first hash commits to the JSON value, while the
second also commits to two-space indentation and the final line feed. The
canonical candidate occupies 5,880,054 bytes and has root
`b2f397cec26d5f22bf0806da1f6e219d26bb5e319a503395150d9278efae8279`.
Its root preimage contains the complete body, and the validator reconstructs
the expected body from the exact retained inputs rather than accepting a
merely self-consistent rerooted replacement.

The ledger cannot be confused with an owner deposit. The schema fixes

```text
status = candidate
freeze_ready = false
evaluation_eligible = false
```

and contains no administrative escape hatch that changes those values. It
pins the replay manifest, independent verification report, copied catalog,
constructive profile, source commit `32803924…`, and source tree before it
emits the repository identity. In replay order, its 384 theorem rows bind
canonical and source statements, formula and proof hashes, readable scripts,
certificate paths and metrics, the logic profile, and source file, file hash,
declaration line, and declaration kind. The source audit found all 384
locators. The rows contain 1,038 declared publication edges.

That last adjective—*declared*—is doing real work. A readable proof can import
one set of lemmas while an optimizer constructs a smaller certificate from
another. The graph used for leakage masks must eventually contain the union of
both direct vectors. H1.1a therefore stores the declared publication vector
but leaves the readable vector, optimized vector, two leave-one-out receipts,
and publication union explicitly null. It sets `minimality_claim = false` and
labels the retained construction `submitted-not-best-known`. A2, not the
metadata builder, owns the comparison that may eventually justify
“best-known.”

### A documentation join is not a file count

The ledger gives each documentation source a per-theorem receipt with one of
three states: `present`, `stale`, or `missing`. Presence requires the record to
join the exact replay theorem; the mere existence of a similarly named file is
not enough.

The vault and theorem atlas cover all 384 rows, with zero missing and zero
stale receipts. The atlas links to immutable commit `32803924…`, not a moving
branch. Its four links per theorem—source, vault note, snapshot record, and
research record—give 1,536 links, all blob-audited at that commit. This fixes a
subtle documentation error: a beautiful current atlas whose permalink points
to an older partial snapshot is not evidence for the current theorem.

The proof explorers expose a different trap. Each corpus has 557 rows, but
only 240 public rows join this 384-theorem candidate. The other 317 names are
disjoint later or non-`L0` material. They remain useful provenance, but the
whole corpus must never be placed in this epoch's training, retrieval, or
evaluation context. Doing so would silently enlarge the frozen library through
documentation rather than theorem imports.

For 144 candidate theorems, the explicit explorer record and the defined-
notation explorer record are physically absent. Their definition receipt is
therefore absent too. The exact gap is 144 missing and zero stale in all three
classes. This yields 240 documentation-complete rows, where “complete” means
that the same theorem has all six joins: source locator, definition receipt,
atlas card, vault note, explicit explorer row, and defined explorer row. A
single aggregate count can now be traced back to exact row receipts rather
than inferred from unrelated corpus totals.

Every theorem also retains pending fields for human explanation review,
lineage assignment, A2's best-known comparison, readable and optimized direct
dependency evidence, and their publication union. Each of these gap counts is
384. This is not disappointing metadata. It is the point of the exercise: an
unknown represented as `null` plus a counted obligation is safer than a
plausible value promoted without evidence.

H1.1 therefore remains open. The next internal step is mechanical but
important: generate and audit the 144 missing explorer and definition records,
then run the A2 comparison/dependency work. Only after those repairs should the
project issue a source-state freeze request to an external independent owner.
That owner deposit still will not activate a benchmark; benchmark activation
is a later, separately authorized event.

The implementation gate has 53 focused adversarial tests. They cover exact
input pins, deterministic rebuilding, fully rerooted forgeries, claim
escalation, non-$L_0$ exclusion, source/report drift, hostile file types, and
the no-default-write CLI. The retained artifacts reproduce byte-for-byte under
`--check`. These tests validate the ledger protocol; they do not fill any of
the recorded gaps or substitute for external owner review.

## Why filtering a larger explorer is not isolation

On 2026-08-09, H1.1b1 addressed the 144-row selected-API gap discovered by the
metadata ledger. The obvious implementation was to extend or filter the
existing 557-row proof explorer. We rejected it after inspecting the records,
because top-level membership is not the whole information boundary.

The legacy public rows contain `dependents` arrays. Across those rows, 757 name
references point into the disjoint 317-row candidate corpus. A filter that
keeps only the 384 selected top-level names can therefore still disclose names
from outside the selection. Hashing the complete corpus is not a repair: if a
disjoint theorem later changes, the 384-theorem documentation root changes as
well. That would couple an alleged candidate-$L_0$ identity to material that is
not in candidate $L_0$.

The safe construction is deliberately less clever. Start with the retained
replay manifest, preserve its exact 384-row order, and construct every record
again. Resolve every declared dependency and tactic reference only in that
selected namespace. Do not copy global PA tags, `dependents`, closures, links,
scopes, foreign theorem names or bodies, or hashes of the larger explorers.
The result is a tagless selected API. The old 557-row explicit and defined
explorers, their tag map, and metadata v1 remain untouched as historical and
research-facing surfaces.

There was a second, quieter information leak at import time. Importing the
single-theorem compactor used to import the full quadratic-reciprocity stack.
That was unnecessary for selected compaction and loaded the wider theorem
corpus merely by asking for a utility function. The wider import is now lazy:
`compact_theorem_spec` can be imported without the 557-row stack, while
`defined_library_edition()` imports that stack only when the historical edition
is actually requested. This is not a security sandbox against arbitrary
Python; it is a precise dependency boundary for the deterministic builder.

### The five-document envelope

The candidate bundle lives at
`artifacts/peano-hydra/l0-documentation-candidate-v1/` and contains exactly
five files:

1. `schema.json`, the closed protocol and source-binding contract;
2. `explicit.json`, the replay-ordered explicit proof records;
3. `defined.json`, the conservative notation records and expansion receipts;
4. `isolation-receipt.json`, the selected-membership and graph check; and
5. `manifest.json`, the hash envelope over the first four.

The explicit side contains exactly 384 theorems, 1,038 internal declared
dependency edges, and 13,862 tactic lines using 20 tactic heads. Its parser
finds 3,989 theorem-reference occurrences: 1,035 declared edges are directly
mentioned by tactic text and three are implicit. These counts describe the
submitted readable scripts; they do not prove dependency minimality.

The defined side serializes 40 core definition records and pins the complete
43-entry parser registry: those 40 core definitions plus three adjacent ones.
The exact-AST compactor changes 321 theorem statements and 624 of the 950 local
propositions. It records 2,027 definition occurrences. Expanded statement
text occupies 224,948 characters and the defined rendering 29,098; expanded
local propositions occupy 148,105 characters and their defined rendering
25,733. The shorter rendering is useful for people and models, but the receipt
earns trust only by expanding back to the exact original AST.

Each retained file has both a semantic root where applicable and an exact
canonical artifact hash:

| File | Semantic identity/root | Artifact SHA-256 |
|---|---|---|
| `schema.json` | `30236aaaecc41104e7e193476f59a8b764d56fe86c63ca04c1561ad38645832d` | `a442e89ac312302dcee777b5741ca7f2d67e10f6ebcc996b8096fc6061c28a9c` |
| `explicit.json` | `b7942fa5a866ff7cd8a38f30c93787ec0abd2948e69710651e4d3578e64377da` | `f1c9f364db0cb7ae7f4c7fe065b1ef48d5522fc49711667479ec3dc4db723936` |
| `defined.json` | `897fd5e4bedb44b63853e428ff5bc2e2c273e30a0c239450e0ec8f93d73fc61f` | `164b34dd0cad555baf2164ee3da114fb60a447bd667112481e7225097dd17cea` |
| `isolation-receipt.json` | `64bdc2c52bcaf88d26382bbe514be4a442cc876b8df2a353c272587e1516d919` | `8c8a6882d0d5a82552942fc0c3efe5a900244a9cad02c32b24cabe3d86a0eee6` |
| `manifest.json` | `8f7ef8fcca69bc6f5f8b39c220293b8414a65fd81576c584f78e59da104d46a4` | `5ded97c27b859cc4725362bc76aba89fac06c5f11843b50529b78050b19348bf` |

The schema identity in the first row is its semantic digest. The isolation
receipt checks exact order and membership, equality of the explicit and
defined name sequences, internal dependency closure, absence of duplicate or
foreign names, and absence of fields such as tags and `dependents`. These
negative checks are central: a document can have all 384 desired rows and
still be contaminated by one extra reference.

The focused implementation file passed 36 tests in 126.87 seconds. After the
final roots were pinned, the seven targeted retained-artifact tests passed
with 36 deselected in 7.10 seconds. Final acceptance then passed all 43 focused
tests in 115.64 seconds and 23 compatibility tests in 18.19 seconds. This is
implementation evidence, not a claim about epoch authority.

H1.1b1 creates selected API records, not deployed pages and not a frozen
epoch. It grants no human-review, owner, source-state, minimality, readable or
optimized dependency, best-known, publication-union, A2, training, retrieval,
or evaluation claim. Metadata v1 truthfully remains the historical
240-complete ledger. H1.1b2 will introduce metadata v2 that binds the isolated
bundle and reports selected API coverage separately from deployed-page
coverage; H1.1 itself remains open.

### A successor ledger, not a rewritten past

H1.1b2 now performs that binding. The tempting implementation was to rerun the
old metadata builder and let its coverage number change from 240 to 384. That
would make a supposedly historical receipt depend on today's generated pages
and would silently change the meaning of a sealed hash. Instead, metadata v1
remains byte-for-byte immutable. Metadata v2 names it as one exact predecessor
and adds a second, exact documentation source: the isolated H1.1b1 bundle.

This gives a useful example of evidence monotonicity. New evidence may add a
successor claim, but it may not rewrite what an earlier receipt observed. The
new ledger keeps the predecessor's theorem semantics, proof receipts, source
locators, atlas and vault receipts, unresolved review fields, and historical
page status. For each replay-ordered theorem it then adds:

- the predecessor row hash;
- the selected explicit-API record hash;
- the selected defined-API record hash;
- a typed preimage and hash for the theorem's definition uses; and
- a new theorem-row hash included in an ordered 384-row root.

The join checks far more than the theorem name. Statement source, canonical
formula, script, source location, layer, explanation, and declared dependency
vector must all agree. Definition occurrences must resolve from stable IDs to
the right names in canonical registry order; their total remains exactly
2,027. A completely rerooted but semantically mismatched predecessor or bundle
is rejected because validation reconstructs the expected document from the
fixed artifacts.

The resulting numbers intentionally answer two different questions. There are
384 complete selected API rows. There are still only 240 rows for which both
historical deployed-page receipts are present, leaving 144 pending explicit
pages and 144 pending defined pages. “We can address a machine-readable record”
is not the same statement as “we deployed and reviewed its teaching page.”

Schema v2 has semantic digest
`498dde0a3b4f762197d8c371609dfac2eabf7edcfc37a6d3c5cdf6ca21efb38a`
and artifact SHA-256
`27af1e5c1ee0e73cb012db3d8b94cb9a6e1be48d08e8158ad48b8edac399973e`.
The 3,732,032-byte ledger has artifact SHA-256
`dc6a59ce08397eba698651f6ed4faac0533dec55c13d5a8ca49d863d19d7b72d`,
root `e0c1d3683e111d7f2883cebbc423694159e82d95471d9375866a81ec596dfb9e`,
and theorem-record root
`22330158f52f049ec920992f51f96a0ab0e9939c3eeb893f533616c17b48e98a`.
The 1,891-byte readiness artifact has SHA-256
`f257646d1ba5b51835c8b1718538b4b21c89ea402ba073a9630842708db0206b`
and binds the exact ledger bytes in addition to the semantic root.

Even the output path is treated as evidence. The loader rejects symlinked
ancestor components, and the CLI's create-if-absent publication cannot
overwrite a file introduced in the inspection-to-publication race window. A
test deliberately creates such a competitor: the tool preserves its inode and
bytes, rolls back its own sibling, and leaves no staging files.

Nothing here freezes $L_0$. The ledger remains intuitionistic, candidate-only,
and ineligible for training, retrieval, and evaluation. All 384 theorems still
lack human review, lineage, verified readable and optimized dependency vectors,
a publication union, and best-known comparison. Those are the next pieces of
the campaign, not details that documentation completeness can waive. A2 and
the 144-row deployed-page repair can proceed in parallel, but both must finish
before an owner freeze.

The final focused suite passed 46 tests in 101.07 seconds. It includes exact
retained byte and root pins, cross-join and fully rerooted forgeries, strict
loader and import isolation, the public-readiness reconstruction boundary, the
private one-build CLI contract, and both ordinary and racing publication
failures. An independent post-optimization threat review found no blocker.

### A generated page source is not yet a deployment

H1.1b3 adds the missing presentation *source* without changing the historical
explorer. A new tagless static tree at
`book/_static/pa-selected-library/` is reconstructed only from the exact
five-file H1.1b1 bundle. It contains an explicit proof page and a defined-
notation page for each of the 384 replay theorems, 40 definition pages, and one
index: 809 HTML pages among 813 exact files. There are no tags, aliases,
client-side scripts, or references to the 317 disjoint legacy candidates.

This distinction matters:

- `generated = true` means the repository retains and can deterministically
  reconstruct all selected static files;
- `deployed = false` means no external host receipt or public availability
  observation has been made; and
- `reviewed = false` remains true in substance: generated prose and pages do
  not grant human, owner, freeze, retrieval, training, or evaluation authority.

The API keeps replay order and binds 1,038 dependency edges, 13,862 tactic
lines, 755 theorem-definition relationships, 2,027 definition occurrences,
and 58 conceptual definition edges. The manifest binds the other 812 files.
All local links and fragments are checked, the stylesheet is scoped below
`body.pa-selected-library`, and every page carries a candidate banner.

The schema semantic/artifact hashes are
`eefb4b1154581f248696de3f81bd90296398e5353c6a42d0d01f35b3ccdb2abb` /
`8cdf0e947ce7156109b7591c99ed28d8ee1f938edd3cddfb414d48d7efacdafd`.
The API artifact/root hashes are
`a7a4be8ba895b9e69955e82bda5bbfe7418eeda47632a59899e6ba0896acaaf0` /
`2efbb00a763f120e5cee6271f3d64838b3a54e04e73a4c78c738f4d50f0b83b1`;
the manifest artifact/root hashes are
`751c3eefc99e5b30d612049fd99a0d890cd696b3fda0f426ca64d835c5fe2e6f` /
`94b38f4914853c87315f0bc94d33347164d4cb7c01cd81568b1c4f47cb1b1563`.
The external readiness artifact/root hashes are
`69b11b858348e3dda9a007b495c7198634822623d45314f6f82f551141bc9357` /
`8f7bf0fc18917b92d02d862e13507d28f1bf7d2842fcd93427d3a2879a193b1f`.

The page core passed 11 focused tests in 74.53 seconds. The WMI runner now
reconstructs and compares it before building the Book, then the integrity gate
audits the copied 813-file tree separately from the legacy explorer. Check the
retained source without writing:

```console
python3 scripts/build_peano_hydra_library_pages.py \
  --output-dir book/_static/pa-selected-library \
  --report artifacts/peano-hydra/library-page-deployment-candidate-v1-readiness.json \
  --check
```

Nothing in this step changes metadata-v2's historical 240 deployed page pairs
or its two 144-row gaps. A host receipt and an additive metadata successor are
required before those numbers can change. The integration harness passed 11
tests, 17 focused Book tests passed, and the warning-as-error Book build plus
its 3,133-page integrity scan completed with no broken targets, fragments,
escapes, remote runtime assets, or unsafe active links.

## Auditing what one tactic recipe actually needs

The first A2 slice asks a deliberately narrower question than “what are the
minimal dependencies of this theorem?” It asks:

> If we leave the tactic script unchanged and remove one imported theorem,
> does that exact script still construct a certificate accepted by the kernel?

That wording is the key to interpreting the result. Suppose a theorem has
target $T$ and declared direct dependencies $D_1,\ldots,D_k$. The body checker
does not trust or replay those named theorems. It temporarily turns them into
ordinary assumptions and checks the curried proposition

$$
D_1 \to D_2 \to \cdots \to D_k \to T.
$$

The generated `intro` prelude names those assumptions exactly as the retained
script expects. The authored tactic lines then run unchanged. Success is not a
tactic-layer opinion: the compiler returns the real formula and proof objects,
and the independent Peano Lab kernel checks the certificate from the empty
context against the complete curried target. This is useful positive evidence,
but it is intentionally non-admitting. Named dependencies have not yet been
resolved into closed certificates for $T$.

### Why the audit repeats to a fixed point

The algorithm starts from the declared vector and visits it backwards. A
kernel-accepted omission is kept immediately. After a complete pass, it starts
again with the shorter vector. It stops only when a complete pass accepts
nothing:

```text
working := declared dependencies
repeat
    removed := false
    for dependency in reverse(copy(working))
        candidate := working without dependency
        if kernel accepts compile(exact script, candidate)
            working := candidate
            removed := true
until one complete pass has removed nothing
```

Repeating matters because removing an assumption changes the proof context in
which later commands run. Fixing reverse declaration order makes the result
reproducible; it does not make it order-independent or globally optimal. The
terminal pass provides a leave-one-out observation for every dependency still
present in this particular fixed point.

Errors are evidence only when their meaning is controlled. A normal tactic or
incomplete-proof rejection says that this exact recipe did not survive that
omission. It does **not** say that no proof exists without the dependency. A
timeout, resource limit, malformed input, unexpected exception, or internal
failure is `unknown`; it aborts the entire document and can never masquerade
as a necessary edge. The compiler preserves finalization-limit status before
the user-facing `checked_final` path can turn it into a generic error.

### What happened on the 384-theorem library

Two complete builds over the selected replay pack were byte-identical. Starting
from 1,038 declared edges, the audit made 1,060 omission observations:

| outcome | count | meaning |
| --- | ---: | --- |
| kernel accepted | 3 | the exact script checked with this assumption removed |
| exact recipe rejected | 1,057 | this exact script failed; no necessity claim |
| unknown | 0 | any nonzero value would have blocked the artifact |

The three candidate reductions are:

| theorem | candidate omission |
| --- | --- |
| `odd_add_odd` | `add_succ_left` |
| `finite_bounded_injective_surjective` | `beta_at_unique` |
| `beta_product_swap_last_invariant` | `le_refl` |

Thus the diagnostic candidate vector has 1,035 edges. The public library still
has 1,038. Each affected A2.1 row says
`requires_certificate_rebuild = true`, because its retained closed certificate
was constructed under the old vector. That field remains immutable historical
evidence. The A2.2 successor described below now supplies and checks all three
closed rebuilds without rewriting A2.1 or proposing a graph change.

The readable and submitted-construction receipts have different hash domains,
so later pipelines cannot silently substitute one role for the other. In A2.1,
however, both observe the same retained `TheoremSpec` tactic recipe. No
optimizer program, comparison set, or Pareto receipt exists yet. It would be
incorrect to call the result an optimized proof, a best-known construction, a
minimal dependency vector, or a publication union.

The schema's semantic/artifact SHA-256s are
`54d6b5128067b1f93d8f7393e0730d7da3a4ac838a0b55b6b6fe0ce92a0d4bc4` /
`ee6eb4daf48fbf320e79a54065befed758ff33c5251ec4a2c18b8093c349c0ff`.
The retained sidecar occupies 4,188,048 bytes. Its artifact SHA-256 is
`4b867bb1ce0161e6392f29d9262e035929e5da86b224063546a2a42c17fd9040`,
its document root is
`12166de8fb0cc028c3b026deb939418a19f001ff8342acab479d433e15d3a83e`,
and its replay-ordered theorem-record root is
`8ae5553e79b15c4e83a76e1eab92cb0983539fa913dfe2bec29d0fb17fb7d784`.
All authority and eligibility flags are false, and the existing replay pack,
metadata ledgers, certificates, generated pages, and graph are unchanged.

The build command writes nothing unless an output is explicit. The retained
artifact can be reconstructed and compared read-only with:

```console
python3 scripts/build_peano_hydra_library_dependency_audit.py \
  --check \
  --output artifacts/peano-hydra/l0-dependency-audit-candidate-v1.json
```

Twenty-six focused tests cover the small fixed-point fixtures, independent
kernel rejection, structured resource and internal failures, strict canonical
JSON, fixed source and import provenance, hash-binding mutations, no-follow
loading, create-only atomic publication, and the exact retained pins. This
closes a useful A2 diagnostic subgate. It does not close A2, H1.1, or any
training, retrieval, evaluation, publication, or freeze gate.

## Closing the three reduced constructions

A2.1 proved three shorter *curried carriers*. It did not yet prove the three
original theorems from no assumptions. On 2026-08-09, A2.2 performed that
missing
step, without turning the experiment into a library edit.

For a candidate direct vector $D_1,\ldots,D_k$, the unchanged tactic recipe
first constructs and checks

$$
D_1 \to \cdots \to D_k \to T.
$$

The rebuild then obtains each $D_i$ from the exact retained replay pack and
checks that dependency certificate independently from the empty context. It
peels the generated implication introductions and inserts the checked
dependencies as a deterministic nested `Cut` spine. Finally, the independent
kernel checks the resulting closed proof from the empty context against the
original, uncurried $T$. A named library theorem never becomes a kernel axiom;
its certificate is proof data.

This distinction matters. “The body still compiles after removing a
hypothesis” and “the original theorem has a closed certificate using that
shorter direct Cut spine” are different propositions about different proof
objects. A2.2 now has the second kind of evidence for all three A2.1 rows:

| theorem | direct edges | artifact bytes | proof nodes | Cuts |
| --- | ---: | ---: | ---: | ---: |
| `odd_add_odd` | 4 → 3 | 14,977 → 13,640 | 302 → 274 | 7 → 6 |
| `finite_bounded_injective_surjective` | 15 → 14 | 1,913,452 → 1,870,657 | 42,463 → 41,341 | 1,266 → 1,235 |
| `beta_product_swap_last_invariant` | 6 → 5 | 391,540 → 386,189 | 7,439 → 7,413 | 205 → 203 |

Across these three candidate constructions, the direct vectors change from 25
to 22 edges. The canonical certificates are 49,483 bytes smaller and contain
1,176 fewer intrinsic proof-tree nodes and 34 fewer Cuts than their immediate
retained predecessors. This is a useful exact comparison, but it is only a
descriptive predecessor comparison. No optimizer program or comparison set
has yet been declared, so the smaller objects are not called optimized,
minimal, Pareto-optimal, or best-known. Counts based on Python object identity
or alias sharing are schedule- and assembly-dependent; the sidecar marks them
non-comparable and excludes them from the deltas.

Nor did the library suddenly become free of the omitted lemmas. The direct
Cut spine for `odd_add_odd` omits `add_succ_left`, but that name remains in its
retained transitive closure. The same is true of `beta_at_unique` for
`finite_bounded_injective_surjective` and `le_refl` for
`beta_product_swap_last_invariant`. “Not a direct edge in this construction”
is the exact claim; “not used transitively” would be false.

The candidate sidecar is
`artifacts/peano-hydra/l0-construction-rebuild-candidate-v1.json`. The schema's
semantic/artifact SHA-256s are
`a189ad140f5e7093f11a2f433705d4dafb71d474672e822cf39e45dbeb1ca571` /
`d1fc09c035e28f96913cdadd63f17c853901fc8dcd2e17df3a094a919612bf9f`.
The exact 3,106,352-byte sidecar has artifact SHA-256
`6176c44a63f791bc27ddd550aa915db6e78c8fbf9f9f0918299f1b3f639fc182`,
document root
`91ecc6b4bb22f4b46cdfa3fcdd2401dce47d8fef38c15101d221c207fd7793b0`,
and replay-ordered theorem-record root
`42d718621f91b52bf55a7909751eab695fefd28da2989863de50470d14397ef5`.
It can be rebuilt and compared without overwriting it:

```console
python3 scripts/build_peano_hydra_library_construction_rebuild.py \
  --check \
  --output artifacts/peano-hydra/l0-construction-rebuild-candidate-v1.json
```

The focused adversarial gate covers fresh empty-context checking, exact pinned
inputs, deterministic rebuilding, certificate and metadata mutations,
rerooted forgeries, path safety, the explicit direct Cut spine, and the
create-only command-line boundary. The admitted `TheoremSpec` records,
retained certificates, replay pack, metadata ledgers, catalog, generated
pages, and 1,038-edge public graph remain unchanged.

That focused suite passed 23 tests in 44.12 seconds, and the exact retained
CLI `--check` passed.

This checks only the A2.2 rebuild box. Every authority, minimality,
optimized-best-known, review, publication, freeze, training, retrieval, and
evaluation flag is false. A2 still needs a declared optimizer, comparison set
and Pareto evidence, separately audited readable and optimized vectors, and a
verified ordered publication union.

### Freezing the experiment before running it

A proof optimizer is easy to overstate. If we search first and describe the
search space afterward, “best” may merely mean “the candidate we happened to
notice.” A2.3a therefore freezes a deliberately small experiment before it
creates any result.

The pilot names three theorem roots: `odd_add_odd`,
`finite_bounded_injective_surjective`, and
`beta_product_swap_last_invariant`. For each root it will compare exactly
three constructions:

1. the exact retained replay certificate;
2. the exact shorter direct-Cut certificate from A2.2; and
3. a new closure-only certificate assembled by the existing layered replay
   compiler.

The third construction is worth separating from tactic search. We start with
already checked closed proofs, verify the declared outer Cut spine, peel that
spine to recover a modular proof body, reintroduce its assumptions, and check
the curried body. The existing compiler then packages only the reachable
dependency closure. It does not rerun the theorem's tactic script, and it is
not a newly invented factorer.

Each finished certificate will be checked from the empty context against the
original theorem. The comparison will use only four reproducible quantities:
serialized artifact bytes, proof-tree nodes, proof depth, and Cut nodes. One
candidate dominates another if it is no worse on all four and strictly better
on at least one. Every nondominated candidate will remain visible. A stable
display representative will be chosen by

```text
(proof_nodes, proof_depth, cut_nodes, artifact_bytes,
 candidate_kind_order, artifact_sha256, candidate_id)
```

That last choice is a user-interface convention within this exact pilot, not
a mathematical optimality theorem. Object-alias counts, wall time, and memory
are excluded because they do not describe the transported proof artifact in
the same stable way.

There is a second subtlety. A layered Cut tree can package an entire reachable
closure without telling us which dependencies deserve to be direct edges.
The protocol therefore records the direct vector and transitive closure as
different surfaces. Selecting a compact layered certificate cannot silently
certify an optimized dependency vector; a domain-separated audit must still do
that work.

The source protocol is now frozen. Its schema semantic/artifact SHA-256 pair
is
`07e5842c221fe84337e163ce5c858ab03dfbbc93d1477f5661edfdd6f8ba3978` /
`006d38ef781fc022b7b8929be35058038df02a0eee91eb2213128598c66a59ae`.
The program, no-default-write CLI, and adversarial-test source SHA-256s are
`7ac7d784c3660c1c9b839c906e50e2a88dced6af96ded00b900165e25ec12eee`,
`3acbd3ec0f190699d484ef0c800e4919c7cc8404fbbd50ba6daf90a5deb5d6ee`,
and
`d5ae3e830573c7a561462f5e0e91ef99bff42f6533986106cc65fc34f0e35dc9`.
The focused protocol gate passed 59 tests in 0.31 seconds.

What did **not** exist at source freeze matters just as much: no real local or
WMI pilot build, result sidecar, layered result certificate, metric vector,
nondominated set, representative, Pareto frontier, document root, or theorem-
record root. Running the no-argument CLI merely reports protocol readiness and
writes nothing:

```console
python3 scripts/build_peano_hydra_library_optimizer_comparison_pilot.py
```

A retained build needs an external canonical producer-source state. It is
byte-bound but deliberately carries `git_verified=false`; a separate receipt
must verify the commit, tree, ancestry, and clean submission. The execution
described below preserves this ordering. Its result still does not complete an
independent optimized-vector audit, so “best-known,” publication, A2,
authority, review, freeze, training, retrieval, and evaluation remain false.

### A2.3a external execution infrastructure (no submission/result)

The frozen question now has a deliberately narrow way to run elsewhere. The
first program observes a clean committed source tree without importing the
optimizer. It emits the exact eight-field producer state expected by the
protocol, still marked `git_verified=false`, and a separate receipt for the
clean HEAD/tree, stage-zero blobs, live bytes, and Git tool. Separating the two
documents prevents an operational Git check from turning into mathematical
authority.

The answer is then checked by a different program in a fresh interpreter. That
verifier may import the standard library and pinned Peano kernel, but not the
producer, layered compiler, tactic engine, library, or replay-pack code. It
canonicalizes and checks all nine certificates from the empty context, then
recomputes the metrics, three nondominated sets, representatives, aggregate
counts, and roots. Thus agreement with the producer is evidence about this
fixed comparison, not a declaration that any dependency vector is optimal or
ready to publish.

The WMI worker makes nondeterminism and failure classification explicit. Two
fresh producers run with hash seeds 0 and 1 and must emit identical bytes; a
third process verifies those bytes with seed 2. The fixed request is one
`cpu_idle` CPU, 4 GiB, and 15 minutes under x86-64 CPython 3.12.12. Timeout,
OOM, preemption, missing evidence, or an untyped process failure means
`unknown`, not “optimizer failed.” The execution receipt is written last, and
a later collector binds it to one terminal Slurm row and the exact bounded
logs.

There is an important operational footnote. The submitter defaults to
`--test-only`, but that mode still creates or verifies the immutable
content-addressed snapshot on WMI before asking `sbatch --test-only` to check
the request. It creates no Slurm job. A real job needs both `--submit` and the
literal confirmation `PEANO-HYDRA-A23A-WMI-PILOT`. This tranche claims no
successful test-only outcome, real submission, or cluster job. Both wrappers
accept an optional syntax-validated `WMI_SSH_JUMP`, passed only as SSH `-J`
beside the validated target; an observed target/jump route is an operational
transport mechanism, not execution evidence.

The source-state generator/test identities are
`4812314f101ac302f712a87641f37ffb627e4cbaa916605e6c7e1e0b0ed90a26` /
`acdde9367e5fdea7fdfc4e6cef1c3ee4c2bddeb4b9fbe1e025581eb3c7fe8860`.
The verifier module/CLI/test identities are
`683ee529ed4be0e93504846340eeddf47eae1cb3f84967168a971d422ade1dbe` /
`1250d0202236a6aa727509c5270767fe91e48cf34e5a6fd9c13ac1a59722f014` /
`08f838332ffca805c934a6c44cf59148e9f0f9168c784f1b7a9c8b8cf353239a`.
The WMI runner/sbatch/submit/collect/test identities are
`46c9bea044640ccf057a5113eff2f3c6161206c55521b8fcd7c48e7342ff8632` /
`1f09c62532a0c9f10fc11bb00a420e1eea1967dc70686ad503c1e5207b75538c` /
`ce94c5e5e77ff83998f147fb77d3e698eae41366774867238b16990accc7fbee` /
`ddafef2eab12d18ba766325b5dbb077a0075cc8589bc553a72bd60aff910cb0e` /
`cc75ad16a90c289d07851f7d59cf79f2e960acd86d9257f8155a1cabc532a755`.
The WMI protocol file passed 18 tests in 0.72 seconds. The three focused suites
passed 52 tests in 8.45 seconds (10 + 24 + 18). The earlier independent threat
audit reported no blocker before the final route refreeze.

This tranche was runnable infrastructure, not yet a run. The successor below
records the later execution separately so infrastructure tests do not masquerade
as optimizer observations.

### The fixed A2.3a pilot ran, and its boundary stayed small

WMI job `219765` ran the frozen comparison from clean commit
`0f6ca3a0cf5998212e3a0ad508ba77e88a15a17d`, tree
`9051b43aa3f7f75d37ce8d410b9c7a81ba472d94`, and snapshot
`707398a7494482dbcc38c8438582688e01f88b395ab61e64be4a7d6396178824`.
The two producer seeds emitted the same 848,463 bytes. The separate seed-2
verifier accepted all nine proof artifacts from the empty context and rebuilt
the comparison. Terminal collection records `COMPLETED`, exit `0:0`, 60
elapsed seconds, and `completed-and-independently-verified`.

Here are the observed vectors, written as
`artifact bytes / proof nodes / proof depth / Cuts`:

| Theorem | retained replay | A2.2 direct rebuild | layered closure |
| --- | ---: | ---: | ---: |
| `odd_add_odd` | `14,977 / 302 / 32 / 7` | `13,640 / 274 / 31 / 6` | `12,709 / 269 / 37 / 3` |
| `finite_bounded_injective_surjective` | `1,913,452 / 42,463 / 89 / 1,266` | `1,870,657 / 41,341 / 89 / 1,235` | `297,637 / 8,355 / 95 / 20` |
| `beta_product_swap_last_invariant` | `391,540 / 7,439 / 67 / 205` | `386,189 / 7,413 / 67 / 203` | `118,018 / 2,011 / 79 / 9` |

All three frontiers are exactly
`[a2.2-direct-cut-rebuild, layered-closure]`. The old retained artifact is
dominated inside this fixed set. The layered construction has fewer bytes,
nodes, and Cuts, but it is deeper; therefore the direct rebuild remains on the
frontier. The preregistered node-first tie-break chooses `layered-closure` as
the display representative in all three cases. “Representative” here means a
stable display choice among three named candidates, not “best proof we know.”

The candidate is retained at SHA-256/root/theorem-record root
`3e989784d371c3383fa5e428df8755d1e94d4c3386328746751981a8a77cab5b` /
`90a3d97a466dc7b1c9e6032b1b56b8ede3fcece8d56a4b39f2d4e5f34dbeb770` /
`4cfcbe22312ff2b92022189e65d3742bc096ba989dacaa82b2054e84282928e5`.
The independent verification is retained at
`6a7942147b8227c61a0de8a8f533653a6d727efe7843a52f3b524f1c47ac084a` /
`e21290f654c1a30e0bdf79e796a8ca1da6ad3aa6a1cb1d8ba34d3d376de052dc` /
`18f882717346477304285c9336d7b769ccf95cd1b58c32b65d335f3e8caa4188`.
Execution and collection receipt artifact/root pairs are
`779a971237f9ac5efe3a86dca5b5c4d74a6da56ab154b91e106f7fd1dac63a34` /
`7a597563c173cd0cb3d57ff42cd566a8531756e84bf8ba907e7c79ec7295dc0e`
and
`25e616fc9225ab59db6a089e8a53ed2d44915a54b42f073bcaaa020fc2ff609a` /
`52339b926ea8b9650787a3db138185e21144f6cdf83596d224ccc6b23435daf2`.
A controlled local CPython 3.12 replay of the retained verifier reproduced its
18,327 bytes and accepted 9/9 artifacts. It did not rerun the optimizer
locally.

The retention boundary is intentionally literal: 19 files, consisting of the
candidate, independent verification, and 17 operational source, deposit,
submission, execution, collection, scheduler, and log files. The original
277,025,280-byte transfer archive was deleted after collection and was not
independently rehashed. Its snapshot hash is bound transitively through the
receipts; that is weaker than retaining and rehashing the archive itself. The
`sacct` row is an unauthenticated scheduler observation. Its `MaxRSS` field is
empty, so the run supplies no measured peak memory or memory ceiling.
Scheduler and verifier stderr are empty; the two producer stderr files retain
the same harmless pre-existing Python 3.12 `SyntaxWarning`s for `\/`. The
focused retained-result gate passed four tests in 3.40 seconds; its 33,374-byte
source SHA-256 is
`28b251f9ab75bea0012949390923b039e267d4721c09bd9ff9b6a08de89cc602`.

The result documents still say `producer_git_verified=false`; the separate
clean-Git receipt proves only the operational source boundary. No readable or
optimized direct dependency vector has yet passed its independent publication
audit. Every minimality, global-best/`optimized_best_known`, vector-audit and
completeness, publication and publication-union, review, lineage, freeze, A2,
proof/admission/publication authority, training, retrieval, and evaluation
flag therefore stays false. Nothing entered the admitted library, 1,038-edge
graph, catalog, generated page source, or deployed site.

## What “matched compute” means

We compare three frozen systems on the same sealed targets:

- $S$: strongest purely symbolic portfolio;
- $S+R$: strongest non-generative learned system; and
- $H$: full Hydra with the generative model at critical frontiers.

Each is measured at 1, 10, 60, and 300 seconds per problem on the same hardware
class. Wall time alone can hide very different work, so the report also gives
CPU instructions or symbolic activations where possible, GPU/CPU energy, peak
memory, and cost. Training cost is reported separately and as an amortized
break-even curve.

The main curve is independently checked solved fraction versus resource. We
also report time-to-proof, PAR-2, proof size, invalid actions, calls, and the
asymmetric sets

\[
  H\setminus(S\cup(S+R))
  \quad\text{and}\quad
  (S\cup(S+R))\setminus H.
\]

The first shows genuinely hybrid-only solves; the second prevents an average
score from hiding regressions.

The preregistered headline gate is intentionally hard. At two adjacent time
budgets, Hydra must beat the better baseline by at least three percentage
points, the lower paired stratified 95% interval must remain above zero, and a
corrected exact paired test must reject equality. Every counted proof must
replay, with no negative-decision regression. Otherwise the result is simply:

> No demonstrated LLM advantage under these budgets.

That is a useful result. We do not rescue a miss by reopening the benchmark,
tuning after inspection, changing to `pass@k`, or asking the teacher.

## The seven gates

The campaign proceeds in order:

| Gate | Question | Required evidence |
|---|---|---|
| H0 | Is the logic and fragment exact? | conformance, reference agreement, mutation rejection |
| H1 | Are authoring and evaluation isolated? | strict schemas, frozen $L_0$, sealed lineage split, symbolic and teacher DEV probes |
| H2 | Is the non-LLM baseline strong? | native/Vampire proof-producing portfolio and replayed resource curves |
| H3 | Are the curricula legitimate? | adjudicated prose pairs, complete QED roots, deterministic builds, zero leakage |
| H4 | Which learned component helps? | model ladder and matched causal ablations |
| H5 | Does the LLM win once, fairly? | one-shot sealed matched-compute comparison |
| H6 | Can another group reproduce it? | source, environments, raw traces, certificates, tables, review |

H0–H4 should take roughly eight to ten weeks for a serious prototype. The full
campaign, including benchmark authorship, independent evaluation, replication,
and release, is more realistically four to six months. GPU training is not the
first step; it is one guarded step after semantics, leakage control, and a
strong baseline exist.

The A0–A6 product gates proceed in parallel from authoring schemas through the
sentence workbench, artifact compiler, Vampire/Qwen help, asynchronous live
assistant, and reviewed library admission. The K5–K11 gates independently
govern any future Rust-authority change. Finishing one track never waives the
acceptance criteria of another.

## What would be novel

The novelty would not be “an LLM printed a Peano proof.” The stronger result
would be a clean demonstration that sparse learned semantic decisions improve
a sound, proof-producing intuitionistic arithmetic prover over strong symbolic
and cheap learned baselines under equal resources. A negative result with the
same controls would also teach us where language models are unnecessary.

That is why the Hydra metaphor fits. The system has many exploratory heads,
but every path returns to one small kernel. More heads may find more routes;
none gets a vote on truth.

## Further reading

- [Peano Lab binding design](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/PEANO_LAB_DESIGN.md)
- [Peano Hydra binding design](https://github.com/nasqret/vietnam2026/blob/peano-lab/docs/PEANO_HYDRA_DESIGN.md)
- [Training a Peano policy](training-a-peano-policy.md)
- [AlphaGeometry](https://www.nature.com/articles/s41586-023-06747-5)
- [AlphaProof](https://www.nature.com/articles/s41586-025-09833-y)
- [Thor](https://proceedings.neurips.cc/paper_files/paper/2022/hash/377c25312668e48f2e531e2f2c422483-Abstract-Conference.html)
- [Efficient Neural Clause-Selection Reinforcement](https://arxiv.org/abs/2503.07792)
  (evaluated inside Vampire)
- [Intuitionistic Logic Theorem Proving library](https://www.iltp.de/)
