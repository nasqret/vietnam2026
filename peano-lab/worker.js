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
 *                    {type: "result", id, out}
 */

const PY_FILES = [
  "py/peano_lab/__init__.py",
  "py/peano_lab/kernel/__init__.py",
  "py/peano_lab/kernel/terms.py",
  "py/peano_lab/kernel/formulas.py",
  "py/peano_lab/kernel/subst.py",
  "py/peano_lab/kernel/proofs.py",
  "py/peano_lab/kernel/checker.py",
  "py/peano_lab/engine/__init__.py",
  "py/peano_lab/engine/state.py",
  "py/peano_lab/engine/proof_reduction.py",
  "py/peano_lab/engine/rewrite.py",
  "py/peano_lab/engine/induction.py",
  "py/peano_lab/engine/tactics.py",
  "py/peano_lab/engine/tacticals.py",
  "py/peano_lab/engine/decide.py",
  "py/peano_lab/engine/norm_num.py",
  "py/peano_lab/engine/ring.py",
  "py/peano_lab/engine/search.py",
  "py/peano_lab/engine/trace.py",
  "py/peano_lab/ui/__init__.py",
  "py/peano_lab/ui/data_tactics.py",
  "py/peano_lab/ui/data_kb.py",
  "py/peano_lab/ui/data_library.py",
  "py/peano_lab/ui/data_tutorials.py",
  "py/peano_lab/ui/tutorial.py",
  "py/peano_lab/ui/panels.py",
  "py/peano_lab/ui/prove.py",
  "py/peano_lab/library/__init__.py",
  "py/peano_lab/library/lean.py",
  "py/peano_lab/library/theorems.py",
  "py/driver.py",
];

// This namespace is derived from the pinned vendor manifest.  It is part of
// the URL, rather than only a query string, because Pyodide constructs the
// URLs for its own .wasm and standard-library files from indexURL.
const VENDOR_ROOT = "../../vendor/v-85fb3352e49c/";

let runLine = null;
let banner = null;

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
    banner = function () { return driver.banner(); };
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
    try {
      output = runLine
        ? String(runLine(message.line))
        : "\x1b[93mThe engine is still starting — try again in a moment.\x1b[0m";
    } catch (error) {
      output = "\x1b[91m" + ((error && error.message) ? error.message : String(error)) + "\x1b[0m";
    }
    postMessage({ type: "result", id: message.id, out: output });
  }
};
