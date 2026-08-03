"use strict";

// Length-prefixed binary driver used only by the deterministic Python/WASM
// differential campaign. Each frame is: one logic byte, four big-endian
// length bytes, then one canonical artifact. One decimal verdict line returns.

const fs = require("fs");

if (process.argv.length !== 3) {
  console.error("usage: node wasm_shadow_batch_runner.js MODULE.wasm");
  process.exit(2);
}

const moduleBytes = fs.readFileSync(process.argv[2]);
const moduleObject = new WebAssembly.Module(moduleBytes);
if (WebAssembly.Module.imports(moduleObject).length !== 0) {
  throw new Error("Peano shadow WASM unexpectedly imports host capabilities");
}

function readExact(length, eofAllowed) {
  const result = Buffer.allocUnsafe(length);
  let offset = 0;
  while (offset < length) {
    const count = fs.readSync(0, result, offset, length - offset, null);
    if (count === 0) {
      if (eofAllowed && offset === 0) return null;
      throw new Error("truncated differential input frame");
    }
    offset += count;
  }
  return result;
}

for (;;) {
  const header = readExact(5, true);
  if (header === null) break;
  const logic = header.readUInt8(0);
  const length = header.readUInt32BE(1);
  const artifact = readExact(length, false);
  const instance = new WebAssembly.Instance(moduleObject, {});
  const api = instance.exports;
  if (
    api.peano_shadow_abi_version() !== 1
    || api.peano_shadow_max_input_bytes() !== 16 * 1024 * 1024
  ) throw new Error("Peano shadow WASM ABI mismatch");
  const pointer = api.peano_shadow_prepare(length);
  let verdict = 4;
  if (pointer > 0 && pointer + length <= api.memory.buffer.byteLength) {
    new Uint8Array(api.memory.buffer, pointer, length).set(artifact);
    verdict = api.peano_shadow_check(length, logic);
  }
  process.stdout.write(String(verdict) + "\n");
}
