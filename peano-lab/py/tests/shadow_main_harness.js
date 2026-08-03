"use strict";

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const source = fs.readFileSync(process.argv[2], "utf8");

function extractFunction(name) {
  const start = source.indexOf("function " + name + "(");
  assert.ok(start >= 0, "missing " + name);
  const opening = source.indexOf("{", start);
  let depth = 0;
  let quote = "";
  let escaped = false;
  for (let index = opening; index < source.length; index += 1) {
    const character = source[index];
    if (quote) {
      if (escaped) escaped = false;
      else if (character === "\\") escaped = true;
      else if (character === quote) quote = "";
      continue;
    }
    if (character === '"' || character === "'" || character === "`") quote = character;
    else if (character === "{") depth += 1;
    else if (character === "}" && --depth === 0) return source.slice(start, index + 1);
  }
  throw new Error("unterminated " + name);
}

function environment() {
  const workers = [];
  const statuses = [];
  const timers = [];
  class FakeWorker {
    constructor(url) {
      this.url = url;
      this.posts = [];
      this.terminated = false;
      workers.push(this);
    }
    postMessage(message, transfer) { this.posts.push({ message, transfer }); }
    terminate() { this.terminated = true; }
  }
  const context = {
    APP_ROOT: "release/",
    BUILD: "test-build",
    MAX_SHADOW_ARTIFACT_BYTES: 16 * 1024 * 1024,
    SHADOW_TIMEOUT_MS: 30000,
    ArrayBuffer,
    Number,
    Worker: FakeWorker,
    clearTimeout(timer) { timer.cleared = true; },
    setTimeout(callback, delay) {
      const timer = { callback, delay, cleared: false };
      timers.push(timer);
      return timer;
    },
    setShadowStatus(kind, message) { statuses.push({ kind, message }); },
    generation: 4,
    shadowWorker: null,
    shadowReady: false,
    shadowQueued: null,
    shadowInFlight: null,
    shadowTimer: null,
    shadowInstance: 0,
  };
  vm.createContext(context);
  const names = [
    "disposeShadowWorker",
    "discardShadow",
    "shadowUnavailable",
    "finishShadow",
    "dispatchShadow",
    "startShadowWorker",
    "queueShadowArtifact",
  ];
  vm.runInContext(names.map(extractFunction).join("\n"), context);
  return { context, workers, statuses, timers };
}

function ready(worker) {
  worker.onmessage({
    data: { type: "ready", v: 1, abi: 1, build: "test-build" },
  });
}

function acceptedDiagnosticIsTransferredAndCannotBeQEDAuthority() {
  const fixture = environment();
  const { context, workers, statuses } = fixture;
  context.startShadowWorker(false);
  const first = workers[0];
  assert.strictEqual(first.url, "release/shadow-worker.js");
  assert.deepStrictEqual(JSON.parse(JSON.stringify(first.posts[0].message)), {
    type: "init", v: 1, build: "test-build", wasmUrl: "peano_kernel_shadow.wasm",
  });
  ready(first);

  const artifact = new Uint8Array([1, 2, 3]).buffer;
  context.queueShadowArtifact({
    type: "shadow-artifact",
    v: 1,
    id: 9,
    format: "peano-lab-v2",
    logic: "ha",
    artifact,
  });
  assert.strictEqual(first.posts[1].message.type, "check");
  assert.strictEqual(first.posts[1].message.id, 9);
  assert.strictEqual(first.posts[1].transfer[0], artifact);

  first.onmessage({ data: { type: "result", v: 1, id: 9, status: "accept" } });
  assert.ok(statuses.at(-1).message.includes("agreement"));
  assert.ok(statuses.at(-1).message.includes("Python QED is authoritative"));
  assert.strictEqual(first.terminated, true);
  assert.strictEqual(workers.length, 2, "a fresh diagnostic worker should prewarm");
}

function rejectionTimeoutAndStaleMessagesRemainDiagnostic() {
  const fixture = environment();
  const { context, workers, statuses, timers } = fixture;
  context.startShadowWorker(false);
  ready(workers[0]);
  context.queueShadowArtifact({
    v: 1, id: 11, format: "peano-lab-v2", logic: "classical",
    artifact: new ArrayBuffer(2),
  });
  workers[0].onmessage({ data: { type: "result", v: 1, id: 11, status: "reject" } });
  assert.ok(statuses.at(-1).message.includes("disagreement"));
  assert.ok(statuses.at(-1).message.includes("remains authoritative"));

  ready(workers[1]);
  context.queueShadowArtifact({
    v: 1, id: 12, format: "peano-lab-v2", logic: "ha",
    artifact: new ArrayBuffer(2),
  });
  assert.strictEqual(timers.at(-1).delay, 30000);
  timers.at(-1).callback();
  assert.ok(statuses.at(-1).message.includes("timed out"));
  const statusCount = statuses.length;
  context.generation += 1;
  workers[1].onmessage({ data: { type: "result", v: 1, id: 12, status: "accept" } });
  assert.strictEqual(statuses.length, statusCount, "stale result must be ignored");
}

function malformedEnvelopeNeverReachesWasm() {
  const fixture = environment();
  fixture.context.startShadowWorker(false);
  ready(fixture.workers[0]);
  fixture.context.queueShadowArtifact({
    v: 1, id: 1, format: "wrong", logic: "ha", artifact: new ArrayBuffer(1),
  });
  assert.strictEqual(fixture.workers[0].posts.length, 1);
  assert.ok(fixture.statuses.at(-1).message.includes("invalid artifact envelope"));
}

function newerQedCancelsSameGenerationDiagnostic() {
  const fixture = environment();
  const { context, workers, statuses } = fixture;
  context.startShadowWorker(false);
  ready(workers[0]);
  context.queueShadowArtifact({
    v: 1, id: 21, format: "peano-lab-v2", logic: "ha",
    artifact: new ArrayBuffer(2),
  });
  const oldWorker = workers[0];
  context.queueShadowArtifact({
    v: 1, id: 22, format: "peano-lab-v2", logic: "ha",
    artifact: new ArrayBuffer(3),
  });
  assert.strictEqual(oldWorker.terminated, true);
  assert.strictEqual(workers.length, 2);
  assert.ok(statuses.at(-1).message.includes("latest QED"));

  const statusCount = statuses.length;
  oldWorker.onmessage({ data: { type: "result", v: 1, id: 21, status: "accept" } });
  assert.strictEqual(statuses.length, statusCount, "older QED result must be ignored");

  ready(workers[1]);
  assert.strictEqual(workers[1].posts[1].message.id, 22);
  workers[1].onmessage({ data: { type: "result", v: 1, id: 22, status: "accept" } });
  assert.ok(statuses.at(-1).message.includes("agreement"));
}

acceptedDiagnosticIsTransferredAndCannotBeQEDAuthority();
rejectionTimeoutAndStaleMessagesRemainDiagnostic();
malformedEnvelopeNeverReachesWasm();
newerQedCancelsSameGenerationDiagnostic();
