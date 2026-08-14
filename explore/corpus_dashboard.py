"""
daily-reader/explore :: corpus dashboard
----------------------------------------
Descriptive dashboard over the roster corpus: where items come from, how much
comes in, at what cadence, with what history depth. Exploration only -- no
rules, no scoring, no recommendations. Reads explore/data/ (from
pull_history.py) and ../state/items.jsonl (read-only).

Usage:  python pull_history.py   (first, or after roster changes)
        python corpus_dashboard.py   ->  open corpus.html
"""

import base64
import datetime as dt
import json
import os
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

HERE = Path(__file__).parent
DATA = HERE / "data"
CHARTS = HERE / "charts"
CHARTS.mkdir(exist_ok=True)
ITEMS = HERE.parent / "state" / "items.jsonl"
FIGSIZE = (11.5, 4.3)

C = {"blue": "#2b6cb0", "red": "#c53030", "green": "#2f855a", "orange": "#c05621",
     "purple": "#6b46c1", "teal": "#2c7a7b", "gray": "#4a5568", "pink": "#b83280"}
PLAT = {"substack-api": C["blue"], "feed-only": C["teal"], "blogspot": C["purple"],
        "youtube": C["red"], "page": C["gray"], "error": C["orange"]}


def styleax(ax, title, ylabel=None):
    ax.set_title(title, fontsize=12, loc="left", color="#1a1a1a", pad=8, weight="bold")
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=9)
    ax.grid(True, alpha=0.25, lw=0.6)
    ax.tick_params(labelsize=9)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)


def save(fig, name):
    path = CHARTS / name
    fig.savefig(path, dpi=110, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def one(fname, drawer, figsize=FIGSIZE):
    fig, ax = plt.subplots(figsize=figsize)
    drawer(ax)
    fig.tight_layout()
    return save(fig, fname)


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
hist = pd.read_json(DATA / "history.jsonl", lines=True)
hist["published"] = pd.to_datetime(hist["published"])
src = pd.read_csv(DATA / "sources.csv")

live = pd.DataFrame(json.loads(l) for l in open(ITEMS, encoding="utf-8"))
live["fetched"] = pd.to_datetime(live["fetched"], utc=True).dt.tz_convert(None)
live["day"] = live["fetched"].dt.normalize()

THIS_MONTH = pd.Timestamp(dt.date.today().replace(day=1))


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
def build_inflow():
    out = []
    by_day = live.groupby(["day", "kind"]).size().unstack(fill_value=0)

    def daily(ax):
        bottom = None
        cols = {"article": C["blue"], "video": C["red"], "page": C["gray"]}
        for kind in by_day.columns:
            v = by_day[kind].values
            ax.bar(by_day.index, v, bottom=bottom, width=0.7,
                   color=cols.get(kind, C["orange"]), label=kind)
            bottom = v if bottom is None else bottom + v
        ax.legend(fontsize=9, frameon=False)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
        styleax(ax, "Live inflow: items fetched per day since launch, by kind", "items")

    d0, d1 = live["day"].min().date(), live["day"].max().date()
    cap1 = (f"items.jsonl holds {len(live)} items fetched {d0} to {d1}; "
            f"the launch-day bar includes each feed's existing window emitted on "
            f"first poll, later bars are new releases only.")
    out.append((one("inflow_daily.png", daily), cap1))

    steady = live[live["day"] > live["day"].min()]
    per_creator = steady.groupby("creator").size().sort_values()

    def creators(ax):
        ax.barh(per_creator.index, per_creator.values, color=C["blue"], height=0.7)
        ax.tick_params(labelsize=8)
        styleax(ax, f"Post-launch items by creator ({steady['day'].min().date()} onward)",
                None)
        ax.set_xlabel("items", fontsize=9)

    cap2 = (f"Excluding launch day, {len(steady)} items arrived from "
            f"{per_creator.size} of the roster's creators; the remainder emitted "
            f"nothing in this window.")
    out.append((one("inflow_creators.png", creators,
                    figsize=(11.5, max(3.5, 0.28 * per_creator.size))), cap2))
    return out


def build_trends():
    out = []
    feeds = hist[hist["entry_point"] == "feed"].copy()
    feeds["month"] = feeds["published"].dt.to_period("M").dt.to_timestamp()
    feeds = feeds[feeds["month"] < THIS_MONTH]
    monthly = feeds.groupby("month").size()

    def total(ax):
        ax.bar(monthly.index, monthly.values, width=20, color=C["blue"])
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        styleax(ax, "Feed corpus: published items per month, trailing 24 months",
                "items / month")

    cap1 = (f"All feed sources combined published {monthly.sum()} items over "
            f"{monthly.size} complete months (mean {monthly.mean():.0f}/month); "
            f"YouTube is excluded here because its feeds only expose the last 15 "
            f"entries, and the partial current month is dropped.")
    out.append((one("trend_total.png", total), cap1))

    top = feeds.groupby("creator").size().nlargest(6).index
    piv = (feeds[feeds["creator"].isin(top)]
           .groupby(["month", "creator"]).size().unstack(fill_value=0))

    def topsix(ax):
        pal = [C["blue"], C["red"], C["green"], C["orange"], C["purple"], C["teal"]]
        for i, c in enumerate(piv.columns):
            ax.plot(piv.index, piv[c].values, lw=1.6, color=pal[i % 6], label=c)
        ax.legend(fontsize=8, frameon=False, ncol=2)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        styleax(ax, "Six most prolific feed sources: items per month", "items / month")

    share = feeds[feeds["creator"].isin(top)].shape[0] / len(feeds) * 100
    cap2 = (f"The six most prolific sources account for {share:.0f}% of all feed "
            f"items in the window; per-source monthly counts are shown unsmoothed.")
    out.append((one("trend_top6.png", topsix), cap2))
    return out


def gaps_by_creator(min_items=4):
    """Per source (creator+entry_point key): sorted gap series in days."""
    rows = []
    for (creator, ep), g in hist.groupby(["creator", "entry_point"]):
        d = g["published"].sort_values()
        if len(d) < min_items:
            continue
        gaps = d.diff().dt.days.dropna()
        rows.append({"creator": creator, "entry_point": ep, "n": len(d),
                     "median_gap": gaps.median(), "cv": gaps.std() / gaps.mean()
                     if gaps.mean() > 0 else float("nan")})
    return pd.DataFrame(rows)


def build_cadence():
    out = []
    g = gaps_by_creator().sort_values("median_gap")

    def med(ax):
        colors = [PLAT.get("youtube" if ep == "youtube" else "substack-api")
                  for ep in g["entry_point"]]
        ax.barh(g["creator"], g["median_gap"], color=colors, height=0.7)
        ax.tick_params(labelsize=8)
        ax.set_xlabel("median days between releases", fontsize=9)
        styleax(ax, "Cadence: median gap between releases, per source")

    cap1 = (f"Median inter-release gap per source with at least 4 visible items "
            f"(blue = feeds over the 24-month archive window, red = YouTube over "
            f"its last-15-entries window); range runs {g['median_gap'].min():.0f} "
            f"to {g['median_gap'].max():.0f} days.")
    out.append((one("cadence_median.png", med,
                    figsize=(11.5, max(4, 0.28 * len(g)))), cap1))

    wk = hist.copy()
    wk["week"] = wk["published"].dt.to_period("W").dt.start_time
    weekly = wk.groupby("week").size()
    weekly = weekly[weekly.index >= weekly.index.max() - pd.Timedelta(weeks=52)]

    def week(ax):
        ax.bar(weekly.index, weekly.values, width=5, color=C["teal"])
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        styleax(ax, "Whole-corpus weekly volume, trailing 52 weeks", "items / week")

    cap2 = (f"Corpus-wide weekly item count for the last year: median "
            f"{weekly.median():.0f}, maximum {weekly.max()} in the week of "
            f"{weekly.idxmax().date()}.")
    out.append((one("cadence_weekly.png", week), cap2))
    return out


def build_burstiness():
    out = []
    g = gaps_by_creator().dropna(subset=["cv"]).sort_values("cv", ascending=False)

    def cv(ax):
        colors = [PLAT.get("youtube" if ep == "youtube" else "substack-api")
                  for ep in g["entry_point"]]
        ax.barh(g["creator"][::-1], g["cv"][::-1], color=colors[::-1], height=0.7)
        ax.axvline(1.0, color="#a0aec0", lw=1.0, ls="--")
        ax.tick_params(labelsize=8)
        ax.set_xlabel("coefficient of variation of release gaps", fontsize=9)
        styleax(ax, "Burstiness: gap variability per source (CV; 1.0 = Poisson-like)")

    cap1 = ("Coefficient of variation of inter-release gaps per source: values "
            "near 0 are metronomic schedules, values above 1 mean releases "
            "cluster in spurts with long silences between; the dashed line marks "
            "CV = 1.")
    out.append((one("burst_cv.png", cv,
                    figsize=(11.5, max(4, 0.28 * len(g)))), cap1))

    sc = gaps_by_creator().dropna(subset=["cv"])
    sc["per_month"] = sc["n"] / (hist.groupby("creator")["published"]
                                 .agg(lambda d: max((d.max() - d.min()).days, 30))
                                 .reindex(sc["creator"]).values / 30.4)

    def scatter(ax):
        for ep, m in (("feed", "o"), ("youtube", "s")):
            s = sc[sc["entry_point"] == ep]
            ax.scatter(s["per_month"], s["cv"], s=42, marker=m, alpha=0.85,
                       color=PLAT["substack-api" if ep == "feed" else "youtube"],
                       label=ep)
        for _, r in sc.nlargest(5, "cv").iterrows():
            ax.annotate(r["creator"].split(" (")[0], (r["per_month"], r["cv"]),
                        fontsize=7.5, xytext=(4, 3), textcoords="offset points")
        ax.legend(fontsize=9, frameon=False)
        ax.set_xlabel("items per month (observed span)", fontsize=9)
        styleax(ax, "Volume vs burstiness, one point per source", "gap CV")

    cap2 = ("Each point is a source, positioned by observed monthly volume and "
            "gap variability; the five highest-CV sources are labeled.")
    out.append((one("burst_scatter.png", scatter), cap2))
    return out


def build_mix():
    out = []
    ep_sources = src.groupby("entry_point").size()
    ep_items = hist.groupby("entry_point").size().reindex(ep_sources.index, fill_value=0)

    def mix(ax):
        x = range(len(ep_sources))
        ax.bar([i - 0.2 for i in x], ep_sources.values, width=0.38,
               color=C["gray"], label="sources (roster rows)")
        ax.bar([i + 0.2 for i in x], ep_items.values, width=0.38,
               color=C["blue"], label="visible historical items")
        ax.set_xticks(list(x))
        ax.set_xticklabels(ep_sources.index, fontsize=10)
        ax.legend(fontsize=9, frameon=False)
        styleax(ax, "Entry points: roster rows vs visible history, log scale", "count")
        ax.set_yscale("log")

    cap1 = (f"The roster's {ep_sources.sum()} rows split "
            + ", ".join(f"{v} {k}" for k, v in ep_sources.items())
            + f"; visible history is almost entirely feed-borne "
              f"({ep_items.get('feed', 0)} of {ep_items.sum()} items), because "
              f"page-watch has no past and YouTube truncates at 15.")
    out.append((one("mix_entry.png", mix), cap1))

    plat_items = hist.groupby("platform").size().sort_values()

    def plats(ax):
        ax.barh(plat_items.index, plat_items.values,
                color=[PLAT.get(p, C["orange"]) for p in plat_items.index], height=0.6)
        ax.set_xlabel("items", fontsize=9)
        styleax(ax, "Visible historical items by platform")

    n_sub = int(src[src["platform"] == "substack-api"].shape[0])
    cap2 = (f"By platform: {n_sub} of the feed rows are Substack-hosted (their "
            f"archive API allows the 24-month pull); the rest expose only what "
            f"their feed carries.")
    out.append((one("mix_platform.png", plats), cap2))
    return out


def build_depth():
    out = []
    s = src[src["n_items"] > 0].copy()
    s["earliest"] = pd.to_datetime(s["earliest"])
    s["latest"] = pd.to_datetime(s["latest"])
    s = s.sort_values("earliest", ascending=False).reset_index(drop=True)

    def depth(ax):
        for i, r in s.iterrows():
            col = PLAT.get(r["platform"], C["orange"])
            ax.hlines(i, r["earliest"], r["latest"], color=col, lw=3, alpha=0.85)
            ax.plot(r["latest"], i, "o", color=col, ms=4)
            if r["truncated"]:
                ax.plot(r["earliest"], i, "o", mfc="white", mec=col, ms=5)
        ax.set_yticks(range(len(s)))
        ax.set_yticklabels(s["creator"], fontsize=8)
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        styleax(ax, "History depth: visible publication span per source")

    n_pages = int((src["entry_point"] == "page-watch").sum())
    zero = src[(src["n_items"] == 0) & (src["entry_point"] != "page-watch")]
    cap1 = (f"Span of retrievable history per source (open circle = truncated "
            f"start, not birth); not drawn: {n_pages} watched pages with no "
            f"retrievable past, and {len(zero)} feed sources with zero items in "
            f"the window ({', '.join(zero['creator'])}).")
    out.append((one("depth_span.png", depth,
                    figsize=(11.5, max(4, 0.28 * len(s)))), cap1))
    return out


# ---------------------------------------------------------------------------
# HTML shell (tic_dashboard.py pattern)
# ---------------------------------------------------------------------------
def build_html(sections):
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    head = """<!doctype html><meta charset="utf-8">
<title>daily-reader :: corpus explorer</title>
<style>
 :root{--ink:#1a202c;--mut:#718096;--line:#e2e8f0;--accent:#2b6cb0;--bg:#fafafa}
 *{box-sizing:border-box}
 body{font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);margin:0;background:var(--bg)}
 header{max-width:1120px;margin:0 auto;padding:26px 24px 0}
 h1{font-size:24px;margin:0 0 3px} .sub{color:var(--mut);margin:0 0 16px;font-size:13px}
 nav{position:sticky;top:0;z-index:10;background:var(--bg);border-bottom:2px solid var(--line)}
 .navwrap{max-width:1120px;margin:0 auto;padding:0 24px;display:flex;gap:4px;flex-wrap:wrap}
 nav button{appearance:none;border:0;background:none;font:600 14px/1 inherit;color:var(--mut);
   padding:14px 16px;cursor:pointer;border-bottom:3px solid transparent;margin-bottom:-2px}
 nav button:hover{color:var(--ink)}
 nav button.active{color:var(--accent);border-bottom-color:var(--accent)}
 main{max-width:1120px;margin:0 auto;padding:22px 24px 56px}
 section{display:none} section.active{display:block}
 figure.ch{margin:0 0 40px}
 figure.ch img{width:100%;height:auto;border:1px solid var(--line);border-radius:6px;background:#fff}
 figure.ch figcaption{font-size:14px;color:#4a5568;margin-top:12px;max-width:940px;line-height:1.5}
 footer{color:#a0aec0;font-size:12px;margin-top:20px}
</style>
"""
    tabs, panels = [], []
    for i, (key, title, items) in enumerate(sections):
        act = " active" if i == 0 else ""
        tabs.append(f'<button class="tab{act}" data-t="{key}">{title}</button>')
        blocks = ""
        for png, cap in items:
            b64 = base64.b64encode(open(png, "rb").read()).decode()
            blocks += (f'<figure class="ch"><img src="data:image/png;base64,{b64}">'
                       f'<figcaption>{cap}</figcaption></figure>')
        panels.append(f'<section class="panel{act}" id="{key}">{blocks}</section>')

    body = f"""<header><h1>daily-reader corpus explorer</h1>
 <p class="sub">Generated {ts} &middot; history: Substack archive API + feeds to 2024-08 &middot; live: state/items.jsonl (read-only) &middot; descriptive only, no rules</p></header>
<nav><div class="navwrap">{''.join(tabs)}</div></nav>
<main>
{''.join(panels)}
 <footer>Raw pulls in <code>data/raw/</code>, derived data in <code>data/</code>. Rebuild: <code>python pull_history.py &amp;&amp; python corpus_dashboard.py</code>.</footer>
</main>
<script>
 document.querySelectorAll('nav button.tab').forEach(function(b){{
   b.addEventListener('click',function(){{
     var t=b.dataset.t;
     document.querySelectorAll('nav button.tab').forEach(function(x){{x.classList.toggle('active',x===b);}});
     document.querySelectorAll('main section.panel').forEach(function(s){{s.classList.toggle('active',s.id===t);}});
     if(location.hash!=='#'+t) history.replaceState(null,'','#'+t);
     window.scrollTo(0,0);
   }});
 }});
 (function(){{var h=location.hash.replace('#','');if(h){{var b=document.querySelector('nav button[data-t="'+h+'"]');if(b)b.click();}}}})();
</script>
"""
    out = HERE / "corpus.html"
    out.write_text(head + body, encoding="utf-8")
    return out


def main():
    sections = [
        ("inflow", "Live inflow", build_inflow()),
        ("trends", "Trends", build_trends()),
        ("cadence", "Cadence", build_cadence()),
        ("burst", "Burstiness", build_burstiness()),
        ("mix", "Mix", build_mix()),
        ("depth", "Depth", build_depth()),
    ]
    monthly = (hist[hist["entry_point"] == "feed"]
               .assign(month=lambda d: d["published"].dt.to_period("M"))
               .groupby("month").size())
    monthly.to_csv(DATA / "monthly_counts.csv")
    gaps_by_creator().to_csv(DATA / "cadence.csv", index=False)
    out = build_html(sections)
    print(f"history: {len(hist)} items, {src.shape[0]} sources; "
          f"live: {len(live)} items")
    print("Report:", out)


if __name__ == "__main__":
    main()
