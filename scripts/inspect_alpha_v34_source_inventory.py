#!/usr/bin/env python3
"""Bounded source-only inspection; neither proof acceptance nor admission."""
from __future__ import annotations
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import resource
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "peano-lab/py"))

def main():
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    started = time.monotonic()
    from peano_lab.library import campaign_research_v34_closure as provider
    from peano_lab.library.theorems import TheoremSpec
    from peano_lab.library.campaign_lower_layer_closure import _specs_digest
    owners = list(provider.FACTORIES)
    if not any(owner.module == "linear_congruence_classification_candidate" for owner in owners):
        owners.append(provider.ResearchFactory(
            "congruence-arithmetic", "linear_congruence_classification_candidate",
            "make_linear_congruence_classification_candidate_theorems",
            "linear-congruence-classification-rfc-v1.md", 18128,
            "12b1a98ce830704485f1ea78475fba8b10e39031ffbef00b1b5dfc8ffdef7f47",
            12, "b1128492a1dd801ec81f63a39f586f733e95b79a1d2a19d33bb0363130d560c8",
            "test_campaign_research_v34_closure.py"))
    rows, records = [], []
    for owner in owners:
        path = ROOT / owner.source
        payload = path.read_bytes()
        if (len(payload), sha256(payload).hexdigest()) != (owner.source_bytes, owner.source_sha256):
            raise ValueError("current mathematical bytes differ: " + owner.module)
        module = import_module("peano_lab.library." + owner.module)
        factory = getattr(module, owner.factory)
        if not Path(module.__file__).samefile(path) or factory.__module__ != module.__name__:
            raise ValueError("foreign canonical factory")
        values = factory(TheoremSpec)
        if type(values) is not tuple or len(values) != owner.count or _specs_digest(values) != owner.specs_sha256:
            raise ValueError("actual specifications differ for " + owner.module
                             + ": " + _specs_digest(values))
        rows.extend(values)
        records.append({"module":owner.module, "count":len(values),
            "names":[row.name for row in values], "specs_sha256":_specs_digest(values)})
    if any(name.startswith("peano_lab.library.editions") for name in sys.modules):
        raise ValueError("source inspection imported a full edition")
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    if peak > 1536 * 1024 * 1024:
        raise ValueError("original RSS ceiling exceeded")
    metadata = tuple(tuple(getattr(owner, key) for key in provider._FACTORY_FIELDS) for owner in owners)
    print(json.dumps({"schema":"alpha-v34-exact-new-source-inventory-v1",
        "proof_calls":0,"admission_performed":False,"count":len(rows),
        "edge_count":sum(len(row.dependencies) for row in rows),
        "command_count":sum(len(row.script) for row in rows),
        "names_sha256":sha256("\n".join(row.name for row in rows).encode()).hexdigest(),
        "specs_sha256":_specs_digest(tuple(rows)),
        "factory_metadata_sha256":sha256(json.dumps(metadata,separators=(",",":")).encode()).hexdigest(),
        "factories":records, "seconds":time.monotonic()-started,"peak_rss_bytes":peak},
        sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
