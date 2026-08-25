"use strict";

// Execute the real selected-theorem frontend against a small browser DOM.
const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const { TextEncoder } = require("util");

const script = process.argv[2] || path.resolve(
  __dirname, "../../../book/_static/lean-selector/lean-selector.js",
);
const source = fs.readFileSync(script, "utf8");

class Element {
  constructor(tag) {
    this.tagName = String(tag).toUpperCase();
    this.children = [];
    this.parentNode = null;
    this.attributes = {};
    this.listeners = {};
    this.className = "";
    this._text = "";
    this.hidden = false;
    this.disabled = false;
    this.value = 0;
  }

  get classList() {
    return { contains: (name) => this.className.split(/\s+/).includes(name) };
  }

  get textContent() {
    return this._text + this.children.map((child) => child.textContent).join("");
  }

  set textContent(value) {
    this._text = String(value);
  }

  get nextElementSibling() {
    if (!this.parentNode) return null;
    const position = this.parentNode.children.indexOf(this);
    return this.parentNode.children[position + 1] || null;
  }

  appendChild(child) {
    child.parentNode = this;
    this.children.push(child);
    return child;
  }

  removeChild(child) {
    this.children.splice(this.children.indexOf(child), 1);
    child.parentNode = null;
    return child;
  }

  setAttribute(name, value) {
    this.attributes[name] = String(value);
  }

  getAttribute(name) {
    return Object.prototype.hasOwnProperty.call(this.attributes, name)
      ? this.attributes[name] : null;
  }

  removeAttribute(name) {
    delete this.attributes[name];
    if (name === "href") delete this.href;
  }

  addEventListener(name, callback) {
    (this.listeners[name] || (this.listeners[name] = [])).push(callback);
  }

  click() {
    if (this.disabled) return;
    (this.listeners.click || []).forEach((callback) => callback({ target: this }));
  }

  matches(selector) {
    if (selector === "dt") return this.tagName === "DT";
    if (selector === "[data-graph-title]") {
      return this.getAttribute("data-graph-title") !== null;
    }
    if (selector === "[data-lean-selector-host]") {
      return this.getAttribute("data-lean-selector-host") !== null;
    }
    if (selector.startsWith(".")) {
      return this.classList.contains(selector.slice(1));
    }
    return false;
  }

  querySelectorAll(selector) {
    const output = [];
    for (const child of this.children) {
      if (child.matches(selector)) output.push(child);
      output.push(...child.querySelectorAll(selector));
    }
    return output;
  }

  querySelector(selector) {
    return this.querySelectorAll(selector)[0] || null;
  }
}

function response(payload, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(payload),
  };
}

function browser(options = {}) {
  const panel = new Element("aside");
  panel.className = options.defined ? "pd-graph-details" : "pa-graph-details";
  const title = panel.appendChild(new Element("h2"));
  title.setAttribute("data-graph-title", "");
  title.textContent = options.title || "PA000F · add_comm";

  const timers = new Map();
  const observers = [];
  const calls = [];
  const responses = [];
  let nextTimer = 0;
  const document = {
    body: new Element("body"),
    readyState: "complete",
    createElement: (tag) => new Element(tag),
    querySelector(selector) {
      if (selector === "meta[name='peano-lean-strand-api']") return null;
      if (selector === "header h1") return null;
      return this.body.querySelector(selector);
    },
    querySelectorAll(selector) {
      if (selector.includes(".pa-graph-details") || selector.includes(".pd-graph-details")) {
        return [panel];
      }
      return this.body.querySelectorAll(selector);
    },
    addEventListener() {},
  };
  document.body.appendChild(panel);
  const nodes = options.nodes || [
    {
      id: "PA000F", tag: "PA000F", name: "add_comm", kind: "theorem",
      stable_member: true, alpha_checked_use: true, alpha_evidence: "stable_closed", scope: "public",
    },
    {
      id: "PA000H", tag: "PA000H", name: "mul_comm", kind: "theorem",
      stable_member: true, alpha_checked_use: true, alpha_evidence: "stable_closed", scope: "public",
    },
    {
      id: "PA00FW", tag: "PA00FW", name: "quadratic_reciprocity_combined", kind: "theorem",
      stable_member: false, alpha_checked_use: true, alpha_evidence: "alpha_closed", scope: "candidate",
    },
    {
      id: "KU0003", tag: "KU0003", name: "division_add_quotient_bit", kind: "theorem",
      stable_member: null, alpha_checked_use: true, alpha_evidence: "alpha_closed", scope: "candidate",
    },
    {
      id: "KU0004", tag: "KU0004", name: "division_add_quotient_lower", kind: "theorem",
      stable_member: null, alpha_checked_use: false, alpha_evidence: null, scope: "candidate",
    },
    {
      id: "PF0000", tag: "PF0000", name: "pythagorean_double_product", kind: "theorem",
      stable_member: null, alpha_checked_use: true, alpha_evidence: "alpha_closed", scope: "candidate",
      status: "Alpha v19 checked-use; independently kernel and Lean verified; not Stable",
    },
    { id: "PD0001", tag: "PD0001", name: "Prime", kind: "definition" },
  ];
  const model = {
    nodes,
    adjacency: {
      PA000F: { ancestors: ["PA0001", "PA000E"] },
      PA00FW: { ancestors: Array.from({ length: 556 }, (_, index) => "NODE" + index) },
    },
  };
  if (options.defined) model.proof_adjacency = model.adjacency;
  const location = new URL("https://proof.example.test/book/_static/pa-proof-explorer/graph.html?target=PA000F");
  const sandbox = {
    document,
    location,
    URL,
    TextEncoder,
    AbortController,
    Promise,
    WeakMap,
    console,
    setTimeout(callback, delay) {
      const identifier = ++nextTimer;
      timers.set(identifier, { callback, delay });
      return identifier;
    },
    clearTimeout(identifier) { timers.delete(identifier); },
    fetch(url, request) {
      calls.push({ url: String(url), request });
      if (!responses.length) return Promise.reject(new Error("unexpected fetch: " + url));
      const next = responses.shift();
      if (next instanceof Error) return Promise.reject(next);
      return Promise.resolve(next);
    },
    MutationObserver: class {
      constructor(callback) {
        this.callback = callback;
        observers.push(this);
      }
      observe(target, configuration) {
        this.target = target;
        this.configuration = configuration;
      }
      disconnect() { this.disconnected = true; }
    },
  };
  sandbox.window = sandbox;
  if (options.defined) sandbox.PA_DEFINED_GRAPH = model;
  else sandbox.PA_PROOF_GRAPH = model;
  vm.runInNewContext(source, sandbox, { filename: "lean-selector.js" });

  async function settle() {
    for (let count = 0; count < 8; count += 1) await Promise.resolve();
    await new Promise((resolve) => setImmediate(resolve));
  }

  async function runTimer(delay) {
    const match = [...timers].find(([, entry]) => entry.delay === delay);
    assert.ok(match, `missing ${delay}-millisecond browser timer`);
    timers.delete(match[0]);
    match[1].callback();
    await settle();
  }

  async function changeTitle(value) {
    title.textContent = value;
    observers.forEach((observer) => observer.callback([{ target: title }]));
    await runTimer(0);
    await settle();
  }

  return { panel, title, document, sandbox, calls, responses, timers, observers, settle, runTimer, changeTitle };
}

function snapshot(theorem, edition, id, status, extra = {}) {
  return Object.assign({
    job_id: id,
    status,
    state: status,
    theorem,
    edition,
    stage: status,
    progress: { current: 0, total: 3, percent: 0 },
  }, extra);
}

async function stableProofBuildProgressDownloadsAndLive() {
  const env = browser();
  const card = env.panel.querySelector(".peano-lean-selector");
  assert.ok(card, "the actual graph selection was enhanced");
  assert.match(card.textContent, /add_comm/);
  assert.match(card.textContent, /Stable/);
  assert.match(card.querySelector(".pls-build").textContent, /^Build Lean proof$/);
  assert.match(card.querySelector(".pls-status").textContent, /one bounded proof worker only when clicked/);
  assert.strictEqual(env.observers[0].target, env.title, "progress mutations never retrigger selection observation");
  assert.strictEqual(env.calls.length, 0, "loading a graph must not start any proof job");

  env.responses.push(response(snapshot("add_comm", "stable", "job-one", "queued"), 202));
  card.querySelector(".pls-build").click();
  await env.settle();
  assert.strictEqual(env.calls.length, 1);
  assert.strictEqual(env.calls[0].url, "/api/lean-strands/jobs");
  assert.strictEqual(env.calls[0].request.method, "POST");
  assert.deepStrictEqual(JSON.parse(env.calls[0].request.body), {
    theorem: "add_comm", edition: "stable",
  });

  env.responses.push(response(snapshot("add_comm", "stable", "job-one", "running", {
    stage: "reconstructing_proofs", progress: { current: 2, total: 3, percent: 67 },
  })));
  await env.runTimer(750);
  assert.match(card.querySelector(".pls-stage").textContent, /reconstructing proofs/);
  assert.match(card.querySelector(".pls-counter").textContent, /2 \/ 3.*67%/);
  assert.strictEqual(card.querySelector(".pls-progress").value, 67);

  env.responses.push(response(snapshot("add_comm", "stable", "job-one", "completed", {
    lean_verified: true,
    live_status: "ready",
    progress: { current: 3, total: 3, percent: 100 },
    downloads: {
      lean: "/api/lean-strands/jobs/job-one/download?format=lean",
      zip: "/api/lean-strands/jobs/job-one/download?format=zip",
    },
    live_compatible: true,
    live_url: "https://live.lean-lang.org/#code=theorem%20ok",
  })));
  await env.runTimer(750);
  assert.strictEqual(card.querySelector(".pls-progress").value, 100);
  assert.strictEqual(card.querySelector(".pls-link").hidden, false);
  assert.strictEqual(card.querySelector(".pls-live").hidden, false);
  assert.match(card.querySelector(".pls-status").textContent, /Independently Lean-verified/);
  assert.match(card.textContent, /Verified Lean package/);
  assert.strictEqual(card.querySelector(".pls-live").target, "_blank");
  assert.strictEqual(card.querySelector(".pls-build").disabled, false);
}

async function alphaAndUncheckedDefinitionsAreTruthful() {
  const alpha = browser({ defined: true, title: "KU0003 · division_add_quotient_bit" });
  let card = alpha.panel.querySelector(".peano-lean-selector");
  assert.ok(card);
  assert.match(card.textContent, /Alpha/);
  alpha.responses.push(response(snapshot("division_add_quotient_bit", "alpha", "alpha-1", "queued"), 202));
  card.querySelector(".pls-build").click();
  await alpha.settle();
  assert.strictEqual(JSON.parse(alpha.calls[0].request.body).edition, "alpha");

  const frontier = browser({ defined: true, title: "PF0000 · pythagorean_double_product" });
  card = frontier.panel.querySelector(".peano-lean-selector");
  assert.match(card.textContent, /pythagorean_double_product/);
  assert.match(card.textContent, /Alpha/);
  assert.strictEqual(card.querySelector(".pls-build").disabled, false);
  frontier.responses.push(response(snapshot("pythagorean_double_product", "alpha", "frontier-1", "queued"), 202));
  card.querySelector(".pls-build").click();
  await frontier.settle();
  assert.deepStrictEqual(JSON.parse(frontier.calls[0].request.body), {
    theorem: "pythagorean_double_product", edition: "alpha",
  });

  const unchecked = browser({ defined: true, title: "KU0004 · division_add_quotient_lower" });
  card = unchecked.panel.querySelector(".peano-lean-selector");
  assert.ok(card);
  assert.strictEqual(card.querySelector(".pls-build").disabled, true);
  assert.match(card.querySelector(".pls-status").textContent, /no closed checked-use authority/);
  card.querySelector(".pls-build").click();
  assert.strictEqual(unchecked.calls.length, 0);

  const definition = browser({ defined: true, title: "PD0001 · Prime" });
  const disabled = definition.panel.querySelector(".peano-lean-selector");
  assert.ok(disabled, "definition selections explain the absent theorem authority");
  assert.strictEqual(disabled.querySelector(".pls-build").disabled, true);
  assert.match(disabled.querySelector(".pls-status").textContent, /notation, not theorem proofs/);

  const unproven = browser({
    defined: true,
    title: "XX0001 · draft_only",
    nodes: [{ id: "XX0001", tag: "XX0001", name: "draft_only", kind: "theorem", scope: "candidate" }],
  });
  const denied = unproven.panel.querySelector(".peano-lean-selector");
  assert.strictEqual(denied.querySelector(".pls-build").disabled, true,
    "missing Alpha checked-use evidence fails closed");
}

async function cancellationAndTheoremSwitchStopTheExactJob() {
  const env = browser();
  let card = env.panel.querySelector(".peano-lean-selector");
  env.responses.push(response(snapshot("add_comm", "stable", "cancel-1", "running"), 202));
  card.querySelector(".pls-build").click();
  await env.settle();
  env.responses.push(response(snapshot("add_comm", "stable", "cancel-1", "cancelled")));
  card.querySelector(".pls-cancel").click();
  await env.settle();
  assert.strictEqual(env.calls[1].request.method, "DELETE");
  assert.strictEqual(env.calls[1].url, "/api/lean-strands/jobs/cancel-1");
  assert.match(card.querySelector(".pls-status").textContent, /cancelled/);

  const switcher = browser();
  card = switcher.panel.querySelector(".peano-lean-selector");
  switcher.responses.push(response(snapshot("add_comm", "stable", "switch-1", "running"), 202));
  card.querySelector(".pls-build").click();
  await switcher.settle();
  switcher.responses.push(response(snapshot("add_comm", "stable", "switch-1", "cancelled")));
  await switcher.changeTitle("PA000H · mul_comm");
  const replacement = switcher.panel.querySelector(".peano-lean-selector");
  assert.notStrictEqual(replacement, card);
  assert.match(replacement.textContent, /mul_comm/);
  assert.strictEqual(switcher.calls[1].request.method, "DELETE");
  assert.strictEqual(switcher.calls.length, 2, "selection changes never auto-build");
}

async function serviceErrorsAndMismatchedJobsFailClosed() {
  const env = browser();
  const card = env.panel.querySelector(".peano-lean-selector");
  env.responses.push(response({ error: "One bounded proof job is already running." }, 409));
  card.querySelector(".pls-build").click();
  await env.settle();
  assert.match(card.querySelector(".pls-status").textContent, /already running/);
  assert.match(card.querySelector(".pls-build").textContent, /Retry/);

  env.responses.push(response(snapshot("mul_comm", "stable", "wrong-job", "queued"), 202));
  card.querySelector(".pls-build").click();
  await env.settle();
  assert.match(card.querySelector(".pls-status").textContent, /untrusted theorem job/);

  const poll = browser();
  const second = poll.panel.querySelector(".peano-lean-selector");
  poll.responses.push(response(snapshot("add_comm", "stable", "honest", "queued"), 202));
  second.querySelector(".pls-build").click();
  await poll.settle();
  poll.responses.push(response(snapshot("mul_comm", "stable", "honest", "running")));
  await poll.runTimer(750);
  assert.match(second.querySelector(".pls-status").textContent, /no longer matches/);
}

async function externalUrlsAndOversizedLiveLinksAreNeverTrusted() {
  const env = browser();
  const api = env.sandbox.PeanoLeanSelector;
  assert.ok(api.safeLiveUrl("https://live.lean-lang.org/#code=theorem%20x"));
  for (const candidate of [
    null,
    "http://live.lean-lang.org/#code=x",
    "https://evil.invalid/#code=x",
    "https://live.lean-lang.org/other#code=x",
    "https://live.lean-lang.org/?x=1#code=x",
    "https://user@live.lean-lang.org/#code=x",
    "https://live.lean-lang.org/#url=https%3A%2F%2Fexample.invalid",
    "https://live.lean-lang.org/#code=" + "x".repeat(9000),
  ]) {
    assert.strictEqual(api.safeLiveUrl(candidate), null, String(candidate));
  }

  const card = env.panel.querySelector(".peano-lean-selector");
  env.responses.push(response(snapshot("add_comm", "stable", "safe-1", "queued"), 202));
  card.querySelector(".pls-build").click();
  await env.settle();
  env.responses.push(response(snapshot("add_comm", "stable", "safe-1", "completed", {
    lean_verified: true,
    downloads: {
      lean: "https://evil.invalid/download?format=lean",
      zip: "/api/lean-strands/jobs/other/download?format=zip",
    },
    live_url: "https://evil.invalid/#code=stolen",
    live_compatible: true,
  })));
  await env.runTimer(750);
  for (const link of card.querySelectorAll(".pls-link")) assert.strictEqual(link.hidden, true);

  const crossOrigin = browser();
  crossOrigin.sandbox.PEANO_LEAN_STRAND_API = "https://evil.invalid/api/lean-strands";
  const unsafe = crossOrigin.panel.querySelector(".peano-lean-selector");
  unsafe.querySelector(".pls-build").click();
  assert.match(unsafe.querySelector(".pls-status").textContent, /same origin/);
  assert.strictEqual(crossOrigin.calls.length, 0);
}

async function largeDefaultSelectionDoesNotRunAutomatically() {
  const env = browser({ title: "PA00FW · quadratic_reciprocity_combined" });
  const card = env.panel.querySelector(".peano-lean-selector");
  assert.ok(card);
  assert.match(card.textContent, /quadratic_reciprocity_combined/);
  assert.match(card.querySelector(".pls-status").textContent, /557 recorded theorem nodes/);
  assert.match(card.querySelector(".pls-status").textContent, /256-node default service limit/);
  assert.strictEqual(env.calls.length, 0);
}

async function verifiedStandaloneAndCompanionStatusesRemainHonest() {
  const unchecked = browser();
  let card = unchecked.panel.querySelector(".peano-lean-selector");
  unchecked.responses.push(response(snapshot("add_comm", "stable", "verify-1", "queued"), 202));
  card.querySelector(".pls-build").click();
  await unchecked.settle();
  unchecked.responses.push(response(snapshot("add_comm", "stable", "verify-1", "completed", {
    lean_verified: false,
    downloads: { lean: "/api/lean-strands/jobs/verify-1/download?format=lean" },
  })));
  await unchecked.runTimer(750);
  assert.match(card.querySelector(".pls-status").textContent, /did not authenticate successful independent Lean verification/);
  assert.strictEqual(card.querySelector(".pls-link").hidden, true);

  const oversized = browser();
  card = oversized.panel.querySelector(".peano-lean-selector");
  oversized.responses.push(response(snapshot("add_comm", "stable", "large-1", "queued"), 202));
  card.querySelector(".pls-build").click();
  await oversized.settle();
  oversized.responses.push(response(snapshot("add_comm", "stable", "large-1", "completed", {
    lean_verified: true,
    lean_live: { status: "oversized", compatible: true, url: null },
    downloads: { lean: "/api/lean-strands/jobs/large-1/download?format=lean" },
  })));
  await oversized.runTimer(750);
  assert.match(card.querySelector(".pls-status").textContent, /Standalone Lean source.*exceeds Lean Live/);
  assert.strictEqual(card.querySelector(".pls-link").hidden, false);
  assert.strictEqual(card.querySelector(".pls-live").hidden, true);

  const fallback = browser();
  card = fallback.panel.querySelector(".peano-lean-selector");
  fallback.responses.push(response(snapshot("add_comm", "stable", "mixed-1", "queued"), 202));
  card.querySelector(".pls-build").click();
  await fallback.settle();
  fallback.responses.push(response(snapshot("add_comm", "stable", "mixed-1", "completed", {
    lean_verified: true,
    manifest: { fallback_node_count: 2 },
    downloads: { lean: "/api/lean-strands/jobs/mixed-1/download?format=lean" },
    live_compatible: true,
    live_url: "https://live.lean-lang.org/#code=fake",
  })));
  await fallback.runTimer(750);
  assert.match(card.querySelector(".pls-status").textContent, /certificate-backed proof requires the configured Lean companion/);
  assert.match(card.querySelector(".pls-link").textContent, /companion-backed/);
  assert.strictEqual(card.querySelector(".pls-live").hidden, true,
    "certificate-dependent proofs cannot be represented as standalone Lean Live links");
}

(async function () {
  await stableProofBuildProgressDownloadsAndLive();
  await alphaAndUncheckedDefinitionsAreTruthful();
  await cancellationAndTheoremSwitchStopTheExactJob();
  await serviceErrorsAndMismatchedJobsFailClosed();
  await externalUrlsAndOversizedLiveLinksAreNeverTrusted();
  await largeDefaultSelectionDoesNotRunAutomatically();
  await verifiedStandaloneAndCompanionStatusesRemainHonest();
  process.stdout.write("Lean theorem selector browser interactions passed.\n");
}()).catch(function (error) {
  console.error(error.stack || String(error));
  process.exitCode = 1;
});
