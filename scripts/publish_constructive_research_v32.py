#!/usr/bin/env python3
"""Publish canonical v32 readers only from a fresh full release verification."""

from __future__ import annotations

import argparse
import resource
import signal

from constructive_alpha_v32_publication_process import publish_from_live_context


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true")
    parser.add_argument("--create-release",action="store_true")
    args=parser.parse_args(argv)
    import build_peano_library_channels_v32 as builder
    import check_alpha_v32_research as audit_module
    from verify_peano_library_channels_v32 import context_from_live_audit, verify_candidate_payloads
    resource.setrlimit(resource.RLIMIT_CPU,audit_module.CPU_LIMITS)
    signal.alarm(15*audit_module.PARENT_TIMEOUT_SECONDS+5*audit_module.WALL_SECONDS)
    payloads,audit=builder.build_payloads()
    verify_candidate_payloads(payloads,audit)
    builder.check_or_write(payloads,check=not args.create_release or args.check)
    context=context_from_live_audit(audit)
    publish_from_live_context(context,check=args.check)
    context.require_unchanged()
    print("Verified Alpha v32 publication: 3971 admissions, Stable432, G009 closed, G091 open.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
