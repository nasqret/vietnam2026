"""Static contracts for the Peano Lab browser shell.

These tests intentionally avoid running a browser. They pin the safety and
deployment properties that are easy to lose during an otherwise cosmetic edit.
"""

from __future__ import annotations

import hashlib
import json
from html import unescape
import re
from pathlib import Path
import subprocess

from peano_lab.kernel.formulas import parse_formula
from peano_lab.kernel.terms import parse_term


LAB = Path(__file__).resolve().parents[2]
INDEX = (LAB / "index.html").read_text(encoding="utf-8")
WORKER = (LAB / "worker.js").read_text(encoding="utf-8")
HTACCESS = (LAB / ".htaccess").read_text(encoding="utf-8")
APP_MANIFEST = LAB / "APP_MANIFEST.sha256"
QR_BUNDLE_SOURCE = (
    LAB.parent
    / "research"
    / "arithmetic-library"
    / "artifacts"
    / "quadratic-reciprocity-proof-bundle-v1.json"
)
QR_BUNDLE_RELEASE_PATH = "proof-artifacts/quadratic-reciprocity-proof-bundle-v1.json"
PROOF_BUNDLE_FILENAMES = (
    "quadratic-reciprocity-proof-bundle-v1.json",
    "supplementary-laws-proof-bundle-v1.json",
    "lucas-proof-bundle-v1.json",
    "kummer-proof-bundle-v1.json",
    "bertrand-proof-bundle-v1.json",
    "four-square-proof-bundle-v1.json",
    "two-square-proof-bundle-v1.json",
    "alpha-v19-residual-proof-bundle-v1.json",
    "alpha-v19-campaign-frontier-proof-bundle-v1.json",
    "alpha-v20-next-layer-proof-bundle-v1.json",
    "alpha-v21-advanced-layer-proof-bundle-v1.json",
    "alpha-v22-transport-layer-proof-bundle-v1.json",
    "alpha-v23-milestone-closure-proof-bundle-v1.json",
    "alpha-v24-research-layer-proof-bundle-v1.json",
    "alpha-v25-breakthrough-layer-proof-bundle-v1.json",
    "alpha-v26-first-wave-proof-bundle-v1.json",
    "alpha-v27-second-wave-proof-bundle-v1.json",
    "alpha-v28-lower-layer-proof-bundle-v1.json",
    "alpha-v29-priority-layer-proof-bundle-v1.json",
    "alpha-v30-gaussian-factorization-proof-bundle-v1.json",
    "bottom-layer-euler-units-proof-bundle-v2.json",
    "bottom-layer-prime-fields-proof-bundle-v1.json",
    "bottom-layer-mobius-values-proof-bundle-v1.json",
    "bottom-layer-signed-sums-proof-bundle-v1.json",
    "lower-tier-divisor-sums-proof-bundle-v1.json",
    "lower-tier-signed-weighted-sums-proof-bundle-v1.json",
    "lower-tier-prime-field-polynomials-proof-bundle-v1.json",
    "lower-continuation-divisor-involutions-proof-bundle-v1.json",
    "lower-continuation-mobius-divisor-cancellation-proof-bundle-v1.json",
    "lower-continuation-rectangular-sums-proof-bundle-v1.json",
    "lower-continuation-polynomial-products-proof-bundle-v1.json",
    "dirichlet-finite-support-proof-bundle-v1.json",
    "dirichlet-convolution-proof-bundle-v1.json",
    "dirichlet-fubini-proof-bundle-v1.json",
    "dirichlet-units-proof-bundle-v1.json",
    "mobius-inversion-proof-bundle-v1.json",
    "dirichlet-signed-units-proof-bundle-v1.json",
    "dirichlet-triangular-proof-bundle-v1.json",
    "dirichlet-inverses-proof-bundle-v1.json",
)
PROOF_BUNDLE_SOURCES = {
    f"proof-artifacts/{filename}": (
        LAB.parent / "research" / "arithmetic-library" / "artifacts" / filename
    )
    for filename in PROOF_BUNDLE_FILENAMES
}


def test_shell_has_its_own_build_history_and_deep_link_contracts() -> None:
    assert re.search(r'const BUILD="[^"\n]+"', INDEX)
    assert 'const HISTORY_KEY="peanoLabHistory"' in INDEX
    assert 'new URLSearchParams(location.search).get("cmd")' in INDEX
    assert 'const APP_ROOT="releases/a-' in INDEX
    assert 'new Worker(APP_ROOT+"worker.js")' in INDEX
    assert "worker.terminate()" in INDEX
    assert "function sanitizeCommand(command)" in INDEX
    assert '.replace(/[\\x00-\\x1f\\x7f-\\x9f]/g," ")' in INDEX
    assert ".slice(0,MAX_INPUT)" in INDEX
    assert ".map(sanitizeCommand).slice(-200)" in INDEX


def test_all_runtime_assets_are_self_hosted() -> None:
    asset_urls = re.findall(
        r'<(?:script|link)\b[^>]+(?:src|href)="([^"]+)"',
        INDEX,
    )
    assert asset_urls
    assert all(re.match(r"vendor/v-[0-9a-f]{12,64}/", url) for url in asset_urls)
    vendor_ids = set(re.findall(r"vendor/(v-[0-9a-f]{12,64})/", INDEX + WORKER))
    assert vendor_ids == {"v-85fb3352e49c"}
    assert 'const VENDOR_ROOT = "../../vendor/v-85fb3352e49c/"' in WORKER
    assert 'importScripts(VENDOR_ROOT + "pyodide/pyodide.js")' in WORKER
    assert 'indexURL: VENDOR_ROOT + "pyodide/"' in WORKER
    assert "cdn.jsdelivr" not in INDEX + WORKER
    assert "unpkg.com" not in INDEX + WORKER


def test_application_release_is_content_addressed_and_complete() -> None:
    lines = APP_MANIFEST.read_text(encoding="utf-8").splitlines()
    entries = {}
    for line in lines:
        digest, relative_path = line.split(maxsplit=1)
        entries[relative_path] = digest

    package_files = {
        path.relative_to(LAB).as_posix()
        for path in (LAB / "py").rglob("*.py")
        if "tests" not in path.relative_to(LAB / "py").parts
    }
    assert set(entries) == package_files | {"worker.js"} | set(PROOF_BUNDLE_SOURCES)
    for relative_path, expected in entries.items():
        source = PROOF_BUNDLE_SOURCES.get(relative_path, LAB / relative_path)
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        assert actual == expected

    release = "a-" + hashlib.sha256(APP_MANIFEST.read_bytes()).hexdigest()[:12]
    assert f'const APP_ROOT="releases/{release}/"' in INDEX


def test_worker_mounts_the_complete_python_surface() -> None:
    listed = set(re.findall(r'"(py/[^"]+\.py)"', WORKER))
    package_files = {
        path.relative_to(LAB).as_posix()
        for path in (LAB / "py" / "peano_lab").rglob("*.py")
    }
    assert listed == package_files | {"py/driver.py"}
    assert all((LAB / relative_path).is_file() for relative_path in listed)
    assert "driver.run_line(line)" in WORKER
    assert "driver.run_line_result(line)" in WORKER
    assert 'failed = result.failed === true' in WORKER
    assert "driver.banner()" in WORKER
    for relative_path in PROOF_BUNDLE_SOURCES:
        assert f'"{relative_path}"' in WORKER
    assert "const artifactsPromise = fetchProofArtifacts()" in WORKER
    assert "return { relativePath, ok: true, response };" in WORKER
    assert "new Uint8Array(await response.arrayBuffer())" in WORKER
    assert "entry.response = null;" in WORKER


def test_worker_source_inventory_is_reproducible() -> None:
    updater = LAB.parent / "scripts" / "update_peano_worker_sources.py"
    result = subprocess.run(
        ["python3", str(updater), "--check"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "source inventory verified" in result.stdout


def test_worker_mounts_every_current_alpha_provider_with_exact_bundle_case() -> None:
    assert len(PROOF_BUNDLE_FILENAMES) == 20
    assert len(set(PROOF_BUNDLE_FILENAMES)) == 20
    assert all(name == name.lower() for name in PROOF_BUNDLE_FILENAMES)
    for module in (
        "prime_valuation_support_candidate",
        "continued_fraction_approximation_candidate",
        "continued_fraction_convergents_candidate",
        "euler_totient_count_candidate",
        "euler_totient_interval_candidate",
        "euler_totient_prime_step_candidate",
        "euler_totient_algebra_candidate",
        "euler_totient_product_candidate",
        "squarefree_decomposition_candidate",
        "perfect_power_profile_candidate",
        "odd_prime_lte_candidate",
        "gaussian_ring_candidate",
        "gaussian_divisibility_candidate",
        "gaussian_gcd_candidate",
        "gaussian_factor_search_candidate",
        "gaussian_factorization_candidate",
        "gaussian_product_reindex_candidate",
        "gaussian_factor_permutation_candidate",
        "campaign_priority_layer_closure",
        "campaign_gaussian_factorization_closure",
        "alpha_enrollment_v29",
        "alpha_enrollment_v30",
        "editions_v29",
        "editions_v30",
        "alpha_enrollment_v31",
        "campaign_completed_lower_closure",
        "editions_v31",
    ):
        assert f'"py/peano_lab/library/{module}.py"' in WORKER


def test_shell_exposes_accessible_proof_controls_and_ladder_shortcuts() -> None:
    assert 'role="status"' in INDEX
    assert 'aria-live="polite"' in INDEX
    assert 'aria-label="Stop the running proof command"' in INDEX
    assert 'aria-keyshortcuts="Escape Control+C"' in INDEX
    assert 'aria-label="Peano Lab proof terminal"' in INDEX
    assert "screenReaderMode:true" in INDEX
    for command in (
        "pa axioms",
        "pa tactic induction",
        "pa kb de-bruijn-criterion",
        "pa tutorial add_comm",
        "pa tutorial norm_num",
        "pa prove 2 * 3 = 6",
        "pa prove forall n. 0 + n = n",
        "pa prove forall n m. S(n) + m = S(n + m)",
        "pa prove forall n m. n + m = m + n",
    ):
        assert f'data-cmd="{command}"' in INDEX


def test_shell_connects_checked_alpha_research_to_multiscale_proof_atlas() -> None:
    assert 'aria-label="Course and research navigation"' in INDEX
    channel = json.loads((LAB.parent / "artifacts/peano-library/channels-v31.json").read_bytes())["channels"]["alpha"]
    revision = channel["artifact_sha256"][:12]
    assert channel["theorem_count"] == channel["checked_use_count"] == 3796
    assert f'<a href="/proofs/?v={revision}">Proof library</a>' in INDEX
    assert f'<a href="/proofs/grand-campaign/?v={revision}">Research atlas</a>' in INDEX
    assert "Alpha: 3,796 proofs" in INDEX
    assert '<span class="lbl">research:</span>' in INDEX
    assert 'data-cmd="pa lib alpha odd_prime_lifting_the_exponent" disabled>odd-prime LTE</button>' in INDEX
    assert 'data-cmd="pa lib alpha positive_squarefree_kernel_and_power_profile" disabled>positive squarefree &amp; power profiles</button>' in INDEX
    for command in (
        "pa lib alpha",
        "pa lib alpha totient_euler_product_formula",
        "pa lib alpha positive_squarefree_kernel_and_power_profile",
        "pa lib alpha odd_prime_lifting_the_exponent",
        "pa lib alpha continued_fraction_convergent_best_approximation",
        "pa lib alpha gaussian_gcd_bezout_exists",
        "pa lib alpha gaussian_unique_prime_factorization",
        "pa lib alpha foundation_division_exists_unique",
        "pa lib alpha prime_factorization_exists_unique_up_to_permutation",
        "pa lib alpha gaussian_euclidean_division_exists",
        "pa lib alpha eisenstein_euclidean_division_exists",
        "pa lib alpha first_primes_list_exists",
        "pa lib alpha signed_recursive_determinant_exists_unique",
        "pa lib alpha rectangular_matrix_rank_exists_unique",
        "pa lib alpha integer_polynomial_prime_simple_root_lifts_all_positive_powers",
        "pa lib alpha crt_pairwise_compatible_prefix_normalized_exists_unique",
        "pa lib alpha multinomial_kummer_carry_valuation",
        "pa lib alpha prime_count_chebyshev_bounds",
        "pa lib alpha cornacchia_prime_two_squares_complete",
        "pa lib alpha prime_cauchy_davenport_sumset_bound",
        "pa lib alpha coprime_square_product_factors",
        "pa lib alpha pythagorean_positive_primitive_classification",
        "pa lib alpha fermat_four_positive_sum_not_square",
        "pa lib alpha signed_matrix_cofactor_family_and_fold_exists",
        "pa lib alpha beta_horner_hensel_lift_exists",
        "pa lib alpha crt_merge_compatible_prefix_canonical_exists_unique",
        "pa lib alpha beta_signed_matrix_minor_exists",
        "pa lib alpha beta_horner_derivative_exists_unique",
        "pa lib alpha crt_pairwise_coprime_prefix_canonical_exists_unique",
        "pa lib alpha infinitely_many_primes_one_mod_four",
        "pa lib alpha infinitely_many_primes_three_mod_four",
        "pa lib alpha euclidean_gcd_execution_logarithmic_bound",
        "pa lib alpha binary_modular_execution_logarithmic_bound",
        "pa lib alpha linear_congruence_solvable_iff_gcd_divides",
        "pa lib alpha prime_is_two_squares_iff_two_or_one_mod_four",
        "pa lib alpha beta_horner_eval_exists",
        "pa lib alpha beta_dot_product_exists_unique",
        "pa lib alpha central_binom_prime_divisor_multiplicity_one_exists",
        "pa lib alpha iterated_bertrand_prime_chain_exists",
        "pa lib alpha continued_fraction_positive_exists",
    ):
        assert f'data-cmd="{command}"' in INDEX


def test_shell_exposes_accessible_bounded_multiline_proof_paste() -> None:
    assert 'id="paste-proof"' in INDEX
    assert 'id="paste-proof-dialog"' in INDEX
    assert 'aria-labelledby="paste-proof-title"' in INDEX
    assert '<label for="paste-proof-input">Complete proof script</label>' in INDEX
    assert 'id="paste-proof-input"' in INDEX
    assert 'maxlength="100000"' in INDEX
    assert 'id="paste-proof-error" role="alert" aria-live="polite"' in INDEX
    assert 'id="run-pasted-proof"' in INDEX
    assert "const MAX_PASTE_CHARS=100000" in INDEX
    assert "const MAX_PASTE_LINES=256" in INDEX
    assert "const MAX_INPUT=8192" in INDEX
    assert "8,192 characters per command" in INDEX
    assert "beginning with <code>pa prove …</code> and ending with <code>qed</code>" in INDEX
    assert 'pasteDialog.addEventListener("close",restorePasteFocus)' in INDEX
    assert "pasteInput.focus()" in INDEX
    assert 'pasteInput.addEventListener("paste",handlePasteInput)' in INDEX


def test_tactic_completion_discovers_surface_checked_arithmetic() -> None:
    match = re.search(r"const TACTICS=\[(.*?)\];", INDEX)
    assert match is not None
    assert '"use"' in match.group(1).split(",")
    assert '"have"' in match.group(1).split(",")
    assert '"suffices"' in match.group(1).split(",")
    assert '"norm_num"' in match.group(1).split(",")
    assert '"ring"' in match.group(1).split(",")
    assert '"compact_arith"' in match.group(1).split(",")
    assert '"compact_arith?"' in INDEX
    assert '"script"' in INDEX
    assert "const ROOT_COMPLETIONS=Array.from(new Set(COMMANDS.concat(TACTICS)))" in INDEX
    assert "if(words.length<=1)return ROOT_COMPLETIONS" in INDEX


def test_quick_button_examples_use_real_surface_syntax() -> None:
    theorem_sources = re.findall(r'data-cmd="pa prove ([^"]+)"', INDEX)
    assert len(theorem_sources) >= 4
    for source in theorem_sources:
        parse_formula(unescape(source))

    term_sources = re.findall(r'data-cmd="pa (?:eval|simp) ([^"]+)"', INDEX)
    assert len(term_sources) >= 2
    for source in term_sources:
        parse_term(unescape(source))


def test_apache_contract_serves_wasm_and_redirects_proxy_http() -> None:
    assert "AddType application/wasm .wasm" in HTACCESS
    assert "AddType font/woff2 .woff2" in HTACCESS
    assert "%{HTTP:X-Forwarded-Proto} =http" in HTACCESS


def test_apache_contract_negotiates_compression_without_recompressing_archives() -> None:
    assert "BROTLI_COMPRESS" in HTACCESS
    assert "DEFLATE" in HTACCESS
    assert "application/wasm" in HTACCESS
    assert "text/x-python" in HTACCESS
    assert "Accept-Encoding" in HTACCESS
    assert "(?!0(\\.0*)?" in HTACCESS
    assert "application/zip" not in HTACCESS
    assert "font/woff2" not in "\n".join(
        line for line in HTACCESS.splitlines() if "AddOutputFilterByType" in line
    )


def test_apache_contract_caches_only_versioned_assets_and_never_the_page() -> None:
    assert 'Header set Cache-Control "no-cache"' in HTACCESS
    assert "max-age=31536000, immutable" in HTACCESS
    assert "/releases/a-[0-9a-f]{12,64}/" in HTACCESS
    assert "/vendor/v-[0-9a-f]{12,64}/" in HTACCESS
    assert "QUERY_STRING" not in HTACCESS
    assert 'Header always set Cache-Control "no-store"' in HTACCESS
    assert "%{REQUEST_STATUS} >= 400" in HTACCESS
    assert "%{REQUEST_STATUS} >= 200 && %{REQUEST_STATUS} <= 299" in HTACCESS
    assert "%{REQUEST_STATUS} == 304" in HTACCESS
    assert '<Files "index.html">' in HTACCESS
    assert "no-store, no-cache, must-revalidate, max-age=0" in HTACCESS


def test_worker_fetches_sources_concurrently_but_mounts_deterministically() -> None:
    harness = Path(__file__).with_name("worker_boot_harness.js")
    result = subprocess.run(
        ["node", str(harness), str(LAB / "worker.js")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_multiline_paste_is_validated_sequential_and_stop_safe() -> None:
    harness = Path(__file__).with_name("multiline_paste_harness.js")
    result = subprocess.run(
        ["node", str(harness), str(LAB / "index.html")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    assert 'term.element.addEventListener("paste",handleTerminalPaste,true)' in INDEX
    assert "event.clipboardData.getData(\"text/plain\")" in INDEX
    assert "event.preventDefault();event.stopImmediatePropagation()" in INDEX
    assert "if(looksLikeMultilinePaste(data)){beginPastedProof(data,false);return;}" in INDEX
    assert "activeGeneration===generation" in INDEX
    assert "typeof result.failed!==\"boolean\"" in INDEX

    paste_runner = INDEX[
        INDEX.index("async function runPreparedPaste") :
        INDEX.index("function sanitizeCommand")
    ]
    assert "downloadProofScript" not in paste_runner
    assert "history.push(command.text)" in paste_runner
    assert "saveHistory()" in paste_runner
    assert "term.focus()" in paste_runner


def test_script_download_is_validated_local_and_requires_direct_keyboard_intent() -> None:
    harness = Path(__file__).with_name("script_download_harness.js")
    result = subprocess.run(
        ["node", str(harness), str(LAB / "index.html")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert 'trimmed==="script download"' in INDEX
    assert "allowDownload===true" in INDEX
    assert "submit(false)" in INDEX  # quick buttons and ?cmd= deep links
    assert 'case "\\r":submit(true)' in INDEX
    assert 'link.download="peano-lab-proof.pa"' in INDEX
    assert 'type:"text/plain;charset=utf-8"' in INDEX
    assert "URL.revokeObjectURL(url)" in INDEX
    assert ".innerHTML" not in INDEX


def test_browser_javascript_is_syntactically_valid() -> None:
    inline_scripts = re.findall(r"<script>(.*?)</script>", INDEX, re.DOTALL)
    assert len(inline_scripts) == 1
    for source in (WORKER, inline_scripts[0]):
        result = subprocess.run(
            ["node", "--check", "-"],
            input=source,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr


def test_fatal_worker_errors_settle_pending_commands_and_require_reload() -> None:
    assert (
        'pending.forEach(function(resolve){resolve({out:"",failed:true,download:null});});pending.clear();'
        in INDEX
    )
    assert 'if(worker){worker.terminate();worker=null;}' in INDEX
    assert "Reload to retry" in INDEX


def test_busy_terminal_has_a_keyboard_stop_path_and_bounded_input() -> None:
    assert "function stopWorker()" in INDEX
    assert 'stopBtn.addEventListener("click",stopWorker)' in INDEX
    assert "term.attachCustomKeyEventHandler" in INDEX
    assert 'event.key==="Escape"' in INDEX
    assert 'event.ctrlKey&&event.key.toLowerCase()==="c"' in INDEX
    assert "MAX_INPUT-buffer.length" in INDEX
