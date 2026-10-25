"""Exercise the real scheduling functions without importing the native engine.

Only selected function ASTs are compiled. Nonlocal bindings become test-module
globals; their bodies and scheduling decisions are otherwise unchanged. These
fixtures check ordering/accounting, not theorem search or mathematical validity.
"""
import ast
import copy
import math
from pathlib import Path
import time
from types import SimpleNamespace
import unittest


APP = Path(__file__).resolve().parents[1]


class _Bindings(ast.NodeTransformer):
    def visit_Nonlocal(self, node):
        return ast.copy_location(ast.Global(names=node.names), node)


def scheduling_fixture(ranker=None, *, maximum=3):
    parsed = ast.parse((APP / "hybrid_search.py").read_text())
    search = next(node for node in parsed.body if isinstance(node, ast.FunctionDef) and node.name == "search")
    names = {"rank_score", "priority", "put"}
    bodies = [_Bindings().visit(copy.deepcopy(node)) for node in search.body
              if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in bodies} != names:
        raise AssertionError("The intended pure search scheduling functions changed.")
    loop = next(node for node in search.body if isinstance(node, ast.While))
    index = next(i for i, node in enumerate(loop.body) if isinstance(node, ast.AugAssign)
                 and isinstance(node.target, ast.Name) and node.target.id == "frontier_turn")
    selection = copy.deepcopy(loop.body[index:index + 2])
    if not isinstance(selection[1], ast.If):
        raise AssertionError("The intended frontier-choice block changed.")
    choose = ast.FunctionDef(name="choose", args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[],
        kw_defaults=[], defaults=[]), body=[ast.Global(names=["frontier_turn"]), *selection,
        ast.Return(value=ast.Name(id="node", ctx=ast.Load()))], decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[*bodies, choose], type_ignores=[]))
    events = []
    environment = {"math": math, "time": time, "branch_ranker": ranker,
        "ranker_scores": {}, "ranker_counts": {"scored_states": 0, "declined_states": 0},
        "ranker_seconds": 0.0, "note": lambda *args: events.append(args),
        "strengthened_nodes": set(), "counts": {"strengthening_expansions": 0, "frontier_peak": 0},
        "continuations": {}, "planned_continuations": {}, "ring_failed_nodes": set(),
        "completed_macro_prefixes": set(), "frontier": {}, "frontier_turn": 0,
        "limits": SimpleNamespace(max_frontier=maximum, heuristic_burst=4),
        "polynomial_records": [], "planner_records": [], "limited_reasons": set(), "events": events}
    exec(compile(module, str(APP / "hybrid_search.py") + "::<pure scheduling>", "exec"), environment)
    return environment


def node(identifier, *, goals=("a : ℕ ⊢ a = a",), depth=3, arithmetic_rank=2):
    return SimpleNamespace(id=identifier, goals=goals, depth=depth, arithmetic_rank=arithmetic_rank)


class RankerSchedulingTests(unittest.TestCase):
    def test_disabled_ranker_preserves_exact_deterministic_tuple(self):
        fixture = scheduling_fixture()
        value = node(7, goals=("⊢ 0 = 0", "⊢ 1 = 1"))
        self.assertEqual(fixture["priority"](value),
            (True, False, True, 2, 2, sum(map(len, value.goals)), 3, 7))
        self.assertIsNone(fixture["rank_score"](value))
        self.assertEqual(fixture["ranker_counts"], {"scored_states": 0, "declined_states": 0})

    def test_callback_receives_all_ordered_obligations_and_only_observed_fields(self):
        received = []
        ranker = SimpleNamespace(callback=lambda **kwargs: received.append(kwargs) or 1.25)
        fixture = scheduling_fixture(ranker)
        value = node(1, goals=("a : ℕ ⊢ a = a", "b : ℕ ⊢ b + 0 = b"), depth=7)
        self.assertEqual(fixture["rank_score"](value), 1.25)
        self.assertEqual(fixture["rank_score"](value), 1.25)
        fixture["rank_score"](node(2, goals=tuple(reversed(value.goals)), depth=7))
        self.assertEqual(len(received), 2)
        self.assertEqual(received[0], {"all_goals": value.goals, "depth": 7,
                                      "proof_cost": None, "remaining_budget": None})
        self.assertEqual(received[1]["all_goals"], tuple(reversed(value.goals)))
        self.assertEqual(fixture["ranker_counts"]["scored_states"], 2)

    def test_continuation_and_strengthening_tiers_precede_learned_score(self):
        ranker = SimpleNamespace(callback=lambda **kwargs: float(kwargs["depth"]))
        fixture = scheduling_fixture(ranker)
        continuation, ordinary = node(10, depth=20), node(11, depth=0)
        fixture["continuations"][continuation.id] = SimpleNamespace(plan_id=0)
        self.assertLess(fixture["priority"](continuation), fixture["priority"](ordinary))
        fixture["continuations"].clear()
        fixture["strengthened_nodes"].add(continuation.id)
        self.assertLess(fixture["priority"](continuation), fixture["priority"](ordinary))
        fixture["counts"]["strengthening_expansions"] = 8
        self.assertGreater(fixture["priority"](continuation), fixture["priority"](ordinary))

    def test_invalid_score_declines_once_without_removing_the_obligation(self):
        fixture = scheduling_fixture(SimpleNamespace(callback=lambda **kwargs: float("nan")))
        value = node(3, goals=("⊢ 0 = 1",))
        fixture["put"](value)
        self.assertIsNone(fixture["rank_score"](value))
        self.assertIsNone(fixture["rank_score"](value))
        self.assertIs(fixture["frontier"][3], value)
        self.assertEqual(value.goals, ("⊢ 0 = 1",))
        self.assertEqual(fixture["ranker_counts"]["declined_states"], 1)
        self.assertEqual(len(fixture["events"]), 1)

    def test_frontier_pruning_keeps_oldest_and_records_resource_loss(self):
        fixture = scheduling_fixture(SimpleNamespace(callback=lambda **kwargs: kwargs["depth"]), maximum=2)
        values = [node(1, depth=20), node(2, depth=10), node(3, depth=0)]
        for value in values:
            fixture["put"](value)
        self.assertEqual(set(fixture["frontier"]), {1, 3})
        self.assertIn("max_frontier", fixture["limited_reasons"])
        self.assertEqual(fixture["counts"]["frontier_peak"], 2)

    def test_fourth_frontier_turn_serves_oldest_even_with_worst_score(self):
        fixture = scheduling_fixture(SimpleNamespace(callback=lambda **kwargs: kwargs["depth"]), maximum=5)
        for identifier, depth in ((1, 20), (2, 0), (3, 1), (4, 2), (5, 3)):
            fixture["put"](node(identifier, depth=depth))
        chosen = [fixture["choose"]().id for _ in range(4)]
        self.assertEqual(chosen, [2, 3, 4, 1])
        self.assertEqual(set(fixture["frontier"]), {5})


if __name__ == "__main__":
    unittest.main()
