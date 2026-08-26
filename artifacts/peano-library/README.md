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

## Private K3B lookup-prefix closure receipt

[`ha-k3b-listat-prefix-closure-219209.json`](ha-k3b-listat-prefix-closure-219209.json)
is the authoritative two-pass cold-closure report for
`cell_history_extend_preserves_prefix`, the first support theorem of
`HA-K3B-LISTAT-1`. Its SHA-256 is
`0d51baf93121da4071d0bb3ebd2b4a2818a7658fa92510fd707620bc2dba6560`.
WMI job `219209` completed `0:0` on `c3n1` in `00:02:14` with
`MaxRSS=85664K`; it binds clean commit
`94cf88912bf368d43a3201abc91c69ddeb442a56` to payload SHA-256
`b288d4641680f48c1b145251209bedeb5b82d7ffab40b356a1a2497fef041c74`
(564,554 bytes, 203 entries).

Both passes yielded the exact receipt
`(29369,81,4668,4896,229,241,7fd7734ab34d90a869c637e76e138db692ba21d4f2bbec41af9817c38ef36498)`
in tuple order
`(nodes,depth,objects,edges,reused,Cuts,proof DAG SHA-256)`. The 104-row
dependency closure is deterministic, the certificate contains zero DNE, and
the result fits the unchanged 500,000-node/100,000-object/depth-256 policy.
This is private `closed_checked_candidate` evidence only; no registry,
catalog, campaign JSON, public snapshot, or admission count is changed.

## Private K3B full history/lookup closure receipt

[`ha-k3b-listat-full-closure-219217.json`](ha-k3b-listat-full-closure-219217.json)
is the authoritative 10,550-byte two-pass cold-closure report for the complete
17-target `HA-K3B-CELLHISTORY-1` plus `HA-K3B-LISTAT-1` theorem stack. Its
SHA-256 is
`c79184bee17a7c053287b3b98dcda74cf00498137499ef62122b9c6d15ec40b8`.
WMI job `219217` completed `0:0` in `00:15:25` with
`MaxRSS=54,496 KiB`. It binds clean commit
`cb6fcbcc6b51e0b9290e02ed1a16d8b034145b8e` to payload SHA-256
`78e0c3d04b98ba1788edce0cd227dae3f7fe36f391a3a80b962da632a1970835`.
Both passes agree for every selected theorem, and every certificate contains
zero DNE.

The first nine receipts reproduce the eight cell-history rows and the
prefix-preservation row recorded above. The newly sealed lookup receipts use
tuple order `(nodes,depth,objects,edges,reused,Cuts,proof DAG SHA-256)`:

- T03 `list_at_domain = (39,23,39,38,0,0,09c7d6d2bb9d7cd09597285eae31355cf76b8bc54d7c370f8c9507ca0377a701)`;
- T04 `list_at_head_iff = (32025,83,4982,5225,244,248,52bb6c215c7123e58374d23935490c71eccd3a8704de193612dacb57dd33cba7)`;
- T05 `list_at_succ_iff = (30885,83,4923,5157,235,247,908364a06285830d2cc6b53919b4399203b12d08c89b9bb98de3cdd4efa5b8fa)`;
- T06 `list_at_external_bound = (34799,87,5767,6043,277,301,7c49ab5ac74468bf1537d510be4d0837bc97d2432727a3c25f00c80026a38663)`;
- T07 `list_at_exists = (133,26,127,132,6,3,6778f7b507370cb1bcd95d2bd90b0fbaea317f5ac262565152dc5eabf759698c)`;
- T08 `list_at_functional = (65579,85,5851,6140,290,296,00fc80f2b18c79f8e45a41682651c32c0fbe8b34bc39c8ca2186067c184d0a4a)`;
- T09 `list_at_history_independent = (65823,86,6022,6312,291,298,8868aaef643ffe84c4b5fb885d2f16c7b4872f071ce5de92149369d60c3dc20b)`;
- T10 `cell_list_extensional = (95253,87,5888,6162,275,266,8558cf1c4c39c0d0d8b363e7304a6c5732cee0593548a4137d1407de58f479ec)`.

This is private `closed_checked_candidate` evidence, not admission evidence.
All 17 targets remain private, unregistered, and unadmitted. The registry,
catalog, campaign JSON, public snapshots, and public counts are unchanged.
