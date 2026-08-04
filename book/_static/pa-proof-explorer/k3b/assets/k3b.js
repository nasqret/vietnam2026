/* Progressive, dependency-free interaction for the private K3B graph. */
(function () {
  "use strict";

  var SVG_NS = "http://www.w3.org/2000/svg";
  var NODE_WIDTH = 246;
  var NODE_HEIGHT = 54;
  var SOURCE_BASE = "https://github.com/nasqret/vietnam2026/blob/";
  var RECEIPT_HREF = "https://github.com/nasqret/vietnam2026/blob/51f6e081a4aa1223bcdff7ff3ff0a662de8f9b08/artifacts/peano-library/ha-k3b-listat-full-closure-219217.json";

  function ready(callback) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", callback, { once: true });
    } else {
      callback();
    }
  }

  function svgElement(name, attributes) {
    var element = document.createElementNS(SVG_NS, name);
    Object.keys(attributes || {}).forEach(function (key) {
      element.setAttribute(key, String(attributes[key]));
    });
    return element;
  }

  function appendPair(list, key, value) {
    var term = document.createElement("dt");
    var detail = document.createElement("dd");
    term.textContent = key;
    detail.textContent = value;
    list.append(term, detail);
  }

  function statusText(node) {
    if (node.status === "public_checked") return "Public checked prerequisite";
    if (node.status === "conservative_definition") return "Conservative display definition — not a theorem";
    if (node.status === "private_support") return "Private closed support — unregistered and unadmitted";
    return "Private closed_checked_candidate — unregistered and unadmitted";
  }

  function labelLines(label) {
    if (label.length <= 25) return [label];
    var words = label.split("_");
    var midpoint = label.length / 2;
    var left = [];
    var right = words.slice();
    while (right.length > 1 && (left.join("_").length < midpoint || left.length === 0)) {
      left.push(right.shift());
    }
    return [left.join("_"), right.join("_")];
  }

  function initialize() {
    if (!document.body || !document.body.classList.contains("k3b-site")) return;
    var root = document.querySelector("[data-k3b-graph]");
    var encoded = document.getElementById("k3b-graph-data");
    if (!root || !encoded) return;

    var graph;
    try {
      graph = JSON.parse(encoded.textContent);
    } catch (_error) {
      return;
    }

    var nodes = graph.nodes.slice();
    var edges = graph.edges.slice();
    var byId = new Map(nodes.map(function (node) { return [node.id, node]; }));
    var focusInput = root.querySelector("[data-k3b-focus]");
    var viewControl = root.querySelector("[data-k3b-view]");
    var edgeControl = root.querySelector("[data-k3b-edges]");
    var form = root.querySelector("[data-k3b-form]");
    var dataList = document.getElementById("k3b-node-list");
    var svg = root.querySelector("[data-k3b-svg]");
    var summary = root.querySelector("[data-k3b-summary]");
    var reset = root.querySelector("[data-k3b-reset]");
    if (!focusInput || !viewControl || !edgeControl || !form || !dataList || !svg) return;

    nodes.slice().sort(function (a, b) {
      return a.label.localeCompare(b.label);
    }).forEach(function (node) {
      var option = document.createElement("option");
      option.value = node.id;
      option.label = node.label + " · " + node.kind;
      dataList.appendChild(option);
    });

    function findNode(value) {
      var normalized = String(value || "").trim().toLowerCase();
      return byId.get(normalized) || nodes.find(function (node) {
        return node.label.toLowerCase() === normalized;
      });
    }

    var parameters;
    try {
      parameters = new URL(window.location.href).searchParams;
    } catch (_error) {
      parameters = new URLSearchParams();
    }
    var initial = findNode(parameters.get("focus")) || byId.get(graph.default_focus);
    var current = initial.id;
    focusInput.value = current;
    if (["neighborhood", "all"].indexOf(parameters.get("view")) !== -1) {
      viewControl.value = parameters.get("view");
    }
    if (["focus", "all", "none"].indexOf(parameters.get("edges")) !== -1) {
      edgeControl.value = parameters.get("edges");
    }

    function synchronizeAddress() {
      if (!window.history || !window.history.replaceState) return;
      try {
        var target = new URL(window.location.href);
        target.searchParams.set("focus", current);
        target.searchParams.set("view", viewControl.value);
        target.searchParams.set("edges", edgeControl.value);
        window.history.replaceState(null, "", target.toString());
      } catch (_error) {
        /* The graph remains usable in a read-only location. */
      }
    }

    function immediateIds(id) {
      var ids = new Set([id]);
      edges.forEach(function (edge) {
        if (edge.target === id) ids.add(edge.source);
        if (edge.source === id) ids.add(edge.target);
      });
      return ids;
    }

    function visibleNodes() {
      var ids = viewControl.value === "all"
        ? new Set(nodes.map(function (node) { return node.id; }))
        : immediateIds(current);
      return nodes.filter(function (node) { return ids.has(node.id); });
    }

    function visibleEdges(ids) {
      if (edgeControl.value === "none") return [];
      return edges.filter(function (edge) {
        if (!ids.has(edge.source) || !ids.has(edge.target)) return false;
        return edgeControl.value === "all" || edge.source === current || edge.target === current;
      });
    }

    function sortNodes(items) {
      return items.slice().sort(function (a, b) {
        if (a.kind !== b.kind) {
          var order = { definition: 0, public: 1, private: 2 };
          return order[a.kind] - order[b.kind];
        }
        return a.label.localeCompare(b.label);
      });
    }

    function stack(items, x, height) {
      var gap = 72;
      var block = Math.max(1, items.length) * gap;
      var top = Math.max(44, (height - block) / 2 + gap / 2);
      var positions = new Map();
      items.forEach(function (node, index) {
        positions.set(node.id, { x: x, y: top + index * gap });
      });
      return positions;
    }

    function neighborhoodLayout(visible) {
      var incomingIds = new Set(edges.filter(function (edge) {
        return edge.target === current;
      }).map(function (edge) { return edge.source; }));
      var outgoingIds = new Set(edges.filter(function (edge) {
        return edge.source === current;
      }).map(function (edge) { return edge.target; }));
      var incoming = sortNodes(visible.filter(function (node) { return incomingIds.has(node.id); }));
      var outgoing = sortNodes(visible.filter(function (node) {
        return outgoingIds.has(node.id) && !incomingIds.has(node.id);
      }));
      var height = Math.max(560, Math.max(incoming.length, outgoing.length, 1) * 72 + 80);
      var positions = stack(incoming, 155, height);
      positions.set(current, { x: 490, y: height / 2 });
      stack(outgoing, 825, height).forEach(function (value, key) {
        positions.set(key, value);
      });
      return { positions: positions, width: 980, height: height };
    }

    function fullLayout(visible) {
      var layers = new Map();
      visible.forEach(function (node) {
        if (!layers.has(node.layer)) layers.set(node.layer, []);
        layers.get(node.layer).push(node);
      });
      var largest = Math.max.apply(null, Array.from(layers.values()).map(function (items) {
        return items.length;
      }));
      var height = Math.max(720, largest * 68 + 80);
      var positions = new Map();
      Array.from(layers.keys()).sort(function (a, b) { return a - b; }).forEach(function (layer) {
        stack(sortNodes(layers.get(layer)), 155 + layer * 290, height).forEach(function (value, key) {
          positions.set(key, value);
        });
      });
      return { positions: positions, width: 2050, height: height };
    }

    function edgePath(source, target) {
      var dx = target.x - source.x;
      var dy = target.y - source.y;
      if (Math.abs(dx) >= 80) {
        var direction = dx > 0 ? 1 : -1;
        var sx = source.x + direction * NODE_WIDTH / 2;
        var tx = target.x - direction * NODE_WIDTH / 2 - direction * 3;
        var bend = sx + (tx - sx) / 2;
        return "M" + sx + "," + source.y + " C" + bend + "," + source.y + " " + bend + "," + target.y + " " + tx + "," + target.y;
      }
      var vertical = dy > 0 ? 1 : -1;
      var sy = source.y + vertical * NODE_HEIGHT / 2;
      var ty = target.y - vertical * NODE_HEIGHT / 2 - vertical * 3;
      var side = source.x + NODE_WIDTH / 2 + 34;
      return "M" + source.x + "," + sy + " C" + side + "," + sy + " " + side + "," + ty + " " + target.x + "," + ty;
    }

    function drawNode(node, position, layer) {
      var group = svgElement("g", {
        "class": "k3b-node k3b-node-" + node.kind + (node.id === current ? " k3b-node-selected" : ""),
        "data-node-id": node.id,
        "role": "button",
        "tabindex": "0",
        "aria-label": node.label + ". " + statusText(node),
        "transform": "translate(" + position.x + " " + position.y + ")"
      });
      var title = svgElement("title");
      title.textContent = node.label + " — " + node.summary;
      group.appendChild(title);
      if (node.kind === "definition") {
        var half = NODE_WIDTH / 2;
        var inset = 24;
        group.appendChild(svgElement("polygon", {
          points: (-half + inset) + "," + (-NODE_HEIGHT / 2) + " " +
            (half - inset) + "," + (-NODE_HEIGHT / 2) + " " +
            half + ",0 " + (half - inset) + "," + (NODE_HEIGHT / 2) + " " +
            (-half + inset) + "," + (NODE_HEIGHT / 2) + " " + (-half) + ",0"
        }));
      } else {
        group.appendChild(svgElement("rect", {
          x: -NODE_WIDTH / 2,
          y: -NODE_HEIGHT / 2,
          width: NODE_WIDTH,
          height: NODE_HEIGHT,
          rx: node.kind === "private" ? 13 : 2
        }));
      }
      var text = svgElement("text", { x: 0, y: 0 });
      var lines = labelLines(node.label);
      lines.forEach(function (line, index) {
        var tspan = svgElement("tspan", {
          x: 0,
          dy: index === 0 ? (lines.length === 1 ? "0.35em" : "-0.15em") : "1.15em"
        });
        tspan.textContent = line;
        text.appendChild(tspan);
      });
      group.appendChild(text);
      group.addEventListener("click", function () { select(node.id, true); });
      group.addEventListener("keydown", function (event) {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          select(node.id, true);
        }
      });
      layer.appendChild(group);
    }

    function relationList(container, items) {
      container.replaceChildren();
      if (!items.length) {
        var empty = document.createElement("li");
        empty.textContent = "None in this direct graph";
        container.appendChild(empty);
        return;
      }
      items.sort(function (a, b) {
        return byId.get(a.id).label.localeCompare(byId.get(b.id).label);
      }).forEach(function (item) {
        var row = document.createElement("li");
        var button = document.createElement("button");
        button.type = "button";
        button.textContent = byId.get(item.id).label + (item.kind === "notation" ? " · notation" : "");
        button.addEventListener("click", function () { select(item.id, true); });
        row.appendChild(button);
        container.appendChild(row);
      });
    }

    function addLink(container, href, label) {
      var link = document.createElement("a");
      link.href = href;
      link.textContent = label;
      container.appendChild(link);
    }

    function updateDetails(node) {
      root.querySelector("[data-k3b-title]").textContent = node.label;
      root.querySelector("[data-k3b-status]").textContent = statusText(node);
      root.querySelector("[data-k3b-description]").textContent = node.summary;
      var metrics = root.querySelector("[data-k3b-metrics]");
      metrics.replaceChildren();
      appendPair(metrics, "Kind", node.kind);
      if (node.metrics) {
        appendPair(metrics, "Nodes / depth", node.metrics.nodes.toLocaleString() + " / " + node.metrics.depth);
        appendPair(metrics, "Objects / edges", node.metrics.objects.toLocaleString() + " / " + node.metrics.edges.toLocaleString());
        appendPair(metrics, "Reused / Cuts", node.metrics.reused.toLocaleString() + " / " + node.metrics.cuts.toLocaleString());
      }
      var links = root.querySelector("[data-k3b-links]");
      links.replaceChildren();
      addLink(links, node.href, node.kind === "public" ? "Open public proof" : "Open Book explanation");
      if (node.source_path) {
        addLink(links, SOURCE_BASE + graph.receipt.source_commit + "/" + node.source_path + "#L" + node.source_line, "Tactic source");
      }
      if (node.test_path) {
        addLink(links, SOURCE_BASE + graph.receipt.source_commit + "/" + node.test_path + "#L" + node.test_line, "Focused audit");
      }
      if (node.metrics) addLink(links, RECEIPT_HREF, "WMI receipt");
      var dependencies = edges.filter(function (edge) { return edge.target === node.id; }).map(function (edge) {
        return { id: edge.source, kind: edge.kind };
      });
      var dependents = edges.filter(function (edge) { return edge.source === node.id; }).map(function (edge) {
        return { id: edge.target, kind: edge.kind };
      });
      relationList(root.querySelector("[data-k3b-dependencies]"), dependencies);
      relationList(root.querySelector("[data-k3b-dependents]"), dependents);
    }

    function draw() {
      var visible = visibleNodes();
      var ids = new Set(visible.map(function (node) { return node.id; }));
      var shownEdges = visibleEdges(ids);
      var layout = viewControl.value === "all" ? fullLayout(visible) : neighborhoodLayout(visible);
      svg.setAttribute("viewBox", "0 0 " + layout.width + " " + layout.height);
      svg.style.width = layout.width + "px";
      svg.style.height = layout.height + "px";
      Array.from(svg.querySelectorAll(".k3b-render")).forEach(function (item) { item.remove(); });
      var edgeLayer = svgElement("g", { "class": "k3b-render k3b-edge-layer" });
      shownEdges.forEach(function (edge) {
        edgeLayer.appendChild(svgElement("path", {
          "class": "k3b-edge k3b-edge-" + edge.kind,
          d: edgePath(layout.positions.get(edge.source), layout.positions.get(edge.target))
        }));
      });
      svg.appendChild(edgeLayer);
      var nodeLayer = svgElement("g", { "class": "k3b-render k3b-node-layer" });
      visible.forEach(function (node) {
        drawNode(node, layout.positions.get(node.id), nodeLayer);
      });
      svg.appendChild(nodeLayer);
      if (summary) {
        summary.textContent = visible.length + " of " + nodes.length + " nodes · " + shownEdges.length + " direct arrows shown · focus " + byId.get(current).label;
      }
      updateDetails(byId.get(current));
    }

    function select(id, updateAddress) {
      if (!byId.has(id)) return;
      current = id;
      focusInput.value = id;
      focusInput.setCustomValidity("");
      if (updateAddress) synchronizeAddress();
      draw();
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var node = findNode(focusInput.value);
      if (!node) {
        focusInput.setCustomValidity("Choose a node from the K3B graph.");
        focusInput.reportValidity();
        return;
      }
      select(node.id, true);
    });
    viewControl.addEventListener("change", function () { synchronizeAddress(); draw(); });
    edgeControl.addEventListener("change", function () { synchronizeAddress(); draw(); });
    focusInput.addEventListener("input", function () { focusInput.setCustomValidity(""); });
    if (reset) {
      reset.addEventListener("click", function () {
        viewControl.value = "neighborhood";
        edgeControl.value = "focus";
        select(graph.default_focus, true);
      });
    }

    draw();
  }

  ready(initialize);
}());
