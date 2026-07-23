"use strict";
/*
 * Lambda Lab evaluation worker.
 * Pyodide + the λ-engine run here, OFF the main thread, so a long or divergent
 * reduction can never freeze the UI and can be cancelled by terminating the
 * worker. Protocol:
 *   main → worker : {type:'init', build}         boot Pyodide + driver
 *                   {type:'run',  id, line}       evaluate one REPL line
 *   worker → main : {type:'boot', msg}            boot progress
 *                   {type:'ready', banner}        engine ready
 *                   {type:'error', msg}           boot failed
 *                   {type:'result', id, out}      evaluation output
 */

const PY_FILES = [
  "py/lambda_lab/__init__.py",
  "py/lambda_lab/lab/__init__.py",
  "py/lambda_lab/lab/i18n.py",
  "py/lambda_lab/lab/lc.py",
  "py/lambda_lab/lab/parser.py",
  "py/lambda_lab/lab/church.py",
  "py/driver.py",
];

let runLine = null;
let bannerFn = null;

async function boot(build) {
  try {
    postMessage({ type: "boot", msg: "loading Python (Pyodide, self-hosted)…" });
    // Self-hosted Pyodide 0.28.3 (vendor/ is fetched by scripts/fetch_vendor.sh).
    // No CDN involved: a lecture-hall demo only needs the faculty server.
    importScripts("vendor/pyodide/pyodide.js");
    const pyodide = await loadPyodide({ indexURL: "vendor/pyodide/" });
    postMessage({ type: "boot", msg: "mounting the λ-engine…" });
    for (const rel of PY_FILES) {
      const response = await fetch(rel + "?v=" + encodeURIComponent(build));
      if (!response.ok) throw new Error("could not load " + rel + " (" + response.status + ")");
      const dst = "/lab/" + rel.replace(/^py\//, "");
      pyodide.FS.mkdirTree(dst.slice(0, dst.lastIndexOf("/")));
      pyodide.FS.writeFile(dst, await response.text());
    }
    pyodide.runPython("import sys; sys.path.insert(0, '/lab')");
    const driver = pyodide.pyimport("driver");
    runLine = function (line) { return driver.run_line(line); };
    bannerFn = function () { return driver.banner(); };
    postMessage({ type: "ready", banner: bannerFn() });
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
    let out = "";
    try {
      out = runLine ? String(runLine(message.line)) : "\x1b[93mThe engine is still starting — try again in a moment.\x1b[0m";
    } catch (error) {
      out = "\x1b[91m" + ((error && error.message) ? error.message : String(error)) + "\x1b[0m";
    }
    postMessage({ type: "result", id: message.id, out: out });
  }
};
