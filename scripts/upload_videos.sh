#!/bin/bash
# Upload the AI World Clips videos into a local clone of this repo, then push.
# The automation repo was created without the videos (the connector that
# built it cannot push binary files), so this is the one manual step.
#
# Usage (on your Mac, where you are signed in to GitHub):
#   git clone https://github.com/mandeep95/ai-world-clips-auto.git
#   cd ai-world-clips-auto
#   bash scripts/upload_videos.sh /path/to/videos-folder
#
# The videos folder is the one handed over with this repo
# (10 .mp4 files, ~196 MB). The script copies them to
# accounts/ai-world-clips/videos/, verifies sizes + SHA-256 against
# MANIFEST.md, commits and pushes.
set -euo pipefail

VIDEOS_DIR="${1:-}"
if [ -z "$VIDEOS_DIR" ] || [ ! -d "$VIDEOS_DIR" ]; then
  echo "Usage: bash scripts/upload_videos.sh /path/to/videos-folder"
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="$REPO_ROOT/accounts/ai-world-clips/videos"
mkdir -p "$TARGET"

echo "Copying videos..."
cp "$VIDEOS_DIR"/*.mp4 "$TARGET"/

if [ -f "$VIDEOS_DIR/poster-latest.jpg" ]; then
  echo "Copying the status-site poster frame..."
  mkdir -p "$REPO_ROOT/assets"
  cp "$VIDEOS_DIR/poster-latest.jpg" "$REPO_ROOT/assets/"
else
  echo "NOTE: poster-latest.jpg not in the videos folder — the status site"
  echo "will show no poster image until the daily workflow regenerates it."
fi

echo "Verifying against MANIFEST.md..."
cd "$TARGET"
MISSING=0
for f in *.mp4; do
  [ "$f" = "*.mp4" ] && continue
  SIZE=$(stat -f%z "$f" 2>/dev/null || stat -c%s "$f")
  if [ "$SIZE" -ge 104857600 ]; then
    echo "FAIL: $f is $SIZE bytes (>= 100 MB GitHub limit)"
    MISSING=1
  fi
  if ! grep -q "  $f " MANIFEST.md && ! grep -q "| $f |" MANIFEST.md; then
    echo "WARN: $f is not listed in MANIFEST.md"
  fi
done
echo "Files in $TARGET:"
ls -la *.mp4

if ! command -v sha256sum >/dev/null 2>&1; then
  echo "NOTE: sha256sum not found — verify hashes manually with: shasum -a 256 *.mp4"
else
  echo "Checking SHA-256 hashes..."
  FAIL=0
  while read -r hash file; do
    [ -z "$hash" ] && continue
    ACTUAL=$(sha256sum "$file" | awk '{print $1}')
    if [ "$ACTUAL" != "$hash" ]; then
      echo "FAIL: $file hash mismatch"
      FAIL=1
    fi
  done < <(cd "$VIDEOS_DIR" && sha256sum *.mp4)
  [ "$FAIL" = "1" ] && exit 1
  echo "All hashes match."
fi

[ "$MISSING" = "1" ] && exit 1

echo "Committing and pushing..."
cd "$REPO_ROOT"
git add accounts/ai-world-clips/videos/ assets/poster-latest.jpg
git commit -m "Add AI World Clips videos (#8-#15 + 2 held)" || echo "(nothing new to commit)"
git push
echo "Done — videos are in the repo."
