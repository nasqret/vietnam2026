from pathlib import Path
import resource
import signal
import sys
import unittest

resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
signal.alarm(35)
root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root / "hydra-playground/tests"))
names = ["test_advice_memory", "test_vampire_cache", "test_vampire_runtime_accounting",
         "test_polynomial_chunks", "test_polynomial_continuations",
         "test_hybrid_search.NativeHybridTests.test_repeated_full_goals_do_not_spend_another_model_decode"]
suite = unittest.defaultTestLoader.loadTestsFromNames(names)
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
