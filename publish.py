r"""Publish the rolling digest to Vercel for the iPhone home-screen icon.

Usage:
    python publish.py            copy digest\latest.html -> publish\index.html
                                 (inject mobile/PWA head tags), refresh static
                                 assets, deploy publish\ to Vercel production
    python publish.py --dry-run  build publish\ but do not deploy

Called by cycle.py after digest (guarded: skipped until publish\.vercel\
project.json exists, i.e. until `vercel link` has been run once). A publish
failure is logged by cycle.py but never breaks the cycle -- the local
archive, view, and toast are already done by then.

One-time setup (interactive, done 2026-08-01):
    vercel login
    cd publish && vercel link --yes --project <obscure-name>

digest.py stays untouched by design: the injection happens on the COPY, so
the local pipeline and its backtest baseline see the same latest.html as
before. explore\corpus.html rides along unmodified when present.
"""

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
VIEW = ROOT / "digest" / "latest.html"
CORPUS = ROOT / "explore" / "corpus.html"
PUB = ROOT / "publish"
ICON = PUB / "apple-touch-icon.png"
TIMEOUT = 300

MARKER = "<title>Daily Reader</title>"
HEAD_TAGS = (
    "<title>Daily Reader</title>\n"
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    '<link rel="manifest" href="manifest.webmanifest">\n'
    '<link rel="apple-touch-icon" href="apple-touch-icon.png">\n'
    '<meta name="apple-mobile-web-app-capable" content="yes">\n'
    '<meta name="apple-mobile-web-app-status-bar-style" content="default">\n'
    '<meta name="apple-mobile-web-app-title" content="Daily Reader">\n'
    # Standalone mode has no reload button by design; refetch on resume.
    # The 60s floor stops a reload loop; pageshow covers bfcache restores.
    "<script>(function(){var t=Date.now();"
    'document.addEventListener("visibilitychange",function(){'
    'if(document.visibilityState==="visible"&&Date.now()-t>60000)'
    "location.reload();});"
    'window.addEventListener("pageshow",function(e){'
    "if(e.persisted)location.reload();});})();</script>"
)

MANIFEST = """{
 "name": "Daily Reader",
 "short_name": "Reader",
 "display": "standalone",
 "start_url": "/",
 "background_color": "#ffffff",
 "theme_color": "#1a5276",
 "icons": [{"src": "apple-touch-icon.png", "sizes": "180x180",
            "type": "image/png"}]
}
"""

# no-cache: the home-screen icon must refetch on every open, not serve a
# cached cycle. Assets are tiny; correctness beats the cache here.
VERCEL_JSON = """{
 "headers": [{"source": "/(.*)",
              "headers": [{"key": "Cache-Control", "value": "no-cache"}]}]
}
"""


def make_icon():
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (180, 180), "#1a5276")
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 76)
    d.text((90, 84), "DR", font=font, fill="#ffffff", anchor="mm")
    img.save(ICON)


def build():
    PUB.mkdir(exist_ok=True)
    html = VIEW.read_text(encoding="utf-8")
    if MARKER in html:
        html = html.replace(MARKER, HEAD_TAGS, 1)
    else:
        print("WARN: title marker not found; publishing latest.html unmodified")
    (PUB / "index.html").write_text(html, encoding="utf-8")
    (PUB / "manifest.webmanifest").write_text(MANIFEST, encoding="utf-8")
    (PUB / "vercel.json").write_text(VERCEL_JSON, encoding="utf-8")
    if not ICON.exists():
        make_icon()
    if CORPUS.exists():
        shutil.copy(CORPUS, PUB / "corpus.html")


def deploy():
    exe = shutil.which("vercel")
    if not exe:
        sys.exit("ERROR: vercel CLI not on PATH (npm install -g vercel)")
    p = subprocess.run([exe, "deploy", "--prod", "--yes"], cwd=PUB,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=TIMEOUT)
    out = (p.stdout or "") + (p.stderr or "")
    if p.returncode:
        print(f"ERROR: vercel deploy rc={p.returncode}\n{out[-800:]}")
        sys.exit(p.returncode)
    urls = [w for w in out.split() if w.startswith("https://")]
    print(f"published: {urls[-1] if urls else '(url not parsed)'}")


def main():
    build()
    if "--dry-run" in sys.argv:
        print(f"DRY RUN: built {PUB} ({len(list(PUB.iterdir()))} files), "
              "no deploy")
        return
    if not (PUB / ".vercel" / "project.json").exists():
        sys.exit("ERROR: publish\\ not linked yet -- run `vercel link` there "
                 "once (see docstring)")
    deploy()


if __name__ == "__main__":
    main()
