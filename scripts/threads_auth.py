#!/usr/bin/env python3
"""Mint a Threads long-lived token (one-time setup, run on your own machine).

Prerequisites (docs/SETUP.md): add the Threads use case to the Meta app,
note the THREADS app ID + app secret (a Threads app has its own ID/secret,
different from the Facebook app's), register the redirect URI in the app
dashboard, and add the @aiwo.rldclips Threads profile as a Threads Tester
(App Dashboard -> App roles -> Roles -> Add People -> Threads Tester).

1. Run:  THREADS_APP_ID=... THREADS_APP_SECRET=... python3 scripts/threads_auth.py
   It prints an authorise URL. Open it, sign in as @aiwo.rldclips, grant
   threads_basic + threads_content_publish.
2. Threads redirects to your redirect URI with ?code=... — copy the full URL
   and paste it back here.
3. The script exchanges the code for a short-lived token, then for a
   long-lived token (60 days), and prints it plus your Threads user id.
   Save them as repo secrets (AWC_THREADS_TOKEN, AWC_THREADS_USER_ID).

Long-lived tokens can be refreshed before they expire; the runner reports a
clear error when the token is dead, and you re-run this script.
"""
import os
import sys
import urllib.parse

import requests

APP_ID = os.environ.get("THREADS_APP_ID")
APP_SECRET = os.environ.get("THREADS_APP_SECRET")
REDIRECT_URI = os.environ.get("THREADS_REDIRECT_URI", "http://127.0.0.1:8080/")
BASE = "https://graph.threads.net"

if not APP_ID or not APP_SECRET:
    print("Set THREADS_APP_ID and THREADS_APP_SECRET first.")
    sys.exit(1)

params = {
    "client_id": APP_ID,
    "redirect_uri": REDIRECT_URI,
    "scope": "threads_basic,threads_content_publish",
    "response_type": "code",
}
print("Open this URL in your browser:\n")
print("https://threads.com/oauth/authorize?" + urllib.parse.urlencode(params))
print("\nAfter granting, paste the full redirect URL (or just the code):")
pasted = input("> ").strip()
code = urllib.parse.parse_qs(urllib.parse.urlparse(pasted).query).get("code", [pasted])[0]

r = requests.post(
    f"{BASE}/oauth/access_token",
    data={
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    },
    timeout=60,
)
r.raise_for_status()
short = r.json()["access_token"]

r = requests.get(
    f"{BASE}/oauth/access_token",
    params={
        "grant_type": "th_exchange_token",
        "client_secret": APP_SECRET,
        "access_token": short,
    },
    timeout=60,
)
r.raise_for_status()
long_token = r.json()["access_token"]

me = requests.get(
    f"{BASE}/v1.0/me",
    params={"fields": "id,username", "access_token": long_token},
    timeout=30,
)
me.raise_for_status()
print("\nSave these as GitHub repo secrets:")
print(f"  AWC_THREADS_TOKEN={long_token}")
print(f"  AWC_THREADS_USER_ID={me.json()['id']}")
print(f"  (Threads user: @{me.json().get('username')})")
print("\nLong-lived token: valid 60 days from now.")
