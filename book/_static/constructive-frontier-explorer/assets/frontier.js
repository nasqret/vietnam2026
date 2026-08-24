(() => {
  "use strict";
  const dashboard = document.querySelector("[data-defined-dashboard]");
  if (dashboard) {
    const input = dashboard.querySelector("[data-search]");
    const kind = dashboard.querySelector("[data-kind]");
    const clear = dashboard.querySelector("[data-clear]");
    const count = dashboard.querySelector("[data-count]");
    const entries = Array.from(dashboard.querySelectorAll("[data-entry]"));
    const refreshLibrary = () => {
      const query = input.value.toLowerCase().trim();
      let visible = 0;
      entries.forEach(entry => {
        const matched = (!query || entry.dataset.search.includes(query))
          && (kind.value === "all" || entry.dataset.kind === kind.value);
        entry.hidden = !matched;
        if (matched) visible += 1;
      });
      count.textContent = `${visible} ${visible === 1 ? "entry" : "entries"}`;
    };
    input.addEventListener("input", refreshLibrary);
    kind.addEventListener("change", refreshLibrary);
    clear.addEventListener("click", () => {
      input.value = "";
      kind.value = "all";
      refreshLibrary();
      input.focus();
    });
  }
  const source = document.getElementById("frontier-corpus");
  if (!source) return;
  const corpus = JSON.parse(source.textContent);
  const nodes = new Map(corpus.nodes.map(node => [node.name, node]));
  const external = new Map(corpus.external_dependencies.map(row => [row.name, row]));
  const definitions = new Map(corpus.definitions.map(row => [row.id, row]));
  const escape = value => String(value).replace(/[&<>"']/g, character => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[character]));
  const detail = document.getElementById("frontier-detail");
  const graph = document.getElementById("frontier-graph");
  const graphScroll = document.querySelector(".frontier-graph-scroll");
  const search = document.getElementById("frontier-search");
  const parameters = new URLSearchParams(window.location?.search || "");
  let selectedName = null;
  let displayMode = document.body?.dataset.frontierNotation === "exact"
    || parameters.get("notation") === "exact" ? "exact" : "defined";
  let dependencyFocus = parameters.get("view") === "prerequisites";
  let zoom = 1;

  function linkedParts(parts) {
    return parts.map(part => part.kind === "definition"
      ? `<button class="frontier-definition-link" data-definition="${escape(part.definition)}" type="button" title="Open exact conservative expansion">${escape(part.text)}</button>`
      : escape(part.text)).join("");
  }

  function openDefinition(identifier) {
    const card = document.getElementById(`frontier-definition-${identifier}`);
    if (!card) return;
    card.open = true;
    card.scrollIntoView({behavior:"smooth",block:"center"});
    card.querySelector("summary")?.focus();
  }

  function refreshVisibility() {
    const query = search?.value.toLowerCase().trim() || "";
    const matched = new Set(corpus.nodes.filter(node => !query || `${node.name} ${node.summary} ${node.statement} ${node.defined.defined_statement}`.toLowerCase().includes(query)).map(node => node.name));
    let neighborhood = null;
    if (dependencyFocus && selectedName) {
      neighborhood = new Set([selectedName, ...(nodes.get(selectedName)?.dependencies || [])]);
      corpus.edges.filter(edge => edge.source === selectedName).forEach(edge => neighborhood.add(edge.target));
    }
    const visible = name => matched.has(name) && (!neighborhood || neighborhood.has(name));
    document.querySelectorAll(".frontier-node").forEach(item => item.classList.toggle("dimmed", !visible(item.dataset.node)));
    document.querySelectorAll(".frontier-edge").forEach(item => item.classList.toggle("dimmed", !visible(item.dataset.source) || !visible(item.dataset.target)));
  }

  function setZoom(next) {
    if (!graph) return;
    zoom = Math.max(.18, Math.min(2.5, next));
    const viewBox = graph.viewBox.baseVal;
    graph.style.width = `${Math.round(viewBox.width * zoom)}px`;
    graph.style.height = `${Math.round(viewBox.height * zoom)}px`;
    const label = document.getElementById("frontier-zoom-level");
    if (label) label.textContent = `${Math.round(zoom * 100)}%`;
  }

  function openNode(name, center = false) {
    const node = nodes.get(name);
    if (!node) return;
    selectedName = name;
    document.querySelectorAll(".frontier-node.selected").forEach(item => item.classList.remove("selected"));
    document.querySelectorAll(".frontier-node").forEach(item => {
      if (item.dataset.node !== name) return;
      item.classList.add("selected");
      if (center) item.scrollIntoView({behavior:"smooth",block:"nearest",inline:"center"});
    });
    const dependencies = node.dependencies.map(dependency => {
      if (nodes.has(dependency)) {
        const target = nodes.get(dependency);
        const channel = target.enrolled_in_alpha ? `Alpha ${target.alpha_edition_version} · body checked; first enrolled ${target.alpha_admission_version}` : "candidate · unenrolled";
        const experiment = target.experimental_closure_verified ? " · independent replay experiment; not admitted" : "";
        return `<button class="frontier-chip internal" data-dependency="${escape(dependency)}" type="button">${escape(dependency)} · ${escape(channel)}${escape(experiment)}</button>`;
      }
      const evidence = external.get(dependency);
      const channel = evidence?.admitted_to_stable
        ? "Stable closed"
        : evidence?.admitted_to_alpha
          ? "Alpha closed"
          : evidence?.enrolled_in_alpha
            ? `Alpha ${evidence.alpha_edition_version} · ${evidence.alpha_evidence} · not admitted`
            : "candidate · unenrolled";
      const experiment = evidence?.experimental_closure_verified ? " · independent replay experiment; not admitted" : "";
      return `<button class="frontier-chip external" data-dependency="${escape(dependency)}" type="button" title="${escape(evidence?.evidence || "release-status-unattested")}">${escape(dependency)} · ${escape(channel)}${escape(experiment)}</button>`;
    }).join("");
    const provenance = node.sources.map(source => `<span class="frontier-chip ${source.selected ? "internal" : "external"}">${escape(source.source_module)} · ${source.selected ? "selected canonical source" : source.matches_selected_statement ? "matching alternate source" : "non-selected alternate statement"}</span>`).join("");
    const defined = node.defined;
    const readable = displayMode === "defined";
    const statement = readable ? linkedParts(defined.statement_parts) : escape(node.statement);
    const lineOverrides = new Map(defined.defined_script_lines.map(line => [line.number, line]));
    const proof = node.script.map((line, index) => {
      const number = index + 1;
      const compact = readable ? lineOverrides.get(number) : null;
      return `${String(number).padStart(3, "0")}  ${compact ? linkedParts(compact.command_parts) : escape(line)}`;
    }).join("\n");
    const uses = Object.entries(defined.definition_uses).map(([identifier, count]) => {
      const definition = definitions.get(identifier);
      return `<button class="frontier-chip internal" data-definition="${escape(identifier)}" type="button">${escape(definition?.name || identifier)} · ${count}</button>`;
    }).join("");
    const receipt = defined.statement_receipt;
    const attestation = receipt
      ? `<p class="frontier-receipt">Exact AST equivalence verified · ${receipt.expanded_characters} → ${receipt.defined_characters} characters · defined SHA-256 ${escape(receipt.defined_source_sha256)}</p><p><small>Canonical expanded AST SHA-256 ${escape(receipt.canonical_expansion_sha256)}</small></p>`
      : `<p class="frontier-mode-note">This statement remains exact only: ${escape(defined.statement_status)}. No unverified equivalence is claimed.</p>`;
    const experiment = node.experimental_closure_verified
      ? `<p class="frontier-experimental-note"><strong>Independent replay-verified experiment, not release evidence.</strong> Named microbatch ${escape(node.experimental_closure_microbatch)} previously checked an empty-context proof. No certificate is persisted; Alpha evidence remains body_checked, with no checked-use authority or Stable promotion.</p>`
      : "";
    const heading = readable ? "Readable conservative defined notation" : "Exact expanded first-order HA statement";
    const proofHeading = readable ? "Proof script with verified readable local propositions" : "Exact stored proof script";
    detail.innerHTML = `<h2>${escape(name)}</h2><p>${escape(node.summary)}</p><p class="frontier-status">${escape(node.status)}</p>${experiment}<p><small>${escape(node.source_module)} · exact statement SHA-256 ${escape(node.statement_sha256)}</small></p><h3>${heading}</h3><pre>${statement}</pre>${attestation}<h3>Linked definitions in this proof</h3><div class="frontier-dependency-list">${uses || "No reviewed notation aliases are needed for this formula."}</div><h3>Declared dependencies</h3><div class="frontier-dependency-list">${dependencies || "No declared dependencies."}</div><h3>Source provenance</h3><div class="frontier-dependency-list">${provenance}</div><h3>${proofHeading}</h3><pre>${proof || "No tactic commands."}</pre>`;
    detail.querySelectorAll("[data-dependency]").forEach(item => {
      if (nodes.has(item.dataset.dependency)) item.addEventListener("click", () => openNode(item.dataset.dependency,true));
    });
    detail.querySelectorAll("[data-definition]").forEach(item => item.addEventListener("click", () => openDefinition(item.dataset.definition)));
    refreshVisibility();
  }
  document.querySelectorAll(".frontier-node").forEach(item => {
    item.addEventListener("click", () => openNode(item.dataset.node));
    item.addEventListener("keydown", event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); openNode(item.dataset.node); } });
  });
  search?.addEventListener("input",refreshVisibility);
  document.querySelectorAll("[data-frontier-view]").forEach(button => {
    button.addEventListener("click", () => {
      displayMode = button.dataset.frontierView === "exact" ? "exact" : "defined";
      document.querySelectorAll("[data-frontier-view]").forEach(item => item.setAttribute("aria-pressed",String(item.dataset.frontierView === displayMode)));
      if (selectedName) openNode(selectedName);
    });
  });
  document.getElementById("frontier-zoom-out")?.addEventListener("click",()=>setZoom(zoom/1.2));
  document.getElementById("frontier-zoom-in")?.addEventListener("click",()=>setZoom(zoom*1.2));
  document.getElementById("frontier-zoom-fit")?.addEventListener("click",()=>{
    if (graph && graphScroll) setZoom((graphScroll.clientWidth-24)/graph.viewBox.baseVal.width);
  });
  document.getElementById("frontier-focus")?.addEventListener("click",event=>{
    dependencyFocus=!dependencyFocus;
    event.currentTarget.setAttribute("aria-pressed",String(dependencyFocus));
    refreshVisibility();
  });
  document.getElementById("frontier-print")?.addEventListener("click",()=>window.print());
  const prime = n => Number.isInteger(n) && n > 1 && Array.from({length: Math.max(0, Math.floor(Math.sqrt(n)) - 1)}, (_, i) => i + 2).every(d => n % d !== 0);
  function choose(n, k) { let result = 1n; for (let i = 1; i <= k; i++) result = result * BigInt(n - k + i) / BigInt(i); return result; }
  function valuation(n, p) { let count = 0; const base = BigInt(p); while (n > 0n && n % base === 0n) { n /= base; count++; } return count; }
  function carries(a, b, p) { let count = 0, carry = 0, first = a, second = b; const digits = []; while (first || second || carry) { const x = first % p, y = second % p, next = x + y + carry >= p ? 1 : 0; digits.push(`${x}+${y}+${carry}→${next}`); count += next; first = Math.floor(first / p); second = Math.floor(second / p); carry = next; if (digits.length > 64) break; } return {count, digits}; }
  function lucasDigitProduct(n, k, p) { let upper = n, lower = k, product = 1n; const digits = []; do { const nd = upper % p, kd = lower % p; const coefficient = kd <= nd ? choose(nd, kd) : 0n; product *= coefficient; digits.push(`C(${nd},${kd})=${coefficient}`); upper = Math.floor(upper / p); lower = Math.floor(lower / p); } while (upper || lower); return {product, digits}; }
  function twoSquare(n) { for (let x = 0; x * x <= n; x++) { const y = Math.floor(Math.sqrt(n - x * x)); if (x * x + y * y === n) return [x, y]; } return null; }
  function fourSquare(n) { for (let a = 0; a * a <= n; a++) for (let b = 0; a * a + b * b <= n; b++) for (let c = 0; a * a + b * b + c * c <= n; c++) { const d = Math.floor(Math.sqrt(n - a * a - b * b - c * c)); if (a * a + b * b + c * c + d * d === n) return [a, b, c, d]; } return null; }
  function greatestCommonDivisor(a, b) { let first = Math.abs(a), second = Math.abs(b); while (second) [first, second] = [second, first % second]; return first; }
  function factor(n) { if (n === 0) return {text:"0 (prime valuations undefined)",bad:[]}; let rest = n, text = [], bad = []; for (let p = 2; p * p <= rest; p++) if (rest % p === 0) { let e = 0; while (rest % p === 0) { rest /= p; e++; } text.push(`${p}^${e}`); if (p % 4 === 3 && e % 2) bad.push(`${p}^${e}`); } if (rest > 1) { text.push(`${rest}^1`); if (rest % 4 === 3) bad.push(`${rest}^1`); } return {text:text.join(" · ") || "1",bad}; }
  const example = document.querySelector("[data-example]");
  const form = example?.querySelector("[data-example-form]");
  const output = example?.querySelector("[data-example-result]");
  function calculate(event) {
    event?.preventDefault();
    try {
      const value = key => Number(example.querySelector(`[data-input="${key}"]`).value);
      if (corpus.example === "supplementary") { const p = value("n"); if (!prime(p) || p === 2) throw Error("Choose an odd prime ≤ 499."); const squares = new Set(Array.from({length:p},(_,x)=>(x*x)%p)); output.textContent = `p=${p}, p mod 4=${p%4}, p mod 8=${p%8}\n−1 is ${squares.has(p-1)?"a quadratic residue":"a nonresidue"}; 2 is ${squares.has(2)?"a quadratic residue":"a nonresidue"}.`; }
      else if (corpus.example === "kummer") { const p=value("p"),a=value("a"),b=value("b"); if (!prime(p)) throw Error("Choose a prime base."); const binomial=choose(a+b,a), count=carries(a,b,p), v=valuation(binomial,p); output.textContent=`C(${a+b},${a})=${binomial}; v_${p}=${v}; carry count=${count.count}\n${count.digits.join(" | ") || "no nonzero digits"}`; }
      else if (corpus.example === "lucas") { const p=value("p"),n=value("n"),k=value("k"); if (!prime(p)) throw Error("Choose a prime base."); if (![n,k].every(Number.isSafeInteger) || n < 0 || k < 0 || k > n) throw Error("Choose natural inputs with 0 ≤ k ≤ n."); const binomial=choose(n,k), expansion=lucasDigitProduct(n,k,p), modulus=BigInt(p); output.textContent=`C(${n},${k})=${binomial} ≡ ${binomial % modulus} (mod ${p})\n${expansion.digits.join(" · ")}\nDigit product=${expansion.product} ≡ ${expansion.product % modulus} (mod ${p})\nFinite numerical illustration; consult the proof map for the checked theorem boundary.`; }
      else if (corpus.example === "two-squares") { const n=value("n"); if (!Number.isInteger(n) || n < 0) throw Error("Choose a nonnegative integer."); const witness=twoSquare(n), factors=factor(n); output.textContent=`${n} = ${factors.text}\n${witness ? `${n} = ${witness[0]}² + ${witness[1]}²` : "No natural two-square witness."}${factors.bad.length ? `\nOdd 3-mod-4 factor: ${factors.bad.join(", ")}` : ""}`; }
      else if (corpus.example === "pythagorean") { const m=value("m"),n=value("n"); if (![m,n].every(Number.isSafeInteger) || n < 1 || m <= n) throw Error("Choose natural parameters with 0 < n < m."); const difference=m*m-n*n,doubled=2*m*n,hypotenuse=m*m+n*n,primitive=greatestCommonDivisor(m,n)===1 && (m-n)%2===1; output.textContent=`m=${m}, n=${n}\n(${difference}, ${doubled}, ${hypotenuse})\n${difference}² + ${doubled}² = ${hypotenuse}²\n${primitive ? "Coprime, opposite-parity parameters." : "Parameters do not satisfy the classical primitive criterion."}\nForward constructor only; primitive inverse classification and Fermat strict descent remain open.`; }
      else { const n=value("n"), witness=fourSquare(n); output.textContent=witness ? `${n} = ${witness[0]}² + ${witness[1]}² + ${witness[2]}² + ${witness[3]}²\nConstructive four-square witness; the kernel-checked universal theorem is available in the proof map.` : "No witness found inside the finite example search."; }
    } catch (error) { output.textContent=error.message; }
  }
  form?.addEventListener("submit",calculate);
  if (example && output) calculate();
  if (dependencyFocus) {
    document.getElementById("frontier-focus")?.setAttribute("aria-pressed", "true");
  }
  if (corpus.root_names.length) {
    const requested = parameters.get("target");
    openNode(nodes.has(requested) ? requested : corpus.root_names[corpus.root_names.length-1]);
  }
  const definitionHash = window.location?.hash || "";
  if (definitionHash.startsWith("#frontier-definition-")) {
    openDefinition(definitionHash.slice("#frontier-definition-".length));
  }
})();
