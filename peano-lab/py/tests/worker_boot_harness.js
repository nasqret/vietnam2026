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
  let shadowLogic = "";
  let shadowArtifact = null;
  let shadowLogicThrows = false;
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
          if (line === "qed") {
            shadowLogic = "ha";
            shadowArtifact = new Uint8Array([91, 93, 10]);
          }
          if (line === "qed-shadow-error") shadowLogicThrows = true;
          return JSON.stringify({ out: line, failed: line === "fail" });
        },
        banner() { return "ready banner"; },
        take_download() {
          const body = pendingDownload;
          pendingDownload = "";
          return body;
        },
        pending_shadow_logic() {
          if (shadowLogicThrows) {
            shadowLogicThrows = false;
            throw new Error("optional shadow metadata failed");
          }
          return shadowLogic;
        },
        take_shadow_artifact() {
          const body = shadowArtifact || new Uint8Array();
          shadowLogic = "";
          shadowArtifact = null;
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

  assert.strictEqual(requests.size, listedFiles.length);
  assert.strictEqual(events[1][0], "loadPyodide");
  assert.ok(events.slice(2).every((event) => event[0] === "fetch"));

  runtime.resolve(makePyodide(writes));
  for (const relativePath of [...listedFiles].reverse()) {
    requests.get(relativePath).resolve({
      ok: true,
      status: 200,
      text: async () => "source:" + relativePath,
    });
  }
  for (let attempt = 0; attempt < 5; attempt += 1) await tick();

  assert.deepStrictEqual(
    writes.map(([path]) => path),
    listedFiles.map((path) => "/lab/" + path.replace(/^py\//, "")),
  );
  assert.deepStrictEqual(
    writes.map(([, source]) => source),
    listedFiles.map((path) => "source:" + path),
  );
  assert.strictEqual(messages.filter((message) => message.type === "ready").length, 1);
  assert.strictEqual(messages.some((message) => message.type === "error"), false);

  context.onmessage({ data: { type: "run", id: 41, line: "script download" } });
  context.onmessage({ data: { type: "run", id: 42, line: "help" } });
  context.onmessage({ data: { type: "run", id: 43, line: "fail" } });
  context.onmessage({ data: { type: "run", id: 44, line: "qed" } });
  context.onmessage({ data: { type: "run", id: 45, line: "qed-shadow-error" } });
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
      { type: "result", id: 44, out: "qed", failed: false, download: null },
      {
        type: "result", id: 45, out: "qed-shadow-error", failed: false, download: null,
      },
    ],
  );
  const shadows = messages.filter((message) => message.type === "shadow-artifact");
  assert.strictEqual(shadows.length, 1);
  assert.strictEqual(shadows[0].v, 1);
  assert.strictEqual(shadows[0].id, 44);
  assert.strictEqual(shadows[0].format, "peano-lab-v2");
  assert.strictEqual(shadows[0].logic, "ha");
  assert.deepStrictEqual(Array.from(new Uint8Array(shadows[0].artifact)), [91, 93, 10]);
  assert.ok(
    messages.findIndex((message) => message.type === "result" && message.id === 44)
      < messages.findIndex((message) => message.type === "shadow-artifact"),
  );
  const metadataError = messages.find(
    (message) => message.type === "shadow-artifact-error" && message.id === 45,
  );
  assert.strictEqual(metadataError.code, "metadata");
  assert.ok(
    messages.findIndex((message) => message.type === "result" && message.id === 45)
      < messages.indexOf(metadataError),
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
  for (const relativePath of [...listedFiles].reverse()) {
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

(async () => {
  assert.ok(listedFiles.length > 20);
  await successfulBootIsConcurrentAndOrdered();
  await failureChoiceIsDeterministicAndAtomic();
})().catch((error) => {
  console.error(error.stack || String(error));
  process.exitCode = 1;
});
