#!/usr/bin/env python3
"""nav2_fault_inject - pause nodes of a running ROS 2 stack to test that it notices and recovers."""
import argparse
import json
import signal
import sys

from . import __version__
from .faults import Injector, hang, list_procs, parse_scenario, run_scenario


def main(argv=None):
    ap = argparse.ArgumentParser(prog='nav2_fault_inject', description=__doc__)
    ap.add_argument('--version', action='version', version=f'nav2_fault_inject {__version__}')
    ap.add_argument('--domain', help='ROS_DOMAIN_ID to act in (default: this shell\'s)')
    ap.add_argument('--dry-run', action='store_true', help='show what would be paused, touch nothing')
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('list', help='node processes that can be targeted')
    h = sub.add_parser('hang', help='pause one node for N seconds, then resume it')
    h.add_argument('node'); h.add_argument('--for', dest='secs', type=float, required=True)
    r = sub.add_parser('run', help='run a timed scenario file')
    r.add_argument('scenario'); r.add_argument('--timeline', help='write the timeline as JSON')
    a = ap.parse_args(argv)

    if a.cmd == 'list':
        procs = list_procs(a.domain)
        for p in procs:
            print(f'{p.pid:8d}  {p.node}')
        print(f'{len(procs)} node process(es) in ROS_DOMAIN_ID={p.domain if procs else a.domain or "(unset)"}')
        return 0

    inj = Injector(dry_run=a.dry_run)
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        if a.cmd == 'hang':
            hang(a.node, a.secs, a.domain, inj)
        else:
            tl = run_scenario(parse_scenario(open(a.scenario).read()), a.domain, inj)
            if a.timeline:
                json.dump(tl, open(a.timeline, 'w'), indent=2)
    except LookupError as e:
        print(f'error: {e}', file=sys.stderr)
        return 2
    except ValueError as e:
        print(f'error: {e}', file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print('interrupted - resuming everything', file=sys.stderr)
        return 130
    finally:
        inj.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
