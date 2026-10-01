#!/usr/bin/env python3
"""Bounded Chrome smoke checks; never uses the user's browser profile."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "book/_static/constructive-sqrt2-power-campaign"
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", choices=(
        "https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/sqrt2-power/",),
        help="Check the deployed campaign instead of the local snapshot.")
    parser.add_argument("--screenshots", type=Path)
    parser.add_argument("--output", type=Path,
                        help="Write an append-only browser validation report.")
    parser.add_argument("--route", action="append",
                        choices=("landing", "overview", "definitions", "future", "atlas", "results", "wave", "local-definitions", "rational", "signed",
                                 "frontier", "gap", "separation", "norm-product", "convolution", "quadratic-definitions", "convolution-definitions",
                                 "norm-transport", "rational-norm-product", "signed-product",
                                 "quadratic-nonzero", "quadratic-trace", "quadratic-trace-definitions"),
                        help="Validate only these routes (default: all twenty-three).")
    args = parser.parse_args()
    if not CHROME.is_file():
        raise SystemExit("Chrome unavailable; browser checks not performed")
    if args.output and (args.output.exists() or args.output.is_symlink()):
        raise SystemExit("a new browser report path is required")
    if args.screenshots:
        args.screenshots.mkdir(parents=True, exist_ok=True)
    routes = [
        ("landing", "index.html", None),
        ("overview", "map.html?target=IR072", "IR072"),
        ("definitions", "map.html?target=IR072&view=prerequisites&definitions=1", "IR072"),
        ("future", "map.html?target=TR006&view=neighborhood", "TR006"),
        ("atlas", "grand-campaign/index.html?view=goal&focus=G121", "G121"),
        ("results", "pilot-results.html", None),
        ("wave", "wave-results.html", None),
        ("local-definitions", "local-definitions.html", None),
        ("rational", "checked/RF003.html", None),
        ("signed", "checked/SN001.html", None),
        ("frontier", "arithmetic-frontier.html", None),
        ("gap", "checked/NG001.html", None),
        ("separation", "checked/SN002.html", None),
        ("norm-product", "checked/SN003.html", None),
        ("convolution", "checked/CV001.html", None),
        ("quadratic-definitions", "quadratic-definitions.html", None),
        ("convolution-definitions", "convolution-definitions.html", None),
        ("norm-transport", "checked/RN001.html", None),
        ("rational-norm-product", "checked/RN002.html", None),
        ("signed-product", "checked/SI001.html", None),
        ("quadratic-nonzero", "checked/QN001.html", None),
        ("quadratic-trace", "checked/QF001.html", None),
        ("quadratic-trace-definitions", "quadratic-trace-definitions.html", None),
    ]
    if args.route:
        routes = [row for row in routes if row[0] in args.route]
    started = time.monotonic()
    results = []
    screenshot_routes = {"landing", "overview", "atlas", "results", "wave", "local-definitions", "rational", "signed",
                         "frontier", "separation", "norm-product", "convolution", "quadratic-definitions", "convolution-definitions",
                         "norm-transport", "rational-norm-product", "signed-product",
                         "quadratic-nonzero", "quadratic-trace", "quadratic-trace-definitions"}
    for label, route, target in routes:
        remaining = 90 - (time.monotonic() - started)
        if remaining <= 0:
            raise SystemExit("aggregate browser deadline exhausted")
        with tempfile.TemporaryDirectory(prefix="sqrt2-campaign-chrome-") as profile:
            viewport = "1500,2200" if label == "frontier" else "1500,1300"
            argv = [str(CHROME), "--headless", "--disable-gpu", "--no-first-run",
                    "--no-default-browser-check", "--disable-background-networking",
                    "--disable-extensions", "--disable-component-update",
                    "--user-data-dir=" + profile, "--window-size=" + viewport,
                    "--virtual-time-budget=1500", "--dump-dom"]
            if args.screenshots and label in screenshot_routes:
                argv.append("--screenshot=" + str((args.screenshots / (label + ".png")).resolve()))
            path, _, query = route.partition("?")
            page_url = args.base_url + path if args.base_url else (SITE / path).as_uri()
            argv.append(page_url + ("?" + query if query else ""))
            forced_cleanup = False
            # Chrome helper processes can retain inherited pipe handles on
            # macOS. Regular temp files keep capture independent of their EOF.
            with tempfile.TemporaryFile(mode="w+") as out, tempfile.TemporaryFile(mode="w+") as err:
                process = subprocess.Popen(argv, stdout=out, stderr=err,
                                           text=True, start_new_session=True)
                deadline = time.monotonic() + min(16, remaining)
                try:
                    # Do not spend the whole timeout waiting for macOS helpers
                    # after Chrome has already emitted the completed document.
                    while process.poll() is None and time.monotonic() < deadline:
                        rendered = b"</html>" in os.pread(
                            out.fileno(), os.fstat(out.fileno()).st_size, 0)
                        screenshot_ready = (not args.screenshots or
                            label not in screenshot_routes or
                            (args.screenshots / (label + ".png")).is_file())
                        if rendered and screenshot_ready:
                            break
                        time.sleep(0.1)
                    forced_cleanup = process.poll() is None
                finally:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=2)
                out.seek(0); err.seek(0)
                output, errors = out.read(), err.read()
            if process.returncode != 0 and not forced_cleanup:
                raise SystemExit("browser failed: " + label + "\n" + errors[-2000:])
            if forced_cleanup and "</html>" not in output:
                raise SystemExit("browser render timed out: " + label + "\n" + errors[-2000:])
            if label == "landing":
                assert "Planning, not proof evidence" in output
                assert "pilot-results.html" in output
            elif label == "results":
                assert "8 local arithmetic leaves passed fresh ordinary-HA replay" in output
                assert "0 irrationality parent obligations closed" in output
                assert "P10 unresolved" in output
                assert 'id="P01"' in output and 'id="P12"' in output
                assert 'href="evidence/P07-native.json.gz"' in output
            elif label == "wave":
                assert "Irrationality remains open" in output
                assert "Twice-square zero theorem" in output and "IR016" in output
                assert "HA + freshly compiled Lean" in output
                assert "13/16 exact pieces" in output and "Open / attempt failed" in output
            elif label == "local-definitions":
                assert 'id="graph-ND0382"' in output and 'id="graph-ND0387"' in output
                assert 'href="checked/RF003.html"' in output
                assert "No new kernel symbol or axiom" in output
            elif label == "rational":
                assert "RF003" in output and "Named statement" in output
                assert "Fresh HA and independently compiled Lean checks" in output
                assert 'href="../local-definitions.html#ND0383"' in output
                assert "not an Alpha/Stable admission" in output
            elif label == "signed":
                assert "SN001" in output and "Named statement" in output
                assert "Fresh HA and independently compiled Lean checks" in output
                assert 'href="../reused-definitions/ND0157.html"' in output
                assert "full irrationality argument remain open" in output
            elif label == "frontier":
                assert 'id="frontier-SN002"' in output and 'id="frontier-CV001"' in output
                assert 'id="frontier-RN001"' in output and 'id="frontier-SI001"' in output
                assert 'id="frontier-QN001"' in output and 'id="frontier-QF001"' in output
                assert 'stroke-dasharray="6 5"' in output
                assert 'href="checked/SN003.html"' in output
                assert "Solid arrows are actual direct root dependencies" in output
                assert "IR072 is still open" in output
            elif label in {"gap", "separation", "norm-product", "convolution", "norm-transport", "rational-norm-product", "signed-product", "quadratic-nonzero", "quadratic-trace"}:
                case = {"gap": "NG001", "separation": "SN002", "norm-product": "SN003", "convolution": "CV001",
                        "norm-transport": "RN001", "rational-norm-product": "RN002", "signed-product": "SI001",
                        "quadratic-nonzero": "QN001", "quadratic-trace": "QF001"}[label]
                assert case in output and "Named statement" in output
                assert "Fresh HA and independently compiled Lean checks" in output
                assert 'href="../arithmetic-frontier.html"' in output
                assert "IR072 remains open" in output
                if label == "norm-product":
                    assert 'href="../quadratic-definitions.html#ND0388"' in output
                    assert 'href="../quadratic-definitions.html#ND0389"' in output
                if label == "convolution":
                    assert 'href="../convolution-definitions.html#ND0293"' in output
                if label == "norm-transport":
                    assert 'href="../local-definitions.html#ND0383"' in output
                if label == "rational-norm-product":
                    assert 'href="../local-definitions.html#ND0385"' in output
                if label == "quadratic-trace":
                    assert 'href="../quadratic-trace-definitions.html#ND0392"' in output
                    assert "Trace existence" in output
            elif label == "quadratic-trace-definitions":
                assert 'id="trace-graph-ND0390"' in output and 'id="trace-graph-ND0393"' in output
                assert "trace does not assume" in output
                assert 'href="checked/QF001.html"' in output
            elif label == "quadratic-definitions":
                assert 'id="ND0388"' in output and 'id="ND0389"' in output
                assert 'href="checked/SN003.html"' in output
                assert "no global registry mutation" in output
            elif label == "convolution-definitions":
                assert 'id="PD0015"' in output and 'id="ND0293"' in output
                assert 'id="convolution-graph-ND0293"' in output
                assert 'aria-label="Eight reused convolution definitions' in output
                assert 'href="checked/CV001.html"' in output
                assert "reused unchanged" in output
            elif label == "atlas":
                assert 'data-error="true"' not in output, "atlas initialization failed"
                assert re.search(r'data-node-id[^>]*>G121', output), "atlas route not selected"
                assert 'href="../map.html?target=IR072"' in output
                assert re.search(r'<p data-plan-navigation=""><a', output), "plan link is hidden"
                assert re.search(r'href="https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/\?v=[0-9a-f]+" data-proof-home', output), "proof-home link points into the local snapshot"
            else:
                assert "planning nodes and" in output, "map JS did not render"
                assert 'class="plan-node' in output, "SVG is empty"
                assert re.search(r'<h2>' + target + ' — ', output), "selected details missing"
                assert not re.search(r'(?:NaN|undefined) (?:NaN|undefined)', output)
            row = dict(route=route, status="render_validated", dom_bytes=len(output.encode()),
                       dom_sha256=sha256(output.encode()).hexdigest(),
                       forced_browser_shutdown_cleanup=forced_cleanup)
            row["expected_page_sha256" if args.base_url else "page_sha256"] = sha256((SITE/path).read_bytes()).hexdigest()
            if args.base_url:
                row["url"] = page_url + ("?" + query if query else "")
            results.append(row)
    report = dict(schema="sqrt2-power-browser-smoke-v1", status="passed", authority="browser_smoke_only",
                  script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                  wall_seconds=round(time.monotonic()-started, 3), routes=results)
    report["surface"] = args.base_url or "local_file_snapshot"
    encoded = (json.dumps(report, sort_keys=True, indent=2)+"\n").encode()
    if args.output:
        from run_sqrt2_power_pilot import save_new
        save_new(args.output, encoded)
    print(encoded.decode(), end="")


if __name__ == "__main__":
    main()
