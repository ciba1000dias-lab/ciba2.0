#!/usr/bin/env python3
"""Construye el episodio CIBA C4-10 con voces HeyGen, música y efectos originales."""
from __future__ import annotations
import argparse, subprocess, tempfile, wave
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import imageio_ffmpeg
from mutagen.mp3 import MP3

CLIPS = [
 ("mama","https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/84854979e66846989bc6c5855f53268f/id=ae68cf2ae3934e998b2c6f6375f730ac.mp3"),
 ("papa","https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/70bc24b8126c446c8cf50fc1a01eb834/id=2bc587a059b548aaa9d645e9b5d459db.mp3"),
 ("pediatra","https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/40ded5e9651a43a58b77f72699b95688/id=7fed57ba19e54fe7bdffdaf900a1aea8.mp3"),
 ("mama","https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/84854979e66846989bc6c5855f53268f/id=abb0f5913d4a408b8a437067499e55f9.mp3"),
 ("pediatra","https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/40ded5e9651a43a58b77f72699b95688/id=0ba7aa86da26404485ad9f28f103fd83.mp3"),
 ("papa","https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/70bc24b8126c446c8cf50fc1a01eb834/id=98294d82fcb642cea5a93cce5652d704.mp3"),
 ("pediatra","https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/40ded5e9651a43a58b77f72699b95688/id=2b68d05f3ba74db881f3a905cf3a9c07.mp3"),
 ("mama","https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/84854979e66846989bc6c5855f53268f/id=58500efe093e40e38c400c27e1fe8c80.mp3"),
 ("pediatra","https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/40ded5e9651a43a58b77f72699b95688/id=18a9c325185744f8b33e1ca07f0cd121.mp3"),
 ("papa","https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/70bc24b8126c446c8cf50fc1a01eb834/id=66b7ddbaed07401494953f1cacaabd07.mp3"),
 ("mama","https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/84854979e66846989bc6c5855f53268f/id=69c1c1a9ad20421b8b3e1f4f5e2e7196.mp3"),
]

def run(args):
 subprocess.run(args,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)

def wav_write(path,left,right,rate=22050):
 stereo=np.column_stack((left,right)); pcm=(np.clip(stereo,-.98,.98)*32767).astype("<i2")
 with wave.open(str(path),"wb") as out:
  out.setnchannels(2);out.setsampwidth(2);out.setframerate(rate);out.writeframes(pcm.tobytes())

def music(path,duration,rate=22050):
 n=int(duration*rate);t=np.arange(n,dtype=np.float64)/rate
 l=np.zeros(n);r=np.zeros(n)
 chords=[(261.63,329.63,392.00,493.88),(220.00,261.63,329.63,392.00),(174.61,220.00,261.63,349.23),(196.00,246.94,293.66,392.00)]
 block=int(4.8*rate)
 for start in range(0,n,block):
  end=min(n,start+block);x=t[start:end]-t[start];ch=chords[(start//block)%len(chords)]
  env=np.minimum(1,x/.35)*np.minimum(1,(duration-t[start:end])/1.2)
  pad=sum(np.sin(2*np.pi*f*x)/(i+1) for i,f in enumerate(ch))+.22*np.sin(2*np.pi*(ch[0]/2)*x)
  l[start:end]+=.035*env*pad;r[start:end]+=.033*env*pad
 notes=[523.25,587.33,659.25,587.33,493.88,587.33,659.25,783.99]
 for k,onset in enumerate(np.arange(.35,duration,.9)):
  start=int(onset*rate);end=min(n,start+int(.72*rate));x=np.arange(end-start)/rate
  env=np.exp(-5.2*x)*np.minimum(1,x/.012);tone=np.sin(2*np.pi*notes[k%len(notes)]*x)+.22*np.sin(2*np.pi*notes[k%len(notes)]*2*x)
  l[start:end]+=.018*env*tone;r[start:end]+=.016*env*tone
 fade=np.minimum(1,t/1.8)*np.minimum(1,(duration-t)/2.5);l*=fade;r*=fade
 wav_write(path,l,r,rate)

def effects(path,duration,rate=22050):
 n=int(duration*rate);l=np.zeros(n);r=np.zeros(n);rng=np.random.default_rng(410)
 for onset in (.15,max(.2,duration-2.2)):
  for j,f in enumerate((523.25,659.25,783.99)):
   start=int((onset+j*.12)*rate);length=min(int(1.4*rate),n-start)
   if length<=0:continue
   x=np.arange(length)/rate;env=np.exp(-3*x)*np.minimum(1,x/.015);tone=.022*env*np.sin(2*np.pi*f*x)
   l[start:start+length]+=tone;r[start:start+length]+=.92*tone
 for onset in (30.0,68.0,113.5,154.2,195.6):
  start=int(onset*rate);length=min(int(.48*rate),n-start)
  if length<=0:continue
  noise=np.convolve(rng.normal(0,1,length),np.ones(19)/19,mode="same")
  x=np.arange(length)/rate;swish=.07*noise*np.sin(np.pi*np.minimum(1,x/.48))**1.5
  l[start:start+length]+=swish;r[start:start+length]+=.9*swish
 wav_write(path,l,r,rate)

def main():
 p=argparse.ArgumentParser();p.add_argument("--out",required=True);out=Path(p.parse_args().out);out.parent.mkdir(parents=True,exist_ok=True)
 ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
 with tempfile.TemporaryDirectory(prefix="ciba-c4-10-") as td:
  tmp=Path(td)
  def download(item):
   i,(speaker,url)=item;dest=tmp/f"{i:02d}-{speaker}.mp3"
   run(["curl","-fLsS","--retry","2","--connect-timeout","20","--max-time","90",url,"-o",str(dest)])
   if dest.stat().st_size<4096:raise RuntimeError(f"Audio {i} demasiado pequeño")
   return dest
  with ThreadPoolExecutor(max_workers=4) as pool: clips=list(pool.map(download,enumerate(CLIPS)))
  inputs=[];filters=[]
  for i,clip in enumerate(clips):
   inputs += ["-i",str(clip)]
   filters.append(f"[{i}:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo,apad=pad_dur=0.28,atrim=duration=999[s{i}]")
  concat="".join(f"[s{i}]" for i in range(len(clips)))
  graph=";".join(filters)+f";{concat}concat=n={len(clips)}:v=0:a=1[speech]"
  speech=tmp/"speech.wav"
  run([ffmpeg,"-y",*inputs,"-filter_complex",graph,"-map","[speech]","-c:a","pcm_s16le","-ar","44100",str(speech)])
  duration=MP3(clips[0]).info.length
  total=sum(MP3(x).info.length for x in clips)+.28*len(clips)+3.0
  bg=tmp/"music.wav";sfx=tmp/"effects.wav";music(bg,total);effects(sfx,total)
  run([ffmpeg,"-y","-i",str(speech),"-i",str(bg),"-i",str(sfx),"-filter_complex",
   "[1:a]volume=0.82,aresample=44100[mb];[mb][0:a]sidechaincompress=threshold=0.018:ratio=5:attack=18:release=420[duck];[0:a][duck][2:a]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[mix]",
   "-map","[mix]","-c:a","libmp3lame","-b:a","128k","-ar","44100",
   "-metadata","title=Pequeños dedos, grandes descubrimientos","-metadata","artist=Podcast CIBA","-metadata","album=CIBA · Crecemos acompañándonos",str(out)])
  info=MP3(out).info
  print(f"Podcast CIBA C4-10 listo: {info.length:.1f} s, {out.stat().st_size} bytes, {out}")
if __name__=="__main__":main()
