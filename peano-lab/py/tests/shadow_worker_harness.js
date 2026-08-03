"use strict";

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const workerPath = process.argv[2];
const source = fs.readFileSync(workerPath, "utf8");

function tick() {
  return new Promise((resolve) => setImmediate(resolve));
}

async function runCase(code, logic = "ha") {
  const messages = [];
  let closed = 0;
  const memory = { buffer: new ArrayBuffer(32 * 1024 * 1024) };
  const exportsObject = {
    memory,
    peano_shadow_abi_version() { return 1; },
    peano_shadow_max_input_bytes() { return 16 * 1024 * 1024; },
    peano_shadow_prepare(length) {
      assert.strictEqual(length, 3);
      return 1024;
    },
    peano_shadow_check(length, mode) {
      assert.strictEqual(length, 3);
      assert.strictEqual(mode, logic === "classical" ? 1 : 0);
      assert.deepStrictEqual(Array.from(new Uint8Array(memory.buffer, 1024, 3)), [1, 2, 3]);
      if (code === "trap") throw new Error("synthetic trap");
      return code;
    },
    peano_shadow_reset() { return 1; },
  };
  const context = {
    ArrayBuffer,
    Date,
    Number,
    Promise,
    Uint8Array,
    WebAssembly: {
      instantiateStreaming: async () => ({ instance: { exports: exportsObject } }),
      instantiate: async () => ({ instance: { exports: exportsObject } }),
    },
    fetch: async () => ({
      ok: true,
      status: 200,
      clone() { return this; },
      arrayBuffer: async () => new ArrayBuffer(8),
    }),
    performance: { now: () => 10 },
    postMessage(message) { messages.push(message); },
    close() { closed += 1; },
  };
  vm.createContext(context);
  vm.runInContext(source, context, { filename: workerPath });
  context.onmessage({
    data: { type: "init", v: 1, build: "test", wasmUrl: "shadow.wasm" },
  });
  await tick();
  assert.deepStrictEqual(JSON.parse(JSON.stringify(messages[0])), {
    type: "ready", v: 1, abi: 1, build: "test",
  });

  const artifact = new Uint8Array([1, 2, 3]).buffer;
  context.onmessage({
    data: { type: "check", v: 1, id: 7, logic, artifact },
  });
  const expected = {
    1: "accept",
    2: "reject",
    3: "input-rejected",
    4: "internal-error",
    trap: "trap",
  }[code];
  assert.strictEqual(messages[1].type, "result");
  assert.strictEqual(messages[1].v, 1);
  assert.strictEqual(messages[1].id, 7);
  assert.strictEqual(messages[1].status, expected);
  assert.strictEqual(messages[1].durationMs, 0);
  assert.strictEqual(closed, 1);
}

async function malformedInputFailsClosedBeforeCallingWasm() {
  const messages = [];
  let calls = 0;
  const exportsObject = {
    memory: { buffer: new ArrayBuffer(1024) },
    peano_shadow_abi_version: () => 1,
    peano_shadow_max_input_bytes: () => 16 * 1024 * 1024,
    peano_shadow_prepare: () => { calls += 1; return 1; },
    peano_shadow_check: () => { calls += 1; return 1; },
    peano_shadow_reset: () => 1,
  };
  const context = {
    ArrayBuffer,
    Date,
    Number,
    Promise,
    Uint8Array,
    WebAssembly: {
      instantiateStreaming: async () => ({ instance: { exports: exportsObject } }),
      instantiate: async () => ({ instance: { exports: exportsObject } }),
    },
    fetch: async () => ({ ok: true, clone() { return this; } }),
    performance: { now: () => 1 },
    postMessage(message) { messages.push(message); },
    close() {},
  };
  vm.createContext(context);
  vm.runInContext(source, context, { filename: workerPath });
  context.onmessage({ data: { type: "init", v: 1, build: "test", wasmUrl: "x" } });
  await tick();
  context.onmessage({
    data: { type: "check", v: 1, id: 8, logic: "unknown", artifact: new ArrayBuffer(1) },
  });
  assert.strictEqual(messages[1].status, "input-rejected");
  assert.strictEqual(calls, 0);
}

(async () => {
  await runCase(1);
  await runCase(1, "classical");
  await runCase(2);
  await runCase(3);
  await runCase(4);
  await runCase("trap");
  await malformedInputFailsClosedBeforeCallingWasm();
})().catch((error) => {
  console.error(error.stack || String(error));
  process.exitCode = 1;
});
