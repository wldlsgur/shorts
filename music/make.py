"""Make a full music video (1920x1080) + highlight Short (1080x1920) + thumbnail from one song.

Usage: python3 music/make.py spec.json OUTDIR
spec.json:
{
  "mp3": "/path/song.mp3",
  "title": "Friday Night Family",          # song title, shown in full on the Short
  "small": ["FRIDAY", "NIGHT"],            # 1-2 short neon words on the cover (A-Z only, <= 7 chars each)
  "big": "Family",                         # big script word on the cover (Latin letters)
  "palette": "sunset",                     # sunset | ocean | neon | forest | night
  "genre": "Funk Pop",                     # shown as "<genre> · AI Original"
  "thumb_lines": ["Friday Night", "Family"], # 1-2 lines on the YouTube thumbnail
  "highlight_lines": ["...", "..."],       # up to 6 chorus lines shown on the Short
  "highlight_start": null,                 # seconds; null = auto (loudest window)
  "short_len": 34,
  "seed": 7                                # changes the skyline
}
Outputs in OUTDIR: full.mp4, short.mp4, thumb.png, cover.png
"""
import json, os, subprocess, sys
import numpy as np
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
spec = json.load(open(sys.argv[1], encoding="utf-8")); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
mp3 = spec["mp3"]; L = spec.get("short_len", 34)

dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3],
                           capture_output=True, text=True).stdout)
start = spec.get("highlight_start")
if start is None:  # loudest window, snapped to a dip just before it (section boundary)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp3, "-ac", "1", "-ar", "8000", "-f", "f32le", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.float32); sr = 8000; q = sr // 4
    r = np.sqrt(np.convolve(a ** 2, np.ones(q) / q, "valid"))[::q]
    win = int(L * 4); score = np.convolve(r, np.ones(win), "valid")
    best = int(np.argmax(score[: max(1, len(r) - win - 8)]))
    lo = max(0, best - 12); dip = lo + int(np.argmin(r[lo:best + 2]))
    start = dip / 4
start = max(0.0, min(start, dur - L)); print(f"duration {dur:.1f}s, highlight {start:.2f}s", flush=True)

JS = """(o)=>{window.OPT=o.opt;const c=document.getElementById('c');c.width=o.W;c.height=o.H;const x=c.getContext('2d');
 const oc=document.createElement('canvas');oc.width=oc.height=1000;cover(oc.getContext('2d'),0,0,1000);
 const S=Math.max(o.W,o.H)*1.2;const blurbg=()=>{x.filter='blur(60px) brightness(.45) saturate(1.3)';x.drawImage(oc,-o.W*0.1,-o.H*0.1,S,S);x.filter='none';};
 const put=(ox,oy,sz)=>x.drawImage(oc,ox,oy,sz,sz);
 const fit=(t,font,size,maxw)=>{let s=size;x.font=s+'px '+font;while(x.measureText(t).width>maxw&&s>30){s-=4;x.font=s+'px '+font;}};
 if(o.kind==='cover'){cover(x,0,0,o.W);}
 if(o.kind==='thumb'){blurbg();put(80,60,600);x.textAlign='left';fit(o.genre.toUpperCase(),'Mono',72,500);x.fillStyle='#ffe9f5';x.shadowColor='#ff2f8e';x.shadowBlur=24;x.fillText(o.genre.toUpperCase(),730,250);x.shadowBlur=0;
   x.fillStyle='#ffd34d';o.thumb.forEach((t,i)=>{fit(t,'Shrik',96,520);x.fillText(t,720,400+i*110);});x.font='40px sans-serif';x.fillStyle='#fff';x.fillText('🎵 AI Original Song',740,620);}
 if(o.kind==='long'){blurbg();put(110,140,800);x.textAlign='left';
   fit(o.title,'Shrik',110,820);x.fillStyle='#ffd34d';x.fillText(o.title,1000,420);
   x.font='38px sans-serif';x.fillStyle='rgba(255,255,255,.85)';x.fillText(o.genre+' · AI Original',1010,500);
   x.font='26px sans-serif';x.fillStyle='rgba(255,255,255,.55)';x.fillText('AI-generated music (made with Suno)',1010,1010);
   x.fillStyle='rgba(255,255,255,.18)';x.fillRect(1010,930,800,8);}
 if(o.kind==='short'){blurbg();put(110,170,860);x.textAlign='center';
   x.font='30px sans-serif';x.fillStyle='rgba(255,255,255,.7)';x.fillText('AI-generated music · Suno',540,120);
   fit(o.title,'Shrik',86,980);x.fillStyle='#ffd34d';x.lineWidth=12;x.strokeStyle='rgba(30,5,40,.6)';x.strokeText(o.title,540,1130);x.fillText(o.title,540,1130);
   o.lyr.slice(0,6).forEach((l,i)=>{fit(l,'sans-serif',40,980);x.font=x.font.replace('px','px')+'';x.font='bold '+x.font;x.fillStyle=i%2?'#ffd6ea':'#fff';x.fillText(l,540,1340+i*56);});}
}"""
opt = {k: spec[k] for k in ("small", "big", "palette", "seed") if k in spec}
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.goto("file://" + os.path.join(HERE, "cover.html"))
    pg.evaluate("Promise.race([new Promise(r=>setTimeout(r,3000)),Promise.all([document.fonts.load('80px Mono'),document.fonts.load('80px Shrik')])])")
    pg.wait_for_timeout(500)
    for kind, W, H in [("cover", 1400, 1400), ("thumb", 1280, 720), ("long", 1920, 1080), ("short", 1080, 1920)]:
        pg.set_viewport_size({"width": W, "height": H})
        pg.evaluate(JS, {"kind": kind, "W": W, "H": H, "opt": opt, "title": spec["title"], "genre": spec.get("genre", "Pop"),
                         "thumb": spec.get("thumb_lines", [spec["title"]]), "lyr": spec.get("highlight_lines", [])})
        pg.locator("canvas").screenshot(path=os.path.join(out, f"{kind}.png"))
    b.close()

def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr[-2000:])

o = lambda n: os.path.join(out, n)
run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "30", "-i", o("long.png"), "-i", mp3,
     "-f", "lavfi", "-i", "color=c=0x00000000:s=800x8:r=30,format=rgba", "-f", "lavfi", "-i", "color=c=0xFF5FA2:s=800x8:r=30,format=rgba",
     "-filter_complex", f"[1:a]aformat=channel_layouts=mono,showwaves=s=800x170:mode=cline:rate=30:colors=0xFFD34D@0.9:scale=sqrt[w];"
     f"[2:v][3:v]overlay=x='-800+800*t/{dur:.2f}':eval=frame:shortest=1[bar];[0:v][w]overlay=1010:700[a];[a][bar]overlay=1010:930,format=yuv420p[v]",
     "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k",
     "-t", f"{dur:.2f}", "-movflags", "+faststart", o("full.part.mp4")])
os.replace(o("full.part.mp4"), o("full.mp4"))
run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "30", "-i", o("short.png"), "-ss", f"{start:.2f}", "-t", str(L), "-i", mp3,
     "-filter_complex", f"[1:a]afade=t=in:d=0.3,afade=t=out:st={L-1.7}:d=1.7,asplit[a1][a2];[a1]aformat=channel_layouts=mono,"
     "showwaves=s=800x110:mode=cline:rate=30:colors=0xFFD34D@0.9:scale=sqrt[w];[0:v][w]overlay=140:1175,format=yuv420p[v]",
     "-map", "[v]", "-map", "[a2]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-tune", "stillimage", "-c:a", "aac", "-b:a", "192k",
     "-t", str(L), "-movflags", "+faststart", o("short.part.mp4")])
os.replace(o("short.part.mp4"), o("short.mp4"))
print("ok", out)
