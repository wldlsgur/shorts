"""Render a "build-your-power" price-grid short (1080x1920, 12s, 30fps) from a JSON spec.

Usage:
  python3 generator/render.py specs/<file>.json out.mp4
  PREVIEW=9 python3 generator/render.py specs/<file>.json frame.jpg   # one still at 9s

Format: 4 price columns x 4 rows. Viewer picks ONE cell from EACH row and the total must
fit the budget. Rows are e.g. 능력 / 지속시간 / 발동 조건 / 패널티 (row 4 is usually a penalty,
priced so the cheap column is the WORST penalty — that creates the dilemma).

Spec:
{
  "title": ["만원으로!", "초능력 뽑기"],          # 2 lines, short
  "budget": "1만원",
  "prices": [1000, 2000, 3000, 4000],           # 원, shown as 1,000원
  "rows": [
    {"key": "A", "label": "능력",     "cells": [["작은 물체 이동", "🪄"], ["투명인간", "👻"], ["순간이동", "🌀"], ["시간 조작", "⏳"]]},
    {"key": "B", "label": "지속시간", "cells": [...]},
    {"key": "C", "label": "발동 조건", "cells": [...]},
    {"key": "D", "label": "패널티",   "cells": [...]}
  ],
  "footer": "줄마다 하나씩! 만원 안에서 골라봐",
  "youtube_title": "..."
}
Cell text: about 9 characters max (two short lines allowed with "\n"). One emoji per cell.
"""
import json, sys, html, subprocess, os, tempfile
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
spec = json.load(open(sys.argv[1], encoding="utf-8")); out = sys.argv[2]
e = html.escape

ROW_COLORS = [("#ffd6dc", "#fff1f3"), ("#cfe6ff", "#eef6ff"), ("#e3d6ff", "#f4eeff"), ("#ffe9a8", "#fff8e0")]
HEAD_COLORS = ["#ffd6dc", "#cfe6ff", "#e3d6ff", "#ffe9a8"]

CSS = """*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;font-family:"Jua","Noto Sans CJK KR",sans-serif;color:#2b2233;overflow:hidden;
background:#fffaf2;background-image:radial-gradient(#f1e6d6 2px,transparent 2.5px);background-size:36px 36px}
.top{position:relative;padding:70px 56px 0;height:330px}
h1{font-size:96px;line-height:1.08;font-weight:400;letter-spacing:-1px;color:#2b2233}
h1 .l2{color:#ff5a76}
.budget{position:absolute;right:60px;top:56px;width:220px;height:220px;border-radius:50%;background:#ffd84d;
border:6px solid #2b2233;display:flex;flex-direction:column;align-items:center;justify-content:center;transform:rotate(8deg)}
.budget small{font-size:36px}
.budget b{font-size:74px;font-weight:400;line-height:1}
.sparkle{position:absolute;font-size:56px}
.grid{margin:0 28px;display:grid;grid-template-columns:132px repeat(4,1fr);gap:8px}
.ph{height:84px;border:4px solid #2b2233;border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:42px;letter-spacing:-1px}
.rl{border:4px solid #2b2233;border-radius:16px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
.rl b{font-size:84px;font-weight:400;line-height:1}
.rl span{font-size:31px;line-height:1.15;margin-top:6px}
.cell{height:262px;border:4px solid #2b2233;border-radius:16px;display:flex;flex-direction:column;align-items:center;padding:14px 8px 0;text-align:center}
.cell .t{font-size:33px;line-height:1.15;letter-spacing:-1px;min-height:76px;display:flex;align-items:center;white-space:pre-line}
.cell .i{font-size:118px;line-height:1;margin-top:10px;font-family:"Noto Color Emoji",sans-serif}
.foot{margin:26px 28px 0;text-align:center}
.foot span{display:inline-block;background:#2b2233;color:#fff;font-size:46px;padding:16px 40px;border-radius:999px}
.foot em{font-style:normal;color:#ffd84d}
@keyframes pop{0%{opacity:0;transform:scale(.5)}70%{opacity:1;transform:scale(1.08)}100%{opacity:1;transform:scale(1)}}
@keyframes popr{0%{opacity:0;transform:rotate(8deg) scale(.4)}70%{opacity:1;transform:rotate(8deg) scale(1.1)}100%{opacity:1;transform:rotate(8deg) scale(1)}}
@keyframes up{0%{opacity:0;transform:translateY(60px)}100%{opacity:1;transform:translateY(0)}}
@keyframes wob{0%,100%{transform:rotate(-6deg)}50%{transform:rotate(6deg)}}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.06)}}"""

def won(n):
    return f"{int(n):,}원"

head = '<div></div>' + "".join(
    f'<div class="ph" style="background:{HEAD_COLORS[i % 4]}">{won(p)}</div>' for i, p in enumerate(spec["prices"]))
rows = ""
for r, row in enumerate(spec["rows"]):
    strong, soft = ROW_COLORS[r % 4]
    rows += f'<div class="rl" style="background:{strong}"><b>{e(row["key"])}</b><span>{e(row["label"])}</span></div>'
    for text, icon in row["cells"]:
        rows += f'<div class="cell" data-row="{r}" style="background:{soft}"><div class="t">{e(text)}</div><div class="i">{e(icon)}</div></div>'

t1, t2 = spec["title"]
doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<link rel="stylesheet" href="file://{HERE}/fonts/jua/index.css"><style>{CSS}</style></head><body>
<div class="top"><h1>{e(t1)}<br><span class="l2">{e(t2)}</span></h1>
<div class="budget"><small>예산</small><b>{e(spec["budget"])}</b></div>
<div class="sparkle" style="right:290px;top:60px">✨</div><div class="sparkle" style="right:36px;top:40px">⭐</div></div>
<div class="grid">{head}{rows}</div>
<div class="foot"><span>{e(spec["footer"])} <em>👇 댓글로</em></span></div></body></html>"""

JS = """const add=(el,n,d,t,x='')=>{el.style.animation=`${n} ${t}s cubic-bezier(.2,.8,.3,1) ${d}s both${x}`};
add(document.querySelector('h1'),'pop',0.1,0.6);
add(document.querySelector('.budget'),'popr',0.6,0.6);
document.querySelectorAll('.sparkle').forEach((s,i)=>s.style.animation=`wob 1.6s ease-in-out ${i*0.3}s infinite`);
document.querySelectorAll('.ph').forEach((p,i)=>add(p,'pop',1.1+i*0.12,0.45));
const rls=document.querySelectorAll('.rl');
rls.forEach((l,r)=>{const t=1.8+r*1.1;add(l,'up',t,0.45);
 document.querySelectorAll(`.cell[data-row="${r}"]`).forEach((c,j)=>add(c,'pop',t+0.15+j*0.13,0.45));});
const fd=1.8+rls.length*1.1+0.2;const f=document.querySelector('.foot span');
f.style.animation=`pop 0.6s cubic-bezier(.2,.8,.3,1) ${fd}s both, pulse 1.1s ease-in-out ${fd+0.7}s infinite`;
document.getAnimations().forEach(a=>a.pause());"""

FPS, DUR = 30, 12.0
with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as fh:
    fh.write(doc); page_path = fh.name
tmp = out + ".part.mp4"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto("file://" + page_path); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(800)
    bottom = pg.evaluate("document.querySelector('.foot').getBoundingClientRect().bottom")
    if bottom > 1650: sys.exit(f"layout too tall ({bottom:.0f}px > 1650): shorten cell text")
    clipped = pg.evaluate("[...document.querySelectorAll('.cell .t,.ph,.rl span')].filter(x=>x.scrollWidth>x.clientWidth+2).map(x=>x.textContent)")
    if clipped: sys.exit(f"text too wide, shorten: {clipped}")
    pg.evaluate(JS)
    if os.environ.get("PREVIEW"):
        pg.evaluate(f"document.getAnimations().forEach(a=>a.currentTime={float(os.environ['PREVIEW'])*1000})")
        pg.screenshot(path=out, type="jpeg", quality=92); b.close(); print("frame", out); sys.exit(0)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "mjpeg", "-i", "-",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
    for i in range(int(FPS * DUR)):
        pg.evaluate(f"document.getAnimations().forEach(a=>a.currentTime={i * 1000 / FPS})")
        ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
    ff.stdin.close(); rc = ff.wait(); b.close()
os.unlink(page_path)
if rc: sys.exit(rc)
os.replace(tmp, out); print("ok", out)
