/* Progressive enhancement for the definition-aware PA Proof Explorer. */
(function () {
  "use strict";

  function ready(callback) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", callback);
    else callback();
  }

  function normalized(value) {
    return String(value || "").trim().toLowerCase();
  }

  function clear(element) {
    while (element && element.firstChild) element.removeChild(element.firstChild);
  }

  function initializeDashboard(root) {
    var search = root.querySelector("[data-search]");
    var kind = root.querySelector("[data-kind]");
    var clearButton = root.querySelector("[data-clear]");
    var count = root.querySelector("[data-count]");
    var cards = Array.from(root.querySelectorAll("[data-entry]"));

    function update() {
      var query = normalized(search.value);
      var selectedKind = kind.value;
      var visible = 0;
      cards.forEach(function (card) {
        var matches = (!query || normalized(card.dataset.search).indexOf(query) !== -1) &&
          (selectedKind === "all" || card.dataset.kind === selectedKind);
        card.hidden = !matches;
        if (matches) visible += 1;
      });
      count.textContent = visible + (visible === 1 ? " entry" : " entries");
    }

    search.addEventListener("input", update);
    kind.addEventListener("change", update);
    clearButton.addEventListener("click", function () {
      search.value = "";
      kind.value = "all";
      update();
      search.focus();
    });
  }

  function initializeCopyButtons() {
    document.querySelectorAll("[data-copy-target]").forEach(function (button) {
      button.addEventListener("click", function () {
        var target = document.getElementById(button.dataset.copyTarget);
        if (!target || !navigator.clipboard) return;
        navigator.clipboard.writeText(target.textContent).then(function () {
          var former = button.textContent;
          button.textContent = "Copied";
          window.setTimeout(function () { button.textContent = former; }, 1200);
        });
      });
    });
  }

  function markProofLine(shouldFocus) {
    document.querySelectorAll(".pd-proof-line.pd-line-target").forEach(function (line) {
      line.classList.remove("pd-line-target");
    });
    var hash = window.location.hash;
    if (!/^#proof-line-[0-9]{4}$/.test(hash)) return;
    var line = document.getElementById(hash.slice(1));
    if (!line || !line.classList.contains("pd-proof-line")) return;
    line.classList.add("pd-line-target");
    line.tabIndex = -1;
    if (shouldFocus) line.focus({ preventScroll: false });
  }

  function svgElement(name, attributes) {
    var element = document.createElementNS("http:" + "//www.w3.org/2000/svg", name);
    Object.keys(attributes || {}).forEach(function (key) {
      element.setAttribute(key, attributes[key]);
    });
    return element;
  }

  function graphModel(payload) {
    var nodes = Array.isArray(payload.nodes) ? payload.nodes.slice() : [];
    var edges = Array.isArray(payload.edges) ? payload.edges.slice() : [];
    var byId = new Map();
    var byName = new Map();
    var order = new Map();
    var proofDependencies = new Map();
    var proofDependents = new Map();
    var notationUses = new Map();
    var notationUsers = new Map();
    var outgoing = new Map();
    var incoming = new Map();

    nodes.forEach(function (node, index) {
      node.id = String(node.id || "").toUpperCase();
      byId.set(node.id, node);
      byName.set(normalized(node.name), node.id);
      order.set(node.id, index);
      proofDependencies.set(node.id, []);
      proofDependents.set(node.id, []);
      notationUses.set(node.id, []);
      notationUsers.set(node.id, []);
      outgoing.set(node.id, []);
      incoming.set(node.id, []);
    });
    edges.forEach(function (edge) {
      edge.source = String(edge.source || "").toUpperCase();
      edge.target = String(edge.target || "").toUpperCase();
      if (!byId.has(edge.source) || !byId.has(edge.target)) return;
      outgoing.get(edge.source).push(edge);
      incoming.get(edge.target).push(edge);
      if (edge.kind === "proof_dependency") {
        proofDependents.get(edge.source).push(edge.target);
        proofDependencies.get(edge.target).push(edge.source);
      } else {
        notationUses.get(edge.source).push(edge.target);
        notationUsers.get(edge.target).push(edge.source);
      }
    });
    return {
      payload: payload,
      nodes: nodes,
      edges: edges,
      byId: byId,
      byName: byName,
      order: order,
      proofDependencies: proofDependencies,
      proofDependents: proofDependents,
      notationUses: notationUses,
      notationUsers: notationUsers,
      outgoing: outgoing,
      incoming: incoming,
      theoremNodes: nodes.filter(function (node) { return node.kind === "theorem"; }),
      definitionNodes: nodes.filter(function (node) { return node.kind === "definition"; })
    };
  }

  function resolveTheorem(model, value) {
    var query = String(value || "").trim();
    if (!query) return null;
    var id = query.toUpperCase();
    if (model.byId.has(id) && model.byId.get(id).kind === "theorem") return id;
    var named = model.byName.get(normalized(query));
    return named && model.byId.get(named).kind === "theorem" ? named : null;
  }

  function proofClosure(model, target, relation) {
    var seen = new Set();
    var pending = [target];
    while (pending.length) {
      var current = pending.pop();
      if (seen.has(current)) continue;
      seen.add(current);
      (relation.get(current) || []).forEach(function (next) {
        if (!seen.has(next)) pending.push(next);
      });
    }
    return seen;
  }

  function criticalPath(model, target) {
    var row = model.payload.proof_adjacency && model.payload.proof_adjacency[target];
    if (!row || !Array.isArray(row.critical_root_path)) return [target];
    return row.critical_root_path.filter(function (id) {
      return model.byId.has(id) && model.byId.get(id).kind === "theorem";
    });
  }

  function addDefinitionClosure(model, ids, sources) {
    var pending = Array.from(sources || ids);
    while (pending.length) {
      var source = pending.pop();
      (model.notationUses.get(source) || []).forEach(function (definitionId) {
        if (!ids.has(definitionId)) {
          ids.add(definitionId);
          pending.push(definitionId);
        }
      });
    }
  }

  function displayedEdges(state, selection) {
    if (state.edgeMode === "none") return [];
    if (state.edgeMode === "all") return selection.edges.slice();
    var route = new Set();
    for (var index = 1; index < selection.path.length; index += 1) {
      route.add(selection.path[index - 1] + "\u0000" + selection.path[index]);
    }
    return selection.edges.filter(function (edge) {
      return edge.source === state.selected || edge.target === state.selected ||
        (edge.kind === "proof_dependency" && route.has(edge.source + "\u0000" + edge.target));
    });
  }

  function graphSelection(state) {
    var theoremIds;
    var path = criticalPath(state.model, state.target);
    if (state.view === "prerequisites") {
      theoremIds = proofClosure(state.model, state.target, state.model.proofDependencies);
    } else if (state.view === "neighborhood") {
      theoremIds = new Set([state.target].concat(
        state.model.proofDependencies.get(state.target) || [],
        state.model.proofDependents.get(state.target) || []
      ));
    } else if (state.view === "corpus") {
      theoremIds = new Set(state.model.theoremNodes.map(function (node) { return node.id; }));
    } else {
      theoremIds = new Set(path);
      (state.model.proofDependencies.get(state.target) || []).forEach(function (id) { theoremIds.add(id); });
      (state.model.proofDependents.get(state.target) || []).forEach(function (id) { theoremIds.add(id); });
    }
    var ids = new Set(theoremIds);
    if (state.definitionMode === "visible") {
      addDefinitionClosure(state.model, ids, theoremIds);
    } else if (state.definitionMode === "selected") {
      ids.add(state.selected);
      addDefinitionClosure(state.model, ids, new Set([state.selected]));
    }
    var edges = state.model.edges.filter(function (edge) {
      return ids.has(edge.source) && ids.has(edge.target) &&
        (state.definitionMode !== "off" || edge.kind === "proof_dependency");
    });
    return { ids: ids, theoremIds: theoremIds, path: path, edges: edges };
  }

  function truncate(value, limit) {
    var text = String(value || "");
    return text.length > limit ? text.slice(0, limit - 1) + "…" : text;
  }

  function definitionDepths(model) {
    var memo = new Map();
    function depth(id, active) {
      if (memo.has(id)) return memo.get(id);
      if (active.has(id)) return 0;
      var next = new Set(active);
      next.add(id);
      var children = (model.notationUses.get(id) || []).filter(function (target) {
        return model.byId.get(target).kind === "definition";
      });
      var result = children.length ? 1 + Math.max.apply(null, children.map(function (child) {
        return depth(child, next);
      })) : 0;
      memo.set(id, result);
      return result;
    }
    model.definitionNodes.forEach(function (node) { depth(node.id, new Set()); });
    return memo;
  }

  function renderSvg(state, selection) {
    clear(state.svg);
    var defs = svgElement("defs");
    [
      ["pd-proof-arrow", "pd-proof-marker"],
      ["pd-notation-arrow", "pd-notation-marker"]
    ].forEach(function (row) {
      var marker = svgElement("marker", {
        id: row[0], viewBox: "0 0 10 10", refX: "9", refY: "5",
        markerWidth: "7", markerHeight: "7", orient: "auto-start-reverse"
      });
      marker.setAttribute("class", row[1]);
      marker.appendChild(svgElement("path", { d: "M 0 0 L 10 5 L 0 10 z" }));
      defs.appendChild(marker);
    });
    state.svg.appendChild(defs);
    var viewport = svgElement("g", { class: "pd-graph-viewport" });
    state.svg.appendChild(viewport);

    var visible = Array.from(selection.ids).map(function (id) { return state.model.byId.get(id); }).filter(Boolean);
    var theoremNodes = visible.filter(function (node) { return node.kind === "theorem"; });
    var definitionNodes = visible.filter(function (node) { return node.kind === "definition"; });
    var compact = visible.length > 160;
    var horizontalStep = compact ? 76 : 225;
    var verticalStep = compact ? 25 : 70;
    var nodeHalfWidth = compact ? 27 : 96;
    var byLayer = new Map();
    theoremNodes.forEach(function (node) {
      var layer = Number(node.layer);
      if (!byLayer.has(layer)) byLayer.set(layer, []);
      byLayer.get(layer).push(node);
    });
    var layers = Array.from(byLayer.keys()).sort(function (a, b) { return a - b; });
    var minimumLayer = layers.length ? layers[0] : 0;
    var maximumLayer = layers.length ? layers[layers.length - 1] : minimumLayer;
    var pathIds = new Set(selection.path);
    var positions = new Map();
    var maximumY = 120;
    layers.forEach(function (layer) {
      var rows = byLayer.get(layer);
      rows.sort(function (left, right) {
        return (pathIds.has(left.id) ? 0 : 1) - (pathIds.has(right.id) ? 0 : 1) ||
          state.model.order.get(left.id) - state.model.order.get(right.id);
      });
      var hasPath = rows.some(function (node) { return pathIds.has(node.id); });
      var branch = 0;
      rows.forEach(function (node) {
        var y = hasPath && pathIds.has(node.id) ? (compact ? 54 : 90) :
          (hasPath ? (compact ? 84 : 165) : (compact ? 54 : 90)) + branch++ * verticalStep;
        positions.set(node.id, { x: 60 + (layer - minimumLayer) * horizontalStep, y: y });
        maximumY = Math.max(maximumY, y);
      });
      var label = svgElement("text", {
        x: 60 + (layer - minimumLayer) * horizontalStep, y: "23",
        class: "pd-graph-layer-label", "text-anchor": "middle"
      });
      label.textContent = "proof layer " + layer;
      viewport.appendChild(label);
    });

    var depths = definitionDepths(state.model);
    var definitionsByDepth = new Map();
    definitionNodes.forEach(function (node) {
      var depth = depths.get(node.id) || 0;
      if (!definitionsByDepth.has(depth)) definitionsByDepth.set(depth, []);
      definitionsByDepth.get(depth).push(node);
    });
    var definitionBaseX = 60 + (maximumLayer - minimumLayer + 1) * horizontalStep;
    Array.from(definitionsByDepth.keys()).sort(function (a, b) { return a - b; }).forEach(function (depth) {
      var rows = definitionsByDepth.get(depth).sort(function (left, right) {
        return state.model.order.get(left.id) - state.model.order.get(right.id);
      });
      rows.forEach(function (node, index) {
        var y = (compact ? 54 : 90) + index * verticalStep;
        positions.set(node.id, { x: definitionBaseX + depth * horizontalStep, y: y });
        maximumY = Math.max(maximumY, y);
      });
      var label = svgElement("text", {
        x: definitionBaseX + depth * horizontalStep, y: "23",
        class: "pd-graph-layer-label", "text-anchor": "middle"
      });
      label.textContent = depth ? "composite definitions " + depth : "definitions";
      viewport.appendChild(label);
    });

    var pathEdges = new Set();
    for (var index = 1; index < selection.path.length; index += 1) {
      pathEdges.add(selection.path[index - 1] + "\u0000" + selection.path[index]);
    }
    selection.displayedEdges.forEach(function (edge) {
      var from = positions.get(edge.source);
      var to = positions.get(edge.target);
      if (!from || !to) return;
      var startOffset = from.x <= to.x ? nodeHalfWidth : -nodeHalfWidth;
      var endOffset = from.x <= to.x ? -nodeHalfWidth : nodeHalfWidth;
      var distance = Math.max(compact ? 12 : 42, Math.abs(to.x - from.x) * 0.42);
      var direction = from.x <= to.x ? 1 : -1;
      var key = edge.source + "\u0000" + edge.target;
      var notation = edge.kind !== "proof_dependency";
      var path = svgElement("path", {
        d: "M " + (from.x + startOffset) + " " + from.y +
          " C " + (from.x + startOffset + direction * distance) + " " + from.y +
          ", " + (to.x + endOffset - direction * distance) + " " + to.y +
          ", " + (to.x + endOffset) + " " + to.y,
        class: "pd-graph-edge" + (notation ? " pd-graph-edge-notation" : "") +
          (pathEdges.has(key) ? " pd-graph-edge-proof-path" : "") +
          (edge.kind === "proof_dependency" && edge.body_reference === false ? " pd-graph-edge-declared" : ""),
        "marker-end": notation ? "url(#pd-notation-arrow)" : "url(#pd-proof-arrow)"
      });
      var title = svgElement("title");
      title.textContent = edge.source + " → " + edge.target + " · " + edge.kind +
        (edge.kind === "uses_definition" ?
          " · " + edge.occurrence_count + " occurrences (" +
          edge.statement_occurrences + " statement, " +
          edge.local_proposition_occurrences + " local)" : "");
      path.appendChild(title);
      viewport.appendChild(path);
    });

    visible.sort(function (left, right) {
      return (left.kind === "theorem" ? 0 : 1) - (right.kind === "theorem" ? 0 : 1) ||
        state.model.order.get(left.id) - state.model.order.get(right.id);
    }).forEach(function (node) {
      var position = positions.get(node.id);
      var classes = ["pd-graph-node", "pd-graph-node-" + node.kind];
      if (compact) classes.push("pd-graph-node-compact");
      if (node.scope) classes.push("pd-scope-" + node.scope);
      if (pathIds.has(node.id)) classes.push("pd-graph-node-path");
      if (node.id === state.selected) classes.push("pd-graph-node-selected");
      var group = svgElement("g", {
        transform: "translate(" + position.x + " " + position.y + ")",
        class: classes.join(" "), tabindex: "0", role: "button",
        "data-graph-node": node.id,
        "aria-label": "Select " + node.kind + " " + node.id + ", " + node.name
      });
      var title = svgElement("title");
      title.textContent = node.id + " · " + node.name + " — click to inspect";
      group.appendChild(title);
      if (node.kind === "definition") {
        group.appendChild(svgElement("polygon", compact ? {
          points: "-27,0 -22,-10 22,-10 27,0 22,10 -22,10"
        } : { points: "-96,0 -78,-27 78,-27 96,0 78,27 -78,27" }));
      } else {
        group.appendChild(svgElement("rect", compact ?
          { x: "-27", y: "-10", width: "54", height: "20", rx: "4" } :
          { x: "-96", y: "-27", width: "192", height: "54", rx: "8" }));
      }
      var idText = svgElement("text", compact ?
        { x: "0", y: "3", class: "pd-node-id", "text-anchor": "middle" } :
        { x: "-84", y: "-5", class: "pd-node-id" });
      idText.textContent = compact ? node.id.slice(2) : node.id;
      group.appendChild(idText);
      if (!compact) {
        var nameText = svgElement("text", { x: "-84", y: "14", class: "pd-node-name" });
        nameText.textContent = truncate(node.name, 27);
        group.appendChild(nameText);
        var open = svgElement("a", {
          href: node.href, "data-graph-open": node.id,
          "aria-label": "Open " + node.kind + " " + node.name
        });
        var openText = svgElement("text", { x: "82", y: "-7", class: "pd-node-open", "text-anchor": "end" });
        openText.textContent = "↗";
        open.appendChild(openText);
        group.appendChild(open);
      }
      viewport.appendChild(group);
    });

    var outerPadding = compact ? 38 : 120;
    var maximumX = definitionNodes.length ?
      Math.max.apply(null, definitionNodes.map(function (node) { return positions.get(node.id).x; })) + outerPadding :
      60 + (maximumLayer - minimumLayer) * horizontalStep + outerPadding;
    state.positions = positions;
    state.compact = compact;
    state.bounds = { x: 5, y: -10, width: Math.max(360, maximumX + 15), height: Math.max(260, maximumY + 75) };
  }

  function appendRelationList(state, element, edges, direction) {
    clear(element);
    if (!edges.length) {
      var none = document.createElement("li");
      none.textContent = "none";
      element.appendChild(none);
      return;
    }
    edges.forEach(function (edge) {
      var otherId = direction === "out" ? edge.target : edge.source;
      var node = state.model.byId.get(otherId);
      var item = document.createElement("li");
      var link = document.createElement("a");
      link.href = node.href;
      link.textContent = otherId + " · " + node.name;
      item.appendChild(link);
      var relation = " · " + edge.kind.replace(/_/g, " ");
      if (edge.kind === "uses_definition") {
        relation += " · " + edge.occurrence_count + " occurrences (" +
          edge.statement_occurrences + " statement, " +
          edge.local_proposition_occurrences + " local)";
      }
      item.appendChild(document.createTextNode(relation));
      element.appendChild(item);
    });
  }

  function updateDetails(state) {
    var node = state.model.byId.get(state.selected);
    state.root.querySelector("[data-graph-title]").textContent = node.id + " · " + node.name;
    state.root.querySelector("[data-graph-kind]").textContent = node.kind === "definition" ?
      "Conservative definition — not a theorem or axiom" :
      (node.scope === "public" ? "Public native theorem" : "Body-checked theorem candidate");
    state.root.querySelector("[data-graph-description]").textContent = node.summary || node.signature || "";
    var metadata = state.root.querySelector("[data-graph-metadata]");
    clear(metadata);
    var rows = node.kind === "theorem" ? [
      ["Proof layer", node.layer],
      ["Proof prerequisites", (state.model.proofDependencies.get(node.id) || []).length],
      ["Definitions used", (state.model.notationUses.get(node.id) || []).length]
    ] : [
      ["Definitions used", (state.model.notationUses.get(node.id) || []).length],
      ["Theorems/definitions using it", (state.model.notationUsers.get(node.id) || []).length]
    ];
    rows.forEach(function (row) {
      var term = document.createElement("dt");
      var description = document.createElement("dd");
      term.textContent = row[0];
      description.textContent = row[1];
      metadata.appendChild(term);
      metadata.appendChild(description);
    });
    var open = state.root.querySelector(".pd-graph-details [data-graph-open]");
    open.setAttribute("href", node.href);
    open.textContent = node.kind === "definition" ? "Open definition →" : "Open theorem →";
    appendRelationList(state, state.root.querySelector("[data-graph-outgoing]"), state.model.outgoing.get(node.id) || [], "out");
    appendRelationList(state, state.root.querySelector("[data-graph-incoming]"), state.model.incoming.get(node.id) || [], "in");
  }

  function setViewBox(state, box) {
    state.currentViewBox = box;
    state.svg.setAttribute("viewBox", [box.x, box.y, box.width, box.height].join(" "));
  }

  function fit(state) {
    if (!state.bounds) return;
    setViewBox(state, {
      x: state.bounds.x - 25, y: state.bounds.y - 25,
      width: state.bounds.width + 50, height: state.bounds.height + 50
    });
  }

  function zoom(state, factor) {
    if (!state.currentViewBox) return;
    var box = state.currentViewBox;
    var width = Math.max(280, Math.min(state.bounds.width * 1.8, box.width * factor));
    var scale = width / box.width;
    var height = box.height * scale;
    setViewBox(state, {
      x: box.x + (box.width - width) / 2,
      y: box.y + (box.height - height) / 2,
      width: width, height: height
    });
  }

  function synchronizeAddress(state) {
    if (!window.history || !window.history.replaceState) return;
    try {
      var url = new URL(window.location.href);
      url.searchParams.set("target", state.target);
      url.searchParams.set("focus", state.selected);
      url.searchParams.set("view", state.view);
      url.searchParams.set("definitions", state.definitionMode);
      url.searchParams.set("edges", state.edgeMode);
      window.history.replaceState(null, "", url.toString());
    } catch (_error) {
      /* A read-only address does not disable the graph. */
    }
  }

  function renderGraph(state, shouldFit) {
    var selection = graphSelection(state);
    if (!selection.ids.has(state.selected)) state.selected = state.target;
    selection.displayedEdges = displayedEdges(state, selection);
    renderSvg(state, selection);
    updateDetails(state);
    var theoremCount = Array.from(selection.ids).filter(function (id) {
      return state.model.byId.get(id).kind === "theorem";
    }).length;
    var definitionCount = selection.ids.size - theoremCount;
    state.summary.textContent = theoremCount + " theorem nodes · " + definitionCount +
      " definition nodes · " + selection.displayedEdges.length + " of " + selection.edges.length +
      " direct typed arrows shown" + (state.compact ? " · compact clickable marks." :
        ". Proof paths ignore notation edges.");
    synchronizeAddress(state);
    window.requestAnimationFrame(function () { if (shouldFit) fit(state); });
  }

  function installViewport(state) {
    state.root.querySelector("[data-graph-zoom='in']").addEventListener("click", function () { zoom(state, 0.78); });
    state.root.querySelector("[data-graph-zoom='out']").addEventListener("click", function () { zoom(state, 1.28); });
    state.root.querySelector("[data-graph-fit]").addEventListener("click", function () { fit(state); });
    var drag = null;
    state.svg.addEventListener("pointerdown", function (event) {
      if (event.button !== 0 || event.target.closest("[data-graph-node],a")) return;
      if (!state.currentViewBox) return;
      drag = { pointer: event.pointerId, x: event.clientX, y: event.clientY, box: Object.assign({}, state.currentViewBox) };
      state.svg.setPointerCapture(event.pointerId);
      state.svg.parentElement.classList.add("pd-panning");
    });
    state.svg.addEventListener("pointermove", function (event) {
      if (!drag || drag.pointer !== event.pointerId) return;
      var scaleX = drag.box.width / Math.max(1, state.svg.clientWidth);
      var scaleY = drag.box.height / Math.max(1, state.svg.clientHeight);
      setViewBox(state, {
        x: drag.box.x - (event.clientX - drag.x) * scaleX,
        y: drag.box.y - (event.clientY - drag.y) * scaleY,
        width: drag.box.width, height: drag.box.height
      });
    });
    function stop(event) {
      if (!drag || drag.pointer !== event.pointerId) return;
      drag = null;
      state.svg.parentElement.classList.remove("pd-panning");
    }
    state.svg.addEventListener("pointerup", stop);
    state.svg.addEventListener("pointercancel", stop);
    state.svg.addEventListener("wheel", function (event) {
      if (!(event.ctrlKey || event.metaKey)) return;
      event.preventDefault();
      zoom(state, event.deltaY < 0 ? 0.86 : 1.16);
    }, { passive: false });
    state.svg.addEventListener("keydown", function (event) {
      if (event.target.closest && event.target.closest("[data-graph-open]")) return;
      var node = event.target.closest && event.target.closest("[data-graph-node]");
      if (node && (event.key === "Enter" || event.key === " ")) {
        event.preventDefault();
        node.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      }
    });
  }

  function initializeGraph(root) {
    var payload = window.PA_DEFINED_GRAPH;
    var summary = root.querySelector("[data-graph-summary]");
    if (!payload || !Array.isArray(payload.nodes)) {
      summary.textContent = "Mixed graph data is unavailable.";
      return;
    }
    var model = graphModel(payload);
    var parameters;
    try { parameters = new URL(window.location.href).searchParams; }
    catch (_error) { parameters = new URLSearchParams(); }
    var target = resolveTheorem(model, parameters.get("target")) ||
      (model.byId.has("PA00FW") ? "PA00FW" : model.theoremNodes[model.theoremNodes.length - 1].id);
    var focus = String(parameters.get("focus") || "").toUpperCase();
    var allowedViews = new Set(["critical", "prerequisites", "neighborhood", "corpus"]);
    var requestedDefinitions = parameters.get("definitions");
    var definitionMode = requestedDefinitions === "1" ? "visible" :
      requestedDefinitions === "0" ? "off" : requestedDefinitions;
    if (!["selected", "visible", "off"].includes(definitionMode)) definitionMode = "selected";
    var requestedEdges = parameters.get("edges");
    var edgeMode = ["focus", "none", "all"].includes(requestedEdges) ? requestedEdges : "focus";
    var state = {
      root: root, model: model, target: target,
      selected: model.byId.has(focus) ? focus : target,
      view: allowedViews.has(parameters.get("view")) ? parameters.get("view") : "neighborhood",
      definitionMode: definitionMode,
      edgeMode: edgeMode,
      summary: summary,
      svg: root.querySelector("[data-graph-svg]"),
      targetInput: root.querySelector("[data-graph-target]"),
      viewInput: root.querySelector("[data-graph-view]"),
      definitionsInput: root.querySelector("[data-graph-definitions]"),
      edgeInput: root.querySelector("[data-graph-edges]")
    };
    state.targetInput.value = state.target;
    state.viewInput.value = state.view;
    state.definitionsInput.value = state.definitionMode;
    state.edgeInput.value = state.edgeMode;
    var datalist = root.querySelector("#pd-graph-theorems");
    model.theoremNodes.forEach(function (node) {
      var option = document.createElement("option");
      option.value = node.id;
      option.label = node.name + " · proof layer " + node.layer;
      datalist.appendChild(option);
    });
    root.querySelector("[data-graph-form]").addEventListener("submit", function (event) {
      event.preventDefault();
      var next = resolveTheorem(model, state.targetInput.value);
      state.targetInput.setCustomValidity(next ? "" : "Enter an exact theorem tag or name.");
      if (!next) return state.targetInput.reportValidity();
      state.target = next;
      state.selected = next;
      state.view = state.viewInput.value;
      state.definitionMode = state.definitionsInput.value;
      state.edgeMode = state.edgeInput.value;
      renderGraph(state, true);
    });
    state.viewInput.addEventListener("change", function () {
      state.view = state.viewInput.value;
      renderGraph(state, true);
    });
    state.definitionsInput.addEventListener("change", function () {
      state.definitionMode = state.definitionsInput.value;
      renderGraph(state, true);
    });
    state.edgeInput.addEventListener("change", function () {
      state.edgeMode = state.edgeInput.value;
      renderGraph(state, true);
    });
    root.addEventListener("click", function (event) {
      if (event.target.closest("[data-graph-open]")) return;
      var group = event.target.closest("[data-graph-node]");
      if (!group) return;
      event.preventDefault();
      var id = group.dataset.graphNode;
      var node = model.byId.get(id);
      if (node.kind === "theorem") {
        state.target = id;
        state.targetInput.value = id;
      }
      state.selected = id;
      renderGraph(state, false);
      root.querySelector("[data-graph-title]").focus({ preventScroll: true });
    });
    installViewport(state);
    renderGraph(state, true);
  }

  ready(function () {
    if (!document.body || !document.body.classList.contains("pa-defined-proof-site")) return;
    document.querySelectorAll("[data-defined-dashboard]").forEach(initializeDashboard);
    document.querySelectorAll("[data-defined-graph]").forEach(initializeGraph);
    initializeCopyButtons();
    markProofLine(false);
    window.addEventListener("hashchange", function () { markProofLine(true); });
  });
}());
