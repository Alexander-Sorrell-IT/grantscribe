#!/usr/bin/env bash
# Lay your recorded voiceover over the demo video.
# Usage:  bash demo/compose_voiceover.sh path/to/your_voice.(wav|mp3|m4a)
set -euo pipefail
VID="demo/out/GrantScribe_trailer_REAL_silent.mp4"
AUD="${1:?Usage: compose_voiceover.sh <audio file>}"
OUT="demo/out/GrantScribe_trailer.mp4"

# Keep video length; pad audio with silence if it's shorter, trim if longer.
ffmpeg -y -i "$VID" -i "$AUD" \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k \
  -af apad -shortest -movflags +faststart "$OUT"

echo "✅ wrote $OUT  ($(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s)"
