"""One-use frontier training/evaluation gate; no consent or data admission writer.

Login-side code uses Python 3.6 and the standard library only. File and command
primitives are reused from search_launch, but NO historical launch, ledger,
reservation, profile, or approval operation is called. A separate human resource
approval pins the raw READY request. Missing reviews, benchmark admission,
production preflight or a clean execution snapshot fail before the SSH wrapper.
"""

import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys


ROOT = Path(__file__).absolute().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from training.peano_hydra import search_launch as safe

require = safe.require
canonical = safe.canonical
digest = safe.digest
decode = safe.decode
relative = safe.relative
directory = safe.directory
read = safe.read
fingerprint = safe.fingerprint
exists = safe.exists
inventory = safe.inventory
run = safe.run
HEX = safe.HEX
COMMIT = safe.COMMIT
JOB_ID = safe.JOB_ID

PROFILE = "peano-hydra-frontier-v1"
RUN_ID = "frontier-v1"
PACKAGE = "_deploy/hydra-frontier-v1"
REQUEST = PACKAGE + "/resource-request.json"
APPROVAL = PACKAGE + "/approval.json"
REQUEST_SCHEMA = "peano-hydra-frontier-resource-request-v1"
APPROVAL_SCHEMA = "peano-hydra-frontier-resource-approval-v1"
LEDGER_SCHEMA = "peano-hydra-frontier-held-chain-ledger-v1"
LEDGER = "logs/hydra-frontier-v1.jsonl"
LOCK = "logs/.hydra-frontier-v1.lock"
SUBMISSIONS = "logs/submissions.tsv"
SUBMISSION_HEADER = safe.SUBMISSION_HEADER
REMOTE_PARENT = "codex-control/projects/peano-lab-training"
REMOTE_CHILD = "experiments/frontier-v1"
ACCOUNT = "plgccaiautore2026-gpu-gh200"
PARTITION = "plgrid-gpu-gh200"
CONFIRM = "PEANO-HYDRA-FRONTIER-9000-GPU-SECONDS"
STAGES = ("train", "evaluate")
JOBS = {stage: "slurm/peano_hydra_frontier_" + stage + ".sbatch" for stage in STAGES}
JOB_NAMES = {stage: PROFILE + "-" + stage for stage in STAGES}
RESERVATIONS = {
    "train": {"seconds": 7200, "gpus": 1, "cpus": 8, "memory_gib": 64},
    "evaluate": {"seconds": 1800, "gpus": 1, "cpus": 8, "memory_gib": 64},
}
WALL = {"train": "02:00:00", "evaluate": "00:30:00"}
MODEL = {"model_id": "Qwen/Qwen3-1.7B-Base",
         "revision": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"}
PINS = {
    "epoch_sha256": "f64b5f100c9c9bc77049ea627f13e641be83ac72aaa474216682076679a468ad",
    "baseline_adapter_manifest_sha256": "172a6928710192c5348dcd7b04f71e6d4d3f75dfa1ab0f7f5add601769704a7c",
    "baseline_adapter_sha256": "4ad0af7b07078a4812ac627b71941d4acec0f4fa9c8fe74723b6606ec2c27310",
    "baseline_tokenizer_sha256": "2c5206dc7dda009d1a466348530a56c21f68d68057115142b2cd121838cf3f5e",
    "tokenizer_json_sha256": "aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4",
}
CANDIDATE_PIN_FIELDS = frozenset(("candidate_readiness_sha256", "native_source_manifest_sha256",
                                  "lineage_proposal_sha256"))
ADMITTED = PACKAGE + "/admitted"
PREPARATION = ADMITTED + "/preparation"
INPUTS = {
    "candidate_readiness": ADMITTED + "/candidate-readiness.json",
    "lineage_review": ADMITTED + "/lineage-review.json",
    "training_admission": ADMITTED + "/training-admission.json",
    "preparation_manifest": PREPARATION + "/manifest.json",
    "preparation_preflight": ADMITTED + "/preflight.json",
    "token_preflight": PACKAGE + "/token-preflight.json",
    "evaluation_request": PACKAGE + "/evaluation-request.json",
    "baseline_adapter_manifest": PACKAGE + "/old-model/manifest.json",
}
ADAPTER_OUTPUT = "results/peano-hydra/qwen3-1.7b-authority-primitive-v28-f64b5f100c9c-frontier-v1"
TRAINING = {
    "run_id": RUN_ID, "initialization": "fresh-pinned-base-plus-new-lora",
    "epochs": 1, "train_rows": 12772, "dev_rows": 2096,
    "per_device_train_batch_size": 1, "gradient_accumulation_steps": 8,
    "expected_optimizer_steps": 1597, "maximum_optimizer_steps": 2048,
    "configured_max_length": 4096, "lora_rank": 16, "lora_alpha": 32,
    "lora_dropout": 0.05, "learning_rate": 0.0001,
    "seed": 20260826, "checkpoint_selection": "final-completed-epoch-only",
    "adapter_output": ADAPTER_OUTPUT, "resume": False,
}
EVALUATION = {
    "cohorts": ["frontier-heldout-candidate32", "frontier-regression32"],
    "goals_per_cohort": 32, "reserve_goals_excluded_not_scored": 32,
    "roles": ["saved-corrected", "new-frontier"], "budgets": [8, 16],
    "total_goal_records": 256, "maximum_model_calls": 3072,
    "search_profile": "context-alpha-v1",
    "fixed_search": {"max_depth": 16, "beam_width": 4, "candidates_per_state": 4,
                     "max_states": 64, "max_new_tokens": 64, "seed": 20260826},
    "candidate_binding": "successful-exact-training-run-final-manifest",
    "all_positive_proofs_require_fresh_native_replay": True,
    "incomplete_outcomes": "unknown", "resume": False,
    "sealed_benchmark_claim": False, "independent_ownership_claim": False,
}
RUNTIME = {
    "project": REMOTE_PARENT, "python": ".venv-helios/bin/python",
    "hf_home": ".cache/huggingface", "module": "ML-bundle/25.10",
    "python_version": "3.13.5", "machine": "aarch64",
    "requirements_sha256": "50315d5465ec6081517e1e3bb93096c3a990907020978a490295cde59a6c7871",
    "offline": True, "read_only": True, "install": False,
}
TOKEN_PREFLIGHT_SOURCES = frozenset((
    "scripts/preflight_peano_hydra_frontier_tokens.py",
    "training/peano_hydra/scaling_admission.py",
    "training/peano_hydra/scaling_lineage.py",
    "training/peano_hydra/posttrain.py",
    "training/peano_hydra/review_runtime.py",
    "training/peano_policy/data.py", "training/peano_policy/prompt.py", "training/peano_policy/budget.py",
))
REQUIRED_SOURCES = frozenset(tuple(JOBS.values()) + (
    "training/peano_hydra/frontier_pilot_launch.py",
    "training/peano_hydra/search_launch.py",
    "scripts/helios_hydra_frontier.sh", "scripts/run_peano_hydra_frontier.sh",
    "scripts/check_peano_hydra_frontier_runtime.py",
    "scripts/execute_peano_hydra_frontier_train.py",
    "scripts/preflight_peano_hydra_frontier_tokens.py",
    "scripts/prepare_peano_hydra_frontier_launch.py",
    "scripts/eval_peano_hydra_frontier_benchmark.py",
    "training/peano_hydra/frontier_benchmark_protocol.py",
    "training/peano_hydra/frontier_benchmark_run.py",
    "training/peano_hydra/scaling_evaluation.py",
    "training/peano_hydra/scaling_admission.py",
    "training/peano_hydra/scaling_lineage.py",
    "training/peano_hydra/posttrain.py",
    "training/peano_hydra/helios_runtime.py",
    "training/peano_hydra/review_runtime.py",
    "training/peano_policy/runtime.py",
    "training/peano_policy/requirements-helios.lock",
)) | TOKEN_PREFLIGHT_SOURCES
REQUEST_FIELDS = frozenset((
    "schema", "status", "profile", "run_id", "source_commit", "source_files",
    "payloads", "payloads_sha256", "inputs", "review_sha256", "pins", "model",
    "training", "evaluation", "reservations", "maximum_aggregate_gpu_seconds",
    "maximum_concurrent_gpus", "automatic_retry", "resume", "refunds",
    "runtime_dependencies", "transfer_authorized", "gpu_execution_authorized",
))
ACKNOWLEDGMENTS = frozenset((
    "declared_relations_and_exposures_only", "no_unseen_or_semantic_completeness_claim",
    "no_independent_test_seal_or_compute_authority", "reviewer_identity_not_cryptographically_verified",
))
MAX_METADATA = 16 * 1024**2
MAX_TOTAL = 2 * 1024**3


def request_template():
    """A non-launchable budget proposal, never an approval or fake identity."""
    return {
        "schema": REQUEST_SCHEMA, "status": "draft-missing-prerequisites",
        "profile": PROFILE, "run_id": RUN_ID, "source_commit": None, "source_files": {},
        "payloads": {}, "payloads_sha256": None, "inputs": dict(INPUTS), "review_sha256": None,
        "pins": dict(PINS, **{key: None for key in sorted(CANDIDATE_PIN_FIELDS)}),
        "model": dict(MODEL), "training": dict(TRAINING), "evaluation": dict(EVALUATION),
        "reservations": {key: dict(value) for key, value in RESERVATIONS.items()},
        "maximum_aggregate_gpu_seconds": 9000, "maximum_concurrent_gpus": 1,
        "automatic_retry": False, "resume": False, "refunds": False,
        "runtime_dependencies": dict(RUNTIME), "transfer_authorized": False, "gpu_execution_authorized": False,
    }


def ready_request(source_commit, review_sha256):
    """Derive exact source/payload identities only after real input admission.

    The caller must run the pinned benchmark --check before publishing this
    request. This function never writes an approval or opens an allocation.
    """
    require(exists(".git"), "request preparation requires the real clean execution Git snapshot")
    require(type(source_commit) is str and COMMIT.fullmatch(source_commit)
            and type(review_sha256) is str and HEX.fullmatch(review_sha256),
            "explicit execution commit and canonical human review SHA required")
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null", GIT_NO_REPLACE_OBJECTS="1",
                       GIT_NO_LAZY_FETCH="1", GIT_OPTIONAL_LOCKS="0")
    tracked = safe.run(["git", "-C", str(ROOT), "ls-files", "-z"], environment).split("\0")
    require(tracked[-1] == "" and 1 <= len(tracked) - 1 <= 4096
            and len(set(tracked[:-1])) == len(tracked) - 1, "bounded unique tracked execution inventory required")
    sources = {relative(name): fingerprint(name)[0] for name in tracked[:-1]}
    safe._execution_commit(source_commit, {name: value["sha256"] for name, value in sources.items()})
    payloads = {name: fingerprint(name)[0] for name in sorted(inventory(PACKAGE) - {REQUEST, APPROVAL})}
    candidate = _json(INPUTS["candidate_readiness"])
    request = request_template()
    request.update(status="ready-for-explicit-resource-approval", source_commit=source_commit,
                   source_files=sources, payloads=payloads, payloads_sha256=digest(payloads),
                   review_sha256=review_sha256)
    request["pins"].update(candidate_readiness_sha256=payloads[INPUTS["candidate_readiness"]]["sha256"],
                           native_source_manifest_sha256=candidate["source_manifest_sha256"],
                           lineage_proposal_sha256=candidate["lineage_proposal_sha256"])
    return validate_request(request)


def _json(name):
    raw = read(name, MAX_METADATA)
    # The shared duplicate/nonfinite-rejecting decoder has a 4 MiB limit.
    # Large corpus manifests are bounded separately and never executed.
    require(len(raw) <= safe.MAX_JSON, "launch JSON metadata exceeds the 4 MiB gate")
    return decode(raw)


def _seal(record, field):
    require(type(record) is dict and type(record.get(field)) is str
            and HEX.fullmatch(record[field])
            and record[field] == digest({k: v for k, v in record.items() if k != field}),
            "semantic metadata seal differs: " + field)


def _files(mapping, label):
    require(type(mapping) is dict and 0 < len(mapping) <= 4096, label + " inventory is missing/oversized")
    total = 0
    for name, expected in mapping.items():
        relative(name)
        require(type(expected) is dict and set(expected) == {"bytes", "sha256"}
                and type(expected["bytes"]) is int and 0 <= expected["bytes"] <= safe.MAX_PAYLOAD
                and type(expected["sha256"]) is str and HEX.fullmatch(expected["sha256"]),
                label + " has an invalid file identity")
        total += expected["bytes"]
        require(total <= MAX_TOTAL, label + " exceeds the total byte cap")
        require(fingerprint(name)[0] == expected, label + " changed: " + name)


def _input_metadata(request):
    pins = request["pins"]
    records = {key: _json(path) for key, path in INPUTS.items()}
    payloads = request["payloads"]
    identity = lambda key: payloads[INPUTS[key]]
    ready = records["candidate_readiness"]
    require(identity("candidate_readiness")["sha256"] == pins["candidate_readiness_sha256"]
            and ready.get("source_manifest_sha256") == pins["native_source_manifest_sha256"]
            and ready.get("lineage_proposal_sha256") == pins["lineage_proposal_sha256"],
            "recovered candidate identity changed")
    review = records["lineage_review"]
    _seal(review, "review_sha256")
    require(review.get("schema") == "peano-hydra-scaling-lineage-review-v1"
            and review.get("decision") == "accept" and review.get("asserted_human_review") is True
            and review.get("review_sha256") == request["review_sha256"]
            and review.get("proposal_sha256") == pins["lineage_proposal_sha256"]
            and type(review.get("reviewer_reference")) is str and review["reviewer_reference"].strip()
            and type(review.get("acknowledgments")) is dict
            and set(review["acknowledgments"]) == ACKNOWLEDGMENTS
            and all(v is True for v in review["acknowledgments"].values()),
            "the exact accepted external human lineage review is required")
    admitted = records["training_admission"]
    _seal(admitted, "admission_sha256")
    require(admitted.get("schema") == "peano-hydra-frontier-model-data-admission-v1"
            and admitted.get("status") == "review-accepted-native-source"
            and admitted.get("run_id") == RUN_ID
            and admitted.get("human_review_asserted") is True
            and admitted.get("model_data_admitted") is True
            and admitted.get("review_sha256") == review["review_sha256"]
            and admitted.get("candidate_readiness_sha256") == pins["candidate_readiness_sha256"]
            and admitted.get("source_manifest_sha256") == pins["native_source_manifest_sha256"]
            and admitted.get("proposal_sha256") == pins["lineage_proposal_sha256"]
            and canonical(admitted.get("scope")) == canonical(review.get("scope"))
            and admitted.get("files", {}).get("lineage-review.json") == identity("lineage_review")
            and admitted.get("files", {}).get("candidate-readiness.json") == identity("candidate_readiness"),
            "exact reviewed training admission is missing or mismatched")
    counts = admitted.get("counts", {})
    require(counts.get("candidate_projected_split_rows") == {"train": 12772, "dev": 2096, "test": 0, "quarantine": 0}
            and counts.get("candidate_projected_rows") == 14868
            and counts.get("native_routes") == 1152 and counts.get("native_transition_rows") == 15264,
            "admitted native/model row accounting changed")
    for name, expected in admitted.get("source_files", {}).items():
        require(payloads.get(ADMITTED + "/source/" + relative(name)) == expected,
                "native source file is absent from the approved payload inventory")
    prep = records["preparation_manifest"]
    require(prep.get("run_id") == RUN_ID and prep.get("model") == MODEL
            and prep.get("epoch_sha256") == PINS["epoch_sha256"]
            and prep.get("training", {}).get("adapter_output_dir") == ADAPTER_OUTPUT
            and prep.get("curriculum_identity", {}).get("review_admission", {}).get("admission_file_sha256")
                == identity("training_admission")["sha256"],
            "admitted preparation changed its review, base, epoch, output or run")
    for name, expected in prep.get("files", {}).items():
        require(type(expected) is dict
                and payloads.get(PREPARATION + "/" + relative(name))
                    == {key: expected[key] for key in ("bytes", "sha256")},
                "preparation file is absent from the approved payload inventory")
    preflight = records["preparation_preflight"]
    require(preflight.get("preparation_manifest_sha256") == identity("preparation_manifest")["sha256"]
            and preflight.get("training_rows") == 12772 and preflight.get("development_rows") == 2096
            and preflight.get("expected_optimizer_steps") == 1597 and preflight.get("run_id") == RUN_ID
            and preflight.get("adapter_output_dir") == ADAPTER_OUTPUT
            and preflight.get("model_trained") is False and preflight.get("cuda_initialized") is False,
            "complete admitted CPU preflight is missing or mismatched")
    tokens = records["token_preflight"]
    require(tokens.get("schema") == "peano-hydra-frontier-production-token-preflight-v1"
            and tokens.get("status") == "passed"
            and tokens.get("preparation_manifest_sha256") == identity("preparation_manifest")["sha256"]
            and tokens.get("tokenizer_file_sha256") == PINS["tokenizer_json_sha256"]
            and tokens.get("model_weights_loaded") is False
            and tokens.get("review_sha256") == request["review_sha256"]
            and tokens.get("admission", {}).get("admission_file_sha256") == identity("training_admission")["sha256"]
            and tokens.get("configured_max_length") == 4096,
            "production token preflight must bind the complete admitted preparation")
    prep_bytes = sum(value["bytes"] for name, value in payloads.items() if name.startswith(PREPARATION + "/"))
    require(type(tokens.get("preparation_bytes")) is int and tokens["preparation_bytes"] == prep_bytes
            and tokens.get("preparation_byte_cap") == 64 * 1024**2 and 0 < prep_bytes <= 64 * 1024**2,
            "production token preflight must measure the complete bounded preparation")
    require(type(tokens.get("execution_source_files")) is dict
            and set(tokens["execution_source_files"]) == TOKEN_PREFLIGHT_SOURCES
            and all(tokens["execution_source_files"][name] == request["source_files"][name]["sha256"]
                    for name in TOKEN_PREFLIGHT_SOURCES),
            "production token preflight belongs to another execution source")
    process_path = INPUTS["token_preflight"] + ".process.json"
    require(tokens.get("process_receipt") == {"file": Path(process_path).name,
                                            "sha256": payloads.get(process_path, {}).get("sha256")}
            and process_path in payloads, "production preflight lacks its exact bounded process receipt")
    audit = _json(process_path)
    process = audit.get("process", {})
    require(audit.get("schema") == "peano-hydra-frontier-token-process-v1"
            and audit.get("passed") is True and audit.get("sources_unchanged") is True
            and audit.get("source_files") == tokens["execution_source_files"]
            and process.get("reason") == "exited" and type(process.get("returncode")) is int
            and process["returncode"] == 0 and process.get("observed_descendant_count") == 0
            and type(process.get("stdout")) is str
            and canonical(decode(process["stdout"].encode())) == canonical(
                {key: value for key, value in tokens.items() if key not in ("process_receipt", "execution_source_files")}),
            "production preflight process failed or does not bind the complete token result")
    require(type(tokens.get("splits")) is dict and set(tokens["splits"]) == {"train", "dev"},
            "production token preflight lacks both complete splits")
    require(type(tokens.get("token_exposure")) is dict and set(tokens["token_exposure"]) == {"train", "dev"},
            "production preflight must retain complete tokenize_split records")
    for split, rows, total, maximum, supervised, square_cap in (
        ("train", 12772, 6977592, 682, 14, 100000000000),
        ("dev", 2096, 1156032, 678, 5, 16000000000),
    ):
        value = tokens["splits"][split]
        exposure = tokens["token_exposure"][split]
        _seal(exposure, "record_sha256")
        require(type(value) is dict and value.get("rows") == rows and value.get("total") == total
                and value.get("maximum") == maximum and value.get("supervised_maximum") == supervised
                and type(value.get("sum_squared")) is int and 0 < value["sum_squared"] <= square_cap
                and exposure.get("format") == "peano-policy-token-exposure" and exposure.get("v") == 1
                and exposure.get("rows") == rows and exposure.get("role") == split
                and exposure.get("max_length") == 4096
                and exposure.get("sequence", {}).get("total") == total
                and exposure.get("sequence", {}).get("maximum") == maximum
                and exposure.get("sequence", {}).get("sum_squared") == value["sum_squared"]
                and exposure.get("supervision", {}).get("maximum") == supervised,
                "production token census differs for " + split)
    old = records["baseline_adapter_manifest"]
    require(identity("baseline_adapter_manifest")["sha256"] == PINS["baseline_adapter_manifest_sha256"]
            and old.get("model") == MODEL
            and old.get("adapter", {}).get("sha256") == PINS["baseline_adapter_sha256"]
            and old.get("tokenizer", {}).get("sha256") == PINS["baseline_tokenizer_sha256"],
            "the saved corrected adapter or tokenizer changed")
    return records


def validate_request(request):
    require(type(request) is dict and set(request) == REQUEST_FIELDS
            and request.get("schema") == REQUEST_SCHEMA
            and request.get("status") == "ready-for-explicit-resource-approval"
            and request.get("profile") == PROFILE and request.get("run_id") == RUN_ID,
            "a draft or incomplete resource request cannot allocate")
    for key, expected in (("inputs", INPUTS), ("model", MODEL), ("training", TRAINING),
                          ("evaluation", EVALUATION), ("reservations", RESERVATIONS), ("runtime_dependencies", RUNTIME)):
        require(canonical(request.get(key)) == canonical(expected), "fixed resource scope changed: " + key)
    require(type(request.get("pins")) is dict and set(request["pins"]) == set(PINS) | CANDIDATE_PIN_FIELDS
            and all(request["pins"][key] == value for key, value in PINS.items())
            and all(type(request["pins"][key]) is str and HEX.fullmatch(request["pins"][key])
                    for key in CANDIDATE_PIN_FIELDS),
            "final candidate identities must be explicit request-pinned hashes")
    require(type(request.get("source_commit")) is str and COMMIT.fullmatch(request["source_commit"])
            and type(request.get("review_sha256")) is str and HEX.fullmatch(request["review_sha256"]),
            "real source and canonical human review identities are required")
    require(type(request["maximum_aggregate_gpu_seconds"]) is int and request["maximum_aggregate_gpu_seconds"] == 9000
            and type(request["maximum_concurrent_gpus"]) is int and request["maximum_concurrent_gpus"] == 1
            and all(request[name] is False for name in ("automatic_retry", "resume", "refunds",
                                                       "transfer_authorized", "gpu_execution_authorized")),
            "resource request changed its fixed no-retry limits or claims authorization")
    sources, payloads = request["source_files"], request["payloads"]
    _files(sources, "execution source")
    require(REQUIRED_SOURCES <= set(sources) and not any(name.startswith((".git/", PACKAGE + "/")) for name in sources),
            "execution inventory omits the new jobs or mixes source and inputs")
    for prefix in ("training", "peano-lab/py", "scripts", "slurm"):
        require(inventory(prefix) == {name for name in sources if name.startswith(prefix + "/")},
                "execution tree has missing, untracked or unapproved leaves: " + prefix)
    _files(payloads, "input payload")
    require(all(name.startswith(PACKAGE + "/") and name not in (REQUEST, APPROVAL) for name in payloads)
            and set(INPUTS.values()) <= set(payloads)
            and digest(payloads) == request["payloads_sha256"]
            and inventory(PACKAGE) - {REQUEST, APPROVAL} == set(payloads),
            "closed input inventory changed")
    require(sources["training/peano_policy/requirements-helios.lock"]["sha256"] == RUNTIME["requirements_sha256"],
            "the existing Helios runtime lock changed")
    records = _input_metadata(request)
    # Benchmark semantic validation belongs to the pinned CPU protocol. The
    # shell invokes its --check BEFORE SSH; the job repeats it before inference.
    # Merely supplying an evaluation JSON is never an admission assertion.
    require(records["evaluation_request"].get("benchmark_review") is not None,
            "an externally anchored benchmark review is required before SSH")
    return request


def validate_metadata(expected_approval_sha256):
    require(type(expected_approval_sha256) is str and HEX.fullmatch(expected_approval_sha256),
            "external RAW resource approval SHA required")
    raw = read(APPROVAL)
    require(hashlib.sha256(raw).hexdigest() == expected_approval_sha256, "external resource approval bytes differ")
    approval = decode(raw)
    require(set(approval) == {"schema", "profile", "run_id", "approved", "approval_reference", "request_file_sha256"}
            and approval.get("schema") == APPROVAL_SCHEMA and approval.get("profile") == PROFILE
            and approval.get("run_id") == RUN_ID and approval.get("approved") is True
            and type(approval.get("approval_reference")) is str
            and 1 <= len(approval["approval_reference"]) <= 2048
            and approval["approval_reference"].strip() == approval["approval_reference"],
            "a proposal is not a separately supplied explicit resource approval")
    request_raw = read(REQUEST)
    require(hashlib.sha256(request_raw).hexdigest() == approval["request_file_sha256"],
            "resource approval does not pin this exact RAW request")
    request = validate_request(decode(request_raw))
    require(read(APPROVAL) == raw and read(REQUEST) == request_raw, "approval or request changed during admission")
    return approval, request


def _identity(approval, request, expected_sha, *, local=False):
    sources = {name: value["sha256"] for name, value in request["source_files"].items()}
    if local:
        require(exists(".git"), "local launch requires its own clean frozen Git checkout")
    synced = safe._execution_commit(request["source_commit"], sources)
    return {"approval_sha256": expected_sha, "request_file_sha256": approval["request_file_sha256"],
            "source_commit": request["source_commit"], "source_files_sha256": digest(request["source_files"]),
            "payloads_sha256": request["payloads_sha256"], "synced_at": synced,
            "job_script_sha256": {stage: sources[JOBS[stage]] for stage in STAGES}}


def _remote_root():
    scratch = os.environ.get("SCRATCH")
    require(type(scratch) is str and scratch.startswith("/") and ".." not in Path(scratch).parts,
            "configured SCRATCH is required")
    parent = Path(scratch) / REMOTE_PARENT
    require(ROOT == parent / REMOTE_CHILD, "frontier must use its own fixed experiment directory")
    fd = directory(ROOT)
    os.close(fd)
    return parent


def _snapshot(raw, stage, job, predecessor=None, running=False):
    require(type(raw) is str and 0 < len(raw.encode()) <= 65536 and len(raw.strip().splitlines()) == 1,
            "held controller record exceeds its bound")
    keys = {"JobId", "JobName", "WorkDir", "JobState", "Reason", "Priority", "Dependency", "Requeue",
            "Account", "Partition", "TimeLimit", "NumNodes", "NumCPUs", "ReqTRES"}
    fields = {}
    for match in re.finditer(r"(?:^|\s)([A-Za-z][A-Za-z0-9]*)=(\S*)", raw):
        key, value = match.groups()
        if key in keys:
            require(key not in fields, "duplicate guarded controller field")
            fields[key] = value
    dependency = "(null)" if predecessor is None else "afterok:" + predecessor
    allowed_dependencies = ((dependency, dependency + "(fulfilled)", "(null)") if running
                            else (dependency, dependency + "(unfulfilled)"))
    require(set(fields) == keys and fields["JobId"] == job and fields["JobName"] == JOB_NAMES[stage]
            and fields["WorkDir"] == str(ROOT)
            and (fields["JobState"] == "RUNNING" if running else
                 fields["JobState"] == "PENDING" and fields["Reason"] == "JobHeldUser" and fields["Priority"] == "0")
            and fields["Dependency"] in allowed_dependencies
            and fields["Requeue"] == "0" and fields["Account"] == ACCOUNT
            and fields["Partition"] == PARTITION and fields["TimeLimit"] == WALL[stage]
            and fields["NumNodes"] in ("1", "1-1") and fields["NumCPUs"] == "8",
            "held frontier job changed its identity, dependency, resources or restart policy")
    resources = {}
    for item in fields["ReqTRES"].split(","):
        key, sep, value = item.partition("=")
        require(sep and key and value and key not in resources, "ambiguous controller resources")
        resources[key] = value
    require(resources.get("cpu") == "8" and resources.get("node") == "1"
            and resources.get("gres/gpu") == "1" and resources.get("mem") in ("64G", "65536M", "67108864K")
            and all(v == "1" for k, v in resources.items() if k.startswith("gres/gpu:")),
            "controller changed the one-GPU/64 GiB reservation")
    return {"raw": raw, "raw_sha256": hashlib.sha256(raw.encode()).hexdigest(), "fields": fields}


def _header(identity):
    return {"kind": "header", "schema": LEDGER_SCHEMA, "profile": PROFILE, "run_id": RUN_ID,
            "identity": identity, "reservations": RESERVATIONS, "maximum_aggregate_gpu_seconds": 9000,
            "maximum_concurrent_gpus": 1, "automatic_retry": False, "resume": False, "refunds": False}


def load_ledger(identity):
    state = {"events": [], "raw": b"", "phase": "empty", "jobs": {}, "created_at": None, "gpu_seconds": 0}
    if not exists(LEDGER):
        return state
    raw = read(LEDGER, safe.MAX_LEDGER)
    lines = raw.splitlines(keepends=True)
    require(raw.endswith(b"\n") and 1 <= len(lines) <= 8, "one-use ledger is truncated or extended")
    kinds = ("header", "reserve", "train-accepted", "evaluate-accepted", "held-validated",
             "release-authorized", "evaluate-released", "train-released")
    previous = "0" * 64
    for index, line in enumerate(lines):
        event = decode(line)
        require(set(event) == {"index", "previous_sha256", "payload", "sha256"}
                and type(event["index"]) is int and event["index"] == index and event["previous_sha256"] == previous
                and event["sha256"] == digest({k: event[k] for k in ("index", "previous_sha256", "payload")})
                and canonical(event) + b"\n" == line, "ledger canonical hash chain differs")
        value = event["payload"]
        require(type(value) is dict and value.get("kind") == kinds[index], "ledger stage order changed")
        if index == 0:
            require(canonical(value) == canonical(_header(identity)), "ledger belongs to another approval/source")
        elif index == 1:
            require(set(value) == {"kind", "reservations", "created_at"}
                    and value["reservations"] == RESERVATIONS and type(value["created_at"]) is str
                    and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value["created_at"]),
                    "ledger reservation differs")
            state["gpu_seconds"], state["created_at"] = 9000, value["created_at"]
        elif index in (2, 3):
            stage = STAGES[index - 2]
            predecessor = None if stage == "train" else state["jobs"]["train"]
            require(set(value) == {"kind", "job_id", "dependency_job_id"}
                    and type(value["job_id"]) is str and JOB_ID.fullmatch(value["job_id"])
                    and value["job_id"] not in state["jobs"].values()
                    and value["dependency_job_id"] == predecessor, "accepted job/dependency differs")
            state["jobs"][stage] = value["job_id"]
        elif index == 4:
            require(set(value) == {"kind", "snapshots"} and set(value["snapshots"]) == set(STAGES),
                    "held barrier omits a job")
            for stage in STAGES:
                snapshot = value["snapshots"][stage]
                require(canonical(snapshot) == canonical(_snapshot(snapshot["raw"], stage, state["jobs"][stage],
                        state["jobs"]["train"] if stage == "evaluate" else None)), "held snapshot changed")
        elif index == 5:
            require(set(value) == {"kind", "jobs"} and value["jobs"] == state["jobs"], "release barrier changed")
        else:
            stage = "evaluate" if index == 6 else "train"
            require(set(value) == {"kind", "job_id"} and value["job_id"] == state["jobs"][stage],
                    "release acknowledgment changed")
        state["events"].append(event)
        previous, state["phase"] = event["sha256"], kinds[index]
    state["raw"] = raw
    return state


def _record(state, payload):
    event = {"index": len(state["events"]),
             "previous_sha256": state["events"][-1]["sha256"] if state["events"] else "0" * 64,
             "payload": payload}
    event["sha256"] = digest(event)
    safe._append(LEDGER, state["raw"], canonical(event) + b"\n", safe.MAX_LEDGER)


def _submission_row(stage, state, identity):
    return [state["created_at"], state["jobs"][stage], JOBS[stage],
            state["jobs"]["train"] if stage == "evaluate" else "", str(ROOT),
            identity["source_commit"], "false", identity["synced_at"], identity["job_script_sha256"][stage]]


def _history(state, identity):
    rows, _ = safe._submissions()
    own = [row for row in rows if row[2] in JOBS.values() or row[1] in state["jobs"].values()]
    require(own == [_submission_row(stage, state, identity) for stage in STAGES if stage in state["jobs"]],
            "frontier submission history differs; no historical adoption or refund")


def _queue_history(state):
    parent = _remote_root()
    user = os.environ.get("USER", "")
    require(re.fullmatch(r"[A-Za-z0-9._-]{1,64}", user), "scheduler user is not declared")
    accepted = {job: JOB_NAMES[stage] for stage, job in state["jobs"].items()}
    active = set()
    for line in run(["squeue", "-h", "-u", user, "-o", "%i|%Z|%j|%T"]).splitlines():
        fields = line.split("|")
        require(len(fields) == 4 and JOB_ID.fullmatch(fields[0]), "ambiguous scheduler queue record")
        job, workdir, name, _ = fields
        if workdir == str(parent) or workdir.startswith(str(parent) + "/") or name in JOB_NAMES.values():
            require(job in accepted and name == accepted[job] and workdir == str(ROOT) and job not in active,
                    "another project allocation is active")
            active.add(job)
    seen = set()
    args = ["sacct", "-n", "-P", "-X", "-u", user, "--starttime=2026-08-30",
            "--name=" + ",".join(JOB_NAMES[stage] for stage in STAGES),
            "--format=JobIDRaw,JobName%80,WorkDir%4096"]
    for line in run(args).splitlines():
        if not line.strip():
            continue
        fields = line.split("|")
        require(len(fields) in (3, 4) and (len(fields) == 3 or fields[3] == ""), "ambiguous accounting record")
        job, name, workdir = fields[:3]
        require(job in accepted and job not in seen and name == accepted[job] and workdir == str(ROOT),
                "unrecorded frontier allocation; deleting a ledger does not refund")
        seen.add(job)
    require(seen | active == set(accepted), "accepted frontier job is missing from queue/accounting")


def outputs(jobs):
    return {"adapter": ADAPTER_OUTPUT,
            "evaluation": "results/peano-hydra/evaluations/frontier-v1-" + jobs["evaluate"]}


def _options(stage, approval_sha, predecessor=None):
    result = ["sbatch", "--parsable", "--hold", "--no-requeue", "--kill-on-invalid-dep=yes",
              "--account=" + ACCOUNT, "--partition=" + PARTITION, "--nodes=1", "--ntasks=1",
              "--cpus-per-task=8", "--mem=64G", "--gres=gpu:1", "--time=" + WALL[stage],
              "--chdir=" + str(ROOT), "--export=ALL", "--job-name=" + JOB_NAMES[stage],
              "--output=logs/" + JOB_NAMES[stage] + "-%j.out", "--error=logs/" + JOB_NAMES[stage] + "-%j.err"]
    if predecessor is not None:
        result.append("--dependency=afterok:" + predecessor)
    return result + [JOBS[stage], approval_sha]


def launch(expected_approval_sha256, *, submit=False, expected_commit=None):
    require(type(submit) is bool and "SLURM_JOB_ID" not in os.environ, "submission cannot nest inside a job")
    require(not any(k.startswith("SBATCH_") for k in os.environ), "SBATCH overrides are unauthorized")
    _remote_root()
    approval, request = validate_metadata(expected_approval_sha256)
    identity = _identity(approval, request, expected_approval_sha256)
    require(identity["source_commit"] == expected_commit and identity["synced_at"] is not None,
            "remote launch requires the exact clean staged source provenance")
    fd = -1
    try:
        if submit:
            parent = directory(ROOT)
            try:
                try:
                    os.mkdir("logs", 0o700, dir_fd=parent)
                except FileExistsError:
                    pass
            finally:
                os.close(parent)
            parent = directory(ROOT / "logs")
            try:
                fd = os.open(Path(LOCK).name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                             0o600, dir_fd=parent)
            finally:
                os.close(parent)
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 0, "unsafe reservation lock")
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = load_ledger(identity)
        require(not state["events"], "frontier budget already opened/charged; no retry, resume, reset or refund")
        _history(state, identity)
        _queue_history(state)
        require(not exists(ADAPTER_OUTPUT), "training output already exists; no resume or adoption")
        if not submit:
            return {"status": "test-only", "allocation_performed": False, "scheduler_submission_tested": False,
                    "reservations": RESERVATIONS, "maximum_aggregate_gpu_seconds": 9000, "automatic_retry": False}
        require(_identity(*validate_metadata(expected_approval_sha256), expected_approval_sha256) == identity,
                "approved inputs or source changed before reservation")

        def record(payload):
            _record(state, payload)
            return load_ledger(identity)

        state = record(_header(identity))
        state = record({"kind": "reserve", "reservations": RESERVATIONS,
                        "created_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"})
        # Charge the entire chain durably BEFORE either sbatch. An uncertain
        # scheduler response is never automatically retried or refunded.
        for stage in STAGES:
            predecessor = state["jobs"].get("train") if stage == "evaluate" else None
            raw = run(_options(stage, expected_approval_sha256, predecessor)).strip()
            require(re.fullmatch(r"[1-9][0-9]{0,19}(?:;[A-Za-z0-9_-]{1,64})?", raw),
                    "ambiguous submission; all 9000 GPU seconds remain charged and jobs remain held")
            job = raw.split(";", 1)[0]
            state = record({"kind": stage + "-accepted", "job_id": job, "dependency_job_id": predecessor})
            rows, before = safe._submissions()
            require(job not in {row[1] for row in rows}, "accepted job already exists in submission history")
            added = ((SUBMISSION_HEADER if not before else "") + "\t".join(_submission_row(stage, state, identity)) + "\n").encode()
            safe._append(SUBMISSIONS, before, added, safe.MAX_JSON)
            _history(state, identity)
            _queue_history(state)
        require(all(not exists(path) for path in outputs(state["jobs"]).values()), "output/checkpoints already exist")
        snapshots = {stage: _snapshot(run(["scontrol", "-o", "show", "job", state["jobs"][stage]]), stage,
                     state["jobs"][stage], state["jobs"]["train"] if stage == "evaluate" else None) for stage in STAGES}
        state = record({"kind": "held-validated", "snapshots": snapshots})
        require(_identity(*validate_metadata(expected_approval_sha256), expected_approval_sha256) == identity,
                "approved inputs changed before release; allocations remain held and charged")
        state = record({"kind": "release-authorized", "jobs": state["jobs"]})
        for stage in ("evaluate", "train"):
            # Runtime may observe the durable barrier before release returns.
            fcntl.flock(fd, fcntl.LOCK_UN)
            run(["scontrol", "release", state["jobs"][stage]])
            safe._await_lock(fd, fcntl.LOCK_EX)
            state = record({"kind": stage + "-released", "job_id": state["jobs"][stage]})
        return {"status": "submitted", "profile": PROFILE, "run_id": RUN_ID, "jobs": state["jobs"],
                "reserved_gpu_seconds": 9000, "maximum_concurrent_gpus": 1, "automatic_retry": False,
                "resume": False, "refunds": False, "ledger": LEDGER, "outputs": outputs(state["jobs"])}
    finally:
        if fd >= 0:
            os.close(fd)


def check_job_reservation(expected_approval_sha256, stage):
    """Read-only gate for an exact job admitted through this held chain."""
    require(stage in STAGES, "unknown frontier stage")
    _remote_root()
    job = os.environ.get("SLURM_JOB_ID", "")
    require(JOB_ID.fullmatch(job) and os.environ.get("SLURM_RESTART_COUNT", "0") == "0"
            and os.environ.get("PEANO_JOB_SCRIPT") == JOBS[stage]
            and os.environ.get("PEANO_HYDRA_PROFILE") == PROFILE
            and os.environ.get("SLURM_SUBMIT_DIR") == str(ROOT)
            and not any(k.startswith("SBATCH_") for k in os.environ),
            "scheduled frontier identity, restart or overrides differ")
    approval, request = validate_metadata(expected_approval_sha256)
    identity = _identity(approval, request, expected_approval_sha256)
    parent = directory(ROOT / "logs")
    try:
        fd = os.open(Path(LOCK).name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    finally:
        os.close(parent)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 0, "unsafe reservation lock")
        safe._await_lock(fd, fcntl.LOCK_SH)
        state = load_ledger(identity)
        require(state["phase"] in ("release-authorized", "evaluate-released", "train-released")
                and state["jobs"].get(stage) == job and state["gpu_seconds"] == 9000,
                "job has no durable exact frontier reservation/release barrier")
        _history(state, identity)
        _snapshot(run(["scontrol", "-o", "show", "job", job]), stage, job,
                  state["jobs"]["train"] if stage == "evaluate" else None, running=True)
        if stage == "evaluate":
            raw = run(["sacct", "-n", "-P", "-X", "-j", state["jobs"]["train"], "--starttime=2026-08-30",
                       "--format=JobIDRaw,State,ExitCode"])
            require(raw.strip().rstrip("|") == state["jobs"]["train"] + "|COMPLETED|0:0",
                    "evaluation requires successful completion of the exact approved training job")
        return {"status": "job-verified", "stage": stage, "job_id": job, "jobs": state["jobs"],
                "approval_sha256": expected_approval_sha256,
                "request_file_sha256": approval["request_file_sha256"],
                "evaluation_request_sha256": request["payloads"][INPUTS["evaluation_request"]]["sha256"],
                "source_commit": identity["source_commit"], "allocation_performed": False}
    finally:
        os.close(fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--check-job", choices=STAGES)
    modes.add_argument("--test-only", action="store_true")
    modes.add_argument("--submit", action="store_true")
    parser.add_argument("--approval-sha256", required=True, help="externally supplied RAW approval-file SHA")
    parser.add_argument("--source-commit")
    parser.add_argument("--local", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args(argv)
    try:
        require(args.confirm == CONFIRM if args.submit else args.confirm is None,
                "real submission requires the separate explicit 9000 GPU-second confirmation")
        require(not args.local or args.check, "--local belongs only to pre-SSH metadata checking")
        if args.check:
            require(args.source_commit is None, "metadata check accepts no source override")
            approval, request = validate_metadata(args.approval_sha256)
            identity = _identity(approval, request, args.approval_sha256, local=args.local)
            result = {"status": "metadata-verified", "source_commit": identity["source_commit"],
                      "evaluation_request_sha256": request["payloads"][INPUTS["evaluation_request"]]["sha256"],
                      "helper_sha256": request["source_files"]["training/peano_hydra/frontier_pilot_launch.py"]["sha256"],
                      "approval_sha256": args.approval_sha256, "allocation_performed": False}
        elif args.check_job:
            require(args.source_commit is None, "job check accepts no source override")
            result = check_job_reservation(args.approval_sha256, args.check_job)
        else:
            result = launch(args.approval_sha256, submit=args.submit, expected_commit=args.source_commit)
        print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as error:
        print("frontier-launch: " + " ".join(str(error).split()), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
