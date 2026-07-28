# Peano arithmetic-library artifacts

This directory is the deterministic, reviewable snapshot of Peano Lab's
checked theorem ladder. It does not extend the trusted kernel.

- `catalog-v1.json` records every closed statement, dependency, authored
  script, certificate hash, exact certificate size, and structural `Cut`
  count. The filename remains stable for downstream compatibility; its
  internal schema is `peano-library-snapshot-v2`.
- `dependency-graph.mmd` is the same directed acyclic graph in Mermaid form.
- `metrics.json` uses `peano-library-metrics-v2` and records aggregate proof
  and `Cut` counts together with the live-`use` resource bounds.
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
