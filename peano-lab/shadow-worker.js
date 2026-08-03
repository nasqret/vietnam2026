"use strict";
/*
 * One-shot Rust/WebAssembly diagnostic checker for Peano Lab.
 *
 * Python has already checked every artifact sent here against its original
 * goal.  No message from this worker grants or retracts QED: accept is only
 * independent agreement, while every outcome is diagnostic only.
 */

const PROTOCOL_VERSION = 1;
const ABI_VERSION = 1;
const MAX_INPUT_BYTES = 16 * 1024 * 1024;

let exportsObject = null;
let ready = false;
let busy = false;

function nowMilliseconds() {
  return typeof performance !== "undefined" && performance.now
    ? performance.now()
    : Date.now();
}

function isFunction(value) {
  return typeof value === "function";
}

function validateExports(candidate) {
  const required = [
    "peano_shadow_abi_version",
    "peano_shadow_max_input_bytes",
    "peano_shadow_prepare",
    "peano_shadow_check",
    "peano_shadow_reset",
  ];
  if (!candidate || !required.every((name) => isFunction(candidate[name]))) {
    throw new Error("shadow WASM has an incomplete ABI");
  }
  if (!candidate.memory || !(candidate.memory.buffer instanceof ArrayBuffer)) {
    throw new Error("shadow WASM does not export linear memory");
  }
  if (candidate.peano_shadow_abi_version() !== ABI_VERSION) {
    throw new Error("shadow WASM ABI version mismatch");
  }
  if (candidate.peano_shadow_max_input_bytes() !== MAX_INPUT_BYTES) {
    throw new Error("shadow WASM input limit mismatch");
  }
  return candidate;
}

async function instantiate(url) {
  const response = await fetch(url, { cache: "force-cache" });
  if (!response.ok) throw new Error("could not load shadow WASM (" + response.status + ")");
  let created;
  if (WebAssembly.instantiateStreaming && response.clone) {
    try {
      created = await WebAssembly.instantiateStreaming(Promise.resolve(response.clone()), {});
    } catch (_streamingError) {
      created = await WebAssembly.instantiate(await response.arrayBuffer(), {});
    }
  } else {
    created = await WebAssembly.instantiate(await response.arrayBuffer(), {});
  }
  return validateExports(created.instance ? created.instance.exports : created.exports);
}

async function boot(message) {
  if (
    ready
    || !message
    || message.v !== PROTOCOL_VERSION
    || typeof message.build !== "string"
    || !message.build
    || typeof message.wasmUrl !== "string"
    || !message.wasmUrl
  ) {
    postMessage({ type: "error", v: PROTOCOL_VERSION, code: "protocol" });
    return;
  }
  try {
    exportsObject = await instantiate(message.wasmUrl);
    ready = true;
    postMessage({
      type: "ready",
      v: PROTOCOL_VERSION,
      abi: ABI_VERSION,
      build: message.build,
    });
  } catch (_error) {
    exportsObject = null;
    postMessage({ type: "error", v: PROTOCOL_VERSION, code: "init" });
  }
}

function finish(id, status, started) {
  const durationMs = Math.max(0, nowMilliseconds() - started);
  postMessage({
    type: "result",
    v: PROTOCOL_VERSION,
    id: id,
    status: status,
    durationMs: durationMs,
  });
  close();
}

function checkArtifact(message) {
  const started = nowMilliseconds();
  if (
    !ready
    || busy
    || !message
    || message.v !== PROTOCOL_VERSION
    || !Number.isSafeInteger(message.id)
    || message.id < 1
    || (message.logic !== "ha" && message.logic !== "classical")
    || !(message.artifact instanceof ArrayBuffer)
    || message.artifact.byteLength < 1
    || message.artifact.byteLength > MAX_INPUT_BYTES
  ) {
    finish(
      message && Number.isSafeInteger(message.id) ? message.id : null,
      "input-rejected",
      started,
    );
    return;
  }
  busy = true;
  const length = message.artifact.byteLength;
  try {
    const pointer = exportsObject.peano_shadow_prepare(length);
    const memory = exportsObject.memory.buffer;
    if (
      !Number.isSafeInteger(pointer)
      || pointer < 1
      || pointer + length > memory.byteLength
    ) {
      finish(message.id, "internal-error", started);
      return;
    }
    // prepare may grow memory, so construct this view only after it returns.
    new Uint8Array(memory, pointer, length).set(new Uint8Array(message.artifact));
    const logic = message.logic === "classical" ? 1 : 0;
    const code = exportsObject.peano_shadow_check(length, logic);
    const statuses = {
      1: "accept",
      2: "reject",
      3: "input-rejected",
      4: "internal-error",
    };
    finish(message.id, statuses[code] || "internal-error", started);
  } catch (_error) {
    try {
      exportsObject.peano_shadow_reset();
    } catch (_resetError) {}
    finish(message.id, "trap", started);
  }
}

onmessage = function (event) {
  const message = event.data || {};
  if (message.type === "init") {
    boot(message);
  } else if (message.type === "check") {
    checkArtifact(message);
  } else {
    postMessage({ type: "error", v: PROTOCOL_VERSION, code: "protocol" });
  }
};
