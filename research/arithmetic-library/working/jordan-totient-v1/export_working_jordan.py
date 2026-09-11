#!/usr/bin/env python3
"""Explicit new-only Jordan authoring entrypoint; original single-process caps."""
import argparse
from pathlib import Path
import resource
import signal
import time

STARTED=time.monotonic()
if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180)
import check_working_jordan as checker
checker.STARTED=STARTED  # One entry clock, never reset between operations.


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--through',required=True,type=int,choices=checker.support.PHASES)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args(argv)
    report=checker.run('author',args.through,output=args.output)
    print(checker.support.canonical(report).decode(),flush=True)
    return 0


if __name__=='__main__':raise SystemExit(main())
