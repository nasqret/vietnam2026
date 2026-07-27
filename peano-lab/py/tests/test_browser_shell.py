"""Static contracts for the Peano Lab browser shell.

These tests intentionally avoid running a browser. They pin the safety and
deployment properties that are easy to lose during an otherwise cosmetic edit.
"""

from __future__ import annotations

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


def test_shell_has_its_own_build_history_and_deep_link_contracts() -> None:
    assert re.search(r'const BUILD="[^"\n]+"', INDEX)
    assert 'const HISTORY_KEY="peanoLabHistory"' in INDEX
    assert 'new URLSearchParams(location.search).get("cmd")' in INDEX
    assert 'new Worker("worker.js?v="+encodeURIComponent(BUILD))' in INDEX
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
    assert all(url.startswith("vendor/") for url in asset_urls)
    assert 'importScripts("vendor/pyodide/pyodide.js")' in WORKER
    assert 'indexURL: "vendor/pyodide/"' in WORKER
    assert "cdn.jsdelivr" not in INDEX + WORKER
    assert "unpkg.com" not in INDEX + WORKER


def test_worker_mounts_the_complete_python_surface() -> None:
    listed = set(re.findall(r'"(py/[^"]+\.py)"', WORKER))
    package_files = {
        path.relative_to(LAB).as_posix()
        for path in (LAB / "py" / "peano_lab").rglob("*.py")
    }
    assert listed == package_files | {"py/driver.py"}
    assert all((LAB / relative_path).is_file() for relative_path in listed)
    assert "driver.run_line(line)" in WORKER
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


def test_tactic_completion_discovers_surface_checked_arithmetic() -> None:
    match = re.search(r"const TACTICS=\[(.*?)\];", INDEX)
    assert match is not None
    assert '"use"' in match.group(1).split(",")
    assert '"norm_num"' in match.group(1).split(",")
    assert '"ring"' in match.group(1).split(",")
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
    assert 'pending.forEach(function(resolve){resolve("");});pending.clear();' in INDEX
    assert 'if(worker){worker.terminate();worker=null;}' in INDEX
    assert "Reload to retry" in INDEX


def test_busy_terminal_has_a_keyboard_stop_path_and_bounded_input() -> None:
    assert "function stopWorker()" in INDEX
    assert 'stopBtn.addEventListener("click",stopWorker)' in INDEX
    assert "term.attachCustomKeyEventHandler" in INDEX
    assert 'event.key==="Escape"' in INDEX
    assert 'event.ctrlKey&&event.key.toLowerCase()==="c"' in INDEX
    assert "MAX_INPUT-buffer.length" in INDEX
