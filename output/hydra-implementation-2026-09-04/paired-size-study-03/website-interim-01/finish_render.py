"""Finish the evidence-backed status section; change no runtime or gallery files."""
from pathlib import Path
import hashlib
import html
import json
import re

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
BASE = ROOT / "output/hydra-implementation-2026-09-04"
INDEX = ROOT / "hydra-playground/index.html"


def pin(path):
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def put(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
    path.chmod(0o444)


before = INDEX.read_bytes()
assert before == (OUT / "index.before.html").read_bytes()
assert hashlib.sha256(before).hexdigest() == "be5ac90c9f630804f146a1844184a04aaf2a7bf53687905754ef6603f80cca21"
assert not (OUT / "index.after.html").exists()
prior = json.loads((BASE / "paired-size-study-02/website-interim-03/HANDOFF.json").read_text())
for name, expected in prior["protected_file_pins"].items():
    assert pin(ROOT / name) == expected
snapshot = json.loads((OUT / "snapshot.json").read_text())
assert snapshot["arms"][-1]["job_id"] == "21982562"
assert snapshot["arms"][-1]["completed_searches"] == 3
assert snapshot["matched_four_arm_comparison"] is False
text = before.decode()
start = text.index('    <section id="study-results"')
end = text.index("    </section>", start) + len("    </section>")
section = text[start:end]


def replace(pattern, value):
    global section
    section, count = re.subn(pattern, lambda _: value, section, flags=re.S)
    assert count == 1, pattern


section = section.replace("A FIXED STUDY · SEPARATE FROM THE GALLERY", "RECORDED TESTS · SEPARATE FROM THE GALLERY")
section = section.replace("Measured model comparison", "Measured model results")
section = section.replace("PARTIAL RESULTS", "INCOMPLETE EVALUATION")
section = section.replace('aria-label="Partial model comparison"', 'aria-label="Recorded model results from separate source versions"')
replace(r'<p class="study-intro">.*?</p>', '<p class="study-intro">Fresh 4B reloaded its saved weights and completed three searches; none produced a full proof. A child-process monitor failure interrupted the fourth case, leaving 12 cases unrun. The earlier 1.7B runs were also incomplete. These results do not establish a model-quality improvement.</p>')
replace(r"<caption>.*?</caption>", "<caption>Snapshot 2026-09-05 · 12 positive cases and 4 negative controls requested · earlier arms use source03; 4B uses source04</caption>")
replace(r"<tbody>.*?</tbody>", '''<tbody>
            <tr><th scope="row">Symbolic baseline<span class="study-row-detail">Native heuristics · source03</span></th><td>Completed · 16/16 cases<span class="study-row-detail">Job 21978966 · exit 0:0</span></td><td>1 / 12<span class="study-row-detail">Independently checked</span></td><td>4 / 4</td><td>0</td><td>199 s</td></tr>
            <tr><th scope="row">Historical 1.7B<span class="study-row-detail">Saved adapter · Torch · source03</span></th><td>Stopped before inference<span class="study-row-detail">Job 21979201 · exit 2:0 · 14 cases not run</span></td><td class="study-pending">Not evaluated</td><td class="study-pending">Not evaluated</td><td class="study-pending">No inference recorded</td><td>174 s</td></tr>
            <tr><th scope="row">Fresh 1.7B<span class="study-row-detail">source03</span></th><td>Loaded · worker unknown<span class="study-row-detail">Monitor failed · 15 cases not run</span><span class="study-row-detail">Job 21980166 · exit 2:0</span></td><td class="study-pending">Not evaluated<span class="study-row-detail">Full arm</span></td><td class="study-pending">Not run</td><td>5 recorded<span class="study-row-detail">One worker; full arm total unavailable</span></td><td>44 s</td></tr>
            <tr><th scope="row">Fresh 4B<span class="study-row-detail">Saved reload checked · source04</span></th><td>3 clean searches · unknown<span class="study-row-detail">Fourth case interrupted · 12 cases not run</span><span class="study-row-detail">Job 21982562 · exit 2:0</span></td><td>0 from 3 completed<span class="study-row-detail">Full arm not evaluated</span></td><td class="study-pending">Not run<span class="study-row-detail">All 4 controls</span></td><td>14 recorded<span class="study-row-detail">Three clean cases only</span></td><td>118 s</td></tr>
          </tbody>''')
replace(r'<p class="study-scope">.*?</p>', '<p class="study-scope"><strong>Scope:</strong> <code>fixed-wall-30-v1</code> · 30-second search limit per case · common native work ceilings. External advisers, checked-library retrieval, structured planning and the learned ranker are disabled. The 4B controller includes a monitor correction, so this is not a fully matched four-arm comparison.</p>')
replace(r'(?m)^      <p class="quiet-note">.*?</p>', '      <p class="quiet-note">Missing measurements are not zeros. Unknown means no proof was found within the bounds; it is not a refutation. Each completed 4B search reached the native state and tactic-attempt ceilings. Its 14 calls, 106 forward passes and 424 generated token slots are a subtotal for those three cases. Accepted model steps on open branches are not completed proofs. The 14 gallery proofs and local model defaults remain separate.</p>')
replace(r'(?m)^        <p class="quiet-note">.*?</p>', '        <p class="quiet-note">The source03 and source04 audits both report incomplete results and are preserved separately. The CPU prerequisite passed, and the corrected leader-exit handling worked in all three completed 4B cases; a different child-accounting failure stopped the run. No GPU retry or retraining was performed. This is a recorded snapshot, not a live job monitor.</p>')
replace(r'<pre id="study-evidence-json">.*?</pre>', '<pre id="study-evidence-json">' + html.escape(json.dumps(snapshot, indent=2)) + '</pre>')
after_text = text[:start] + section + text[end:]
after = after_text.encode()
# Character offsets stay in decoded text; byte checks use encoded prefixes.
assert after.startswith(text[:start].encode()) and after.endswith(text[end:].encode())
assert len(after) < 65536
assert after_text.count('id="study-results"') == 1
with (OUT / "index.after.html").open("xb") as stream:
    stream.write(after)
(OUT / "index.after.html").chmod(0o444)
assert INDEX.read_bytes() == before
INDEX.write_bytes(after)
for name, expected in prior["protected_file_pins"].items():
    assert pin(ROOT / name) == expected
record = {"schema": "hydra-website-model-results-update-v2",
          "changed_live_files": ["hydra-playground/index.html"],
          "changed_section": "study-results only", "index_before": pin(OUT / "index.before.html"),
          "index_after": pin(INDEX), "snapshot": pin(OUT / "snapshot.json"),
          "protected_file_pins": prior["protected_file_pins"], "protected_files_unchanged": True,
          "runtime_or_default_changed": False, "gallery_changed": False,
          "frozen_bundle_changed": False, "source_versions_pooled": False,
          "http_verification_pending": True, "visual_verification_performed": False}
put(OUT / "HANDOFF.json", record)
print(json.dumps({key: record[key] for key in ("index_after", "snapshot", "changed_section")}))
