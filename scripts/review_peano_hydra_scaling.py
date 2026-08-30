#!/usr/bin/env python3
"""Record an operator's explicit lineage decision; never approve compute."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).absolute().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "peano-lab/py")]


def main(argv=None):
    from training.peano_hydra import scaling_workflow as workflow
    from training.peano_hydra import scaling_lineage as lineage
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--expected-readiness-sha256", required=True)
    parser.add_argument("--reviewer-reference", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if not sys.stdin.isatty():
            raise ValueError("human review requires an interactive terminal; no piped confirmation")
        workflow.fileio.guard_output(args.output,
            protected=(*workflow._protected(), args.bundle.absolute()))
        ready, summary = workflow._check_bundle_metadata(args.bundle,
            expected_readiness_sha256=args.expected_readiness_sha256)
        proposal, _ = workflow.read_json(args.bundle / "lineage-proposal.json")
        print("Hydra frontier: human lineage review (no GPU approval)")
        print("Readiness SHA:", args.expected_readiness_sha256)
        print("Proposal SHA:", proposal["proposal_sha256"])
        print("Full evidence:", args.bundle.absolute() / "lineage-proposal.json")
        print("Native source:", args.bundle.absolute() / "source")
        print("Raw transitions:", summary["native_verified_transitions"],
              "; distinct projected examples:", ready["projected_unique_rows"])
        components = {c["component_id"]: c for c in proposal["components"]}
        for allocation in proposal["allocations"]:
            component = components[allocation["component_id"]]
            print(allocation["component_id"], "->", allocation["split"],
                  "diagnostic=" + str(allocation["diagnostic"]),
                  "routes=" + str(len(component["route_ids"])))
        print("\nBefore deciding, inspect the linked template/parent components, exposure")
        print("coverage, exclusions and native proof examples. Unknowns stay quarantined.")
        print("This checks declared relations only, not all semantic equivalences.")
        print("These authored DEV goals are diagnostics, not a sealed unseen benchmark.")
        print("Your reviewer identity is asserted, not cryptographically verified.")
        print("This decision does not grant reference readiness, final-test ownership,")
        print("token fit, upload, GPU time, model training or a research claim.")
        answer = input("Type ACCEPT LINEAGE REVIEW or REJECT LINEAGE REVIEW: ")
        if answer not in {"ACCEPT LINEAGE REVIEW", "REJECT LINEAGE REVIEW"}:
            raise ValueError("no exact human decision supplied; no review was written")
        body = {
            "schema": "peano-hydra-scaling-lineage-review-v1",
            "proposal_sha256": proposal["proposal_sha256"], "scope": proposal["allocations"],
            "decision": "accept" if answer.startswith("ACCEPT") else "reject",
            "reviewer_reference": args.reviewer_reference,
            "reviewed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "asserted_human_review": True,
            "acknowledgments": {
                "declared_relations_and_exposures_only": True,
                "no_unseen_or_semantic_completeness_claim": True,
                "no_independent_test_seal_or_compute_authority": True,
                "reviewer_identity_not_cryptographically_verified": True,
            },
        }
        review = {**body, "review_sha256": lineage.canonical_sha256(body)}
        lineage.validate_review_record(review, proposal=proposal,
            expected_proposal_sha256=proposal["proposal_sha256"],
            expected_review_sha256=review["review_sha256"], required_scope=proposal["allocations"])
        # Bind the decision to the exact evidence displayed, even after a long
        # human inspection pause. Never overwrite input or an earlier review.
        after, after_summary = workflow._check_bundle_metadata(args.bundle,
            expected_readiness_sha256=args.expected_readiness_sha256)
        workflow.require(after == ready and after_summary == summary, "review evidence changed while you inspected it")
        raw_sha = workflow.write_json(args.output, review)
        print("Saved", args.output.absolute())
        print("Canonical review SHA (use for admission):", review["review_sha256"])
        print("Raw file SHA (file transfer/audit only):", raw_sha)
        return 0
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, EOFError) as error:
        print("hydra-lineage-review: " + " ".join(str(error).split()), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
