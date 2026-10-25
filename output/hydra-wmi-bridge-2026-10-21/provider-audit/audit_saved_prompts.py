"""Read authenticated saved WMI receipts; no project/model/native imports."""
from pathlib import Path
import ast
from collections import Counter
import hashlib
import json
import re
import statistics

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
EVIDENCE = HERE.parent / "wmi-evidence"
LATENT = REPO / "output/hydra-model-upgrade-2026-10-20/comparison-01/latent-source/src/latentproof"


def pin(path):
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def require(condition, message):
    if not condition:
        raise ValueError(message)


summary = json.loads((EVIDENCE / "summary.json").read_text())
require(pin(EVIDENCE / "proofs.jsonl")["sha256"] == summary["proofs_sha256"], "Saved proof file differs")
rows = [json.loads(line) for line in (EVIDENCE / "proofs.jsonl").read_text().splitlines()]
require(len(rows) == 64, "Expected all 64 saved rows")
source = LATENT / "qwen_data.py"
require(pin(source)["sha256"] == "2f1423410fc26eb32476e3ef051f0270723fa3f9a1296be3d3369e85112d5da4", "Frozen renderer differs")
# Execute only this audited pure JSON function, never module imports.
tree = ast.parse(source.read_text())
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "compact_prompt")
namespace = {"json": json, "require": require}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"), namespace)
compact_prompt = namespace["compact_prompt"]


def analyze(selected):
    counts, commands = Counter(), Counter()
    widths, lengths, generation_seconds, per_case = [], [], [], []
    alias_examples = []
    for row in selected:
        trace = [step for step in row["native_result"]["trace"] if "v" in step]
        require(len(trace) == len(row["steps"]) == len(row["actions"]), "Trace action accounting differs")
        lengths.append(len(row["actions"]))
        seconds = sum(step["generation"]["seconds"] for step in row["steps"])
        generation_seconds.append(seconds)
        alias_case = False
        for step, native in zip(row["steps"], trace):
            prompt = step["prompt"]
            state = json.loads(prompt.split("\n", 2)[1])
            goals = state["goals"]
            require(prompt == compact_prompt(goals, library_prefix_length=247, focus=0), "Exact prompt reconstruction failed")
            require(hashlib.sha256(prompt.encode()).hexdigest() == step["prompt_sha256"] == step["generation"]["prompt_sha256"], "Prompt hash differs")
            require(goals == native["goals_before"], "Model input does not contain all ordered native goals")
            require(step["decoded"]["action"] == row["actions"][step["index"] - 1], "Action differs")
            counts["prompts_exact"] += 1
            counts["multigoal_prompts"] += len(goals) > 1
            counts["prompt_focus_nonzero"] += state["focus"] != 0
            counts["native_focus_nonzero"] += native["focus"] != 0
            widths.append(len(goals))
            aliases = sorted(set(re.findall(r"\?t\d+", prompt)))
            if aliases:
                counts["metavariable_prompts"] += 1
                alias_case = True
                if "?t1" not in aliases:
                    counts["metavariable_prompts_missing_t1"] += 1
                    if len(aliases) == 1:
                        alias_examples.append({"id": row["id"], "step": step["index"], "aliases": aliases,
                                               "prompt_sha256": step["prompt_sha256"], "goals": len(goals)})
        counts["cases_with_metavariables"] += alias_case
        counts["actions_over512bytes"] += sum(len(a.encode()) > 512 for a in row["actions"])
        commands.update(a.split()[0] for a in row["actions"])
        per_case.append({"id": row["id"], "actions": len(row["actions"]), "generation_seconds_on_WMI": seconds,
                         "metavariables": alias_case})
    return {"cases": len(selected), "counts": dict(counts), "command_counts": dict(commands),
            "actions": {"min": min(lengths), "median": statistics.median(lengths), "max": max(lengths),
                        "over16": sum(n > 16 for n in lengths), "over32": sum(n > 32 for n in lengths),
                        "over64": sum(n > 64 for n in lengths), "over96": sum(n > 96 for n in lengths)},
            "open_goals": {"min": min(widths), "max": max(widths)},
            "generation_seconds_on_WMI": {"min": min(generation_seconds), "median": statistics.median(generation_seconds),
                "max": max(generation_seconds), "over30": sum(n > 30 for n in generation_seconds),
                "scope": "Sum of retained generation seconds only; not CPU replay time and not portable GH200/Mac timing"},
            "earliest_single_alias_examples": sorted(alias_examples, key=lambda x: (x["step"], x["id"]))[:5],
            "per_case": per_case}


success = [row for row in rows if row["autonomous_python_kernel_proof"]]
require(len(success) == 50, "Expected 50 saved successful trajectories")
files = [EVIDENCE / "proofs.jsonl", EVIDENCE / "summary.json", source,
         REPO / "output/hydra-model-upgrade-2026-10-20/comparison-01/hydra_torch_candidate.py",
         REPO / "output/hydra-model-upgrade-2026-10-20/comparison-01/run_arm.py"]
report = {"schema": "hydra-saved-wmi-prompt-audit-v1", "scope": "File-only source and saved-receipt audit; no tokenizer/model/native execution",
          "inputs": {str(path.relative_to(REPO)): pin(path) for path in files},
          "all": analyze(rows), "saved_successes": analyze(success)}
(HERE / "SAVED_PROMPT_AUDIT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": "passed", "all_prompts": report["all"]["counts"]["prompts_exact"],
                  "saved_successes": len(success), "output": str(HERE / "SAVED_PROMPT_AUDIT.json")}))
