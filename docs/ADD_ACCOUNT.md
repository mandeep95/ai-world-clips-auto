# Adding another account

The repo is multi-account by design. Each account is one folder under
`accounts/` plus its own set of repo secrets. No code changes needed.

## 1. Copy the account folder

```bash
cp -r accounts/ai-world-clips accounts/my-new-account
cd accounts/my-new-account
rm -rf videos/*.mp4   # keep MANIFEST.md out too — rewrite it for the new clips
```

Then edit:

- **`config.yaml`** — set `slug`, `name`, `env_prefix` (a short unique
  prefix, e.g. `ACCT2`), `queue_file`, `video_dir`, `video_public_base`
  (same repo, new folder path), `caption_footer`, `hashtags`, platform
  toggles, and the Dailymotion category / YouTube category if they differ.
- **`queue.yaml`** — replace the items with the new account's clips
  (id, index, title, source file name, hook, status `pending`).
- **`videos/MANIFEST.md`** — rewrite with the new files' names, sizes and
  SHA-256 hashes (`sha256sum *.mp4`).

## 2. Upload the new account's videos

Same as the first account: `scripts/upload_videos.sh` (it takes the account
folder as a second argument in future — for now copy the files into
`accounts/<slug>/videos/` in a clone and push), or the GitHub web UI.
Every file must be under 100 MB.

## 3. Add the new account's secrets

Same secret names as the first account, but with the new prefix. E.g. for
prefix `ACCT2`:
`ACCT2_META_PAGE_ID`, `ACCT2_META_PAGE_TOKEN`, `ACCT2_META_IG_USER_ID`,
`ACCT2_THREADS_TOKEN`, `ACCT2_THREADS_USER_ID`, `ACCT2_DM_CLIENT_ID`,
`ACCT2_DM_CLIENT_SECRET`, `ACCT2_DM_REFRESH_TOKEN`, `ACCT2_YT_CLIENT_ID`,
`ACCT2_YT_CLIENT_SECRET`, `ACCT2_YT_REFRESH_TOKEN`.

Each platform needs its own tokens: a Meta app per Facebook Page/Instagram
account (or the same app if the Page is under the same business), a Threads
token per Threads profile, a Dailymotion key per channel, a YouTube refresh
token per channel. Mint them with the same `scripts/*_auth.py` helpers —
just save the results under the new prefix.

## 4. Run it

Actions → Daily AI World Clips post → Run workflow → account =
`my-new-account` → dry_run on first. Check the summary, then run live.

The daily schedule currently runs only `ai-world-clips`. To run a second
account daily too, add a second job (or a matrix over accounts) in
`.github/workflows/daily.yml` — a small edit; the runner already takes
`--account`.
