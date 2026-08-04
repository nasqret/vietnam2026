#!/usr/bin/env python3
"""Build the searchable arithmetic theorem atlas for the Jupyter Book.

The checked snapshot is the source of truth for native statements, authored
scripts, dependencies, certificate identities, and proof metrics.  The
research catalog contributes the human domain/title/status metadata.  Keeping
this page generated makes documentation drift a testable failure.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import html
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]
SNAPSHOT = REPO / "artifacts" / "peano-library" / "catalog-v1.json"
METRICS = REPO / "artifacts" / "peano-library" / "metrics.json"
RESEARCH = REPO / "research" / "arithmetic-library" / "catalog.json"
THEOREM_SOURCES = (
    REPO / "peano-lab" / "py" / "peano_lab" / "library" / "theorems.py",
    REPO / "peano-lab" / "py" / "peano_lab" / "library" / "parity.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "quadratic_residue_theorems.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "finite_fold_theorems.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "finite_range_theorems.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "finite_sum_theorems.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "finite_congruence_theorems.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "finite_bitcount_theorems.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "finite_factorial_theorems.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "power_congruence_theorems.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "power_algebra_theorems.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "gauss_sign_bridge.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "gauss_half_range.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "finite_permutation_theorems.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "finite_product_permutation_theorems.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "finite_product_reindex_support.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "qr_bounded_units.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "qr_prime_units.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "qr_small_moduli.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "ha_canonical_remainder_candidate.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "ha_canonical_congruence_candidate.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "wilson_inverse_point_candidate.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "ha_modular_inverse_candidate.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "ha_relational_lcm_candidate.py",
    REPO
    / "peano-lab"
    / "py"
    / "peano_lab"
    / "library"
    / "ha_lcm_totality_bridge_candidate.py",
)
OUTPUT = REPO / "book" / "arithmetic-library" / "theorem-atlas.md"

# The proof snapshot was published by this immutable commit before the book
# layer was added.  Permalinks keep every source, vault, and artifact receipt
# valid both in the draft PR and after later branch movement.
PROOF_SNAPSHOT_COMMIT = "ff3d0ebd440d52f3df12dbae765fe7acc53ee6c5"
GITHUB_ROOT = (
    "https://github.com/nasqret/vietnam2026/blob/" + PROOF_SNAPSHOT_COMMIT
)

DOMAIN_ORDER = (
    "equality",
    "addition",
    "multiplication",
    "order",
    "divisibility",
    "congruence",
    "division",
    "gcd_coprime",
    "primes",
    "factorization",
    "quadratic_residues",
)

DOMAIN_LABELS = {
    "equality": "Equality",
    "addition": "Addition",
    "multiplication": "Multiplication",
    "order": "Order",
    "divisibility": "Divisibility",
    "congruence": "Congruence & CRT",
    "division": "Division",
    "gcd_coprime": "GCD, Bézout & coprimality",
    "primes": "Primes",
    "factorization": "β sequences, products & FTA",
    "quadratic_residues": "Quadratic reciprocity campaign",
}

DOMAIN_CHAPTERS = {
    "equality": "../peano/induction-ladder.html",
    "addition": "../peano/induction-ladder.html",
    "multiplication": "../peano/induction-ladder.html",
    "order": "dependency-ladder.html",
    "divisibility": "divisibility-and-congruence.html",
    "congruence": "divisibility-and-congruence.html",
    "division": "guided-tour.html#stage-division",
    "gcd_coprime": "guided-tour.html#stage-bezout",
    "primes": "guided-tour.html#stage-primes",
    "factorization": "guided-tour.html#stage-factorization",
    "quadratic_residues": "quadratic-reciprocity.html",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _e(value: object, *, quote_attr: bool = True) -> str:
    return html.escape(str(value), quote=quote_attr)


def _source_lines(path: Path) -> dict[str, tuple[str, int]]:
    source = path.read_text(encoding="utf-8")
    relative = str(path.relative_to(REPO))
    result: dict[str, tuple[str, int]] = {}
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id not in {
            "TheoremSpec",
            "spec",
        }:
            continue
        name_node: ast.expr | None = node.args[0] if node.args else None
        if name_node is None:
            for keyword in node.keywords:
                if keyword.arg == "name":
                    name_node = keyword.value
                    break
        if not isinstance(name_node, ast.Constant) or not isinstance(name_node.value, str):
            # The reviewed small-modulus generator constructs exactly these
            # three finite-case names from the literal moduli 3, 5 and 7.
            # Keep their links on the helper that returns the specs while
            # retaining the literal-name requirement everywhere else.
            literal_fragments = "".join(
                item.value
                for item in getattr(name_node, "values", ())
                if isinstance(item, ast.Constant) and isinstance(item.value, str)
            )
            generated_small_moduli = {
                "lt__cases": ("lt_five_cases", "lt_seven_cases"),
                "bounded_square_mod_classify": (
                    "bounded_square_mod3_classify",
                    "bounded_square_mod5_classify",
                    "bounded_square_mod7_classify",
                ),
                "qres_mod_": (
                    "qres_mod3_zero",
                    "qres_mod3_one",
                    "qres_mod5_zero",
                    "qres_mod5_one",
                    "qres_mod5_four",
                    "qres_mod7_zero",
                    "qres_mod7_one",
                    "qres_mod7_two",
                    "qres_mod7_four",
                ),
                "qres_mod_canonical_iff": (
                    "qres_mod3_canonical_iff",
                    "qres_mod5_canonical_iff",
                    "qres_mod7_canonical_iff",
                ),
                "not_qres_mod_": (
                    "not_qres_mod3_two",
                    "not_qres_mod5_two",
                    "not_qres_mod5_three",
                    "not_qres_mod7_three",
                    "not_qres_mod7_five",
                    "not_qres_mod7_six",
                ),
            }
            if (
                path.name == "qr_small_moduli.py"
                and isinstance(name_node, ast.JoinedStr)
                and literal_fragments in generated_small_moduli
            ):
                for generated in generated_small_moduli[literal_fragments]:
                    result.setdefault(generated, (relative, node.lineno))
                continue
            raise ValueError(
                f"TheoremSpec in {relative} at line {node.lineno} has no literal name"
            )
        # The reconciled modular source intentionally repeats fourteen exact
        # overlaps.  The runtime exposes each only once; link to the first
        # declaration, which is the foundational entry selected by the ladder.
        result.setdefault(name_node.value, (relative, node.lineno))
    return result


def _research_by_runtime_name(rows: list[dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for row in rows:
        peano = row.get("peano")
        if peano is None:
            continue
        name = peano.get("existing_name") or row["id"]
        if name in result:
            raise ValueError(f"duplicate research mapping for {name}")
        result[name] = row
    return result


def _chips(names: list[str] | tuple[str, ...], *, empty: str) -> str:
    if not names:
        return f'<span class="pa-empty-relation">{_e(empty)}</span>'
    return " ".join(
        f'<a class="pa-theorem-chip" data-theorem-link="{_e(name)}" '
        f'href="#theorem-{_e(name)}"><code>{_e(name)}</code></a>'
        for name in names
    )


def _proof_recipe(theorem: dict) -> str:
    commands = [f"pa prove {theorem['statement']}"]
    commands.extend(f"use {name}" for name in theorem["dependencies"])
    commands.extend(theorem["script"])
    commands.append("qed")
    return "\n".join(commands)


def _card(
    theorem: dict,
    research: dict,
    dependents: dict[str, list[str]],
    source_lines: dict[str, tuple[str, int]],
) -> str:
    name = theorem["name"]
    domain = research["domain"]
    title = research.get("title") or theorem["summary"]
    summary = theorem["summary"]
    prerequisites = theorem["dependencies"]
    next_names = dependents[name]
    source_path, line = source_lines[name]
    source_url = (
        f"{GITHUB_ROOT}/{source_path}#L{line}"
    )
    vault_url = f"{GITHUB_ROOT}/vault/lemmas/{name}.md"
    artifact_url = f"{GITHUB_ROOT}/artifacts/peano-library/catalog-v1.json"
    research_url = f"{GITHUB_ROOT}/research/arithmetic-library/catalog.json"
    proof_id = f"proof-{name}"
    exact_id = f"statement-{name}"
    search_text = " ".join(
        [name, title, summary, theorem["statement"], domain, *prerequisites]
    ).lower()

    return f"""
<article class="pa-theorem-card" id="theorem-{_e(name)}"
  data-name="{_e(name)}" data-domain="{_e(domain)}"
  data-status="{_e(research['status'])}"
  data-dependencies="{_e(','.join(prerequisites))}"
  data-search="{_e(search_text)}">
  <details>
    <summary>
      <span class="pa-card-title"><code>{_e(name)}</code><span>{_e(title)}</span></span>
      <span class="pa-badge pa-domain-{_e(domain)}">{_e(DOMAIN_LABELS[domain])}</span>
      <span class="pa-badge pa-status-checked">checked</span>
    </summary>
    <div class="pa-card-body">
      <p class="pa-card-summary">{_e(summary)}</p>
      <div class="pa-relation-grid" aria-label="Theorem dependency neighborhood">
        <div><strong>Prerequisites</strong><div class="pa-chip-row">{_chips(prerequisites, empty='none — a root theorem')}</div></div>
        <div><strong>Used directly by</strong><div class="pa-chip-row">{_chips(next_names, empty='no direct dependent')}</div></div>
      </div>

      <details class="pa-proof-dropdown">
        <summary>Exact expanded PA statement</summary>
        <button class="pa-copy-button" type="button" data-copy-target="{exact_id}">Copy statement</button>
        <pre id="{exact_id}"><code>{_e(theorem['statement'])}</code></pre>
      </details>

      <details class="pa-proof-dropdown">
        <summary>Complete replay recipe: dependency imports + authored proof</summary>
        <button class="pa-copy-button" type="button" data-copy-target="{proof_id}">Copy proof</button>
        <pre id="{proof_id}"><code>{_e(_proof_recipe(theorem))}</code></pre>
      </details>

      <dl class="pa-proof-receipt">
        <div><dt>Occurrences</dt><dd>{theorem['proof_nodes']:,}</dd></div>
        <div><dt>Distinct objects</dt><dd>{theorem['distinct_proof_objects']:,}</dd></div>
        <div><dt>Reused references</dt><dd>{theorem['reused_proof_references']:,}</dd></div>
        <div><dt>Depth</dt><dd>{theorem['proof_depth']}</dd></div>
        <div><dt>Cuts</dt><dd>{theorem['cut_nodes']:,}</dd></div>
        <div><dt>Certificate SHA-256</dt><dd><code title="{_e(theorem['certificate_sha256'])}">{_e(theorem['certificate_sha256'][:12])}…</code></dd></div>
      </dl>

      <nav class="pa-card-links" aria-label="Links for {_e(name)}">
        <span class="pa-deployment-note" title="The public Peano Lab does not contain this candidate snapshot yet"><code>pa lib {_e(name)}</code> after promotion</span>
        <a href="{_e(source_url)}">Native source</a>
        <a href="{_e(vault_url)}">Vault note</a>
        <a href="{_e(artifact_url)}">Snapshot record</a>
        <a href="{_e(research_url)}">Research catalog</a>
        <a href="{_e(DOMAIN_CHAPTERS[domain])}">Read the chapter</a>
      </nav>
    </div>
  </details>
</article>""".strip()


def _blocked_card(row: dict) -> str:
    blocker = row["blocker"]
    dependencies = row.get("dependencies", [])
    detail = blocker["detail"].replace(
        "should be designed explicitly",
        "has now been designed explicitly and checked under a separate name",
    )
    return f"""
<article class="pa-theorem-card pa-blocked-card" id="boundary-{_e(row['id'])}"
  data-name="{_e(row['id'])}" data-domain="{_e(row['domain'])}"
  data-status="blocked_by_language"
  data-dependencies="{_e(','.join(dependencies))}"
  data-search="{_e(' '.join([row['id'], row['title'], row['summary'], detail]).lower())}">
  <details>
    <summary>
      <span class="pa-card-title"><code>{_e(row['id'])}</code><span>{_e(row['title'])}</span></span>
      <span class="pa-badge pa-domain-{_e(row['domain'])}">{_e(DOMAIN_LABELS[row['domain']])}</span>
      <span class="pa-badge pa-status-blocked">representation boundary</span>
    </summary>
    <div class="pa-card-body">
      <p class="pa-card-summary">{_e(row['summary'])}</p>
      <p>{_e(detail)}</p>
      <div><strong>Depends conceptually on</strong><div class="pa-chip-row">{_chips(dependencies, empty='none')}</div></div>
      <p><strong>Related representational choices:</strong> {_e('; '.join(blocker['unblocks_with']))}.</p>
      <p>This card deliberately contains no native proof script or certificate. The separately named balanced four-natural Bézout theorem is checked.</p>
    </div>
  </details>
</article>""".strip()


def render() -> str:
    snapshot = _load(SNAPSHOT)
    metrics = _load(METRICS)
    research_catalog = _load(RESEARCH)
    theorems = snapshot["theorems"]
    research_rows = research_catalog["lemmas"]
    research_by_name = _research_by_runtime_name(research_rows)
    source_lines: dict[str, tuple[str, int]] = {}
    for source_path in THEOREM_SOURCES:
        for name, location in _source_lines(source_path).items():
            source_lines.setdefault(name, location)

    names = [theorem["name"] for theorem in theorems]
    missing_research = sorted(set(names) - set(research_by_name))
    missing_source = sorted(set(names) - set(source_lines))
    if missing_research or missing_source:
        raise ValueError(
            "atlas inputs are incomplete: "
            f"research={missing_research}, source={missing_source}"
        )
    if len(names) != len(set(names)):
        raise ValueError("duplicate theorem name in checked snapshot")
    if metrics["theorem_count"] != len(theorems):
        raise ValueError("metrics theorem count disagrees with snapshot")

    dependents = {name: [] for name in names}
    for theorem in theorems:
        for dependency in theorem["dependencies"]:
            dependents[dependency].append(theorem["name"])

    checked_by_domain = {domain: 0 for domain in DOMAIN_ORDER}
    for theorem in theorems:
        checked_by_domain[research_by_name[theorem["name"]]["domain"]] += 1

    blocked = [row for row in research_rows if row["status"] == "blocked_by_language"]
    if len(blocked) != 1:
        raise ValueError(f"expected one language boundary, got {len(blocked)}")

    domain_options = "\n".join(
        f'<option value="{domain}">{_e(DOMAIN_LABELS[domain])} ({checked_by_domain[domain]})</option>'
        for domain in DOMAIN_ORDER
    )
    focus_options = "\n".join(
        f'<option value="{_e(theorem["name"])}">{_e(theorem["name"])} — {_e(research_by_name[theorem["name"]]["title"])}</option>'
        for theorem in theorems
    )
    cards = "\n\n".join(
        _card(theorem, research_by_name[theorem["name"]], dependents, source_lines)
        for theorem in theorems
    )
    blocked_cards = "\n\n".join(_blocked_card(row) for row in blocked)
    digest = hashlib.sha256(cards.encode("utf-8")).hexdigest()

    return f"""# The native theorem atlas

This is the complete interactive reading surface for the current native Peano
arithmetic library. It is generated from the same checked snapshot used by the
current library tests and catalog—not copied by hand. The released training
corpus remains explicitly frozen at its earlier 247-theorem checkpoint. Search
by mathematical idea, filter by
domain, focus a theorem to move backward to prerequisites or forward to its
clients, and expand any card to read the exact first-order statement and the
complete authored tactic recipe.

```{{admonition}} What “actual proof” means here
:class: tip
Every checked card embeds its full authored tactic body plus the explicit
`use` imports that reconstruct its dependencies. Replay produces one closed
self-contained certificate, which the independent kernel checks from the
empty context. The much larger certificate tree is identified by its hash and
metrics rather than pasted as tens of thousands of constructor nodes.
```

```{{admonition}} Public-lab deployment status
:class: caution
The {len(theorems)}-theorem candidate is checked locally but is not yet deployed to
the public Peano Lab. Cards therefore show the eventual `pa lib NAME` command
without turning it into a misleading live command link. The embedded recipe,
immutable source links, and local checkout are usable now.
```

<div class="pa-atlas-hero" role="note">
  <div><strong>{len(theorems)}</strong><span>checked native theorems</span></div>
  <div><strong>{metrics['total_proof_nodes']:,}</strong><span>structural proof occurrences</span></div>
  <div><strong>{metrics['total_cut_nodes']:,}</strong><span>self-contained Cuts</span></div>
  <div><strong>{len(blocked)}</strong><span>explicit language boundary</span></div>
</div>

Snapshot root: <code>{_e(snapshot['ordered_root_sha256'])}</code>
Generated card digest: <code>{digest}</code>

<noscript>
  <p class="pa-noscript">The theorem cards remain readable without JavaScript. Search, filtering, copy buttons, and the focused dependency navigator require JavaScript.</p>
</noscript>

```{{raw}} html
<div class="pa-atlas" data-pa-atlas data-snapshot="{_e(snapshot['ordered_root_sha256'])}">
  <section class="pa-atlas-controls" aria-label="Theorem atlas controls">
    <label>Search all names, statements, summaries, and prerequisites
      <input type="search" data-pa-search placeholder="Try: Euclid, remainder, beta, cancellation…" autocomplete="off">
    </label>
    <label>Domain
      <select data-pa-domain>
        <option value="all">All domains ({len(theorems)})</option>
        {domain_options}
      </select>
    </label>
    <label>Status
      <select data-pa-status>
        <option value="all">Checked + boundary</option>
        <option value="checked">Checked only ({len(theorems)})</option>
        <option value="blocked_by_language">Language boundary ({len(blocked)})</option>
      </select>
    </label>
    <button type="button" data-pa-clear>Clear filters</button>
    <output data-pa-count aria-live="polite">{len(theorems) + len(blocked)} entries</output>
  </section>

  <section class="pa-focus-panel" aria-labelledby="pa-focus-title">
    <div class="pa-focus-heading">
      <div><span class="pa-eyebrow">Back-and-forth navigator</span><h2 id="pa-focus-title">Focus one theorem</h2></div>
      <label>Selected theorem
        <select data-pa-focus>
          {focus_options}
        </select>
      </label>
      <label>Neighborhood depth
        <select data-pa-hops>
          <option value="1">1 hop</option>
          <option value="2" selected>2 hops</option>
          <option value="3">3 hops</option>
          <option value="4">4 hops</option>
        </select>
      </label>
    </div>
    <div class="pa-focus-graph" data-pa-focus-graph aria-live="polite"></div>
  </section>

  <div class="pa-atlas-list" data-pa-list>
{cards}

{blocked_cards}
  </div>
</div>
```

## How to use this atlas

- Start with the {{doc}}`guided route <guided-tour>` if the exact formulas are
  unfamiliar.
- Select `division_remainder_exists`, `euclid_prime_dvd_product`,
  `beta_prefix_product_trace_exists`, `prime_factorization_existence`, or
  `fundamental_theorem_of_arithmetic` in the focused navigator to see the main
  dependency spine.
- A theorem card's prerequisite and dependent chips are bidirectional links.
  Browser Back and Forward therefore become mathematical navigation controls.
- The `pa lib NAME` label is the command to run in this candidate checkout and
  will become a live browser action only after this checked build is
  promoted. “Native source” and “Vault note” already point to immutable proof
  material.
- The single boundary card is intentionally not presented as proved. It keeps
  the conventional integer-coefficient Bézout interface distinct from the
  checked balanced-natural theorem.

This page is regenerated with:

```console
python3 scripts/build_arithmetic_book_atlas.py
python3 scripts/build_arithmetic_book_atlas.py --check
```
"""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if the generated page has drifted")
    args = parser.parse_args(argv)
    rendered = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
            print(f"arithmetic theorem atlas is stale: {OUTPUT}", file=sys.stderr)
            return 1
        print(f"verified arithmetic theorem atlas: {OUTPUT}")
        return 0
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"wrote arithmetic theorem atlas: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
