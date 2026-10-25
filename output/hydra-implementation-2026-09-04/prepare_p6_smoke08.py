"""Prepare a diagnosed follow-up, without submitting, releasing, or retrying it."""
from pathlib import Path
import ast
import hashlib
import json

HERE = Path(__file__).resolve().parent
OLD_SMOKE = "267e150ec3f1a432cb5c36a1864bbf1735d2866a04224cd654ae6c533f469bb4"
NEW_SMOKE = "cc8dec7bcb2187568c1aed1eaa1b580435460e297573b655eac2b32b74a271b4"


def replace_one(text, old, new):
    assert text.count(old) == 1, (old, text.count(old))
    return text.replace(old, new)


def write_script(name, text):
    tree = ast.parse(text, filename=name)
    # Parse embedded remote code too, without importing or executing it.
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "remote" for t in node.targets):
            ast.parse(ast.literal_eval(node.value), filename=name + ":remote")
    with (HERE / name).open("x") as stream:
        stream.write(text)
    return {"path": name, "sha256": hashlib.sha256(text.encode()).hexdigest(),
            "bytes": len(text.encode())}


def main():
    submitted = (HERE / "submit_p6_smoke_decoder_v2.py").read_text()
    submitted = submitted.replace("p6-smoke-4b-07", "p6-smoke-4b-08")
    submitted = submitted.replace("p6-transfer-05", "p6-transfer-06")
    submitted = submitted.replace("p6-source-bundle-05", "p6-source-bundle-06")
    submitted = submitted.replace("source-data-06", "source-data-07")
    submitted = replace_one(submitted, OLD_SMOKE, NEW_SMOKE)
    submitted = replace_one(submitted,
        "Separately sealed bundle05 with decoder-v2 and its two dependent helper pins, materialized as new source-data-07; all old archives, source trees and failures preserved",
        "Separately sealed bundle06 with unchanged decoder-v2 and the reviewed scheduler-v3 helper, materialized as new source-data-07; all old archives, source trees and failures preserved")
    old_diagnosis = "21909940 loaded actual4B and failed its first beam callback: Transformers4.53.3 supplies2*beam-width candidate rows. The versioned provider now checks that exact shape while charging only beam-width times decode iterations. Twenty-six pure decoder gates and sixteen controller gates passed; no native authority, vocab mask, training/data/limits changed. This new diagnosed allocation repeats the same one theorem, two calls and at most eight gradient examples with zero optimizer updates. Original failure and source bundle remain unchanged; no automatic retry."
    diagnosis = "Job21911045 failed before model admission on the old combined wall/output scheduler guard. The reviewed helper now permits one query up to15seconds and records the exact failure reason, without retries or changes to identity,64KiB output,64successful-query cap,allocation or outer deadlines. Its23pure tests passed. A separate actual CPU fixture must pass the same scheduler query and native positive/negative/owned-cleanup checks before this held submission. Decoder v2 still requires actual GPU validation. This new one-use600second allocation keeps the same one theorem,two model calls,eight gradient examples,and zero optimizer updates. Original attempts remain unchanged."
    submitted = replace_one(submitted, old_diagnosis, diagnosis)
    cpu_gate = '''    cpu_path = HERE / "p6-cpu-prerequisite-01.json"
    cpu_raw = cpu_path.read_bytes()
    cpu_gate = json.loads(cpu_raw)
    assert cpu_gate["schema"] == "hydra-p6-actual-cpu-prerequisite-v1"
    assert cpu_gate["scheduler_helper_sha256"] == "cc8dec7bcb2187568c1aed1eaa1b580435460e297573b655eac2b32b74a271b4"
    assert cpu_gate["completed"] and cpu_gate["positive_proof_replayed"]
    assert cpu_gate["negative_probe_rejected"] and cpu_gate["owned_cleanup_verified"]
    assert cpu_gate["actual_process_exit_code"] == 0 and cpu_gate["actual_scheduler_exit"] == "0:0"
    assert cpu_gate["actual_scheduler_query_exit_code"] == 0
    assert len(cpu_gate["evidence_files"]) >= 3
    for relative, digest in cpu_gate["evidence_files"].items():
        target = (HERE / relative).resolve()
        assert target.is_relative_to(HERE.resolve()) and target.is_file() and not target.is_symlink()
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
'''
    submitted = replace_one(submitted, "def main():\n", "def main():\n" + cpu_gate)
    submitted = replace_one(submitted, '        "provider_sha256":"7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f",',
        '        "provider_sha256":"7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f",\n'
        '        "cpu_prerequisite_sha256":hashlib.sha256(cpu_raw).hexdigest(),\n'
        '        "scheduler_helper_sha256":"' + NEW_SMOKE + '",')
    submitted = replace_one(submitted, "timeout=5)", "timeout=15)")

    released = (HERE / "release_p6_smoke_decoder_v2.py").read_text()
    released = released.replace("p6-smoke-4b-07", "p6-smoke-4b-08")
    released = replace_one(released, "['squeue','-h','-u'", "['squeue','--array','-h','-u'")
    released = released.replace("timeout=5)", "timeout=15)")
    released = replace_one(released, "timeout=40)", "timeout=60)")

    collected = (HERE / "collect_p6_smoke_decoder_v2.py").read_text()
    collected = collected.replace("p6-smoke-4b-07", "p6-smoke-4b-08")
    collected = replace_one(collected,
        "assert directory.name=='p6-smoke-4b-08' and job=='21911045'",
        "assert directory.name=='p6-smoke-4b-08'\n"
        "bound=directory/'reservation.json';assert bound.is_file() and not bound.is_symlink() and bound.stat().st_size<=32768\n"
        "reservation=json.loads(bound.read_bytes())\n"
        "assert reservation==request['reservation'] and reservation['job_id']==job and reservation['uid']==os.getuid()\n"
        "assert reservation['job_name']=='hydra-p6-smoke-4b-08' and reservation['seconds']==600")
    collected = replace_one(collected,
        'input=json.dumps({"directory":request["remote_job_directory"],"job_id":reservation["job_id"]}).encode()',
        'input=json.dumps({"directory":request["remote_job_directory"],"job_id":reservation["job_id"],"reservation":reservation}).encode()')
    collected = replace_one(collected, "timeout=5)", "timeout=15)")
    collected = replace_one(collected, "timeout=35)", "timeout=45)")
    outputs = [write_script("submit_p6_smoke_scheduler_v3.py", submitted),
               write_script("release_p6_smoke_scheduler_v3.py", released),
               write_script("collect_p6_smoke_scheduler_v3.py", collected)]
    record = {"schema":"hydra-smoke-launcher-derivation-v1", "attempt":"p6-smoke-4b-08",
              "source":"p6-source-bundle-06", "remote_source":"source-data-07",
              "status":"prepared_not_submitted", "cpu_prerequisite":"p6-cpu-prerequisite-01.json",
              "generated":outputs, "embedded_remote_syntax_checked":True,
              "allocations":0, "model_calls":0, "native_calls":0, "automatic_retry":False}
    with (HERE / "p6-smoke08-launch-preparation.json").open("x") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")
    print(json.dumps(record))


if __name__ == "__main__":
    main()
