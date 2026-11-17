# Setup — AI World Clips automation

Do the steps in order. Nothing here costs money; everything is a free tier.
Total hands-on time: about 1 hour (plus waiting on Google for step 5).

## Step 0 — Create the repo (1 minute, your click)

The code is built and ready to push, but the GitHub integration connected
here can read and write repositories — it cannot *create* one (GitHub
answers `403 Resource not accessible by integration`). So this one step is
yours:

1. Open https://github.com/new (signed in as **mandeep95**).
2. **Repository name:** `ai-world-clips-auto`. Select **Public**.
3. Leave **all** the initialise boxes unticked — no README, no .gitignore,
   no licence. The repo must be **empty** for the first push.
4. Click **Create repository**.
5. If the GitHub App for Muse was installed for "Only select repositories",
   also add the new repo to it: GitHub → Settings → Applications → Muse →
   Configure → Repository access → add `ai-world-clips-auto`. (If it was
   installed for "All repositories", skip this.)
6. Tell Deep "repo created" — he pushes the code immediately and verifies
   it landed.

## Step 1 — Upload the videos (10 files, ~196 MB) + poster frame

The build could not push binary files, so the videos are not in the repo yet.
Without them the runner skips every run with "video file missing". The
status site also needs one small image, `poster-latest.jpg` (a frame from
the latest reel, 33 KB) — it is in the same handover folder as the videos.

**Option A — from your Mac (easiest):**
```bash
git clone https://github.com/mandeep95/ai-world-clips-auto.git
cd ai-world-clips-auto
bash scripts/upload_videos.sh /path/to/videos-folder
```
(The videos folder was handed over with this build — 10 `.mp4` files plus
`poster-latest.jpg`. The script copies the poster to `assets/` as well.)

**Option B — GitHub web UI:** open the repo → `accounts/ai-world-clips/videos/`
→ **Add file → Upload files** → drag the 10 files in → Commit. Each file is
under GitHub's 100 MB per-file limit (largest is 62 MB). Then upload
`poster-latest.jpg` to `assets/` the same way (Add file → Upload files).

Verify: open `accounts/ai-world-clips/videos/MANIFEST.md` in the repo and
check the file list matches (names + sizes). SHA-256 hashes are in the
manifest if you want to be exact.

> Why a public repo? Threads can only fetch a video from a **public URL**.
> The clips are already published publicly on YouTube, Threads, Facebook,
> Instagram and Dailymotion, so a public repo adds no new exposure — and it
> avoids paying for, and maintaining, a second host (e.g. Cloudflare R2).
> No secrets are ever in the repo — tokens live only in repo secrets.

## Step 2 — Add the repo secrets

Repo → **Settings → Secrets and variables → Actions → New repository secret**.
Add each of these (names must match exactly):

| Secret | Value — where to get it |
|---|---|
| `AWC_META_PAGE_ID` | `1434747539720565` |
| `AWC_META_PAGE_TOKEN` | The long-lived Page token. Copy `PAGE_ACCESS_TOKEN` from the file `~/workspace/ai-world-clips-api/.env` on the build machine (or ask Deep — it is already stored there). **Never paste it in chat.** |
| `AWC_META_IG_USER_ID` | `17841471858921184` (optional — the runner resolves it from the Page if missing) |
| `AWC_THREADS_TOKEN` | From step 3 |
| `AWC_THREADS_USER_ID` | From step 3 |
| `AWC_DM_CLIENT_ID` | From step 4 (Dailymotion API key) |
| `AWC_DM_CLIENT_SECRET` | From step 4 (Dailymotion API secret) |
| `AWC_DM_REFRESH_TOKEN` | From step 4 |
| `AWC_YT_CLIENT_ID` | From step 5 (Google Cloud OAuth client ID) |
| `AWC_YT_CLIENT_SECRET` | From step 5 |
| `AWC_YT_REFRESH_TOKEN` | From step 5 |

Platforms with missing secrets are **skipped, not failed** — the run posts
to whatever is configured and reports the rest as "not configured".

## Step 3 — Threads token (~10 min, your browser)

1. Open the Meta app **AI World Clips Poster** at
   https://developers.facebook.com/apps/1153715580860968/dashboard/
   → **Add product / use case → Threads API** (or "Threads" use case).
   Note the **Threads app ID** and **Threads app secret** — a Threads app has
   its own ID/secret, different from the Facebook app's.
2. In the app dashboard, add a redirect URI you will use for the token
   helper, e.g. `http://127.0.0.1:8080/` (App Dashboard → Threads API →
   Settings / Redirect URIs).
3. Add your Threads profile as a tester: **App Dashboard → App roles →
   Roles → Add People → Threads Tester** → invite `@aiwo.rldclips`.
   Accept the invite in Threads → Settings → Account → Website permissions.
   (No App Review needed — you are posting to your own account. Review is
   only needed to post for *other* people's accounts.)
4. On your own machine:
   ```bash
   THREADS_APP_ID=<threads app id> THREADS_APP_SECRET=<threads app secret> \
     python3 scripts/threads_auth.py
   ```
   Open the URL it prints, grant `threads_basic` + `threads_content_publish`,
   paste the redirect URL back. It prints `AWC_THREADS_TOKEN` and
   `AWC_THREADS_USER_ID` — save both as repo secrets.
   (Long-lived token: valid 60 days. Re-run the helper when it expires.)

## Step 4 — Dailymotion token (~10 min, your browser)

1. Sign in to Dailymotion (the AI World Clips account) → **Settings →
   API Keys** (or https://www.dailymotion.com/settings/developer) →
   **Create a new API key**. Name it e.g. "AI World Clips Auto", callback URL
   `http://127.0.0.1:8080/`. Note the **API key** (= client ID) and **API
   secret**.
2. On your own machine:
   ```bash
   DM_CLIENT_ID=<api key> DM_CLIENT_SECRET=<api secret> \
     python3 scripts/dm_auth.py
   ```
   Open the URL it prints, grant the `video.manage` scope, paste the
   redirect URL back. It prints `AWC_DM_REFRESH_TOKEN` — save it plus the
   client ID/secret as repo secrets. The runner mints a fresh access token
   from the refresh token on every run.

## Step 5 — YouTube token (~20 min, your browser) + verification

1. **Google Cloud Console** (https://console.cloud.google.com) → create a
   project (e.g. "AI World Clips Auto") → **APIs & Services → Library** →
   enable **YouTube Data API v3**.
2. **APIs & Services → OAuth consent screen** → User type **External** →
   fill app name + support email → add scope
   `https://www.googleapis.com/auth/youtube.upload` → add yourself
   (Devdeeep2000@gmail.com) as a test user.
3. **IMPORTANT — stop the 7-day expiry:** on the same consent screen, click
   **Publish app** (Publishing status → Production). A refresh token minted
   while the app is in Testing mode expires after 7 days; publishing stops
   that. (For your own use Google does not require the full verification
   audit to publish — it flips immediately. The "unverified app" warning on
   the consent screen is expected.)
4. **Credentials → Create Credentials → OAuth client ID → Desktop app.**
   Note the client ID + secret.
5. On your own machine:
   ```bash
   YT_CLIENT_ID=<id> YT_CLIENT_SECRET=<secret> python3 scripts/yt_auth.py
   ```
   Open the URL, sign in as the channel owner, grant access, paste the
   redirect URL back. It prints `AWC_YT_REFRESH_TOKEN` — save it plus the
   client ID/secret as repo secrets.

### YouTube verification (uploads go public)

Until Google verifies the API project, **every video uploaded through the
API is forced PRIVATE** (Google rule for unverified projects). The runner
reports this honestly in the run summary — it never claims a public Short
when the upload landed private.

To lift it, submit the app for YouTube API verification:
1. In Google Cloud Console → OAuth consent screen → **Prepare for
   verification** / **Submit for verification**.
2. Google asks for: a **demo video** (screen recording showing the OAuth
   sign-in, the upload, and the Short live) and a **privacy policy** page.
   Both are prepared for you in `docs/youtube-verification/`:
   - `demo-video-script.md` — shot-by-shot script, ~3 minutes.
   - `privacy-policy.html` — ready-to-host page. Publish it anywhere public
     (e.g. GitHub Pages from this repo, or your own site) and give Google
     that URL.
3. Review typically takes a few days. You will get an email; if Google asks
   for changes, they say exactly what is missing.
4. Once verified, uploads go public automatically — no code change needed.

## Step 6 — Dry run (no posting)

Actions → **Daily AI World Clips post** → Run workflow → tick **dry_run**.
It converts the next clip, checks the dimensions, and prints the exact
request each platform would make — posting nothing. The run summary shows
which platforms are configured and which are still missing secrets.

## Step 7 — First live run + switch-over

1. Actions → Run workflow (dry_run off). Check the run summary: each
   platform should show ✅ with a live URL.
2. Verify the posts by opening the URLs (Instagram Reel, Facebook video,
   Threads post, Dailymotion video, YouTube Short).
3. Only then switch over: the old daily routine (`ai-world-clips-daily`,
   browser-based) keeps running until you say so. When the API route has
   posted cleanly for 2–3 days, disable the old routine.
4. After the first live run, `queue.yaml` in the repo shows item #8 marked
   done with its live URLs — that is the runner's own record.

## Step 8 — Turn on the public status site

The repo contains a public status page (`index.html` at the root, generated
by `scripts/render_site.py` after every run). To publish it:

1. Repo → **Settings → Pages**.
2. Under **Build and deployment → Source**, choose **Deploy from a branch**.
3. **Branch:** `main`, **Folder:** `/(root)` → **Save**.
4. Wait a few minutes for the first publish, then open
   **https://mandeep95.github.io/ai-world-clips-auto/**

The page shows the latest reel (with its real poster frame), per-platform
status, the Posted ledger with live links, and the Next up queue. The daily
workflow regenerates it after every run, so it stays current with no manual
work. Held clips (including the copyright-flagged #3) are never shown.

## If a run fails

- Open the failed run in Actions → read the per-platform lines. Each
  platform reports its own exact error (e.g. `invalid_grant` = token
  expired → re-run the matching `*_auth.py` helper and update the secret).
- A failed platform never blocks the others, and a clip is never re-posted
  where it already went live. If **all** platforms fail, the item stays
  `pending` and is tried again the next day.
- Never edit `queue.yaml` by hand to mark something done — the runner owns
  that file. To skip a clip, set its status to `skipped` (with a note) and
  commit.
