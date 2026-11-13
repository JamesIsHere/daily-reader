r"""One scheduled cycle: poll, watch, digest, publish, log.

Usage:
    python cycle.py        what Task Scheduler runs (once daily at 00:00,
                           via pythonw.exe so no console window flashes)

Runs poller.py, watch.py, digest.py, then publish.py as subprocesses, and
tees their outputs (including digest's per-cycle API cost line) to
state\cycle.log; stdout vanishes under Task Scheduler. There is no
notification: the Windows toast was removed 2026-11-13 (James: too
annoying). toast.ps1 is archived under archived\2026-11-13-toast\.
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
CYCLE_LOG = ROOT / "state" / "cycle.log"


def run_step(script):
    # Captured stdout is a pipe, which Windows defaults to cp1252 in the
    # child; an emoji in an item title then crashes the report print, as at
    # the 2026-07-27 13:00 cycle. Force the children to UTF-8, matching the
    # decode below.
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    p = subprocess.run([sys.executable, str(ROOT / script)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=ROOT, timeout=1500, env=env)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rc_poll, poll_out = run_step("poller.py")
    # Page watcher runs between poll and digest so its items make this
    # cycle's digest.
    rc_watch, watch_out = run_step("watch.py")
    rc_dig, dig_out = run_step("digest.py")
    # Publish the fresh view to Vercel (iPhone home-screen icon). Guarded
    # until the one-time `vercel link` has been done; never fatal: the
    # archive and view do not depend on the network mirror.
    rc_pub, pub_out = 0, ""
    if (ROOT / "publish" / ".vercel" / "project.json").exists():
        rc_pub, pub_out = run_step("publish.py")
    with CYCLE_LOG.open("a", encoding="utf-8") as f:
        f.write(f"===== cycle {stamp} =====\n"
                f"{poll_out}{watch_out}{dig_out}{pub_out}")
        if rc_poll or rc_watch or rc_dig or rc_pub:
            f.write(f"WARN exit codes: poller={rc_poll} watch={rc_watch} "
                    f"digest={rc_dig} publish={rc_pub}\n")
    sys.exit(1 if (rc_poll or rc_watch or rc_dig) else 0)


if __name__ == "__main__":
    main()
