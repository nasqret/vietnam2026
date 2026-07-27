"""Static contracts for the Peano Lab browser shell.

These tests intentionally avoid running a browser. They pin the safety and
deployment properties that are easy to lose during an otherwise cosmetic edit.
"""

from __future__ import annotations

import hashlib
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
    assert set(entries) == package_files | {"worker.js"}
    for relative_path, expected in entries.items():
        actual = hashlib.sha256((LAB / relative_path).read_bytes()).hexdigest()
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
