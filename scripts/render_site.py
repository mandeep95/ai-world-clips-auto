#!/usr/bin/env python3
"""Render the public status site (index.html) from the queue + last run.

Static, single file, no backend, no build step: GitHub Pages serves the
generated index.html from the repo root. The daily workflow regenerates it
after every run, so the page stays current with no manual work.

Usage:
    python3 scripts/render_site.py --account ai-world-clips [--out index.html]

Design: Hallmark, Kiln theme (ember colourway), Manifesto shape, Poster hero.
Futuristic motion per the user's direction: slow ember blooms drifting
(transform only), glassy wells, neon ember signal, pulsing live markers.
Content is visible with scripting off; all motion freezes under
prefers-reduced-motion.
"""
import argparse
import datetime
import html
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

PLATFORM_LABELS = [
    ("instagram", "Instagram"),
    ("facebook", "Facebook"),
    ("youtube", "YouTube"),
    ("threads", "Threads"),
    ("dailymotion", "Dailymotion"),
]

PROFILE_URLS = [
    ("Instagram", "https://www.instagram.com/aiwo.rldclips/"),
    ("YouTube", "https://www.youtube.com/@AIWorldClips-z4v"),
    ("Threads", "https://www.threads.com/@aiwo.rldclips"),
    ("Facebook", "https://www.facebook.com/profile.php?id=61596150134728"),
]

# What the status site says about each platform before the first run.
# Keys match the `setup:` map in the account config.
SETUP_DETAILS = {
    "wired": ("Wired", "Ready to post"),
    "awaiting-token": ("Awaiting token", "Authorisation pending"),
}


def esc(s):
    return html.escape(str(s or ""), quote=True)


def hook_html(hook):
    """Escape a hook for display, keeping the last word and a trailing
    emoji run together as one unbreakable unit (no orphan emoji line on
    narrow screens). The posted caption is untouched — display-only."""
    text = esc(hook)
    m = re.search(r" (\S+) (\S+)$", text)
    if m and any(ord(c) > 0x2500 for c in m.group(2)):
        text = (text[:m.start()] + ' <span class="nowrap">'
                + m.group(1) + "\u00a0" + m.group(2) + "</span>")
    return text


def fmt_date(iso):
    try:
        d = datetime.date.fromisoformat(str(iso)[:10])
        return d.strftime("%d %b %Y")
    except Exception:
        return str(iso or "")


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f) or {}


CSS = """/* Hallmark · kiln: ember · deal: atmospheric 3/3 (spore, coral, kiln) · draw: 398f00 · shape: Manifesto · genre: atmospheric · job: visit · hero: Poster · nav: slab · footer: colophon block · signature: the latest reel as a poster card · posture: full-palette · copy: verbatim (#5 caption, user-approved 2026-11-15) */
/* Hallmark · pre-emit critique: P4 H4 E4 S5 R4 V4 · weakest: E, unbuilt; sweep after build */
/* Hallmark · waive 29 · two fixed-size ember radial blooms, 24% of canvas, transform-only drift, frozen under reduced motion · user asked for future-based motion */
/* Hallmark · waive 81 · blooms are aria-hidden decor divs; the page's real picture is the latest-reel poster frame, which loads · user asked for future-based glow motion */
/* Hallmark · finish-review: subagent · 6 findings · 6 resolved · gap: none */
/* Hallmark · answered F2 · hooks keep their ellipsis; they are approved caption copy */
/* User direction over the theme: glassy wells (backdrop blur) and amber neon motion, per "animation look like future based". */
:root {
  --color-paper: oklch(13% 0.012 40); --color-paper-2: oklch(17.5% 0.016 40); --color-paper-3: oklch(22% 0.018 40);
  --color-ink: oklch(94% 0.02 80); --color-ink-2: oklch(84% 0.025 70); --color-muted: oklch(72% 0.03 60);
  --color-rule: oklch(96% 0.01 80 / 0.12);
  --color-accent: oklch(70% 0.2 45); --color-accent-ink: oklch(14% 0.02 40); --color-focus: oklch(76% 0.19 56);
  --heat-2: oklch(40% 0.16 27);
  --font-display: "Boska", "Iowan Old Style", Georgia, serif; --font-body: "Geist", ui-sans-serif, system-ui, sans-serif;
  --radius-card: 28px; --radius-well: 16px; --radius-pill: 999px; --rule-hair: 1px;
  --space-xs: 8px; --space-sm: 12px; --space-md: 16px; --space-lg: 24px; --space-xl: 40px; --space-2xl: 64px; --space-3xl: 96px;
  --section-gap-s: 56px; --section-gap: 80px; --section-gap-l: 120px;
  --dur-short: 160ms; --dur-long: 700ms; --ease-out: cubic-bezier(0.22, 1, 0.36, 1);
  --text-display: clamp(56px, 8vw, 108px); --text-section: clamp(32px, 4vw, 48px); --text-title: 22px;
}
*, *::before, *::after { box-sizing: border-box; }
html, body { overflow-x: clip; }
html { scrollbar-color: var(--color-muted) var(--color-paper); }
body {
  margin: 0; background: var(--color-paper); color: var(--color-ink);
  font-family: var(--font-body); font-size: 17px; line-height: 1.55;
  -webkit-font-smoothing: antialiased;
}
::selection { background: color-mix(in oklab, var(--color-accent) 35%, transparent); }
a { color: var(--color-ink); }
a:focus-visible, button:focus-visible { outline: 2px solid var(--color-focus); outline-offset: 3px; }
h1, h2, h3 { font-family: var(--font-display); font-weight: 500; line-height: 1.04; letter-spacing: -0.02em; overflow-wrap: break-word; min-width: 0; margin: 0; text-wrap: balance; }
h1 { font-size: var(--text-display); line-height: 1.0; }
h2 { font-size: var(--text-section); }
p { margin: 0; }
.wrap { max-width: 1360px; margin: 0 auto; padding: 0 var(--space-lg); }
@media (min-width: 900px) { .wrap { padding: 0 var(--space-xl); } }
.bloom { position: fixed; z-index: 0; border-radius: 50%; pointer-events: none;
  background: radial-gradient(circle, color-mix(in oklab, var(--color-accent) 16%, transparent) 0%, transparent 70%);
  animation: drift 46s var(--ease-out) infinite alternate; }
.bloom-a { width: 26vw; height: 26vw; min-width: 320px; min-height: 320px; top: -6vw; right: -4vw; }
.bloom-b { width: 22vw; height: 22vw; min-width: 280px; min-height: 280px; bottom: -8vw; left: -6vw; animation-duration: 58s; animation-delay: -20s; }
@keyframes drift { from { transform: translate3d(0, 0, 0); } to { transform: translate3d(-4vw, 3vh, 0); } }
.slab { position: relative; z-index: 1; border-bottom: var(--rule-hair) solid var(--color-rule); background: color-mix(in oklab, var(--color-paper) 82%, transparent); backdrop-filter: blur(14px); }
.slab-in { display: flex; align-items: center; justify-content: space-between; gap: var(--space-md); min-height: 64px; flex-wrap: wrap; padding-top: var(--space-sm); padding-bottom: var(--space-sm); }
.wordmark { font-family: var(--font-display); font-weight: 500; font-size: 22px; letter-spacing: -0.02em; color: var(--color-ink); text-decoration: none; white-space: nowrap; }
.navlinks { display: flex; gap: var(--space-lg); flex-wrap: wrap; }
.navlinks a { font-size: 15px; font-weight: 500; color: var(--color-ink-2); text-decoration: none; transition: color var(--dur-short) var(--ease-out); }
.navlinks a:hover { color: var(--color-ink); }
main { position: relative; z-index: 1; }
.hero { padding: var(--section-gap-l) 0 var(--section-gap); }
.hero p.lede { font-size: 19px; color: var(--color-ink-2); max-width: 32ch; margin-top: var(--space-md); }
.actions { display: flex; gap: var(--space-md); flex-wrap: wrap; margin-top: var(--space-lg); }
.btn { display: inline-flex; align-items: center; min-height: 50px; padding: 0 var(--space-lg); border-radius: var(--radius-pill); font-weight: 500; font-size: 16px; text-decoration: none; white-space: nowrap; transition: background-color var(--dur-short) var(--ease-out), box-shadow var(--dur-short) var(--ease-out), color var(--dur-short) var(--ease-out); }
.btn--primary { background: var(--color-accent); color: var(--color-accent-ink); box-shadow: 0 0 32px color-mix(in oklab, var(--color-accent) 32%, transparent); }
.btn--primary:hover { background: var(--color-focus); }
.btn:active { transform: translateY(1px); }
.navlinks a:active, .links a:active { color: var(--color-accent); }
.btn--ghost { background: transparent; color: var(--color-ink); box-shadow: inset 0 0 0 var(--rule-hair) var(--color-rule); }
.btn--ghost:hover { box-shadow: inset 0 0 0 var(--rule-hair) var(--color-ink-2); }
.poster { margin-top: var(--space-2xl); }
.well { background: color-mix(in oklab, var(--color-paper-2) 72%, transparent); backdrop-filter: blur(14px); border: var(--rule-hair) solid var(--color-rule); border-radius: var(--radius-well); }
.poster-card { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--space-md); padding: var(--space-lg); max-width: 880px; }
.poster-card img { width: 100%; height: 180px; object-fit: cover; object-position: center 30%; border-radius: var(--radius-well); display: block; }
@media (min-width: 760px) { .poster-card { grid-template-columns: 216px minmax(0, 1fr); align-items: center; } .poster-card img { height: auto; aspect-ratio: 9 / 16; } }
.poster-card .poster-title { font-size: var(--text-title); margin-top: var(--space-sm); }
.poster-card .hook { color: var(--color-ink-2); margin-top: var(--space-sm); max-width: 65ch; }
.meta { font-size: 15px; font-weight: 500; color: var(--color-muted); }
.nowrap { white-space: nowrap; }
.links { display: flex; gap: var(--space-md); flex-wrap: wrap; margin-top: var(--space-md); }
.links a { font-size: 15px; font-weight: 500; color: var(--color-ink); text-decoration: underline; text-decoration-color: var(--color-rule); text-underline-offset: 4px; transition: text-decoration-color var(--dur-short) var(--ease-out); }
.links a:hover { text-decoration-color: var(--color-accent); }
section { padding: var(--section-gap) 0; }
section.status { padding: var(--section-gap-s) 0; }
section + section { border-top: var(--rule-hair) solid var(--color-rule); }
section > .wrap > h2 { margin-bottom: var(--space-lg); }
.rows { display: grid; gap: var(--space-md); }
.row { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--space-sm); padding: var(--space-md) var(--space-lg); }
.row.row--solo { grid-template-columns: minmax(0, 1fr); }
@media (min-width: 760px) { .row { grid-template-columns: 150px minmax(0, 1fr); align-items: start; } }
.row h3 { font-size: var(--text-title); }
.row .hook { color: var(--color-ink-2); margin-top: 4px; max-width: 65ch; }
.row time { font-size: 15px; font-weight: 500; color: var(--color-muted); }
.state { display: inline-flex; align-items: center; gap: var(--space-sm); font-size: 15px; font-weight: 500; }
.marker { width: 9px; height: 9px; border-radius: 50%; flex: none; background: var(--color-muted); }
.marker--live { background: var(--color-accent); box-shadow: 0 0 12px color-mix(in oklab, var(--color-accent) 65%, transparent); animation: pulse 2.4s var(--ease-out) infinite; }
.marker--failed { background: var(--heat-2); }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
.status-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: var(--space-md); }
.status-cell { padding: var(--space-md) var(--space-lg); }
.status-cell .pname { font-weight: 500; }
.status-cell .detail { font-size: 15px; color: var(--color-muted); margin-top: 4px; overflow-wrap: break-word; }
.note { color: var(--color-muted); max-width: 65ch; }
footer { border-top: var(--rule-hair) solid var(--color-rule); padding: var(--space-2xl) 0 var(--space-3xl); position: relative; z-index: 1; }
footer .cols { display: grid; gap: var(--space-md); }
@media (min-width: 760px) { footer .cols { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); } }
footer p { color: var(--color-muted); font-size: 15px; max-width: 65ch; }
footer a { color: var(--color-ink-2); }
.js .reveal { opacity: 0; transform: translateY(14px); transition: opacity var(--dur-long) var(--ease-out), transform var(--dur-long) var(--ease-out); }
.js .reveal.in { opacity: 1; transform: translateY(0); }
@media (prefers-reduced-motion: reduce) {
  .bloom, .marker--live { animation: none; }
  .js .reveal { opacity: 1; transform: none; transition: none; }
  * { scroll-behavior: auto; }
}
"""

JS = """<script>
document.documentElement.classList.add('js');
(function () {
  var els = document.querySelectorAll('.reveal');
  if (!('IntersectionObserver' in window)) {
    els.forEach(function (el) { el.classList.add('in'); });
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    });
  }, { threshold: 0.12 });
  els.forEach(function (el) { io.observe(el); });
})();
</script>"""


def platform_links(urls):
    out = []
    for key, label in PLATFORM_LABELS:
        url = (urls or {}).get(key)
        if url:
            out.append(f'<a href="{esc(url)}">{label}</a>')
    return "".join(out)


def refresh_poster(cfg, queue):
    """Re-extract the latest reel's poster frame (540x960) when its source
    video is in the repo. Returns True when assets/poster-latest.jpg exists
    afterwards. A missing source (e.g. local generation before the videos
    are uploaded) keeps whatever poster is already there."""
    out = os.path.join(ROOT, "assets", "poster-latest.jpg")
    done = [i for i in queue.get("items", [])
            if i.get("status") == "done" and i.get("source")]
    if not done:
        return os.path.exists(out)
    latest = max(done, key=lambda i: str(i.get("posted_date", "")))
    src = os.path.join(ROOT, cfg["video_dir"], latest["source"])
    if not os.path.exists(src):
        return os.path.exists(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-ss", "2",
                        "-frames:v", "1", "-vf",
                        "scale=540:960:force_original_aspect_ratio=increase,"
                        "crop=540:960", out], check=True)
    except Exception as e:  # noqa: BLE001 - keep the old poster, note it
        print(f"poster: ffmpeg failed ({e}); keeping existing poster",
              file=sys.stderr)
        return os.path.exists(out)
    return True


def render(account_slug):
    acct_dir = os.path.join(ROOT, "accounts", account_slug)
    cfg = load_yaml(os.path.join(acct_dir, "config.yaml"))
    queue = load_yaml(os.path.join(ROOT, cfg["queue_file"]))
    refresh_poster(cfg, queue)
    last_path = os.path.join(acct_dir, "last_run.json")
    last = None
    if os.path.exists(last_path):
        with open(last_path) as f:
            last = json.load(f)

    items = queue.get("items", [])
    done = [i for i in items if i.get("status") == "done" and i.get("urls")]
    done.sort(key=lambda i: str(i.get("posted_date", "")), reverse=True)
    pending = [i for i in items if i.get("status") == "pending"]
    latest = done[0] if done else None
    latest_url = None
    if latest:
        latest_url = (latest.get("urls") or {}).get("instagram") or \
            (latest.get("urls") or {}).get("youtube")

    generated = datetime.datetime.now(IST).strftime("%d %B %Y, %H:%M IST")

    # --- status cells ---
    if last and last.get("results"):
        cells = []
        for key, label in PLATFORM_LABELS:
            if key in ("instagram", "facebook"):
                r = last["results"].get("meta", {})
                state = "live" if (r.get("urls") or {}).get(key) else r.get("status", "skipped")
                detail = (r.get("urls") or {}).get(key, "") or r.get("reason", "")
            else:
                r = last["results"].get(key, {})
                state = r.get("status", "skipped")
                detail = (r.get("urls") or {}).get(key, "") or r.get("reason", "") or r.get("detail", "")
            marker = "marker--live" if state in ("ok", "live") else \
                "marker--failed" if state == "failed" else ""
            state_text = {"ok": "live", "live": "live"}.get(state, state)
            cells.append(
                f'<div class="well status-cell reveal"><p class="pname">{label}</p>'
                f'<p class="state"><span class="marker {marker}" aria-hidden="true"></span>'
                f'<span role="status">{esc(state_text)}</span></p>'
                + (f'<p class="detail">{esc(detail)}</p>' if detail else "") +
                '</div>'
            )
        status_html = "".join(cells)
        status_note = (f'<p class="note" style="margin-top: var(--space-md)">'
                       f"Last run {esc(fmt_date(last.get('run_date_ist')))}"
                       + (f", clip #{last.get('item_id')}" if last.get("item_id") else "")
                       + "</p>")
    else:
        setup = cfg.get("setup", {}) or {}
        cells = []
        for key, label in PLATFORM_LABELS:
            plat = "meta" if key in ("instagram", "facebook") else key
            state_text, detail = SETUP_DETAILS.get(
                setup.get(plat, "awaiting-token"),
                ("Awaiting token", "Authorisation pending"))
            marker = "marker--live" if state_text == "Wired" else ""
            cells.append(
                f'<div class="well status-cell reveal"><p class="pname">{label}</p>'
                f'<p class="state"><span class="marker {marker}" aria-hidden="true"></span>'
                f'<span role="status">{esc(state_text)}</span></p>'
                f'<p class="detail">{esc(detail)}</p>'
                f'</div>'
            )
        status_html = "".join(cells)
        status_note = (
            '<p class="note" style="margin-top: var(--space-md)">'
            'The first automated run hasn\u2019t happened yet. '
            'The daily run posts one clip at 17:00 IST.</p>')

    # --- posted ledger ---
    if done:
        rows = []
        for it in done:
            rows.append(
                f'<article class="well row reveal">'
                f'<time datetime="{esc(it.get("posted_date", ""))}">{esc(fmt_date(it.get("posted_date")))}</time>'
                f'<div><h3>{esc(it.get("title", ""))}</h3>'
                f'<p class="hook">{hook_html(it.get("hook", ""))}</p>'
                f'<p class="links">{platform_links(it.get("urls"))}</p></div>'
                f'</article>'
            )
        posted_html = '<div class="rows">' + "".join(rows) + "</div>"
    else:
        posted_html = '<p class="note">Nothing posted yet.</p>'

    # --- next queue ---
    if pending:
        rows = []
        for it in pending:
            rows.append(
                f'<article class="well row row--solo reveal">'
                f'<div><h3>{esc(it.get("title", ""))}</h3>'
                f'<p class="hook">{hook_html(it.get("hook", ""))}</p>'
                f'<p class="meta">Clip {esc(it.get("id"))}</p></div>'
                f'</article>'
            )
        next_html = '<div class="rows">' + "".join(rows) + "</div>"
    else:
        next_html = '<p class="note">The queue is empty. New clips will appear here.</p>'

    # --- hero poster card (latest reel) ---
    if latest:
        img = ""
        if os.path.exists(os.path.join(ROOT, "assets", "poster-latest.jpg")):
            img = (f'<img src="assets/poster-latest.jpg" width="540" height="960" '
                   f'alt="Still from {esc(latest.get("title", ""))}">')
        poster = (
            f'<div class="well poster-card reveal">{img}<div><p class="meta">Latest reel, '
            f'{esc(fmt_date(latest.get("posted_date")))}</p>'
            f'<h2 class="poster-title">{esc(latest.get("title", ""))}</h2>'
            f'<p class="hook">{hook_html(latest.get("hook", ""))}</p>'
            f'<p class="links">{platform_links(latest.get("urls"))}</p></div></div>'
        )
        primary = (f'<a class="btn btn--primary" href="{esc(latest_url)}">Watch the latest reel</a>'
                   if latest_url else "")
    else:
        poster = ""
        primary = ""

    nav = "".join(
        f'<a href="{esc(url)}">{label}</a>' for label, url in PROFILE_URLS
    )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI World Clips: daily reels, posted</title>
<meta name="description" content="AI World Clips posts one short video a day. See what went live, what is next, and the status of every platform.">
<link rel="preconnect" href="https://api.fontshare.com" crossorigin>
<link rel="preconnect" href="https://fonts.googleapis.com" crossorigin>
<link href="https://api.fontshare.com/v2/css?f[]=boska@500&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500&display=swap" rel="stylesheet">
<style>
{CSS}</style>
</head>
<body>
<div class="bloom bloom-a" aria-hidden="true"></div>
<div class="bloom bloom-b" aria-hidden="true"></div>
<header class="slab"><div class="wrap slab-in">
<a class="wordmark" href="./">AI World Clips</a>
<nav class="navlinks" aria-label="Channel profiles">{nav}</nav>
</div></header>
<main>
<section class="hero"><div class="wrap">
<h1>AI World Clips</h1>
<p class="lede">One short video a day, everywhere you watch.</p>
<div class="actions">{primary}<a class="btn btn--ghost" href="#next">See what&rsquo;s next</a></div>
<div class="poster">{poster}</div>
</div></section>
<section class="status"><div class="wrap">
<h2>Platforms, right now</h2>
<div class="status-grid">{status_html}</div>{status_note}
</div></section>
<section><div class="wrap">
<h2>Posted, one a day</h2>
{posted_html}
</div></section>
<section id="next"><div class="wrap">
<h2>Next up at 17:00</h2>
{next_html}
</div></section>
</main>
<footer><div class="wrap cols">
<p>AI World Clips posts one short video a day at 17:00 IST. This page is generated from the posting queue after every run.</p>
<p>Source code: <a href="https://github.com/mandeep95/ai-world-clips-auto">github.com/mandeep95/ai-world-clips-auto</a><br>Page generated {esc(generated)}.<br>Type: Boska and Geist.</p>
</div></footer>
{JS}
</body>
</html>
"""
    return page


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", default="ai-world-clips")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out = args.out or os.path.join(ROOT, "index.html")
    page = render(args.account)
    with open(out, "w") as f:
        f.write(page)
    print(f"Wrote {out} ({len(page)} bytes)")


if __name__ == "__main__":
    main()
