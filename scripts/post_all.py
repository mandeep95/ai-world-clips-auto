#!/usr/bin/env python3
"""Standalone daily poster for AI World Clips (and other accounts).

No AI keys, no agent at runtime. Reads the next pending item from the
account's queue, converts the clip to 1080x1920 9:16, and posts it to every
enabled platform through its official API. Each platform is isolated: one
failure stops only that platform and is reported exactly — never retried in
a loop, never re-posted where it already went live.

Usage:
    python3 scripts/post_all.py --account ai-world-clips [--dry-run] [--item 8]

Credentials come from environment variables named <PREFIX>_<NAME>, where
PREFIX is the account's env_prefix in its config.yaml:
    Meta:        <P>_META_PAGE_ID, <P>_META_PAGE_TOKEN, <P>_META_IG_USER_ID (optional)
    Threads:     <P>_THREADS_TOKEN, <P>_THREADS_USER_ID (optional, resolved via /me)
    Dailymotion: <P>_DM_CLIENT_ID, <P>_DM_CLIENT_SECRET, <P>_DM_REFRESH_TOKEN
                 (+ <P>_DM_ACCESS_TOKEN as a fallback if no refresh token)
    YouTube:     <P>_YT_CLIENT_ID, <P>_YT_CLIENT_SECRET, <P>_YT_REFRESH_TOKEN

Exit codes: 0 = posted, nothing pending, or skipped cleanly (setup
incomplete / all platforms failed — item stays pending for the next run);
1 = fatal error (bad queue/config, conversion failed).
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml  # noqa: E402

from convert import convert_to_9x16, probe  # noqa: E402
from queuefile import find_item, load_queue, next_pending, save_queue  # noqa: E402
from platforms.meta import post_meta  # noqa: E402
from platforms.threads import post_threads, resolve_user_id  # noqa: E402
from platforms.dailymotion import post_dailymotion  # noqa: E402
from platforms.youtube import post_youtube  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY_IST = datetime.datetime.now(
    datetime.timezone(datetime.timedelta(hours=5, minutes=30))
).strftime("%Y-%m-%d")


def load_config(slug):
    path = os.path.join(ROOT, "accounts", slug, "config.yaml")
    with open(path) as f:
        return yaml.safe_load(f)


def build_caption(cfg, item):
    footer = cfg.get("caption_footer", "")
    tags = cfg.get("hashtags", "")
    return f"{item['hook']}\n{footer}\n{tags}"


def env_get(prefix, name):
    return os.environ.get(f"{prefix}_{name}")


def check_caption_limits(caption, hook):
    problems = []
    if len(caption) > 500:
        problems.append(f"caption {len(caption)} chars > Threads 500-char limit")
    if len(hook) > 100:
        problems.append(f"hook {len(hook)} chars > YouTube 100-char title limit")
    return problems


def run_platforms(cfg, item, converted, video_url, dry_run):
    """Post to each enabled platform. Returns {platform: result dict}."""
    prefix = cfg["env_prefix"]
    caption = build_caption(cfg, item)
    hook = item["hook"]
    results = {}
    enabled = cfg.get("platforms", {})

    # --- Meta: Facebook Page + Instagram Reel ---
    if enabled.get("meta"):
        page_id = env_get(prefix, "META_PAGE_ID")
        token = env_get(prefix, "META_PAGE_TOKEN")
        if not page_id or not token:
            results["meta"] = {"status": "skipped",
                               "reason": "not configured (missing AWC_META_PAGE_ID / AWC_META_PAGE_TOKEN)"}
        elif dry_run:
            results["meta"] = {"status": "dry-run",
                               "detail": f"POST /{page_id}/videos + IG resumable upload "
                                         f"(caption {len(caption)} chars)"}
        else:
            try:
                urls = post_meta(converted, caption, {
                    "PAGE_ID": page_id,
                    "PAGE_TOKEN": token,
                    "IG_USER_ID": env_get(prefix, "META_IG_USER_ID"),
                })
                results["meta"] = {"status": "ok", "urls": urls}
            except Exception as e:  # noqa: BLE001 - isolate platform failures
                results["meta"] = {"status": "failed", "reason": str(e)}
    else:
        results["meta"] = {"status": "skipped", "reason": "disabled in config"}

    # --- Threads ---
    if enabled.get("threads"):
        token = env_get(prefix, "THREADS_TOKEN")
        if not token:
            results["threads"] = {"status": "skipped",
                                  "reason": "not configured (missing AWC_THREADS_TOKEN)"}
        elif not video_url:
            results["threads"] = {"status": "skipped",
                                  "reason": "no public video URL configured"}
        elif dry_run:
            results["threads"] = {"status": "dry-run",
                                  "detail": f"POST /me/threads media_type=VIDEO "
                                            f"video_url={video_url}"}
        else:
            try:
                user_id = env_get(prefix, "THREADS_USER_ID")
                if not user_id:
                    user_id, _ = resolve_user_id(token)
                url = post_threads(video_url, caption, user_id, token)
                results["threads"] = {"status": "ok", "urls": {"threads": url}}
            except Exception as e:  # noqa: BLE001
                results["threads"] = {"status": "failed", "reason": str(e)}
    else:
        results["threads"] = {"status": "skipped", "reason": "disabled in config"}

    # --- Dailymotion ---
    if enabled.get("dailymotion"):
        cid = env_get(prefix, "DM_CLIENT_ID")
        csec = env_get(prefix, "DM_CLIENT_SECRET")
        rtok = env_get(prefix, "DM_REFRESH_TOKEN")
        atok = env_get(prefix, "DM_ACCESS_TOKEN")
        if not (cid and csec and (rtok or atok)):
            results["dailymotion"] = {"status": "skipped",
                                      "reason": "not configured (missing DM_CLIENT_ID / "
                                                "DM_CLIENT_SECRET / DM_REFRESH_TOKEN)"}
        elif dry_run:
            results["dailymotion"] = {"status": "dry-run",
                                      "detail": "POST /v2/files/upload_sessions, upload file, "
                                                f"POST /v2/profiles/<id>/videos "
                                                f"(category={cfg.get('dailymotion_category')})"}
        else:
            try:
                url = post_dailymotion(
                    converted, hook, caption,
                    [t.lstrip("#") for t in cfg.get("hashtags", "").split()],
                    cfg.get("dailymotion_category", "funny"),
                    cid, csec, rtok, atok,
                )
                results["dailymotion"] = {"status": "ok",
                                          "urls": {"dailymotion": url}}
            except Exception as e:  # noqa: BLE001
                results["dailymotion"] = {"status": "failed", "reason": str(e)}
    else:
        results["dailymotion"] = {"status": "skipped", "reason": "disabled in config"}

    # --- YouTube ---
    if enabled.get("youtube"):
        cid = env_get(prefix, "YT_CLIENT_ID")
        csec = env_get(prefix, "YT_CLIENT_SECRET")
        rtok = env_get(prefix, "YT_REFRESH_TOKEN")
        if not (cid and csec and rtok):
            results["youtube"] = {"status": "skipped",
                                  "reason": "not configured (missing YT_CLIENT_ID / "
                                            "YT_CLIENT_SECRET / YT_REFRESH_TOKEN)"}
        elif dry_run:
            results["youtube"] = {"status": "dry-run",
                                  "detail": "POST /upload/youtube/v3/videos "
                                            "uploadType=resumable (snippet,status)"}
        else:
            try:
                video_id, privacy = post_youtube(
                    converted, hook, caption,
                    [t.lstrip("#") for t in cfg.get("hashtags", "").split()],
                    str(cfg.get("youtube_category_id", "24")),
                    cid, csec, rtok,
                )
                note = ""
                if privacy != "public":
                    note = (" (UPLOADED AS PRIVATE — the Google Cloud project is "
                            "not YouTube-verified yet; see docs/SETUP.md)")
                results["youtube"] = {"status": "ok",
                                      "urls": {"youtube": f"https://www.youtube.com/shorts/{video_id}"},
                                      "detail": f"privacy={privacy}{note}"}
            except Exception as e:  # noqa: BLE001
                results["youtube"] = {"status": "failed", "reason": str(e)}
    else:
        results["youtube"] = {"status": "skipped", "reason": "disabled in config"}

    return results


def record_last_run(acct_dir, payload):
    """Write the run record the status site reads (live runs only)."""
    path = os.path.join(acct_dir, "last_run.json")
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")


def print_results(item, results):
    """Print the per-platform outcome to stdout (dry run and live)."""
    print(f"\n## Results \u2014 item #{item['id']} ({item.get('title', '')})")
    for platform, r in results.items():
        line = f"- {platform}: {r['status']}"
        if r.get("reason"):
            line += f" \u2014 {r['reason']}"
        if r.get("detail"):
            line += f" \u2014 {r['detail']}"
        if r.get("urls"):
            for k, v in r["urls"].items():
                line += f"\n    {k}: {v}"
        print(line)


def append_step_summary(item, results):
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    lines = [f"### Clip #{item['id']} — {item.get('title', '')}", ""]
    for platform, r in results.items():
        icon = {"ok": "✅", "failed": "❌", "skipped": "⏭️",
                "dry-run": "🔍"}.get(r["status"], "•")
        lines.append(f"- {icon} **{platform}**: {r['status']}"
                     + (f" — {r.get('reason', '')}" if r.get("reason") else "")
                     + (f" — {r.get('detail', '')}" if r.get("detail") else ""))
        for k, v in (r.get("urls") or {}).items():
            lines.append(f"  - {k}: {v}")
    with open(summary_path, "a") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True, help="account slug in accounts/")
    ap.add_argument("--dry-run", action="store_true",
                    help="convert + validate everything, post nothing")
    ap.add_argument("--item", default=None,
                    help="post a specific queue item id instead of the next pending one")
    args = ap.parse_args()

    acct_dir = os.path.join(ROOT, "accounts", args.account)
    cfg = load_config(args.account)
    queue_path = os.path.join(ROOT, cfg["queue_file"])
    queue = load_queue(queue_path)
    last_base = {
        "account": args.account,
        "run_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "run_date_ist": TODAY_IST,
    }

    if args.item is not None:
        item = find_item(queue, args.item)
        if item is None:
            print(f"FATAL: no queue item #{args.item}")
            return 1
        if item.get("status") != "pending":
            print(f"REFUSED: item #{args.item} is '{item.get('status')}' — "
                  f"never re-post a clip that already went live.")
            return 1
    else:
        item = next_pending(queue)
        if item is None:
            print("QUEUE EMPTY — nothing pending, nothing posted.")
            if not args.dry_run:
                record_last_run(acct_dir, {**last_base, "status": "empty",
                                           "results": {}})
            return 0

    print(f"Item #{item['id']}: {item.get('title', '')} "
          f"(source: {item.get('source')})")
    caption = build_caption(cfg, item)
    problems = check_caption_limits(caption, item["hook"])
    if problems:
        print("FATAL caption problems: " + "; ".join(problems))
        return 1

    src = os.path.join(ROOT, cfg["video_dir"], item["source"])
    if not os.path.exists(src):
        print(f"SKIPPED: video file missing: {src}\n"
              f"Nothing posted. Upload the videos to the repo first "
              f"(see docs/SETUP.md).")
        if not args.dry_run:
            record_last_run(acct_dir, {**last_base, "status": "skipped",
                                       "item_id": item["id"],
                                       "item_title": item.get("title", ""),
                                       "reason": "video file missing",
                                       "results": {}})
        return 0
    src_info = probe(src)
    print(f"Source: {src_info['width']}x{src_info['height']}, "
          f"{src_info['duration']:.1f}s, audio={src_info['has_audio']}")

    workdir = os.path.join(ROOT, "work", args.account)
    os.makedirs(workdir, exist_ok=True)
    converted = os.path.join(workdir, f"{item['id']:02d}-9x16.mp4")
    print("Converting to 1080x1920 ...")
    try:
        out_info = convert_to_9x16(src, converted)
    except Exception as e:  # noqa: BLE001 - record the failure, then exit 1
        print(f"FATAL: conversion failed: {e}")
        if not args.dry_run:
            record_last_run(acct_dir, {**last_base, "status": "error",
                                       "item_id": item["id"],
                                       "item_title": item.get("title", ""),
                                       "error": str(e), "results": {}})
        return 1
    print(f"Converted: {out_info['width']}x{out_info['height']}, "
          f"{out_info['duration']:.1f}s")

    video_url = None
    base = cfg.get("video_public_base", "").rstrip("/")
    if base:
        video_url = f"{base}/{item['source']}"

    if args.dry_run:
        print("DRY RUN — no network calls, nothing posted.")
        print(f"Caption ({len(caption)} chars):\n{caption}")
        print(f"Threads video_url: {video_url}")
        results = run_platforms(cfg, item, converted, video_url, dry_run=True)
        print_results(item, results)
        print("\nDry run OK — conversion verified, request shapes validated.")
        return 0

    results = run_platforms(cfg, item, converted, video_url, dry_run=False)
    print_results(item, results)
    append_step_summary(item, results)
    record_last_run(acct_dir, {**last_base,
                               "item_id": item["id"],
                               "item_title": item.get("title", ""),
                               "results": results,
                               "status": "posted" if any(
                                   r.get("urls") for r in results.values())
                               else "failed"})

    urls = {}
    for r in results.values():
        urls.update(r.get("urls") or {})
    if not urls:
        print("\nALL PLATFORMS FAILED OR SKIPPED — item stays pending for the "
              "next run. No queue change made.")
        return 0

    item["status"] = "done"
    item["posted_date"] = TODAY_IST
    item["urls"] = urls
    save_queue(queue_path, queue)
    print(f"\nQueue updated: item #{item['id']} marked done ({TODAY_IST}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
