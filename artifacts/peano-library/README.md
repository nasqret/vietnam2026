# Peano arithmetic-library artifacts

This directory is the deterministic, reviewable snapshot of Peano Lab's
63-entry checked theorem ladder. It does not extend the trusted kernel. By
publication provenance, the snapshot contains the original 23-entry core, a
14-entry general-arithmetic extension, and the 26-entry modular-arithmetic
extension. `metrics.json` instead groups reusable support lemmas by their
mathematical role, hence its `23 + 28 + 12` layer split.

- `catalog-v1.json` records every closed statement, dependency, authored
  script, certificate hash, and exact certificate size.
- `dependency-graph.mmd` is the same directed acyclic graph in Mermaid form.
- `metrics.json` records aggregate counts and the live-`use` resource bounds.
- `mod5-source-validation-report.json` preserves the independent source audit
  for the 26 imported modular-arithmetic theorems.
- `NOTICE.md` records the exact source revisions for both public extensions
  and preserves the modular source's license.

Rebuild or verify the generated snapshot from the repository root:

```bash
python3 scripts/build_peano_library_snapshot.py
python3 scripts/build_peano_library_snapshot.py --check
```

Generation replays every tactic script, eliminates theorem-dependency cuts,
and submits the resulting closed certificate to the independent kernel before
writing anything. The JSON hashes are provenance aids; they confer no theorem
authority.
