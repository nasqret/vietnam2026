/* On-demand, same-origin Lean proof jobs for authenticated theorem selectors. */
(function (global) {
  "use strict";

  if (!global || !global.document) return;
  var document = global.document;
  var NAME = /^[A-Za-z][A-Za-z0-9_]{0,199}$/;
  var JOB = /^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/;
  var POLL_MILLISECONDS = 750;
  var REQUEST_MILLISECONDS = 20000;
  var LIVE_MAX_BYTES = 8192;
  var DEFAULT_MAX_NODES = 256;
  var PANEL_SELECTOR = ".pa-graph-details, .pd-graph-details, .pa-proof-sidebar, .pd-theorem-layout > aside, [data-lean-selector-host]";
  var instances = new WeakMap();
  var refreshQueued = false;

  function text(value, maximum) {
    var result = String(value === undefined || value === null ? "" : value);
    return result.length > maximum ? result.slice(0, maximum - 1) + "…" : result;
  }

  function bytes(value) {
    if (typeof global.TextEncoder === "function") {
      return new global.TextEncoder().encode(String(value)).length;
    }
    return unescape(encodeURIComponent(String(value))).length;
  }

  function apiRoot() {
    var meta = document.querySelector("meta[name='peano-lean-strand-api']");
    var selected = global.PEANO_LEAN_STRAND_API ||
      (meta && meta.getAttribute("content")) || "/api/lean-strands";
    var endpoint = new URL(String(selected), global.location.href);
    if (endpoint.origin !== global.location.origin || endpoint.username ||
        endpoint.password || endpoint.search || endpoint.hash) {
      throw new Error("The Lean proof service must use the same origin.");
    }
    return endpoint.pathname.replace(/\/$/, "");
  }

  function safeLiveUrl(candidate) {
    if (typeof candidate !== "string" || !candidate || bytes(candidate) > LIVE_MAX_BYTES) {
      return null;
    }
    try {
      var parsed = new URL(candidate);
      if (parsed.protocol !== "https:" || parsed.hostname !== "live.lean-lang.org" ||
          parsed.port || parsed.username || parsed.password || parsed.pathname !== "/" ||
          parsed.search || parsed.hash.indexOf("#code=") !== 0 || parsed.hash.length <= 6) {
        return null;
      }
      return parsed.href;
    } catch (_error) {
      return null;
    }
  }

  function safeDownload(candidate, id, format) {
    if (typeof candidate !== "string" || !JOB.test(id)) return null;
    try {
      var selected = new URL(candidate, global.location.href);
      var expected = apiRoot() + "/jobs/" + encodeURIComponent(id) + "/download";
      if (selected.origin !== global.location.origin || selected.pathname !== expected ||
          selected.username || selected.password || selected.hash ||
          selected.searchParams.get("format") !== format ||
          Array.from(selected.searchParams.keys()).length !== 1) return null;
      return selected.pathname + selected.search;
    } catch (_error) {
      return null;
    }
  }

  function make(tag, className, label) {
    var element = document.createElement(tag);
    if (className) element.className = className;
    if (label !== undefined) element.textContent = label;
    return element;
  }

  function button(label, className) {
    var control = make("button", className, label);
    control.type = "button";
    return control;
  }

  function jobState(snapshot) {
    return String(snapshot && (snapshot.state || snapshot.status) || "queued").toLowerCase();
  }

  function updateProgress(instance, snapshot) {
    var details = snapshot.progress && typeof snapshot.progress === "object" ?
      snapshot.progress : {};
    var completed = Number(snapshot.completed !== undefined ? snapshot.completed : details.current || 0);
    var total = Number(snapshot.total !== undefined ? snapshot.total : details.total || 0);
    var percent = Number(snapshot.percent !== undefined ? snapshot.percent : details.percent || 0);
    if (!Number.isFinite(completed) || completed < 0) completed = 0;
    if (!Number.isFinite(total) || total < 0) total = 0;
    if (!Number.isFinite(percent)) percent = total ? 100 * completed / total : 0;
    percent = Math.max(0, Math.min(100, Math.round(percent)));
    instance.progress.hidden = false;
    instance.progress.max = 100;
    instance.progress.value = percent;
    instance.counter.textContent = total ?
      completed + " / " + total + " theorem nodes · " + percent + "%" :
      percent + "%";
    instance.stage.textContent = text(snapshot.stage || jobState(snapshot), 100)
      .replace(/_/g, " ");
  }

  function resetLinks(instance) {
    [instance.lean, instance.archive, instance.live].forEach(function (link) {
      link.hidden = true;
      link.removeAttribute("href");
    });
  }

  function finish(instance, snapshot) {
    clearTimer(instance);
    instance.running = false;
    instance.build.disabled = !instance.eligible;
    instance.cancel.hidden = true;
    var state = jobState(snapshot);
    updateProgress(instance, snapshot);
    if (state === "completed") {
      if (snapshot.lean_verified !== true) {
        fail(instance, new Error("The service did not authenticate successful independent Lean verification."));
        return;
      }
      instance.progress.value = 100;
      instance.build.textContent = "Build Lean proof again";
      var downloads = snapshot.downloads || snapshot.download_urls || {};
      var lean = safeDownload(downloads.lean, instance.jobId, "lean");
      var zip = safeDownload(downloads.zip, instance.jobId, "zip");
      var liveStatus = snapshot.live_status ||
        (snapshot.lean_live && snapshot.lean_live.status) || "unavailable";
      var mixed = snapshot.companion_required === true || liveStatus === "fallback_required" ||
        !!(snapshot.manifest && Number(snapshot.manifest.fallback_node_count) > 0);
      if (mixed) {
        instance.status.textContent = "Independently Lean-verified. This certificate-backed proof requires the configured Lean companion project.";
      } else if (liveStatus === "oversized") {
        instance.status.textContent = "Independently Lean-verified. Standalone Lean source is available for download, but exceeds Lean Live's share limit.";
      } else {
        instance.status.textContent = "Independently Lean-verified: the compiler accepted this selected theorem and its proof strand.";
      }
      if (lean) {
        instance.lean.href = lean;
        instance.lean.textContent = mixed ? "Download companion-backed .lean" :
          "Download standalone .lean";
        instance.lean.hidden = false;
      }
      if (zip) {
        instance.archive.href = zip;
        instance.archive.hidden = false;
      }
      var live = snapshot.live_url || (snapshot.lean_live && snapshot.lean_live.url);
      live = safeLiveUrl(live);
      if (live && !mixed && snapshot.live_compatible !== false) {
        instance.live.href = live;
        instance.live.hidden = false;
      }
    } else if (state === "cancelled" || state === "canceled") {
      instance.status.textContent = "Proof construction cancelled.";
      instance.build.textContent = "Build Lean proof";
    } else {
      instance.status.textContent = text(snapshot.error || "Lean proof construction failed.", 320);
      instance.build.textContent = "Retry Build";
    }
  }

  function clearTimer(instance) {
    if (instance.timer !== null) {
      global.clearTimeout(instance.timer);
      instance.timer = null;
    }
  }

  function request(instance, url, options) {
    var controller = typeof global.AbortController === "function" ?
      new global.AbortController() : null;
    if (controller) {
      options.signal = controller.signal;
      instance.controller = controller;
    }
    options.credentials = "same-origin";
    var timeout = global.setTimeout(function () {
      if (controller) controller.abort();
    }, REQUEST_MILLISECONDS);
    return global.fetch(url, options).then(function (response) {
      if (!response || !response.ok) {
        return Promise.resolve(response && response.json ? response.json() : null)
          .catch(function () { return null; })
          .then(function (payload) {
            throw new Error(text(payload && payload.error ||
              "Lean service unavailable (HTTP " + (response && response.status || 0) + ").", 260));
          });
      }
      return response.json();
    }).finally(function () {
      global.clearTimeout(timeout);
      if (instance.controller === controller) instance.controller = null;
    });
  }

  function fail(instance, error) {
    if (instance.disposed) return;
    clearTimer(instance);
    instance.running = false;
    instance.cancel.hidden = true;
    instance.build.disabled = !instance.eligible;
    instance.build.textContent = "Retry Build";
    instance.status.textContent = text(error && error.message ||
      "Lean proof service could not be reached.", 320);
    instance.stage.textContent = "failed";
  }

  function poll(instance) {
    if (instance.disposed || !instance.running || !JOB.test(instance.jobId)) return;
    var endpoint;
    try {
      endpoint = apiRoot() + "/jobs/" + encodeURIComponent(instance.jobId);
    } catch (error) {
      fail(instance, error);
      return;
    }
    request(instance, endpoint, { method: "GET" }).then(function (snapshot) {
      if (instance.disposed || !instance.running) return;
      if (snapshot.theorem !== instance.theorem || snapshot.edition !== instance.edition ||
          String(snapshot.job_id || "") !== instance.jobId) {
        throw new Error("The Lean job no longer matches the selected checked theorem.");
      }
      var state = jobState(snapshot);
      if (state === "completed" || state === "failed" ||
          state === "cancelled" || state === "canceled") {
        finish(instance, snapshot);
      } else {
        updateProgress(instance, snapshot);
        instance.status.textContent = "Building the selected theorem in a bounded background job.";
        instance.timer = global.setTimeout(function () { poll(instance); }, POLL_MILLISECONDS);
      }
    }).catch(function (error) {
      if (!instance.disposed) fail(instance, error);
    });
  }

  function start(instance) {
    if (!instance.eligible || instance.running || instance.disposed) return;
    var endpoint;
    try {
      endpoint = apiRoot() + "/jobs";
    } catch (error) {
      fail(instance, error);
      return;
    }
    instance.running = true;
    instance.build.disabled = true;
    instance.cancel.hidden = false;
    instance.status.textContent = "Submitting the selected checked theorem…";
    instance.stage.textContent = "queued";
    instance.counter.textContent = "0%";
    instance.progress.hidden = false;
    instance.progress.value = 0;
    resetLinks(instance);
    request(instance, endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify({ theorem: instance.theorem, edition: instance.edition })
    }).then(function (snapshot) {
      if (instance.disposed) return;
      var id = String(snapshot.job_id || "");
      if (!JOB.test(id) || snapshot.theorem !== instance.theorem ||
          snapshot.edition !== instance.edition) {
        throw new Error("The Lean service returned an untrusted theorem job.");
      }
      instance.jobId = id;
      updateProgress(instance, snapshot);
      var state = jobState(snapshot);
      if (state === "completed" || state === "failed" || state === "cancelled") {
        finish(instance, snapshot);
      } else {
        instance.timer = global.setTimeout(function () { poll(instance); }, POLL_MILLISECONDS);
      }
    }).catch(function (error) { fail(instance, error); });
  }

  function cancel(instance, quiet) {
    clearTimer(instance);
    if (instance.controller) instance.controller.abort();
    var id = instance.jobId;
    instance.running = false;
    instance.cancel.hidden = true;
    instance.build.disabled = !instance.eligible;
    if (!quiet) instance.status.textContent = "Cancelling the selected Lean proof job…";
    if (!JOB.test(id || "")) {
      if (!quiet) finish(instance, { state: "cancelled", stage: "cancelled", progress: {} });
      return Promise.resolve();
    }
    var endpoint;
    try {
      endpoint = apiRoot() + "/jobs/" + encodeURIComponent(id);
    } catch (error) {
      if (!quiet) fail(instance, error);
      return Promise.resolve();
    }
    return global.fetch(endpoint, {
      method: "DELETE",
      credentials: "same-origin",
      headers: { "Accept": "application/json" }
    }).then(function (response) {
      if (!response.ok) throw new Error("The Lean proof job could not be cancelled.");
      return response.json();
    }).then(function (snapshot) {
      if (!quiet && !instance.disposed) finish(instance, snapshot);
    }).catch(function (error) {
      if (!quiet && !instance.disposed) fail(instance, error);
    });
  }

  function describeModel(panel) {
    var explicit = global.PA_PROOF_GRAPH;
    var defined = global.PA_DEFINED_GRAPH;
    var title = panel.querySelector("[data-graph-title]");
    var model = title && panel.classList.contains("pd-graph-details") ? defined : explicit;
    if (title && (!model || !Array.isArray(model.nodes))) model = defined || explicit;
    if (title && model && Array.isArray(model.nodes)) {
      var label = String(title.textContent || "");
      var separator = label.indexOf(" · ");
      if (separator < 0) return null;
      var tag = label.slice(0, separator).trim();
      var node = model.nodes.find(function (item) {
        return item && (item.id === tag || item.tag === tag);
      });
      if (!node || !NAME.test(node.name || "")) return null;
      var stable = node.stable_member === true || node.scope === "public";
      var definition = node.kind === "definition";
      var adjacency = (model.adjacency || model.proof_adjacency || {})[tag];
      var count = adjacency && Array.isArray(adjacency.ancestors) ?
        adjacency.ancestors.length + 1 : null;
      return {
        theorem: node.name,
        edition: stable ? "stable" : "alpha",
        eligible: !definition && (stable || node.alpha_checked_use === true),
        evidence: node.alpha_evidence || "unknown",
        kind: definition ? "definition" : "theorem",
        nodeCount: count
      };
    }
    var theorem = panel.getAttribute("data-lean-theorem") ||
      (document.querySelector("header h1") || {}).textContent || "";
    if (!NAME.test(String(theorem).trim())) return null;
    var metadata = {};
    panel.querySelectorAll("dt").forEach(function (term) {
      var next = term.nextElementSibling;
      if (next) metadata[String(term.textContent).trim()] = String(next.textContent).trim();
    });
    var edition = panel.getAttribute("data-lean-edition") ||
      (metadata["Stable membership"] === "yes" ? "stable" : "alpha");
    var stableMembership = metadata["Stable membership"] === "yes";
    var checkedUse = metadata["Checked theorem use"] === "yes" ||
      panel.getAttribute("data-lean-eligible") === "true";
    return {
      theorem: String(theorem).trim(),
      edition: edition,
      eligible: panel.getAttribute("data-lean-eligible") !== "false" &&
        (edition === "stable" ? stableMembership : checkedUse),
      evidence: metadata["Current release evidence"] || "unknown"
    };
  }

  function dispose(instance) {
    if (!instance) return;
    instance.disposed = true;
    if (instance.running) cancel(instance, true);
    clearTimer(instance);
    if (instance.card && instance.card.parentNode) instance.card.parentNode.removeChild(instance.card);
  }

  function mount(panel, descriptor) {
    if (!panel || !descriptor || !NAME.test(String(descriptor.theorem || "")) ||
        ["stable", "alpha"].indexOf(descriptor.edition) === -1) return null;
    var current = instances.get(panel);
    if (current && current.theorem === descriptor.theorem &&
        current.edition === descriptor.edition &&
        current.eligible === (descriptor.eligible !== false)) return current;
    if (current) dispose(current);

    var card = make("section", "peano-lean-selector");
    card.setAttribute("aria-label", "Independent Lean proof for " + descriptor.theorem);
    var kicker = make("p", "pls-kicker", "Independent proof export");
    var title = make("h3", "pls-title", "Build a Lean proof");
    var theorem = make("p", "pls-theorem", descriptor.theorem);
    var badge = make("span", "pls-edition", descriptor.edition === "stable" ? "Stable" : "Alpha");
    theorem.appendChild(badge);
    var stage = make("p", "pls-stage", "ready");
    var progress = make("progress", "pls-progress");
    progress.max = 100;
    progress.value = 0;
    progress.hidden = true;
    progress.setAttribute("aria-label", "Lean proof construction progress");
    var counter = make("p", "pls-counter", "");
    var statusMessage = descriptor.kind === "definition" ?
      "Definitions provide notation, not theorem proofs; Lean proof construction is unavailable." :
      descriptor.eligible === false ? "This theorem has no closed checked-use authority." :
      "Builds one bounded proof worker only when clicked.";
    if (descriptor.eligible !== false && Number(descriptor.nodeCount) > DEFAULT_MAX_NODES) {
      statusMessage += " " + descriptor.nodeCount + " recorded theorem nodes exceed the " +
        DEFAULT_MAX_NODES + "-node default service limit; oversized jobs are refused safely.";
    }
    var status = make("p", "pls-status", statusMessage);
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    var controls = make("div", "pls-controls");
    var build = button("Build Lean proof", "pls-build");
    var stop = button("Cancel", "pls-cancel");
    stop.hidden = true;
    build.disabled = descriptor.eligible === false;
    controls.appendChild(build);
    controls.appendChild(stop);
    var downloads = make("div", "pls-downloads");
    var lean = make("a", "pls-link", "Download .lean");
    var archive = make("a", "pls-link", "Verified Lean package (.zip)");
    var live = make("a", "pls-link pls-live", "Open in Lean Live");
    live.target = "_blank";
    live.rel = "noopener noreferrer";
    [lean, archive, live].forEach(function (link) {
      link.hidden = true;
      downloads.appendChild(link);
    });
    [kicker, title, theorem, stage, progress, counter, controls, status, downloads]
      .forEach(function (element) { card.appendChild(element); });
    panel.appendChild(card);
    var instance = {
      panel: panel,
      card: card,
      theorem: String(descriptor.theorem),
      edition: descriptor.edition,
      eligible: descriptor.eligible !== false,
      jobId: null,
      running: false,
      disposed: false,
      timer: null,
      controller: null,
      build: build,
      cancel: stop,
      progress: progress,
      stage: stage,
      counter: counter,
      status: status,
      lean: lean,
      archive: archive,
      live: live
    };
    build.addEventListener("click", function () { start(instance); });
    stop.addEventListener("click", function () { cancel(instance, false); });
    instances.set(panel, instance);
    return instance;
  }

  function refresh() {
    refreshQueued = false;
    if (!document.body) return;
    document.querySelectorAll(PANEL_SELECTOR).forEach(function (panel) {
      var descriptor = describeModel(panel);
      if (!descriptor) {
        var existing = instances.get(panel);
        if (existing) {
          dispose(existing);
          instances.delete(panel);
        }
        return;
      }
      mount(panel, descriptor);
    });
  }

  function scheduleRefresh() {
    if (refreshQueued) return;
    refreshQueued = true;
    global.setTimeout(refresh, 0);
  }

  function boot() {
    refresh();
    if (typeof global.MutationObserver === "function" && document.body) {
      var observer = new global.MutationObserver(scheduleRefresh);
      document.querySelectorAll(PANEL_SELECTOR).forEach(function (panel) {
        var selectionTitle = panel.querySelector("[data-graph-title]");
        if (selectionTitle) {
          observer.observe(selectionTitle, {
            subtree: true,
            childList: true,
            characterData: true
          });
        }
      });
    }
  }

  global.PeanoLeanSelector = {
    mount: mount,
    refresh: refresh,
    selection: describeModel,
    safeLiveUrl: safeLiveUrl,
    cancel: function (panel) {
      var instance = instances.get(panel);
      return instance ? cancel(instance, false) : Promise.resolve();
    }
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
}(typeof window === "undefined" ? null : window));
