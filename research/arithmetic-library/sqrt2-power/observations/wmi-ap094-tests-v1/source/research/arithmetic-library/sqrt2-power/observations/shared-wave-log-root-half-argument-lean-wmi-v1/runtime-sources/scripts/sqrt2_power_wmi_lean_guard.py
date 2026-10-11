#!/usr/bin/env python3
"""Linux Lean-only guard: virtual reservation is not resident memory.

CPU and 16-GiB address space are hard Unix limits. The unchanged supervisor
samples/enforces 2-GiB RSS; the Slurm job requests a 4-GiB memory envelope.
This guard cannot run arbitrary programs or run outside the explicit profile.
"""
import argparse
import os
import resource
import signal

from sqrt2_power_wmi_resources import require_allocation, WORKER_RSS_BYTES, LEAN_ADDRESS_SPACE_BYTES

LEAN_EXECUTABLE = "/work/bnaskrecki/peano-lab-kernel/toolchains/lean-4.31.0-linux-07a633cc8d9151cbc08825ea4cdda50d4b02a2c9cb852c0131b13046f49cad7f/lean-4.31.0-linux/bin/lean"


def validate_request(cpu, rss, command):
    if (type(cpu) is not int or not 1 <= cpu <= 120 or rss != WORKER_RSS_BYTES
            or not command or command[0] != LEAN_EXECUTABLE
            or len(command) > 64 or any(not isinstance(a,str) or '\x00' in a or len(a)>16384 for a in command)
            or sum(a == "-j" for a in command) != 1
            or command[command.index("-j")+1:command.index("-j")+2] != ["1"]):
        raise ValueError("not an approved single-threaded Lean request")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu-seconds",type=int,required=True)
    parser.add_argument("--rss-bytes",type=int,required=True)
    parser.add_argument("command",nargs=argparse.REMAINDER)
    args=parser.parse_args()
    command=args.command[1:] if args.command[:1]==["--"] else args.command
    require_allocation()
    validate_request(args.cpu_seconds,args.rss_bytes,command)
    resource.setrlimit(resource.RLIMIT_CPU,(args.cpu_seconds,args.cpu_seconds+1))
    resource.setrlimit(resource.RLIMIT_AS,(LEAN_ADDRESS_SPACE_BYTES,LEAN_ADDRESS_SPACE_BYTES))
    signal.pthread_sigmask(signal.SIG_UNBLOCK,{signal.SIGALRM})
    os.execvpe(command[0],command,os.environ)


if __name__=="__main__":
    main()
