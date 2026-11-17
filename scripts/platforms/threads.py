"""Threads video posting via the official Threads API.

Docs: https://developers.facebook.com/documentation/threads/posts
(verified 2026-11-17).

Flow: create a media container (media_type=VIDEO, video_url must be a PUBLIC
URL Meta can fetch) -> poll the container status until FINISHED -> publish.
Permissions: threads_basic + threads_content_publish. The app user posts on
their own account; no App Review is needed for the app's own admin/testers —
review is only needed to post for other users.

Limits: text max 500 chars; video MP4/MOV, H.264/HEVC, AAC <=128kbps,
23-60fps, max 1920px wide, 9:16 recommended, max 300s, max 1GB.
250 published posts per profile per 24h.
"""
import time

import requests

BASE = "https://graph.threads.net/v1.0"


class ThreadsError(RuntimeError):
    pass


def _raise(resp, what):
    try:
        detail = resp.json()
    except Exception:
        detail = resp.text[:500]
    raise ThreadsError(f"{what} failed ({resp.status_code}): {detail}")


def resolve_user_id(token):
    """Threads user id + username for the token owner."""
    r = requests.get(
        f"{BASE}/me", params={"fields": "id,username", "access_token": token},
        timeout=30,
    )
    if not r.ok:
        _raise(r, "Resolve Threads user")
    return r.json()["id"], r.json().get("username")


def post_threads(video_url, caption, user_id, token):
    """Publish a video post. Returns the post permalink."""
    if len(caption) > 500:
        raise ThreadsError(
            f"Caption is {len(caption)} chars, Threads limit is 500"
        )
    r = requests.post(
        f"{BASE}/{user_id}/threads",
        data={
            "media_type": "VIDEO",
            "video_url": video_url,
            "text": caption,
            "access_token": token,
        },
        timeout=60,
    )
    if not r.ok:
        _raise(r, "Threads container creation")
    container_id = r.json()["id"]

    # Video needs processing time; poll once a minute, max 5 minutes.
    for _ in range(5):
        st = requests.get(
            f"{BASE}/{container_id}",
            params={"fields": "status,error_message", "access_token": token},
            timeout=30,
        )
        if not st.ok:
            _raise(st, "Threads container status")
        data = st.json()
        status = data.get("status")
        if status == "FINISHED":
            break
        if status == "ERROR":
            raise ThreadsError(
                f"Threads container {container_id} errored: "
                f"{data.get('error_message')}"
            )
        time.sleep(60)
    else:
        raise ThreadsError(
            f"Threads container {container_id} not FINISHED after 5 minutes"
        )

    pub = requests.post(
        f"{BASE}/{user_id}/threads_publish",
        data={"creation_id": container_id, "access_token": token},
        timeout=60,
    )
    if not pub.ok:
        _raise(pub, "Threads publish")
    media_id = pub.json()["id"]

    link = requests.get(
        f"{BASE}/{media_id}",
        params={"fields": "permalink", "access_token": token},
        timeout=30,
    )
    if link.ok and link.json().get("permalink"):
        return link.json()["permalink"]
    return f"https://www.threads.com/t/{media_id}"
