# Peano arithmetic-library artifacts

This directory is the deterministic, reviewable snapshot of Peano Lab's
checked theorem ladder. It does not extend the trusted kernel.

- `catalog-v1.json` records every closed statement, dependency, authored
  script, certificate hash, and exact certificate size.
- `dependency-graph.mmd` is the same directed acyclic graph in Mermaid form.
- `metrics.json` records aggregate counts and the live-`use` resource bounds.

Rebuild the generated files from the repository root:

```bash
python3 scripts/build_peano_library_snapshot.py
```

Verify that the committed snapshot is current:

```bash
python3 scripts/build_peano_library_snapshot.py --check
```

Generation replays every tactic script, eliminates theorem-dependency cuts,
and submits the resulting closed certificate to the independent kernel before
writing anything. The JSON hashes are provenance aids; they confer no theorem
authority.
