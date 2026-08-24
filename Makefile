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
STAGE     := _deploy/vietnam2026
STAGENEXT := _deploy/lab-lambda-next
PEANO_CORPUS_PYTHON ?= python3
PEANO_POLICY_DIR ?= data/peano-policy-v2
PEANO_POLICY_PILOT_DIR ?= data/peano-policy-pilot-v1
PEANO_POLICY_ROWS ?= 10000
PEANO_TRAIN_JOB ?= 217859
PEANO_TRAIN_DASHBOARD_PORT ?= 8766
# This path is a deletion target in `stage-peano`; command-line assignments
# must not be able to widen it beyond the repository's dedicated stage tree.
override STAGEPEANO := _deploy/peano-lab
override STAGEPROOFS := _deploy/proofs
override PEANOAPPID := a-526f19ff3b30

.PHONY: help book book-atlas book-proof-explorer book-bertrand-proof-explorer book-bertrand-defined-explorer book-constructive-frontier-explorer lean lean-fta peano-library-alpha peano-library-alpha-check peano-library-alpha-v2 peano-library-alpha-v2-check peano-library-alpha-v3 peano-library-alpha-v3-check peano-library-alpha-v4 peano-library-alpha-v4-check peano-library-alpha-v5 peano-library-alpha-v5-check peano-library-alpha-v6 peano-library-alpha-v6-check peano-library-alpha-v7 peano-library-alpha-v7-check peano-library-alpha-v8 peano-library-alpha-v8-check peano-library-alpha-v9 peano-library-alpha-v9-check peano-library-alpha-v10 peano-library-alpha-v10-check peano-library-alpha-v11 peano-library-alpha-v11-check peano-library-alpha-v12 peano-library-alpha-v12-check peano-library-alpha-v13 peano-library-alpha-v13-check peano-library-alpha-v14 peano-library-alpha-v14-check peano-library-alpha-v15 peano-library-alpha-v15-check peano-library-channels peano-library-channels-check peano-library-channels-v2 peano-library-channels-v2-check peano-library-channels-v3 peano-library-channels-v3-check peano-library-channels-v4 peano-library-channels-v4-check peano-library-channels-v5 peano-library-channels-v5-check peano-library-channels-v6 peano-library-channels-v6-check peano-library-channels-v7 peano-library-channels-v7-check peano-library-channels-v8 peano-library-channels-v8-check peano-library-channels-v9 peano-library-channels-v9-check peano-library-channels-v10 peano-library-channels-v10-check peano-library-channels-v11 peano-library-channels-v11-check peano-library-channels-v12 peano-library-channels-v12-check peano-library-channels-v13 peano-library-channels-v13-check peano-library-channels-v14 peano-library-channels-v14-check peano-library-channels-v15 peano-library-channels-v15-check ha-number-theory-check ha-constructive-frontier-check ha-k3b-cell-history-check ha-k3b-list-lookup-check lab-serve peano-serve peano-training-dashboard peano-corpus peano-corpus-smoke peano-policy-pilot peano-policy-data peano-eval stage \
	stage-peano stage-proofs deploy-site deploy-lab deploy-lab-next deploy-peano \
	deploy-peano-next deploy-proofs \
	deploy clean

help:
	@echo "Targets:"
	@echo "  make book         build the JupyterBook (book/_build/html)"
	@echo "  make book-atlas   regenerate the checked arithmetic theorem atlas"
	@echo "  make book-proof-explorer  regenerate the static PA proof explorer"
	@echo "  make book-bertrand-proof-explorer  regenerate the full Bertrand map"
	@echo "  make book-bertrand-defined-explorer  regenerate the readable Bertrand map"
	@echo "  make book-constructive-frontier-explorer  regenerate six evidence-honest frontier proof maps"
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
	@echo "  make ha-number-theory-check  validate strict-HA admission, gcd, and signed normalization tranches"
	@echo "  make ha-constructive-frontier-check  replay ordered stages 1-6 in bounded isolated proof processes"
	@echo "  make ha-k3b-cell-history-check  run the lightweight Alpha K3B RFC/body checks"
	@echo "  make ha-k3b-list-lookup-check  run the Alpha K3B ListAt surface checks"
	@echo "  make lab-serve    serve lab-lambda locally on :8001"
	@echo "  make peano-serve serve the staged Peano Lab locally on :8002"
	@echo "  make peano-training-dashboard  observe WMI job $(PEANO_TRAIN_JOB) on :$(PEANO_TRAIN_DASHBOARD_PORT)"
	@echo "  make peano-corpus reproduce the leakage-safe Peano train/val release"
	@echo "  make peano-corpus-smoke  run the all-ladder M9 generation/export smoke"
	@echo "  make peano-policy-pilot  build the checked M19 pilot policy dataset"
	@echo "  make peano-policy-v2-data  build+attest $(PEANO_POLICY_ROWS) model-v2 policy rows"
	@echo "  make peano-policy-data   compatibility alias for peano-policy-v2-data"
	@echo "  make peano-eval   run the deterministic kernel-judged random baseline"
	@echo "  make stage        assemble _deploy/vietnam2026 (landing + book + slides)"
	@echo "  make deploy-site  rsync the site to $(SITE)"
	@echo "  make deploy-lab   rsync the browser lab to $(LAB)"
	@echo "  make deploy-lab-next  deploy the Web Worker preview to $(LABNEXT)"
	@echo "  make deploy-peano  rsync Peano Lab to $(PEANO)"
	@echo "  make deploy-peano-next  deploy Peano Lab staging to $(PEANONEXT)"
	@echo "  make stage-proofs  assemble the standalone proof-explorer families"
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

book-constructive-frontier-explorer:
	python3 scripts/build_constructive_frontier_explorer.py

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

lab-serve:
	@echo "→ http://localhost:8001/  (Ctrl-C to stop)"
	cd lab-lambda && python3 -m http.server 8001

peano-serve: stage-peano
	@echo "→ http://localhost:8002/  (Ctrl-C to stop)"
	cd "$(STAGEPEANO)" && python3 -m http.server 8002

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

stage-proofs: book-proof-explorer book-constructive-frontier-explorer
	rm -rf "$(STAGEPROOFS)"
	mkdir -p "$(STAGEPROOFS)/assets"
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
	rsync -a --delete --exclude '.DS_Store' \
		book/_static/pa-proof-explorer/ \
		"$(STAGEPROOFS)/quadratic-reciprocity/explorer/"
	rsync -a --delete book/_static/bertrand-proof-explorer/ \
		"$(STAGEPROOFS)/bertrand-postulate/explorer/"
	rsync -a book/_static/constructive-frontier-explorer/assets/ \
		"$(STAGEPROOFS)/assets/"
	mkdir -p "$(STAGEPROOFS)/supplementary-laws" \
		"$(STAGEPROOFS)/kummer" "$(STAGEPROOFS)/two-squares" \
		"$(STAGEPROOFS)/four-squares" "$(STAGEPROOFS)/lucas" \
		"$(STAGEPROOFS)/pythagorean-fermat-four"
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
	@echo "Staged proof explorers in $(STAGEPROOFS)"

deploy-proofs: stage-proofs
	rsync -avz --delete "$(STAGEPROOFS)/" $(SERVER):$(PROOFS)/
	@echo "Deployed proof explorers → https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/"

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
	rm -rf "$(STAGEPEANO)" && mkdir -p "$(STAGEPEANO)/releases/$(PEANOAPPID)"
	cp peano-lab/index.html "$(STAGEPEANO)/index.html"
	cp peano-lab/.htaccess  "$(STAGEPEANO)/.htaccess"
	cp peano-lab/worker.js "$(STAGEPEANO)/releases/$(PEANOAPPID)/worker.js"
	cp peano-lab/APP_MANIFEST.sha256 "$(STAGEPEANO)/releases/$(PEANOAPPID)/APP_MANIFEST.sha256"
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
