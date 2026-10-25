"""Seal an inference-only source derivative; never run application or model code.

The old training source, plans and artifacts remain original evidence. Only the
experimental provider changes. A later verifier must distinguish its runtime
plan from the preserved original training plan; this is not a training bundle.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import importlib.util
import json
import resource
import signal
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = HERE / "p6-source-bundle-06"
OUT = HERE / "p6-source-bundle-08"
PROVIDER = "hydra-playground/experimental_model.py"
REPLACEMENT = ROOT / "output/p6-offline-base-identity-v1/experimental_model.py"
PINS = {
    "manifest.json": "e1f5518231eaa04469d39c830bd480ec11ff4ed891907772d48aeab67da18f96",
    "actual-completion.json": "510fd1e3f1871e59f98c16e362bac9a88dd77bb860e9a6c991b9d959e616cb9f",
    "local-seal.json": "fe2b602d75c6e2c9a3227bdfc7783717ea6cc546407b1614211322f17071e79b",
}
HELPER_SHA = "1c22c1a48ab0f647da5565fd8776c383480be0381e4eb4a254c45862cfe72b99"
OLD_PROVIDER_SHA = "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replacement-sha256", required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--review-sha256", required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, (60, 75))
    resource.setrlimit(resource.RLIMIT_FSIZE, (128 * 1024**2, 128 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    signal.alarm(120)
    began = time.monotonic()
    helper_path = HERE / "build_p6_bundle_06.py"
    assert hashlib.sha256(helper_path.read_bytes()).hexdigest() == HELPER_SHA
    spec = importlib.util.spec_from_file_location("_inference_bundle_file_helpers", helper_path)
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    b.OLD, b.OUT, b.SOURCE = OLD, OUT, OUT / "source"
    require, canonical, descriptor = b.require, b.canonical, b.descriptor
    require(not OUT.exists(), "This inference revision already exists.")
    for name, expected in PINS.items():
        require(descriptor(OLD / name)["sha256"] == expected, "Original bundle pin changed: " + name)
    old = json.loads((OLD / "manifest.json").read_bytes())
    actual = json.loads((OLD / "actual-completion.json").read_bytes())
    require(actual["actual_exit_code"] == 0 and actual["completed"] is True,
            "Original source build was not actually completed.")
    files_before = b.inventory(OLD / "source")
    require(files_before == old["files"] and len(files_before) == 1206,
            "Original complete inventory changed.")
    require(files_before[PROVIDER]["sha256"] == OLD_PROVIDER_SHA,
            "Wrong original training provider.")
    require(descriptor(OLD / "source-data.tar.gz") ==
            {"bytes": old["archive_bytes"], "sha256": old["archive_sha256"]}, "Original archive changed.")
    replacement = descriptor(REPLACEMENT)
    require(replacement["sha256"] == args.replacement_sha256, "Reviewed provider changed.")
    review = descriptor(args.review.resolve(), with_path=True)
    require(review["sha256"] == args.review_sha256, "Provider review record changed.")
    profile = b.literal(ast.parse(REPLACEMENT.read_bytes()), "PROFILE")
    require(profile != old["provider_profile"] and profile == "hydra-experimental-torch-qwen3-v3",
            "The new inference provider must report its separate identity.")
    old_scope = json.loads((OLD / "controller-source-pins.json").read_bytes())
    require(len(old_scope) == 585 and hashlib.sha256(canonical(old_scope)).hexdigest() ==
            "11aa82af08bce4369747ddc153a8d0b334243f69d497b16267a7151d0b62513c"
            and all(files_before[k] == v for k, v in old_scope.items()), "Original execution scope changed.")
    OUT.mkdir(mode=0o700)
    b.SOURCE.mkdir(mode=0o700)
    for name in files_before:
        incoming = REPLACEMENT if name == PROVIDER else OLD / "source" / name
        destination = b.SOURCE / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with incoming.open("rb") as src, destination.open("xb") as dst:
            while chunk := src.read(b.BLOCK):
                dst.write(chunk)
        destination.chmod(0o444)
    files = b.inventory(b.SOURCE)
    require(set(files) == set(files_before)
            and {k for k in files if files[k] != files_before[k]} == {PROVIDER}
            and files[PROVIDER] == replacement, "More than the reviewed provider changed.")
    scope = {name: files[name] for name in old_scope}
    scope_sha = hashlib.sha256(canonical(scope)).hexdigest()
    b.save("controller-source-pins.json", scope)
    b.save("original-training-source-pins.json", old_scope)
    original_plans = {}
    for key in b.MODELS:
        name = "prepared-" + key + ".json"
        incoming = OLD / name
        raw = incoming.read_bytes()
        plan = json.loads(raw)
        require(hashlib.sha256(canonical({k: v for k, v in plan.items() if k != "plan_sha256"})).hexdigest()
                == plan["plan_sha256"], "Original plan hash changed.")
        require(all(files_before[k]["sha256"] == v for k, v in plan["source_pins"].items()),
                "Original plan no longer matches original training source.")
        target = OUT / ("original-" + name)
        with target.open("xb") as stream:
            stream.write(raw)
        require(target.read_bytes() == raw, "Original plan copy changed.")
        original_plans[key] = {**descriptor(target, with_path=True), "plan_sha256": plan["plan_sha256"],
                               "is_runtime_prepared_plan": False}
    with (OUT / "source-data.tar.gz").open("xb") as stream:
        archive = b.archive(files, stream)
    require(archive == b.archive(files), "Deterministic archive regeneration differed.")
    b.verify_archive(files)
    zero_work = {"application_modules_imported": 0, "model_calls": 0, "native_proof_replays": 0,
        "tokenizers_loaded": 0, "training_performed": False, "automatic_launch": False,
        "automatic_retry": False, "gpu_allocations": 0, "uploads": 0}
    manifest = {"schema": "hydra-exact-source-data-bundle-v3", **archive, "file_count": len(files),
        "expanded_bytes": sum(v["bytes"] for v in files.values()), "files": files,
        "derived_from": {"path": str(OLD.relative_to(ROOT)), "manifest_sha256": PINS["manifest.json"],
                         "actual_completion_sha256": PINS["actual-completion.json"], "unchanged_files": 1205},
        "changed_files": {PROVIDER: {"before": files_before[PROVIDER], "after": files[PROVIDER],
                                     "replacement_source": str(REPLACEMENT.relative_to(ROOT))}},
        "added_files": {}, "removed_files": [], "provider_sha256": args.replacement_sha256,
        "provider_profile": profile, "runner_sha256": old["runner_sha256"],
        "training_controller_sha256": old["training_controller_sha256"],
        "controller_source_pins_sha256": scope_sha,
        "original_training_source_pins_sha256": old["controller_source_pins_sha256"],
        "dataset_manifest_sha256": old["dataset_manifest_sha256"], "inference_only": True,
        "training_execution_allowed": False, "training_launch_inputs_issued": False,
        "original_training_plans": original_plans, "runtime_plans_regenerated": False,
        "provider_review": review, "preparation_mode": "authenticated_offline_base_inference_revision", **zero_work}
    b.save("manifest.json", manifest)
    require(b.inventory(OLD / "source") == files_before and b.inventory(b.SOURCE) == files,
            "Original or derived files changed during build.")
    result = {"schema": "hydra-inference-source-derived-build-v1", "completed": True,
        "original_bundle_unchanged": True, "only_changed_source": PROVIDER,
        "manifest": descriptor(OUT / "manifest.json", with_path=True),
        "controller_source_pins_sha256": scope_sha, "archive": archive,
        "elapsed_seconds": time.monotonic() - began, **zero_work}
    b.save("build-result.json", result)
    for path in b.SOURCE.rglob("*"):
        if path.is_dir():
            path.chmod(0o555)
    b.SOURCE.chmod(0o555)
    signal.alarm(0)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
