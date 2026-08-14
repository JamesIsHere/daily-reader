r"""One scheduled cycle: poll, digest, log, ding.

Usage:
    python cycle.py        what Task Scheduler runs every 3 waking hours
                           (via pythonw.exe so no console window flashes)

Runs poller.py then digest.py as subprocesses, tees both outputs (including
digest's per-cycle API cost line) to state\cycle.log — stdout vanishes under
Task Scheduler, and the cost log is the local half of the owner's
consumption-pattern experiment. Then fires a Windows toast EVERY cycle
(goal.md: the ding is also the break clock; quiet cycles say so plainly).
Clicking the toast opens digest\latest.html; closing it leaves no state.

Toast delivery is toast.ps1 (WinRT via PowerShell 5.1, zero dependencies).
The toast XML payload is written to state\toast.xml as UTF-8 and loaded from
disk by the script — item titles never cross a PowerShell command line, which
PS 5.1 would mangle. A toast failure is logged, never fatal: the archive and
rolling view are already written by then.
"""

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

import digest as dg

ROOT = Path(__file__).parent
CYCLE_LOG = ROOT / "state" / "cycle.log"
TOAST_XML = ROOT / "state" / "toast.xml"
TOAST_PS1 = ROOT / "toast.ps1"
VIEW = ROOT / "digest" / "latest.html"
TOAST_MAX_LINES = 3


def run_step(script):
    # Captured stdout is a pipe, which Windows defaults to cp1252 in the
    # child — an emoji in an item title then crashes the report print (and
    # with it the toast's NEW lines, as at the 2026-07-27 13:00 cycle).
    # Force the children to UTF-8, matching the decode below.
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    p = subprocess.run([sys.executable, str(ROOT / script)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=ROOT, timeout=1500, env=env)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def toast_payload(poll_out):
    new = re.findall(r"^  NEW \[(article|video)\] (.+)$", poll_out, re.M)
    if not new:
        return "Daily Reader - nothing new", "Quiet cycle. Go stretch."
    lines = []
    for _, rest in new[:TOAST_MAX_LINES]:
        creator, _, title = rest.partition(": ")
        lines.append(f"{creator.split(' (')[0]}: {dg.clean_title(title)}")
    if len(new) > TOAST_MAX_LINES:
        lines.append(f"+{len(new) - TOAST_MAX_LINES} more")
    return f"Daily Reader - {len(new)} new", "\n".join(lines)


def fire_toast(title, body):
    xml = (f'<toast activationType="protocol" launch="{VIEW.resolve().as_uri()}">'
           f'<visual><binding template="ToastGeneric">'
           f'<text>{escape(title)}</text><text>{escape(body)}</text>'
           f'</binding></visual>'
           f'<audio src="ms-winsoundevent:Notification.Default"/></toast>')
    TOAST_XML.write_text(xml, encoding="utf-8")
    p = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-File", str(TOAST_PS1), "-XmlPath", str(TOAST_XML)],
        capture_output=True, text=True, timeout=60)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main():
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rc_poll, poll_out = run_step("poller.py")
    # Page watcher runs between poll and digest so its items make this
    # cycle's digest; its NEW lines merge into poll_out for the toast.
    rc_watch, watch_out = run_step("watch.py")
    poll_out += watch_out
    rc_dig, dig_out = run_step("digest.py")
    # Publish the fresh view to Vercel (iPhone home-screen icon). Guarded
    # until the one-time `vercel link` has been done; never fatal -- the
    # archive, view, and toast do not depend on the network mirror.
    rc_pub, pub_out = 0, ""
    if (ROOT / "publish" / ".vercel" / "project.json").exists():
        rc_pub, pub_out = run_step("publish.py")
    title, body = toast_payload(poll_out)
    rc_toast, toast_out = fire_toast(title, body)
    with CYCLE_LOG.open("a", encoding="utf-8") as f:
        f.write(f"===== cycle {stamp} =====\n{poll_out}{dig_out}{pub_out}")
        f.write(f"toast: rc={rc_toast} \"{title}\"\n")
        if rc_poll or rc_watch or rc_dig or rc_toast or rc_pub:
            f.write(f"WARN exit codes: poller={rc_poll} watch={rc_watch} "
                    f"digest={rc_dig} toast={rc_toast} publish={rc_pub}\n"
                    f"{toast_out}")
    sys.exit(1 if (rc_poll or rc_watch or rc_dig) else 0)


if __name__ == "__main__":
    main()
