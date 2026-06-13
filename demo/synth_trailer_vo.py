"""Synthesize the trailer voiceover per block (cloned voice, XTTS-v2) and assemble it
so each block lands exactly on its video slot in GrantScribe_trailer_REAL_silent.mp4.

Blocks are parsed from demo/VOICEOVER_TRAILER.md. A block shorter than its slot is
padded with silence; one that overruns is sped up (atempo-style resample via numpy is
avoided — we just warn and let the caller trim the text, except small overruns ≤8%
which are absorbed by trimming the inter-sentence gaps).

Output: demo/out/vo_trailer_raw.wav (24 kHz mono) — master it with the usual
highpass+denoise+loudnorm chain before compose_voiceover.sh.
"""
from __future__ import annotations
import os
import re
import sys

import numpy as np
import soundfile as sf
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

MODEL_DIR = "/tmp/gs_clone/xtts_model"
SPEAKER = "/tmp/gs_clone/user_voice.wav"
MD = os.path.join(os.path.dirname(__file__), "VOICEOVER_TRAILER.md")
OUT = os.path.join(os.path.dirname(__file__), "out", "vo_trailer_raw.wav")
SR = 24000
GAP = 0.40  # s of silence between sentences

# slot boundaries in the silent video (s): intro/slack/verify_loi/verify_pathway/close
SLOTS = [(0.0, 14.0), (14.0, 83.8), (83.8, 115.0), (115.0, 137.8), (137.8, 149.8)]


def blocks_from_md(path: str) -> list[str]:
    blocks: list[list[str]] = []
    for line in open(path).read().splitlines():
        if line.startswith("## Block"):
            blocks.append([])
        elif blocks and line.strip() and not line.startswith("#"):
            blocks[-1].append(line.strip())
    return [" ".join(b) for b in blocks]


def sentences(text: str) -> list[str]:
    out = []
    for sent in re.split(r"(?<=[.!?]) +", text):
        sent = sent.strip()
        while len(sent) > 230:
            cut = sent.rfind(",", 80, 230)
            cut = cut if cut > 80 else 230
            out.append(sent[:cut].strip())
            sent = sent[cut:].strip()
        if sent:
            out.append(sent)
    return out


def main() -> None:
    texts = blocks_from_md(MD)
    assert len(texts) == len(SLOTS), f"{len(texts)} blocks vs {len(SLOTS)} slots"

    print("loading XTTS-v2…", flush=True)
    config = XttsConfig()
    config.load_json(os.path.join(MODEL_DIR, "config.json"))
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir=MODEL_DIR, use_deepspeed=False)
    model.eval()
    gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=[SPEAKER])

    track: list[np.ndarray] = []
    cursor = 0.0
    ok = True
    for bi, (text, (start, end)) in enumerate(zip(texts, SLOTS), 1):
        if cursor < start:
            track.append(np.zeros(int(SR * (start - cursor)), dtype=np.float32))
            cursor = start
        sents = sentences(text)
        pieces: list[np.ndarray] = []
        for i, s in enumerate(sents):
            out = model.inference(s, "en", gpt_cond_latent, speaker_embedding, temperature=0.7)
            pieces.append(np.asarray(out["wav"], dtype=np.float32))
            print(f"  [b{bi} {i + 1}/{len(sents)}] {s[:60]}…", flush=True)
        speech = sum(len(p) for p in pieces) / SR
        slot = end - start
        gap = GAP
        if speech + GAP * (len(pieces) - 1) > slot:  # absorb small overruns in the gaps
            gap = max(0.10, (slot - speech) / max(1, len(pieces) - 1))
        block = np.concatenate(
            [x for p in pieces for x in (p, np.zeros(int(SR * gap), dtype=np.float32))][:-1]
        )
        dur = len(block) / SR
        status = "OK" if dur <= slot else "OVERRUN — trim this block's text"
        if dur > slot:
            ok = False
        print(f"block {bi}: speech {dur:5.1f}s / slot {slot:5.1f}s  {status}", flush=True)
        track.append(block)
        cursor += dur

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    sf.write(OUT, np.concatenate(track), SR)
    print(f"{'DONE' if ok else 'DONE WITH OVERRUNS'} -> {OUT} ({cursor:.1f}s)", flush=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
