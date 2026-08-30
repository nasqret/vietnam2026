# VIASM 2026 — Automatic Theorem Proving in Mathematics
# Build & deploy targets. See docs/BUILD.md and docs/DEPLOY.md.

SERVER    := lts-faculty.wmi.amu.edu.pl
SITE      := ~/public_html/vietnam2026
LAB       := ~/public_html/lab-lambda
LABNEXT   := ~/public_html/lab-lambda-next
# These are `rsync --delete` destinations.  Keep command-line Make variable
# overrides from widening either one to an unrelated remote directory.
override PEANO     := ~/public_html/peano-lab
override PEANONEXT := ~/public_html/peano-lab-next
override PROOFS    := ~/public_html/proofs
override LEANAPI   := ~/public_html/api/lean-strands
STAGE     := _deploy/vietnam2026
STAGENEXT := _deploy/lab-lambda-next
PEANO_CORPUS_PYTHON ?= python3
PEANO_POLICY_DIR ?= data/peano-policy-v2
PEANO_POLICY_PILOT_DIR ?= data/peano-policy-pilot-v1
PEANO_POLICY_ROWS ?= 10000
HYDRA_CATALOG_LIMIT ?= 192
HYDRA_CATALOG_MAX_DECISIONS ?= 16
HYDRA_DEV_DIR ?= _deploy/hydra-development-v1
HYDRA_REVIEW_DIR ?= _deploy/hydra-reference-review-v1
HYDRA_REVIEW_LEAN ?=
HYDRA_REVIEW_REFERENCE_PROJECT ?= ../peano-lab-lean
HYDRA_REVIEW_COLD_SCOPE ?= sample
HYDRA_REVIEW_COLD_BATCH_SIZE ?= 1
HYDRA_REVIEW_COLD_WALL_BUDGET ?= 900
PEANO_TRAIN_JOB ?= 217859
PEANO_TRAIN_DASHBOARD_PORT ?= 8766
PEANO_LEAN_BROWSER_HOST ?= 127.0.0.1
PEANO_LEAN_BROWSER_PORT ?= 8787
PEANO_LEAN_BROWSER_ARGS ?=
PEANO_LEAN_BROWSER_CHECK_ARGS ?=
PEANO_LEAN_PUBLIC_API ?=
PEANO_LEAN_PUBLIC_ORIGIN ?= https://bnaskrecki.faculty.wmi.amu.edu.pl
PEANO_LEAN_PUBLIC_ARGS ?=
# This path is a deletion target in `stage-peano`; command-line assignments
# must not be able to widen it beyond the repository's dedicated stage tree.
override STAGEPEANO := _deploy/peano-lab
override STAGEPROOFS := _deploy/proofs
override STAGELEANAPI := _deploy/lean-api
override PEANOAPPID := a-e4012dd8e319

.PHONY: help book book-atlas book-proof-explorer book-bertrand-proof-explorer book-bertrand-defined-explorer book-constructive-frontier-explorer lean lean-fta peano-library-alpha peano-library-alpha-check peano-library-alpha-v2 peano-library-alpha-v2-check peano-library-alpha-v3 peano-library-alpha-v3-check peano-library-alpha-v4 peano-library-alpha-v4-check peano-library-alpha-v5 peano-library-alpha-v5-check peano-library-alpha-v6 peano-library-alpha-v6-check peano-library-alpha-v7 peano-library-alpha-v7-check peano-library-alpha-v8 peano-library-alpha-v8-check peano-library-alpha-v9 peano-library-alpha-v9-check peano-library-alpha-v10 peano-library-alpha-v10-check peano-library-alpha-v11 peano-library-alpha-v11-check peano-library-alpha-v12 peano-library-alpha-v12-check peano-library-alpha-v13 peano-library-alpha-v13-check peano-library-alpha-v14 peano-library-alpha-v14-check peano-library-alpha-v15 peano-library-alpha-v15-check peano-library-channels peano-library-channels-check peano-library-channels-v2 peano-library-channels-v2-check peano-library-channels-v3 peano-library-channels-v3-check peano-library-channels-v4 peano-library-channels-v4-check peano-library-channels-v5 peano-library-channels-v5-check peano-library-channels-v6 peano-library-channels-v6-check peano-library-channels-v7 peano-library-channels-v7-check peano-library-channels-v8 peano-library-channels-v8-check peano-library-channels-v9 peano-library-channels-v9-check peano-library-channels-v10 peano-library-channels-v10-check peano-library-channels-v11 peano-library-channels-v11-check peano-library-channels-v12 peano-library-channels-v12-check peano-library-channels-v13 peano-library-channels-v13-check peano-library-channels-v14 peano-library-channels-v14-check peano-library-channels-v15 peano-library-channels-v15-check ha-number-theory-check ha-constructive-frontier-check ha-k3b-cell-history-check ha-k3b-list-lookup-check lab-serve peano-serve peano-training-dashboard peano-corpus peano-corpus-smoke peano-policy-pilot peano-policy-data peano-eval stage \
	stage-peano stage-proofs stage-lean-api deploy-site deploy-lab deploy-lab-next deploy-peano \
	deploy-peano-next deploy-proofs deploy-lean-api lean-public lean-public-check \
	deploy clean

.PHONY: serve

help:
	@echo "Targets:"
	@echo "  make book         build the JupyterBook (book/_build/html)"
	@echo "  make book-atlas   regenerate the checked arithmetic theorem atlas"
	@echo "  make book-proof-explorer  regenerate the static PA proof explorer"
	@echo "  make book-bertrand-proof-explorer  regenerate the full Bertrand map"
	@echo "  make book-bertrand-defined-explorer  regenerate the readable Bertrand map"
	@echo "  make book-constructive-frontier-explorer  regenerate six evidence-honest frontier proof maps"
	@echo "  make book-constructive-next-layer-explorer  regenerate four historical Alpha-v20 research maps"
	@echo "  make book-constructive-advanced-layer-explorer  regenerate three independently checked Alpha-v21 research maps"
	@echo "  make book-constructive-transport-layer-explorer  regenerate three canonical Alpha-v22 proof maps"
	@echo "  make book-constructive-milestone-closure-explorer  regenerate three complete Alpha-v23 milestone proof maps"
	@echo "  make book-constructive-research-layer-explorer  regenerate three canonical Alpha-v24 research proof maps"
	@echo "  make book-constructive-second-wave-explorer  verify the frozen Alpha-v27 campaign maps"
	@echo "  make book-constructive-second-wave-current-explorer  publish unchanged v27/v28/v29 proofs under current v30 authority"
	@echo "  make book-constructive-lower-layer-explorer  verify four frozen Alpha-v28 proof families"
	@echo "  make book-constructive-gaussian-factorization-explorer  publish the complete Gaussian unique-factorization map"
	@echo "  make book-constructive-bottom-layer-publication  verify four public research checkpoint maps without Alpha admission"
	@echo "  make book-constructive-lower-tier-publication  verify 126 further public research proofs without Alpha admission"
	@echo "  make check-constructive-lower-continuation  recheck 125 subsequent local proofs and twelve ordinary certificates"
	@echo "  make book-constructive-lower-continuation-explorer  verify four subsequent local-only canonical proof maps"
	@echo "  make check-constructive-dirichlet  recheck 113 local convolution/inversion proofs and fifteen ordinary certificates"
	@echo "  make book-constructive-dirichlet-explorer  verify five local canonical maps, including full finite Mobius inversion"
	@echo "  make check-constructive-dirichlet-inverse  recheck 40 local general-inverse proofs and nine ordinary certificates"
	@echo "  make book-constructive-dirichlet-inverse-explorer  verify three local canonical maps toward G009"
	@echo "  make peano-library-alpha-v29-check  verify the exact four priority targets with all proof gates"
	@echo "  make peano-library-alpha-v30-check  verify the complete Gaussian factorization release and current UI"
	@echo "  make lean         build & axiom-check the Lean artifact"
	@echo "  make lean-fta     build & exact-axiom-check the Lean FTA companion"
	@echo "  make peano-library-alpha  regenerate the sealed Alpha v1 parent artifacts"
	@echo "  make peano-library-alpha-check  verify sealed Alpha v1/Stable channels"
	@echo "  make peano-library-alpha-v2  regenerate the current additive Alpha v2 artifacts"
	@echo "  make peano-library-alpha-v2-check  verify additive Alpha v2 and replay K3C bodies"
	@echo "  make peano-library-channels-v2  compatibility alias for the current Alpha v2 build"
	@echo "  make peano-library-channels-v2-check  compatibility alias for the current Alpha v2 check"
	@echo "  make peano-library-alpha-v3  regenerate additive Bertrand Alpha v3 artifacts"
	@echo "  make peano-library-alpha-v3-check  verify Alpha v3 and replay all 21 Bertrand bodies"
	@echo "  make peano-library-channels-v3  compatibility alias for the Bertrand Alpha v3 build"
	@echo "  make peano-library-channels-v3-check  compatibility alias for the Bertrand Alpha v3 check"
	@echo "  make peano-library-alpha-v4  regenerate additive Bertrand Round-2 Alpha v4 artifacts"
	@echo "  make peano-library-alpha-v4-check  verify Alpha v4 and replay all 42 Round-2 bodies"
	@echo "  make peano-library-channels-v4  compatibility alias for the Bertrand Alpha v4 build"
	@echo "  make peano-library-channels-v4-check  compatibility alias for the Bertrand Alpha v4 check"
	@echo "  make peano-library-alpha-v5  regenerate additive Bertrand FactorialVal Alpha v5 artifacts"
	@echo "  make peano-library-alpha-v5-check  verify Alpha v5 and replay all 7 FactorialVal bodies"
	@echo "  make peano-library-channels-v5  compatibility alias for the Bertrand Alpha v5 build"
	@echo "  make peano-library-channels-v5-check  compatibility alias for the Bertrand Alpha v5 check"
	@echo "  make peano-library-alpha-v6  regenerate additive 21-row Bertrand Alpha v6 artifacts"
	@echo "  make peano-library-alpha-v6-check  verify Alpha v6 and replay all 21 appended bodies"
	@echo "  make peano-library-channels-v6  compatibility alias for the Bertrand Alpha v6 build"
	@echo "  make peano-library-channels-v6-check  compatibility alias for the Bertrand Alpha v6 check"
	@echo "  make peano-library-alpha-v7  regenerate additive 24-row Bertrand Alpha v7 artifacts"
	@echo "  make peano-library-alpha-v7-check  verify Alpha v7 and replay all 24 appended bodies"
	@echo "  make peano-library-channels-v7  compatibility alias for the Bertrand Alpha v7 build"
	@echo "  make peano-library-channels-v7-check  compatibility alias for the Bertrand Alpha v7 check"
	@echo "  make peano-library-alpha-v8  regenerate additive 38-row Bertrand Alpha v8 artifacts"
	@echo "  make peano-library-alpha-v8-check  verify v8, replay 38 bodies, then run 19 source suites serially"
	@echo "  make peano-library-channels-v8  compatibility alias for the Bertrand Alpha v8 build"
	@echo "  make peano-library-channels-v8-check  compatibility alias for the Bertrand Alpha v8 check"
	@echo "  make peano-library-alpha-v9  regenerate additive 21-row Bertrand Alpha v9 artifacts"
	@echo "  make peano-library-alpha-v9-check  verify v9, replay 21 bodies, then run 2 source suites serially"
	@echo "  make peano-library-channels-v9  compatibility alias for the Bertrand Alpha v9 build"
	@echo "  make peano-library-channels-v9-check  compatibility alias for the Bertrand Alpha v9 check"
	@echo "  make peano-library-alpha-v10  regenerate additive 1+8-row Bertrand Alpha v10 artifacts"
	@echo "  make peano-library-alpha-v10-check  verify v10, replay 9 bodies, then run 2 source suites serially"
	@echo "  make peano-library-channels-v10  compatibility alias for the Bertrand Alpha v10 build"
	@echo "  make peano-library-channels-v10-check  compatibility alias for the Bertrand Alpha v10 check"
	@echo "  make peano-library-alpha-v11  regenerate additive 38-row Bertrand Alpha v11 artifacts"
	@echo "  make peano-library-alpha-v11-check  verify v11, replay 38 bodies, then run 5 source suites serially"
	@echo "  make peano-library-channels-v11  compatibility alias for the Bertrand Alpha v11 build"
	@echo "  make peano-library-channels-v11-check  compatibility alias for the Bertrand Alpha v11 check"
	@echo "  make peano-library-alpha-v12  regenerate additive 180-row Bertrand Alpha v12 artifacts"
	@echo "  make peano-library-alpha-v12-check  verify the complete body-checked Bertrand proof release"
	@echo "  make peano-library-channels-v12  compatibility alias for the Bertrand Alpha v12 build"
	@echo "  make peano-library-channels-v12-check  compatibility alias for the Bertrand Alpha v12 check"
	@echo "  make peano-library-alpha-v13  regenerate additive 196+44-row Lagrange/Lucas Alpha v13 artifacts"
	@echo "  make peano-library-alpha-v13-check  independently verify Alpha v13 and its body-only admission boundary"
	@echo "  make peano-library-channels-v13  compatibility alias for the Lagrange/Lucas Alpha v13 build"
	@echo "  make peano-library-channels-v13-check  compatibility alias for the Lagrange/Lucas Alpha v13 check"
	@echo "  make peano-library-alpha-v14  regenerate additive 13-row Kummer Alpha v14 artifacts"
	@echo "  make peano-library-alpha-v14-check  independently verify Alpha v14 and its body-only Kummer admission"
	@echo "  make peano-library-channels-v14  compatibility alias for the Kummer Alpha v14 build"
	@echo "  make peano-library-channels-v14-check  compatibility alias for the Kummer Alpha v14 check"
	@echo "  make peano-library-alpha-v15  regenerate additive 117-row supplementary/two-square Alpha v15 artifacts"
	@echo "  make peano-library-alpha-v15-check  independently verify Alpha v15 and its body-only admission"
	@echo "  make peano-library-channels-v15  compatibility alias for the supplementary/two-square Alpha v15 build"
	@echo "  make peano-library-channels-v15-check  compatibility alias for the supplementary/two-square Alpha v15 check"
	@echo "  make peano-library-alpha-v16  seal the independently closed quadratic-reciprocity Alpha v16 evidence promotion"
	@echo "  make peano-library-alpha-v16-check  independently verify all genuine QR proofs, immutable history, and 315 checked-use promotions"
	@echo "  make peano-library-channels-v16  compatibility alias for the current Alpha v16 build"
	@echo "  make peano-library-channels-v16-check  compatibility alias for the current Alpha v16 check"
	@echo "  make peano-library-alpha-v17  seal both independently closed quadratic supplementary laws"
	@echo "  make peano-library-alpha-v17-check  verify immutable history, all 438 actual proofs, and 31 checked-use promotions"
	@echo "  make peano-library-channels-v17  compatibility alias for the historical Alpha v17 build"
	@echo "  make peano-library-channels-v17-check  compatibility alias for the historical Alpha v17 check"
	@echo "  make peano-library-alpha-v18  seal five completely proved constructive flagship campaigns"
	@echo "  make peano-library-alpha-v18-check  verify all five actual proof bundles and 673 checked-use promotions"
	@echo "  make peano-library-channels-v18  compatibility alias for the historical Alpha v18 build"
	@echo "  make peano-library-channels-v18-check  compatibility alias for the historical Alpha v18 check"
	@echo "  make peano-library-alpha-v19  seal the fully checked constructive number-theory campaign"
	@echo "  make peano-library-alpha-v19-check  verify all 1,737 proofs, 84 closures, and 64 new results"
	@echo "  make peano-library-channels-v19  compatibility alias for the historical Alpha v19 build"
	@echo "  make peano-library-channels-v19-check  compatibility alias for the historical Alpha v19 check"
	@echo "  make peano-library-alpha-v20  seal 39 additive polynomial, matrix, Bertrand, and continued-fraction theorems"
	@echo "  make peano-library-alpha-v20-check  independently verify all 1,776 checked theorems and their exact next-layer bundle"
	@echo "  make peano-library-channels-v20  compatibility alias for the historical Alpha v20 build"
	@echo "  make peano-library-channels-v20-check  compatibility alias for the historical Alpha v20 check"
	@echo "  make peano-library-alpha-v21  seal 54 matrix, Euclidean, and binary modular theorems"
	@echo "  make peano-library-alpha-v21-check  independently verify all 1,830 theorems and their compact 209-node bundle"
	@echo "  make peano-library-channels-v21  compatibility alias for the historical Alpha v21 build"
	@echo "  make peano-library-channels-v21-check  compatibility alias for the historical Alpha v21 check"
	@echo "  make peano-library-alpha-v22  seal 60 historical binary and Euclidean transport theorems"
	@echo "  make peano-library-alpha-v22-check  independently verify all 1,890 historical Alpha-v22 theorems"
	@echo "  make peano-library-alpha-v23  seal the three fully proved 1,949-theorem Alpha-v23 campaigns"
	@echo "  make peano-library-alpha-v23-check  independently verify all original-kernel and Lean-checked Alpha-v23 evidence"
	@echo "  make peano-library-channels-v23  compatibility alias for the current Alpha-v23 build"
	@echo "  make peano-library-channels-v23-check  compatibility alias for the current Alpha-v23 check"
	@echo "  make peano-library-alpha-v24  seal the independently checked CRT, determinant, and polynomial research layer"
	@echo "  make peano-library-alpha-v24-check  verify every Alpha-v24 proof, immutable parent, and Lean certificate"
	@echo "  make peano-library-channels-v24  compatibility alias for the current Alpha-v24 build"
	@echo "  make peano-library-channels-v24-check  compatibility alias for the current Alpha-v24 check"
	@echo "  make peano-library-alpha-v25  seal the additive cofactor, Taylor, and CRT-compatibility breakthrough layer"
	@echo "  make peano-library-alpha-v25-check  independently verify every Alpha-v25 proof, definition DAG, and Lean certificate"
	@echo "  make peano-library-channels-v25  compatibility alias for the current Alpha-v25 build"
	@echo "  make peano-library-channels-v25-check  compatibility alias for the current Alpha-v25 check"
	@echo "  make peano-library-alpha-v26  seal the completed Pythagorean/Fermat first execution wave"
	@echo "  make peano-library-alpha-v26-check  verify all first-wave proofs, Lean certificates, definitions, and maps"
	@echo "  make peano-library-alpha-v27  seal the seven completed second-wave campaigns over unchanged Stable"
	@echo "  make peano-library-alpha-v27-check  verify all 422 new proofs, complete certificates, definitions, and publication routes"
	@echo "  make peano-library-alpha-v28  build the independently closed lower-layer Alpha release"
	@echo "  make peano-library-alpha-v28-check  verify exact lower-layer endpoints, historical boundaries, and canonical explorers"
	@echo "  make ha-number-theory-check  validate strict-HA admission, gcd, and signed normalization tranches"
	@echo "  make ha-constructive-frontier-check  replay ordered stages 1-6 in bounded isolated proof processes"
	@echo "  make ha-k3b-cell-history-check  run the lightweight Alpha K3B RFC/body checks"
	@echo "  make ha-k3b-list-lookup-check  run the Alpha K3B ListAt surface checks"
	@echo "  make serve        serve the whole site locally on :8000 (landing + book + slides + labs)"
	@echo "  make lab-serve    serve lab-lambda alone on :8001"
	@echo "  make peano-serve serve the staged Peano Lab locally on :8002"
	@echo "  make lean-browser  open the theorem graph and bounded Lean proof builder on :$(PEANO_LEAN_BROWSER_PORT)"
	@echo "  make lean-browser-check  independently smoke-test the running Lean theorem browser"
	@echo "  make lean-public  connect the public faculty proof gateway to the private local Lean worker"
	@echo "  make lean-public-start  start a managed background public proof tunnel and bounded worker"
	@echo "  make lean-public-status  verify the public gateway and private worker are identical"
	@echo "  make lean-public-stop  stop the managed public tunnel and its owned worker"
	@echo "  make lean-public-check  independently verify the deployed public theorem-to-Lean workflow"
	@echo "  make deploy-lean-public  publish all proof explorers and the isolated public Lean gateway"
	@echo "  make peano-training-dashboard  observe WMI job $(PEANO_TRAIN_JOB) on :$(PEANO_TRAIN_DASHBOARD_PORT)"
	@echo "  make peano-corpus reproduce the leakage-safe Peano train/val release"
	@echo "  make peano-corpus-smoke  run the all-ladder M9 generation/export smoke"
	@echo "  make peano-policy-pilot  build the checked M19 pilot policy dataset"
	@echo "  make peano-policy-v2-data  build+attest $(PEANO_POLICY_ROWS) model-v2 policy rows"
	@echo "  make peano-policy-data   compatibility alias for peano-policy-v2-data"
	@echo "  make hydra-check  verify the canonical DAGs, Hydra product contracts, and checked development pipeline"
	@echo "  make hydra-prepare  export deterministic verified proof-optimization/discovery post-training artifacts"
	@echo "  make hydra-scale  replay a bounded, mixed Stable/Alpha theorem curriculum"
	@echo "  make hydra-posttrain-prepare  build heldout-clean Alpha model training/validation artifacts"
	@echo "  make hydra-posttrain-preflight  verify the Alpha-authorized Qwen training contract without loading a model"
	@echo "  make hydra-eval-plan  verify a matched pretrained/trained evaluation without fabricating model results"
	@echo "  make hydra-eval-control  independently run the bounded model-free symbolic benchmark control"
	@echo "  make hydra-dev-plan  inspect the broader lineage-audited symbolic development experiment"
	@echo "  make hydra-dev-evaluate  explicitly run isolated bounded CPU development searches"
	@echo "  make hydra-dev-verify  independently replay every retained development proof"
	@echo "  make hydra-review-plan  inspect reference/lineage review evidence; requires HYDRA_REVIEW_LEAN=/installed/bin/lean"
	@echo "  make hydra-review-run  run bounded reference and cold-sample checks with the explicitly selected Lean binary"
	@echo "  make hydra-review-verify  independently recheck the frozen evidence in HYDRA_REVIEW_DIR"
	@echo "  make hydra-posttrain-ready  build and verify the complete bounded Alpha model-development pipeline"
	@echo "  make hydra-posttrain-execute  explicitly run bounded Alpha LoRA training on one prepared CUDA GPU"
	@echo "  make peano-eval   run the deterministic kernel-judged random baseline"
	@echo "  make stage        assemble _deploy/vietnam2026 (landing + book + slides)"
	@echo "  make deploy-site  rsync the site to $(SITE)"
	@echo "  make deploy-lab   rsync the browser lab to $(LAB)"
	@echo "  make deploy-lab-next  deploy the Web Worker preview to $(LABNEXT)"
	@echo "  make deploy-peano  rsync Peano Lab to $(PEANO)"
	@echo "  make deploy-peano-next  deploy Peano Lab staging to $(PEANONEXT)"
	@echo "  make stage-proofs  assemble the standalone proof-explorer families"
	@echo "  make stage-lean-api  assemble the isolated same-origin faculty PHP proof gateway"
	@echo "  make deploy-lean-api  publish only the isolated same-origin Lean proof gateway"
	@echo "  make deploy-proofs  publish the proof hub to $(PROOFS)"
	@echo "  make deploy       stage + deploy-site + deploy-lab"
	@echo "  make clean        remove build/stage artifacts"

book-atlas:
	python3 scripts/build_arithmetic_book_atlas.py

book-bertrand-proof-explorer:
	python3 scripts/build_bertrand_proof_explorer.py

book-bertrand-defined-explorer: book-bertrand-proof-explorer
	python3 scripts/build_bertrand_defined_explorer.py

book-proof-explorer: book-bertrand-defined-explorer
	python3 scripts/build_pa_proof_explorer.py
	python3 scripts/build_pa_defined_explorer.py

.PHONY: book-proof-explorer-check

# Publication verifies the historical flagships without rewriting their trees.
book-proof-explorer-check:
	PYTHONMALLOC=malloc python3 scripts/build_bertrand_proof_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/build_bertrand_defined_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/build_pa_proof_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/build_pa_defined_explorer.py --check

book-constructive-frontier-explorer:
	python3 scripts/build_constructive_frontier_explorer.py

.PHONY: book-constructive-next-layer-explorer

book-constructive-next-layer-explorer:
	python3 scripts/build_constructive_next_layer_explorer.py

.PHONY: book-constructive-advanced-layer-explorer

book-constructive-advanced-layer-explorer:
	python3 scripts/build_constructive_advanced_layer_explorer.py

.PHONY: book-constructive-transport-layer-explorer

book-constructive-transport-layer-explorer:
	python3 scripts/build_constructive_transport_layer_explorer.py

.PHONY: book-constructive-milestone-closure-explorer

book-constructive-milestone-closure-explorer:
	python3 scripts/build_constructive_milestone_closure_explorer.py

.PHONY: book-constructive-research-layer-explorer

book-constructive-research-layer-explorer:
	python3 scripts/build_constructive_research_layer_explorer.py

.PHONY: book-constructive-breakthrough-layer-explorer

book-constructive-breakthrough-layer-explorer:
	python3 scripts/build_constructive_breakthrough_layer_explorer.py

.PHONY: book-constructive-second-wave-explorer

book-constructive-second-wave-explorer:
	python3 scripts/upgrade_constructive_second_wave_publication_v28.py --check-historical

.PHONY: book-constructive-second-wave-current-explorer book-constructive-lower-layer-explorer

book-constructive-second-wave-current-explorer:
	python3 scripts/upgrade_constructive_priority_layer_publication_v30.py

book-constructive-lower-layer-explorer:
	python3 scripts/build_constructive_lower_layer_explorer.py --check

.PHONY: book-constructive-current-atlas book-constructive-gaussian-factorization-explorer \
	book-constructive-priority-layer-explorer book-constructive-second-wave-v28-explorer

book-constructive-current-atlas:
	PYTHONMALLOC=malloc python3 scripts/extend_constructive_gaussian_factorization_campaign.py

# Current publication must follow its separately authenticated current atlas.
# The v27, v28 and v29 historical generators and their outputs remain frozen.
book-constructive-frontier-explorer book-constructive-next-layer-explorer \
	book-constructive-advanced-layer-explorer book-constructive-transport-layer-explorer \
	book-constructive-milestone-closure-explorer book-constructive-research-layer-explorer \
	book-constructive-breakthrough-layer-explorer book-constructive-second-wave-current-explorer \
	book-constructive-gaussian-factorization-explorer: book-constructive-current-atlas

book-constructive-gaussian-factorization-explorer:
	PYTHONMALLOC=malloc python3 scripts/build_constructive_gaussian_factorization_explorer.py

book-constructive-priority-layer-explorer:
	PYTHONMALLOC=malloc python3 scripts/build_constructive_priority_layer_explorer.py --check

book-constructive-second-wave-v28-explorer:
	python3 scripts/upgrade_constructive_second_wave_publication_v28.py --check

.PHONY: book-constructive-bottom-layer-publication

# Public research checkpoints are complete proofs, not an Alpha promotion.
# Verify the recorded snapshot and actual HA/Lean bundles before staging it.
book-constructive-bottom-layer-publication:
	PYTHONMALLOC=malloc python3 scripts/build_constructive_bottom_layer_publication.py --check

.PHONY: book-constructive-lower-tier-publication
book-constructive-lower-tier-publication:
	PYTHONMALLOC=malloc python3 scripts/build_constructive_lower_tier_publication.py --check

.PHONY: check-constructive-lower-continuation book-constructive-lower-continuation-explorer
# Subsequent research remains local: these gates are not stage-proofs inputs.
check-constructive-lower-continuation:
	PYTHONMALLOC=malloc python3 scripts/check_constructive_lower_continuation.py --check

book-constructive-lower-continuation-explorer:
	PYTHONMALLOC=malloc python3 scripts/build_constructive_lower_continuation_explorer.py --check

.PHONY: check-constructive-dirichlet book-constructive-dirichlet-explorer
# Dirichlet research is local only; neither target is a stage-proofs input.
check-constructive-dirichlet:
	PYTHONMALLOC=malloc python3 scripts/check_constructive_dirichlet.py --check

book-constructive-dirichlet-explorer:
	PYTHONMALLOC=malloc python3 scripts/build_constructive_dirichlet_explorer.py --check

.PHONY: check-constructive-dirichlet-inverse book-constructive-dirichlet-inverse-explorer
# General inverses remain local; these gates do not stage or promote proofs.
check-constructive-dirichlet-inverse:
	PYTHONMALLOC=malloc python3 scripts/check_constructive_dirichlet_inverse.py --check

book-constructive-dirichlet-inverse-explorer:
	PYTHONMALLOC=malloc python3 scripts/build_constructive_dirichlet_inverse_explorer.py --check

.PHONY: peano-library-alpha-v31 peano-library-alpha-v31-publish peano-library-alpha-v31-check book-constructive-completed-lower-explorer-v31
# The additive presentation entrypoint preserves all sealed v31 sources and
# corrects the aggregate atlas link. Saved receipts never replace its 72 fresh
# proof jobs. Rendering keeps three original 180s windows and mandatory tests.
peano-library-alpha-v31:
	PYTHONMALLOC=malloc python3 scripts/publish_constructive_completed_lower_v31.py --create-release
	python3 scripts/build_constructive_completed_lower_hub_v31.py

peano-library-alpha-v31-publish:
	PYTHONMALLOC=malloc python3 scripts/publish_constructive_completed_lower_v31.py
	python3 scripts/build_constructive_completed_lower_hub_v31.py

peano-library-alpha-v31-check:
	PYTHONMALLOC=malloc python3 scripts/publish_constructive_completed_lower_v31.py --check
	python3 scripts/build_constructive_completed_lower_hub_v31.py --check

book-constructive-completed-lower-explorer-v31: peano-library-alpha-v31-check

book: book-atlas book-proof-explorer
	rm -rf book/_build   # full rebuild: incremental Sphinx leaves stale sidebars after TOC changes
	jupyter-book build book/
	@# ensure a directory index exists (external-toc usually writes one)
	@[ -f book/_build/html/index.html ] || cp book/_build/html/intro.html book/_build/html/index.html

lean:
	cd artifacts/lean && lake build
	cd artifacts/lean && printf 'import Artifacts\nopen Artifacts Artifacts.Sqrt2\n#print axioms s_combinator\n#print axioms add_comm'"'"'\n#print axioms no_sqrt2\n' > /tmp/check.lean && lake env lean /tmp/check.lean | tee /dev/stderr | (! grep -q sorryAx)

lean-fta:
	cd artifacts/lean-fta && lake update
	cd artifacts/lean-fta && lake exe cache get
	cd artifacts/lean-fta && lake build
	python3 scripts/verify_lean_fta.py

peano-library-alpha:
	python3 scripts/build_peano_library_channels.py

peano-library-alpha-check:
	python3 scripts/build_peano_library_channels.py --check
	python3 scripts/verify_peano_library_channels.py
	python3 -m pytest -q scripts/test_verify_peano_library_channels.py

peano-library-alpha-v2:
	python3 scripts/build_peano_library_channels_v2.py

peano-library-alpha-v2-check:
	python3 scripts/build_peano_library_channels_v2.py --check
	python3 scripts/verify_peano_library_channels_v2.py
	python3 -m pytest -q scripts/test_verify_peano_library_channels_v2.py scripts/test_run_wmi_k3c_cell_list_closure.py
	cd peano-lab/py && python3 -m pytest -q \
		tests/test_ha_cell_list_membership_surface_candidate.py \
		tests/test_ha_cell_list_membership_candidate.py \
		tests/test_library_editions_v2.py

peano-library-alpha-v3:
	python3 scripts/build_peano_library_channels_v3.py

peano-library-alpha-v3-check:
	python3 scripts/build_peano_library_channels_v3.py --check
	python3 scripts/verify_peano_library_channels_v3.py
	python3 -m pytest -q scripts/test_verify_peano_library_channels_v3.py
	cd peano-lab/py && python3 -m pytest -q \
		tests/test_library_editions_v3.py \
		tests/test_bertrand_prime_interval_candidate.py \
		tests/test_bertrand_power_order_candidate.py \
		tests/test_bertrand_power_growth_candidate.py \
		tests/test_bertrand_power_valuation_candidate.py

peano-library-alpha-v4:
	python3 scripts/build_peano_library_channels_v4.py

peano-library-alpha-v4-check:
	python3 scripts/build_peano_library_channels_v4.py --check
	python3 scripts/verify_peano_library_channels_v4.py
	python3 -m pytest -q scripts/test_verify_peano_library_channels_v4.py
	cd peano-lab/py && python3 -m pytest -q \
		tests/test_library_editions_v4.py \
		tests/test_bertrand_power_valuation_laws_candidate.py \
		tests/test_bertrand_power_divisibility_candidate.py \
		tests/test_bertrand_integer_envelope_candidate.py \
		tests/test_bertrand_ceil_sqrt_candidate.py \
		tests/test_bertrand_floor_sqrt_total_candidate.py \
		tests/test_bertrand_quotient_budget_candidate.py

peano-library-alpha-v5:
	python3 scripts/build_peano_library_channels_v5.py

peano-library-alpha-v5-check:
	python3 scripts/build_peano_library_channels_v5.py --check
	python3 scripts/verify_peano_library_channels_v5.py
	python3 -m pytest -q scripts/test_verify_peano_library_channels_v5.py
	cd peano-lab/py && python3 -m pytest -q \
		tests/test_library_editions_v5.py \
		tests/test_bertrand_factorial_valuation_candidate.py

peano-library-alpha-v6:
	python3 scripts/build_peano_library_channels_v6.py

peano-library-alpha-v6-check:
	python3 scripts/build_peano_library_channels_v6.py --check
	python3 scripts/verify_peano_library_channels_v6.py
	python3 -m pytest -q scripts/test_verify_peano_library_channels_v6.py
	cd peano-lab/py && python3 -m pytest -q \
		tests/test_library_editions_v6.py \
		tests/test_bertrand_threshold_base_candidate.py \
		tests/test_bertrand_legendre_sum_candidate.py \
		tests/test_bertrand_power_bridge_candidate.py \
		tests/test_bertrand_legendre_valuation_bridge_candidate.py

peano-library-alpha-v7:
	python3 scripts/build_peano_library_channels_v7.py

peano-library-alpha-v7-check:
	python3 scripts/build_peano_library_channels_v7.py --check
	python3 scripts/verify_peano_library_channels_v7.py
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v7.py::test_repository_v7_validates_with_all_twenty_four_body_replays \
		scripts/test_verify_peano_library_channels_v7.py::test_v7_builder_is_byte_deterministic_for_all_outputs
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v7.py::test_parent_prefix_mutation_is_rejected \
		scripts/test_verify_peano_library_channels_v7.py::test_parent_family_binding_mutation_is_rejected \
		scripts/test_verify_peano_library_channels_v7.py::test_each_source_block_runtime_specification_is_pinned
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v7.py::test_source_test_and_rfc_documents_are_byte_bound \
		scripts/test_verify_peano_library_channels_v7.py::test_every_source_block_document_is_byte_bound \
		scripts/test_verify_peano_library_channels_v7.py::test_source_test_rfc_parent_cross_bundle_mutation_is_rejected
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v7.py::test_fabricated_closure_checked_use_and_proof_tag_are_rejected \
		scripts/test_verify_peano_library_channels_v7.py::test_body_receipt_mutation_is_rejected_by_fresh_kernel_replay \
		scripts/test_verify_peano_library_channels_v7.py::test_each_v7_artifact_mutation_is_rejected \
		scripts/test_verify_peano_library_channels_v7.py::test_stable_pointer_object_cannot_change \
		scripts/test_verify_peano_library_channels_v7.py::test_sealed_v6_parent_artifact_mutation_is_rejected
	cd peano-lab/py && python3 -m pytest -q tests/test_library_editions_v7.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_initial_segment_constructor_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_legendre_successor_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_power_total_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_hj_base_window_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_legendre_recurrence_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_hj_transport_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_factorial_legendre_candidate.py

peano-library-alpha-v8:
	python3 scripts/build_peano_library_channels_v8.py

peano-library-alpha-v8-check:
	python3 scripts/build_peano_library_channels_v8.py --check
	python3 scripts/verify_peano_library_channels_v8.py
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v8.py::test_repository_v8_validates_with_all_thirty_eight_body_replays \
		scripts/test_verify_peano_library_channels_v8.py::test_v8_builder_is_byte_deterministic_for_all_outputs
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v8.py::test_parent_prefix_mutation_is_rejected \
		scripts/test_verify_peano_library_channels_v8.py::test_parent_family_binding_mutation_is_rejected \
		scripts/test_verify_peano_library_channels_v8.py::test_each_source_block_runtime_specification_is_pinned
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v8.py::test_source_test_and_rfc_documents_are_byte_bound \
		scripts/test_verify_peano_library_channels_v8.py::test_every_source_block_document_is_byte_bound \
		scripts/test_verify_peano_library_channels_v8.py::test_source_test_rfc_parent_cross_bundle_mutation_is_rejected
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v8.py::test_fabricated_closure_checked_use_and_proof_tag_are_rejected \
		scripts/test_verify_peano_library_channels_v8.py::test_body_receipt_mutation_is_rejected_by_fresh_kernel_replay \
		scripts/test_verify_peano_library_channels_v8.py::test_each_v8_artifact_mutation_is_rejected \
		scripts/test_verify_peano_library_channels_v8.py::test_stable_pointer_object_cannot_change \
		scripts/test_verify_peano_library_channels_v8.py::test_sealed_v7_parent_artifact_mutation_is_rejected
	cd peano-lab/py && python3 -m pytest -q tests/test_library_editions_v8.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_choose_foundation_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_choose_row_functional_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_choose_table_row_functional_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_choose_laws_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_choose_diagonal_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_choose_recurrence_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_choose_pascal_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_choose_symmetry_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_choose_positive_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_central_binom_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_central_binom_zero_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_central_binom_succ_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_choose_weighted_vertical_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_central_binom_recurrence_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_choose_factorial_support_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_choose_factorial_bridge_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_central_binom_growth_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_central_binom_lower_seed_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_central_binom_lower_bound_candidate.py

peano-library-alpha-v9:
	python3 scripts/build_peano_library_channels_v9.py

peano-library-alpha-v9-check:
	python3 scripts/build_peano_library_channels_v9.py --check
	python3 scripts/verify_peano_library_channels_v9.py
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v9.py::test_repository_v9_validates_with_all_twenty_one_body_replays \
		scripts/test_verify_peano_library_channels_v9.py::test_v9_builder_is_byte_deterministic_for_all_outputs
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v9.py::test_parent_prefix_mutation_is_rejected \
		scripts/test_verify_peano_library_channels_v9.py::test_parent_family_binding_mutation_is_rejected \
		scripts/test_verify_peano_library_channels_v9.py::test_each_source_block_runtime_specification_is_pinned
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v9.py::test_source_test_and_rfc_documents_are_byte_bound \
		scripts/test_verify_peano_library_channels_v9.py::test_every_source_block_document_is_byte_bound \
		scripts/test_verify_peano_library_channels_v9.py::test_source_test_rfc_parent_cross_bundle_mutation_is_rejected
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v9.py::test_fabricated_closure_checked_use_and_proof_tag_are_rejected \
		scripts/test_verify_peano_library_channels_v9.py::test_body_receipt_mutation_is_rejected_by_fresh_kernel_replay \
		scripts/test_verify_peano_library_channels_v9.py::test_each_v9_artifact_mutation_is_rejected \
		scripts/test_verify_peano_library_channels_v9.py::test_stable_pointer_object_cannot_change \
		scripts/test_verify_peano_library_channels_v9.py::test_sealed_v8_parent_artifact_mutation_is_rejected
	cd peano-lab/py && python3 -m pytest -q tests/test_library_editions_v9.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_primorial_foundation_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_primorial_membership_candidate.py

peano-library-alpha-v10:
	python3 scripts/build_peano_library_channels_v10.py

peano-library-alpha-v10-check:
	python3 scripts/build_peano_library_channels_v10.py --check
	python3 scripts/verify_peano_library_channels_v10.py
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v10.py::test_repository_v10_validates_with_all_nine_body_replays \
		scripts/test_verify_peano_library_channels_v10.py::test_v10_builder_is_byte_deterministic_for_all_outputs
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v10.py::test_parent_prefix_mutation_is_rejected \
		scripts/test_verify_peano_library_channels_v10.py::test_parent_family_binding_mutation_is_rejected \
		scripts/test_verify_peano_library_channels_v10.py::test_each_source_block_runtime_specification_is_pinned
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v10.py::test_source_test_and_rfc_documents_are_byte_bound \
		scripts/test_verify_peano_library_channels_v10.py::test_every_source_block_document_is_byte_bound \
		scripts/test_verify_peano_library_channels_v10.py::test_source_test_rfc_parent_cross_bundle_mutation_is_rejected
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v10.py::test_fabricated_closure_checked_use_and_proof_tag_are_rejected \
		scripts/test_verify_peano_library_channels_v10.py::test_body_receipt_mutation_is_rejected_by_fresh_kernel_replay \
		scripts/test_verify_peano_library_channels_v10.py::test_each_v10_artifact_mutation_is_rejected \
		scripts/test_verify_peano_library_channels_v10.py::test_stable_pointer_object_cannot_change \
		scripts/test_verify_peano_library_channels_v10.py::test_sealed_v9_parent_artifact_mutation_is_rejected
	cd peano-lab/py && python3 -m pytest -q tests/test_library_editions_v10.py
	cd peano-lab/py && python3 -m pytest -q tests/test_finite_product_prefix_suffix_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_primorial_interval_candidate.py

peano-library-alpha-v11:
	python3 scripts/build_peano_library_channels_v11.py

peano-library-alpha-v11-check:
	@# The verifier independently replays all 38 bodies and regenerates all four
	@# canonical payloads, so a preceding builder --check would duplicate the
	@# memory-intensive v11 build without adding a distinct gate.
	python3 scripts/verify_peano_library_channels_v11.py
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v11.py::test_parent_prefix_mutation_is_rejected \
		scripts/test_verify_peano_library_channels_v11.py::test_parent_family_binding_mutation_is_rejected \
		scripts/test_verify_peano_library_channels_v11.py::test_each_source_block_runtime_specification_is_pinned
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v11.py::test_source_test_and_rfc_documents_are_byte_bound
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v11.py::test_every_source_block_document_is_byte_bound
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v11.py::test_source_test_rfc_parent_cross_bundle_mutation_is_rejected
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v11.py::test_fabricated_closure_checked_use_and_proof_tag_are_rejected \
		scripts/test_verify_peano_library_channels_v11.py::test_sealed_v10_parent_artifact_mutation_is_rejected
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v11.py::test_body_receipt_mutation_is_rejected_by_fresh_kernel_replay
	python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v11.py::test_each_v11_artifact_mutation_is_rejected \
		scripts/test_verify_peano_library_channels_v11.py::test_stable_pointer_object_cannot_change
	cd peano-lab/py && python3 -m pytest -q tests/test_library_editions_v11.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_primorial_duplicate_free_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_primorial_choose_interval_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_central_binom_upper_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_primorial_four_power_candidate.py
	cd peano-lab/py && python3 -m pytest -q tests/test_bertrand_central_binom_prime_support_candidate.py

peano-library-alpha-v12:
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v12.py

peano-library-alpha-v12-check:
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v12.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v12.py
	PYTHONMALLOC=malloc python3 -m pytest -q \
		scripts/test_verify_peano_library_channels_v12.py \
		-k 'not repository_v12 and not builder_is_byte_deterministic'
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q \
		tests/test_library_editions_v12.py -k 'not one_hundred_eighty'
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_hj_base_thirty_two_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_hj_all_s_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_b6_growth_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_b6_layered_closure.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_finite_product_order_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_b5_order_quotient_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_central_binom_valuation_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_central_binom_carry_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_central_binom_square_tail_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_central_binom_zero_range_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_central_binom_factor_ranges_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_prime_contribution_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_prime_contribution_complete_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_b5_range_boundaries_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_b5_contribution_split_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_b5_central_upper_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_b7_eventual_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_b8_prime_certificates_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_b8_covering_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_b8_small_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_bp01_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q tests/test_bertrand_bp02_candidate.py
	python3 scripts/build_bertrand_proof_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/build_bertrand_defined_explorer.py --check
	python3 -m pytest -q \
		peano-lab/py/tests/test_bertrand_proof_explorer.py \
		peano-lab/py/tests/test_bertrand_defined_explorer.py

peano-library-alpha-v13:
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v13.py

peano-library-alpha-v13-check:
	@# Every gate owns its interpreter: 240 dependency-curried body receipts
	@# never accumulate alongside independent release/admission proof caches.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v13.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v13.py
	PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		scripts/test_verify_peano_library_channels_v13.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_library_editions_v13_admission.py

peano-library-alpha-v14:
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v14.py

peano-library-alpha-v14-check:
	@# Preserve bounded proof caches by isolating each independent release gate.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v14.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v14.py
	PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		scripts/test_verify_peano_library_channels_v14.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_library_editions_v14_admission.py

peano-library-alpha-v15:
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v15.py

peano-library-alpha-v15-check:
	@# All 14 candidate factories replay serially inside fresh proof workers.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v15.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v15.py
	PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		scripts/test_verify_peano_library_channels_v15.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_library_editions_v15_admission.py

.PHONY: peano-library-alpha-v16 peano-library-alpha-v16-check \
	peano-library-channels-v16 peano-library-channels-v16-check

peano-library-alpha-v16:
	@# Decode and check all 557 actual intuitionistic proof bodies.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v16.py

peano-library-alpha-v16-check:
	@# Every gate checks real proof data while preserving isolated proof caches.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v16.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v16.py
	PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		scripts/test_verify_peano_library_channels_v16.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_library_editions_v16_admission.py

.PHONY: peano-library-alpha-v17 peano-library-alpha-v17-check \
	peano-library-channels-v17 peano-library-channels-v17-check

peano-library-alpha-v17:
	@# Decode and independently check all 438 ordinary constructive proof bodies.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v17.py

peano-library-alpha-v17-check:
	@# Isolated proof workers preserve unchanged node/object limits and bounded RSS.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v17.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v17.py
	PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		scripts/test_verify_peano_library_channels_v17.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_library_editions_v17_admission.py tests/test_alpha_v16_ui.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_supplementary_laws_closure.py \
		-k 'not test_each_supplement_endpoint_has_actual_empty_context_kernel_proof'
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/supplementary-laws-proof-bundle-v1.json

.PHONY: peano-library-alpha-v18 peano-library-alpha-v18-check \
	peano-library-channels-v18 peano-library-channels-v18-check

peano-library-alpha-v18:
	@# All five canonical artifacts are independently decoded and kernel checked.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v18.py

peano-library-alpha-v18-check:
	@# Isolate heavyweight proof caches while preserving every original hard cap.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v18.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v18.py
	PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		scripts/test_verify_peano_library_channels_v18.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_library_editions_v18_admission.py tests/test_alpha_v16_ui.py
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/lucas-proof-bundle-v1.json
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/kummer-proof-bundle-v1.json
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/bertrand-proof-bundle-v1.json
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/four-square-proof-bundle-v1.json
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/two-square-proof-bundle-v1.json

.PHONY: peano-library-alpha-v19 peano-library-alpha-v19-check \
	peano-library-channels-v19 peano-library-channels-v19-check

peano-library-alpha-v19:
	@# Both exact artifacts independently recheck every unchanged-kernel body.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v19.py

peano-library-alpha-v19-check:
	@# Isolated workers preserve every historical proof and memory limit.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v19.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v19.py
	PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		scripts/test_verify_peano_library_channels_v19.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_library_editions_v19_admission.py tests/test_alpha_v16_ui.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_campaign_residual_closure.py \
		tests/test_linear_congruence_complete_candidate.py \
		tests/test_primes_one_mod_four_candidate.py
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/alpha-v19-residual-proof-bundle-v1.json
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/alpha-v19-campaign-frontier-proof-bundle-v1.json

.PHONY: peano-library-alpha-v20 peano-library-alpha-v20-check \
	peano-library-channels-v20 peano-library-channels-v20-check

peano-library-alpha-v20:
	@# Every new theorem is closed by one self-contained ordinary proof DAG.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v20.py

peano-library-alpha-v20-check:
	@# Isolate the heavyweight next-layer proof graph and preserve all hard caps.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v20.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v20.py
	PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		scripts/test_verify_peano_library_channels_v20.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_library_editions_v20_admission.py tests/test_alpha_v16_ui.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_campaign_next_layer_closure.py \
		tests/test_polynomial_horner_candidate.py \
		tests/test_matrix_dot_product_candidate.py \
		tests/test_bertrand_prime_campaign_candidate.py \
		tests/test_continued_fraction_candidate.py
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/alpha-v20-next-layer-proof-bundle-v1.json

.PHONY: peano-library-alpha-v21 peano-library-alpha-v21-check \
	peano-library-channels-v21 peano-library-channels-v21-check

peano-library-alpha-v21:
	@# Every additive row is independently checked by the original kernel and Lean.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v21.py

peano-library-alpha-v21-check:
	@# Isolated checks keep the exact compact advanced-layer proof graph bounded.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v21.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v21.py
	PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		scripts/test_verify_peano_library_channels_v21.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_library_editions_v21_admission.py \
		tests/test_campaign_advanced_layer_closure.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_matrix_coded_product_candidate.py \
		tests/test_euclidean_complexity_candidate.py \
		tests/test_binary_modular_exponentiation_candidate.py
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/alpha-v21-advanced-layer-proof-bundle-v1.json

.PHONY: peano-library-alpha-v22 peano-library-alpha-v22-check \
	peano-library-channels-v22 peano-library-channels-v22-check

peano-library-alpha-v22:
	@# Every transport theorem needs both unchanged-kernel and independent Lean checks.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v22.py

peano-library-alpha-v22-check:
	@# Keep candidate suites isolated to bound proof-object and theorem-cache memory.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v22.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v22.py
	PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		scripts/test_verify_peano_library_channels_v22.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_library_editions_v22_admission.py \
		tests/test_campaign_transport_layer_closure.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_binary_length_candidate.py \
		tests/test_euclidean_gcd_transport_candidate.py \
		tests/test_binary_modular_execution_candidate.py
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/alpha-v22-transport-layer-proof-bundle-v1.json

.PHONY: peano-library-alpha-v23 peano-library-alpha-v23-check \
	peano-library-channels-v23 peano-library-channels-v23-check

peano-library-alpha-v23:
	@# Every closed milestone requires both original-kernel and compiled-Lean evidence.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v23.py

peano-library-alpha-v23-check:
	@# Keep each large proof/Lean check isolated to preserve bounded memory.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v23.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v23.py
	PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		scripts/test_verify_peano_library_channels_v23.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_library_editions_v23_admission.py \
		tests/test_campaign_milestone_closure.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_euclidean_logarithmic_bound_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_binary_digit_extraction_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_primes_three_mod_four_candidate.py
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/alpha-v23-milestone-closure-proof-bundle-v1.json

.PHONY: peano-library-alpha-v24 peano-library-alpha-v24-check \
	peano-library-channels-v24 peano-library-channels-v24-check

peano-library-alpha-v24:
	@# Every new theorem requires both unchanged-kernel and compiled-Lean evidence.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v24.py

peano-library-alpha-v24-check:
	@# Keep heavyweight proof and Lean checks isolated and memory-bounded.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v24.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v24.py
	PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		scripts/test_verify_peano_library_channels_v24.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_library_editions_v24_admission.py \
		tests/test_campaign_research_layer_closure.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_generalized_crt_fold_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_matrix_determinant_minors_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_polynomial_hensel_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_constructive_grand_campaign.py \
		tests/test_constructive_definition_graph.py \
		tests/test_constructive_research_layer_explorer.py \
		tests/test_constructive_research_publication_v24.py
	python3 scripts/sync_constructive_grand_campaign.py --check
	python3 scripts/update_peano_worker_sources.py --check
	bash scripts/update_peano_app_manifest.sh --check
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/alpha-v24-research-layer-proof-bundle-v1.json

.PHONY: peano-library-alpha-v25 peano-library-alpha-v25-check \
	peano-library-channels-v25 peano-library-channels-v25-check

peano-library-alpha-v25:
	@# Admission requires exact unchanged-kernel and independently compiled Lean proofs.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v25.py

peano-library-alpha-v25-check:
	@# Isolate bounded theorem replays to avoid cross-campaign memory retention.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v25.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v25.py
	PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		scripts/test_verify_peano_library_channels_v25.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_library_editions_v25_admission.py \
		tests/test_campaign_breakthrough_layer_closure.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_matrix_cofactor_expansion_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_polynomial_taylor_hensel_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_generalized_crt_compatibility_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_constructive_grand_campaign.py \
		tests/test_constructive_campaign_dag.py \
		tests/test_constructive_definition_graph.py \
		tests/test_constructive_breakthrough_layer_explorer.py \
		tests/test_constructive_breakthrough_publication_v25.py
	python3 scripts/sync_constructive_grand_campaign.py --check
	python3 scripts/update_peano_worker_sources.py --check
	bash scripts/update_peano_app_manifest.sh --check
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/alpha-v25-breakthrough-layer-proof-bundle-v1.json

peano-library-channels: peano-library-alpha

peano-library-channels-check: peano-library-alpha-check

peano-library-channels-v2: peano-library-alpha-v2

peano-library-channels-v2-check: peano-library-alpha-v2-check

peano-library-channels-v3: peano-library-alpha-v3

peano-library-channels-v3-check: peano-library-alpha-v3-check

peano-library-channels-v4: peano-library-alpha-v4

peano-library-channels-v4-check: peano-library-alpha-v4-check

peano-library-channels-v5: peano-library-alpha-v5

peano-library-channels-v5-check: peano-library-alpha-v5-check

peano-library-channels-v6: peano-library-alpha-v6

peano-library-channels-v6-check: peano-library-alpha-v6-check

peano-library-channels-v7: peano-library-alpha-v7

peano-library-channels-v7-check: peano-library-alpha-v7-check

peano-library-channels-v8: peano-library-alpha-v8

peano-library-channels-v8-check: peano-library-alpha-v8-check

peano-library-channels-v9: peano-library-alpha-v9

peano-library-channels-v9-check: peano-library-alpha-v9-check

peano-library-channels-v10: peano-library-alpha-v10

peano-library-channels-v10-check: peano-library-alpha-v10-check

peano-library-channels-v11: peano-library-alpha-v11

peano-library-channels-v11-check: peano-library-alpha-v11-check

peano-library-channels-v12: peano-library-alpha-v12

peano-library-channels-v12-check: peano-library-alpha-v12-check

peano-library-channels-v13: peano-library-alpha-v13

peano-library-channels-v13-check: peano-library-alpha-v13-check

peano-library-channels-v14: peano-library-alpha-v14

peano-library-channels-v14-check: peano-library-alpha-v14-check

peano-library-channels-v15: peano-library-alpha-v15

peano-library-channels-v15-check: peano-library-alpha-v15-check

peano-library-channels-v16: peano-library-alpha-v16

peano-library-channels-v16-check: peano-library-alpha-v16-check

peano-library-channels-v17: peano-library-alpha-v17

peano-library-channels-v17-check: peano-library-alpha-v17-check

peano-library-channels-v18: peano-library-alpha-v18

peano-library-channels-v18-check: peano-library-alpha-v18-check

peano-library-channels-v19: peano-library-alpha-v19

peano-library-channels-v19-check: peano-library-alpha-v19-check

peano-library-channels-v20: peano-library-alpha-v20

peano-library-channels-v20-check: peano-library-alpha-v20-check

peano-library-channels-v21: peano-library-alpha-v21

peano-library-channels-v21-check: peano-library-alpha-v21-check

peano-library-channels-v22: peano-library-alpha-v22

peano-library-channels-v22-check: peano-library-alpha-v22-check

peano-library-channels-v23: peano-library-alpha-v23

peano-library-channels-v23-check: peano-library-alpha-v23-check

peano-library-channels-v24: peano-library-alpha-v24

peano-library-channels-v24-check: peano-library-alpha-v24-check

peano-library-channels-v25: peano-library-alpha-v25

peano-library-channels-v25-check: peano-library-alpha-v25-check

.PHONY: peano-library-alpha-v26 peano-library-alpha-v26-check \
	peano-library-channels-v26 peano-library-channels-v26-check

peano-library-alpha-v26:
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v26.py

peano-library-alpha-v26-check:
	@# Reconstruct/replay in bounded processes; never substitute body-only evidence.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v26.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v26.py --verify-roots
	PYTHONMALLOC=malloc python3 -m pytest -q --tb=line scripts/test_verify_peano_library_channels_v26.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_coprime_square_factor_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_pythagorean_inverse_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_fermat_four_descent_candidate.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_library_editions_v26_admission.py tests/test_campaign_first_wave_closure.py \
		tests/test_constructive_first_wave_definitions.py tests/test_constructive_local_formula_compaction.py \
		tests/test_constructive_first_wave_publication_v26.py tests/test_constructive_first_wave_hub.py \
		tests/test_deploy_contract.py
	PYTHONMALLOC=malloc python3 scripts/sync_constructive_grand_campaign.py --check
	PYTHONMALLOC=malloc python3 scripts/build_constructive_frontier_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/build_constructive_next_layer_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/build_constructive_advanced_layer_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/build_constructive_transport_layer_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/build_constructive_milestone_closure_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/build_constructive_research_layer_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/build_constructive_breakthrough_layer_explorer.py --check
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/alpha-v26-first-wave-proof-bundle-v1.json

peano-library-channels-v26: peano-library-alpha-v26

peano-library-channels-v26-check: peano-library-alpha-v26-check

.PHONY: peano-library-alpha-v27 peano-library-alpha-v27-check \
	peano-library-channels-v27 peano-library-channels-v27-check

peano-library-alpha-v27:
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v27.py

peano-library-alpha-v27-check:
	@# Each mathematical suite gets a fresh interpreter; complete HA and Lean checks remain mandatory.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v27.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v27.py --verify-roots
	PYTHONMALLOC=malloc python3 -m pytest -q --tb=line scripts/test_verify_peano_library_channels_v27.py
	@for suite in \
		matrix_recursive_determinant_candidate \
		matrix_recursive_determinant_extensional_candidate \
		matrix_rank_finite_coding_candidate \
		matrix_rank_selected_minors_candidate \
		matrix_rank_certificate_candidate \
		integer_column_span_candidate \
		matrix_integer_invariance_candidate \
		matrix_rank_integer_invariance_candidate \
		matrix_lattice_data_candidate \
		hensel_prime_power_candidate \
		signed_hensel_lifting_candidate \
		hensel_simple_root_criterion_candidate \
		generalized_crt_full_candidate \
		multinomial_kummer_candidate \
		prime_count_chebyshev_candidate \
		cornacchia_candidate \
		finite_modular_set_candidate \
		cauchy_davenport_candidate; do \
		(cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line "tests/test_$${suite}.py") || exit $$?; \
	done
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_library_editions_v27_admission.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_campaign_second_wave_closure.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_constructive_campaign_dag.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_constructive_definition_graph.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_constructive_grand_campaign.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_constructive_second_wave_definitions.py tests/test_constructive_second_wave_explorer.py \
		tests/test_constructive_first_wave_hub.py tests/test_deploy_contract.py tests/test_browser_shell.py
	PYTHONMALLOC=malloc python3 scripts/sync_constructive_grand_campaign.py --check
	PYTHONMALLOC=malloc python3 scripts/build_constructive_frontier_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/build_constructive_next_layer_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/build_constructive_advanced_layer_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/build_constructive_transport_layer_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/build_constructive_milestone_closure_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/build_constructive_research_layer_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/build_constructive_breakthrough_layer_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/upgrade_constructive_second_wave_publication_v28.py --check-historical
	bash scripts/update_peano_app_manifest.sh --check
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/alpha-v27-second-wave-proof-bundle-v1.json

peano-library-channels-v27: peano-library-alpha-v27

peano-library-channels-v27-check: peano-library-alpha-v27-check

.PHONY: peano-library-alpha-v28 peano-library-alpha-v28-check \
	peano-library-channels-v28 peano-library-channels-v28-check

peano-library-alpha-v28:
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v28.py

peano-library-alpha-v28-check:
	@# Isolated mathematical suites bound memory; no original HA or Lean gate is omitted.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v28.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v28.py --verify-roots
	PYTHONMALLOC=malloc python3 -m pytest -q --tb=line scripts/test_verify_peano_library_channels_v28.py
	@for suite in \
		foundation_saturation_candidate \
		prime_factorization_permutation_candidate \
		signed_integer_division_candidate \
		gaussian_euclidean_candidate \
		eisenstein_euclidean_candidate \
		prime_enumeration_candidate; do \
		(cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line "tests/test_$${suite}.py") || exit $$?; \
	done
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_library_editions_v28_admission.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_campaign_lower_layer_closure.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_constructive_lower_layer_definitions.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_constructive_lower_layer_explorer.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_constructive_second_wave_publication_v28.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_constructive_second_wave_explorer.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line \
		tests/test_constructive_campaign_dag.py tests/test_constructive_definition_graph.py \
		tests/test_constructive_grand_campaign.py tests/test_constructive_first_wave_hub.py \
		tests/test_alpha_v28_ui.py tests/test_deploy_contract.py tests/test_browser_shell.py \
		tests/test_book_arithmetic_part.py
	PYTHONMALLOC=malloc python3 scripts/extend_constructive_lower_layer_campaign.py --check
	PYTHONMALLOC=malloc python3 scripts/sync_constructive_grand_campaign.py --check
	PYTHONMALLOC=malloc python3 scripts/build_constructive_lower_layer_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/upgrade_constructive_second_wave_publication_v28.py --check
	PYTHONMALLOC=malloc python3 scripts/upgrade_constructive_second_wave_publication_v28.py --check-historical
	bash scripts/update_peano_app_manifest.sh --check
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/alpha-v28-lower-layer-proof-bundle-v1.json

peano-library-channels-v28: peano-library-alpha-v28

peano-library-channels-v28-check: peano-library-alpha-v28-check

.PHONY: peano-library-alpha-v29 peano-library-alpha-v29-check \
	peano-library-channels-v29 peano-library-channels-v29-check

peano-library-alpha-v29:
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v29.py

peano-library-alpha-v29-check:
	@# Sequential, bounded proof suites; no historical, HA or Lean gate is omitted.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v29.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v29.py --verify-roots
	PYTHONMALLOC=malloc python3 -m pytest -q --tb=line scripts/test_verify_peano_library_channels_v29.py
	@for suite in \
		prime_valuation_support_candidate \
		continued_fraction_approximation_candidate \
		continued_fraction_convergents_candidate \
		euler_totient_count_candidate \
		euler_totient_interval_candidate \
		euler_totient_prime_step_candidate \
		euler_totient_algebra_candidate \
		euler_totient_product_candidate \
		squarefree_decomposition_candidate \
		perfect_power_profile_candidate \
		odd_prime_lte_candidate; do \
		(cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line "tests/test_$${suite}.py") || exit $$?; \
	done
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_library_editions_v29_admission.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_campaign_priority_layer_closure.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_constructive_priority_layer_definitions.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_constructive_priority_layer_explorer.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_constructive_lower_layer_publication_v29.py
	PYTHONMALLOC=malloc python3 scripts/extend_constructive_priority_layer_campaign.py --check
	PYTHONMALLOC=malloc python3 scripts/build_constructive_priority_layer_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/upgrade_constructive_lower_layer_publication_v29.py --check
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/alpha-v29-priority-layer-proof-bundle-v1.json

peano-library-channels-v29: peano-library-alpha-v29

peano-library-channels-v29-check: peano-library-alpha-v29-check

.PHONY: peano-library-alpha-v30 peano-library-alpha-v30-check \
	peano-library-channels-v30 peano-library-channels-v30-check

peano-library-alpha-v30:
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v30.py

peano-library-alpha-v30-check:
	@# Sequential, bounded proof suites; no historical, HA or Lean gate is omitted.
	PYTHONMALLOC=malloc python3 scripts/build_peano_library_channels_v30.py --check
	PYTHONMALLOC=malloc python3 scripts/verify_peano_library_channels_v30.py --verify-roots
	PYTHONMALLOC=malloc python3 -m pytest -q --tb=line scripts/test_verify_peano_library_channels_v30.py
	@for suite in \
		gaussian_ring_candidate \
		gaussian_divisibility_candidate \
		gaussian_gcd_candidate \
		gaussian_factor_search_candidate \
		gaussian_factorization_candidate \
		gaussian_product_reindex_candidate \
		gaussian_factor_permutation_candidate; do \
		(cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line "tests/test_$${suite}.py") || exit $$?; \
	done
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_library_editions_v30_admission.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_campaign_gaussian_factorization_closure.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_constructive_gaussian_factorization_definitions.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_constructive_gaussian_factorization_explorer.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_constructive_priority_layer_publication_v30.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_alpha_v30_ui.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_lean_certified_export.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_lean_proof_strand_cli.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_lean_presentation_cli.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_lean_strand_service_v30.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_constructive_exact_graph_navigation.py
	cd peano-lab/py && PYTHONMALLOC=pymalloc python3 -m pytest -q --tb=line tests/test_constructive_publication_json_encoding.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_deploy_contract.py
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q --tb=line tests/test_browser_shell.py
	PYTHONMALLOC=malloc python3 scripts/extend_constructive_gaussian_factorization_campaign.py --check
	PYTHONMALLOC=malloc python3 scripts/build_constructive_gaussian_factorization_explorer.py --check
	PYTHONMALLOC=malloc python3 scripts/upgrade_constructive_priority_layer_publication_v30.py --check
	@for layer in frontier next_layer advanced_layer transport_layer milestone_closure research_layer breakthrough_layer; do \
		PYTHONMALLOC=pymalloc python3 "scripts/build_constructive_$${layer}_explorer.py" --check || exit $$?; \
	done
	@for suite in \
		constructive_frontier_explorer \
		constructive_next_layer_explorer \
		constructive_next_layer_public_site \
		constructive_advanced_layer_explorer \
		constructive_transport_layer_explorer \
		constructive_milestone_closure_explorer \
		constructive_research_layer_explorer \
		constructive_breakthrough_layer_explorer \
		constructive_research_publication_v24 \
		constructive_breakthrough_publication_v25; do \
		if test "$${suite}" = constructive_next_layer_explorer; then \
			for selection in \
				'not (current or recent or v30_retains_exact)' \
				'(current or recent) and not (current_publishers_reject or v30_retains_exact) and current_parent' \
				'current_v30_publishers' \
				'recent_parent_audit' \
				'(current or recent) and not (current_publishers_reject or v30_retains_exact or current_parent or current_v30_publishers or recent_parent_audit)' \
				'current_publishers_reject and not v30_retains_exact' \
				'v30_retains_exact'; do \
				(cd peano-lab/py && PYTHONMALLOC=pymalloc python3 -m pytest -q --tb=line "tests/test_$${suite}.py" -k "$${selection}") || exit $$?; \
			done; \
		elif test "$${suite}" = constructive_research_layer_explorer || test "$${suite}" = constructive_breakthrough_layer_explorer; then \
			for selection in 'current_authority_corruption' 'not current_authority_corruption'; do \
				(cd peano-lab/py && PYTHONMALLOC=pymalloc python3 -m pytest -q --tb=line "tests/test_$${suite}.py" -k "$${selection}") || exit $$?; \
			done; \
		else \
			(cd peano-lab/py && PYTHONMALLOC=pymalloc python3 -m pytest -q --tb=line "tests/test_$${suite}.py") || exit $$?; \
		fi; \
	done
	bash scripts/update_peano_app_manifest.sh --check
	../peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify \
		research/arithmetic-library/artifacts/alpha-v30-gaussian-factorization-proof-bundle-v1.json

peano-library-channels-v30: peano-library-alpha-v30

peano-library-channels-v30-check: peano-library-alpha-v30-check

ha-number-theory-check:
	python3 scripts/verify_ha_number_theory_campaign.py
	python3 scripts/verify_ha_definition_freeze.py --replay-proved-api
	python3 -m pytest -q scripts/test_verify_ha_number_theory_campaign.py scripts/test_verify_ha_definition_freeze.py scripts/test_verify_ha_pair_cell_rfc.py
	cd peano-lab/py && python3 -m pytest -q \
		tests/test_ha_canonical_remainder_candidate.py \
		tests/test_ha_canonical_congruence_candidate.py \
		tests/test_ha_modular_inverse_candidate.py \
		tests/test_ha_canonical_gcd_candidate.py \
		tests/test_ha_canonical_gcd_edges_candidate.py \
		tests/test_ha_signed_parity_candidate.py \
		tests/test_ha_signed_decode_candidate.py \
		tests/test_ha_signed_code_extensional_candidate.py \
		tests/test_ha_signed_balance_candidate.py \
		tests/test_ha_signed_balance_complete_candidate.py \
		tests/test_ha_signed_negate_candidate.py \
		tests/test_ha_signed_add_candidate.py \
		tests/test_ha_signed_add_laws_candidate.py \
		tests/test_ha_signed_add_associative_candidate.py \
		tests/test_ha_signed_mul_candidate.py \
		tests/test_ha_signed_mul_laws_candidate.py \
		tests/test_ha_signed_mul_associative_candidate.py \
		tests/test_ha_signed_mul_distributive_candidate.py \
		tests/test_ha_signed_nat_scale_candidate.py \
		tests/test_ha_signed_nat_scale_laws_candidate.py \
		tests/test_ha_signed_bezout_candidate.py \
		tests/test_ha_pair_cell_seed_candidate.py \
		tests/test_ha_pair_shell_candidate.py \
		tests/test_ha_pair_injective_candidate.py \
		tests/test_ha_cell_functional_candidate.py \
		tests/test_ha_cell_bounds_candidate.py \
		tests/test_ha_signed_bezout_gcd_candidate.py \
		tests/test_ha_relational_lcm_candidate.py \
		tests/test_ha_lcm_totality_bridge_candidate.py \
		tests/test_ha_number_theory_tranche01_admission.py \
		tests/test_ha_number_theory_k4_gcd_lcm_admission.py \
		tests/test_ha_generalized_crt_congruence_candidate.py \
		tests/test_ha_generalized_crt_sufficiency_candidate.py \
		tests/test_ha_generalized_crt_zero_boundary_candidate.py \
		tests/test_ha_generalized_crt_classification_candidate.py \
		tests/test_ha_generalized_crt_canonical_boundary_candidate.py \
		tests/test_ha_generalized_crt_decision_candidate.py \
		tests/test_ha_generalized_crt_total_decision_candidate.py \
		tests/test_ha_number_theory_m5_generalized_crt_admission.py

# Every frontier suite gets a fresh interpreter: proof DAG caches from one
# constructive campaign must not inflate the memory envelope of the next.
# Compact tracebacks prevent deeply nested first-order AST repr explosions on
# an unexpected failed assertion or exploratory proof mutation.
ha-constructive-frontier-check:
	@echo "Stage 1: quadratic reciprocity, supplementary laws, and Bertrand promotion"
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_quadratic_reciprocity_layered_experiment.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_euler_criterion_bounded_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_gauss_lemma_bounded_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_quadratic_supplement_minus_one_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_quadratic_supplement_two_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_bertrand_promotion.py
	@echo "Stage 2: general Kummer valuation and carry-count theorem"
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_kummer_valuation_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_kummer_carry_candidate.py
	@echo "Stage 3: Fermat two-square roots, bounds, collisions, and residue grids"
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_fermat_two_squares_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_fermat_two_squares_pigeonhole_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_finite_prefix_collision_decision_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_fermat_two_squares_residue_grid_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_fermat_two_squares_collision_norm_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_fermat_two_squares_prime_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_fermat_two_squares_brahmagupta_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_fermat_two_squares_classification_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_fermat_two_squares_valuation_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_fermat_two_squares_factor_fold_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_fermat_two_squares_pairing_candidate.py
	@echo "Stage 4: unconditional Euler identity, prime seeds, and four-square descent"
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_four_square_identity_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_four_square_euler_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_four_square_lagrange_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_four_square_cross_pigeonhole_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_four_square_residue_intersection_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_four_square_descent_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_four_square_signed_quaternion_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_four_square_signed_block_negative_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_four_square_signed_orientation_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_four_square_bounded_seed_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_four_square_lagrange_bridge_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_four_square_parity_selection_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_four_square_branch_descent_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_four_square_conjugate_identity_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_four_square_signed_cases_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_four_square_lagrange_final_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_four_square_frontier_promotion.py
	@echo "Stage 5: complete constructive multidigit Lucas theorem"
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_lucas_digit_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_lucas_convolution_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_lucas_low_digit_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_lucas_block_digit_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_lucas_multidigit_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_frontier_promotion.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_lucas_mixed_promotion.py
	@echo "Stage 6: constructive Pythagorean triples and conditional Fermat-four descent"
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_pythagorean_fermat_four_candidate.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_pythagorean_primitive_candidate.py
	@echo "Presentation: six evidence-honest constructive frontier proof maps"
	python3 scripts/build_constructive_frontier_explorer.py --check
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_constructive_frontier_explorer.py
	cd peano-lab/py && python3 -m pytest -q --tb=line tests/test_deploy_contract.py

# Deliberately separate from ha-number-theory-check: this is a lightweight
# BODY-CHECKED authoring gate, not the isolated cold empty-context closure gate.
ha-k3b-cell-history-check:
	python3 -m pytest -q scripts/test_verify_ha_cell_history_rfc.py
	python3 -m pytest -q scripts/test_verify_ha_cell_history_wmi_receipt.py
	cd peano-lab/py && python3 -m pytest -q \
		tests/test_ha_cell_history_candidate.py \
		tests/test_ha_cell_list_equations_candidate.py \
		tests/test_ha_cell_list_length_functional_candidate.py \
		tests/test_ha_cell_list_length_bound_candidate.py \
		tests/test_ha_cell_list_length_total_candidate.py

# Deliberately lightweight locally: candidate bodies are dependency-curried,
# while the two empty-context WMI receipts are verified without proof replay.
ha-k3b-list-lookup-check:
	python3 -m pytest -q scripts/test_verify_ha_cell_list_lookup_rfc.py
	python3 -m pytest -q scripts/test_verify_ha_cell_list_lookup_wmi_receipt.py
	python3 -m pytest -q scripts/test_verify_ha_cell_list_lookup_full_wmi_receipt.py
	cd peano-lab/py && python3 -m pytest -q \
		tests/test_ha_cell_list_lookup_surface_candidate.py \
		tests/test_ha_cell_history_prefix_preservation_candidate.py \
		tests/test_ha_cell_list_lookup_domain_candidate.py \
		tests/test_ha_cell_list_lookup_head_candidate.py \
		tests/test_ha_cell_list_lookup_succ_candidate.py \
		tests/test_ha_cell_list_lookup_external_bound_candidate.py \
		tests/test_ha_cell_list_lookup_exists_candidate.py \
		tests/test_ha_cell_list_lookup_functional_candidate.py \
		tests/test_ha_cell_list_lookup_history_independent_candidate.py \
		tests/test_ha_cell_list_extensional_candidate.py

# Full local preview: landing page at /, with /lab-lambda/ resolving like on the
# server (symlink tree in _preview/, so edits are live). Needs `make book` once.
serve:
	python3 scripts/serve_local.py

lab-serve:
	@echo "→ http://localhost:8001/  (Ctrl-C to stop)"
	cd lab-lambda && python3 -m http.server 8001

peano-serve: stage-peano
	@echo "→ http://localhost:8002/  (Ctrl-C to stop)"
	cd "$(STAGEPEANO)" && python3 -m http.server 8002

.PHONY: lean-browser lean-browser-check lean-public-start lean-public-status \
	lean-public-stop deploy-lean-public
lean-browser:
	python3 scripts/serve_lean_strands.py \
		--host "$(PEANO_LEAN_BROWSER_HOST)" \
		--port "$(PEANO_LEAN_BROWSER_PORT)" \
		$(PEANO_LEAN_BROWSER_ARGS)

lean-browser-check:
	python3 scripts/check_lean_browser.py \
		--base-url "http://$(PEANO_LEAN_BROWSER_HOST):$(PEANO_LEAN_BROWSER_PORT)" \
		$(PEANO_LEAN_BROWSER_CHECK_ARGS)

lean-public:
	python3 scripts/serve_public_lean.py \
		--ssh-host "$(SERVER)" \
		$(PEANO_LEAN_PUBLIC_ARGS)

lean-public-start:
	python3 scripts/public_lean_tunnel.py start

lean-public-status:
	python3 scripts/public_lean_tunnel.py status

lean-public-stop:
	python3 scripts/public_lean_tunnel.py stop

lean-public-check:
	python3 scripts/check_lean_browser.py \
		--base-url "$(PEANO_LEAN_PUBLIC_ORIGIN)" \
		--site-url "$(PEANO_LEAN_PUBLIC_ORIGIN)" \
		$(PEANO_LEAN_BROWSER_CHECK_ARGS)

peano-training-dashboard:
	python3 scripts/serve_wmi_training_dashboard.py --job-id "$(PEANO_TRAIN_JOB)" --port "$(PEANO_TRAIN_DASHBOARD_PORT)"

# The committed learning release deliberately omits every ladder session.  Raw
# session JSONL remains a reproducible intermediate in /tmp; the manifest keeps
# its exact byte hash and the released transitions live under peano-lab/corpus/.
peano-corpus:
	@$(PEANO_CORPUS_PYTHON) -c 'import platform, sys; actual = f"{platform.python_implementation()} {platform.python_version()}"; expected = "CPython 3.10.0"; sys.exit(0 if actual == expected else f"byte-identical Peano corpus reproduction needs {expected}, got {actual}; override PEANO_CORPUS_PYTHON with that interpreter")'
	$(PEANO_CORPUS_PYTHON) scripts/generate_peano_traces.py \
		--output /tmp/peano-lab-release-raw.jsonl \
		--manifest peano-lab/corpus/generation-manifest.json \
		--seed 0 --renamed 1500 --commuted 96 --numeric 96 \
		--auto-depth 5 --auto-max-nodes 5000 \
		--no-ladder-auto --no-ladder-scripts
	$(PEANO_CORPUS_PYTHON) scripts/export_traces.py /tmp/peano-lab-release-raw.jsonl \
		--output-dir peano-lab/corpus --val-fraction 0.1 --seed peano-lab-v1

# The acceptance superset includes honest bounded-auto attempts and checked
# authored replays for every theorem-ladder entry.  It is not training input.
peano-corpus-smoke:
	$(PEANO_CORPUS_PYTHON) scripts/generate_peano_traces.py \
		--output /tmp/peano-lab-acceptance-raw.jsonl \
		--manifest /tmp/peano-lab-acceptance-manifest.json \
		--renamed 0 --commuted 0 --numeric 0 \
		--auto-depth 1 --auto-max-nodes 1
	$(PEANO_CORPUS_PYTHON) scripts/export_traces.py /tmp/peano-lab-acceptance-raw.jsonl \
		--output-dir /tmp/peano-lab-acceptance-export

# Small M19 end-to-end artifact: proof-first public-surface generation followed
# by exact replay compilation into completion-only train/val/test examples.
peano-policy-pilot:
	mkdir -p "$(PEANO_POLICY_PILOT_DIR)"
	$(PEANO_CORPUS_PYTHON) scripts/generate_peano_policy_corpus.py \
		--trace-output "$(PEANO_POLICY_PILOT_DIR)/raw-traces.jsonl" \
		--metadata-output "$(PEANO_POLICY_PILOT_DIR)/session-metadata.jsonl" \
		--manifest "$(PEANO_POLICY_PILOT_DIR)/source-manifest.json"
	$(PEANO_CORPUS_PYTHON) scripts/build_peano_policy_dataset.py \
		"$(PEANO_POLICY_PILOT_DIR)/raw-traces.jsonl" \
		--metadata "$(PEANO_POLICY_PILOT_DIR)/session-metadata.jsonl" \
		--output-dir "$(PEANO_POLICY_PILOT_DIR)"

peano-policy-data: peano-policy-v2-data

peano-policy-v2-data:
	mkdir -p "$(PEANO_POLICY_DIR)"
	$(PEANO_CORPUS_PYTHON) scripts/generate_peano_synthetic_corpus.py \
		--profile model-v2 \
		--trace-output "$(PEANO_POLICY_DIR)/raw-traces.jsonl" \
		--metadata-output "$(PEANO_POLICY_DIR)/session-metadata.jsonl" \
		--manifest "$(PEANO_POLICY_DIR)/source-manifest.json" \
		--row-budget "$(PEANO_POLICY_ROWS)"
	$(PEANO_CORPUS_PYTHON) scripts/build_peano_policy_dataset.py \
		"$(PEANO_POLICY_DIR)/raw-traces.jsonl" \
		--metadata "$(PEANO_POLICY_DIR)/session-metadata.jsonl" \
		--output-dir "$(PEANO_POLICY_DIR)"
	$(PEANO_CORPUS_PYTHON) -m training.peano_policy.attest \
		--train "$(PEANO_POLICY_DIR)/train.jsonl" \
		--eval "$(PEANO_POLICY_DIR)/val.jsonl" \
		--output "$(PEANO_POLICY_DIR)/attestation.json"

peano-eval:
	$(PEANO_CORPUS_PYTHON) scripts/eval_peano_policy.py --k 8 --max-steps 16 --seed 20260727

.PHONY: hydra-check hydra-prepare hydra-scale hydra-posttrain-prepare \
	hydra-posttrain-preflight hydra-eval-plan hydra-eval-control hydra-posttrain-ready \
	hydra-posttrain-execute hydra-dev-plan hydra-dev-evaluate hydra-dev-verify \
	hydra-review-plan hydra-review-run hydra-review-verify

# A future source file or unfinished Alpha campaign never expands Hydra
# authority: both the synchronized product DAG gate and epoch freeze bind the
# exact current sealed release before any checked search or training export.
hydra-check:
	python3 scripts/sync_constructive_grand_campaign.py --check --json
	python3 scripts/update_peano_worker_sources.py --check
	bash scripts/update_peano_app_manifest.sh --check
	cd peano-lab/py && PYTHONMALLOC=malloc python3 -m pytest -q -p no:cacheprovider --tb=line \
		tests/test_browser_shell.py \
		tests/test_constructive_campaign_dag.py \
		tests/test_constructive_definition_graph.py \
		tests/test_constructive_next_layer_public_site.py \
		tests/test_constructive_breakthrough_layer_explorer.py \
		tests/test_constructive_breakthrough_publication_v25.py \
		tests/test_deploy_contract.py \
		tests/test_hydra_product_roadmap.py \
		tests/test_lean_selector_ui.py \
		tests/test_lean_strand_service.py \
		tests/test_public_lean_selector.py \
		tests/test_peano_hydra_policy.py \
		tests/test_peano_hydra_runner.py \
		tests/test_peano_hydra_scheduler.py \
		tests/test_peano_hydra_pilot.py \
		tests/test_peano_hydra_epoch.py \
		tests/test_peano_hydra_development.py \
		tests/test_peano_hydra_posttrain.py \
		tests/test_peano_hydra_evaluation.py \
		tests/test_peano_hydra_cluster.py \
		tests/test_peano_hydra_protocol.py \
		tests/test_peano_hydra_benchmark.py \
		tests/test_peano_hydra_symbolic.py \
		tests/test_peano_hydra_frontier.py \
		tests/test_peano_hydra_cold_replay.py \
		tests/test_peano_hydra_conformance.py \
		tests/test_peano_hydra_lineage_review.py \
		tests/test_peano_hydra_reference.py \
		tests/test_peano_hydra_review_runtime.py \
		tests/test_peano_hydra_review_sources.py \
		tests/test_peano_hydra_review.py \
		tests/test_peano_hydra_review_archive.py \
		tests/test_helios_control.py
	PYTHONMALLOC=malloc python3 scripts/prepare_peano_hydra.py --check

hydra-prepare:
	PYTHONMALLOC=malloc python3 scripts/prepare_peano_hydra.py \
		--output-dir "_deploy/hydra" --include-graphs

hydra-scale:
	PYTHONMALLOC=malloc python3 scripts/prepare_peano_hydra.py \
		--output-dir "_deploy/hydra" --include-graphs \
		--catalog-all --catalog-limit "$(HYDRA_CATALOG_LIMIT)" \
		--catalog-max-decisions "$(HYDRA_CATALOG_MAX_DECISIONS)"

hydra-posttrain-prepare:
	PYTHONMALLOC=malloc python3 scripts/prepare_peano_hydra_posttrain.py \
		--source-dir "_deploy/hydra" --output-dir "_deploy/hydra-posttrain"

hydra-posttrain-preflight:
	PYTHONMALLOC=malloc python3 -m training.peano_hydra.posttrain \
		--preflight --preparation-dir "_deploy/hydra-posttrain"

hydra-eval-plan:
	PYTHONMALLOC=malloc python3 scripts/eval_peano_hydra_posttrain.py \
		--preparation-dir "_deploy/hydra-posttrain" --check

hydra-eval-control:
	PYTHONMALLOC=malloc python3 scripts/eval_peano_hydra_posttrain.py \
		--preparation-dir "_deploy/hydra-posttrain" --check --symbolic-controls

hydra-posttrain-ready: hydra-scale
	PYTHONMALLOC=malloc python3 scripts/prepare_peano_hydra_posttrain.py \
		--source-dir "_deploy/hydra" --output-dir "_deploy/hydra-posttrain"
	PYTHONMALLOC=malloc python3 -m training.peano_hydra.posttrain \
		--preflight --preparation-dir "_deploy/hydra-posttrain"
	PYTHONMALLOC=malloc python3 scripts/eval_peano_hydra_posttrain.py \
		--preparation-dir "_deploy/hydra-posttrain" --check --symbolic-controls

# These are model-free public development diagnostics, never a sealed test.
# Reusing an existing output is refused; select a fresh HYDRA_DEV_DIR.
hydra-dev-plan:
	PYTHONMALLOC=malloc python3 scripts/eval_peano_hydra_development.py --plan

hydra-dev-evaluate:
	PYTHONMALLOC=malloc python3 scripts/eval_peano_hydra_development.py \
		--run --output-dir "$(HYDRA_DEV_DIR)"

hydra-dev-verify:
	PYTHONMALLOC=malloc python3 scripts/eval_peano_hydra_development.py \
		--verify "$(HYDRA_DEV_DIR)"

# These targets prepare review evidence; they never grant human approval or
# train a model. The checker requires a real installed binary (not an elan
# shim), and execution refuses to reuse an existing HYDRA_REVIEW_DIR.
hydra-review-plan:
	$(if $(strip $(HYDRA_REVIEW_LEAN)),,$(error Set HYDRA_REVIEW_LEAN=/absolute/path/to/installed/lean; no compiler is inferred or installed))
	PYTHONMALLOC=malloc python3 scripts/check_peano_hydra_review.py \
		--plan --reference-project "$(HYDRA_REVIEW_REFERENCE_PROJECT)" \
		--lean-binary "$(HYDRA_REVIEW_LEAN)" \
		--cold-scope "$(HYDRA_REVIEW_COLD_SCOPE)" \
		--cold-batch-size "$(HYDRA_REVIEW_COLD_BATCH_SIZE)" \
		--cold-wall-budget "$(HYDRA_REVIEW_COLD_WALL_BUDGET)"

hydra-review-run:
	$(if $(strip $(HYDRA_REVIEW_LEAN)),,$(error Set HYDRA_REVIEW_LEAN=/absolute/path/to/installed/lean; no compiler is inferred or installed))
	PYTHONMALLOC=malloc python3 scripts/check_peano_hydra_review.py \
		--run --output-dir "$(HYDRA_REVIEW_DIR)" \
		--reference-project "$(HYDRA_REVIEW_REFERENCE_PROJECT)" \
		--lean-binary "$(HYDRA_REVIEW_LEAN)" \
		--cold-scope "$(HYDRA_REVIEW_COLD_SCOPE)" \
		--cold-batch-size "$(HYDRA_REVIEW_COLD_BATCH_SIZE)" \
		--cold-wall-budget "$(HYDRA_REVIEW_COLD_WALL_BUDGET)"

hydra-review-verify:
	PYTHONMALLOC=malloc python3 scripts/check_peano_hydra_review.py \
		--verify "$(HYDRA_REVIEW_DIR)"

# Training is deliberately separate from all preparation and check targets.
# The runner refuses execution without the verified Alpha handoff, one CUDA
# GPU, pinned Qwen weights, and explicitly bounded rows/tokens/update steps.
hydra-posttrain-execute:
	PYTHONHASHSEED=20260826 PYTHONMALLOC=malloc python3 \
		-m training.peano_hydra.posttrain \
		--execute --preparation-dir "_deploy/hydra-posttrain"

stage: book
	rm -rf $(STAGE) && mkdir -p $(STAGE)
	cp index.html $(STAGE)/index.html
	cp deploy/site.htaccess $(STAGE)/.htaccess
	cp -R assets $(STAGE)/assets
	cp -R book/_build/html $(STAGE)/book
	cp -R slides $(STAGE)/slides
	@echo "Staged site in $(STAGE)"

deploy-site: stage
	rsync -avz --delete $(STAGE)/ $(SERVER):$(SITE)/

stage-proofs: book-proof-explorer-check book-constructive-frontier-explorer book-constructive-next-layer-explorer book-constructive-advanced-layer-explorer book-constructive-transport-layer-explorer book-constructive-milestone-closure-explorer book-constructive-research-layer-explorer book-constructive-breakthrough-layer-explorer book-constructive-second-wave-current-explorer book-constructive-gaussian-factorization-explorer book-constructive-bottom-layer-publication book-constructive-lower-tier-publication
	@test "$$(shasum -a 256 book/_static/pa-proof-explorer/api/corpus.json | cut -d' ' -f1)" = \
		"ebc78a0c16fe6e9123a52363a69929590d8ca875380431776ef0de28b9b1193a" || \
		{ echo "Immutable Alpha parent quadratic-reciprocity evidence corpus changed" >&2; exit 1; }
	@python3 scripts/sync_constructive_grand_campaign.py --check
	@python3 scripts/extend_constructive_gaussian_factorization_campaign.py --check
	rm -rf "$(STAGEPROOFS)"
	mkdir -p "$(STAGEPROOFS)/assets"
	mkdir -p "$(STAGEPROOFS)/grand-campaign"
	mkdir -p "$(STAGEPROOFS)/artifacts"
	mkdir -p "$(STAGEPROOFS)/arithmetic-library"
	mkdir -p "$(STAGEPROOFS)/quadratic-reciprocity/explorer"
	mkdir -p "$(STAGEPROOFS)/bertrand-postulate/explorer"
	cp deploy/proofs/index.html "$(STAGEPROOFS)/index.html"
	cp deploy/proofs/quadratic-reciprocity.html \
		"$(STAGEPROOFS)/quadratic-reciprocity/index.html"
	cp deploy/proofs/bertrand-postulate.html \
		"$(STAGEPROOFS)/bertrand-postulate/index.html"
	cp deploy/proofs/proofs.css "$(STAGEPROOFS)/assets/proofs.css"
	cp deploy/proofs/proofs-og.png "$(STAGEPROOFS)/assets/proofs-og.png"
	cp deploy/proofs/.htaccess "$(STAGEPROOFS)/.htaccess"
	rsync -a --delete deploy/proofs/arithmetic-library/ "$(STAGEPROOFS)/arithmetic-library/"
	rsync -a --delete book/_static/constructive-gaussian-campaign/ \
		"$(STAGEPROOFS)/grand-campaign/"
	cp research/arithmetic-library/artifacts/quadratic-reciprocity-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/quadratic-reciprocity-proof-bundle-v1.json"
	cp research/arithmetic-library/quadratic-reciprocity-closure-receipt.md \
		"$(STAGEPROOFS)/artifacts/quadratic-reciprocity-closure-receipt.md"
	cp research/arithmetic-library/artifacts/supplementary-laws-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/supplementary-laws-proof-bundle-v1.json"
	cp research/arithmetic-library/supplementary-laws-closure-receipt.md \
		"$(STAGEPROOFS)/artifacts/supplementary-laws-closure-receipt.md"
	cp research/arithmetic-library/artifacts/lucas-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/lucas-proof-bundle-v1.json"
	cp research/arithmetic-library/lucas-complete-closure-receipt.md \
		"$(STAGEPROOFS)/artifacts/lucas-complete-closure-receipt.md"
	cp research/arithmetic-library/artifacts/kummer-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/kummer-proof-bundle-v1.json"
	cp research/arithmetic-library/kummer-complete-closure-receipt.md \
		"$(STAGEPROOFS)/artifacts/kummer-complete-closure-receipt.md"
	cp research/arithmetic-library/artifacts/bertrand-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/bertrand-proof-bundle-v1.json"
	cp research/arithmetic-library/bertrand-complete-closure-receipt.md \
		"$(STAGEPROOFS)/artifacts/bertrand-complete-closure-receipt.md"
	cp research/arithmetic-library/artifacts/four-square-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/four-square-proof-bundle-v1.json"
	cp research/arithmetic-library/four-square-complete-closure-receipt.md \
		"$(STAGEPROOFS)/artifacts/four-square-complete-closure-receipt.md"
	cp research/arithmetic-library/artifacts/two-square-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/two-square-proof-bundle-v1.json"
	cp research/arithmetic-library/two-square-complete-closure-receipt.md \
		"$(STAGEPROOFS)/artifacts/two-square-complete-closure-receipt.md"
	cp research/arithmetic-library/artifacts/alpha-v19-residual-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/alpha-v19-residual-proof-bundle-v1.json"
	cp research/arithmetic-library/campaign-residual-closure-receipt.md \
		"$(STAGEPROOFS)/artifacts/campaign-residual-closure-receipt.md"
	cp research/arithmetic-library/artifacts/alpha-v19-campaign-frontier-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/alpha-v19-campaign-frontier-proof-bundle-v1.json"
	cp research/arithmetic-library/alpha-v19-campaign-frontier-closure-receipt.md \
		"$(STAGEPROOFS)/artifacts/alpha-v19-campaign-frontier-closure-receipt.md"
	cp research/arithmetic-library/artifacts/alpha-v20-next-layer-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/alpha-v20-next-layer-proof-bundle-v1.json"
	cp research/arithmetic-library/alpha-v20-next-layer-closure-receipt.md \
		"$(STAGEPROOFS)/artifacts/alpha-v20-next-layer-closure-receipt.md"
	cp research/arithmetic-library/artifacts/alpha-v21-advanced-layer-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/alpha-v21-advanced-layer-proof-bundle-v1.json"
	cp research/arithmetic-library/alpha-v21-advanced-layer-closure-receipt.md \
		"$(STAGEPROOFS)/artifacts/alpha-v21-advanced-layer-closure-receipt.md"
	cp research/arithmetic-library/artifacts/alpha-v22-transport-layer-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/alpha-v22-transport-layer-proof-bundle-v1.json"
	cp research/arithmetic-library/alpha-v22-transport-layer-closure-receipt.md \
		"$(STAGEPROOFS)/artifacts/alpha-v22-transport-layer-closure-receipt.md"
	cp research/arithmetic-library/artifacts/alpha-v23-milestone-closure-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/alpha-v23-milestone-closure-proof-bundle-v1.json"
	cp research/arithmetic-library/alpha-v23-milestone-closure-receipt.md \
		"$(STAGEPROOFS)/artifacts/alpha-v23-milestone-closure-receipt.md"
	cp research/arithmetic-library/artifacts/alpha-v24-research-layer-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/alpha-v24-research-layer-proof-bundle-v1.json"
	cp research/arithmetic-library/alpha-v24-research-layer-receipt.md \
		"$(STAGEPROOFS)/artifacts/alpha-v24-research-layer-receipt.md"
	cp research/arithmetic-library/artifacts/alpha-v25-breakthrough-layer-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/alpha-v25-breakthrough-layer-proof-bundle-v1.json"
	cp research/arithmetic-library/alpha-v25-breakthrough-layer-receipt.md \
		"$(STAGEPROOFS)/artifacts/alpha-v25-breakthrough-layer-receipt.md"
	cp research/arithmetic-library/artifacts/alpha-v26-first-wave-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/alpha-v26-first-wave-proof-bundle-v1.json"
	cp research/arithmetic-library/alpha-v26-first-wave-receipt.md \
		"$(STAGEPROOFS)/artifacts/alpha-v26-first-wave-receipt.md"
	cp research/arithmetic-library/artifacts/alpha-v27-second-wave-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/alpha-v27-second-wave-proof-bundle-v1.json"
	cp research/arithmetic-library/alpha-v27-second-wave-receipt.md \
		"$(STAGEPROOFS)/artifacts/alpha-v27-second-wave-receipt.md"
	cp research/arithmetic-library/artifacts/alpha-v28-lower-layer-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/alpha-v28-lower-layer-proof-bundle-v1.json"
	cp research/arithmetic-library/alpha-v28-lower-layer-receipt.md \
		"$(STAGEPROOFS)/artifacts/alpha-v28-lower-layer-receipt.md"
	cp research/arithmetic-library/artifacts/alpha-v29-priority-layer-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/alpha-v29-priority-layer-proof-bundle-v1.json"
	cp research/arithmetic-library/alpha-v29-priority-layer-receipt.md \
		"$(STAGEPROOFS)/artifacts/alpha-v29-priority-layer-receipt.md"
	cp research/arithmetic-library/artifacts/alpha-v30-gaussian-factorization-proof-bundle-v1.json \
		"$(STAGEPROOFS)/artifacts/alpha-v30-gaussian-factorization-proof-bundle-v1.json"
	cp research/arithmetic-library/alpha-v30-gaussian-factorization-receipt.md \
		"$(STAGEPROOFS)/artifacts/alpha-v30-gaussian-factorization-receipt.md"
	rsync -a --delete --exclude '.DS_Store' \
		book/_static/pa-proof-explorer/ \
		"$(STAGEPROOFS)/quadratic-reciprocity/explorer/"
	rsync -a --delete book/_static/bertrand-proof-explorer/ \
		"$(STAGEPROOFS)/bertrand-postulate/explorer/"
	rsync -a book/_static/constructive-frontier-explorer/assets/ \
		"$(STAGEPROOFS)/assets/"
	rsync -a book/_static/constructive-next-layer-explorer/assets/ \
		"$(STAGEPROOFS)/assets/"
	rsync -a book/_static/constructive-advanced-layer-explorer/assets/ \
		"$(STAGEPROOFS)/assets/"
	rsync -a book/_static/constructive-transport-layer-explorer/assets/ \
		"$(STAGEPROOFS)/assets/"
	rsync -a book/_static/constructive-milestone-closure-explorer/assets/ \
		"$(STAGEPROOFS)/assets/"
	rsync -a book/_static/constructive-research-layer-explorer/assets/ \
		"$(STAGEPROOFS)/assets/"
	rsync -a book/_static/constructive-breakthrough-layer-explorer/assets/ \
		"$(STAGEPROOFS)/assets/"
	rsync -a book/_static/constructive-second-wave-explorer-v30/assets/ \
		"$(STAGEPROOFS)/assets/"
	rsync -a book/_static/constructive-lower-layer-explorer-v30/assets/ \
		"$(STAGEPROOFS)/assets/"
	rsync -a book/_static/constructive-priority-layer-explorer-v30/assets/ \
		"$(STAGEPROOFS)/assets/"
	rsync -a book/_static/constructive-gaussian-factorization-explorer/assets/ \
		"$(STAGEPROOFS)/assets/"
	mkdir -p "$(STAGEPROOFS)/supplementary-laws" \
		"$(STAGEPROOFS)/kummer" "$(STAGEPROOFS)/two-squares" \
		"$(STAGEPROOFS)/four-squares" "$(STAGEPROOFS)/lucas" \
		"$(STAGEPROOFS)/pythagorean-fermat-four" \
		"$(STAGEPROOFS)/polynomial-horner" "$(STAGEPROOFS)/matrix-dot-product" \
		"$(STAGEPROOFS)/bertrand-prime-chains" "$(STAGEPROOFS)/continued-fractions" \
		"$(STAGEPROOFS)/matrix-coded-products" "$(STAGEPROOFS)/euclidean-complexity" \
		"$(STAGEPROOFS)/binary-modular-exponentiation" \
		"$(STAGEPROOFS)/binary-length" "$(STAGEPROOFS)/euclidean-gcd-transport" \
		"$(STAGEPROOFS)/binary-modular-execution" \
		"$(STAGEPROOFS)/euclidean-logarithmic-bound" \
		"$(STAGEPROOFS)/binary-digit-extraction" \
		"$(STAGEPROOFS)/primes-three-mod-four" \
		"$(STAGEPROOFS)/matrix-determinant-minors" \
		"$(STAGEPROOFS)/polynomial-hensel" \
		"$(STAGEPROOFS)/generalized-crt-fold" \
		"$(STAGEPROOFS)/matrix-cofactor-expansion" \
		"$(STAGEPROOFS)/polynomial-taylor-hensel" \
		"$(STAGEPROOFS)/generalized-crt-compatibility" \
		"$(STAGEPROOFS)/integer-linear-algebra" "$(STAGEPROOFS)/hensel-lifting" \
		"$(STAGEPROOFS)/generalized-crt" "$(STAGEPROOFS)/multinomial-kummer" \
		"$(STAGEPROOFS)/prime-count-chebyshev" "$(STAGEPROOFS)/cornacchia" \
		"$(STAGEPROOFS)/cauchy-davenport" \
		"$(STAGEPROOFS)/arithmetic-foundations" "$(STAGEPROOFS)/prime-enumeration" \
		"$(STAGEPROOFS)/gaussian-integers" "$(STAGEPROOFS)/eisenstein-integers" \
		"$(STAGEPROOFS)/prime-valuation-support" \
		"$(STAGEPROOFS)/best-approximation" \
		"$(STAGEPROOFS)/totient-products" \
		"$(STAGEPROOFS)/squarefree-kernels" \
		"$(STAGEPROOFS)/exponent-lifting" \
		"$(STAGEPROOFS)/gaussian-factorization"
	rsync -a --delete book/_static/constructive-frontier-explorer/supplementary-laws/ \
		"$(STAGEPROOFS)/supplementary-laws/"
	rsync -a --delete book/_static/constructive-frontier-explorer/kummer/ \
		"$(STAGEPROOFS)/kummer/"
	rsync -a --delete book/_static/constructive-frontier-explorer/two-squares/ \
		"$(STAGEPROOFS)/two-squares/"
	rsync -a --delete book/_static/constructive-frontier-explorer/four-squares/ \
		"$(STAGEPROOFS)/four-squares/"
	rsync -a --delete book/_static/constructive-frontier-explorer/lucas/ \
		"$(STAGEPROOFS)/lucas/"
	rsync -a --delete book/_static/constructive-frontier-explorer/pythagorean-fermat-four/ \
		"$(STAGEPROOFS)/pythagorean-fermat-four/"
	rsync -a --delete book/_static/constructive-next-layer-explorer/polynomial-horner/ \
		"$(STAGEPROOFS)/polynomial-horner/"
	rsync -a --delete book/_static/constructive-next-layer-explorer/matrix-dot-product/ \
		"$(STAGEPROOFS)/matrix-dot-product/"
	rsync -a --delete book/_static/constructive-next-layer-explorer/bertrand-prime-chains/ \
		"$(STAGEPROOFS)/bertrand-prime-chains/"
	rsync -a --delete book/_static/constructive-next-layer-explorer/continued-fractions/ \
		"$(STAGEPROOFS)/continued-fractions/"
	rsync -a --delete book/_static/constructive-advanced-layer-explorer/matrix-coded-products/ \
		"$(STAGEPROOFS)/matrix-coded-products/"
	rsync -a --delete book/_static/constructive-advanced-layer-explorer/euclidean-complexity/ \
		"$(STAGEPROOFS)/euclidean-complexity/"
	rsync -a --delete book/_static/constructive-advanced-layer-explorer/binary-modular-exponentiation/ \
		"$(STAGEPROOFS)/binary-modular-exponentiation/"
	rsync -a --delete book/_static/constructive-transport-layer-explorer/binary-length/ \
		"$(STAGEPROOFS)/binary-length/"
	rsync -a --delete book/_static/constructive-transport-layer-explorer/euclidean-gcd-transport/ \
		"$(STAGEPROOFS)/euclidean-gcd-transport/"
	rsync -a --delete book/_static/constructive-transport-layer-explorer/binary-modular-execution/ \
		"$(STAGEPROOFS)/binary-modular-execution/"
	rsync -a --delete book/_static/constructive-milestone-closure-explorer/euclidean-logarithmic-bound/ \
		"$(STAGEPROOFS)/euclidean-logarithmic-bound/"
	rsync -a --delete book/_static/constructive-milestone-closure-explorer/binary-digit-extraction/ \
		"$(STAGEPROOFS)/binary-digit-extraction/"
	rsync -a --delete book/_static/constructive-milestone-closure-explorer/primes-three-mod-four/ \
		"$(STAGEPROOFS)/primes-three-mod-four/"
	rsync -a --delete book/_static/constructive-research-layer-explorer/matrix-determinant-minors/ \
		"$(STAGEPROOFS)/matrix-determinant-minors/"
	rsync -a --delete book/_static/constructive-research-layer-explorer/polynomial-hensel/ \
		"$(STAGEPROOFS)/polynomial-hensel/"
	rsync -a --delete book/_static/constructive-research-layer-explorer/generalized-crt-fold/ \
		"$(STAGEPROOFS)/generalized-crt-fold/"
	rsync -a --delete book/_static/constructive-breakthrough-layer-explorer/matrix-cofactor-expansion/ \
		"$(STAGEPROOFS)/matrix-cofactor-expansion/"
	rsync -a --delete book/_static/constructive-breakthrough-layer-explorer/polynomial-taylor-hensel/ \
		"$(STAGEPROOFS)/polynomial-taylor-hensel/"
	rsync -a --delete book/_static/constructive-breakthrough-layer-explorer/generalized-crt-compatibility/ \
		"$(STAGEPROOFS)/generalized-crt-compatibility/"
	rsync -a --delete book/_static/constructive-second-wave-explorer-v30/integer-linear-algebra/ \
		"$(STAGEPROOFS)/integer-linear-algebra/"
	rsync -a --delete book/_static/constructive-second-wave-explorer-v30/hensel-lifting/ \
		"$(STAGEPROOFS)/hensel-lifting/"
	rsync -a --delete book/_static/constructive-second-wave-explorer-v30/generalized-crt/ \
		"$(STAGEPROOFS)/generalized-crt/"
	rsync -a --delete book/_static/constructive-second-wave-explorer-v30/multinomial-kummer/ \
		"$(STAGEPROOFS)/multinomial-kummer/"
	rsync -a --delete book/_static/constructive-second-wave-explorer-v30/prime-count-chebyshev/ \
		"$(STAGEPROOFS)/prime-count-chebyshev/"
	rsync -a --delete book/_static/constructive-second-wave-explorer-v30/cornacchia/ \
		"$(STAGEPROOFS)/cornacchia/"
	rsync -a --delete book/_static/constructive-second-wave-explorer-v30/cauchy-davenport/ \
		"$(STAGEPROOFS)/cauchy-davenport/"
	rsync -a --delete book/_static/constructive-lower-layer-explorer-v30/arithmetic-foundations/ \
		"$(STAGEPROOFS)/arithmetic-foundations/"
	rsync -a --delete book/_static/constructive-lower-layer-explorer-v30/prime-enumeration/ \
		"$(STAGEPROOFS)/prime-enumeration/"
	rsync -a --delete book/_static/constructive-lower-layer-explorer-v30/gaussian-integers/ \
		"$(STAGEPROOFS)/gaussian-integers/"
	rsync -a --delete book/_static/constructive-lower-layer-explorer-v30/eisenstein-integers/ \
		"$(STAGEPROOFS)/eisenstein-integers/"
	rsync -a --delete book/_static/constructive-priority-layer-explorer-v30/prime-valuation-support/ \
		"$(STAGEPROOFS)/prime-valuation-support/"
	rsync -a --delete book/_static/constructive-priority-layer-explorer-v30/best-approximation/ \
		"$(STAGEPROOFS)/best-approximation/"
	rsync -a --delete book/_static/constructive-priority-layer-explorer-v30/totient-products/ \
		"$(STAGEPROOFS)/totient-products/"
	rsync -a --delete book/_static/constructive-priority-layer-explorer-v30/squarefree-kernels/ \
		"$(STAGEPROOFS)/squarefree-kernels/"
	rsync -a --delete book/_static/constructive-priority-layer-explorer-v30/exponent-lifting/ \
		"$(STAGEPROOFS)/exponent-lifting/"
	rsync -a --delete book/_static/constructive-gaussian-factorization-explorer/gaussian-factorization/ \
		"$(STAGEPROOFS)/gaussian-factorization/"
	mkdir -p "$(STAGEPROOFS)/checkpoints"
	rsync -a --delete book/_static/constructive-bottom-layer-publication/ \
		"$(STAGEPROOFS)/checkpoints/"
	mkdir -p "$(STAGEPROOFS)/checkpoints/lower-tier"
	rsync -a --delete book/_static/constructive-lower-tier-publication/ \
		"$(STAGEPROOFS)/checkpoints/lower-tier/"
	python3 scripts/stage_public_checkpoint_navigation.py --root "$(STAGEPROOFS)"
	python3 scripts/stage_lower_tier_checkpoint_navigation.py --root "$(STAGEPROOFS)"
	python3 scripts/build_constructive_completed_lower_hub_v31.py --check
	python3 scripts/stage_completed_lower_publication_v31.py --root "$(STAGEPROOFS)"
	python3 scripts/stage_public_lean_selector.py \
		--root "$(STAGEPROOFS)" \
		--api-url "$(PEANO_LEAN_PUBLIC_API)"
	python3 scripts/stage_completed_lower_publication_v31.py --root "$(STAGEPROOFS)" \
		--check --api-url "$(PEANO_LEAN_PUBLIC_API)"
	@echo "Staged proof explorers in $(STAGEPROOFS)"

stage-lean-api:
	rm -rf "$(STAGELEANAPI)"
	mkdir -p "$(STAGELEANAPI)"
	cp deploy/lean-api/.htaccess "$(STAGELEANAPI)/.htaccess"
	cp deploy/lean-api/index.php "$(STAGELEANAPI)/index.php"
	cp scripts/public_lean_mailbox.py "$(STAGELEANAPI)/broker.py"
	@echo "Staged same-origin Lean proof gateway in $(STAGELEANAPI)"

deploy-lean-api: stage-lean-api
	ssh "$(SERVER)" 'mkdir -p ~/public_html/api/lean-strands ~/.hydra-lean-mailbox && chmod 755 ~/public_html/api ~/public_html/api/lean-strands && chmod 700 ~/.hydra-lean-mailbox'
	rsync -avz "$(STAGELEANAPI)/.htaccess" "$(STAGELEANAPI)/index.php" $(SERVER):$(LEANAPI)/
	rsync -avz "$(STAGELEANAPI)/broker.py" $(SERVER):~/.hydra-lean-mailbox/broker.py
	ssh "$(SERVER)" 'chmod 600 ~/.hydra-lean-mailbox/broker.py'
	@echo "Deployed public Lean proof gateway → $(PEANO_LEAN_PUBLIC_ORIGIN)/api/lean-strands/"

deploy-proofs: stage-proofs deploy-lean-api
	rsync -avz --delete "$(STAGEPROOFS)/" $(SERVER):$(PROOFS)/
	@echo "Deployed proof explorers → https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/"

deploy-lean-public: deploy-proofs
	@echo "Public proof explorers and their isolated Lean gateway are deployed"

# The lab IS the worker+self-hosted build (promoted 2026-07-24).
deploy-lab:
	rm -rf $(STAGENEXT) && mkdir -p $(STAGENEXT)
	cp lab-lambda/index.html $(STAGENEXT)/index.html
	cp lab-lambda/worker.js  $(STAGENEXT)/worker.js
	cp lab-lambda/.htaccess  $(STAGENEXT)/.htaccess
	rsync -a --exclude '__pycache__' --exclude 'tests' lab-lambda/py/ $(STAGENEXT)/py/
	rsync -a lab-lambda/vendor/ $(STAGENEXT)/vendor/
	rsync -avz --delete $(STAGENEXT)/ $(SERVER):$(LAB)/
	@echo "Deployed lab → https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda/"

# Staging channel: identical assembly, deployed to /lab-lambda-next/
deploy-lab-next:
	rm -rf $(STAGENEXT) && mkdir -p $(STAGENEXT)
	cp lab-lambda/index.html $(STAGENEXT)/index.html
	cp lab-lambda/worker.js  $(STAGENEXT)/worker.js
	cp lab-lambda/.htaccess  $(STAGENEXT)/.htaccess
	rsync -a --exclude '__pycache__' --exclude 'tests' lab-lambda/py/ $(STAGENEXT)/py/
	rsync -a lab-lambda/vendor/ $(STAGENEXT)/vendor/
	rsync -avz --delete $(STAGENEXT)/ $(SERVER):$(LABNEXT)/
	@echo "Deployed staging → https://bnaskrecki.faculty.wmi.amu.edu.pl/lab-lambda-next/"

# Peano Lab uses its own local vendor mirror.  Its staged release namespaces
# are served by `make peano-serve`; scripts/fetch_vendor.sh creates both mirrors.
stage-peano:
	@bash scripts/verify_peano_vendor_manifest.sh >/dev/null || \
		{ echo "Peano Lab vendor verification failed; rerun: bash scripts/fetch_vendor.sh" >&2; exit 1; }
	@bash scripts/update_peano_app_manifest.sh --check >/dev/null || \
		{ echo "Peano Lab application manifest is stale; run scripts/update_peano_app_manifest.sh" >&2; exit 1; }
	@test "$$(shasum -a 256 peano-lab/APP_MANIFEST.sha256 | cut -c1-12)" = "$(patsubst a-%,%,$(PEANOAPPID))" || \
		{ echo "PEANOAPPID does not match APP_MANIFEST.sha256" >&2; exit 1; }
	@grep -Fq 'const APP_ROOT="releases/$(PEANOAPPID)/";' peano-lab/index.html || \
		{ echo "index.html APP_ROOT does not match PEANOAPPID" >&2; exit 1; }
	@grep -Eq 'const BUILD="[^"]+";' peano-lab/index.html || \
		{ echo "index.html has no human-facing BUILD" >&2; exit 1; }
	rm -rf "$(STAGEPEANO)" && mkdir -p "$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts"
	cp peano-lab/index.html "$(STAGEPEANO)/index.html"
	cp peano-lab/.htaccess  "$(STAGEPEANO)/.htaccess"
	cp peano-lab/worker.js "$(STAGEPEANO)/releases/$(PEANOAPPID)/worker.js"
	cp peano-lab/APP_MANIFEST.sha256 "$(STAGEPEANO)/releases/$(PEANOAPPID)/APP_MANIFEST.sha256"
	cp research/arithmetic-library/artifacts/quadratic-reciprocity-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/quadratic-reciprocity-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/supplementary-laws-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/supplementary-laws-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/lucas-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/lucas-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/kummer-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/kummer-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/bertrand-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/bertrand-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/four-square-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/four-square-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/two-square-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/two-square-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/alpha-v19-residual-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/alpha-v19-residual-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/alpha-v19-campaign-frontier-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/alpha-v19-campaign-frontier-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/alpha-v20-next-layer-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/alpha-v20-next-layer-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/alpha-v21-advanced-layer-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/alpha-v21-advanced-layer-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/alpha-v22-transport-layer-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/alpha-v22-transport-layer-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/alpha-v23-milestone-closure-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/alpha-v23-milestone-closure-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/alpha-v24-research-layer-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/alpha-v24-research-layer-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/alpha-v25-breakthrough-layer-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/alpha-v25-breakthrough-layer-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/alpha-v26-first-wave-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/alpha-v26-first-wave-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/alpha-v27-second-wave-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/alpha-v27-second-wave-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/alpha-v28-lower-layer-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/alpha-v28-lower-layer-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/alpha-v29-priority-layer-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/alpha-v29-priority-layer-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/alpha-v30-gaussian-factorization-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/alpha-v30-gaussian-factorization-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/bottom-layer-euler-units-proof-bundle-v2.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/bottom-layer-euler-units-proof-bundle-v2.json"
	cp research/arithmetic-library/artifacts/bottom-layer-prime-fields-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/bottom-layer-prime-fields-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/bottom-layer-mobius-values-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/bottom-layer-mobius-values-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/bottom-layer-signed-sums-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/bottom-layer-signed-sums-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/lower-tier-divisor-sums-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/lower-tier-divisor-sums-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/lower-tier-signed-weighted-sums-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/lower-tier-signed-weighted-sums-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/lower-tier-prime-field-polynomials-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/lower-tier-prime-field-polynomials-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/lower-continuation-divisor-involutions-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/lower-continuation-divisor-involutions-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/lower-continuation-mobius-divisor-cancellation-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/lower-continuation-mobius-divisor-cancellation-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/lower-continuation-rectangular-sums-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/lower-continuation-rectangular-sums-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/lower-continuation-polynomial-products-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/lower-continuation-polynomial-products-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/dirichlet-finite-support-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/dirichlet-finite-support-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/dirichlet-convolution-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/dirichlet-convolution-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/dirichlet-fubini-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/dirichlet-fubini-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/dirichlet-units-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/dirichlet-units-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/mobius-inversion-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/mobius-inversion-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/dirichlet-signed-units-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/dirichlet-signed-units-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/dirichlet-triangular-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/dirichlet-triangular-proof-bundle-v1.json"
	cp research/arithmetic-library/artifacts/dirichlet-inverses-proof-bundle-v1.json \
		"$(STAGEPEANO)/releases/$(PEANOAPPID)/proof-artifacts/dirichlet-inverses-proof-bundle-v1.json"
	rsync -a --delete --exclude '/tests/***' --exclude '__pycache__/' --exclude '.pytest_cache/' --include '*/' --include '*.py' --exclude '*' peano-lab/py/ "$(STAGEPEANO)/releases/$(PEANOAPPID)/py/"
	rsync -a --delete peano-lab/vendor/ "$(STAGEPEANO)/vendor/"
	@echo "Staged Peano Lab in $(STAGEPEANO)"

# Production channel.  Promotion policy is documented in PLAN/09_peano_lab.md.
deploy-peano: stage-peano
	rsync -avz "$(STAGEPEANO)/.htaccess" "$(STAGEPEANO)/vendor" "$(STAGEPEANO)/releases" $(SERVER):$(PEANO)/
	rsync -avz "$(STAGEPEANO)/index.html" $(SERVER):$(PEANO)/index.html
	@echo "Deployed Peano Lab → https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab/"

# Staging channel: byte-for-byte the same assembled tree, under /peano-lab-next/.
deploy-peano-next: stage-peano
	rsync -avz "$(STAGEPEANO)/.htaccess" "$(STAGEPEANO)/vendor" "$(STAGEPEANO)/releases" $(SERVER):$(PEANONEXT)/
	rsync -avz "$(STAGEPEANO)/index.html" $(SERVER):$(PEANONEXT)/index.html
	@echo "Deployed Peano Lab staging → https://bnaskrecki.faculty.wmi.amu.edu.pl/peano-lab-next/"

deploy: deploy-site deploy-lab
	@echo "Deployed:  https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026  +  /lab-lambda"

clean:
	rm -rf book/_build _deploy
	rm -rf artifacts/lean/.lake artifacts/lean-fta/.lake
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
