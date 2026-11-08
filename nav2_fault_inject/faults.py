"""Fault injection for a running ROS 2 stack by pausing node processes (SIGSTOP / SIGCONT).

No remaps, no rebuild: pausing the process that hosts a node freezes everything it publishes, so
"stop the bridge" gives a sensor/TF dropout and "stop controller_server" gives a node hang.
Safety: only processes in OUR ROS_DOMAIN_ID whose command line names the node exactly are touched,
and every paused process is resumed on exit, error or Ctrl+C.
"""
import os
import signal
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Proc:
    pid: int
    node: str
    domain: str
    exe: str = ''


def _read(path):
    with open(path, 'rb') as f:
        return f.read().decode(errors='replace')


def list_procs(domain=None, proc_root='/proc', self_pid=None):
    """ROS node processes in `domain` (default: our own): those with `__node:=NAME`, or any process
    started with `--ros-args` (node name then defaults to the executable's name)."""
    domain = os.environ.get('ROS_DOMAIN_ID', '') if domain is None else str(domain)
    self_pid = os.getpid() if self_pid is None else self_pid
    out = []
    for d in os.listdir(proc_root):
        if not d.isdigit() or int(d) == self_pid:
            continue
        try:
            args = _read(f'{proc_root}/{d}/cmdline').split('\0')
            exe = os.path.basename(args[0]) if args and args[0] else ''
            node = next((a[len('__node:='):] for a in args if a.startswith('__node:=')), None)
            if node is None and '--ros-args' in args:
                node = exe
            if not node:
                continue
            env = dict(kv.split('=', 1) for kv in _read(f'{proc_root}/{d}/environ').split('\0') if '=' in kv)
            if env.get('ROS_DOMAIN_ID', '') != domain:
                continue
            out.append(Proc(int(d), node, domain, exe))
        except OSError:
            continue
    return sorted(out, key=lambda p: (p.node, p.pid))


def find(node, domain=None, proc_root='/proc'):
    node = node.lstrip('/')
    return [p for p in list_procs(domain, proc_root) if node in (p.node, p.exe)]


class Injector:
    """Pauses/resumes processes and remembers what it paused so `close()` can always undo it."""

    def __init__(self, kill=os.kill, log=print, dry_run=False):
        self._kill, self._log, self.dry_run = kill, log, dry_run
        self.paused = {}                        # pid -> node
        self.timeline = []                      # [{t, action, node, pid}]
        self._t0 = time.monotonic()

    def _rec(self, action, p):
        wall = time.strftime('%H:%M:%S')
        self.timeline.append({'t': round(time.monotonic() - self._t0, 2), 'wall': wall, 'action': action,
                              'node': p.node, 'pid': p.pid})
        self._log(f'{wall} [{self.timeline[-1]["t"]:6.2f}s] {action:7s} {p.node} (pid {p.pid})'
                  + ('  [dry-run]' if self.dry_run else ''))

    def pause(self, procs):
        for p in procs:
            if p.pid in self.paused:
                continue
            if not self.dry_run:
                self._kill(p.pid, signal.SIGSTOP)
            self.paused[p.pid] = p.node
            self._rec('PAUSE', p)

    def resume(self, procs):
        for p in procs:
            if p.pid not in self.paused:
                continue
            if not self.dry_run:
                try:
                    self._kill(p.pid, signal.SIGCONT)
                except ProcessLookupError:
                    pass
            del self.paused[p.pid]
            self._rec('RESUME', p)

    def close(self):
        """Resume everything still paused. Safe to call twice."""
        for pid, node in list(self.paused.items()):
            self.resume([Proc(pid, node, '')])

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def hang(node, seconds, domain=None, inj=None, sleep=time.sleep, proc_root='/proc'):
    """Pause `node` for `seconds`, then resume it. Returns the processes that were paused."""
    procs = find(node, domain, proc_root)
    if not procs:
        raise LookupError(f'no process for node "{node}" in ROS_DOMAIN_ID='
                          f'{os.environ.get("ROS_DOMAIN_ID", "") if domain is None else domain} '
                          '(is the stack running and the domain right? try `list`)')
    own = inj is None
    inj = inj or Injector()
    try:
        inj.pause(procs)
        sleep(seconds)
    finally:
        inj.resume(procs) if not own else inj.close()
    return procs


def parse_scenario(text):
    """YAML list of {at: seconds, node: name, for: seconds}. Returns sorted [(at, node, dur)]."""
    import yaml
    data = yaml.safe_load(text)
    items = data['faults'] if isinstance(data, dict) else data
    out = []
    for i, it in enumerate(items):
        try:
            at, node, dur = float(it['at']), str(it['node']), float(it['for'])
        except (KeyError, TypeError, ValueError) as e:
            raise ValueError(f'fault #{i + 1} needs numeric `at`, `for` and a `node`: {it!r}') from e
        if at < 0 or dur <= 0:
            raise ValueError(f'fault #{i + 1}: `at` must be >= 0 and `for` > 0: {it!r}')
        out.append((at, node, dur))
    return sorted(out)


def run_scenario(faults, domain=None, inj=None, now=time.monotonic, sleep=time.sleep, proc_root='/proc'):
    """Run timed faults. Each node is paused at `at` and resumed after `for`. Always cleans up."""
    inj = inj or Injector()
    events = []                                  # (time, 0=resume/1=pause, node)
    for at, node, dur in faults:
        if not find(node, domain, proc_root):
            raise LookupError(f'no process for node "{node}" - aborting before injecting anything')
        events += [(at, 1, node), (at + dur, 0, node)]
    events.sort(key=lambda e: (e[0], e[1]))
    t0 = now()
    try:
        for t, is_pause, node in events:
            delay = t - (now() - t0)
            if delay > 0:
                sleep(delay)
            procs = find(node, domain, proc_root)
            (inj.pause if is_pause else inj.resume)(procs)
    finally:
        inj.close()
    return inj.timeline
