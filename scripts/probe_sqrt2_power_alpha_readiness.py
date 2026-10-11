#!/usr/bin/env python3
"""Bounded diagnostic of the existing Alpha ordinary-certificate gate.

This is NOT admission. It neither changes a registry nor loads receipts as
authority. The immutable AP095 bundle is decoded, conservatively interned,
compiled by the existing Alpha compiler, and checked in the empty context.
Run in a dedicated one-CPU Slurm allocation, not on the login node.
"""
import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path
import resource
import signal
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("generation", type=Path)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    resource.setrlimit(resource.RLIMIT_AS, (1536 * 1024**2,) * 2)
    signal.alarm(180)
    start = time.monotonic()
    result = dict(schema="sqrt2-alpha-readiness-v1", case="AP095",
                  authority="diagnostic_not_admission", library_admissions=0,
                  cpu_limit=170, wall_limit=180, address_space_mib=1536)
    def checkpoint(phase, **fields):
        result.update(phase=phase, **fields)
        print(json.dumps(result, sort_keys=True), flush=True)
    try:
        checkpoint("imports")
        from peano_lab.library.proof_bundle import decode_proof_bundle
        from peano_lab.library.layered_replay import (
            LayeredReplayBundle, LayeredReplayNode, intern_layered_replay_bodies,
        )
        from peano_lab.library.campaign_gaussian_factorization_closure import (
            compile_gaussian_factorization_replay,
        )
        from peano_lab.kernel.checker import check
        from peano_lab.kernel.formulas import Imp, Bot
        process = json.loads(gzip.decompress(args.generation.read_bytes()))
        generated = json.loads(process["stdout"])
        payload = generated["bundle"]
        if sha256(payload.encode()).hexdigest() != "07d48fca1276244b05d415dc9c46a505b1fd357dc8178abea55a624e7347ff7e":
            raise ValueError("AP095 bundle changed")
        bundle, target = decode_proof_bundle(payload)
        checkpoint("decoded", bundle_nodes=len(bundle.nodes))
        graph = LayeredReplayBundle(tuple(LayeredReplayNode(n.node_id, n.target,
            n.dependencies, n.body) for n in bundle.nodes), bundle.root)
        graph = intern_layered_replay_bodies(graph, target)
        if graph is None:
            raise ValueError("unchanged Alpha interning limits reject this bundle")
        checkpoint("interned")
        table = {n.node_id: n for n in graph.nodes}
        for node in graph.nodes:
            goal = node.target
            for dep in reversed(node.dependencies):
                goal = Imp(table[dep].target, goal)
            if not check((), node.body, goal):
                raise ValueError("interned ordinary body rejected")
        checkpoint("bodies_checked")
        candidate = compile_gaussian_factorization_replay(graph, target)
        if candidate is None:
            raise ValueError("unchanged Alpha ordinary-certificate compiler rejected the graph")
        checkpoint("compiled", proof_nodes=candidate.proof_nodes,
                   proof_depth=candidate.proof_depth,
                   annotations=candidate.proof_annotation_occurrences)
        if not check((), candidate.certificate, target):
            raise ValueError("ordinary empty-context certificate rejected")
        if check((), candidate.certificate, Bot()):
            raise ValueError("false target accepted")
        checkpoint("complete", status="ordinary_checked_not_enrolled")
    except Exception as exc:
        checkpoint("stopped", status="not_promotion_ready", error=type(exc).__name__ + ": " + str(exc))
    finally:
        checkpoint(result["phase"], elapsed_wall_seconds=time.monotonic()-start,
                   cpu_seconds=time.process_time(), peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


if __name__ == "__main__":
    main()
