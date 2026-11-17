"""YouTube Shorts upload via the YouTube Data API v3 (videos.insert).

Resumable upload protocol, plain requests (no google client library needed):
refresh the OAuth token -> create a resumable session
(POST /upload/youtube/v3/videos?uploadType=resumable&part=snippet,status)
-> PUT the file in 8MB chunks (server answers 308 Resume Incomplete until
the final chunk returns 200 with the video id).

Scope: https://www.googleapis.com/auth/youtube.upload
Quota: videos.insert costs 1,600 units of the default 10,000/day project
quota (about 6 uploads/day). 1 video/day is far inside it.

Two Google-side gotchas (see docs/SETUP.md for the fixes):
- A refresh token from an OAuth app in Testing mode expires after 7 days.
  Publish the consent screen to Production and re-authorise once.
- Videos uploaded by an UNVERIFIED API project are forced PRIVATE.
  Full YouTube API verification (audit) lifts that. Until it is done, uploads
  land private — the runner reports the privacy status it set and the video
  id either way; it never silently claims a public Short.
"""
import json
import os

import requests

TOKEN_URL = "https://oauth2.googleapis.com/token"
UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
CHUNK = 8 * 1024 * 1024


class YouTubeError(RuntimeError):
    pass


def _raise(resp, what):
    try:
        detail = resp.json()
    except Exception:
        detail = resp.text[:500]
    raise YouTubeError(f"{what} failed ({resp.status_code}): {detail}")


def refresh_access_token(client_id, client_secret, refresh_token):
    r = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        },
        timeout=60,
    )
    if not r.ok:
        _raise(r, "YouTube token refresh (invalid_grant usually means the "
                  "refresh token expired — re-authorise, see docs/SETUP.md)")
    return r.json()["access_token"]


def post_youtube(video_path, title, description, tags, category_id,
                 client_id, client_secret, refresh_token,
                 privacy_status="public"):
    """Upload a Short. Returns (video_id, privacy_status)."""
    token = refresh_access_token(client_id, client_secret, refresh_token)
    size = os.path.getsize(video_path)
    metadata = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }
    sess = requests.post(
        f"{UPLOAD_URL}?uploadType=resumable&part=snippet,status",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(size),
        },
        data=json.dumps(metadata),
        timeout=60,
    )
    if not sess.ok:
        _raise(sess, "YouTube resumable session")
    session_uri = sess.headers.get("Location")
    if not session_uri:
        raise YouTubeError("YouTube did not return a resumable session URL")

    uploaded = 0
    video_id = None
    with open(video_path, "rb") as f:
        while uploaded < size:
            chunk = f.read(CHUNK)
            end = uploaded + len(chunk) - 1
            put = requests.put(
                session_uri,
                headers={
                    "Content-Type": "video/mp4",
                    "Content-Length": str(len(chunk)),
                    "Content-Range": f"bytes {uploaded}-{end}/{size}",
                },
                data=chunk,
                timeout=600,
            )
            if put.status_code in (200, 201):
                video_id = put.json()["id"]
                uploaded = size
            elif put.status_code == 308:
                # Resume Incomplete — server tells us what it has.
                rng = put.headers.get("Range", "")
                uploaded = int(rng.split("-")[1]) + 1 if "-" in rng else uploaded + len(chunk)
                f.seek(uploaded)
            else:
                _raise(put, "YouTube chunk upload")
    if not video_id:
        raise YouTubeError("YouTube upload finished without a video id")
    return video_id, privacy_status
