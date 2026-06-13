#!/usr/bin/env bash
# Run once /tmp/gs_clone/vo_cloned.wav exists: master it, score it vs the user's
# real Monticello data points, and produce the deliverable mp3/wav.
set -uo pipefail
cd "$(dirname "$0")/.."
RAW=/tmp/gs_clone/vo_cloned.wav
[ -s "$RAW" ] || { echo "no cloned wav yet at $RAW"; exit 1; }

echo "=== master (same clean chain: highpass + denoise + loudnorm + true-peak) ==="
ffmpeg -y -i "$RAW" -af "highpass=f=70,afftdn=nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11" -ar 44100 \
  demo/out/voiceover_cloned.wav 2>/dev/null
ffmpeg -y -i demo/out/voiceover_cloned.wav -codec:a libmp3lame -q:a 2 demo/out/voiceover_cloned.mp3 2>/dev/null
echo "  -> demo/out/voiceover_cloned.mp3  ($(ffprobe -v error -show_entries format=duration -of csv=p=0 demo/out/voiceover_cloned.wav 2>/dev/null)s)"

echo "=== scorecard: your CLONED voice vs your REAL Monticello voice ==="
echo "  [your real voice: F0 136Hz, F0var 3.44st, jitter 2.89%, shimmer 10.5%, HNR 14.1]"
timeout 200 uv run --with praat-parselmouth --with numpy python demo/voice_scorecard.py demo/out/voiceover_cloned.wav /tmp/gs_clone/vo_text.txt 2>&1 \
  | grep -E 'speaking rate|F0 mean|F0 variation|jitter|shimmer|HNR|intensity' | tail -7
