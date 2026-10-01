/* No network dependency: works over file:// as well as HTTP. Planned edges only. */
(() => {
  "use strict";
  const plan = JSON.parse(document.getElementById("plan-data").textContent);
  const nodes = new Map(plan.nodes.map(n => [n.id, n]));
  const by = id => document.getElementById(id);
  const target = by("plan-target"), view = by("plan-view"), definitions = by("plan-definitions");
  const params = new URLSearchParams(location.search);
  const svgNS = "http://www.w3.org/2000/svg";
  function element(tag, attrs = {}, text = "") {
    const e = document.createElementNS(svgNS, tag);
    for (const [key, value] of Object.entries(attrs)) e.setAttribute(key, String(value));
    if (text) e.textContent = text;
    return e;
  }
  function parents(id, includeDefinitions = false) {
    const n = nodes.get(id);
    return n.deps.concat(includeDefinitions ? (n.definitions || []) : []);
  }
  function closure(id, includeDefinitions = false) {
    const seen = new Set();
    function visit(key) { if (seen.has(key)) return; seen.add(key); parents(key, includeDefinitions).forEach(visit); }
    visit(id); return seen;
  }
  for (const node of plan.nodes) {
    const option = document.createElement("option");
    option.value = node.id; option.textContent = node.id + " — " + node.title;
    target.appendChild(option);
  }
  target.value = nodes.has(params.get("target")) ? params.get("target") : plan.active_target;
  view.value = ["overview", "prerequisites", "neighborhood", "all"].includes(params.get("view")) ? params.get("view") : "overview";
  definitions.checked = params.get("definitions") === "1";
  const landmarks = new Set(["IR012", "IR024", "IR027", "IR035", "IR043", "IR048", "IR058", "IR064", "IR068", "IR072", "IR073", "TR003", "TR006"]);
  function render() {
    const current = nodes.get(target.value);
    let selected;
    if (view.value === "prerequisites") selected = closure(current.id, definitions.checked);
    else if (view.value === "neighborhood") {
      selected = new Set([current.id, ...parents(current.id, definitions.checked)]);
      for (const n of plan.nodes) if (parents(n.id, definitions.checked).includes(current.id)) selected.add(n.id);
    } else if (view.value === "all") selected = new Set(nodes.keys());
    else selected = new Set([...landmarks, current.id]);
    if (!definitions.checked) for (const id of selected) if (nodes.get(id).kind === "definition" && id !== current.id) selected.delete(id);
    if (view.value === "overview" && definitions.checked) {
      for (const id of [...selected]) for (const d of nodes.get(id).definitions || []) closure(d, true).forEach(x => selected.add(x));
    }
    let edges = plan.dag.edges.filter(e => selected.has(e.source) && selected.has(e.target));
    if (view.value === "overview") {
      const reach = new Map([...selected].map(id => [id, closure(id, false)]));
      for (const to of selected) for (const from of selected) {
        if (from === to || !reach.get(to).has(from) || edges.some(e => e.source === from && e.target === to)) continue;
        if ([...selected].some(mid => mid !== from && mid !== to && reach.get(to).has(mid) && reach.get(mid).has(from))) continue;
        edges.push({source: from, target: to, kind: "planned_prerequisite"});
      }
    }
    const ranks = new Map();
    for (const id of plan.dag.order.filter(id => selected.has(id))) {
      ranks.set(id, Math.max(0, ...edges.filter(e => e.target === id).map(e => ranks.get(e.source) + 1)));
    }
    const columns = new Map(), positions = new Map();
    for (const id of selected) {
      const col = ranks.get(id) || 0;
      const row = columns.get(col) || 0; columns.set(col, row + 1);
      positions.set(id, {x: 24 + col * 246, y: 24 + row * 92});
    }
    const width = (Math.max(0, ...columns.keys()) + 1) * 246 + 24;
    const height = Math.max(1, ...columns.values()) * 92 + 24;
    const svg = by("plan-graph"); svg.replaceChildren();
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.setAttribute("width", String(width)); svg.setAttribute("height", String(height));
    const defs = element("defs"), marker = element("marker", {id: "plan-arrow", viewBox: "0 0 10 10", refX: 8, refY: 5, markerWidth: 5, markerHeight: 5, orient: "auto-start-reverse"});
    marker.appendChild(element("polygon", {points: "0,0 10,5 0,10", fill: "#a77632"})); defs.appendChild(marker); svg.appendChild(defs);
    for (const edge of edges) {
      const a = positions.get(edge.source), b = positions.get(edge.target);
      svg.appendChild(element("path", {class: edge.kind, "marker-end": "url(#plan-arrow)", d: `M ${a.x+214} ${a.y+32} C ${a.x+235} ${a.y+32},${b.x-20} ${b.y+32},${b.x} ${b.y+32}`}));
    }
    for (const id of selected) {
      const node = nodes.get(id), p = positions.get(id);
      const link = element("a", {href: `?target=${id}&view=neighborhood&v=${plan.current_catalog_revision}`, class: `plan-node ${node.kind}${id === current.id ? " selected" : ""}`, tabindex: 0});
      link.appendChild(element("title", {}, `${id}: ${node.title}. ${node.status}. ${node.contract}`));
      link.appendChild(element("rect", {x:p.x, y:p.y, width:214, height:66, rx:8}));
      link.appendChild(element("text", {x:p.x+10, y:p.y+19, class:"node-id"}, `${id} · ${node.status}`));
      const words = node.title.split(" "); let line = "", lines = [];
      for (const word of words) { if ((line + " " + word).length > 29) {lines.push(line); line = word;} else line += (line ? " " : "") + word; }
      lines.push(line); lines.slice(0,2).forEach((t,i) => link.appendChild(element("text", {x:p.x+10, y:p.y+38+i*14}, t)));
      link.addEventListener("click", event => {event.preventDefault(); target.value=id; view.value="neighborhood"; render();}); svg.appendChild(link);
    }
    const details = by("plan-details"); details.replaceChildren();
    const heading = document.createElement("h2"); heading.textContent = current.id + " — " + current.title;
    const contract = document.createElement("p"); contract.className="contract"; contract.textContent=current.contract;
    const boundary = document.createElement("p"); boundary.textContent="Planned, not proved. " + (current.method ? "Method: " + current.method + "; induction: " + current.induction + "; risk: " + current.risk + "." : "Proposed definition; kernel elaboration and hygiene checks are still required.");
    const link = document.createElement("a"); link.href=(current.kind === "definition" ? "definitions/" : "lemmas/") + current.id + ".html?v=" + plan.current_catalog_revision; link.textContent="Open full contract and prerequisites →";
    details.append(heading,contract,boundary,link);
    by("plan-summary").textContent=`${selected.size} planning nodes and ${edges.length} proposed arrows shown. 0 new verified theorems. Scroll horizontally for deeper layers; select any node to explore its neighborhood.`;
    const route = new URL(location.href); route.searchParams.set("target",current.id); route.searchParams.set("view",view.value); route.searchParams.set("definitions",definitions.checked ? "1" : "0");
    try { history.replaceState(null,"",route); } catch (_) { /* file:// navigation remains functional */ }
  }
  by("plan-controls").addEventListener("submit", event => event.preventDefault());
  [target,view,definitions].forEach(e => e.addEventListener("change",render));
  by("plan-print").addEventListener("click",() => window.print());
  render();
})();
