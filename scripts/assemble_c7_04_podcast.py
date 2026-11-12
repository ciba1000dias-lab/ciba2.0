#!/usr/bin/env python3
"""Assemble the CIBA C7-04 master podcast from the recovered HeyGen source tracks."""
from pathlib import Path
from pydub import AudioSegment, effects

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "source-audio"
OUT = ROOT / "assets" / "audio" / "c7-04-con-lo-que-tenemos.mp3"

def load(name):
    p = SRC / name
    if not p.exists():
        raise SystemExit(f"Missing source audio: {p}")
    return AudioSegment.from_file(p).set_frame_rate(44100).set_channels(2)

tracks = {
    "rocio": load("01-rocio.mp3"),
    "yadira": load("02-yadira.mp3"),
    "emiliano": load("03-emiliano.mp3"),
    "montserrat": load("04-montserrat.mp3"),
}
theme = load("05-ciba-theme.mp3")
whoosh = load("06-transition-whoosh.mp3") if (SRC / "06-transition-whoosh.mp3").exists() else None
rattle = load("07-small-objects.mp3") if (SRC / "07-small-objects.mp3").exists() else None
page = load("08-page-turn.mp3") if (SRC / "08-page-turn.mp3").exists() else None

# Each range is a verified speech interval from the automatic transcript.
# The order restores the four-person conversation rather than playing four
# character tracks consecutively.
sequence = [
    ("rocio", 0.00, 25.76),
    ("yadira", 0.00, 20.48),
    ("emiliano", 0.00, 10.44),
    ("yadira", 20.48, 26.36),
    ("rocio", 25.76, 33.84),
    ("montserrat", 0.00, 29.92),
    ("emiliano", 10.44, 19.96),
    ("montserrat", 31.40, 59.24),
    ("rocio", 33.84, 44.76),
    ("emiliano", 19.96, 39.40),
    ("yadira", 26.36, 39.56),
    ("montserrat", 59.28, 102.76),
    ("yadira", 39.56, 52.72),
    ("rocio", 44.76, 53.40),
    ("montserrat", 102.76, 124.92),
    ("yadira", 52.76, 62.64),
    ("emiliano", 39.40, 55.68),
    ("montserrat", 124.92, 183.68),
    ("rocio", 53.40, 78.20),
]

silence = AudioSegment.silent(duration=230, frame_rate=44100).set_channels(2)
speech = AudioSegment.empty()
for who, start, end in sequence:
    clip = tracks[who][int(start * 1000):int(end * 1000)]
    if len(clip) < 250:
        raise SystemExit(f"Suspiciously short segment: {who} {start}-{end}")
    # Keep natural pauses while bringing voices to a consistent perceived level.
    clip = effects.normalize(clip, headroom=3.0)
    speech += clip + silence

# Official theme: musical opening, discreet low-level bed, and recognizable close.
intro = theme[:15000].fade_out(1200)
outro = theme[-16000:].fade_in(900).fade_out(2600)
bed = (theme * (len(speech) // len(theme) + 1))[:len(speech)].apply_gain(-29)
speech_mix = speech.overlay(bed)

# Incidental accents are kept quiet and placed at natural topic transitions.
def place_effect(base, effect, position_ms, gain_db):
    if effect is None:
        return base
    return base.overlay(effect.apply_gain(gain_db), position=position_ms)

speech_mix = place_effect(speech_mix, whoosh, 0, -17)
speech_mix = place_effect(speech_mix, rattle, 92000, -21)
speech_mix = place_effect(speech_mix, page, 205000, -20)
speech_mix = place_effect(speech_mix, whoosh, 300000, -19)

master = intro + speech_mix + outro
master = master.fade_in(500).fade_out(1800)
master = effects.normalize(master, headroom=1.5)

OUT.parent.mkdir(parents=True, exist_ok=True)
master.export(
    OUT,
    format="mp3",
    bitrate="128k",
    tags={
        "title": "Con lo que tenemos: criar también es crear",
        "artist": "CIBA",
        "album": "Zona Podcast CIBA · C7",
        "comment": "Episodio C7-04. Voces, canción tema CIBA y efectos incidentales."
    },
)
print(f"MASTER={OUT}")
print(f"DURATION_SECONDS={len(master)/1000:.2f}")
print(f"SIZE_BYTES={OUT.stat().st_size}")
