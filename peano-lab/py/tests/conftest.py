"""Explicit historical presentation inputs; never substitute proof authority."""

from pathlib import Path
import sys

import pytest


@pytest.fixture(scope="module", autouse=True)
def frozen_second_wave_atlas_inputs(request):
    """Run the sealed v27 publication suite against its sealed v27 atlas.

    V28 has its own independent current-publication suite. Only these two
    historical input paths are selected; all original checks, negative tests,
    compiled Lean calls, and byte-for-byte output comparisons still run.
    """
    module = getattr(request.module, "__file__", None)
    expected = Path(__file__).with_name("test_constructive_second_wave_explorer.py").resolve()
    if module is None or Path(module).resolve() != expected:
        yield
        return
    root = Path(__file__).resolve().parents[3]
    if str(root / "scripts") not in sys.path:
        sys.path.insert(0, str(root / "scripts"))
    from upgrade_constructive_second_wave_publication_v28 import historical_presentation_context

    with historical_presentation_context():
        yield
