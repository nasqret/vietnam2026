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

The current snapshot contains 432 checked theorems. Its 137-entry
`quadratic_residue_foundation` layer additionally proves native finite folds,
factorial and power algebra, modular units, exact small-modulus residue
classifications, sign and half-range bridges, β-prefix swap/reindex,
constructive finite pigeonhole, replacement balance, and exact swap-last
product invariance needed by the quadratic-reciprocity campaign. The separate
48-entry `ha_number_theory_campaign` layer adds canonical remainder,
canonical congruence, exact bounded modular inverses, relational LCM totality
and uniqueness, the gcd--LCM product identity, and the selectively admitted
23-row M5 generalized-CRT closure at indices 409--431. That closure publishes
unrestricted solvability, relational-LCM solution classification, the honest
zero/nonzero canonical boundary, and raw-input constructive decision. Six
reviewed M5 convenience rows remain private. The snapshot has 1,185 dependency
edges, 1,982,360 structural nodes, 468,010 distinct proof objects, 57,692
structural Cut occurrences, and 373 Cut-bearing certificates; its ordered root
is `4d02dc439d53533e8992a471b26ee34059fb6001f822041e42c56b2cc0a7a079`. The live
resource policy admits 500,000 structural occurrences, 100,000 distinct proof
objects, and depth 256; these are availability limits, not logical rules.

## Private K3B cell-history closure receipt

[`ha-k3b-cell-history-closure-219203.json`](ha-k3b-cell-history-closure-219203.json)
is the authoritative two-pass cold-closure report for the eight private
first-ten theorem rows of `HA-K3B-CELLHISTORY-1`. Its SHA-256 is
`6ef49fcb5edb2b1c5478ff592c97dc9af56ed2f79ec03308c5ebf341833b825c`.
WMI job `219203` completed `0:0` on `c3n1` in `00:04:46` with
`MaxRSS=82428K`; it binds clean commit
`0b33b6675481a93d0e330987b22d9ef91564a0a0` to payload SHA-256
`edf77bff5cf824cbfd549179f8cef2a18ac65904d473ce3bbd2bd5e5f1c95620`
(3,911,680 bytes, 201 entries). Both passes were deterministic and every
certificate contains zero DNE.

Exact receipts use tuple order
`(nodes,depth,objects,edges,reused,Cuts,proof DAG SHA-256)`:

- `cell_history_nil = (155,18,155,154,0,2,a3038bd67616f11f8e97727c98f03af09aacde863a70637d9575e2ff9d337ff8)`;
- `cell_history_extend = (29352,81,4651,4879,229,241,370de792b2c3fed8b3d36f90147c426b846d15578cac8c66520a59df81750c78)`;
- `cell_history_succ_elim = (1245,60,772,810,39,27,e8aee67cfef618fde3b08d48dffb4a6b31cdd22a578e38206d4e5a20a96c338c)`;
- `cell_list_zero_iff_nil = (1309,60,880,916,37,26,f7fdef58a28a86bd70b133bf839f6b49526817e020da6c698b85b3cd369f2f73)`;
- `cell_list_succ_iff_cell = (30648,83,4761,4992,232,246,a64ad8e5095d50afe10b47b1036ad9b680ab82462b41beb115d23956f9fa5699)`;
- `cell_list_length_functional = (34732,85,5700,5976,277,299,5dd0e4b8f585990ec826ba5ef02960cb6817f0aec5edcb86c9bb1e22d44c5a6c)`;
- `cell_list_length_le_code = (31002,84,4891,5129,239,257,50fe47364958e1a506315935796e517f41ddd947a1792fcdb134956ba05290a9)`;
- `cell_list_length_total = (29569,84,4848,5078,231,246,2d6063d54e16c0f093aab270329bdd4ca5a7c02aa68b528c2c7c771945ccba17)`.

These are `closed_checked_candidate` receipts only. Gates G1--G6 and G7's
quarantine/closure portion pass, but public admission was deliberately not
performed. All eight rows remain private, unregistered, and unadmitted. The
public catalog and campaign JSON are unchanged: strict K3 stays 96 rows across
21 modules and campaign accounting stays 95 public references, 121 private
candidates, and 169 receipts.
