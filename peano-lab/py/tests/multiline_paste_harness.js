"use strict";

// Behavioral contract for the dependency-free multiline-paste helpers in
// index.html.  DOM rendering is deliberately left to the browser-shell tests;
// this harness pins parsing, sequencing, and the Stop-generation boundary.

const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const indexSource = fs.readFileSync(process.argv[2], "utf8");

function extractFunction(name) {
  const declaration = "function " + name + "(";
  const functionStart = indexSource.indexOf(declaration);
  assert.ok(functionStart >= 0, "missing " + name + " in index.html");
  const asyncStart = indexSource.lastIndexOf("async ", functionStart);
  const start = asyncStart >= 0 && asyncStart + 6 === functionStart
    ? asyncStart
    : functionStart;
  const opening = indexSource.indexOf("{", start);
  assert.ok(opening > start);
  let depth = 0;
  let quote = "";
  let escaped = false;
  for (let index = opening; index < indexSource.length; index += 1) {
    const character = indexSource[index];
    if (quote) {
      if (escaped) escaped = false;
      else if (character === "\\") escaped = true;
      else if (character === quote) quote = "";
      continue;
    }
    if (character === "\"" || character === "'" || character === "`") {
      quote = character;
      continue;
    }
    if (character === "{") depth += 1;
    else if (character === "}") {
      depth -= 1;
      if (depth === 0) return indexSource.slice(start, index + 1);
    }
  }
  throw new Error("unterminated helper " + name);
}

const forbiddenCalls = [];
const routedPastes = [];
const focusCalls = [];
const context = {
  MAX_INPUT: 4000,
  MAX_PASTE_CHARS: 100000,
  MAX_PASTE_COMMANDS: 256,
  MAX_PASTE_LINES: 256,
  // Aliases keep the harness concerned with behavior rather than private
  // constant spelling.
  MAX_PASTED_PROOF: 100000,
  MAX_PASTED_COMMANDS: 256,
  history: {
    push() { forbiddenCalls.push("history.push"); },
  },
  saveHistory() { forbiddenCalls.push("saveHistory"); },
  downloadProofScript() { forbiddenCalls.push("downloadProofScript"); },
  busy: false,
  beginPastedProof(source, inDialog) { routedPastes.push([source, inDialog]); },
  pasteInput: { value: "", selectionStart: 0, selectionEnd: 0 },
  pasteError: { textContent: "" },
  term: { focus() { focusCalls.push("terminal"); } },
  pasteBtn: { focus() { focusCalls.push("button"); } },
};
vm.createContext(context);
vm.runInContext(
    extractFunction("unwrapBracketedPaste") + "\n" +
    extractFunction("preparePastedProof") + "\n" +
    extractFunction("looksLikeMultilinePaste") + "\n" +
    extractFunction("handleTerminalPaste") + "\n" +
    extractFunction("handlePasteInput") + "\n" +
    extractFunction("restorePasteFocus") + "\n" +
    extractFunction("executePastedCommands"),
  context,
  { filename: "peano-multiline-paste-helpers.js" },
);

function plain(value) {
  return JSON.parse(JSON.stringify(value));
}

function browserEventsRouteOnlyBoundedMultilineInputAndRestoreFocus() {
  function eventFor(text) {
    return {
      clipboardData: { getData(type) { assert.strictEqual(type, "text/plain"); return text; } },
      prevented: false,
      stopped: false,
      preventDefault() { this.prevented = true; },
      stopImmediatePropagation() { this.stopped = true; },
    };
  }

  const single = eventFor("refl");
  context.handleTerminalPaste(single);
  assert.strictEqual(single.prevented, false);
  assert.deepStrictEqual(routedPastes, []);

  const multiline = eventFor("pa prove 0 = 0\r\nrefl\r\nqed\r\n");
  context.handleTerminalPaste(multiline);
  assert.strictEqual(multiline.prevented, true);
  assert.strictEqual(multiline.stopped, true);
  assert.deepStrictEqual(routedPastes, [["pa prove 0 = 0\r\nrefl\r\nqed\r\n", false]]);

  context.busy = true;
  const ignoredWhileBusy = eventFor("pa prove 1 = 1\nrefl\nqed\n");
  context.handleTerminalPaste(ignoredWhileBusy);
  assert.strictEqual(ignoredWhileBusy.prevented, false);
  assert.strictEqual(routedPastes.length, 1);

  context.pasteInput.value = "pa prove 0 = 0\n";
  context.pasteInput.selectionStart = context.pasteInput.value.length;
  context.pasteInput.selectionEnd = context.pasteInput.value.length;
  const oversized = eventFor("x".repeat(100000));
  context.handlePasteInput(oversized);
  assert.strictEqual(oversized.prevented, true);
  assert.ok(context.pasteError.textContent.includes("100,000"));

  context.restorePasteFocus();
  context.busy = false;
  context.restorePasteFocus();
  assert.deepStrictEqual(focusCalls, ["terminal", "button"]);
}

function reject(source, fragments = []) {
  const result = plain(context.preparePastedProof(source));
  assert.deepStrictEqual(result.commands, []);
  assert.strictEqual(typeof result.error, "string");
  assert.ok(result.error.length > 0, "rejection must have final English text");
  for (const fragment of fragments) assert.ok(result.error.includes(fragment), result.error);
}

function preparationAcceptsPortableTextAndPreservesSourceLines() {
  const source =
    "\x1b[200~\r\n  pa prove forall n. n = n  \r\n\t\r" +
    " intro n\r  refl  \r\nqed\r\n\x1b[201~";
  assert.deepStrictEqual(
    plain(context.preparePastedProof(source)),
    {
      commands: [
        { line: 2, text: "pa prove forall n. n = n" },
        { line: 4, text: "intro n" },
        { line: 5, text: "refl" },
        { line: 6, text: "qed" },
      ],
      error: "",
    },
  );

  assert.deepStrictEqual(
    plain(context.preparePastedProof("pa prove 0 = 0\n\t\nrefl\nqed")).commands,
    [
      { line: 1, text: "pa prove 0 = 0" },
      { line: 3, text: "refl" },
      { line: 4, text: "qed" },
    ],
  );

  // The boundary values are accepted.  Validation is syntactic and does not
  // try to parse the theorem or tactic language in JavaScript.
  const exactLimit = "pa prove " + "x".repeat(3991) + "\nqed";
  assert.strictEqual(context.preparePastedProof(exactLimit).error, "");
  const maximumCommands = ["pa prove 0 = 0"]
    .concat(Array(254).fill("refl"), ["qed"])
    .join("\n");
  assert.strictEqual(context.preparePastedProof(maximumCommands).commands.length, 256);
}

function preparationRejectsEveryUnsafeOrAmbiguousShape() {
  reject(null);
  reject("");
  reject(" \r\n\t\r\n ");
  reject("PA prove 0 = 0\nrefl\nqed", ["1"]);
  reject("pa prove 0 = 0\nrefl");
  reject("pa prove 0 = 0\nqed now");
  reject("pa prove 0 = 0\nqed\nqed", ["2"]);
  reject("pa prove 0 = 0\npa prove 1 = 1\nqed", ["2"]);
  for (const blocked of ["abort", "undo", "?", "help", "hint", "script", "script download"]) {
    reject("pa prove 0 = 0\n" + blocked + "\nqed", ["2"]);
  }

  reject("pa prove 0 = 0\n" + "x".repeat(4001) + "\nqed", ["2", "4,000"]);
  const tooMany = ["pa prove 0 = 0"]
    .concat(Array(255).fill("refl"), ["qed"])
    .join("\n");
  reject(tooMany, ["256"]);
  const tooLarge = ["pa prove 0 = 0"]
    .concat(Array(26).fill("x".repeat(4000)), ["qed"])
    .join("\n");
  assert.ok(tooLarge.length > 100000);
  reject(tooLarge, ["100,000"]);

  for (const unsafe of ["\x00", "\x09", "\x1b", "\x9b", "\u202e", "\u2028", "\ud800"]) {
    reject("pa prove 0 = 0\nrefl" + unsafe + "evil\nqed", ["2"]);
  }
  reject("pa prove 0 = 0\n\x1b[200~refl\x1b[201~\nqed", ["2"]);
}

function deferred() {
  let resolve;
  let rejectPromise;
  const promise = new Promise((done, fail) => {
    resolve = done;
    rejectPromise = fail;
  });
  return { promise, resolve, reject: rejectPromise };
}

function tick() {
  return new Promise((resolve) => setImmediate(resolve));
}

async function executionIsStrictlySequentialAndObservesSettledResults() {
  const commands = [
    { line: 2, text: "pa prove 0 = 0" },
    { line: 4, text: "refl" },
    { line: 5, text: "qed" },
  ];
  const requests = commands.map(() => deferred());
  const attempted = [];
  const observed = [];
  const execution = context.executePastedCommands(
    commands,
    (command) => {
      attempted.push(plain(command));
      return requests[attempted.length - 1].promise;
    },
    (command, result) => observed.push([plain(command), plain(result)]),
    () => true,
  );

  await tick();
  assert.deepStrictEqual(attempted.map((command) => command.line), [2]);
  assert.deepStrictEqual(observed, []);
  requests[0].resolve({ failed: false, out: "Goal 1/1" });
  await tick();
  assert.deepStrictEqual(attempted.map((command) => command.line), [2, 4]);
  requests[1].resolve({ failed: false, out: "No open goals" });
  await tick();
  assert.deepStrictEqual(attempted.map((command) => command.line), [2, 4, 5]);
  requests[2].resolve({ failed: false, out: "QED." });

  assert.deepStrictEqual(plain(await execution), {
    completed: true,
    stoppedLine: null,
    interrupted: false,
  });
  assert.deepStrictEqual(observed.map(([command]) => command.line), [2, 4, 5]);
  assert.deepStrictEqual(forbiddenCalls, []);
}

async function failuresStopAtTheirOriginalLineAndAreObservedOnce() {
  const commands = [
    { line: 1, text: "pa prove 0 = 0" },
    { line: 3, text: "exact missing" },
    { line: 4, text: "qed" },
  ];
  const attempted = [];
  const observed = [];
  const result = await context.executePastedCommands(
    commands,
    async (command) => {
      attempted.push(command.line);
      return command.line === 3
        ? { failed: true, out: "Tactic error: unknown hypothesis 'missing'.", download: null }
        : { failed: false, out: "Goal 1/1", download: null };
    },
    (command, response) => observed.push([command.line, plain(response)]),
    () => true,
  );

  assert.deepStrictEqual(plain(result), {
    completed: false,
    stoppedLine: 3,
    interrupted: false,
  });
  assert.deepStrictEqual(attempted, [1, 3]);
  assert.deepStrictEqual(observed.map(([line]) => line), [1, 3]);
  assert.strictEqual(observed[1][1].failed, true);
}

async function rejectedRunsBecomeObservedFailuresWithoutEscaping() {
  const command = { line: 7, text: "ring" };
  const observed = [];
  const result = await context.executePastedCommands(
    [command],
    async () => { throw new Error("worker transport failed"); },
    (item, response) => observed.push([plain(item), plain(response)]),
    () => true,
  );

  assert.deepStrictEqual(plain(result), {
    completed: false,
    stoppedLine: 7,
    interrupted: false,
  });
  assert.strictEqual(observed.length, 1);
  assert.strictEqual(observed[0][1].failed, true);
  assert.ok(observed[0][1].out.includes("worker transport failed"));

  const malformed = [];
  const invalidResult = await context.executePastedCommands(
    [{ line: 11, text: "refl" }],
    async () => ({ out: "missing structured status" }),
    (item, response) => malformed.push([plain(item), plain(response)]),
    () => true,
  );
  assert.deepStrictEqual(plain(invalidResult), {
    completed: false,
    stoppedLine: 11,
    interrupted: false,
  });
  assert.strictEqual(malformed.length, 1);
  assert.strictEqual(malformed[0][1].failed, true);
  assert.ok(malformed[0][1].out.includes("Invalid proof-worker response"));
}

async function generationChangeSuppressesStaleOutputAndAllLaterCommands() {
  const commands = [
    { line: 1, text: "pa prove 0 = 0" },
    { line: 2, text: "refl" },
    { line: 3, text: "qed" },
  ];
  const first = deferred();
  let live = true;
  const attempted = [];
  const observed = [];
  const execution = context.executePastedCommands(
    commands,
    (command) => { attempted.push(command.line); return first.promise; },
    (command, response) => observed.push([command.line, response]),
    () => live,
  );
  await tick();
  live = false;
  first.resolve({ failed: false, out: "stale goal state" });

  assert.deepStrictEqual(plain(await execution), {
    completed: false,
    stoppedLine: 1,
    interrupted: true,
  });
  assert.deepStrictEqual(attempted, [1]);
  assert.deepStrictEqual(observed, []);

  live = true;
  const beforeNext = await context.executePastedCommands(
    commands,
    async () => ({ failed: false, out: "ok" }),
    () => { live = false; },
    () => live,
  );
  assert.deepStrictEqual(plain(beforeNext), {
    completed: false,
    stoppedLine: 2,
    interrupted: true,
  });
}

async function executorCannotClaimHistoryOrDownloadAuthority() {
  const attempted = [];
  const observed = [];
  const commands = [
    { line: 1, text: "script download" },
    { line: 2, text: "qed" },
  ];
  const result = await context.executePastedCommands(
    commands,
    async (command) => {
      attempted.push(command.text);
      return {
        failed: false,
        out: "preview",
        download: "pa prove 0 = 0\nrefl\nqed\n",
      };
    },
    (command, response) => observed.push([command.text, response.download]),
    () => true,
  );

  assert.strictEqual(result.completed, true);
  assert.deepStrictEqual(attempted, ["script download", "qed"]);
  assert.deepStrictEqual(observed.map(([text]) => text), attempted);
  assert.deepStrictEqual(forbiddenCalls, []);
}

(async () => {
  browserEventsRouteOnlyBoundedMultilineInputAndRestoreFocus();
  preparationAcceptsPortableTextAndPreservesSourceLines();
  preparationRejectsEveryUnsafeOrAmbiguousShape();
  await executionIsStrictlySequentialAndObservesSettledResults();
  await failuresStopAtTheirOriginalLineAndAreObservedOnce();
  await rejectedRunsBecomeObservedFailuresWithoutEscaping();
  await generationChangeSuppressesStaleOutputAndAllLaterCommands();
  await executorCannotClaimHistoryOrDownloadAuthority();
})().catch((error) => {
  console.error(error.stack || String(error));
  process.exitCode = 1;
});
