"""Repository-wide discovery of the exact historical graph observation fix.

Only the source-pinned historical graph cases are handled by this plugin;
all other pytest calls retain their existing implementations and fixtures.
"""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
for directory in (ROOT / "scripts", ROOT / "peano-lab/py"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from constructive_historical_graph_test_support import HistoricalGraphUIPlugin


def pytest_configure(config):
    config.pluginmanager.register(
        HistoricalGraphUIPlugin(), "reviewed-historical-graph-ui-v31",
    )
