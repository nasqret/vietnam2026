"use strict";

// Behavioral contract for the two dependency-free download helpers embedded
// in index.html.  The surrounding terminal is intentionally not simulated.

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const indexSource = fs.readFileSync(process.argv[2], "utf8");
const start = indexSource.indexOf("function validateProofDownload");
const end = indexSource.indexOf("async function submit", start);
assert.ok(start >= 0 && end > start);
const helpers = indexSource.slice(start, end);

function environment(options = {}) {
  const events = [];
  const timers = [];
  let lastBlob = null;
  let lastLink = null;

  class FakeBlob {
    constructor(parts, settings) {
      this.parts = parts;
      this.type = settings.type;
      this.size = Buffer.byteLength(parts.join(""), "utf8");
      lastBlob = this;
      events.push("blob");
    }
  }

  const context = {
    MAX_SCRIPT_DOWNLOAD: 500000,
    Blob: FakeBlob,
    URL: {
      createObjectURL(blob) {
        assert.strictEqual(blob, lastBlob);
        events.push("create-url");
        return "blob:test";
      },
      revokeObjectURL(url) {
        assert.strictEqual(url, "blob:test");
        events.push("revoke-url");
      },
    },
    document: {
      body: {
        appendChild(link) {
          assert.strictEqual(link, lastLink);
          events.push("append");
        },
      },
      createElement(tag) {
        assert.strictEqual(tag, "a");
        const link = {
          href: "",
          download: "",
          hidden: false,
          click() {
            events.push("click");
            if (options.throwOnClick) throw new Error("click failed");
          },
          remove() { events.push("remove"); },
        };
        lastLink = link;
        return link;
      },
    },
    setTimeout(callback, delay) {
      assert.strictEqual(delay, 0);
      timers.push(callback);
      events.push("schedule-revoke");
    },
  };
  vm.createContext(context);
  vm.runInContext(helpers, context, { filename: "peano-download-helpers.js" });
  return { context, events, timers, getBlob: () => lastBlob, getLink: () => lastLink };
}

function rejectionCases() {
  const { context, events } = environment();
  const invalid = [
    null,
    "",
    "pa prove 0 = 0",
    "pa prove 0 = 0\r\n",
    "pa prove 0 = 0\n\n",
    "refl\n",
    "pa prove 0 = 0\nqed\nrefl\n",
    "pa prove 0 = 0\nqed\nqed\n",
    "pa prove 0 = 0\nrefl\u001b\n",
    "pa prove 0 = 0\nrefl\u009b\n",
    "pa prove 0 = 0\nrefl\u202e\n",
    "pa prove 0 = 0\nrefl\u2028\n",
    "pa prove 0 = 0\nrefl\ud800\n",
    "pa prove " + "x".repeat(500001) + "\n",
  ];
  for (const text of invalid) {
    assert.notStrictEqual(context.validateProofDownload(text), "");
    assert.notStrictEqual(context.downloadProofScript(text), "");
  }
  assert.deepStrictEqual(events, []);
}

function validLifecycle() {
  const fixture = environment();
  const text = "pa prove 0 = 0\nrefl\nqed\n";
  assert.strictEqual(fixture.context.validateProofDownload(text), "");
  assert.strictEqual(fixture.context.downloadProofScript(text), "");
  assert.strictEqual(fixture.getBlob().parts.length, 1);
  assert.strictEqual(fixture.getBlob().parts[0], text);
  assert.strictEqual(fixture.getBlob().type, "text/plain;charset=utf-8");
  assert.strictEqual(fixture.getLink().download, "peano-lab-proof.pa");
  assert.deepStrictEqual(
    fixture.events,
    ["blob", "create-url", "append", "click", "remove", "schedule-revoke"],
  );
  assert.strictEqual(fixture.timers.length, 1);
  fixture.timers[0]();
  assert.deepStrictEqual(fixture.events.slice(-1), ["revoke-url"]);

  // A live prefix with no QED is also a valid, explicitly unchecked replay.
  assert.strictEqual(
    fixture.context.validateProofDownload("pa prove 0 = 0\nrefl\n"),
    "",
  );
}

function cleanupAfterClickFailure() {
  const fixture = environment({ throwOnClick: true });
  assert.throws(
    () => fixture.context.downloadProofScript("pa prove 0 = 0\nrefl\n"),
    /click failed/,
  );
  assert.ok(fixture.events.includes("remove"));
  assert.strictEqual(fixture.timers.length, 1);
  fixture.timers[0]();
  assert.strictEqual(fixture.events.filter((event) => event === "revoke-url").length, 1);
}

rejectionCases();
validLifecycle();
cleanupAfterClickFailure();
