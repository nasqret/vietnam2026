#!/usr/bin/env python3
"""Observe exact v34 metadata without accepting proofs or writing releases."""
from __future__ import annotations
import json
from pathlib import Path
import resource
import signal
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"peano-lab/py"))
def main():
    resource.setrlimit(resource.RLIMIT_CPU,(170,175))
    signal.alarm(180)
    started=time.monotonic()
    from peano_lab.library import editions_v33 as parent
    from peano_lab.library.alpha_enrollment_v34 import alpha_v34_enrollment
    e=alpha_v34_enrollment()
    frontier=tuple(parent.EditionEntry(spec=item,membership=parent.Membership.ALPHA_ONLY,
        evidence=parent.EvidenceStatus.ALPHA_CLOSED,enrollment_origin=parent.EnrollmentOrigin.HA,
        provenance=(parent.EnrollmentOrigin.HA,),source_module=e.source_by_name[item.name])
        for item in e.frontier_specs)
    entries=(*parent.ALPHA_ENTRIES,*frontier)
    observed=parent._make_streamed_edition(parent.EditionName.ALPHA,entries)
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=="darwin" else 1024)
    if peak>1536*1024*1024: raise ValueError("original RSS bound exceeded")
    print(json.dumps({"schema":"alpha-v34-pre-admission-edition-metadata-v1",
        "proof_calls":0,"admission_performed":False,"parent_count":len(parent.ALPHA_ENTRIES),
        "count":len(entries),"frontier_count":len(frontier),"stable_count":len(parent.STABLE_SPECS),
        "parent_entry_identities_preserved":all(a is b for a,b in zip(entries,parent.ALPHA_ENTRIES)),
        "edge_count":observed.edge_count,"layer_count":observed.layer_count,
        "enrollment_sha256":observed.enrollment_identity_sha256,"identity_sha256":observed.identity_sha256,
        "seconds":time.monotonic()-started,"peak_rss_bytes":peak},sort_keys=True))
    return 0
if __name__=="__main__":raise SystemExit(main())
