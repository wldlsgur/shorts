"""Render a "100억 준다면 어디까지 할래?" ladder short (1080x1920, 12s, 30fps) from a JSON spec.

Usage:
  python3 generator/render_100eok.py specs/<file>.json out.mp4
  PREVIEW=10 python3 generator/render_100eok.py specs/<file>.json frame.jpg   # one still at 10s

Format: 8 conditions stacked as 1단계~8단계, getting worse step by step. Viewer accepts the
money only up to the step they can stand ("몇 단계까지 OK?" → comments).
Conditions are imaginary curses on everyday life that everyone can relate to
(e.g. 평생 와이파이 1칸, 양말 한 짝씩 실종, 모든 음식 민트초코 맛).

Spec:
{
  "kind": "100eok",
  "title": ["100억 준다면", "어디까지 할래?"],   # 2 short lines
  "prize": "100억",
  "items": [["평생 양말 한 짝씩 실종", "🧦"], ... 8 items, mild -> brutal],
  "footer": "몇 단계까지 OK?",
  "youtube_title": "..."
}
Item text: one line, about 14 Korean characters max. One emoji per item.
"""
import json, sys, html, subprocess, os, tempfile
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
spec = json.load(open(sys.argv[1], encoding="utf-8")); out = sys.argv[2]
e = html.escape
items = spec["items"]
if len(items) != 8: sys.exit(f"need exactly 8 items, got {len(items)}")

# mild (green) -> brutal (red)
STEP = ["#d8f5d0", "#e6f5c8", "#f3f2bf", "#fde9b0", "#ffdca6", "#ffcaa0", "#ffb5a0", "#ff9d9d"]
TAG = ["#5fbf4a", "#86c13d", "#b8b431", "#e0a72a", "#ee8c2a", "#f0702e", "#e95238", "#d63a3a"]

CSS = """*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;font-family:"Jua","Noto Sans CJK KR",sans-serif;color:#2b2233;overflow:hidden;
background:#fffaf2;background-image:radial-gradient(#f1e6d6 2px,transparent 2.5px);background-size:36px 36px}
.top{position:relative;padding:64px 56px 0;height:300px}
h1{font-size:92px;line-height:1.08;font-weight:400;letter-spacing:-1px}
h1 .l2{color:#ff5a76}
.prize{position:absolute;right:52px;top:48px;width:230px;height:230px;border-radius:50%;background:#ffd84d;
border:6px solid #2b2233;display:flex;flex-direction:column;align-items:center;justify-content:center;transform:rotate(8deg)}
.prize small{font-size:66px;line-height:1}
.prize b{font-size:70px;font-weight:400;line-height:1.05}
.sparkle{position:absolute;font-size:56px}
.list{margin:0 36px;display:flex;flex-direction:column;gap:12px}
.it{height:128px;border:4px solid #2b2233;border-radius:22px;display:flex;align-items:center;padding:0 22px 0 14px}
.it .n{flex:none;width:150px;height:92px;border-radius:16px;border:4px solid #2b2233;color:#fff;font-size:44px;
display:flex;align-items:center;justify-content:center;-webkit-text-stroke:1.5px #2b2233}
.it .t{flex:1;min-width:0;font-size:46px;letter-spacing:-1px;margin:0 14px 0 22px;white-space:nowrap;overflow:hidden}
.it .i{flex:none;font-size:84px;line-height:1;font-family:"Noto Color Emoji",sans-serif}
.foot{margin:26px 28px 0;text-align:center}
.foot span{display:inline-block;background:#2b2233;color:#fff;font-size:50px;padding:16px 44px;border-radius:999px}
.foot em{font-style:normal;color:#ffd84d}
@keyframes pop{0%{opacity:0;transform:scale(.5)}70%{opacity:1;transform:scale(1.08)}100%{opacity:1;transform:scale(1)}}
@keyframes popr{0%{opacity:0;transform:rotate(8deg) scale(.4)}70%{opacity:1;transform:rotate(8deg) scale(1.1)}100%{opacity:1;transform:rotate(8deg) scale(1)}}
@keyframes slide{0%{opacity:0;transform:translateX(-120px)}100%{opacity:1;transform:translateX(0)}}
@keyframes wob{0%,100%{transform:rotate(-6deg)}50%{transform:rotate(6deg)}}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.06)}}
@keyframes shake{0%,100%{transform:translateX(0)}25%{transform:translateX(-6px)}75%{transform:translateX(6px)}}"""

rows = "".join(
    f'<div class="it" style="background:{STEP[i]}"><div class="n" style="background:{TAG[i]}">{i+1}단계</div>'
    f'<div class="t">{e(t)}</div><div class="i">{e(ic)}</div></div>' for i, (t, ic) in enumerate(items))
t1, t2 = spec["title"]
doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<link rel="stylesheet" href="file://{HERE}/fonts/jua/index.css"><style>{CSS}</style></head><body>
<div class="top"><h1>{e(t1)}<br><span class="l2">{e(t2)}</span></h1>
<div class="prize"><small>💰</small><b>{e(spec["prize"])}</b></div>
<div class="sparkle" style="right:300px;top:40px">✨</div><div class="sparkle" style="right:24px;top:24px">⭐</div></div>
<div class="list">{rows}</div>
<div class="foot"><span>{e(spec["footer"])} <em>👇 댓글로</em></span></div></body></html>"""

JS = """const add=(el,n,d,t,x='')=>{el.style.animation=`${n} ${t}s cubic-bezier(.2,.8,.3,1) ${d}s both${x}`};
add(document.querySelector('h1'),'pop',0.1,0.6);
add(document.querySelector('.prize'),'popr',0.6,0.6);
document.querySelectorAll('.sparkle').forEach((s,i)=>s.style.animation=`wob 1.6s ease-in-out ${i*0.3}s infinite`);
const its=document.querySelectorAll('.it');
its.forEach((el,i)=>{const t=1.3+i*0.95;
 if(i>=6) el.style.animation=`slide .45s cubic-bezier(.2,.8,.3,1) ${t}s both, shake .25s linear ${t+0.45}s 3`;
 else add(el,'slide',t,0.45);});
const fd=1.3+its.length*0.95+0.2;const f=document.querySelector('.foot span');
f.style.animation=`pop 0.6s cubic-bezier(.2,.8,.3,1) ${fd}s both, pulse 1.1s ease-in-out ${fd+0.7}s infinite`;
document.getAnimations().forEach(a=>a.pause());"""

FPS, DUR = 30, 12.0
with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as fh:
    fh.write(doc); page_path = fh.name
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
tmp = out + ".part.mp4"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto("file://" + page_path); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(800)
    bottom = pg.evaluate("document.querySelector('.foot').getBoundingClientRect().bottom")
    if bottom > 1650: sys.exit(f"layout too tall ({bottom:.0f}px > 1650)")
    clipped = pg.evaluate("[...document.querySelectorAll('.it .t,h1')].filter(x=>x.scrollWidth>x.clientWidth+2).map(x=>x.textContent)")
    if clipped: sys.exit(f"text too wide, shorten: {clipped}")
    title_hit = pg.evaluate("(()=>{const h=document.querySelector('h1').getBoundingClientRect(),p=document.querySelector('.prize').getBoundingClientRect();"
                           "return [...document.querySelectorAll('h1')].some(()=>{const r=document.createRange();r.selectNodeContents(document.querySelector('h1'));"
                           "return [...r.getClientRects()].some(c=>c.right>p.left-10&&c.top<p.bottom)})})()")
    if title_hit: sys.exit("title overlaps the prize badge: shorten title")
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
