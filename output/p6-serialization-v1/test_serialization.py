"""One metadata-only regression using the actual failed 1.7B run's inputs.

Loads only pinned stdlib-only configuration modules, not the dataset exporter,
native parser/checker, model, trainer execution, scheduler, or SSH transport.
Reconstructs the config representation created by prepare(); does not claim
that the failed process succeeded or that its saved adapter is admitted.
"""
from __future__ import annotations

import ast
import copy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
import types
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CAMPAIGN = ROOT / "output/hydra-implementation-2026-09-04"
FROZEN = CAMPAIGN / "p6-source-bundle-06/source"
OBSERVATION = CAMPAIGN / "p6-training-launchers-v2/attempts/p6-training-fresh-1.7b-v2-01/observation-013"
ERROR = "Returned training artifact differs from the saved manifest."


def pinned(path, expected):
    raw = path.read_bytes()
    if len(raw) > 256 * 1024 or hashlib.sha256(raw).hexdigest() != expected:
        raise AssertionError("Changed/oversized actual regression input: " + str(path))
    return raw


def metadata_module(name, path, expected):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(pinned(path, expected), str(path), "exec"), module.__dict__)
    return module


def comparison_guard(path, expected):
    """Execute only the actual require expression, never controller run()."""
    tree = ast.parse(pinned(path, expected), filename=str(path))
    matches = [node for node in ast.walk(tree)
               if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
               and isinstance(node.value.func, ast.Name) and node.value.func.id == "require"
               and len(node.value.args) == 2 and isinstance(node.value.args[1], ast.Constant)
               and node.value.args[1].value == ERROR]
    if len(matches) != 1:
        raise AssertionError("The actual artifact comparison must occur once.")
    return compile(ast.Module(body=matches, type_ignores=[]), str(path), "exec")


class ActualPreparedPlanSerialization(unittest.TestCase):
    def test_actual_tuple_plan_matches_only_its_unchanged_serialized_value(self):
        plan = json.loads(pinned(OBSERVATION / "job/result/prepared-plan.json",
            "2e2f9641c1febcd621b05ba80d06c3e90f3a8c6733fdcbc8d9d54815ef53792c"))
        disk = json.loads(pinned(OBSERVATION / "artifact/manifest.json",
            "3799c7d3212885667cd28f7ba6e9d8f9ffcd12bc90bd7d03d031b96a7325f135"))
        self.assertEqual(disk["plan"], plan)
        config_path = FROZEN / plan["config"]["path"]
        pinned(config_path, "807933e5625536fc2b6412e680010d1534cac7e94156e284ae3e63e87a047e27")
        self.assertEqual(plan["config_sha256"], hashlib.sha256(config_path.read_bytes()).hexdigest())

        # Namespace placeholders avoid running peano_policy/__init__.py. The two
        # loaded modules are byte-exact original configuration implementations.
        prefix = "hydra_serialization_metadata_only"
        try:
            for name in (prefix, prefix + ".peano_policy"):
                package = types.ModuleType(name)
                package.__path__ = []
                sys.modules[name] = package
            training = FROZEN / "hydra-playground/training-v5/hydra_training_v5"
            metadata_module(prefix + ".peano_policy.config", training / "peano_policy/config.py",
                "7cc7cd31a33000c5d09d90e8943c896b34b4dc289643feec90b483a442da5080")
            loader = metadata_module(prefix + ".pilot_config", training / "pilot_config.py",
                "8516bfdc9c79ab040bbd0a514ae7a3095ab7a1614a62b0920c0adaa433a710cb")
            config = loader.load_pilot_config(config_path)
            # Exact metadata construction from frozen decision_pilot.prepare().
            configuration = asdict(config)
            configuration["path"] = config.path.relative_to(FROZEN).as_posix()
        finally:
            for name in tuple(sys.modules):
                if name == prefix or name.startswith(prefix + "."):
                    del sys.modules[name]

        native_plan = copy.deepcopy(plan)
        native_plan["config"] = configuration
        artifact = copy.deepcopy(disk)
        artifact["plan"] = native_plan
        self.assertIsInstance(configuration["lora"]["target_modules"], tuple)
        self.assertIsInstance(disk["plan"]["config"]["lora"]["target_modules"], list)
        canonical = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"),
                                            ensure_ascii=False, allow_nan=False).encode()
        self.assertNotEqual(plan, native_plan)
        self.assertEqual(canonical(plan), canonical(native_plan))
        self.assertEqual(canonical(disk), canonical(artifact))

        def require(condition, message):
            if not condition:
                raise ValueError(message)

        old = comparison_guard(ROOT / "output/p6-scheduler-v3/remote_training_pilot.py",
            "41b97e63f09571071a75e1f1b01c6df8ab173783f596bc6ee1c3f3b0fab3c617")
        new = comparison_guard(HERE / "remote_training_pilot.py",
            "b0701a1c337fb33e904e6f721b450aa7d541b72ae38b2c2cfaf54e790bc192b7")
        environment = {"disk": disk, "artifact": artifact, "canonical": canonical, "require": require}
        with self.assertRaisesRegex(ValueError, "differs from the saved manifest"):
            exec(old, environment)
        exec(new, environment)
        # A real content change must still fail; this is not a skipped check.
        changed = copy.deepcopy(artifact)
        changed["plan"]["config"]["lora"]["alpha"] += 1
        with self.assertRaisesRegex(ValueError, "differs from the saved manifest"):
            exec(new, {**environment, "artifact": changed})
        self.assertIsInstance(artifact["plan"]["config"]["lora"]["target_modules"], tuple)
        self.assertFalse(any(name == "torch" or name.startswith(("peano_lab", "transformers"))
                             for name in sys.modules))


if __name__ == "__main__":
    unittest.main(verbosity=2)
