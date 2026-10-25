# Publishing experimental-engine proofs

`publish_showcase.py` accepts finalized `evaluate_advanced.py` live HTTP records. It never accepts reference audits, manual fixtures, running jobs, failed workers or open proofs as discoveries. Its default action is staging; `--publish` additionally appends to the local gallery. Existing artifact bytes and existing manifest entries are preserved. No model, symbolic helper or search runs during publication.

For an experimental record, the original request selection is carried into one fresh, isolated replay of the **complete original theorem and returned script**. The native source manifest, unchanged original kernel files, checked-library edition, reservation and target-bound capability must match. The recorded search code is bound to its finalized run; the current replay wrapper is separately hashed. Older P2 requests may omit later default-off planner/ranker/adviser fields, but no explicit selection can change.

Checked certificates are loaded by the fixed native resolver, checked eagerly, and admitted on each `use`. The complete fresh replay must match the original theorem, commands and certificate occurrence count. Distinct-object/depth measurements retain their explicit **original search certificate** scope; the publisher does not claim a second measurement of DAG sharing.

SymPy/cvc5/egg/E step credits require matching actual helper execution, input/context, source identities and per-command provenance. Requests, actual launches, cache hits, successful proof steps, checked imports and eager preload checks stay separate. A deterministic structured plan remains heuristic; its checked commands, plan hash and complete recorded context are bound individually. Generated or failed plans earn no winning-step credit.

Parent RSS supervision samples the one owned replay process and kills/reaps it if necessary. Its 2 GiB limit is a sampled safeguard, not an instantaneous guarantee. Each replay has at most 120 seconds; the CLI also has a finite total duration and never retries a failed replay.

Suggested first publication (at most three entries, all still require the fresh publisher replay):

| Live record | Suggested title and description | Actual original winning steps | Original objects / occurrences |
|---|---|---|---|
| `p8-http-01/000-sympy_variable_divisor-symbolic.json` | **A variable-factor witness.** For every natural number a, a itself witnesses divisibility of a²+a by a+1. SymPy suggested the native witness steps. | heuristic 1, SymPy 2; one SymPy launch | 1,834 / 4,740 |
| `p8-http-cvc5-02/000-cvc5_affine_context_witness-heuristic.json` | **A witness from an equation.** If a+a=b, a witnesses an existential equation w+w=b. cvc5 advice is reconstructed as native proof steps. | heuristic 3, cvc5 5; one cvc5 launch | 1,267 / 1,606 |
| Optional `p2-http-01/000-p2_addition_reuse-heuristic.json` | **Reusing a checked addition lemma.** Prove commutativity together with the right-zero identity, using one certified library import. | heuristic 6; one winning `use`, followed by its application | 186 / 257 |

These are small, exposed integration examples over the naturals, not unseen accuracy evidence or new mathematical results. The actual P9 HTTP successes so far used heuristic winning steps: they are not eligible for E/egg contribution labels merely because those advisers were selected or called. Read these paths relative to `output/hydra-implementation-2026-09-04/`.

Example **unexecuted** staging command, after supplying editorial-only curation and choosing a fresh output directory:

```sh
python3 -I -B hydra-playground/publish_showcase.py \
  --records \
    output/hydra-implementation-2026-09-04/p8-http-01/000-sympy_variable_divisor-symbolic.json \
    output/hydra-implementation-2026-09-04/p8-http-cvc5-02/000-cvc5_affine_context_witness-heuristic.json \
  --curation output/hydra-implementation-2026-09-04/showcase-curation-p10.json \
  --output output/hydra-implementation-2026-09-04/p10-showcase-stage-01 \
  --total-seconds 420
```

Curation schema remains `hydra-showcase-curation-v1`; only `title`, `display`, `description` and `tags` can be overridden. The rich attribution and experimental replay authority live in each hash-bound proof artifact, under `adviser_contributions`, `structured_plan_contributions`, `certificate_cost` and `independent_replay.experimental_authority`. Existing server/UI request and artifact schemas remain compatible; no new unbound catalogue badge fields were added.

The focused test suite uses constructed temporary records and mock children only. Actual live metadata inspection separately checked the three suggested records' source/adviser bindings without parsing formulas or replaying proofs. Neither activity constitutes fresh proof verification or publication.
