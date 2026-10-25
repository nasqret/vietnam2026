"""Derive fresh one-use smoke08 transport scripts; never import or launch them."""
from pathlib import Path
import ast
import hashlib
import json

HERE = Path(__file__).resolve().parent


def change(text, before, after, count=1):
    assert text.count(before) == count, (before, text.count(before), count)
    return text.replace(before, after)


def save(name, text):
    ast.parse(text, filename=name)
    with (HERE / name).open("x") as stream:
        stream.write(text)
    return {"path": name, "bytes": len(text.encode()),
            "sha256": hashlib.sha256(text.encode()).hexdigest()}


def main():
    bundle = HERE / "p6-source-bundle-06"
    expected = {
        "manifest.json": "e1f5518231eaa04469d39c830bd480ec11ff4ed891907772d48aeab67da18f96",
        "source-data.tar.gz": "aa0a66ee80f5710e0a42a33805a34cd085be3bb083b06baa066b6954d2f3fbf5",
        "training-launch-inputs.json": "6ae22bd1075f7e83ad1ff427dbe468eeb5e38f30619e98ea7fcc71d48aae6e88",
        "local-seal.json": "fe2b602d75c6e2c9a3227bdfc7783717ea6cc546407b1614211322f17071e79b",
    }
    for relative, digest in expected.items():
        assert hashlib.sha256((bundle / relative).read_bytes()).hexdigest() == digest
    manifest = json.loads((bundle / "manifest.json").read_bytes())
    original = json.loads((HERE / "p6-source-bundle-05/manifest.json").read_bytes())
    changed = {name for name in manifest["files"]
               if manifest["files"][name] != original["files"][name]}
    assert changed == {"output/p6-prototype/remote_provider_smoke.py",
                       "output/p6-prototype/remote_training_pilot.py"}
    for name in ("prepared-plans.json", "prepared-qwen3-1.7b-base.json",
                 "prepared-qwen3-4b-base.json", "prepared-qwen3-8b-base.json"):
        assert (bundle / name).read_bytes() == (HERE / "p6-source-bundle-05" / name).read_bytes()

    stage = (HERE / "stage_p6_decoder_v2.py").read_text()
    stage = change(stage, "separately sealed decoder-v2 bundle", "separately sealed scheduler-v3 bundle")
    stage = change(stage, 'BUNDLE = HERE / "p6-source-bundle-05"', 'BUNDLE = HERE / "p6-source-bundle-06"')
    stage = change(stage, 'OUT = HERE / "p6-transfer-05"', 'OUT = HERE / "p6-transfer-06"')
    stage = change(stage, 'CHANGED = {"hydra-playground/experimental_model.py",\n           ', 'CHANGED = {')
    stage = stage.replace("source-data-06", "source-data-07")
    stage = change(stage, 'HERE / "p6-source-bundle-04/manifest.json"', 'HERE / "p6-source-bundle-05/manifest.json"')
    stage = change(stage, "Only the reviewed decoder callback fix and its two dependent controller pins; original inputs, configs and data remain identical.",
                   "Only the reviewed 15-second scheduler-query guard and its dependent trainer pin; provider v2, prepared plans, configs and data remain byte-identical to bundle05.")
    stage = change(stage, "'decoder_revision':'beam-callback-accounting-v2'", "'decoder_revision':'beam-callback-accounting-v2','scheduler_revision':'bounded-query-v3'")
    stage = change(stage, '    manifest = json.loads(manifest_raw)\n',
                   '    assert hashlib.sha256(manifest_raw).hexdigest() == "e1f5518231eaa04469d39c830bd480ec11ff4ed891907772d48aeab67da18f96"\n'
                   '    manifest = json.loads(manifest_raw)\n'
                   '    assert manifest["archive_sha256"] == "aa0a66ee80f5710e0a42a33805a34cd085be3bb083b06baa066b6954d2f3fbf5"\n')

    generated = [save("stage_p6_scheduler_v3.py", stage)]
    receipt = {"schema": "hydra-smoke-launcher-derivation-v1", "phase": "transport_only",
               "sealed_bundle": str(bundle.relative_to(HERE)), "bundle_pins": expected,
               "payload_changes": sorted(changed), "generated": generated,
               "application_imports": 0, "model_calls": 0, "native_calls": 0,
               "uploads": 0, "allocations": 0, "automatic_retry": False}
    with (HERE / "p6-scheduler-v3-launch-preparation.json").open("x") as stream:
        json.dump(receipt, stream, indent=2)
        stream.write("\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
