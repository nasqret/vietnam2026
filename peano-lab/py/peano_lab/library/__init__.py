"""Checked theorem-ladder data and deterministic Lean 4 cross-check exports.

The library is untrusted: :mod:`theorems` replays scripts, packages checked
dependencies into self-contained kernel ``Cut`` nodes, and submits every
closed result to :mod:`peano_lab.kernel.checker` in one invocation.
"""
