"""Produce a reviewable UI-only patch without changing the live application."""
from pathlib import Path
import difflib
import hashlib
import json

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
LIVE = ROOT / "hydra-playground/app.js"
raw = LIVE.read_bytes()
original = raw.decode("utf-8")
anchor = "  function renderProfile() {\n"
helper = '''  function repeatedWorkNote(search) {
    const notes=[];
    const model=search?.model_repeated_prompts_skipped;
    const vampire=search?.vampire_advice_cache?.cache_hits;
    if(Number.isSafeInteger(model) && model>0)notes.push(`Skipped ${model} repeated model prompt${model===1?"":"s"} before decoding.`);
    if(Number.isSafeInteger(vampire) && vampire>0)notes.push(`Skipped ${vampire} repeated Vampire request${vampire===1?"":"s"} after unsuccessful attempts (no new solver launches).`);
    return notes.join(" ");
  }

'''
caption_anchor = '    ui["result-caption"].textContent=caption;\n'
caption_replacement = ('    const repeated=searched?repeatedWorkNote(result.search):"";\n'
                       '    if(repeated)caption+=" "+repeated;\n' + caption_anchor)
progress_anchor = '      ui["progress-detail"].textContent=parts.join(" · ");\n'
progress_replacement = ('      const repeated=repeatedWorkNote(progress);\n'
                        '      if(repeated)parts.push(repeated);\n' + progress_anchor)
assert original.count(anchor) == original.count(caption_anchor) == original.count(progress_anchor) == 1
assert "repeatedWorkNote" not in original
candidate = original.replace(anchor, helper + anchor).replace(caption_anchor, caption_replacement).replace(
    progress_anchor, progress_replacement)
# Every existing line remains byte-identical; only the helper and its two
# text-only call sites are added. No DOM/layout/framework/browser work.
restored = candidate.replace(helper, "").replace(caption_replacement, caption_anchor).replace(
    progress_replacement, progress_anchor)
assert restored == original
assert candidate.index('if(recorded)caption="Recorded, independently checked proof.') < candidate.index(
    'const repeated=searched?repeatedWorkNote(result.search):"";')
assert candidate.count("Number.isSafeInteger(") - original.count("Number.isSafeInteger(") == 2
assert LIVE.read_bytes() == raw
with (OUT / "app.js").open("x", encoding="utf-8") as stream:
    stream.write(candidate)
diff = "".join(difflib.unified_diff(original.splitlines(keepends=True), candidate.splitlines(keepends=True),
                                  fromfile="a/hydra-playground/app.js", tofile="b/hydra-playground/app.js"))
with (OUT / "app.js.patch").open("x", encoding="utf-8") as stream:
    stream.write(diff)
record = {"status": "prepared_not_installed", "live_source_unchanged": True,
          "live_sha256": hashlib.sha256(raw).hexdigest(),
          "candidate_sha256": hashlib.sha256(candidate.encode("utf-8")).hexdigest(),
          "added_lines": len(candidate.splitlines()) - len(original.splitlines()),
          "changed_existing_lines": 0, "dom_changes": 0, "browser_launches": 0,
          "checks": ["three unique insertion points", "existing source restored byte-for-byte after removing insertions",
                     "recorded caption retained before new note", "both new counters require positive safe integers"]}
with (OUT / "prepared.json").open("x", encoding="utf-8") as stream:
    json.dump(record, stream, indent=2)
    stream.write("\n")
print(json.dumps(record, sort_keys=True))
