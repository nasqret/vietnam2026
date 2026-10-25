#!/usr/bin/env python3
"""Render an actual study06 audit to a new local candidate; never publish it."""
from __future__ import annotations

import argparse
from hashlib import sha256
from html import escape, unescape
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
MAX_BYTES = 524288
COUNTERS = ("actual_model_calls", "forward_passes", "generated_token_slots")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def descriptor(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), "Input must be a local workspace file.")
    require(path.is_file() and path.stat().st_size <= MAX_BYTES, "Missing or oversized input.")
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
            "sha256": sha256(raw).hexdigest()}


def pinned(item):
    path = ROOT / item["path"]
    require(descriptor(path) == item, "Input changed: " + item["path"])
    return path.read_bytes()


def decoded(item):
    return json.loads(pinned(item))


def section_parts(raw):
    page = raw.decode("utf-8")
    marker = '    <section id="study-results"'
    require(page.count(marker) == 1, "Expected one results section.")
    start = page.index(marker)
    end = page.index("    </section>", start) + len("    </section>")
    section = page[start:end]
    require(section.count("<section") == 1, "Results section must not contain nested sections.")
    return tuple(part.encode("utf-8") for part in (page[:start], section, page[end:]))


def prepared_inputs():
    preparation = json.loads((HERE / "PREPARED.json").read_bytes())
    for item in preparation["inputs"].values():
        pinned(item)
    require(len(preparation["protected_files"]) == 21, "Protected file count changed.")
    for item in preparation["protected_files"].values():
        pinned(item)
    original = pinned(preparation["inputs"]["base_page"])
    prefix, section, suffix = section_parts(original)
    require({"prefix_sha256": sha256(prefix).hexdigest(),
             "section_sha256": sha256(section).hexdigest(),
             "suffix_sha256": sha256(suffix).hexdigest()} == preparation["section_boundary"],
            "Section boundary changed.")
    study = decoded(preparation["inputs"]["study"])
    require(study["study_id"] == "paired-size-20260905-v6"
            and study["scope"] == "full16" and study["wall_profile"] == "fixed-wall-30-v1"
            and study["comparison"] == "fixed_native_work_guarded", "Study scope changed.")
    return preparation, study, original, prefix, suffix


def receipt_matches(receipt, audit_pin, audit):
    item = receipt.get("audit", receipt.get("result"))
    require(isinstance(item, dict)
            and item.get("bytes") == audit_pin["bytes"]
            and item.get("sha256") == audit_pin["sha256"], "Actual receipt must pin this audit.")
    require(str(receipt.get("schema", "")).startswith("hydra-paired-"), "Unexpected actual receipt schema.")
    actual_exit = receipt.get("actual_tool_exit_code", receipt.get("actual_exit_code"))
    require(type(actual_exit) is int and actual_exit == (0 if audit["status"] == "complete" else 2),
            "Actual audit exit does not match its recorded status.")
    require(isinstance(receipt.get("completion_chunk"), str) and receipt["completion_chunk"],
            "Root-observed actual completion chunk is required.")


def summarize(arm):
    cases = arm["cases"]
    clean = [c for c in cases if c["status"] in {"proved", "unknown"}]
    positives = [c for c in clean if c["category"] == "prospective_positive"]
    controls = [c for c in clean if c["category"] == "negative_control"]
    proved = [c for c in positives if c["kernel_checked_and_replayed"] is True]
    require(arm["positive_case_count"] == 12 and arm["control_case_count"] == 4,
            "Unexpected case population.")
    require(arm["positive_proofs"] == len(proved)
            and arm["control_checked_proofs"] == sum(c["kernel_checked_and_replayed"] for c in controls),
            "Proof counts disagree with case evidence.")
    require(len(cases) + len(arm["not_run"]) == 16, "Case coverage is incomplete in the audit.")
    measured = [c for c in cases if c.get("counters") is not None and c["counters"]["complete"] is True]
    for c in measured:
        require(all(type(c["counters"][key]) is int and c["counters"][key] >= 0 for key in COUNTERS),
                "Invalid measured counter.")
    work = {key: sum(c["counters"][key] for c in measured) for key in COUNTERS} if measured else None
    if arm["counter_accounting_complete"]:
        require(len(measured) == 16, "A complete counter total requires all cases.")
    return {
        "arm": arm["arm"], "terminal": arm["terminal"],
        "execution_complete": arm["execution_complete"],
        "counter_accounting_complete": arm["counter_accounting_complete"],
        "attempted_cases": len(cases), "clean_cases": len(clean),
        "unrun_cases": len(arm["not_run"]), "clean_positive_cases": len(positives),
        "positive_proofs": len(proved), "positive_case_count": 12,
        "clean_controls": len(controls),
        "controls_unknown": sum(c["status"] == "unknown" for c in controls),
        "control_checked_proofs": arm["control_checked_proofs"], "control_case_count": 4,
        "model_work": work, "measured_counter_cases": len(measured),
        "model_work_scope": "arm_total" if arm["counter_accounting_complete"] else "measured_case_subtotal",
        "checked_positive_cases": [{"case_id": c["case_id"], "winning_steps": c["winning_steps"]} for c in proved],
        "case_statuses": [{"case_id": c["case_id"], "category": c["category"], "status": c["status"],
                           "kernel_checked_and_replayed": c["kernel_checked_and_replayed"]} for c in cases],
    }


def snapshot(preparation, study, audit_pin, audit, receipt_pin):
    require(audit["schema"] == "hydra-p6-p10-paired-comparison-v1"
            and audit["study_sha256"] == preparation["inputs"]["study"]["sha256"], "Audit study changed.")
    for key in ("scope", "comparison", "wall_profile", "holdout_sha256"):
        require(audit[key] == study[key], "Audit scope differs: " + key)
    require([a["arm"] for a in audit["arms"]] == ["fresh_4b"], "Only the selected 4B arm is admitted here.")
    require(audit["missing_arms"] == ["fresh_1_7b", "historical_1_7b", "symbolic"],
            "Unselected auditor roles changed.")
    require(audit["status"] == "incomplete", "The declared four-role audit must retain its raw status.")
    historical = decoded(preparation["inputs"]["source03_audit"])
    reference = decoded(preparation["inputs"]["source05_audit"])
    symbolic = summarize(next(a for a in historical["arms"] if a["arm"] == "symbolic"))
    fresh17 = summarize(reference["arms"][0])
    require(fresh17["arm"] == "fresh_1_7b" and fresh17["clean_cases"] == 6
            and fresh17["positive_proofs"] == 0 and fresh17["model_work"] == dict(zip(COUNTERS, (46, 222, 888))),
            "Historical source05 reference differs.")
    require(symbolic["execution_complete"] is True and symbolic["positive_proofs"] == 1
            and symbolic["controls_unknown"] == 4, "Historical source03 reference differs.")
    token = decoded(preparation["inputs"]["tokenizer_audit"])
    train, val = token["splits"]["train"], token["splits"]["val"]
    require(token["completed"] is True and (train["compatible_rows"], train["rows"],
            val["compatible_rows"], val["rows"]) == (2045, 2047, 432, 432), "Tokenizer result changed.")
    return {
        "schema": "hydra-website-model-tests-v3", "snapshot_date": "2026-09-06",
        "study_id": study["study_id"], "source": "source07", "scope": study["scope"],
        "wall_profile": study["wall_profile"], "features": study["features"],
        "selected_arms": ["fresh_4b"], "unselected_declared_roles": audit["missing_arms"],
        "raw_audit_status": audit["status"], "selected_result": summarize(audit["arms"][0]),
        "separate_references": [{"source": "source05", "study": "paired-size-study-04", "result": fresh17},
                                {"source": "source03", "study": "paired-size-study-02", "result": symbolic}],
        "tokenizer_compatibility": {"training_reachable": 2045, "training_rows": 2047,
            "validation_reachable": 432, "validation_rows": 432,
            "masked_training_targets": 1, "over_limit_training_targets": 1,
            "long_target_tokens_with_eos": 70, "generation_token_limit": 64,
            "model_or_dataset_modified": False, "proof_quality_measurement": False},
        "gallery_proofs": 14, "matched_model_size_comparison": False,
        "model_quality_improvement_established": False, "changes_local_model_defaults": False,
        "evidence": {**{key: value for key, value in preparation["inputs"].items()
                        if key not in {"base_page", "prior_preparation"}},
                     "selected_audit": audit_pin, "selected_audit_actual_completion": receipt_pin},
    }


def render(value):
    selected = value["selected_result"]
    terminal = selected["terminal"]
    full = selected["execution_complete"]
    proofs = selected["positive_proofs"]
    badge = "4B EVALUATION COMPLETE" if full else "4B EVALUATION INCOMPLETE"
    if selected["control_checked_proofs"]:
        badge = "CONTROL PROOF REQUIRES REVIEW"
    if full:
        intro = f"Fresh 4B completed the 16-case evaluation and proved {proofs} of 12 positive cases with independent kernel replay."
    else:
        intro = (f"Fresh 4B completed {selected['clean_cases']} clean searches and produced {proofs} checked positive proofs. "
                 f"The allocation ended {terminal['state']}; {selected['unrun_cases']} cases were not run.")
    if selected["control_checked_proofs"]:
        intro += f" It also proved {selected['control_checked_proofs']} negative controls; these outcomes require review."
    detail = lambda text: '<span class="study-row-detail">' + escape(str(text)) + '</span>'
    proof_cell = (f"{proofs} / 12" + detail("Independently checked")) if full else (
        f"{proofs} from {selected['clean_positive_cases']} clean cases" + detail("Full arm incomplete"))
    control_cell = (f"{selected['controls_unknown']} / 4" if selected["clean_controls"] else "Not run")
    if not full and selected["clean_controls"]:
        control_cell += detail(f"{selected['clean_controls']} clean control cases")
    execution = ("Completed" if full else "Incomplete") + detail(f"{selected['clean_cases']} / 16 clean cases")
    execution += detail(f"Job {terminal['job_id']} · {terminal['state']} · exit {terminal['exit_code']}:{terminal['exit_signal']}")
    work = selected["model_work"]
    if work is None:
        call_cell, work_note = "Not available", "Model-work counters are unavailable."
    else:
        scope = "Arm total" if selected["counter_accounting_complete"] else f"Subtotal: {selected['measured_counter_cases']} measured cases"
        call_cell = str(work["actual_model_calls"]) + detail(scope)
        work_note = (f"{scope}: {work['actual_model_calls']} model calls, {work['forward_passes']} forward passes "
                     f"and {work['generated_token_slots']} generated token slots.")
    row = ('<tr><th scope="row">Fresh 4B' + detail("Saved adapter · source07") + '</th><td>' + execution +
           '</td><td>' + proof_cell + '</td><td>' + control_cell + '</td><td>' + call_cell +
           '</td><td>' + escape(str(terminal["elapsed_seconds"])) + ' s</td></tr>')
    checked_note = ""
    if selected["checked_positive_cases"]:
        names = [c["case_id"].removeprefix("holdout_").replace("_", " ") for c in selected["checked_positive_cases"]]
        model_wins = sum((c["winning_steps"] or {}).get("model", 0) > 0 for c in selected["checked_positive_cases"])
        checked_note = '<p class="quiet-note"><strong>Checked proofs:</strong> ' + escape("; ".join(names)) + ". "
        checked_note += escape(f"{model_wins} winning scripts contained a model-origin step.") + '</p>\n'
    embedded = escape(json.dumps(value, indent=2, ensure_ascii=False))
    return f'''    <section id="study-results" class="panel study-results" aria-labelledby="study-results-title">
      <div class="study-heading"><div><p class="eyebrow">RECORDED TESTS · SEPARATE FROM THE GALLERY</p><h2 id="study-results-title">Measured model results</h2></div><span class="badge neutral">{escape(badge)}</span></div>
      <p class="study-intro">{escape(intro)}</p>
      <div class="study-table-wrap" role="region" aria-label="Fresh 4B evaluation results" tabindex="0">
        <table>
          <caption>Snapshot 2026-09-06 · source07 · 12 positive cases and 4 negative controls</caption>
          <thead><tr><th scope="col">Search arm</th><th scope="col">Execution</th><th scope="col">Positive proofs</th><th scope="col">Controls unknown</th><th scope="col">Model calls</th><th scope="col">Scheduler elapsed</th></tr></thead>
          <tbody>{row}</tbody>
        </table>
      </div>
      {checked_note}<p class="study-scope"><strong>Scope:</strong> 30 seconds of search per case, with common native work ceilings. This run tests native heuristics plus primitive model guidance. Vampire and other external advisers, library retrieval, structured planning and the learned ranker are disabled. Only fresh 4B was selected on source07.</p>
      <p class="quiet-note">{escape(work_note)} Unknown means no proof was found within the limits. Accepted steps on an open branch do not count as completed proofs.</p>
      <p class="quiet-note"><strong>Earlier references:</strong> Fresh 1.7B on source05 completed six clean searches, all unknown, before an infrastructure failure left nine cases unrun; those six cases used 46 calls, 222 forward passes and 888 generated token slots. Native heuristics on source03 proved 1/12 positives and left all four controls unknown. These separate runs do not establish a matched model-size comparison.</p>
      <p class="quiet-note"><strong>Training compatibility:</strong> A tokenizer-only check found 2,045/2,047 training targets and 432/432 validation targets reachable under the current decoder. One training target was masked; another required 70 tokens against the 64-token limit. This check did not change the dataset or weights.</p>
      <details class="study-evidence" id="study-evidence">
        <summary>Inspect this snapshot’s evidence and source hashes</summary>
        <p class="quiet-note">The raw four-role audit retains its incomplete status because the other three roles were not selected. The selected 4B arm’s actual status appears above. The 14 gallery proofs and local model defaults are separate from these remote tests.</p>
        <pre id="study-evidence-json">{embedded}</pre>
      </details>
    </section>'''.encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-inputs", action="store_true")
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--audit-sha256")
    parser.add_argument("--actual-receipt", type=Path)
    parser.add_argument("--actual-receipt-sha256")
    parser.add_argument("--render-name", default="render-01")
    args = parser.parse_args()
    preparation, study, before, prefix, suffix = prepared_inputs()
    if args.check_inputs:
        require(not any((args.audit, args.audit_sha256, args.actual_receipt, args.actual_receipt_sha256)),
                "Static input checking must not contain result arguments.")
        print(json.dumps({"status": "static_inputs_verified", "protected_files": 21,
                          "gallery_proofs": 14, "candidate_created": False, "live_write": False}))
        return
    require(all((args.audit, args.audit_sha256, args.actual_receipt, args.actual_receipt_sha256)),
            "Genuine pinned audit and actual completion receipt are required.")
    audit_pin, receipt_pin = descriptor(args.audit), descriptor(args.actual_receipt)
    require(audit_pin["sha256"] == args.audit_sha256 and receipt_pin["sha256"] == args.actual_receipt_sha256,
            "Supplied result pins differ.")
    audit, receipt = decoded(audit_pin), decoded(receipt_pin)
    receipt_matches(receipt, audit_pin, audit)
    value = snapshot(preparation, study, audit_pin, audit, receipt_pin)
    section = render(value)
    after = prefix + section + suffix
    require(len(after) <= MAX_BYTES, "Rendered page exceeds size limit.")
    actual_prefix, actual_section, actual_suffix = section_parts(after)
    require(actual_prefix == prefix and actual_suffix == suffix and actual_section == section,
            "Candidate changed bytes outside the results section.")
    encoded = after.decode().split('<pre id="study-evidence-json">', 1)[1].split('</pre>', 1)[0]
    require(json.loads(unescape(encoded)) == value, "Embedded snapshot differs.")
    # Recheck every immutable input immediately before writing an exclusive candidate directory.
    prepared_inputs()
    pinned(audit_pin)
    pinned(receipt_pin)
    require(re.fullmatch(r"render-[0-9]{2}", args.render_name), "Use a numbered local render directory.")
    destination = HERE / args.render_name
    destination.mkdir(exist_ok=False)
    for name, raw in (("index.before.html", before), ("index.after.html", after),
                      ("snapshot.json", (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode())):
        with (destination / name).open("xb") as stream:
            stream.write(raw)
    handoff = {"schema": "hydra-study06-results-candidate-v1", "status": "candidate_only",
        "renderer": descriptor(Path(__file__)), "preparation": descriptor(HERE / "PREPARED.json"),
        "audit": audit_pin, "actual_audit_receipt": receipt_pin,
        "outputs": {name: descriptor(destination / name) for name in ("index.before.html", "index.after.html", "snapshot.json")},
        "only_changed_section": "study-results", "protected_files_unchanged": 21,
        "gallery_proofs_unchanged": 14, "live_write": False, "http_or_visual_verification": False,
        "model_or_native_execution": False, "network_operations": 0}
    with (destination / "HANDOFF.json").open("x", encoding="utf-8") as stream:
        json.dump(handoff, stream, indent=2)
        stream.write("\n")
    print(json.dumps(handoff))


if __name__ == "__main__":
    main()
