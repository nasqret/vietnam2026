"""Derive a bounded, separately named CPU follow-up; no remote execution."""
from pathlib import Path
import ast
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREDECESSOR = HERE / "stage_p6_postsave_recovery_base3.py"
PACKAGE = HERE / "p6-postsave-recovery-v4"
DEST = HERE / "stage_p6_postsave_recovery_import4.py"
CONTINUATION = PACKAGE / "CONTINUATION.json"


def pin(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    assert pin(PREDECESSOR)["sha256"] == "a7f085f88024d5f61070a4f1e4fc2c864dea4674066f4b21b7576078633013ca"
    assert not DEST.exists() and not CONTINUATION.exists()
    source = PREDECESSOR.read_text()
    constants = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                constants[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    prepared = json.loads((PACKAGE / "PREPARED-GPU.json").read_bytes())
    prepared_sha = pin(PACKAGE / "PREPARED-GPU.json")["sha256"]
    new_pins = {row["destination"]: {key: row[key] for key in ("bytes", "sha256")}
                for row in prepared["new_remote_inputs"]}
    assert set(new_pins) == {"metadata_recovery_import4.py", "gpu_saved_reload_import4.py"}
    assert sum(row["bytes"] for row in new_pins.values()) == prepared["new_remote_input_total_bytes"]
    old_pins = dict(constants["OLD_INPUT_PINS"], **constants["PINS"])
    failures = dict(constants["PREVIOUS_FAILURE_PINS"])
    previous_output = HERE / "p6-postsave-metadata-base3-01/collect-001"
    for name in ("metadata-recovery-base3.json", "metadata-base3-invocation.json",
                 "metadata-base3-process-completion.json", "metadata-base3-stdout.txt", "metadata-base3-stderr.txt"):
        failures[name] = pin(previous_output / name)
    assert len(failures) == 15
    assert failures["metadata-recovery-base3.json"]["sha256"] == "f5005f9f660e58bb4d2847a57b63371ec4f0dea9786c9eddff447b94851bdae7"
    assert json.loads((previous_output / "metadata-base3-process-completion.json").read_bytes())["actual_metadata_process_exit_code"] == 1

    def once(old, new):
        nonlocal source
        assert source.count(old) == 1, (old[:100], source.count(old))
        source = source.replace(old, new)

    once(source[:source.index('from pathlib import Path')], '''"""Explicit import4 follow-up for the observed parser initialization failure.

This is a new, manually scheduled continuation under the user's standing Hydra
experiment authority. Packet02 and its approval remain exact prior evidence;
neither is rewritten or claimed to contain these new hashes. Only two new
CPU/GPU scripts are staged, with no overwrite, training, GPU allocation or
automatic retry by this driver. The prior three CPU failures stay unchanged.
Each actual invocation performs at most one SSH operation. Only a genuinely
successful CPU check permits a separately observed actual completion companion.
"""
''')
    source = source.replace('p6-postsave-recovery-v3', 'p6-postsave-recovery-v4')
    source = source.replace('p6-postsave-metadata-base3-01', 'p6-postsave-metadata-import4-01')
    source = source.replace('metadata_recovery_base3.py', 'metadata_recovery_import4.py')
    source = source.replace('gpu_saved_reload_base3.py', 'gpu_saved_reload_import4.py')
    source = source.replace('metadata-recovery-base3', 'metadata-recovery-import4')
    source = source.replace('metadata-actual-completion-base3', 'metadata-actual-completion-import4')
    source = source.replace('metadata-base3-', 'metadata-import4-')
    source = source.replace('base3-inference-runtime09', 'import4-inference-runtime09')
    source = source.replace('Base3', 'Import4')
    source = source.replace('Only the three new Import4 files', 'Only the two new import4 files')
    source = source.replace("'both_failed_cpu_attempts_unchanged':True", "'all_three_failed_cpu_attempts_unchanged':True")
    # Rebind complete literals after filename substitutions; old input names stay exact.
    for key, value in (("PREPARED_SHA", prepared_sha), ("PREDECESSOR_SHA", pin(PREDECESSOR)["sha256"]),
                       ("PINS", new_pins), ("OLD_INPUT_PINS", old_pins), ("PREVIOUS_FAILURE_PINS", failures)):
        tree = ast.parse(source)
        node = next(n for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == key for t in n.targets))
        lines = source.splitlines(keepends=True)
        lines[node.lineno - 1:node.end_lineno] = [key + " = " + repr(value) + "\n"]
        source = ''.join(lines)
    source = source.replace('160318', str(prepared['new_remote_input_total_bytes']))
    start = source.index('def validate_authority(request):')
    end = source.index('def stage_inputs(request):', start)
    source = source[:start] + '''def validate_authority(request):
 for key in ('continuation_sha256','driver_sha256'):
  require(type(request.get(key)) is str and re.fullmatch('[0-9a-f]{64}',request[key]),'Missing exact continuation identity')
 continuation_raw=base64.b64decode(request['continuation_base64'],validate=True)
 authority_raw=base64.b64decode(request['standing_authority_base64'],validate=True)
 approval_raw=base64.b64decode(request['prior_approval_base64'],validate=True)
 require(len(continuation_raw)<=16384 and len(authority_raw)<=8192 and len(approval_raw)<=8192,'Authority record bound')
 require(pin(continuation_raw)['sha256']==request['continuation_sha256'],'Continuation bytes differ')
 require(pin(authority_raw)['sha256']=='90104131a70120cb8c735dd8b2390986111bf90283441f5b8e1c025b105e5f62','Standing authority differs')
 require(pin(approval_raw)['sha256']=='08f5191195e577a466664d5f1c5825768bdc7d166d6a40e96cdb218514307d0e','Prior approval evidence differs')
 continuation=json.loads(continuation_raw);approval=json.loads(approval_raw)
 require(type(continuation) is dict and continuation.get('schema')=='hydra-p6-postsave-import4-continuation-v1'
  and continuation.get('recovery_prepared_sha256')==PREPARED_SHA
  and continuation.get('runtime_manifest_sha256')==RUNTIME_MANIFEST_SHA
  and continuation.get('cpu_driver_sha256')==request['driver_sha256']
  and continuation.get('new_user_approval_claimed') is False
  and continuation.get('automatic_retry') is False,'Continuation does not bind this exact separately revised follow-up')
 require(continuation.get('new_remote_input_pins')==PINS and continuation.get('previous_failed_output_pins')==PREVIOUS_FAILURE_PINS,
  'Continuation input or preserved failure pins differ')
 require(type(approval) is dict and approval.get('status')=='approved_by_user'
  and approval.get('pending_action_sha256')=='716d01952c5af9cdbe7b35754f9c4d5df3f727ff4d2609bc19936496781857ed',
  'Previously approved source09 workflow provenance differs')
''' + source[end:]
    start = source.index('    parser.add_argument("phase",')
    end = source.index('    if args.phase == "stage":', start)
    source = source[:start] + '''    parser.add_argument("phase", choices=("preflight", "stage", "verify", "collect", "stage-actual"))
    parser.add_argument("--continuation-sha256", required=True, help="Exact diagnosed follow-up record, not a new approval.")
    parser.add_argument("--index", type=int, default=1)
    parser.add_argument("--actual-sha256")
    args = parser.parse_args(argv)
    ast.parse(REMOTE)
    assert re.fullmatch(r"[0-9a-f]{64}", args.continuation_sha256)
    continuation_raw = read(PACKAGE / "CONTINUATION.json", args.continuation_sha256, 16384)
    authority_raw = read(ROOT / "HYDRA_EXPERIMENT_AUTHORITY.md", "90104131a70120cb8c735dd8b2390986111bf90283441f5b8e1c025b105e5f62", 8192)
    approval_raw = read(REVIEW / "USER_APPROVAL.json", "08f5191195e577a466664d5f1c5825768bdc7d166d6a40e96cdb218514307d0e", 8192)
    read(REVIEW / "PENDING_ACTION.json", "716d01952c5af9cdbe7b35754f9c4d5df3f727ff4d2609bc19936496781857ed", 16384)
    continuation, approval = json.loads(continuation_raw), json.loads(approval_raw)
    driver_sha = hashlib.sha256(read(__file__)).hexdigest()
    assert continuation["schema"] == "hydra-p6-postsave-import4-continuation-v1"
    assert continuation["recovery_prepared_sha256"] == PREPARED_SHA
    assert continuation["runtime_manifest_sha256"] == RUNTIME_MANIFEST_SHA
    assert continuation["cpu_driver_sha256"] == driver_sha and continuation["new_user_approval_claimed"] is False
    assert continuation["automatic_retry"] is False
    assert continuation["new_remote_input_pins"] == PINS and continuation["previous_failed_output_pins"] == PREVIOUS_FAILURE_PINS
    assert approval["status"] == "approved_by_user" and approval["pending_action_sha256"] == "716d01952c5af9cdbe7b35754f9c4d5df3f727ff4d2609bc19936496781857ed"
    prepared = json.loads(read(PACKAGE / "PREPARED-GPU.json", PREPARED_SHA))
    assert prepared["schema"] == __PREPARED_SCHEMA__
    assert prepared["new_remote_input_total_bytes"] == __PAYLOAD_BYTES__
    assert {row["destination"]: {key: row[key] for key in ("bytes", "sha256")}
            for row in prepared["new_remote_inputs"]} == PINS
    for row in prepared["new_remote_inputs"]:
        path = ROOT / row["path"]
        assert path.parent == PACKAGE and len(read(path, row["sha256"])) == row["bytes"]
    request = {"phase": args.phase, "continuation_sha256": args.continuation_sha256,
        "driver_sha256": driver_sha, "continuation_base64": base64.b64encode(continuation_raw).decode(),
        "standing_authority_base64": base64.b64encode(authority_raw).decode(),
        "prior_approval_base64": base64.b64encode(approval_raw).decode(),
        "environment_revision": "el8-libffi-env2", "recovery_revision": "import4-inference-runtime09",
        "predecessor_driver_sha256": PREDECESSOR_SHA}
    if args.phase == "preflight":
        assert args.index == 1 and args.actual_sha256 is None
        print(json.dumps({"preflight": True, "driver_sha256": driver_sha,
            "remote_script_sha256": hashlib.sha256(REMOTE.encode()).hexdigest(),
            "continuation_sha256": args.continuation_sha256, "new_remote_inputs": PINS,
            "payload_bytes": prepared["new_remote_input_total_bytes"], "prior_failed_files_preserved": len(PREVIOUS_FAILURE_PINS),
            "ssh_calls": 0, "cpu_verifications": 0, "gpu_allocations": 0, "model_calls": 0}))
        return 0
''' + source[end:]
    source = source.replace('__PREPARED_SCHEMA__', repr(prepared['schema'])).replace('__PAYLOAD_BYTES__', str(prepared['new_remote_input_total_bytes']))
    ast.parse(source)
    with DEST.open('x') as stream:
        stream.write(source)
    continuation = {"schema": "hydra-p6-postsave-import4-continuation-v1",
        "status": "prepared_explicit_diagnosed_followup_under_standing_authority",
        "new_user_approval_claimed": False, "automatic_retry": False,
        "purpose": "Initialize and verify the authenticated native-v7 package before data preparation; retain the strict app-only import guard.",
        "authority": {"path": "HYDRA_EXPERIMENT_AUTHORITY.md", **pin(ROOT / 'HYDRA_EXPERIMENT_AUTHORITY.md')},
        "prior_specific_approval": {"path": "output/hydra-implementation-2026-09-04/p6-upload-review-02/USER_APPROVAL.json", **pin(HERE / 'p6-upload-review-02/USER_APPROVAL.json')},
        "prior_packet_unchanged": {"path": "output/hydra-implementation-2026-09-04/p6-upload-review-02/PENDING_ACTION.json", **pin(HERE / 'p6-upload-review-02/PENDING_ACTION.json')},
        "prior_cpu_failure": {"actual_exit_code": 1, "completion_chunk": "4370cc",
            "evidence": "p6-postsave-metadata-base3-01/verify/actual-tool-completion.json",
            "error": "Recovery imported training/native/provider code outside the new runtime tree.",
            "diagnosis_basis": "Source inspection: NativeIdentity selected the same-runtime frozen fallback before native-v7 initialization; not an actual import trace."},
        "recovery_prepared_sha256": prepared_sha, "runtime_manifest_sha256": constants['RUNTIME_MANIFEST_SHA'],
        "cpu_driver_sha256": pin(DEST)['sha256'], "predecessor_driver_sha256": pin(PREDECESSOR)['sha256'],
        "new_remote_input_pins": new_pins, "new_remote_input_total_bytes": prepared['new_remote_input_total_bytes'],
        "existing_remote_input_pins": old_pins, "previous_failed_output_pins": failures,
        "remote_package": prepared['remote_package'], "source09_and_combined02_transfers_already_completed": True,
        "cpu_verification_invocations": 1, "cpu_limits": {"cpu_seconds": 90, "wall_seconds": 120, "address_space_bytes": 2147483648},
        "gpu_allocations_by_this_driver": 0, "conditional_saved_reload_allocation": prepared['allocation'],
        "gpu_prerequisite": "Actual new successful CPU report and root-observed completion companion; no failed CPU result admits a GPU.",
        "training_or_generation_or_native_proof_execution": False,
        "native_formula_parsing_performed_by_cpu_admission": True,
        "overwrite_existing_inputs_outputs_or_weights": False}
    assert len(json.dumps(continuation).encode()) <= 16384
    with CONTINUATION.open('x') as stream:
        stream.write(json.dumps(continuation, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'driver': pin(DEST), 'continuation': pin(CONTINUATION), 'new_files': len(new_pins),
                      'new_bytes': prepared['new_remote_input_total_bytes'], 'remote_operations': 0}))


if __name__ == '__main__':
    main()
