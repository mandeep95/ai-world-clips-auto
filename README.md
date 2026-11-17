# AI World Clips — standalone daily poster

Posts one short video a day to **Facebook, Instagram, Threads, Dailymotion
and YouTube** — with no AI key, no agent and no browser at runtime. One
Python script reads the next pending clip from the queue, converts it to
1080×1920 9:16 with ffmpeg, and posts it through each platform's official
API. It runs on GitHub Actions (free), daily at 17:00 IST.

**Rumble is deliberately excluded** — it has no upload API, so it cannot be
automated this way.

## How it works

```
queue.yaml  ──>  post_all.py  ──>  ffmpeg convert (1080x1920)
                                  ├─ Meta API      → Facebook Page video + Instagram Reel
                                  ├─ Threads API   → video post (fetches the clip from this repo)
                                  ├─ Dailymotion   → API v2 upload + publish
                                  └─ YouTube API   → videos.insert (Short)
                              ──>  queue.yaml updated + committed back
```

- Each platform is isolated: one failure stops only that platform, reports
  the exact error, and never retries in a loop. A clip is never re-posted
  where it already went live.
- Hooks are baked into `queue.yaml` — the runner needs no AI at runtime.
- Secrets live only in GitHub repo secrets, never in the repo.

## Status (2026-11-17, build day)

| Piece | State |
|---|---|
| Repo | ⏳ Needs creating (1 min, your click — the GitHub integration cannot create repos; see `docs/SETUP.md` step 0). Code is built and ready to push. |
| Meta (Facebook + Instagram) | ✅ Fully wired. Script logic already proven live (FB unpublished upload + IG container FINISHED, 2026-11-17). Needs only the repo secret. |
| Threads | 🟡 Code written + verified against official Meta docs. Needs the Threads use-case token (user step, ~10 min). |
| Dailymotion | 🟡 Code written + verified against official Dailymotion docs. Needs a free API key + token (user step, ~10 min). |
| YouTube | 🟡 Code written + verified against official Google docs. Needs a Google Cloud OAuth client + refresh token (user step, ~20 min) **and** YouTube verification before uploads go public (see below). |
| Videos in repo | ⏳ Not uploaded yet — see `docs/SETUP.md` step 1. |
| Public status site | ✅ Built. `index.html` generated from the queue + last run; published free via GitHub Pages once the repo exists — see `docs/SETUP.md` step 8. Live at https://mandeep95.github.io/ai-world-clips-auto/ |
| Daily schedule | ✅ `.github/workflows/daily.yml` — 11:30 UTC (17:00 IST) + manual dispatch. |

## Public status site

**https://mandeep95.github.io/ai-world-clips-auto/** (GitHub Pages, free,
no backend). It shows the channel, the latest reel as a poster card with
its real frame and live links, per-platform status, the Posted ledger
(date, title, hook, links to all five platforms), and the Next up queue.
The daily workflow regenerates it after every run (`scripts/render_site.py`
reads `queue.yaml` + `last_run.json`), and the latest reel's poster frame
(`assets/poster-latest.jpg`) is re-extracted from the posted clip. Held
clips are never shown.

Design: Hallmark, Kiln theme (ember), Manifesto shape, Poster hero —
near-black ground, cream ink, Boska display over Geist body, one amber
signal. Futuristic motion per the brief: slow drifting ember blooms,
glassy wells, neon ember button, pulsing live markers — transform/opacity
only, frozen under `prefers-reduced-motion`, content visible with
scripting off. Sloplint sweep: 0 FAIL (1 WARN, a false positive — the
render tier claims the webfonts did not load, but the screenshots show
Boska rendering and all four font hosts return HTTP 200; 1 waived gate,
81, the blooms are decor; 2 notes: a verbatim approved caption and the
Posted ledger's word count). Finish review in fresh context: 6 findings,
all 6 resolved (Next up rows filled, status dots vary by state, poster
card capped, channel-own section heads, visitor-facing setup copy, no
orphan emoji lines).

**Hallmark · v2.0.0**

- **Shape** · Manifesto, from draw 398f00 · genre atmospheric · job: visit, the action in the hero and the queue below
- **Theme** · Kiln, dealt 3/3 (spore, coral, kiln), ember colourway · near-black ground, cream ink, Boska display over Geist body, one ember signal
- **Chrome** · nav: slab, wordmark + profile links · footer: colophon block, one sentence + source link + generation time + type credit
- **Hero** · Poster: the latest reel as a poster card, headline + one sentence + two actions
- **Signature** · the latest reel as a poster card, with its real frame and live links
- **Sections** · Hero (latest reel poster) · Platform status (five cells) · Posted (ledger, newest first) · Next up (queue in order) · Footer
- **Material** · real: the queue, the posted reels and their live URLs, the real poster frame · pictures: the latest reel's frame · absent: held clips (including the copyright-flagged #3), invented metrics, dates
- **Sweep** · run after build — Floor 0 FAIL · Reflex 1 (1 waived: 81) · finish-review: subagent, 6 resolved

## YouTube — read this first

Two Google-side rules affect YouTube:

1. **Refresh tokens from an OAuth app in Testing mode expire after 7 days.**
   Fix: set the consent screen to **Production** and re-authorise once.
   (5 minutes, no review needed for your own use.)
2. **Videos uploaded by an unverified API project are forced PRIVATE.**
   Fix: full YouTube API verification (Google audit). Until it is done,
   uploads land private — the runner says so in the run summary instead of
   claiming a public Short. Verification materials are prepared in
   `docs/youtube-verification/` (demo-video script + privacy policy draft).

## Setup

See [`docs/SETUP.md`](docs/SETUP.md) — one page, in order:
1. Upload the videos, 2. Add the repo secrets, 3. Mint the three missing
tokens, 4. Run a dry-run, 5. First live run.

## Adding another account

The repo is multi-account from the start: one folder per account under
`accounts/`, one config + queue + videos each, secrets prefixed per account
(`AWC_…` for AI World Clips). See [`docs/ADD_ACCOUNT.md`](docs/ADD_ACCOUNT.md).

## Run it locally

```bash
pip install -r scripts/requirements.txt
python3 scripts/post_all.py --account ai-world-clips --dry-run
```
