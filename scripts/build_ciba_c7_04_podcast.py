from __future__ import annotations

from pathlib import Path
import subprocess

from pydub import AudioSegment, effects

ROOT = Path("recovered")
OUT_DIR = Path("assets/audio")
OUT_DIR.mkdir(parents=True, exist_ok=True)
WAV = OUT_DIR / "c7-04-con-lo-que-tenemos.wav"
MP3 = OUT_DIR / "c7-04-con-lo-que-tenemos.mp3"

tracks = {
    "R": AudioSegment.from_file(ROOT / "01-rocio.mp3"),
    "Y": AudioSegment.from_file(ROOT / "02-yadira.mp3"),
    "E": AudioSegment.from_file(ROOT / "03-emiliano.mp3"),
    "M": AudioSegment.from_file(ROOT / "04-montserrat.mp3"),
}
for key in tracks:
    tracks[key] = tracks[key].set_frame_rate(44100).set_channels(2)

theme = AudioSegment.from_file(ROOT / "05-ciba-theme.mp3").set_frame_rate(44100).set_channels(2)
whoosh = AudioSegment.from_file(ROOT / "06-transition-whoosh.mp3").set_frame_rate(44100).set_channels(2)
objects = AudioSegment.from_file(ROOT / "07-small-objects.mp3").set_frame_rate(44100).set_channels(2)
page = AudioSegment.from_file(ROOT / "08-page-turn.mp3").set_frame_rate(44100).set_channels(2)

def clip(speaker: str, start: float, end: float) -> AudioSegment:
    source = tracks[speaker]
    left = max(0, int(start * 1000) - 70)
    right = min(len(source), int(end * 1000) + 100)
    segment = source[left:right]
    if len(segment) > 220:
        segment = segment.fade_in(55).fade_out(90)
    return segment

def silence(ms: int = 300) -> AudioSegment:
    return AudioSegment.silent(duration=ms, frame_rate=44100).set_channels(2)

# Reassembled by transcript into a multi-speaker conversation. The individual source
# files contain each character's turns grouped together; these cuts restore the dialogue.
sequence = [
    ("R", 0.00, 24.36, "intro"),
    ("R", 25.76, 28.16, "question to Yadira"),
    ("Y", 0.00, 21.00, "Yadira explains her concern"),
    ("E", 0.00, 10.44, "Emiliano recalls simple play"),
    ("Y", 21.00, 26.36, "Yadira responds to her grandfather"),
    ("R", 28.16, 33.84, "question to the pediatrician"),
    ("M", 0.00, 21.20, "pediatrician explains stimulation"),
    ("Y", 26.36, 30.44, "Yadira reflects on play"),
    ("M", 22.20, 29.92, "pediatrician reinforces interaction"),
    ("E", 10.44, 15.68, "Emiliano proposes a homemade rattle"),
    ("Y", 30.44, 35.80, "Yadira proposes a reviewed play box"),
    ("R", 33.84, 44.76, "host flags unsafe objects"),
    ("M", 31.40, 59.24, "pediatrician explains toy safety"),
    ("E", 15.68, 55.68, "Emiliano reflects on safe improvisation and family support"),
    ("Y", 35.80, 43.76, "Yadira raises food insecurity"),
    ("Y", 43.76, 52.72, "Yadira asks about food substitutions"),
    ("M", 59.28, 102.76, "pediatrician explains infant feeding safety"),
    ("R", 44.76, 50.84, "host introduces clothing and reused items"),
    ("Y", 52.76, 62.64, "Yadira asks about clothing and support"),
    ("M", 102.76, 137.20, "pediatrician explains safe reuse and support"),
    ("R", 50.84, 55.72, "host asks what must never be improvised"),
    ("M", 137.20, 178.04, "pediatrician summarizes non-negotiable safety"),
    ("M", 178.04, 183.68, "pediatrician closes the thought"),
    ("R", 55.72, 78.20, "CIBA closing"),
]

program = AudioSegment.empty()
for index, (speaker, start, end, label) in enumerate(sequence):
    segment = effects.normalize(clip(speaker, start, end), headroom=2.5)
    if index:
        program += silence(330 if label not in ("intro", "CIBA closing") else 500)
    if label in (
        "question to the pediatrician",
        "host flags unsafe objects",
        "pediatrician explains infant feeding safety",
        "host introduces clothing and reused items",
        "host asks what must never be improvised",
    ):
        program += (whoosh - 19).fade_in(80).fade_out(250)
        program += silence(120)
    if label == "Emiliano proposes a homemade rattle":
        program += (objects - 24).fade_in(60).fade_out(250)
        program += silence(100)
    if label == "Yadira raises food insecurity":
        program += (page - 23).fade_in(50).fade_out(200)
        program += silence(100)
    program += segment

opening = theme[:5000].fade_in(500).fade_out(700) - 7
closing = theme[30000:41000].fade_in(700).fade_out(2200) - 5
program = opening + program + silence(250) + closing

music_loop = theme
while len(music_loop) < len(program) + 1000:
    music_loop += theme
music_bed = music_loop[:len(program)].low_pass_filter(2600) - 27
music_bed = music_bed.fade_in(1800).fade_out(5000)
master = program.overlay(music_bed).set_frame_rate(44100).set_channels(2)
master.export(WAV, format="wav")

subprocess.run(
    [
        "ffmpeg", "-y", "-i", str(WAV),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=8",
        "-codec:a", "libmp3lame", "-b:a", "128k", "-ar", "44100",
        str(MP3),
    ],
    check=True,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
WAV.unlink(missing_ok=True)
print(f"Master creado: {MP3} ({MP3.stat().st_size} bytes)")
