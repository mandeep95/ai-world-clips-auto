"""Facebook Page + Instagram Reel posting via Meta's official Graph API.

Adapted from the proven post_reel.py (tested 2026-11-17: Facebook
unpublished upload OK, Instagram resumable container reached FINISHED).
Same endpoints, same flow — only the credential source changed: environment
variables instead of a .env file.

Graph API v21.0. Page token is a long-lived Page access token.
"""
import os
import time

import requests

GRAPH = "https://graph.facebook.com/v21.0"


class MetaError(RuntimeError):
    pass


def _raise(resp, what):
    try:
        detail = resp.json()
    except Exception:
        detail = resp.text[:500]
    raise MetaError(f"{what} failed ({resp.status_code}): {detail}")


def resolve_ig_user_id(page_id, token):
    r = requests.get(
        f"{GRAPH}/{page_id}",
        params={"fields": "instagram_business_account", "access_token": token},
        timeout=30,
    )
    if not r.ok:
        _raise(r, "Resolve Instagram account")
    ig = r.json().get("instagram_business_account", {})
    if not ig.get("id"):
        raise MetaError(f"No Instagram account linked to Page {page_id}: {r.json()}")
    return ig["id"]


def fb_post_video(page_id, token, video_path, title, description):
    """Upload a video to the Facebook Page. Returns the video id."""
    with open(video_path, "rb") as f:
        r = requests.post(
            f"{GRAPH}/{page_id}/videos",
            params={"access_token": token},
            data={"title": title, "description": description},
            files={"source": (os.path.basename(video_path), f, "video/mp4")},
            timeout=600,
        )
    if not r.ok:
        _raise(r, "Facebook video upload")
    return r.json()["id"]


def ig_post_reel(ig_user_id, token, video_path, caption):
    """Publish a Reel via the Instagram Graph API (resumable upload).

    Flow: create upload session -> upload bytes -> wait for FINISHED -> publish.
    Returns the published media id.
    """
    size = os.path.getsize(video_path)
    r = requests.post(
        f"{GRAPH}/{ig_user_id}/media",
        params={
            "upload_type": "resumable",
            "media_type": "REELS",
            "access_token": token,
        },
        timeout=60,
    )
    if not r.ok:
        _raise(r, "Instagram upload session")
    session = r.json()
    upload_uri = session["uri"]
    creation_id = session["id"]

    with open(video_path, "rb") as f:
        up = requests.post(
            upload_uri,
            headers={
                "Authorization": f"OAuth {token}",
                "Content-Type": "application/octet-stream",
                "Offset": "0",
                "file_size": str(size),
            },
            data=f,
            timeout=600,
        )
    if not up.ok:
        _raise(up, "Instagram byte upload")

    for _ in range(30):
        st = requests.get(
            f"{GRAPH}/{creation_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=30,
        )
        if not st.ok:
            _raise(st, "Instagram container status")
        if st.json().get("status_code") == "FINISHED":
            break
        time.sleep(10)
    else:
        raise MetaError(f"Instagram container {creation_id} never finished processing")

    pub = requests.post(
        f"{GRAPH}/{ig_user_id}/media_publish",
        params={"creation_id": creation_id, "caption": caption, "access_token": token},
        timeout=60,
    )
    if not pub.ok:
        _raise(pub, "Instagram media_publish")
    return pub.json()["id"]


def ig_permalink(media_id, token):
    r = requests.get(
        f"{GRAPH}/{media_id}",
        params={"fields": "permalink", "access_token": token},
        timeout=30,
    )
    if not r.ok:
        return None
    return r.json().get("permalink")


def post_meta(video_path, caption, env):
    """Post to Facebook Page AND Instagram. Returns {facebook, instagram} URLs.

    env: dict with PAGE_ID, PAGE_TOKEN, IG_USER_ID (IG id optional — resolved
    from the Page when missing).
    """
    page_id = env["PAGE_ID"]
    token = env["PAGE_TOKEN"]
    ig_user_id = env.get("IG_USER_ID") or resolve_ig_user_id(page_id, token)
    title = caption.split("\n")[0][:100]

    fb_id = fb_post_video(page_id, token, video_path, title, caption)
    fb_url = f"https://www.facebook.com/reel/{fb_id}/"

    ig_id = ig_post_reel(ig_user_id, token, video_path, caption)
    ig_url = ig_permalink(ig_id, token) or f"https://www.instagram.com/reel/{ig_id}/"
    return {"facebook": fb_url, "instagram": ig_url}
