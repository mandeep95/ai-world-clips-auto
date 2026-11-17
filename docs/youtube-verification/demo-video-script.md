# YouTube API verification — demo video script

Google asks for a short screen recording that proves what the app does with
the `youtube.upload` scope. Record it on your own machine (phone camera
pointed at the screen is fine, but a screen recorder is cleaner). Keep it
under ~3 minutes. Narrate in plain English or Hindi — either is fine.

## Shots (in order)

1. **(0:00–0:20) The app.** Show the repo README on screen
   (`github.com/mandeep95/ai-world-clips-auto`). Say: "This is my automation
   for my own channel AI World Clips. Once a day it uploads one short video
   I made to my own YouTube channel."
2. **(0:20–0:50) The OAuth consent screen.** Open the authorise URL the
   `scripts/yt_auth.py` helper prints. Show the Google sign-in and the
   consent screen with the `youtube.upload` permission. Say: "I sign in with
   my own Google account and grant upload access to my own channel. The app
   never sees my password and never touches anyone else's channel."
3. **(0:50–1:20) The token.** Run the helper, paste the redirect URL, show
   it printing the refresh token (blur the token itself on screen). Say:
   "The refresh token is stored as a secret in the repo. It is only used to
   upload to this one channel."
4. **(1:20–2:10) The upload.** Run a manual workflow dispatch (or the local
   dry-run, then a live run) and show the Actions log line
   `youtube: ok` with the Shorts URL. Say: "One video a day, title and
   description from the queue file, uploaded as a Short."
5. **(2:10–2:40) The result.** Open the Short on youtube.com/shorts/…
   in the browser, play a few seconds. Say: "The video is live on my
   channel AI World Clips, public, and it is my own content."
6. **(2:40–3:00) Privacy.** Show the privacy policy page
   (`docs/youtube-verification/privacy-policy.html`, hosted publicly). Say:
   "The privacy policy is at this URL. The app stores only my own channel's
   upload token; it collects no data about anyone else."

## Upload the demo video

Upload it to YouTube as **Unlisted** and paste the link in the verification
form where Google asks for the demo video. (Unlisted is fine — Google only
needs the link.)
