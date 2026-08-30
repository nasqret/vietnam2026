"""Read-only, bounded exposure audit for proposed frontier benchmark families.

This module never grants a test seal, training admission, or human review.
Exact alpha-canonical formula and rendered-state comparisons are reproducible.
An additional logical skeleton check deliberately over-approximates template
reuse: it erases arithmetic atoms and outer universal parameters. Its matches
are review flags, not proofs of semantic equivalence. A caller must enumerate
the source files and separately disclose gaps in historical coverage.

No model, network, subprocess, proof replay, or corpus regeneration is used.
Run substantial inventories in the existing caller-owned bounded CPU worker.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import stat


SCHEMA = "peano-hydra-frontier-benchmark-exposure-audit-v1"
MAX_FILE_BYTES = 96 * 1024**2
MAX_TOTAL_BYTES = 2 * 1024**3
MAX_ROW_BYTES = 2 * 1024**2
MAX_FORMULA_BYTES = 16 * 1024
MAX_FILES = 2048
MAX_RECORDS = 1000000
MAX_FEATURES = 1000000
MAX_EXAMPLES = 3
_NUMERAL = re.compile(r"(?<![A-Za-z_0-9'])[0-9]+")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z_0-9.:-]*\Z")


def logical_count_signature(source):
    """Necessary equality invariant, not a parser or equivalence decision.

    Negation expands to implication/bottom; <= expands to one existential
    equation. Quantifiers and all term operations are ignored, so this also
    is a necessary invariant of our deliberately coarse logical skeleton.
    Nonmatching counts can safely rule out a syntactic alias without expanding
    a huge numeral or a quarter-megabyte catalog formula into a native AST.
    """
    negations = len(re.findall(r"[~¬]", source))
    return [len(re.findall(r"<=|≤|=", source)),
            len(re.findall(r"->|→", source)) + negations,
            len(re.findall(r"/\\|∧", source)), len(re.findall(r"\\/|∨", source)),
            len(re.findall(r"⊥|(?<![\w'])(?:bot|false)(?![\w'])", source)) + negations]


class BenchmarkAuditError(ValueError):
    """An input escaped its declared identity or resource boundary."""


def canonical_bytes(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode()


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _require(condition, message):
    if not condition:
        raise BenchmarkAuditError(message)


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        _require(key not in value, "duplicate JSON key")
        value[key] = item
    return value


def _decode(raw):
    def nonfinite(value):
        raise BenchmarkAuditError("non-finite JSON value")
    try:
        return json.loads(raw, object_pairs_hook=_pairs, parse_constant=nonfinite)
    except (ValueError, RecursionError, UnicodeError) as error:
        raise BenchmarkAuditError(f"invalid JSON: {error}") from None


def read_file(path, expected_sha256=None):
    """Read one bounded regular file and detect replacement during the read."""
    path = Path(path)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            _require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_FILE_BYTES,
                     "source is not a bounded regular file")
            raw = stream.read(MAX_FILE_BYTES + 1)
            after = os.fstat(stream.fileno())
        _require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns,
                  before.st_ctime_ns) == (after.st_dev, after.st_ino, after.st_size,
                                         after.st_mtime_ns, after.st_ctime_ns)
                 and len(raw) == before.st_size, "source changed while reading")
    except OSError as error:
        raise BenchmarkAuditError(f"cannot read source: {error}") from None
    sha = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None:
        _require(type(expected_sha256) is str and _SHA.fullmatch(expected_sha256),
                 "source anchor must be a raw SHA-256")
        _require(sha == expected_sha256, "source raw SHA-256 differs from anchor")
    return raw, {"path": str(path), "bytes": len(raw), "sha256": sha}


@lru_cache(maxsize=65536)
def formula_features(source):
    """Canonical text, closedness and conservative whole-formula skeleton."""
    _require(type(source) is str and 0 < len(source.encode()) <= MAX_FORMULA_BYTES,
             "formula text exceeds bound")
    _require("\n" not in source and "\r" not in source and "?" not in source,
             "formula is multiline or contains an unresolved metavariable")
    _require(not any(c.isdigit() and not c.isascii() for c in source),
             "non-ASCII numeral is outside audit profile")
    _require(all(len(n) <= 3 and int(n) <= 256 for n in _NUMERAL.findall(source)),
             "numeral exceeds audit profile")
    _require(source.count("(") <= 512 and len(source.split()) <= 4096,
             "formula parser work exceeds bound")
    from peano_lab.kernel.formulas import (And, Bot, Eq, Exists, Forall, Imp, Or,
                                           parse_formula_with_names, pretty_formula)
    try:
        formula, names = parse_formula_with_names(source)
        canonical = pretty_formula(formula, list(names))
        def skeleton(node):
            if isinstance(node, Eq):
                return "atom"
            if isinstance(node, Bot):
                return "bottom"
            if isinstance(node, (Forall, Exists)):
                return [type(node).__name__, skeleton(node.body)]
            if isinstance(node, (And, Or, Imp)):
                return [type(node).__name__, skeleton(node.left), skeleton(node.right)]
            raise BenchmarkAuditError("unknown native formula constructor")
        body = formula
        while isinstance(body, Forall):
            body = body.body
        return {"canonical": canonical, "closed": not names,
                "canonical_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
                "skeleton_sha256": digest(skeleton(body)), "skeleton": skeleton(body)}
    except (ValueError, TypeError, RecursionError) as error:
        raise BenchmarkAuditError(f"formula outside native audit profile: {error}") from None


class ExposureIndex:
    """Bounded facts with exact counts and capped location examples."""

    def __init__(self):
        self.features = {kind: {} for kind in
                         ("roots", "closed_targets", "states", "skeletons", "families",
                          "lineages", "names", "template_hashes")}
        self.counts = Counter()
        self.gaps = Counter()
        self.gap_examples = []
        self.unparsed_formulas = {}
        self.relations = set()

    def add(self, kind, key, location):
        bucket = self.features[kind]
        if key not in bucket:
            _require(sum(len(v) for v in self.features.values()) < MAX_FEATURES,
                     "exposure feature bound exceeded")
            bucket[key] = {"occurrences": 0, "examples": []}
        record = bucket[key]
        record["occurrences"] += 1
        if len(record["examples"]) < MAX_EXAMPLES and location not in record["examples"]:
            record["examples"].append(location)

    def gap(self, reason, location):
        self.gaps[reason] += 1
        if len(self.gap_examples) < 50:
            self.gap_examples.append({"reason": reason, "location": location})

    def formula(self, source, location, *, intermediate=False):
        self.counts["formula_observations"] += 1
        if type(source) is str and "?" in source and intermediate:
            # A metavariable is not a closed kernel formula. Its complete
            # rendered state is still present in the exact state inventory.
            self.counts["metavariable_target_observations"] += 1
            return
        try:
            features = formula_features(source)
        except BenchmarkAuditError as error:
            self.gap(str(error), location)
            if type(source) is str:
                key = hashlib.sha256(source.encode()).hexdigest()
                if key not in self.unparsed_formulas:
                    self.unparsed_formulas[key] = {"source_sha256": key,
                        "logical_count_signature": logical_count_signature(source),
                        "reason": str(error), "intermediate": intermediate,
                        "bytes": len(source.encode()), "example_location": location,
                        "occurrences": 0}
                self.unparsed_formulas[key]["occurrences"] += 1
            return
        if not features["closed"]:
            self.counts["open_target_observations"] += 1
            if not intermediate:
                self.gap("open_root_formula", location)
            return
        kind = "closed_targets" if intermediate else "roots"
        self.add(kind, features["canonical_sha256"], location)
        # Intermediate atomic fragments intentionally do not create template
        # conflicts: shared primitive vocabulary is not a whole-family match.
        if not intermediate:
            self.add("skeletons", features["skeleton_sha256"], location)
        self.counts["closed_target_observations" if intermediate else "root_observations"] += 1

    def goals(self, goals, location):
        _require(type(goals) is list and len(goals) <= 128
                 and all(type(g) is str and len(g.encode()) <= 65536 for g in goals),
                 "goal list escaped bounds")
        if goals:
            self.add("states", digest(goals), location)
        for i, rendered in enumerate(goals):
            _, marker, target = rendered.rpartition("⊢")
            if not marker and rendered.strip():
                self.counts["bare_diagnostic_target_observations"] += 1
                self.formula(rendered.strip(), f"{location}:{i}", intermediate=True)
            elif not target.strip():
                self.gap("goal_without_turnstile", location)
            else:
                self.formula(target.strip(), f"{location}:{i}", intermediate=True)

    def record(self, value, location, *, depth=0):
        """Read declared statement/state fields, not arbitrary prose or scripts."""
        _require(depth <= 64, "record nesting exceeds bound")
        if type(value) is list:
            for i, item in enumerate(value):
                if isinstance(item, (dict, list)):
                    self.record(item, f"{location}/{i}", depth=depth + 1)
            return
        if type(value) is not dict:
            return
        self.counts["objects"] += 1
        _require(self.counts["objects"] <= MAX_RECORDS * 8, "nested object bound exceeded")
        if "formula" in value and type(value["formula"]) is str:
            self.formula(value["formula"], location + "/formula")
        if "statement" in value and type(value["statement"]) is str:
            self.formula(value["statement"], location + "/statement")
        if "canonical" in value and type(value["canonical"]) is str:
            self.formula(value["canonical"], location + "/canonical")
        if type(value.get("theorem")) is str:
            if "formula" in value or "statement" in value or (
                    _IDENTIFIER.fullmatch(value["theorem"]) and value["theorem"] not in {"bot", "false"}):
                self.add("names", value["theorem"], location + "/theorem")
            else:
                self.formula(value["theorem"], location + "/theorem")
        for key, kind in (("family", "families"), ("lineage_sha256", "lineages"),
                          ("lineage", "lineages"), ("theorem_name", "names"),
                          ("template_sha256", "template_hashes")):
            if type(value.get(key)) is str:
                self.add(kind, value[key], location)
        identity = value.get("name", value.get("id", value.get("family")))
        if type(identity) is str:
            for key in ("parent_families", "dependencies", "dependency_ids", "equivalent_ids"):
                for parent in value.get(key, []) if type(value.get(key, [])) is list else []:
                    if type(parent) is str:
                        self.relations.add((identity, parent, key))
        consumed = set()
        for key in ("goals_before", "goals_after", "state"):
            if type(value.get(key)) is list and all(type(g) is str for g in value[key]):
                self.goals(value[key], location + "/" + key)
                consumed.add(key)
        if "goals_before" in consumed and type(value.get("state_sha256")) is str:
            _require(value["state_sha256"] == digest(value["goals_before"]),
                     "row state hash differs from its before-state bytes")
        if type(value.get("goals")) is list and value["goals"] and all(
                type(g) is str for g in value["goals"]):
            if all(_IDENTIFIER.fullmatch(g) for g in value["goals"]):
                for name in value["goals"]:
                    self.add("names", name, location + "/goals")
            else:
                self.goals(value["goals"], location + "/goals")
            consumed.add("goals")
        prompt = value.get("prompt")
        # Prompt-only preferences expose the whole state even without an
        # embedded transition. Extract the protocol's JSON state directly.
        if type(prompt) is str:
            matches = re.findall(r"<state>(.*?)</state>", prompt, re.DOTALL)
            if len(matches) != 1:
                self.gap("prompt_state_not_recognized", location)
            else:
                state = _decode(matches[0])
                if type(state) is not dict or "goals" not in state:
                    self.gap("prompt_state_not_recognized", location)
                else:
                    self.goals(state["goals"], location + "/prompt-state")
        for key, child in value.items():
            if key not in consumed and isinstance(child, (dict, list)):
                self.record(child, location + "/" + key, depth=depth + 1)

    def to_dict(self):
        return {"features": self.features, "counts": dict(self.counts),
                "parse_gaps": dict(self.gaps), "parse_gap_examples": self.gap_examples,
                "unparsed_formulas": list(self.unparsed_formulas.values()),
                "declared_relations": [list(r) for r in sorted(self.relations)]}


def build_exposure_index(specs, *, coverage_gaps):
    """Hash every listed file; parse byte-identical payloads only once.

    ``anchor_origin`` is an explicit caller description, not an authentication
    claim. A freshly measured SHA does not establish historical provenance.
    Files with an expected SHA are rejected on mismatch, never silently skipped.
    """
    _require(type(specs) is list and 0 < len(specs) <= MAX_FILES, "file inventory bound")
    _require(type(coverage_gaps) is list and all(type(g) is str for g in coverage_gaps),
             "coverage gaps must be explicitly enumerated")
    index = ExposureIndex()
    inventory, seen = [], {}
    total_bytes, total_records = 0, 0
    for ordinal, spec in enumerate(specs):
        _require(type(spec) is dict and {"path", "format", "role", "anchor_origin"} <= set(spec),
                 "incomplete source specification")
        _require(spec["format"] in ("json", "jsonl"), "unsupported source format")
        raw, identity = read_file(spec["path"], spec.get("expected_sha256"))
        total_bytes += len(raw)
        _require(total_bytes <= MAX_TOTAL_BYTES, "complete inventory bytes exceeded")
        file_id = f"source-{ordinal:04d}"
        record = {**identity, "source_id": file_id, "role": spec["role"],
                  "format": spec["format"], "anchor_origin": spec["anchor_origin"],
                  "raw_anchor_matched": spec.get("expected_sha256") is not None}
        identity_key = (identity["sha256"], spec["format"])
        if identity_key in seen:
            record["duplicate_payload_of"] = seen[identity_key]
            inventory.append(record)
            continue
        seen[identity_key] = file_id
        before_counts = index.counts.copy()
        before_gaps = sum(index.gaps.values())
        records = 0
        if spec["format"] == "jsonl":
            _require(not raw or raw.endswith(b"\n"), "unterminated JSONL record")
            for lineno, line in enumerate(raw.splitlines(), 1):
                _require(0 < len(line) <= MAX_ROW_BYTES, "blank or excessive JSONL row")
                item = _decode(line)
                _require(type(item) is dict, "JSONL row must be an object")
                records += 1
                total_records += 1
                _require(total_records <= MAX_RECORDS, "total record bound exceeded")
                index.record(item, f"{file_id}:{lineno}")
        else:
            item = _decode(raw)
            _require(type(item) in (dict, list), "JSON document must be structured")
            index.record(item, file_id)
            records = 1
        record.update({"records_parsed": records,
                       "observations": dict(index.counts - before_counts),
                       "parse_gap_observations": sum(index.gaps.values()) - before_gaps})
        inventory.append(record)
    return {"schema": SCHEMA, "source_inventory": inventory,
            "source_inventory_sha256": digest(inventory), "listed_bytes": total_bytes,
            "unique_payloads": len(seen), "unique_payload_records": total_records,
            "coverage_gaps": coverage_gaps, **index.to_dict(),
            "claims": {"listed_file_bytes_checked": True,
                       "all_historical_exposures_known": False,
                       "semantic_equivalence_complete": False,
                       "independent_authorship_verified": False,
                       "test_seal_granted": False, "research_claim_eligible": False}}


def audit_candidates(exposure, candidates, *, candidate_identity, reference_records=None,
                     reference_expected_counts=None):
    """Audit whole families; never keep selected clean-looking seeds of a hit.

    Candidate records need id/name, family, and statement. Optional explicit
    parent_families/parent_lineages/template_sha256 join whole-family checks.
    ``reference_records`` contains native before/after states, when available.
    Missing reference states are disclosed and prevent complete-state claims.
    """
    _require(type(candidates) is list and 0 < len(candidates) <= 1024, "candidate count bound")
    facts = exposure["features"]
    families = defaultdict(list)
    identifiers = set()
    relevant_signatures = set()
    for candidate in candidates:
        _require(type(candidate) is dict and type(candidate.get("family")) is str,
                 "candidate lacks family")
        identifier = candidate.get("id", candidate.get("name"))
        _require(type(identifier) is str and identifier not in identifiers,
                 "candidate identity is missing or duplicate")
        identifiers.add(identifier)
        features = formula_features(candidate.get("statement"))
        _require(features["closed"], "candidate root is open")
        relevant_signatures.add(tuple(logical_count_signature(features["canonical"])))
        hits = {}
        for kind in ("roots", "closed_targets"):
            match = facts[kind].get(features["canonical_sha256"])
            if match:
                hits[kind] = match
        skeleton = facts["skeletons"].get(features["skeleton_sha256"])
        if skeleton:
            hits["logical_skeleton_review_flag"] = skeleton
        for field, kind in (("family", "families"), ("template_sha256", "template_hashes")):
            match = facts[kind].get(candidate.get(field))
            if match:
                hits[kind] = match
        for field, kind in (("parent_families", "families"), ("parent_lineages", "lineages"),
                            ("dependency_ids", "names"), ("equivalent_ids", "names")):
            parent_matches = {parent: facts[kind][parent] for parent in candidate.get(field, [])
                              if parent in facts[kind]}
            if parent_matches:
                hits[field] = parent_matches
        families[candidate["family"]].append({"id": identifier,
            "statement": features["canonical"],
            "statement_sha256": features["canonical_sha256"],
            "skeleton_sha256": features["skeleton_sha256"], "matches": hits})
    reference_hits = defaultdict(list)
    primitive_correlations = defaultdict(list)
    reference_closed_targets = set()
    reference_covered = set()
    reference_steps = defaultdict(list)
    if reference_records is not None:
        _require(type(reference_records) is list, "reference records must be explicit")
        for row in reference_records:
            identifier = row.get("theorem_name", row.get("id", row.get("name")))
            _require(identifier in identifiers, "reference record belongs to unknown candidate")
            reference_covered.add(identifier)
            reference_steps[identifier].append(row)
            for field in ("goals_before", "goals_after"):
                for goal in row.get(field, []):
                    _, marker, target = goal.rpartition("⊢")
                    _require(bool(marker), "candidate goal lost turnstile")
                    if "?" in target:
                        continue
                    features = formula_features(target.strip())
                    if features["closed"]:
                        reference_closed_targets.add(features["canonical"])
                        relevant_signatures.add(tuple(logical_count_signature(features["canonical"])))
                        for kind in ("roots", "closed_targets"):
                            match = facts[kind].get(features["canonical_sha256"])
                            if match:
                                hit = {"kind": kind, "sha256": features["canonical_sha256"], "evidence": match}
                                # A target of bottom under different hypotheses
                                # is shared primitive vocabulary. It is not an
                                # identical theorem or policy state. Keep the
                                # correlation explicit; exact full states below
                                # still quarantine the entire family.
                                bucket = primitive_correlations if features["canonical"] == "⊥" else reference_hits
                                if hit not in bucket[identifier]:
                                    bucket[identifier].append(hit)
                state = row.get(field)
                if state:
                    sha = digest(state)
                    if sha in facts["states"]:
                        reference_hits[identifier].append({"kind": "states", "sha256": sha,
                                                          "evidence": facts["states"][sha]})
    complete_references = set()
    if reference_expected_counts is not None:
        _require(type(reference_expected_counts) is dict
                 and set(reference_expected_counts) == identifiers,
                 "reference count inventory differs from candidate inventory")
        for identifier, count in reference_expected_counts.items():
            _require(type(count) is int and 1 <= count <= 64, "reference decision bound")
            rows = reference_steps[identifier]
            _require(len(rows) == count and [r.get("step") for r in rows] == list(range(1, count + 1)),
                     "reference trace is incomplete or reordered")
            _require(rows[-1].get("goals_after") == []
                     and all(a.get("goals_after") == b.get("goals_before")
                             for a, b in zip(rows, rows[1:])),
                     "reference trace is not contiguous to original-goal completion")
            complete_references.add(identifier)
    results = []
    for family, goals in sorted(families.items()):
        exact = any(set(g["matches"]) - {"logical_skeleton_review_flag"} for g in goals)
        exact = exact or any(reference_hits[g["id"]] for g in goals)
        structural = any("logical_skeleton_review_flag" in g["matches"] for g in goals)
        results.append({"family": family, "goal_count": len(goals), "goals": goals,
            "reference_overlap": {g["id"]: reference_hits[g["id"]] for g in goals if reference_hits[g["id"]]},
            "shared_primitive_correlations": {g["id"]: primitive_correlations[g["id"]]
                                                for g in goals if primitive_correlations[g["id"]]},
            "all_reference_goals_observed": all(g["id"] in reference_covered for g in goals),
            "complete_reference_state_traces": all(g["id"] in complete_references for g in goals),
            "status": "quarantine-exact-exposure" if exact else
                      "quarantine-template-review" if structural else "no-detected-overlap-in-declared-sources",
            "whole_family_quarantined": bool(exact or structural)})
    unparsed = exposure.get("unparsed_formulas", [])
    unresolved = [r for r in unparsed if tuple(r["logical_count_signature"]) in relevant_signatures]
    blocking_gaps = []
    if unresolved:
        blocking_gaps.append("unparsed_exposure_cannot_be_excluded_by_necessary_logical_counts")
    if sum(r["occurrences"] for r in unparsed) != sum(exposure["parse_gaps"].values()):
        blocking_gaps.append("exposure_parse_gap_without_formula_signature")
    if complete_references != identifiers:
        blocking_gaps.append("candidate_complete_reference_state_inventory_missing")
    body = {"schema": SCHEMA, "candidate_identity": candidate_identity,
            "source_inventory": exposure["source_inventory"],
            "exposure_inventory_sha256": exposure["source_inventory_sha256"],
            "candidate_count": len(candidates), "family_count": len(families),
            "families": results, "reference_state_coverage_complete": complete_references == identifiers,
            "coverage_gaps": exposure["coverage_gaps"], "coverage_limitations": exposure["coverage_gaps"],
            "blocking_coverage_gaps": blocking_gaps, "parse_gaps": exposure["parse_gaps"],
            "out_of_profile_exposure": {"unparsed_unique_formulas": len(unparsed),
                "excluded_by_necessary_logical_counts": len(unparsed) - len(unresolved),
                "unparsed_formula_inventory": unparsed,
                "potentially_matching_unparsed": unresolved,
                "canonical_closed_reference_targets": sorted(reference_closed_targets),
                "comparison_signatures": [list(s) for s in sorted(relevant_signatures)]},
            "limits": {"alpha_canonicalization_only": True,
                       "skeleton_erases_atoms_and_outer_universal_parameters": True,
                       "rendered_states_are_exact_not_alpha_equivalence": True,
                       "bottom_under_different_context_is_shared_primitive_only": True,
                       "complete_semantic_equivalence_checked": False,
                       "unlisted_exposure_sources_not_checked": True,
                       "human_lineage_decision_still_required": True},
            "claims": {"sealed_benchmark": False, "training_admission_granted": False,
                       "independent_authorship_verified": False, "research_claim_eligible": False}}
    return {**body, "audit_sha256": digest(body)}


def validate_audit_record(record):
    """Validate bounded receipt metadata and rederive every admission summary.

    A self-consistent digest is not authentication. The caller MUST first pin
    the raw receipt externally and check its exact input file identities.
    This function does not reread historical corpora, replay proofs, certify
    authorship, or turn incomplete semantic checks into a test seal.
    """
    _require(type(record) is dict and len(canonical_bytes(record)) <= 16 * 1024**2,
             "audit record exceeds metadata bound")
    required = {"schema", "candidate_identity", "source_inventory", "exposure_inventory_sha256",
        "candidate_count", "family_count", "families", "reference_state_coverage_complete",
        "coverage_gaps", "coverage_limitations", "blocking_coverage_gaps", "parse_gaps",
        "out_of_profile_exposure", "limits", "claims", "audit_sha256"}
    _require(set(record) == required and record["schema"] == SCHEMA, "audit schema changed")
    _require(record["audit_sha256"] == digest({k: v for k, v in record.items() if k != "audit_sha256"}),
             "audit canonical digest changed")
    inventory = record["source_inventory"]
    _require(type(inventory) is list and 0 < len(inventory) <= MAX_FILES
             and digest(inventory) == record["exposure_inventory_sha256"], "exposure file inventory changed")
    sources = set()
    source_by_id = {}
    for item in inventory:
        _require(type(item) is dict and type(item.get("source_id")) is str
                 and item["source_id"] not in sources and type(item.get("path")) is str
                 and Path(item["path"]).is_absolute() and type(item.get("bytes")) is int
                 and 0 <= item["bytes"] <= MAX_FILE_BYTES and _SHA.fullmatch(item.get("sha256", "")),
                 "invalid source identity")
        if "duplicate_payload_of" in item:
            _require(item["duplicate_payload_of"] in sources, "duplicate source refers forward or nowhere")
            other = source_by_id[item["duplicate_payload_of"]]
            _require((item["sha256"], item["bytes"], item["format"])
                     == (other["sha256"], other["bytes"], other["format"]),
                     "duplicate payload bytes/format differ")
        sources.add(item["source_id"])
        source_by_id[item["source_id"]] = item
    _require(sum(i["bytes"] for i in inventory) <= MAX_TOTAL_BYTES, "source byte total exceeds bound")
    claims = {"sealed_benchmark": False, "training_admission_granted": False,
              "independent_authorship_verified": False, "research_claim_eligible": False}
    _require(record["claims"] == claims, "audit promoted a forbidden claim")
    expected_limits = {"alpha_canonicalization_only": True,
        "skeleton_erases_atoms_and_outer_universal_parameters": True,
        "rendered_states_are_exact_not_alpha_equivalence": True,
        "bottom_under_different_context_is_shared_primitive_only": True,
        "complete_semantic_equivalence_checked": False,
        "unlisted_exposure_sources_not_checked": True, "human_lineage_decision_still_required": True}
    _require(record["limits"] == expected_limits, "audit claim limits changed")
    _require(record["coverage_gaps"] == record["coverage_limitations"], "coverage limitations diverged")
    _require(type(record["candidate_identity"]) is dict, "candidate identity missing")
    families = record["families"]
    _require(type(families) is list and len(families) == record["family_count"] <= 128,
             "family inventory changed")
    identifiers, family_names = set(), set()
    comparison_signatures = set()
    complete = True
    for family in families:
        _require(type(family.get("family")) is str and family["family"] not in family_names,
                 "duplicate family identity")
        family_names.add(family["family"])
        goals = family["goals"]
        _require(type(goals) is list and len(goals) == family["goal_count"] > 0,
                 "family goal inventory changed")
        ids = set()
        for goal in goals:
            _require(type(goal.get("id")) is str and goal["id"] not in identifiers,
                     "duplicate goal identity")
            identifiers.add(goal["id"])
            ids.add(goal["id"])
            features = formula_features(goal["statement"])
            _require(features["closed"] and features["canonical"] == goal["statement"]
                     and features["canonical_sha256"] == goal["statement_sha256"]
                     and features["skeleton_sha256"] == goal["skeleton_sha256"],
                     "goal canonical identity changed")
            comparison_signatures.add(tuple(logical_count_signature(goal["statement"])))
            _require(type(goal["matches"]) is dict, "goal match record changed")
        _require(set(family["reference_overlap"]) <= ids
                 and set(family["shared_primitive_correlations"]) <= ids,
                 "reference overlap belongs to a different family")
        exact = any(set(g["matches"]) - {"logical_skeleton_review_flag"} for g in goals)
        exact = exact or bool(family["reference_overlap"])
        structural = any("logical_skeleton_review_flag" in g["matches"] for g in goals)
        expected = "quarantine-exact-exposure" if exact else "quarantine-template-review" if structural else "no-detected-overlap-in-declared-sources"
        _require(family["status"] == expected and family["whole_family_quarantined"] is bool(exact or structural),
                 "family status does not follow its exposure evidence")
        _require(type(family["complete_reference_state_traces"]) is bool, "reference coverage type changed")
        complete = complete and family["complete_reference_state_traces"]
    _require(len(identifiers) == record["candidate_count"] <= 1024
             and record["reference_state_coverage_complete"] is complete, "candidate/reference coverage changed")
    out = record["out_of_profile_exposure"]
    _require(type(out) is dict and type(out["potentially_matching_unparsed"]) is list
             and out["unparsed_unique_formulas"] == out["excluded_by_necessary_logical_counts"]
                 + len(out["potentially_matching_unparsed"]), "out-of-profile coverage changed")
    for source in out["canonical_closed_reference_targets"]:
        features = formula_features(source)
        _require(features["closed"] and features["canonical"] == source,
                 "closed reference target changed")
        comparison_signatures.add(tuple(logical_count_signature(source)))
    _require(out["comparison_signatures"] == [list(s) for s in sorted(comparison_signatures)],
             "negative filter comparison signatures changed")
    unparsed = out["unparsed_formula_inventory"]
    _require(type(unparsed) is list and len(unparsed) == out["unparsed_unique_formulas"],
             "unparsed exposure inventory changed")
    unresolved = [r for r in unparsed if tuple(r["logical_count_signature"]) in comparison_signatures]
    _require(unresolved == out["potentially_matching_unparsed"], "negative filter outcome changed")
    _require(type(record["parse_gaps"]) is dict
             and all(type(k) is str and type(v) is int and v >= 0 for k, v in record["parse_gaps"].items()),
             "invalid parser gap counts")
    expected_gaps = []
    if out["potentially_matching_unparsed"]:
        expected_gaps.append("unparsed_exposure_cannot_be_excluded_by_necessary_logical_counts")
    if sum(r["occurrences"] for r in unparsed) != sum(record["parse_gaps"].values()):
        expected_gaps.append("exposure_parse_gap_without_formula_signature")
    if not complete:
        expected_gaps.append("candidate_complete_reference_state_inventory_missing")
    _require(record["blocking_coverage_gaps"] == expected_gaps, "blocking coverage status changed")
    return record


def audit_summary(record, *, goal_ids=None):
    """Pure fail-closed summary for a selected cohort; no review override."""
    validate_audit_record(record)
    all_ids = {g["id"] for f in record["families"] for g in f["goals"]}
    selected = all_ids if goal_ids is None else set(goal_ids)
    _require(bool(selected) and selected <= all_ids, "selected cohort contains unknown goals")
    families = [f for f in record["families"] if selected & {g["id"] for g in f["goals"]}]
    exact = [f["family"] for f in families if f["status"] == "quarantine-exact-exposure"]
    templates = [f["family"] for f in families if any(
        "logical_skeleton_review_flag" in g["matches"] for g in f["goals"])]
    blocked = bool(exact or templates or record["blocking_coverage_gaps"])
    return {"status": "blocked" if blocked else "no-detected-overlap-in-declared-sources",
            "selected_goal_count": len(selected), "selected_family_count": len(families),
            "audited_file_sha256": sorted({r["sha256"] for r in record["source_inventory"]}),
            "blocking_exact_overlap_families": exact,
            "template_review_flags": templates,
            "blocking_coverage_gaps": record["blocking_coverage_gaps"],
            "coverage_limitations": record["coverage_limitations"],
            "human_review_required": True, "sealed_benchmark": False,
            "research_claim_eligible": False, "audit_sha256": record["audit_sha256"]}
