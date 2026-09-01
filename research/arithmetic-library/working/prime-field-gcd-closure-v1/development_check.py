#!/usr/bin/env python3
"""One original dependency-curried HA body, not closed proof acceptance.

The selected family plus explicitly requested prerequisite families are read
before their bytes are executed. Unrelated mutable source families are never
loaded. Every actually used input is checked again even on a diagnostic error.
"""
import argparse
from dataclasses import asdict
import json
import resource
import signal
import time


def main(argv=None):
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    started = time.monotonic()
    import working_gcd_closure_support as support
    from check_constructive_bottom_layers import authoring_rss_bytes
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--family', required=True, choices=[x[0] for x in support.FAMILIES])
    parser.add_argument('--support-family', action='append', default=[], choices=[x[0] for x in support.FAMILIES])
    parser.add_argument('--name', required=True)
    parser.add_argument('--source-only', action='store_true', help='describe actual inputs without a proof call')
    args = parser.parse_args(argv)
    families = tuple(dict.fromkeys([args.family, *args.support_family]))
    state = support.load_candidate_state(families)
    validation_pin = support.FilePin('peano-lab/py/peano_lab/library/candidate_validation.py',
        5046, 'de38ddb037e03bbbfec2cc48a96aae5d5dd253c190968b61d9a9f7ff28cf9a42')
    support.check_pin(validation_pin, support.ROOT, support.MAX_SOURCE_BYTES)
    before = (*state.source_pins, validation_pin,
              support.snapshot_source(support.HERE/'development_check.py')[0],
              support.snapshot_source(support.HERE/'working_gcd_closure_support.py')[0])
    selected_short = next(x[2] for x in support.FAMILIES if x[0] == args.family)
    selected_path = next(p for p in before if p.path.endswith('/' + selected_short + '.py'))
    # Reconstruct just the selected family to authenticate ownership of --name;
    # its bytes must still equal the already captured input identity.
    selected_state = support.load_candidate_state((args.family,))
    support._require(selected_path in selected_state.source_pins, 'selected source changed')
    selected = next((r for r in selected_state.rows[95:] if r.name == args.name), None)
    support._require(selected is not None, '--name is not owned by the selected family')
    core = support.canonical_provider_table()
    for row in state.rows:
        support._require(row.name not in core, 'working row shadows a canonical source')
        core[row.name] = row
    support._require(all(name in core for name in selected.dependencies),
                     'missing direct source prerequisite; specify the required --support-family')
    owners = support.prior._edition_bindings()
    print(json.dumps(dict(kind='conditional-body-inputs', name=selected.name,
        dependencies=selected.dependencies, commands=len(selected.script),
        source_pins=[asdict(pin) for pin in before], prior95_final_binding=support.PRIOR_FINAL_BINDING)), flush=True)
    try:
        if not args.source_only:
            from peano_lab.library.candidate_validation import replay_candidate_bodies
            receipt = replay_candidate_bodies((selected,), core=core)[0]
            print(json.dumps(dict(kind='conditional-body-result', **asdict(receipt))), flush=True)
    finally:
        for pin in before:
            support.check_pin(pin, support.ROOT, support.MAX_SOURCE_BYTES)
        support.preserve_prior()
        after = support.prior._edition_bindings()
        support._require(after.keys() == owners.keys() and all(after[k] is v for k, v in owners.items()),
                         'diagnostic imported or replaced an Alpha edition')
        support._require(resource.getrlimit(resource.RLIMIT_CPU) == support.CPU_LIMITS,
                         'original CPU limits changed')
        print(json.dumps(dict(kind='conditional-body-resources',
            seconds=time.monotonic()-started, peak_rss_bytes=authoring_rss_bytes(),
            cpu_limits=[170,175], wall_alarm_seconds=180, conditional_only=True,
            source_only=args.source_only,
            complete_cone_checked=False, independent_lean_checked=False,
            admission_performed=False)), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
