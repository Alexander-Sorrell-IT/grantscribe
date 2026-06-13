"""Clone the user's voice (Monticello recording) and narrate the GrantScribe script
with XTTS-v2 — loading the model DIRECTLY from local files (no manager / no TOS prompt
/ no re-download). Output: /tmp/vo_cloned.wav
"""
from __future__ import annotations
import os
import re

import numpy as np
import soundfile as sf
import torch
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

MODEL_DIR = "/tmp/gs_clone/xtts_model"          # isolated from the other agent's /tmp collisions
SPEAKER = "/tmp/gs_clone/user_voice.wav"
TEXT = "/tmp/gs_clone/vo_text.txt"
OUT = "/tmp/gs_clone/vo_cloned.wav"
SR = 24000

print("loading XTTS-v2 from local files…", flush=True)
config = XttsConfig()
config.load_json(os.path.join(MODEL_DIR, "config.json"))
model = Xtts.init_from_config(config)
model.load_checkpoint(config, checkpoint_dir=MODEL_DIR, use_deepspeed=False)
model.eval()  # CPU

print("extracting your voice fingerprint from the Monticello recording…", flush=True)
gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=[SPEAKER])

# chunk the script
chunks: list[str] = []
for para in open(TEXT).read().splitlines():
    para = para.strip()
    if not para:
        continue
    for sent in re.split(r"(?<=[.!?]) +", para):
        sent = sent.strip()
        while len(sent) > 230:
            cut = sent.rfind(",", 80, 230)
            cut = cut if cut > 80 else 230
            chunks.append(sent[:cut].strip())
            sent = sent[cut:].strip()
        if sent:
            chunks.append(sent)

print(f"{len(chunks)} chunks; synthesizing in your cloned voice…", flush=True)
audio: list[np.ndarray] = []
for i, c in enumerate(chunks):
    out = model.inference(c, "en", gpt_cond_latent, speaker_embedding, temperature=0.7)
    audio.append(np.asarray(out["wav"], dtype=np.float32))
    audio.append(np.zeros(int(SR * 0.45), dtype=np.float32))
    print(f"  [{i+1}/{len(chunks)}] {c[:48]}…", flush=True)

sf.write(OUT, np.concatenate(audio), SR)
print(f"DONE -> {OUT}", flush=True)
