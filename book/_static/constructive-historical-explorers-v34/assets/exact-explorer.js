/* Progressive enhancement for the generated native-PA proof explorer. */
(function () {
  "use strict";

  function whenReady(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
    } else {
      callback();
    }
  }

  function normalized(value) {
    return String(value || "").trim().toLocaleLowerCase();
  }

  function setCount(output, visible, total) {
    if (!output) return;
    var phrase = visible === total
      ? total + (total === 1 ? " theorem" : " theorems")
      : visible + " of " + total + " theorems";
    output.value = phrase;
    output.textContent = phrase;
  }

  function initializeDashboard(root) {
    var search = root.querySelector("[data-proof-search]");
    var status = root.querySelector("[data-proof-status]");
    var layer = root.querySelector("[data-proof-layer]");
    var clear = root.querySelector("[data-proof-clear]");
    var count = root.querySelector("[data-proof-count]");
    var cards = Array.from(root.querySelectorAll(".pa-proof-result[data-name][data-tag]"));
    if (!search || !status || !layer || !cards.length) return;

    var parameters;
    try {
      parameters = new URL(window.location.href).searchParams;
    } catch (_error) {
      parameters = new URLSearchParams();
    }

    function selectKnown(control, value) {
      if (!value) return;
      var exists = Array.from(control.options).some(function (option) {
        return option.value === value;
      });
      if (exists) control.value = value;
    }

    search.value = parameters.get("q") || "";
    selectKnown(status, parameters.get("status"));
    selectKnown(layer, parameters.get("layer"));

    function synchronizeAddress() {
      if (!window.history || !window.history.replaceState) return;
      try {
        var target = new URL(window.location.href);
        var query = search.value.trim();
        if (query) target.searchParams.set("q", query);
        else target.searchParams.delete("q");
        if (status.value && status.value !== "all") {
          target.searchParams.set("status", status.value);
        } else {
          target.searchParams.delete("status");
        }
        if (layer.value && layer.value !== "all") {
          target.searchParams.set("layer", layer.value);
        } else {
          target.searchParams.delete("layer");
        }
        window.history.replaceState(null, "", target.toString());
      } catch (_error) {
        /* Filtering still works in browsers with a read-only address. */
      }
    }

    function applyFilters(updateAddress) {
      var query = normalized(search.value);
      var statusValue = status.value;
      var layerValue = layer.value;
      var visible = 0;
      cards.forEach(function (card) {
        var haystack = normalized(
          card.dataset.search || [
            card.dataset.tag,
            card.dataset.name,
            card.textContent
          ].join(" ")
        );
        var matches = (!query || haystack.indexOf(query) !== -1) &&
          (statusValue === "all" || card.dataset.status === statusValue) &&
          (layerValue === "all" || card.dataset.layer === layerValue);
        card.hidden = !matches;
        if (matches) visible += 1;
      });
      setCount(count, visible, cards.length);
      var empty = root.querySelector(".pa-empty-results");
      if (empty) empty.hidden = visible !== 0;
      if (updateAddress) synchronizeAddress();
    }

    search.addEventListener("input", function () { applyFilters(true); });
    status.addEventListener("change", function () { applyFilters(true); });
    layer.addEventListener("change", function () { applyFilters(true); });
    if (clear) {
      clear.addEventListener("click", function () {
        search.value = "";
        status.value = "all";
        layer.value = "all";
        applyFilters(true);
        search.focus();
      });
    }

    root.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && document.activeElement === search && search.value) {
        search.value = "";
        applyFilters(true);
      }
    });
    document.addEventListener("keydown", function (event) {
      var tag = event.target && event.target.tagName;
      if (event.key === "/" && !/^(INPUT|SELECT|TEXTAREA)$/.test(tag || "")) {
        event.preventDefault();
        search.focus();
      }
    });

    applyFilters(false);
  }

  function copyFallback(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    area.style.pointerEvents = "none";
    document.body.appendChild(area);
    area.select();
    var copied = false;
    try { copied = document.execCommand("copy"); } catch (_error) { copied = false; }
    area.remove();
    return copied;
  }

  function copiedFeedback(button, successful) {
    var original = button.dataset.copyLabel || button.textContent;
    button.dataset.copyLabel = original;
    button.textContent = successful ? "Copied" : "Copy failed";
    window.setTimeout(function () { button.textContent = original; }, 1400);
  }

  function initializeCopyControls() {
    document.addEventListener("click", function (event) {
      var button = event.target.closest("[data-copy-target]");
      if (!button) return;
      var targetId = button.dataset.copyTarget;
      var target = targetId ? document.getElementById(targetId) : null;
      if (!target) {
        copiedFeedback(button, false);
        return;
      }
      var text = target.textContent || "";
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(
          function () { copiedFeedback(button, true); },
          function () { copiedFeedback(button, copyFallback(text)); }
        );
      } else {
        copiedFeedback(button, copyFallback(text));
      }
    });
  }

  function proofLineFromHash() {
    var hash = window.location.hash;
    if (!/^#proof-line-[0-9]{4}$/.test(hash)) return null;
    var line = document.getElementById(hash.slice(1));
    return line && line.classList.contains("pa-proof-line") ? line : null;
  }

  function markProofLine(shouldFocus) {
    document.querySelectorAll(".pa-proof-line.pa-line-target").forEach(function (line) {
      line.classList.remove("pa-line-target");
    });
    var line = proofLineFromHash();
    if (!line) return;
    line.classList.add("pa-line-target");
    if (!line.hasAttribute("tabindex")) line.setAttribute("tabindex", "-1");
    if (shouldFocus) {
      try { line.focus({ preventScroll: true }); } catch (_error) { line.focus(); }
      var reduced = window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      line.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "center" });
    }
  }

  function initializeGraphNavigation() {
    var page = document.body && document.body.dataset.page;
    if (!page || page === "graph") return;
    var header = document.querySelector(".pa-proof-header");
    if (!header || header.querySelector("[data-graph-navigation]")) return;
    var tag = document.querySelector(".pa-theorem-heading .pa-tag");
    var prefix = page === "theorem" ? "../" : "";
    var href = prefix + "graph.html";
    if (tag) href += "?target=" + encodeURIComponent(tag.textContent.trim());
    var link = document.createElement("a");
    link.href = href;
    link.dataset.graphNavigation = "";
    link.textContent = page === "theorem" ? "Dependency paths" : "Dependency graph";
    var nav = header.querySelector("nav");
    if (!nav) {
      nav = document.createElement("nav");
      nav.setAttribute("aria-label", "Proof Explorer");
      header.appendChild(nav);
    }
    nav.appendChild(link);

    if (page === "theorem") {
      var neighborhood = Array.from(document.querySelectorAll(".pa-proof-panel section")).find(function (section) {
        var heading = section.querySelector("h2");
        return heading && heading.textContent.trim() === "Proof neighborhood";
      });
      if (neighborhood) {
        var paragraph = document.createElement("p");
        paragraph.className = "pa-graph-inline-link";
        var localLink = link.cloneNode(true);
        localLink.textContent = "Trace this theorem through the interactive dependency graph →";
        paragraph.appendChild(localLink);
        neighborhood.appendChild(paragraph);
      }
    }
  }

  function graphData(root) {
    if (window.PA_PROOF_GRAPH && Array.isArray(window.PA_PROOF_GRAPH.nodes)) {
      return Promise.resolve(window.PA_PROOF_GRAPH);
    }
    var source = root.dataset.graphJson || "api/graph.json";
    if (!window.fetch) return Promise.reject(new Error("This browser cannot load the graph payload."));
    return window.fetch(source).then(function (response) {
      if (!response.ok) throw new Error("Graph payload returned HTTP " + response.status + ".");
      return response.json();
    });
  }

  function graphModel(payload) {
    var nodes = Array.isArray(payload.nodes) ? payload.nodes.slice() : [];
    var edges = Array.isArray(payload.edges) ? payload.edges.slice() : [];
    var byTag = new Map();
    var byName = new Map();
    var order = new Map();
    var dependencies = new Map();
    var dependents = new Map();
    var edgeByPair = new Map();

    nodes.forEach(function (node, index) {
      node.tag = String(node.tag || "").toUpperCase();
      byTag.set(node.tag, node);
      byName.set(normalized(node.name), node.tag);
      order.set(node.tag, index);
      dependencies.set(node.tag, []);
      dependents.set(node.tag, []);
    });
    edges.forEach(function (edge) {
      var dependency = String(edge.dependency || "").toUpperCase();
      var dependent = String(edge.dependent || "").toUpperCase();
      if (!byTag.has(dependency) || !byTag.has(dependent)) return;
      dependencies.get(dependent).push(dependency);
      dependents.get(dependency).push(dependent);
      edgeByPair.set(dependency + "\u0000" + dependent, edge);
    });

    function knownTags(values) {
      return Array.from(new Set(Array.isArray(values) ? values : [])).map(function (tag) {
        return String(tag).toUpperCase();
      }).filter(function (tag) { return byTag.has(tag); });
    }

    var foundations = knownTags(payload.foundations);
    if (!foundations.length) {
      foundations = nodes.filter(function (node) {
        return dependencies.get(node.tag).length === 0;
      }).map(function (node) { return node.tag; });
    }
    var terminals = knownTags(payload.terminals);
    if (!terminals.length) {
      terminals = nodes.filter(function (node) {
        return dependents.get(node.tag).length === 0;
      }).map(function (node) { return node.tag; });
    }

    return {
      payload: payload,
      nodes: nodes,
      edges: edges,
      byTag: byTag,
      byName: byName,
      order: order,
      dependencies: dependencies,
      dependents: dependents,
      edgeByPair: edgeByPair,
      foundations: foundations,
      terminals: terminals
    };
  }

  function graphResolve(model, value) {
    var query = String(value || "").trim();
    if (!query) return null;
    var tag = query.toUpperCase();
    if (model.byTag.has(tag)) return tag;
    if (model.byName.has(normalized(query))) return model.byName.get(normalized(query));
    var matches = model.nodes.filter(function (node) {
      return normalized(node.name).indexOf(normalized(query)) !== -1;
    });
    return matches.length === 1 ? matches[0].tag : null;
  }

  function graphClosure(model, start, direction) {
    var relation = direction === "dependencies" ? model.dependencies : model.dependents;
    var seen = new Set();
    var pending = [start];
    while (pending.length) {
      var current = pending.pop();
      if (seen.has(current)) continue;
      seen.add(current);
      (relation.get(current) || []).forEach(function (tag) {
        if (!seen.has(tag)) pending.push(tag);
      });
    }
    return seen;
  }

  function graphPayloadPath(model, target, field) {
    var adjacency = model.payload.adjacency && model.payload.adjacency[target];
    if (!adjacency || !Array.isArray(adjacency[field])) return null;
    var path = adjacency[field].map(function (tag) { return String(tag).toUpperCase(); });
    if (!path.length || path[path.length - 1] !== target || path.some(function (tag) {
      return !model.byTag.has(tag);
    })) return null;
    return path;
  }

  function graphShortestPath(model, source, target) {
    var starts = source ? [source] : model.foundations.slice();
    var queue = starts.slice();
    var previous = new Map();
    starts.forEach(function (tag) { previous.set(tag, null); });
    for (var cursor = 0; cursor < queue.length; cursor += 1) {
      var current = queue[cursor];
      if (current === target) break;
      (model.dependents.get(current) || []).forEach(function (next) {
        if (!previous.has(next)) {
          previous.set(next, current);
          queue.push(next);
        }
      });
    }
    if (!previous.has(target)) return [];
    var result = [];
    var step = target;
    while (step !== null) {
      result.push(step);
      step = previous.get(step);
    }
    result.reverse();
    return result;
  }

  function graphCriticalPath(model, source, target) {
    var starts = source ? [source] : model.foundations.slice();
    var best = new Map();
    starts.forEach(function (tag) { best.set(tag, [tag]); });
    var ordered = model.nodes.slice().sort(function (left, right) {
      return Number(left.layer) - Number(right.layer) ||
        model.order.get(left.tag) - model.order.get(right.tag);
    });
    ordered.forEach(function (node) {
      var path = best.get(node.tag);
      if (!path) return;
      (model.dependents.get(node.tag) || []).forEach(function (next) {
        var candidate = path.concat(next);
        var existing = best.get(next);
        if (!existing || candidate.length > existing.length) best.set(next, candidate);
      });
    });
    return best.get(target) || [];
  }

  function graphChosenPath(model, source, target, view) {
    if (!source) {
      var field = view === "shortest" ? "shortest_root_path" : "critical_root_path";
      var supplied = graphPayloadPath(model, target, field);
      if (supplied) return supplied;
    }
    return view === "shortest"
      ? graphShortestPath(model, source, target)
      : graphCriticalPath(model, source, target);
  }

  function graphView(model, source, target, view) {
    var routeView = view === "shortest" ? "shortest" : "critical";
    var path = graphChosenPath(model, source, target, routeView);
    var tags;
    if (view === "critical" || view === "shortest") {
      tags = new Set(path);
      (model.dependencies.get(target) || []).forEach(function (tag) { tags.add(tag); });
      (model.dependents.get(target) || []).forEach(function (tag) { tags.add(tag); });
    } else if (view === "corridor") {
      var corridorSource = source || (graphChosenPath(model, null, target, "critical")[0]);
      var forward = graphClosure(model, corridorSource, "dependents");
      var backward = graphClosure(model, target, "dependencies");
      tags = new Set(Array.from(forward).filter(function (tag) { return backward.has(tag); }));
      path = graphCriticalPath(model, corridorSource, target);
    } else if (view === "prerequisites") {
      tags = graphClosure(model, target, "dependencies");
    } else if (view === "dependents") {
      tags = graphClosure(model, target, "dependents");
    } else if (view === "corpus") {
      tags = new Set(model.nodes.map(function (node) { return node.tag; }));
    } else {
      tags = new Set([target].concat(
        model.dependencies.get(target) || [],
        model.dependents.get(target) || []
      ));
    }
    if (!path.length) path = graphChosenPath(model, null, target, "critical");
    var edges = model.edges.filter(function (edge) {
      return tags.has(edge.dependency) && tags.has(edge.dependent);
    });
    return { tags: tags, edges: edges, path: path };
  }

  function graphDisplayedEdges(state, selection) {
    if (state.edgeMode === "none") return [];
    if (state.edgeMode === "all") return selection.edges.slice();
    var route = new Set();
    for (var index = 1; index < selection.path.length; index += 1) {
      route.add(selection.path[index - 1] + "\u0000" + selection.path[index]);
    }
    return selection.edges.filter(function (edge) {
      return edge.dependency === state.target || edge.dependent === state.target ||
        route.has(edge.dependency + "\u0000" + edge.dependent);
    });
  }

  function graphSvgElement(name, attributes) {
    var element = document.createElementNS("http:" + "//www.w3.org/2000/svg", name);
    Object.keys(attributes || {}).forEach(function (key) {
      element.setAttribute(key, attributes[key]);
    });
    return element;
  }

  function graphClear(element) {
    while (element.firstChild) element.removeChild(element.firstChild);
  }

  function graphTruncate(value, limit) {
    var text = String(value || "");
    return text.length > limit ? text.slice(0, limit - 1) + "…" : text;
  }

  function graphRenderSvg(state, selection) {
    var svg = state.svg;
    var model = state.model;
    graphClear(svg);

    var defs = graphSvgElement("defs");
    var marker = graphSvgElement("marker", {
      id: "pa-graph-arrow", viewBox: "0 0 10 10", refX: "9", refY: "5",
      markerWidth: "7", markerHeight: "7", orient: "auto-start-reverse"
    });
    marker.appendChild(graphSvgElement("path", { d: "M 0 0 L 10 5 L 0 10 z" }));
    defs.appendChild(marker);
    svg.appendChild(defs);

    var viewport = graphSvgElement("g", { class: "pa-graph-viewport" });
    svg.appendChild(viewport);
    state.preludeX = undefined;
    var pathTags = new Set(selection.path);
    var pathEdges = new Set();
    for (var p = 1; p < selection.path.length; p += 1) {
      pathEdges.add(selection.path[p - 1] + "\u0000" + selection.path[p]);
    }

    var visible = Array.from(selection.tags).map(function (tag) {
      return model.byTag.get(tag);
    }).filter(Boolean).sort(function (left, right) {
      return Number(left.layer) - Number(right.layer) ||
        model.order.get(left.tag) - model.order.get(right.tag);
    });
    var compact = visible.length > 160;
    var horizontalStep = compact ? 76 : 230;
    var verticalStep = compact ? 25 : 70;
    var nodeHalfWidth = compact ? 27 : 96;
    var byLayer = new Map();
    visible.forEach(function (node) {
      var layer = Number(node.layer);
      if (!byLayer.has(layer)) byLayer.set(layer, []);
      byLayer.get(layer).push(node);
    });
    var layers = Array.from(byLayer.keys()).sort(function (a, b) { return a - b; });
    var minimumLayer = layers.length ? layers[0] : 0;
    var positions = new Map();
    var maximumY = 100;
    layers.forEach(function (layer) {
      var rows = byLayer.get(layer);
      rows.sort(function (left, right) {
        var leftPath = pathTags.has(left.tag) ? 0 : 1;
        var rightPath = pathTags.has(right.tag) ? 0 : 1;
        return leftPath - rightPath || model.order.get(left.tag) - model.order.get(right.tag);
      });
      var hasPath = rows.some(function (node) { return pathTags.has(node.tag); });
      var branch = 0;
      rows.forEach(function (node) {
        var y;
        if (hasPath && pathTags.has(node.tag)) y = compact ? 54 : 92;
        else {
          y = (hasPath ? (compact ? 84 : 170) : (compact ? 54 : 92)) + branch * verticalStep;
          branch += 1;
        }
        var x = 60 + (layer - minimumLayer) * horizontalStep;
        positions.set(node.tag, { x: x, y: y });
        maximumY = Math.max(maximumY, y);
      });
      var label = graphSvgElement("text", {
        x: 60 + (layer - minimumLayer) * horizontalStep,
        y: "24", class: "pa-graph-layer-label", "text-anchor": "middle"
      });
      label.textContent = "layer " + layer;
      viewport.appendChild(label);
    });

    selection.displayedEdges.forEach(function (edge) {
      var from = positions.get(edge.dependency);
      var to = positions.get(edge.dependent);
      if (!from || !to) return;
      var key = edge.dependency + "\u0000" + edge.dependent;
      var distance = Math.max(compact ? 12 : 42, (to.x - from.x) * 0.44);
      var path = graphSvgElement("path", {
        d: "M " + (from.x + nodeHalfWidth) + " " + from.y +
          " C " + (from.x + nodeHalfWidth + distance) + " " + from.y +
          ", " + (to.x - nodeHalfWidth - distance) + " " + to.y +
          ", " + (to.x - nodeHalfWidth) + " " + to.y,
        class: "pa-graph-edge" +
          (pathEdges.has(key) ? " pa-graph-edge-path" : "") +
          (edge.body_reference === false ? " pa-graph-edge-declared" : ""),
        "marker-end": "url(#pa-graph-arrow)"
      });
      var edgeTitle = graphSvgElement("title");
      edgeTitle.textContent = edge.dependency + " → " + edge.dependent +
        (edge.body_reference === false ? " (declared dependency; no explicit tactic-body citation)" : "");
      path.appendChild(edgeTitle);
      viewport.appendChild(path);
    });

    if (selection.path.length && model.foundations.indexOf(selection.path[0]) !== -1) {
      var rootPosition = positions.get(selection.path[0]);
      if (rootPosition) {
        var preludeX = rootPosition.x - (compact ? 90 : 230);
        var preludeEdge = graphSvgElement("path", {
          d: "M " + (preludeX + (compact ? 27 : 96)) + " " + rootPosition.y + " L " +
            (rootPosition.x - nodeHalfWidth) + " " + rootPosition.y,
          class: "pa-graph-prelude-edge"
        });
        viewport.appendChild(preludeEdge);
        var preludeLink = graphSvgElement("a", { href: "foundations.html", class: "pa-graph-prelude" });
        var preludeGroup = graphSvgElement("g", { transform: "translate(" + preludeX + " " + rootPosition.y + ")" });
        preludeGroup.appendChild(graphSvgElement("rect", compact ?
          { x: "-27", y: "-10", width: "54", height: "20", rx: "4" } :
          { x: "-96", y: "-27", width: "192", height: "54", rx: "8" }));
        var preludeTitle = graphSvgElement("title");
        preludeTitle.textContent = "PA foundations prelude (not a theorem node)";
        preludeGroup.appendChild(preludeTitle);
        var preludeText = graphSvgElement("text", { x: "0", y: compact ? "3" : "-3", "text-anchor": "middle" });
        preludeText.textContent = compact ? "PA" : "PA foundations";
        preludeGroup.appendChild(preludeText);
        if (!compact) {
          var preludeSubtext = graphSvgElement("text", { x: "0", y: "14", "text-anchor": "middle", class: "pa-graph-node-name" });
          preludeSubtext.textContent = "prelude · not a theorem";
          preludeGroup.appendChild(preludeSubtext);
        }
        preludeLink.appendChild(preludeGroup);
        viewport.appendChild(preludeLink);
        state.preludeX = preludeX;
      }
    }

    visible.forEach(function (node) {
      var position = positions.get(node.tag);
      var classes = ["pa-graph-node", "pa-graph-node-" + node.scope, "pa-graph-node-status-" + node.status];
      if (compact) classes.push("pa-graph-node-compact");
      if (pathTags.has(node.tag)) classes.push("pa-graph-node-path");
      if (node.tag === state.target) classes.push("pa-graph-node-selected");
      var group = graphSvgElement("g", {
        transform: "translate(" + position.x + " " + position.y + ")",
        class: classes.join(" "), tabindex: "0", role: "button",
        "data-graph-node": node.tag,
        "aria-label": "Select " + node.tag + ", " + node.name + ", layer " + node.layer
      });
      var title = graphSvgElement("title");
      title.textContent = node.tag + " · " + node.name + (compact ? " — click to inspect" : " — click to select; open arrow for formal proof");
      group.appendChild(title);
      group.appendChild(graphSvgElement("rect", compact ?
        { x: "-27", y: "-10", width: "54", height: "20", rx: "4" } :
        { x: "-96", y: "-27", width: "192", height: "54", rx: "8" }));
      var tagText = graphSvgElement("text", compact ?
        { x: "0", y: "3", class: "pa-graph-node-tag", "text-anchor": "middle" } :
        { x: "-84", y: "-5", class: "pa-graph-node-tag" });
      tagText.textContent = compact ? node.tag.slice(2) : node.tag;
      group.appendChild(tagText);
      if (!compact) {
        var nameText = graphSvgElement("text", { x: "-84", y: "14", class: "pa-graph-node-name" });
        nameText.textContent = graphTruncate(node.name, 27);
        group.appendChild(nameText);
        var open = graphSvgElement("a", {
          href: "tag/" + node.tag + ".html", "data-graph-open": node.tag,
          "aria-label": "Open the formal proof of " + node.name
        });
        var openText = graphSvgElement("text", { x: "82", y: "-7", class: "pa-graph-node-open", "text-anchor": "end" });
        openText.textContent = "↗";
        open.appendChild(openText);
        group.appendChild(open);
      }
      viewport.appendChild(group);
    });

    var outerPadding = compact ? 38 : 120;
    var minimumX = selection.path.length && state.preludeX !== undefined ? state.preludeX - outerPadding : 10;
    var maximumX = layers.length ? 60 + (layers[layers.length - 1] - minimumLayer) * horizontalStep + outerPadding : 260;
    state.positions = positions;
    state.compact = compact;
    state.bounds = {
      x: minimumX,
      y: -12,
      width: Math.max(360, maximumX - minimumX),
      height: Math.max(250, maximumY + 75)
    };
  }

  function graphSetViewBox(state, box) {
    state.currentViewBox = box;
    state.svg.setAttribute("viewBox", [box.x, box.y, box.width, box.height].join(" "));
  }

  function graphFit(state) {
    var bounds = state.bounds;
    if (!bounds) return;
    var padding = 30;
    graphSetViewBox(state, {
      x: bounds.x - padding,
      y: bounds.y - padding,
      width: bounds.width + padding * 2,
      height: bounds.height + padding * 2
    });
  }

  function graphCenterTarget(state) {
    var position = state.positions && state.positions.get(state.target);
    if (!position) return graphFit(state);
    var ratio = Math.max(1.25, state.svg.clientWidth / Math.max(1, state.svg.clientHeight));
    var width = Math.min(1250, Math.max(720, state.bounds.width));
    if (state.bounds.width <= 1250 && state.bounds.height <= width / ratio) return graphFit(state);
    var height = width / ratio;
    graphSetViewBox(state, {
      x: position.x - width * 0.73,
      y: Math.max(state.bounds.y - 20, position.y - height * 0.5),
      width: width,
      height: height
    });
  }

  function graphZoom(state, factor) {
    var box = state.currentViewBox;
    if (!box) return;
    var nextWidth = Math.max(260, Math.min(state.bounds.width * 1.7, box.width * factor));
    var scale = nextWidth / box.width;
    var nextHeight = box.height * scale;
    graphSetViewBox(state, {
      x: box.x + (box.width - nextWidth) / 2,
      y: box.y + (box.height - nextHeight) / 2,
      width: nextWidth,
      height: nextHeight
    });
  }

  function graphRelationList(state, element, tags) {
    graphClear(element);
    if (!tags.length) {
      var none = document.createElement("li");
      none.textContent = "none";
      element.appendChild(none);
      return;
    }
    tags.forEach(function (tag) {
      var node = state.model.byTag.get(tag);
      var item = document.createElement("li");
      var select = document.createElement("button");
      select.type = "button";
      select.dataset.graphSelect = tag;
      select.textContent = tag + " · " + node.name;
      item.appendChild(select);
      item.appendChild(document.createTextNode(" "));
      var proof = document.createElement("a");
      proof.href = "tag/" + tag + ".html";
      proof.setAttribute("aria-label", "Open formal proof of " + node.name);
      proof.textContent = "↗";
      item.appendChild(proof);
      element.appendChild(item);
    });
  }

  function graphUpdateDetails(state, selection) {
    var node = state.model.byTag.get(state.target);
    state.root.querySelector("[data-graph-title]").textContent = node.tag + " · " + node.name;
    var status = state.root.querySelector("[data-graph-status]");
    status.className = node.scope === "public" ? "pa-status-public" : "pa-status-candidate";
    status.textContent = node.scope === "public" ? "public native theorem" :
      (node.status === "pending_layered_closure" ? "pending layered closure" : "body-checked candidate; not publicly admitted");
    state.root.querySelector("[data-graph-description]").textContent = node.summary || "";
    var metadata = state.root.querySelector("[data-graph-metadata]");
    graphClear(metadata);
    var rows = [
      ["Layer", node.layer],
      ["Direct prerequisites", (state.model.dependencies.get(node.tag) || []).length],
      ["Direct dependents", (state.model.dependents.get(node.tag) || []).length]
    ];
    var adjacency = state.model.payload.adjacency && state.model.payload.adjacency[node.tag];
    if (adjacency && adjacency.root_path_count !== undefined) {
      rows.push(["Root-to-theorem chains", Number(adjacency.root_path_count).toLocaleString()]);
    }
    rows.forEach(function (row) {
      var term = document.createElement("dt");
      var description = document.createElement("dd");
      term.textContent = row[0];
      description.textContent = row[1];
      metadata.appendChild(term);
      metadata.appendChild(description);
    });
    state.root.querySelector("[data-graph-proof]").href = "tag/" + node.tag + ".html";
    graphRelationList(state, state.root.querySelector("[data-graph-dependencies]"), state.model.dependencies.get(node.tag) || []);
    graphRelationList(state, state.root.querySelector("[data-graph-dependents]"), state.model.dependents.get(node.tag) || []);

    var list = state.root.querySelector("[data-graph-path-list]");
    graphClear(list);
    if (selection.path.length && state.model.foundations.indexOf(selection.path[0]) !== -1) {
      var prelude = document.createElement("li");
      var foundations = document.createElement("a");
      foundations.href = "foundations.html";
      foundations.textContent = "PA language, arithmetic axioms, and proof rules";
      prelude.appendChild(foundations);
      prelude.appendChild(document.createTextNode(" "));
      var preludeNote = document.createElement("small");
      preludeNote.textContent = "foundations prelude; not a theorem node";
      prelude.appendChild(preludeNote);
      list.appendChild(prelude);
    }
    selection.path.forEach(function (tag) {
      var pathNode = state.model.byTag.get(tag);
      var item = document.createElement("li");
      var link = document.createElement("a");
      link.href = "tag/" + tag + ".html";
      var code = document.createElement("code");
      code.textContent = tag;
      link.appendChild(code);
      link.appendChild(document.createTextNode(" · " + pathNode.name));
      item.appendChild(link);
      var layer = document.createElement("small");
      layer.textContent = "layer " + pathNode.layer;
      item.appendChild(layer);
      list.appendChild(item);
    });
    var note = state.root.querySelector("[data-graph-path-note]");
    if (state.view === "shortest") {
      note.textContent = "One short premise chain is listed below. Other valid routes may exist.";
    } else if (state.view === "corridor") {
      note.textContent = "The graph shows every node on a start-to-target route; this text alternative follows one critical/deepest chain through that corridor.";
    } else {
      note.textContent = "One critical/deepest premise chain is listed below. It is a navigation route, not the whole proof dependency cone.";
    }
  }

  function graphSynchronizeAddress(state) {
    if (!window.history || !window.history.replaceState) return;
    try {
      var target = new URL(window.location.href);
      target.searchParams.set("focus", state.target);
      target.searchParams.set("target", state.target);
      target.searchParams.set("view", state.view);
      target.searchParams.set("edges", state.edgeMode);
      if (state.source) target.searchParams.set("source", state.source);
      else target.searchParams.delete("source");
      window.history.replaceState(null, "", target.toString());
    } catch (_error) {
      /* The graph remains usable with a read-only address. */
    }
  }

  function graphViewLabel(view) {
    return {
      critical: "critical/deepest premise chain with direct target branches",
      shortest: "short premise chain with direct target branches",
      corridor: "start-to-target route corridor",
      prerequisites: "complete prerequisite cone",
      neighborhood: "direct neighborhood",
      dependents: "complete dependent cone",
      corpus: "entire theorem corpus"
    }[view] || "dependency view";
  }

  function graphRender(state, shouldCenter) {
    var selection = graphView(state.model, state.source, state.target, state.view);
    if ((state.view === "critical" || state.view === "shortest" || state.view === "corridor") && !selection.path.length) {
      state.sourceInput.setCustomValidity("The selected start theorem does not lead to this target.");
      state.sourceInput.reportValidity();
      return false;
    }
    state.sourceInput.setCustomValidity("");
    selection.displayedEdges = graphDisplayedEdges(state, selection);
    graphRenderSvg(state, selection);
    graphUpdateDetails(state, selection);
    var layers = Array.from(selection.tags).map(function (tag) {
      return Number(state.model.byTag.get(tag).layer);
    });
    var layerSpan = layers.length ? Math.min.apply(null, layers) + "–" + Math.max.apply(null, layers) : "none";
    state.summary.textContent = selection.tags.size + " theorem " + (selection.tags.size === 1 ? "node" : "nodes") +
      " · " + selection.displayedEdges.length + " of " + selection.edges.length + " direct dependency arrows shown" +
      " · layers " + layerSpan + " · " + graphViewLabel(state.view) +
      (state.compact ? " · compact clickable marks." : ".");
    graphSynchronizeAddress(state);
    window.requestAnimationFrame(function () {
      if (shouldCenter) graphCenterTarget(state);
      else graphFit(state);
    });
    return true;
  }

  function graphSelectTarget(state, tag) {
    if (!state.model.byTag.has(tag)) return;
    var former = state.target;
    state.target = tag;
    state.targetInput.value = tag;
    if (!graphRender(state, true)) {
      state.source = null;
      state.sourceInput.value = "";
      state.sourceInput.setCustomValidity("");
      graphRender(state, true);
      state.summary.textContent += " The previous start was cleared because it does not lead to this target.";
    }
    if (former !== tag) state.root.querySelector("[data-graph-title]").focus({ preventScroll: true });
  }

  function graphInstallViewportControls(state) {
    state.root.querySelector("[data-graph-zoom='in']").addEventListener("click", function () { graphZoom(state, 0.78); });
    state.root.querySelector("[data-graph-zoom='out']").addEventListener("click", function () { graphZoom(state, 1.28); });
    state.root.querySelector("[data-graph-center]").addEventListener("click", function () { graphCenterTarget(state); });
    state.root.querySelector("[data-graph-fit]").addEventListener("click", function () { graphFit(state); });

    var drag = null;
    state.svg.addEventListener("pointerdown", function (event) {
      if (event.button !== 0 || event.target.closest("[data-graph-node], a")) return;
      var box = state.currentViewBox;
      if (!box) return;
      drag = { pointer: event.pointerId, x: event.clientX, y: event.clientY, box: Object.assign({}, box) };
      state.svg.setPointerCapture(event.pointerId);
      state.stage.classList.add("pa-is-panning");
    });
    state.svg.addEventListener("pointermove", function (event) {
      if (!drag || event.pointerId !== drag.pointer) return;
      var scaleX = drag.box.width / Math.max(1, state.svg.clientWidth);
      var scaleY = drag.box.height / Math.max(1, state.svg.clientHeight);
      graphSetViewBox(state, {
        x: drag.box.x - (event.clientX - drag.x) * scaleX,
        y: drag.box.y - (event.clientY - drag.y) * scaleY,
        width: drag.box.width,
        height: drag.box.height
      });
    });
    function stopDrag(event) {
      if (!drag || event.pointerId !== drag.pointer) return;
      drag = null;
      state.stage.classList.remove("pa-is-panning");
    }
    state.svg.addEventListener("pointerup", stopDrag);
    state.svg.addEventListener("pointercancel", stopDrag);
    state.svg.addEventListener("wheel", function (event) {
      if (!(event.ctrlKey || event.metaKey)) return;
      event.preventDefault();
      graphZoom(state, event.deltaY < 0 ? 0.86 : 1.16);
    }, { passive: false });
    state.svg.addEventListener("keydown", function (event) {
      if (event.target.closest && event.target.closest("[data-graph-open]")) return;
      var node = event.target.closest && event.target.closest("[data-graph-node]");
      if (node && (event.key === "Enter" || event.key === " ")) {
        event.preventDefault();
        graphSelectTarget(state, node.dataset.graphNode);
        return;
      }
      if (event.key === "+" || event.key === "=") graphZoom(state, 0.78);
      else if (event.key === "-") graphZoom(state, 1.28);
      else if (event.key === "0") graphFit(state);
      else return;
      event.preventDefault();
    });
  }

  function initializeDependencyGraph(root) {
    var summary = root.querySelector("[data-graph-summary]");
    graphData(root).then(function (payload) {
      var model = graphModel(payload);
      if (!model.nodes.length) throw new Error("The graph payload contains no theorem nodes.");
      var parameters;
      try { parameters = new URL(window.location.href).searchParams; }
      catch (_error) { parameters = new URLSearchParams(); }
      var target = graphResolve(model, parameters.get("target") || parameters.get("focus")) ||
        (model.byTag.has("PA00FW") ? "PA00FW" : model.terminals[0] || model.nodes[model.nodes.length - 1].tag);
      var source = graphResolve(model, parameters.get("source"));
      var allowedViews = new Set(["critical", "shortest", "corridor", "prerequisites", "neighborhood", "dependents", "corpus"]);
      var view = allowedViews.has(parameters.get("view")) ? parameters.get("view") : "neighborhood";
      var allowedEdgeModes = new Set(["focus", "none", "all"]);
      var edgeMode = allowedEdgeModes.has(parameters.get("edges")) ? parameters.get("edges") : "focus";
      var state = {
        root: root,
        model: model,
        target: target,
        source: source,
        view: view,
        edgeMode: edgeMode,
        summary: summary,
        form: root.querySelector("[data-graph-form]"),
        sourceInput: root.querySelector("[data-graph-source]"),
        targetInput: root.querySelector("[data-graph-target]"),
        viewInput: root.querySelector("[data-graph-view]"),
        edgeInput: root.querySelector("[data-graph-edges]"),
        svg: root.querySelector("[data-graph-svg]"),
        stage: root.querySelector("[data-graph-stage]")
      };
      state.targetInput.value = target;
      state.sourceInput.value = source || "";
      state.viewInput.value = view;
      state.edgeInput.value = edgeMode;
      var datalist = root.querySelector("#pa-graph-theorems");
      model.nodes.forEach(function (node) {
        var option = document.createElement("option");
        option.value = node.tag;
        option.label = node.name + " · layer " + node.layer;
        datalist.appendChild(option);
      });
      state.form.addEventListener("submit", function (event) {
        event.preventDefault();
        var nextTarget = graphResolve(model, state.targetInput.value);
        var nextSource = state.sourceInput.value.trim() ? graphResolve(model, state.sourceInput.value) : null;
        state.targetInput.setCustomValidity(nextTarget ? "" : "Enter one exact theorem tag or theorem name.");
        state.sourceInput.setCustomValidity(!state.sourceInput.value.trim() || nextSource ? "" : "Enter one exact theorem tag or theorem name.");
        if (!nextTarget) return state.targetInput.reportValidity();
        if (state.sourceInput.value.trim() && !nextSource) return state.sourceInput.reportValidity();
        state.target = nextTarget;
        state.source = nextSource;
        state.view = state.viewInput.value;
        state.edgeMode = state.edgeInput.value;
        graphRender(state, true);
      });
      state.viewInput.addEventListener("change", function () {
        state.view = state.viewInput.value;
        graphRender(state, false);
      });
      state.edgeInput.addEventListener("change", function () {
        state.edgeMode = state.edgeInput.value;
        graphRender(state, false);
      });
      root.addEventListener("click", function (event) {
        if (event.target.closest("[data-graph-open]")) return;
        var control = event.target.closest("[data-graph-select]");
        var node = event.target.closest("[data-graph-node]");
        var tag = control ? control.dataset.graphSelect : node ? node.dataset.graphNode : null;
        if (tag) {
          event.preventDefault();
          graphSelectTarget(state, tag);
        }
      });
      graphInstallViewportControls(state);
      graphRender(state, true);
    }).catch(function (error) {
      summary.textContent = "Unable to load the theorem graph. " + error.message;
      var svg = root.querySelector("[data-graph-svg]");
      graphClear(svg);
      var message = graphSvgElement("text", { x: "24", y: "42" });
      message.textContent = "Graph data unavailable. The theorem index remains usable.";
      svg.appendChild(message);
    });
  }

  whenReady(function () {
    // Jupyter Book 1.x recursively registers nested _static JavaScript on
    // every Book page.  The generated microsite alone owns this body class;
    // leave the theorem atlas and all narrative chapters untouched.
    if (!document.body || !document.body.classList.contains("pa-proof-site")) return;
    document.querySelectorAll("[data-proof-dashboard]").forEach(initializeDashboard);
    initializeGraphNavigation();
    document.querySelectorAll("[data-dependency-graph]").forEach(initializeDependencyGraph);
    initializeCopyControls();
    markProofLine(false);
    window.addEventListener("hashchange", function () { markProofLine(true); });
  });
}());
