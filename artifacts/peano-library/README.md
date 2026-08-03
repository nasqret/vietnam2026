# Peano arithmetic-library artifacts

This directory is the deterministic, reviewable snapshot of Peano Lab's
checked theorem ladder. It does not extend the trusted kernel.

- `catalog-v1.json` records every closed statement, dependency, authored
  script, certificate hash, exact structural and identity-sharing metrics,
  and structural `Cut` count. The filename remains stable for downstream
  compatibility; its internal schema is `peano-library-snapshot-v3`.
- `dependency-graph.mmd` is the same directed acyclic graph in Mermaid form.
- `metrics.json` uses `peano-library-metrics-v3` and records aggregate proof,
  distinct-object, and `Cut` counts together with the dual live-`use`
  resource bounds.
- `mod5-source-validation-report.json` is immutable upstream provenance for
  the original cut-free modulo-five catalog. It is not regenerated or
  reinterpreted by this runtime snapshot.

Rebuild the generated files from the repository root:

```bash
python3 scripts/build_peano_library_snapshot.py
```

Verify that the committed snapshot is current:

```bash
python3 scripts/build_peano_library_snapshot.py --check
```

Generation replays every tactic script and submits its closed, self-contained
certificate to the independent kernel from the empty context before writing
anything. Declared dependencies are packaged as checked `Cut` nodes containing
the proposition, its proof, and the dependent body; they do not rely on an
external theorem-name or hash lookup. The snapshot records this Cut-bearing
representation as `python-dataclass-repr-with-cut-v2` and makes no claim that
erasing those nodes is an independently validated certificate transformation.
The JSON hashes are provenance aids; they confer no theorem authority.

The current snapshot contains 393 checked theorems. Its 137-entry
`quadratic_residue_foundation` layer additionally proves native finite folds,
factorial and power algebra, modular units, exact small-modulus residue
classifications, sign and half-range bridges, β-prefix swap/reindex,
constructive finite pigeonhole, replacement balance, and exact swap-last
product invariance needed by the quadratic-reciprocity campaign. The separate
nine-entry `ha_number_theory_campaign` layer adds canonical remainder,
canonical-congruence, and exact bounded modular-inverse interfaces. The live
resource policy admits 500,000 structural occurrences, 100,000 distinct proof
objects, and depth 256; these are availability limits, not logical rules.
