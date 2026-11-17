"""Dailymotion video upload via the official Dailymotion API v2.

Docs: https://developers.dailymotion.com/docs/upload-videos (verified 2026-11-17).

Flow: refresh the OAuth token -> create an upload session
(POST /v2/files/upload_sessions) -> POST the file (multipart, field "file")
to the returned upload_url -> create the video
(POST /v2/profiles/{profile_id}/videos) with title, category, visibility,
is_for_kids and source.file_url. Scope needed: video.manage.

API key + secret come from Dailymotion Settings -> API Keys (free).
The access token is minted at runtime from the stored refresh token, so only
the refresh token (plus client id/secret) needs to be stored as a secret.
"""
import json
import urllib.parse

import requests

API = "https://api.dailymotion.com"


class DailymotionError(RuntimeError):
    pass


def _raise(resp, what):
    try:
        detail = resp.json()
    except Exception:
        detail = resp.text[:500]
    raise DailymotionError(f"{what} failed ({resp.status_code}): {detail}")


def refresh_access_token(client_id, client_secret, refresh_token):
    r = requests.post(
        f"{API}/oauth/token",
        data={
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        },
        timeout=60,
    )
    if not r.ok:
        _raise(r, "Dailymotion token refresh")
    return r.json()["access_token"]


def _profile_id(token, upload_url=None):
    r = requests.get(
        f"{API}/me", params={"fields": "id", "access_token": token}, timeout=30
    )
    if r.ok and r.json().get("id"):
        return r.json()["id"]
    # Fallback: the upload URL carries the profile id in its `extra` param.
    if upload_url:
        extra = urllib.parse.parse_qs(
            urllib.parse.urlparse(upload_url).query
        ).get("extra", [None])[0]
        if extra:
            return extra
    raise DailymotionError("Could not resolve Dailymotion profile id")


def post_dailymotion(video_path, title, description, tags, category,
                     client_id, client_secret, refresh_token,
                     access_token=None):
    """Upload + publish a video. Returns the video URL."""
    token = access_token
    if refresh_token:
        token = refresh_access_token(client_id, client_secret, refresh_token)
    if not token:
        raise DailymotionError("No Dailymotion access token (and no refresh token)")

    headers = {"Authorization": f"Bearer {token}"}

    sess = requests.post(
        f"{API}/v2/files/upload_sessions", headers=headers, timeout=60
    )
    if not sess.ok:
        _raise(sess, "Dailymotion upload session")
    upload_url = sess.json()["upload_url"]

    with open(video_path, "rb") as f:
        up = requests.post(
            upload_url,
            files={"file": (video_path.split("/")[-1], f, "video/mp4")},
            timeout=600,
        )
    if not up.ok:
        _raise(up, "Dailymotion file upload")
    file_url = up.json().get("url")
    if not file_url:
        raise DailymotionError(f"Dailymotion upload gave no file URL: {up.text[:300]}")

    profile_id = _profile_id(token, upload_url)
    create = requests.post(
        f"{API}/v2/profiles/{profile_id}/videos",
        headers={**headers, "Content-Type": "application/json"},
        data=json.dumps({
            "title": title[:255],
            "description": description,
            "tags": tags,
            "category": category,
            "visibility": "public",
            "is_for_kids": False,
            "source": {"file_url": file_url},
        }),
        timeout=60,
    )
    if not create.ok:
        _raise(create, "Dailymotion video creation")
    video_id = create.json().get("video_id") or create.json().get("id")
    return f"https://www.dailymotion.com/video/{video_id}"
