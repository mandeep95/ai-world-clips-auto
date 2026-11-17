#!/usr/bin/env python3
"""Mint a YouTube refresh token (one-time setup, run on your own machine).

1. In Google Cloud Console, enable the YouTube Data API v3 and create an
   OAuth client ID (Desktop app). Note the client ID + secret.
2. Run:  YT_CLIENT_ID=... YT_CLIENT_SECRET=... python3 scripts/yt_auth.py
   It prints an authorise URL. Open it, sign in as the channel owner
   (Devdeeep2000@gmail.com for AI World Clips), grant access.
   Google redirects to http://127.0.0.1:8080/?code=... — the browser will show
   "can't reach this site". That is expected: copy the full address-bar URL
   and paste it back here.
3. The script prints the REFRESH TOKEN. Save it as a repo secret
   (AWC_YT_REFRESH_TOKEN) along with the client ID/secret. Never commit it.

IMPORTANT: do this AFTER setting the OAuth consent screen to Production
(docs/SETUP.md) — a refresh token minted while the app is in Testing mode
expires after 7 days.
"""
import os
import sys
import urllib.parse

import requests

CLIENT_ID = os.environ.get("YT_CLIENT_ID")
CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8080/"
SCOPE = "https://www.googleapis.com/auth/youtube.upload"

if not CLIENT_ID or not CLIENT_SECRET:
    print("Set YT_CLIENT_ID and YT_CLIENT_SECRET first.")
    sys.exit(1)

params = {
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "response_type": "code",
    "scope": SCOPE,
    "access_type": "offline",
    "prompt": "consent",
}
print("Open this URL in your browser:\n")
print("https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params))
print("\nAfter granting, paste the full redirect URL (or just the code):")
pasted = input("> ").strip()
code = urllib.parse.parse_qs(urllib.parse.urlparse(pasted).query).get("code", [pasted])[0]

r = requests.post(
    "https://oauth2.googleapis.com/token",
    data={
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    },
    timeout=60,
)
r.raise_for_status()
tok = r.json()
print("\nSave these as GitHub repo secrets:")
print(f"  AWC_YT_CLIENT_ID={CLIENT_ID}")
print(f"  AWC_YT_CLIENT_SECRET={CLIENT_SECRET}")
print(f"  AWC_YT_REFRESH_TOKEN={tok['refresh_token']}")
print("\nScope granted:", tok.get("scope"))
