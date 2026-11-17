#!/usr/bin/env python3
"""Mint a Dailymotion refresh token (one-time setup, run on your own machine).

Prerequisites (docs/SETUP.md): create an API key at Dailymotion Settings ->
API Keys (free). Note the API key (= client ID) + API secret. The callback
URL you entered there must match the redirect URI below.

1. Run:  DM_CLIENT_ID=... DM_CLIENT_SECRET=... python3 scripts/dm_auth.py
   It prints an authorise URL. Open it, sign in to the AI World Clips
   Dailymotion account, grant the video.manage scope.
2. Dailymotion redirects to your callback URL with ?code=... — copy the full
   URL and paste it back here.
3. The script prints the REFRESH TOKEN. Save it as a repo secret
   (AWC_DM_REFRESH_TOKEN) along with the client ID/secret. The runner mints
   a fresh access token from it on every run, so the refresh token is the
   only Dailymotion secret the repo needs.
"""
import os
import sys
import urllib.parse

import requests

CLIENT_ID = os.environ.get("DM_CLIENT_ID")
CLIENT_SECRET = os.environ.get("DM_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("DM_REDIRECT_URI", "http://127.0.0.1:8080/")
SCOPE = "video.manage"

if not CLIENT_ID or not CLIENT_SECRET:
    print("Set DM_CLIENT_ID and DM_CLIENT_SECRET first.")
    sys.exit(1)

params = {
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
}
print("Open this URL in your browser:\n")
print("https://www.dailymotion.com/oauth/authorize?" + urllib.parse.urlencode(params))
print("\nAfter granting, paste the full redirect URL (or just the code):")
pasted = input("> ").strip()
code = urllib.parse.parse_qs(urllib.parse.urlparse(pasted).query).get("code", [pasted])[0]

r = requests.post(
    "https://api.dailymotion.com/oauth/token",
    data={
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    },
    timeout=60,
)
r.raise_for_status()
tok = r.json()
print("\nSave these as GitHub repo secrets:")
print(f"  AWC_DM_CLIENT_ID={CLIENT_ID}")
print(f"  AWC_DM_CLIENT_SECRET={CLIENT_SECRET}")
print(f"  AWC_DM_REFRESH_TOKEN={tok['refresh_token']}")
print("\nScope granted:", tok.get("scope"))
