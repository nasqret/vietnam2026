"use strict";

const assert = require("assert");
const fs = require("fs");

const wasmPath = process.argv[2];
const bytes = fs.readFileSync(wasmPath);
const moduleObject = new WebAssembly.Module(bytes);
assert.deepStrictEqual(WebAssembly.Module.imports(moduleObject), []);

const exportsList = WebAssembly.Module.exports(moduleObject);
const exportNames = new Set(exportsList.map((entry) => entry.name));
for (const name of [
  "memory",
  "peano_shadow_abi_version",
  "peano_shadow_max_input_bytes",
  "peano_shadow_prepare",
  "peano_shadow_check",
  "peano_shadow_reset",
]) assert.ok(exportNames.has(name), "missing WASM export " + name);

const instance = new WebAssembly.Instance(moduleObject, {});
const api = instance.exports;
assert.strictEqual(api.peano_shadow_abi_version(), 1);
assert.strictEqual(api.peano_shadow_max_input_bytes(), 16 * 1024 * 1024);
assert.ok(!(api.memory.buffer instanceof SharedArrayBuffer));
assert.ok(api.memory.buffer.byteLength >= 2 * 1024 * 1024, "2 MiB stack not reserved");

function artifact(text) {
  return new TextEncoder().encode(text);
}

function check(input, logic) {
  const pointer = api.peano_shadow_prepare(input.byteLength);
  assert.ok(pointer > 0);
  new Uint8Array(api.memory.buffer, pointer, input.byteLength).set(input);
  return api.peano_shadow_check(input.byteLength, logic);
}

const atom = '["eq",["zero"],["zero"]]';
const refl = '["eq_refl",["zero"]]';
const accepted = artifact('["peano-lab-v2",8,' + atom + ',' + refl + ']\n');
assert.strictEqual(check(accepted, 0), 1);
assert.strictEqual(api.peano_shadow_check(accepted.byteLength, 0), 4, "check is one-shot");

const wrongTarget = artifact(
  '["peano-lab-v2",8,["imp",' + atom + ',' + atom + '],' + refl + ']\n',
);
assert.strictEqual(check(wrongTarget, 0), 2);
const zeroFuel = artifact('["peano-lab-v2",0,' + atom + ',' + refl + ']\n');
assert.strictEqual(check(zeroFuel, 0), 2);
assert.strictEqual(check(accepted.slice(0, -1), 0), 3);

const classicalTarget =
  '["imp",["imp",["imp",' + atom + ',["bot"]],["bot"]],' + atom + ']';
const classical = artifact(
  '["peano-lab-v2",16,' + classicalTarget + ',["dne",' + atom + ']]\n',
);
assert.strictEqual(check(classical, 0), 2);
assert.strictEqual(check(classical, 1), 1);
assert.strictEqual(check(accepted, 99), 4);

const portableIndex = 4294967039;
const excessiveIndex = portableIndex + 1;
function openRefl(index) {
  const variable = '["var",' + index + ']';
  return artifact(
    '["peano-lab-v2",8,["eq",' + variable + ',' + variable +
    '],["eq_refl",' + variable + ']]\n',
  );
}
assert.strictEqual(check(openRefl(portableIndex), 0), 2, "safe open target is logical reject");
assert.strictEqual(check(openRefl(excessiveIndex), 0), 3, "nonportable index is resource reject");

assert.strictEqual(api.peano_shadow_prepare(0), 0);
assert.strictEqual(api.peano_shadow_prepare(16 * 1024 * 1024 + 1), 0);

// The linker-fixed maximum is observable by growing exactly to 256 MiB and
// requiring one additional page to fail.  WASM pages are 64 KiB and memory is
// unshared, so this does not require COOP/COEP or SharedArrayBuffer.
const maximumPages = 4096;
const currentPages = api.memory.buffer.byteLength / 65536;
assert.ok(currentPages < maximumPages);
api.memory.grow(maximumPages - currentPages);
assert.strictEqual(api.memory.buffer.byteLength, 256 * 1024 * 1024);
assert.throws(() => api.memory.grow(1), RangeError);
