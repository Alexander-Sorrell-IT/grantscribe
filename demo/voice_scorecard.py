"""Naturalness scorecard: measure a TTS wav against human-speech reference ranges."""
import sys
import numpy as np
import parselmouth
from parselmouth.praat import call

WAV = sys.argv[1] if len(sys.argv) > 1 else "/tmp/vo2_master.wav"
TXT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/vo_text.txt"

snd = parselmouth.Sound(WAV)
dur = snd.get_total_duration()
words = len(open(TXT).read().split())

# --- tempo ---
wpm = words / (dur / 60)

# --- pitch (F0) ---
pitch = snd.to_pitch(time_step=0.01, pitch_floor=75, pitch_ceiling=300)
f0 = pitch.selected_array["frequency"]
voiced = f0[f0 > 0]
f0_mean = float(np.mean(voiced))
f0_sd_hz = float(np.std(voiced))
st = 12 * np.log2(voiced / np.median(voiced))          # semitones rel. median
f0_sd_st = float(np.std(st))
voiced_frac = len(voiced) / len(f0)

# --- jitter / shimmer / HNR (voice-quality, on VOICED speech only) ---
pp = call(snd, "To PointProcess (periodic, cc)", 75, 300)
jitter = call(pp, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3) * 100          # %
shimmer = call([snd, pp], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6) * 100  # %
harm = call(snd, "To Harmonicity (cc)", 0.01, 75, 0.1, 1.0)
hv = np.array(harm.values[0])
hv = hv[hv > 0]                                # voiced frames only (drop silence)
hnr = float(np.mean(hv)) if len(hv) else 0.0   # dB

# --- intensity dynamics (speech frames only) ---
inten = snd.to_intensity(minimum_pitch=75)
iv = inten.values[0]
iv = iv[np.isfinite(iv)]
speech = iv[iv > (np.max(iv) - 25)]            # within 25 dB of peak = real speech
int_sd = float(np.std(speech))
silent_frac = float(np.mean(iv <= (np.max(iv) - 25)))


def flag(val, lo, hi):
    if val < lo:
        return f"LOW  (human {lo}-{hi})"
    if val > hi:
        return f"HIGH (human {lo}-{hi})"
    return f"ok   (human {lo}-{hi})"


print(f"\n{'='*64}\nVOICE NATURALNESS SCORECARD  —  {WAV.split('/')[-1]}\n{'='*64}")
print(f"  duration            {dur:6.1f} s   ({words} words)")
print(f"  speaking rate       {wpm:6.0f} wpm   {flag(wpm, 120, 160)}")
print(f"  voiced fraction     {voiced_frac*100:6.1f} %    {flag(voiced_frac*100, 55, 75)}")
print(f"  F0 mean             {f0_mean:6.0f} Hz    {flag(f0_mean, 100, 150)}  (male speaking)")
print(f"  F0 variation        {f0_sd_st:6.2f} st    {flag(f0_sd_st, 2.0, 4.0)}  <- intonation (flat=robotic)")
print(f"  jitter (local)      {jitter:6.2f} %     {flag(jitter, 0.4, 1.04)}  <- pitch micro-wobble")
print(f"  shimmer (local)     {shimmer:6.2f} %     {flag(shimmer, 2.0, 4.0)}  <- amplitude micro-wobble")
print(f"  HNR                 {hnr:6.1f} dB    {flag(hnr, 15, 25)}  <- >25=too-clean/synthetic")
print(f"  intensity variation {int_sd:6.1f} dB    {flag(int_sd, 4, 12)}  <- emphasis dynamics")
print(f"  silence fraction    {silent_frac*100:6.1f} %    {flag(silent_frac*100, 10, 22)}")
print(f"{'='*64}")
