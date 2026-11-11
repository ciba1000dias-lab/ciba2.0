#!/usr/bin/env python3
"""Build CIBA C4-12 podcast from approved HeyGen dialogue stems."""
from __future__ import annotations
import argparse, subprocess, tempfile, wave, urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import imageio_ffmpeg
from mutagen.mp3 import MP3

CLIPS = [
 ("mama","https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/84854979e66846989bc6c5855f53268f/id=e4907f334ba24482991305b3ec355414.mp3"),
 ("papa","https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/70bc24b8126c446c8cf50fc1a01eb834/id=752596d4ea7747b4802c72f113a91372.mp3"),
 ("pediatra","https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/40ded5e9651a43a58b77f72699b95688/id=f245d5f687aa4d1a8074482b5310f649.mp3"),
 ("mama-cierre","https://resource2.heygen.ai/text_to_speech/bb9c33b9a4f246bfaad6f76f0b2e5310/84854979e66846989bc6c5855f53268f/id=72200166d26440d9b3a161eee5464ae3.mp3"),
]
def run(cmd):
 subprocess.run(cmd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
def write_wav(path,left,right,rate=22050):
 pcm=(np.clip(np.column_stack((left,right)),-.98,.98)*32767).astype("<i2")
 with wave.open(str(path),"wb") as f:
  f.setnchannels(2);f.setsampwidth(2);f.setframerate(rate);f.writeframes(pcm.tobytes())
def make_music(path,duration,rate=22050):
 n=int(duration*rate);t=np.arange(n,dtype=np.float64)/rate;l=np.zeros(n);r=np.zeros(n)
 chords=[(261.63,329.63,392.00,493.88),(220.00,261.63,329.63,392.00),(174.61,220.00,261.63,349.23),(196.00,246.94,293.66,392.00)]
 block=int(5.2*rate)
 for start in range(0,n,block):
  end=min(n,start+block);x=t[start:end]-t[start];ch=chords[(start//block)%4]
  env=np.minimum(1,x/.5)*np.minimum(1,(duration-t[start:end])/1.5)
  pad=sum(np.sin(2*np.pi*f*x)/(i+1) for i,f in enumerate(ch))+.2*np.sin(2*np.pi*(ch[0]/2)*x)
  l[start:end]+=.026*env*pad;r[start:end]+=.024*env*pad
 notes=[523.25,587.33,659.25,587.33,493.88,587.33,659.25,783.99]
 for k,on in enumerate(np.arange(.4,duration,.95)):
  st=int(on*rate);en=min(n,st+int(.7*rate));x=np.arange(en-st)/rate
  env=np.exp(-5*x)*np.minimum(1,x/.015);tone=np.sin(2*np.pi*notes[k%8]*x)
  l[st:en]+=.012*env*tone;r[st:en]+=.011*env*tone
 fade=np.minimum(1,t/1.8)*np.minimum(1,(duration-t)/2.5);write_wav(path,l*fade,r*fade,rate)
def make_fx(path,duration,rate=22050):
 n=int(duration*rate);l=np.zeros(n);r=np.zeros(n)
 rng=np.random.default_rng(412)
 # Soft three-note opening/closing motif.
 for on in (.18,max(.25,duration-2.2)):
  for j,freq in enumerate((587.33,698.46,880.0)):
   st=int((on+j*.13)*rate);ln=min(int(1.1*rate),n-st)
   if ln<=0:continue
   x=np.arange(ln)/rate;env=np.exp(-3.5*x)*np.minimum(1,x/.018)
   s=.016*env*np.sin(2*np.pi*freq*x);l[st:st+ln]+=s;r[st:st+ln]+=.92*s
 # Subtle soft transition swishes between family speakers.
 for on in (29.0,52.0,144.0):
  st=int(on*rate);ln=min(int(.38*rate),n-st)
  if ln<=0:continue
  noise=np.convolve(rng.normal(0,1,ln),np.ones(17)/17,mode="same")
  x=np.arange(ln)/rate;env=np.sin(np.pi*np.minimum(1,x/.38))**1.5
  s=.035*noise*env;l[st:st+ln]+=s;r[st:st+ln]+=.9*s
 write_wav(path,l,r,rate)
def main():
 p=argparse.ArgumentParser();p.add_argument("--out",required=True);out=Path(p.parse_args().out);out.parent.mkdir(parents=True,exist_ok=True)
 ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
 with tempfile.TemporaryDirectory(prefix="ciba-c4-12-") as td:
  tmp=Path(td)
  def download(item):
   i,(speaker,url)=item;dest=tmp/f"{i:02d}-{speaker}.mp3"
   req=urllib.request.Request(url,headers={"User-Agent":"CIBA-Podcast-Builder/1.0"})
   with urllib.request.urlopen(req,timeout=60) as response,dest.open("wb") as f:f.write(response.read())
   if dest.stat().st_size<4096:raise RuntimeError(f"Audio {i} demasiado pequeño")
   return dest
  with ThreadPoolExecutor(max_workers=4) as pool:clips=list(pool.map(download,enumerate(CLIPS)))
  inputs=[];filters=[]
  for i,clip in enumerate(clips):
   inputs += ["-i",str(clip)]
   filters.append(f"[{i}:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=stereo,apad=pad_dur=0.38,atrim=duration=999[s{i}]")
  concat="".join(f"[s{i}]" for i in range(len(clips)))
  speech=tmp/"speech.wav";graph=";".join(filters)+f";{concat}concat=n={len(clips)}:v=0:a=1[speech]"
  run([ffmpeg,"-y",*inputs,"-filter_complex",graph,"-map","[speech]","-c:a","pcm_s16le","-ar","44100",str(speech)])
  total=sum(MP3(x).info.length for x in clips)+.38*len(clips)+3
  music=tmp/"music.wav";fx=tmp/"fx.wav";make_music(music,total);make_fx(fx,total)
  run([ffmpeg,"-y","-i",str(speech),"-i",str(music),"-i",str(fx),"-filter_complex",
   "[1:a]volume=0.72,aresample=44100[mb];[mb][0:a]sidechaincompress=threshold=0.018:ratio=5:attack=18:release=420[duck];[0:a][duck][2:a]amix=inputs=3:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[mix]",
   "-map","[mix]","-c:a","libmp3lame","-b:a","112k","-ar","44100",
   "-metadata","title=Que la pantalla no se quede con el juego","-metadata","artist=Podcast CIBA","-metadata","album=CIBA · Crecemos acompañándonos",str(out)])
  info=MP3(out).info
  print(f"Podcast CIBA C4-12 listo: {info.length:.1f} s, {out.stat().st_size} bytes, {out}")
if __name__=="__main__":main()
