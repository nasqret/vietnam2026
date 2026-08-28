"use strict";

// Dynamic contract for worker.js.  The browser shell tests invoke this small
// Node VM so concurrency, deterministic failure selection, and mount order are
// tested as behavior rather than fragile source-text patterns.

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const workerPath = process.argv[2];
const workerSource = fs.readFileSync(workerPath, "utf8");
const listedFiles = Array.from(
  workerSource.matchAll(/"(py\/[^"\n]+\.py)"/g),
  (match) => match[1],
);
const listedProofArtifacts = Array.from(
  new Set(Array.from(
    workerSource.matchAll(/"(proof-artifacts\/[^"\n]+\.json)"/g),
    (match) => match[1],
  )),
);
const allRuntimeFiles = [...listedFiles, ...listedProofArtifacts];

function deferred() {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
}

function tick() {
  return new Promise((resolve) => setImmediate(resolve));
}

function makePyodide(writes) {
  let pendingDownload = "pa prove 0 = 0\nrefl\nqed\n";
  return {
    FS: {
      mkdirTree() {},
      writeFile(path, source) { writes.push([path, source]); },
    },
    runPython() {},
    pyimport(name) {
      assert.strictEqual(name, "driver");
      return {
        run_line(line) { return line; },
        run_line_result(line) {
          return JSON.stringify({ out: line, failed: line === "fail" });
        },
        banner() { return "ready banner"; },
        take_download() {
          const body = pendingDownload;
          pendingDownload = "";
          return body;
        },
      };
    },
  };
}

async function successfulBootIsConcurrentAndOrdered() {
  const events = [];
  const messages = [];
  const writes = [];
  const proofBodyReads = [];
  const runtime = deferred();
  const requests = new Map();

  const context = {
    encodeURIComponent,
    importScripts(url) { events.push(["importScripts", url]); },
    loadPyodide(options) {
      events.push(["loadPyodide", options.indexURL]);
      return runtime.promise;
    },
    fetch(url) {
      events.push(["fetch", url]);
      const request = deferred();
      requests.set(url, request);
      return request.promise;
    },
    postMessage(message) { messages.push(message); },
    setTimeout,
    clearTimeout,
  };
  vm.createContext(context);
  vm.runInContext(workerSource, context, { filename: workerPath });
  context.onmessage({ data: { type: "init", build: "test-build" } });

  assert.strictEqual(requests.size, allRuntimeFiles.length);
  assert.strictEqual(events[1][0], "loadPyodide");
  assert.ok(events.slice(2).every((event) => event[0] === "fetch"));

  runtime.resolve(makePyodide(writes));
  for (const relativePath of [...allRuntimeFiles].reverse()) {
    requests.get(relativePath).resolve({
      ok: true,
      status: 200,
      text: async () => {
        assert.strictEqual(relativePath.startsWith("proof-artifacts/"), false);
        return "source:" + relativePath;
      },
      arrayBuffer: async () => {
        proofBodyReads.push(relativePath);
        return Uint8Array.from(Buffer.from("source:" + relativePath)).buffer;
      },
    });
  }
  for (let attempt = 0; attempt < listedProofArtifacts.length + 5; attempt += 1) {
    await tick();
  }

  assert.deepStrictEqual(
    writes.map(([path]) => path),
    [
      ...listedFiles.map((path) => "/lab/" + path.replace(/^py\//, "")),
      ...listedProofArtifacts.map((path) => "/lab/" + path),
    ],
  );
  assert.deepStrictEqual(
    writes.slice(0, listedFiles.length).map(([, source]) => source),
    listedFiles.map((path) => "source:" + path),
  );
  assert.deepStrictEqual(
    writes.slice(listedFiles.length).map(([, source]) => Buffer.from(source).toString("utf8")),
    listedProofArtifacts.map((path) => "source:" + path),
  );
  assert.deepStrictEqual(proofBodyReads, listedProofArtifacts);
  assert.strictEqual(messages.filter((message) => message.type === "ready").length, 1);
  assert.strictEqual(messages.some((message) => message.type === "error"), false);

  context.onmessage({ data: { type: "run", id: 41, line: "script download" } });
  context.onmessage({ data: { type: "run", id: 42, line: "help" } });
  context.onmessage({ data: { type: "run", id: 43, line: "fail" } });
  const results = messages.filter((message) => message.type === "result");
  assert.deepStrictEqual(
    JSON.parse(JSON.stringify(results)),
    [
      {
        type: "result",
        id: 41,
        out: "script download",
        failed: false,
        download: "pa prove 0 = 0\nrefl\nqed\n",
      },
      { type: "result", id: 42, out: "help", failed: false, download: null },
      { type: "result", id: 43, out: "fail", failed: true, download: null },
    ],
  );
}

async function failureChoiceIsDeterministicAndAtomic() {
  const messages = [];
  const writes = [];
  const requests = new Map();
  const context = {
    encodeURIComponent,
    importScripts() {},
    loadPyodide() { return Promise.resolve(makePyodide(writes)); },
    fetch(url) {
      const request = deferred();
      requests.set(url, request);
      return request.promise;
    },
    postMessage(message) { messages.push(message); },
    setTimeout,
    clearTimeout,
  };
  vm.createContext(context);
  vm.runInContext(workerSource, context, { filename: workerPath });
  context.onmessage({ data: { type: "init", build: "failure-build" } });

  const firstFailure = listedFiles[2];
  const laterFailure = listedFiles[listedFiles.length - 2];
  for (const relativePath of [...allRuntimeFiles].reverse()) {
    const failed = relativePath === firstFailure || relativePath === laterFailure;
    requests.get(relativePath).resolve({
      ok: !failed,
      status: failed ? 503 : 200,
      text: async () => "source:" + relativePath,
    });
  }
  for (let attempt = 0; attempt < 5; attempt += 1) await tick();

  const errors = messages.filter((message) => message.type === "error");
  assert.strictEqual(errors.length, 1);
  assert.strictEqual(
    errors[0].msg,
    "could not load " + firstFailure + " (503)",
  );
  assert.strictEqual(messages.some((message) => message.type === "ready"), false);
  assert.deepStrictEqual(writes, []);
}

async function missingProofArtifactFailsBeforeAnyMount(missingArtifact) {
  const messages = [];
  const writes = [];
  const requests = new Map();
  const context = {
    encodeURIComponent,
    importScripts() {},
    loadPyodide() { return Promise.resolve(makePyodide(writes)); },
    fetch(url) {
      const request = deferred();
      requests.set(url, request);
      return request.promise;
    },
    postMessage(message) { messages.push(message); },
    setTimeout,
    clearTimeout,
  };
  vm.createContext(context);
  vm.runInContext(workerSource, context, { filename: workerPath });
  context.onmessage({ data: { type: "init", build: "missing-artifact" } });

  for (const relativePath of allRuntimeFiles) {
    const failed = relativePath === missingArtifact;
    requests.get(relativePath).resolve({
      ok: !failed,
      status: failed ? 404 : 200,
      text: async () => "source:" + relativePath,
    });
  }
  for (let attempt = 0; attempt < 5; attempt += 1) await tick();

  assert.strictEqual(
    messages.find((message) => message.type === "error").msg,
    "could not load " + missingArtifact + " (404)",
  );
  assert.strictEqual(messages.some((message) => message.type === "ready"), false);
  assert.deepStrictEqual(writes, []);
}

(async () => {
  assert.ok(listedFiles.length > 20);
  assert.deepStrictEqual(listedProofArtifacts, [
    "proof-artifacts/quadratic-reciprocity-proof-bundle-v1.json",
    "proof-artifacts/supplementary-laws-proof-bundle-v1.json",
    "proof-artifacts/lucas-proof-bundle-v1.json",
    "proof-artifacts/kummer-proof-bundle-v1.json",
    "proof-artifacts/bertrand-proof-bundle-v1.json",
    "proof-artifacts/four-square-proof-bundle-v1.json",
    "proof-artifacts/two-square-proof-bundle-v1.json",
    "proof-artifacts/alpha-v19-residual-proof-bundle-v1.json",
    "proof-artifacts/alpha-v19-campaign-frontier-proof-bundle-v1.json",
    "proof-artifacts/alpha-v20-next-layer-proof-bundle-v1.json",
    "proof-artifacts/alpha-v21-advanced-layer-proof-bundle-v1.json",
    "proof-artifacts/alpha-v22-transport-layer-proof-bundle-v1.json",
    "proof-artifacts/alpha-v23-milestone-closure-proof-bundle-v1.json",
    "proof-artifacts/alpha-v24-research-layer-proof-bundle-v1.json",
    "proof-artifacts/alpha-v25-breakthrough-layer-proof-bundle-v1.json",
    "proof-artifacts/alpha-v26-first-wave-proof-bundle-v1.json",
    "proof-artifacts/alpha-v27-second-wave-proof-bundle-v1.json",
    "proof-artifacts/alpha-v28-lower-layer-proof-bundle-v1.json",
    "proof-artifacts/alpha-v29-priority-layer-proof-bundle-v1.json",
    "proof-artifacts/alpha-v30-gaussian-factorization-proof-bundle-v1.json",
  ]);
  await successfulBootIsConcurrentAndOrdered();
  await failureChoiceIsDeterministicAndAtomic();
  for (const artifact of listedProofArtifacts) {
    await missingProofArtifactFailsBeforeAnyMount(artifact);
  }
})().catch((error) => {
  console.error(error.stack || String(error));
  process.exitCode = 1;
});
