#!/usr/bin/env python3
"""Build the CIBA C4-11 podcast master from the approved HeyGen dialogue stems."""
from __future__ import annotations
import argparse
import json
import subprocess
import tempfile
import urllib.request
import wave
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import imageio_ffmpeg
from mutagen.mp3 import MP3

CLIPS = [
    ("intro", "https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/84854979e66846989bc6c5855f53268f/id=ed21665db47142ac8510903fb83c2fdc.mp3"),
    ("mama", "https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/84854979e66846989bc6c5855f53268f/id=e27378b9fee146c0858e43bb0838abc5.mp3"),
    ("papa", "https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/70bc24b8126c446c8cf50fc1a01eb834/id=8fc1dc17af8d45b28dd3acde70bd0175.mp3"),
    ("pediatra", "https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/40ded5e9651a43a58b77f72699b95688/id=641885725c7140b0b5f2afb3f500d8f8.mp3"),
    ("mama", "https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/84854979e66846989bc6c5855f53268f/id=fd304278847246a8b77aef60571e85e8.mp3"),
    ("pediatra", "https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/40ded5e9651a43a58b77f72699b95688/id=151ec238bca2498ebebb7c3fb9ee8499.mp3"),
    ("papa", "https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/70bc24b8126c446c8cf50fc1a01eb834/id=884e1423312a4eef8816351a8ce88c42.mp3"),
    ("pediatra", "https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/40ded5e9651a43a58b77f72699b95688/id=8ca64af9c43445c08402b30ad7fe93fe.mp3"),
    ("mama", "https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/84854979e66846989bc6c5855f53268f/id=e11aededc7c14360b41275c6af403ddd.mp3"),
    ("papa", "https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/70bc24b8126c446c8cf50fc1a01eb834/id=c5185ad7c2d14cd2804c9acc1d9cddfa.mp3"),
    ("pediatra", "https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/40ded5e9651a43a58b77f72699b95688/id=83ff9cbca4964ae792beadb1897a6dd8.mp3"),
]

def run(args: list[str]) -> None:
    subprocess.run(args, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def write_stereo_wav(path: Path, left: np.ndarray, right: np.ndarray, rate: int = 22050) -> None:
    stereo = np.column_stack((left, right))
    pcm = np.clip(stereo, -0.98, 0.98)
    pcm = (pcm * 32767).astype("<i2")
    with wave.open(str(path), "wb") as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(pcm.tobytes())

def make_music(path: Path, duration: float, rate: int = 22050) -> None:
    n = int(duration * rate)
    t = np.arange(n, dtype=np.float64) / rate
    left = np.zeros(n, dtype=np.float64)
    right = np.zeros(n, dtype=np.float64)
    chords = [
        (261.63, 329.63, 392.00, 493.88),  # Cmaj7
        (220.00, 261.63, 329.63, 392.00),  # Am7
        (174.61, 220.00, 261.63, 349.23),  # Fmaj7
        (196.00, 246.94, 293.66, 392.00),  # Gsus2
    ]
    block = int(4.8 * rate)
    for start in range(0, n, block):
        end = min(n, start + block)
        local = t[start:end] - t[start]
        chord = chords[(start // block) % len(chords)]
        fade = np.minimum(1.0, local / 0.35) * np.minimum(1.0, (duration - t[start:end]) / 1.2)
        pad = sum(np.sin(2*np.pi*f*local) / (i+1) for i, f in enumerate(chord))
        pad += 0.22 * np.sin(2*np.pi*(chord[0]/2)*local)
        left[start:end] += 0.035 * fade * pad
        right[start:end] += 0.033 * fade * pad
    # A quiet, repeating upper-register figure adds a light piano-like pulse.
    notes = [523.25, 587.33, 659.25, 587.33, 493.88, 587.33, 659.25, 783.99]
    beat = 0.9
    for k, onset in enumerate(np.arange(0.35, duration, beat)):
        start = int(onset * rate)
        end = min(n, start + int(0.72 * rate))
        if end <= start:
            continue
        local = np.arange(end-start, dtype=np.float64) / rate
        env = np.exp(-5.2 * local) * np.minimum(1.0, local / 0.012)
        tone = np.sin(2*np.pi*notes[k % len(notes)]*local)
        tone += 0.22 * np.sin(2*np.pi*notes[k % len(notes)]*2*local)
        left[start:end] += 0.018 * env * tone
        right[start:end] += 0.016 * env * tone
    # Gentle fade-in/out.
    left *= np.minimum(1.0, t / 1.8) * np.minimum(1.0, (duration-t) / 2.5)
    right *= np.minimum(1.0, t / 1.8) * np.minimum(1.0, (duration-t) / 2.5)
    write_stereo_wav(path, left, right, rate)

def make_sfx(path: Path, duration: float, rate: int = 22050) -> None:
    n = int(duration * rate)
    left = np.zeros(n, dtype=np.float64)
    right = np.zeros(n, dtype=np.float64)
    rng = np.random.default_rng(411)
    # Soft opening/closing three-note chime.
    for onset in (0.15, max(0.2, duration-2.2)):
        for j, freq in enumerate((523.25, 659.25, 783.99)):
            start = int((onset + j*0.12) * rate)
            length = min(int(1.4*rate), n-start)
            if length <= 0:
                continue
            x = np.arange(length, dtype=np.float64) / rate
            env = np.exp(-3.0*x) * np.minimum(1.0, x/0.015)
            sig = 0.022 * env * np.sin(2*np.pi*freq*x)
            left[start:start+length] += sig
            right[start:start+length] += sig * 0.92
    # Page-turn rustles at natural pauses between ideas.
    for onset in (28.0, 101.0):
        start = int(onset * rate)
        length = min(int(0.48*rate), n-start)
        if length <= 0:
            continue
        noise = rng.normal(0, 1, length)
        # Smooth the noise to create a soft paper-like swish, not a harsh hiss.
        kernel = np.ones(19) / 19
        noise = np.convolve(noise, kernel, mode="same")
        x = np.arange(length, dtype=np.float64) / rate
        env = np.sin(np.pi*np.minimum(1, x/0.48))**1.5
        swish = 0.07 * noise * env
        left[start:start+length] += swish
        right[start:start+length] += swish * 0.9
    write_stereo_wav(path, left, right, rate)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ciba-podcast-") as tmp:
        work = Path(tmp)
        def download_clip(item):
            i, (speaker, url) = item
            target = work / f"{i:02d}-{speaker}.mp3"
            request = urllib.request.Request(url, headers={"User-Agent": "CIBA-Podcast-Builder/1.0"})
            with urllib.request.urlopen(request, timeout=35) as response, target.open("wb") as dest:
                dest.write(response.read())
            if target.stat().st_size < 4096:
                raise RuntimeError(f"Audio source {i} is unexpectedly small")
            return target
        with ThreadPoolExecutor(max_workers=4) as pool:
            files = list(pool.map(download_clip, enumerate(CLIPS)))
        # Join all speakers with a short natural pause. Every stem is resampled identically.
        inputs = []
        filters = []
        for i, file in enumerate(files):
            inputs += ["-i", str(file)]
            filters.append(f"[{i}:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo,apad=pad_dur=0.28,atrim=duration=999[s{i}]")
        concat_inputs = "".join(f"[s{i}]" for i in range(len(files)))
        graph = ";".join(filters) + f";{concat_inputs}concat=n={len(files)}:v=0:a=1[speech]"
        speech = work / "speech.wav"
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        run([ffmpeg,"-y",*inputs,"-filter_complex",graph,"-map","[speech]","-c:a","pcm_s16le","-ar","44100",str(speech)])
        speech_duration = sum((13.725,11.345,25.340,7.288,27.732,9.459,28.672,6.986,7.033,41.024,7.892)) + 0.28*len(files)
        mix_duration = speech_duration + 3.0
        music = work / "music.wav"
        sfx = work / "sfx.wav"
        make_music(music,mix_duration)
        make_sfx(sfx,mix_duration)
        run([
            ffmpeg,"-y","-i",str(speech),"-i",str(music),"-i",str(sfx),
            "-filter_complex",
            "[1:a]volume=0.85,aresample=44100[mb];"
            "[mb][0:a]sidechaincompress=threshold=0.018:ratio=5:attack=18:release=420[duck];"
            "[0:a][duck][2:a]amix=inputs=3:duration=first:normalize=0,"
            "loudnorm=I=-16:TP=-1.5:LRA=11[mix]",
            "-map","[mix]","-c:a","libmp3lame","-b:a","128k","-ar","44100",
            "-metadata","title=Un cuento no tiene que terminarse",
            "-metadata","artist=Podcast CIBA",
            "-metadata","album=CIBA · Crecemos acompañándonos",
            str(output)
        ])
        info=MP3(output).info
        print(f"Podcast CIBA listo: {info.length:.1f} s, {output.stat().st_size} bytes, {output}")

if __name__ == "__main__":
    main()
