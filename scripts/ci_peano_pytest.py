"""Bound pytest IDs for huge integer parameters, without changing test values.

Load explicitly with ``-p ci_peano_pytest`` and this directory on PYTHONPATH.
The native decimal-conversion guard stays untouched. Only exact built-in ints
larger than 512 bits receive an ID: even the smallest supported native guard
(640 decimal digits) is well above that threshold. Small values, bools, int
subclasses, other objects, and explicit pytest IDs keep their usual behavior.

Same-size integers may share a proposed ID; pytest makes those IDs unique.
There is no decimal conversion of parameter values, large hash, or proof change.
"""

from __future__ import annotations


_MAX_NATIVE_ID_BITS = 512


def pytest_make_parametrize_id(val: object) -> str | None:
    """Describe an exact large int using only its sign and bit length."""

    if type(val) is not int:
        return None
    bits = val.bit_length()
    if bits <= _MAX_NATIVE_ID_BITS:
        return None
    sign = "neg" if val < 0 else "pos"
    return f"int-{sign}-{bits}bits"
