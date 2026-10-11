"""Dependency-free migration tests. Never generate a proof or submit a job."""
import ast
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import package_sqrt2_power_wmi as package
import check_sqrt2_power_fresh_lean as fresh


class WmiMigrationTests(unittest.TestCase):
    def test_explicit_platform_inventory_preserves_all_six_pins(self):
        for platform, suffix in (("linux", ".so"), ("darwin", ".dylib")):
            names = fresh.toolchain_library_names(platform)
            self.assertEqual(names[:2], ("Init.olean", "Lean.olean"))
            self.assertEqual(len(names), 6)
            self.assertTrue(all(n.endswith(suffix) for n in names[2:]))
        with self.assertRaises(ValueError):
            fresh.toolchain_library_names("unknown")

    def test_relative_tool_paths_cannot_invoke_any_process(self):
        with tempfile.TemporaryDirectory() as folder:
            for kwargs in (dict(lean=Path("lean")), dict(lean_repo=Path("relative"))):
                with patch.object(fresh, "runtime", side_effect=AssertionError("must not execute")):
                    with self.assertRaises(ValueError):
                        fresh.execute(Path(folder)/"new", [Path(folder)], **kwargs)

    def test_exact_lean_checker_sources_remain_required(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/"PeanoLab").mkdir()
            for name in fresh.MODULES:
                (root/"PeanoLab"/(name+".lean")).write_bytes(b"changed")
            with patch.object(fresh, "runtime", side_effect=AssertionError("must not execute")):
                with self.assertRaisesRegex(ValueError, "checker sources changed"):
                    fresh.execute(root/"new", [root], lean_repo=root)

    def test_unsafe_member_names_are_rejected(self):
        for name in ("../escape", "/source/a", "source/../a", "source//a", "source/./a", "credentials/key"):
            with self.assertRaises(ValueError):
                package.safe_name(name)
        self.assertEqual(package.safe_name("source/scripts/a.py"), "source/scripts/a.py")

    def test_archive_bytes_are_deterministic_and_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder)/"a.tar", Path(folder)/"b.tar"
            with patch.object(package, "selected_files", return_value={"source/a.py": b"a\n"}):
                first, second = package.build_archive(a), package.build_archive(b)
                self.assertEqual(first, second)
                self.assertEqual(a.read_bytes(), b.read_bytes())
                with self.assertRaises(ValueError):
                    package.build_archive(a)

    def test_snapshot_mutation_and_symlink_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            stage = Path(folder)
            (stage/"source").mkdir()
            p = stage/"source/a.py"
            p.write_bytes(b"a\n")
            manifest = dict(schema=package.SCHEMA, case="AP090", files={"source/a.py": package.digest(b"a\n")})
            (stage/package.MANIFEST).write_bytes(package.canonical(manifest))
            self.assertEqual(package.verify_snapshot(stage)["files"], 1)
            p.write_bytes(b"b\n")
            with self.assertRaises(ValueError):
                package.verify_snapshot(stage)
            p.unlink()
            p.symlink_to(stage/package.MANIFEST)
            with self.assertRaises(ValueError):
                package.verify_snapshot(stage)

    def test_proof_producer_is_exactly_unchanged(self):
        raw = (package.ROOT/"scripts/sqrt2_power_fixed_half_log_root.py").read_bytes()
        self.assertEqual(sha256(raw).hexdigest(), package.PRODUCER_SHA256)

    def test_package_contains_transitive_library_imports_not_only_proof_pins(self):
        paths = package.runtime_library_paths(package.ROOT)
        for name in ("finite_factorial_theorems.py", "finite_permutation_theorems.py", "quadratic_residue_surface.py"):
            self.assertIn("peano-lab/py/peano_lab/library/" + name, paths)
        self.assertTrue(all(p.endswith(".py") and "__pycache__" not in p for p in paths))

    def test_collector_rejects_invalid_targets_before_network(self):
        import collect_sqrt2_power_wmi as collector
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(collector.subprocess, "run", side_effect=AssertionError("must not contact server")):
                for snapshot, job in (("../escape", "123"), ("0"*64, "1;false")):
                    with self.assertRaises(ValueError):
                        collector.collect(snapshot, job, Path(folder)/"new")
                with self.assertRaises(ValueError):
                    collector.collect("0"*64, "123", Path(folder))

    def test_local_profile_and_proof_limits_remain_unchanged(self):
        import run_sqrt2_power_wave as wave
        from dataclasses import asdict
        from sqrt2_power_binary_dag import BinaryDAGLimits
        self.assertEqual(wave.generation_phase_limits("AP090"), (28, 40))
        self.assertEqual(wave.replay_phase_limits("AP090"), (30, 40))
        self.assertEqual(wave.generation_phase_limits("AP090")[0]+wave.replay_phase_limits("AP090")[0]+2, 60)
        self.assertEqual(fresh.resource_settings("local"), dict(phases=dict(version=(1,3), build=(10,15),
            check=(20,30), negative=(5,10)), rss_bytes=768*1024**2, controller_base_wall=170))
        self.assertEqual(asdict(BinaryDAGLimits()), dict(max_value_bits=128, max_input_nodes=2048,
            max_nodes=4096, max_total_body_nodes=200000, max_depth=256, max_payload_bytes=8*1024**2))

    def test_larger_profile_requires_the_explicit_wmi_allocation(self):
        import sqrt2_power_wmi_resources as resources
        expected = dict(SLURM_JOB_ID="257999", SLURM_CPUS_PER_TASK="1", SLURM_JOB_PARTITION="cpu_idle",
            SLURM_MEM_PER_NODE="4096", SLURM_RESTART_COUNT="0", PEANO_SQRT2_SNAPSHOT_SHA256="a"*64)
        with patch.object(resources.sys, "platform", "linux"), patch.dict(resources.os.environ, expected, clear=True):
            resources.require_allocation()
            with patch.dict(resources.os.environ, {"SLURM_JOB_PARTITION":"cpu"}):
                resources.require_allocation()
            with patch.dict(resources.os.environ, {"SLURM_JOB_PARTITION":"gpu"}):
                with self.assertRaises(ValueError):resources.require_allocation()
            for key, value in (("SLURM_CPUS_PER_TASK","2"), ("SLURM_MEM_PER_NODE","2048"),
                    ("SLURM_RESTART_COUNT","1"), ("PEANO_SQRT2_SNAPSHOT_SHA256","bad")):
                with patch.dict(resources.os.environ, {key:value}):
                    with self.assertRaises(ValueError):
                        resources.require_allocation()
            with patch.object(resources.sys, "platform", "darwin"):
                with self.assertRaises(ValueError):
                    resources.require_allocation()
        with self.assertRaises(ValueError):
            fresh.resource_settings("unbounded")

    def test_wmi_profile_is_bounded_and_does_not_mutate_the_supervisor(self):
        import sqrt2_power_wmi_resources as resources
        from sqrt2_power_automation_baseline import runtime
        self.assertEqual(resources.HA_PHASE, (120,180))
        self.assertEqual(resources.WORKER_RSS_BYTES, 2*1024**3)
        self.assertEqual(resources.REQUESTED, dict(partition="cpu_idle",cpus=1,memory_mib=4096,wall_seconds=2700))
        for cpu, wall in (*resources.LEAN_PHASES.values(), resources.HA_PHASE, resources.PREFLIGHT_PHASE):
            runtime().ProcessLimits(cpu_seconds=cpu,wall_seconds=wall,rss_bytes=resources.WORKER_RSS_BYTES,output_bytes=8*1024**2)
        self.assertEqual(fresh.resource_settings(resources.NAME)["phases"],resources.LEAN_PHASES)
        snapshot=json.loads((package.ROOT/package.SOURCE_SNAPSHOT).read_bytes())["source_pins"]
        for name in ("training/peano_hydra/review_runtime.py","scripts/hydra_bounded_exec.py"):
            self.assertEqual(package.digest((package.ROOT/name).read_bytes()),snapshot[name])

    def test_wmi_launches_the_original_worker_and_replay_in_fresh_processes(self):
        import run_sqrt2_power_wmi as pilot
        tree=ast.parse(Path(pilot.__file__).read_bytes())
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="run_wmi_wave")
        constants={n.value for n in ast.walk(function) if isinstance(n,ast.Constant) and type(n.value) is str}
        self.assertTrue({"--worker","--replay","AP090","original_target_checked","empty_context",
            "false_target_rejected","forged_body_rejected"}<=constants)
        self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and
            isinstance(n.func.value,ast.Name) and n.func.value.id=="wave" and n.func.attr in {"worker","replay"}
            for n in ast.walk(function)))

    def test_lean_guard_only_accepts_the_single_threaded_configured_tool(self):
        import sqrt2_power_wmi_lean_guard as guard
        rss=2*1024**3
        command=[guard.LEAN_EXECUTABLE,"-j","1","--version"]
        guard.validate_request(5,rss,command)
        for cpu, memory, argv in ((0,rss,command),(121,rss,command),(True,rss,command),
                (5,rss//2,command),(5,rss,["/bin/echo","-j","1"]),
                (5,rss,[guard.LEAN_EXECUTABLE,"--version"]),
                (5,rss,[guard.LEAN_EXECUTABLE,"-j"]),
                (5,rss,[guard.LEAN_EXECUTABLE,"-j","2"]),
                (5,rss,command+["-j","1"]),(5,rss,command+["\x00"])):
            with self.assertRaises(ValueError):
                guard.validate_request(cpu,memory,argv)
        self.assertEqual(guard.LEAN_ADDRESS_SPACE_BYTES,16*1024**3)

    def test_lean_supervisor_is_private_and_keeps_the_original_enforcement(self):
        from sqrt2_power_automation_baseline import runtime
        from sqrt2_power_wmi_lean_runtime import lean_runtime
        baseline=runtime(); original_guard=baseline.GUARD
        lean=lean_runtime()
        self.assertIsNot(lean,baseline)
        self.assertEqual(baseline.GUARD,original_guard)
        self.assertEqual(lean.GUARD,package.ROOT/"scripts/sqrt2_power_wmi_lean_guard.py")
        self.assertEqual(lean.run_bounded.__code__.co_code,baseline.run_bounded.__code__.co_code)
        self.assertEqual(lean.validate_process_record.__code__.co_code,baseline.validate_process_record.__code__.co_code)
        self.assertIn("16-GiB virtual address",lean.RESOURCE_MEASUREMENT)
        self.assertNotIn("16-GiB",baseline.RESOURCE_MEASUREMENT)

    def test_lean_followup_never_invokes_proof_generation(self):
        import verify_sqrt2_power_wmi_lean as followup
        tree=ast.parse(Path(followup.__file__).read_bytes())
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
        self.assertFalse(any(isinstance(n.func,ast.Name) and n.func.id in {"run_wmi_wave","pilot","worker","replay"} for n in calls))
        literals={n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and type(n.value) is str}
        self.assertNotIn("--worker",literals)
        self.assertNotIn("--replay",literals)
        self.assertIn("258959",literals)
        raw=(package.ROOT/"scripts/submit_sqrt2_power_wmi_lean.sh").read_text()
        self.assertIn("258959|FAILED|1:0",raw)
        self.assertIn(followup.HA_REPORT_SHA256,raw)
        self.assertIn("authorization-AP090-lean-v1",raw)
        self.assertLess(raw.index("job-id.txt\"\n"),raw.index("scontrol release"))
        self.assertEqual(raw.count('sbatch --hold --parsable'),1)
        self.assertIn('"$snapshot" "$mode"',raw)

    def test_regressions_use_pinned_offline_dependencies_and_existing_certificates(self):
        import verify_sqrt2_power_wmi_regressions as regression
        self.assertEqual(len(regression.WHEELS),5)
        self.assertTrue(all(n.endswith("-py3-none-any.whl") and len(v)==64 for n,v in regression.WHEELS.items()))
        for path in regression.FILES:
            tree=ast.parse((package.ROOT/path).read_bytes())
            self.assertEqual(len([n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name.startswith("test_")]),13)
        constants={n.value for n in ast.walk(ast.parse(Path(regression.__file__).read_bytes()))
            if isinstance(n,ast.Constant) and type(n.value) is str}
        self.assertTrue({"--no-index","--no-deps","--no-compile","--target"}<=constants)
        self.assertFalse({"--worker","--replay"}&constants)

    def test_node_local_staging_has_digest_gate_and_exit_preservation(self):
        raw=(package.ROOT/"slurm/peano_wmi_sqrt2_pilot.sbatch").read_text()
        self.assertIn('sha256sum "$work/snapshot.tar"',raw)
        self.assertIn('trap preserve_results EXIT',raw)
        self.assertIn('PYTHONPATH="$work/source/peano-lab/py:$work/source/scripts"',raw)
        self.assertIn('--mem=4096M',raw)
        self.assertIn('--time=00:45:00',raw)

    def test_submission_records_held_job_before_release_and_never_requeues(self):
        raw = (package.ROOT/"scripts/submit_sqrt2_power_wmi.sh").read_text()
        self.assertIn('authorization-AP090-v1', raw)
        self.assertIn('authorization-AP090-v2', raw)
        self.assertIn('257867|FAILED|1:0', raw)
        self.assertIn("report['full_attempt_started'] is not False",raw)
        self.assertNotRegex(raw,r'(^|[;&\s])rm\s')
        self.assertEqual(raw.count('sbatch --hold --parsable'), 1)
        self.assertIn('--no-requeue', raw)
        self.assertLess(raw.index('job-id.txt'), raw.index('scontrol release'))
        self.assertIn('StrictHostKeyChecking=yes', raw)


if __name__ == "__main__":
    unittest.main()
