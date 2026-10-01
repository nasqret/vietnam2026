"""Source-only ownership checks: no imports, signals, subprocesses or proofs.

These regressions inspect the exact narrow signal-mask handoff. They are not
an execution test of OS scheduling or a substitute for a supervised smoke.
"""
from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "training/peano_hydra/review_runtime.py"
GUARD = ROOT / "scripts/hydra_bounded_exec.py"


def _function(path, name):
    module = ast.parse(path.read_text(), filename=str(path))
    matches = [node for node in module.body
               if isinstance(node, ast.FunctionDef) and node.name == name]
    assert len(matches) == 1
    return matches[0]


def _same(node, source):
    return ast.dump(node) == ast.dump(ast.parse(source, mode="eval").body)


def _call(node, source):
    return isinstance(node, ast.Call) and _same(node.func, source)


def _name(node, identifier):
    return isinstance(node, ast.Name) and node.id == identifier


def _handoff():
    function = _function(RUNTIME, "run_bounded")
    owners = [node for node in ast.walk(function) if isinstance(node, ast.Try)
              and node.body and isinstance(node.body[0], ast.Assign)
              and _call(node.body[0].value, "subprocess.Popen")]
    assert len(owners) == 1
    return function, owners[0]


def _mask_statement(node, operation, argument):
    assert isinstance(node, ast.Expr)
    assert _same(node.value, f"signal.pthread_sigmask(signal.{operation}, {argument})")


def test_only_sigalrm_is_blocked_immediately_before_cleanup_try():
    function, owner = _handoff()
    blocks = [node for node in ast.walk(function) if isinstance(node, ast.Assign)
              and _call(node.value, "signal.pthread_sigmask")]
    assert len(blocks) == 1
    block = blocks[0]
    assert len(block.targets) == 1 and _name(block.targets[0], "previous_signal_mask")
    assert _same(block.value, "signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})")
    containers = [node for node in ast.walk(function) if hasattr(node, "body")
                  and isinstance(node.body, list) and owner in node.body]
    assert len(containers) == 1
    siblings = containers[0].body
    index = siblings.index(owner)
    assert siblings[index - 1] is block
    initial = siblings[index - 2]
    assert isinstance(initial, ast.Assign)
    assert len(initial.targets) == 1 and _name(initial.targets[0], "process")
    assert _same(initial.value, "None")


def test_pending_alarm_delivery_follows_owned_assignment_inside_cleanup_try():
    _, owner = _handoff()
    assignment = owner.body[0]
    assert len(assignment.targets) == 1 and _name(assignment.targets[0], "process")
    _mask_statement(owner.body[1], "SIG_SETMASK", "previous_signal_mask")
    assert isinstance(owner.body[2], ast.While)
    assert len(owner.body) == 3


def test_spawn_still_owns_a_new_process_group_and_uses_the_guard():
    _, owner = _handoff()
    call = owner.body[0].value
    assert len(call.args) == 1 and _same(call.args[0], "guarded")
    keywords = {item.arg: item.value for item in call.keywords}
    assert _same(keywords["start_new_session"], "True")
    assert _same(keywords["cwd"], "cwd")
    assert _same(keywords["env"], "environment")


def test_alarm_and_spawn_failures_share_baseexception_cleanup():
    _, owner = _handoff()
    assert len(owner.handlers) == 1
    handler = owner.handlers[0]
    assert _same(handler.type, "BaseException")
    assert len(handler.body) == 2 and isinstance(handler.body[-1], ast.Raise)
    assert handler.body[-1].exc is None
    owned = handler.body[0]
    assert isinstance(owned, ast.If) and _same(owned.test, "process is not None")
    assert not owned.orelse
    assert _same(owned.body[0].value, "_kill_owned_group(process.pid)")
    waits = [node for node in ast.walk(owned) if _call(node, "os.wait4")]
    assert len(waits) == 1 and _same(waits[0], "os.wait4(process.pid, 0)")


def test_parent_mask_is_restored_even_when_spawn_or_cleanup_raises():
    _, owner = _handoff()
    assert len(owner.finalbody) == 1
    _mask_statement(owner.finalbody[0], "SIG_SETMASK", "previous_signal_mask")
    assert not owner.orelse


def test_runtime_has_no_additional_signal_mask_operations():
    function, _ = _handoff()
    calls = [node for node in ast.walk(function) if _call(node, "signal.pthread_sigmask")]
    assert len(calls) == 3


def test_guard_unblocks_only_sigalrm_immediately_before_exec():
    function = _function(GUARD, "main")
    calls = [node for node in ast.walk(function) if _call(node, "signal.pthread_sigmask")]
    assert len(calls) == 1
    assert _same(calls[0], "signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGALRM})")
    exec_statements = [node for node in function.body if isinstance(node, ast.Expr)
                       and _call(node.value, "os.execvpe")]
    assert len(exec_statements) == 1
    index = function.body.index(exec_statements[0])
    _mask_statement(function.body[index - 1], "SIG_UNBLOCK", "{signal.SIGALRM}")
    assert _same(exec_statements[0].value, "os.execvpe(command[0], command, os.environ)")


def test_guard_keeps_original_cpu_hard_margin_and_address_space_limits():
    function = _function(GUARD, "main")
    calls = [node for node in ast.walk(function) if _call(node, "resource.setrlimit")]
    assert len(calls) == 2
    expected = (
        "resource.setrlimit(resource.RLIMIT_CPU, (args.cpu_seconds, args.cpu_seconds + 1))",
        "resource.setrlimit(resource.RLIMIT_AS, (args.rss_bytes, args.rss_bytes))",
    )
    assert all(any(_same(node, source) for node in calls) for source in expected)
