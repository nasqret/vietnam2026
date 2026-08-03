"use strict";
/*
 * Peano Lab evaluation worker.
 *
 * Pyodide, the tactic engine, and the independent PA kernel all run off the
 * main thread. Terminating this worker is therefore a real Stop operation: a
 * divergent search cannot leave the page unresponsive.
 *
 * Protocol:
 *   main -> worker : {type: "init", build}
 *                    {type: "run", id, line}
 *   worker -> main : {type: "boot", msg}
 *                    {type: "ready", banner}
 *                    {type: "error", msg}
 *                    {type: "result", id, out, failed, download: null|string}
 */

const PY_FILES = [
  "py/peano_lab/__init__.py",
  "py/peano_lab/batch.py",
  "py/peano_lab/engine/__init__.py",
  "py/peano_lab/engine/compact_arith.py",
  "py/peano_lab/engine/decide.py",
  "py/peano_lab/engine/induction.py",
  "py/peano_lab/engine/norm_num.py",
  "py/peano_lab/engine/proof_reduction.py",
  "py/peano_lab/engine/rewrite.py",
  "py/peano_lab/engine/ring.py",
  "py/peano_lab/engine/search.py",
  "py/peano_lab/engine/state.py",
  "py/peano_lab/engine/tacticals.py",
  "py/peano_lab/engine/tactics.py",
  "py/peano_lab/engine/trace.py",
  "py/peano_lab/experimental/__init__.py",
  "py/peano_lab/experimental/closed_proof_dag.py",
  "py/peano_lab/experimental/layered_cut_bundle.py",
  "py/peano_lab/experimental/quadratic_reciprocity_layered.py",
  "py/peano_lab/kernel/__init__.py",
  "py/peano_lab/kernel/checker.py",
  "py/peano_lab/kernel/formulas.py",
  "py/peano_lab/kernel/proofs.py",
  "py/peano_lab/kernel/subst.py",
  "py/peano_lab/kernel/terms.py",
  "py/peano_lab/library/__init__.py",
  "py/peano_lab/library/candidate_validation.py",
  "py/peano_lab/library/defined_edition.py",
  "py/peano_lab/library/defined_syntax.py",
  "py/peano_lab/library/distinct_primes_nondivisibility_candidate.py",
  "py/peano_lab/library/eisenstein_division_threshold_candidate.py",
  "py/peano_lab/library/eisenstein_fubini_row_decomposition_candidate.py",
  "py/peano_lab/library/eisenstein_fubini_total_candidate.py",
  "py/peano_lab/library/eisenstein_initial_segment_count_candidate.py",
  "py/peano_lab/library/eisenstein_lattice_orientation_candidate.py",
  "py/peano_lab/library/eisenstein_outer_sum_bridge_candidate.py",
  "py/peano_lab/library/eisenstein_quotient_bound_candidate.py",
  "py/peano_lab/library/eisenstein_quotient_sum_identity_candidate.py",
  "py/peano_lab/library/eisenstein_rectangle_count_candidate.py",
  "py/peano_lab/library/eisenstein_remainder_nonzero_candidate.py",
  "py/peano_lab/library/eisenstein_row_indicator_candidate.py",
  "py/peano_lab/library/eisenstein_row_quotient_candidate.py",
  "py/peano_lab/library/eisenstein_scaled_division_candidate.py",
  "py/peano_lab/library/eisenstein_transposed_cell_candidate.py",
  "py/peano_lab/library/eisenstein_transposed_column_candidate.py",
  "py/peano_lab/library/eisenstein_transposed_column_count_candidate.py",
  "py/peano_lab/library/eisenstein_transposed_outer_cell_candidate.py",
  "py/peano_lab/library/euler_criterion_arbitrary_candidate.py",
  "py/peano_lab/library/euler_criterion_bounded_candidate.py",
  "py/peano_lab/library/euler_criterion_residue_candidate.py",
  "py/peano_lab/library/euler_nonresidue_endpoint_candidate.py",
  "py/peano_lab/library/euler_pair_product_candidate.py",
  "py/peano_lab/library/euler_scaled_inverse_candidate.py",
  "py/peano_lab/library/euler_scaled_inverse_prefix_candidate.py",
  "py/peano_lab/library/euler_scaled_inverse_prefix_extensional_candidate.py",
  "py/peano_lab/library/euler_scaled_pair_order_entrance_candidate.py",
  "py/peano_lab/library/euler_scaled_pair_order_iteration_candidate.py",
  "py/peano_lab/library/fermat_endpoints_candidate.py",
  "py/peano_lab/library/fermat_product_balance_candidate.py",
  "py/peano_lab/library/fermat_residue_map_candidate.py",
  "py/peano_lab/library/fermat_residue_product_candidate.py",
  "py/peano_lab/library/fermat_residue_reindex_candidate.py",
  "py/peano_lab/library/fermat_scale_product_candidate.py",
  "py/peano_lab/library/finite_bitcount_complement_candidate.py",
  "py/peano_lab/library/finite_bitcount_theorems.py",
  "py/peano_lab/library/finite_congruence_theorems.py",
  "py/peano_lab/library/finite_division_prefix_candidate.py",
  "py/peano_lab/library/finite_factorial_theorems.py",
  "py/peano_lab/library/finite_fold_surface.py",
  "py/peano_lab/library/finite_fold_theorems.py",
  "py/peano_lab/library/finite_omission_candidate.py",
  "py/peano_lab/library/finite_permutation_theorems.py",
  "py/peano_lab/library/finite_pointwise_mul_product_candidate.py",
  "py/peano_lab/library/finite_pointwise_mul_recode_candidate.py",
  "py/peano_lab/library/finite_prime_product_coprime_candidate.py",
  "py/peano_lab/library/finite_product_permutation_theorems.py",
  "py/peano_lab/library/finite_product_reindex_candidate.py",
  "py/peano_lab/library/finite_product_reindex_support.py",
  "py/peano_lab/library/finite_range_theorems.py",
  "py/peano_lab/library/finite_repeat_sum_candidate.py",
  "py/peano_lab/library/finite_sum_permutation_candidate.py",
  "py/peano_lab/library/finite_sum_pointwise_add_candidate.py",
  "py/peano_lab/library/finite_sum_pointwise_mod_candidate.py",
  "py/peano_lab/library/finite_sum_reindex_candidate.py",
  "py/peano_lab/library/finite_sum_theorems.py",
  "py/peano_lab/library/finite_sum_transport_candidate.py",
  "py/peano_lab/library/gauss_count_sum_parity_candidate.py",
  "py/peano_lab/library/gauss_eisenstein_data_candidate.py",
  "py/peano_lab/library/gauss_eisenstein_pointwise_candidate.py",
  "py/peano_lab/library/gauss_eisenstein_sum_candidate.py",
  "py/peano_lab/library/gauss_half_range.py",
  "py/peano_lab/library/gauss_lemma_arbitrary_candidate.py",
  "py/peano_lab/library/gauss_lemma_bounded_candidate.py",
  "py/peano_lab/library/gauss_lemma_endpoint_candidate.py",
  "py/peano_lab/library/gauss_magnitude_coprime_candidate.py",
  "py/peano_lab/library/gauss_magnitude_permutation_candidate.py",
  "py/peano_lab/library/gauss_magnitude_product_candidate.py",
  "py/peano_lab/library/gauss_product_composition_candidate.py",
  "py/peano_lab/library/gauss_sign_bridge.py",
  "py/peano_lab/library/gauss_sign_factor_recode_candidate.py",
  "py/peano_lab/library/gauss_sign_product_candidate.py",
  "py/peano_lab/library/gauss_signed_division_alignment_candidate.py",
  "py/peano_lab/library/gauss_signed_half_candidate.py",
  "py/peano_lab/library/gauss_signed_pointwise_product_candidate.py",
  "py/peano_lab/library/gauss_signed_prefix_candidate.py",
  "py/peano_lab/library/ha_canonical_congruence_candidate.py",
  "py/peano_lab/library/ha_canonical_gcd_candidate.py",
  "py/peano_lab/library/ha_canonical_remainder_candidate.py",
  "py/peano_lab/library/ha_modular_inverse_candidate.py",
  "py/peano_lab/library/layered_replay.py",
  "py/peano_lab/library/lean.py",
  "py/peano_lab/library/parity.py",
  "py/peano_lab/library/parity_mod_two_candidate.py",
  "py/peano_lab/library/parity_odd_division_candidate.py",
  "py/peano_lab/library/parity_odd_half_mod_four_candidate.py",
  "py/peano_lab/library/parity_sum_classification_candidate.py",
  "py/peano_lab/library/power_algebra_theorems.py",
  "py/peano_lab/library/power_congruence_theorems.py",
  "py/peano_lab/library/qr_bounded_units.py",
  "py/peano_lab/library/qr_prime_units.py",
  "py/peano_lab/library/qr_small_moduli.py",
  "py/peano_lab/library/quadratic_reciprocity_candidate.py",
  "py/peano_lab/library/quadratic_reciprocity_conditional_candidate.py",
  "py/peano_lab/library/quadratic_reciprocity_parity_candidate.py",
  "py/peano_lab/library/quadratic_reciprocity_stack.py",
  "py/peano_lab/library/quadratic_reciprocity_stack_runtime.py",
  "py/peano_lab/library/quadratic_residue_surface.py",
  "py/peano_lab/library/quadratic_residue_theorems.py",
  "py/peano_lab/library/signed_division_parity_bridge_candidate.py",
  "py/peano_lab/library/theorems.py",
  "py/peano_lab/library/wilson_endpoint_restoration_candidate.py",
  "py/peano_lab/library/wilson_inverse_endpoints_candidate.py",
  "py/peano_lab/library/wilson_inverse_involution_candidate.py",
  "py/peano_lab/library/wilson_inverse_orbit_candidate.py",
  "py/peano_lab/library/wilson_inverse_point_candidate.py",
  "py/peano_lab/library/wilson_inverse_prefix_candidate.py",
  "py/peano_lab/library/wilson_pair_order_candidate.py",
  "py/peano_lab/library/wilson_pair_order_induction_candidate.py",
  "py/peano_lab/library/wilson_pair_order_iteration_candidate.py",
  "py/peano_lab/library/wilson_pair_order_paired_iteration_candidate.py",
  "py/peano_lab/library/wilson_pair_product_candidate.py",
  "py/peano_lab/library/wilson_square_one_candidate.py",
  "py/peano_lab/library/wilson_successor_lift_candidate.py",
  "py/peano_lab/library/wilson_terminal_product_candidate.py",
  "py/peano_lab/ui/__init__.py",
  "py/peano_lab/ui/data_kb.py",
  "py/peano_lab/ui/data_library.py",
  "py/peano_lab/ui/data_tactics.py",
  "py/peano_lab/ui/data_tutorials.py",
  "py/peano_lab/ui/panels.py",
  "py/peano_lab/ui/prove.py",
  "py/peano_lab/ui/tutorial.py",
  "py/driver.py",
];

// This namespace is derived from the pinned vendor manifest.  It is part of
// the URL, rather than only a query string, because Pyodide constructs the
// URLs for its own .wasm and standard-library files from indexURL.
const VENDOR_ROOT = "../../vendor/v-85fb3352e49c/";

let runLine = null;
let runLineResult = null;
let banner = null;
let takeDownload = null;

async function fetchPythonSources() {
  return Promise.all(PY_FILES.map(async (relativePath) => {
    try {
      const response = await fetch(relativePath);
      if (!response.ok) {
        return {
          relativePath,
          ok: false,
          message: "could not load " + relativePath + " (" + response.status + ")",
        };
      }
      return { relativePath, ok: true, source: await response.text() };
    } catch (_error) {
      return {
        relativePath,
        ok: false,
        message: "could not load " + relativePath + " (network error)",
      };
    }
  }));
}

async function boot(build) {
  try {
    postMessage({ type: "boot", msg: "loading Python and prover sources (self-hosted)…" });
    // scripts/fetch_vendor.sh pins and fetches this local runtime. No CDN is
    // consulted by the browser, so the lab also works on an isolated network.
    importScripts(VENDOR_ROOT + "pyodide/pyodide.js");

    // Start the large runtime first, then overlap it with all small source
    // transfers. Promise.all retains PY_FILES order; each task returns an
    // envelope instead of rejecting, so the first reported failure is also
    // deterministic in PY_FILES order rather than network-completion order.
    const pyodidePromise = loadPyodide({ indexURL: VENDOR_ROOT + "pyodide/" });
    const sourcesPromise = fetchPythonSources();
    const pyodide = await pyodidePromise;
    const sources = await sourcesPromise;
    const failure = sources.find((entry) => !entry.ok);
    if (failure) throw new Error(failure.message);

    postMessage({ type: "boot", msg: "mounting the Peano kernel and tactic engine…" });
    for (const entry of sources) {
      const relativePath = entry.relativePath;
      const destination = "/lab/" + relativePath.replace(/^py\//, "");
      pyodide.FS.mkdirTree(destination.slice(0, destination.lastIndexOf("/")));
      pyodide.FS.writeFile(destination, entry.source);
    }

    pyodide.runPython("import sys; sys.path.insert(0, '/lab')");
    const driver = pyodide.pyimport("driver");
    runLine = function (line) { return driver.run_line(line); };
    runLineResult = function (line) {
      return JSON.parse(String(driver.run_line_result(line)));
    };
    banner = function () { return driver.banner(); };
    takeDownload = function () { return driver.take_download(); };
    postMessage({ type: "ready", banner: String(banner()) });
  } catch (error) {
    postMessage({ type: "error", msg: (error && error.message) ? error.message : String(error) });
  }
}

onmessage = function (event) {
  const message = event.data || {};
  if (message.type === "init") {
    boot(message.build);
    return;
  }
  if (message.type === "run") {
    let output = "";
    let failed = false;
    let download = null;
    try {
      if (runLineResult) {
        const result = runLineResult(message.line);
        output = String(result.out === undefined ? "" : result.out);
        failed = result.failed === true;
      } else {
        output = runLine
          ? String(runLine(message.line))
          : "\x1b[93mThe engine is still starting — try again in a moment.\x1b[0m";
        failed = true;
      }
      if (takeDownload) {
        const body = String(takeDownload());
        download = body || null;
      }
    } catch (error) {
      output = "\x1b[91m" + ((error && error.message) ? error.message : String(error)) + "\x1b[0m";
      failed = true;
    }
    postMessage({ type: "result", id: message.id, out: output, failed: failed, download: download });
  }
};
