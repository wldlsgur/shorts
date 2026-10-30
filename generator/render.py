"""Render a balance-game short (1080x1920, 12s, 30fps) from a JSON spec.
Usage: python3 generator/render.py specs/<file>.json out.mp4
Spec: {"tag":"밸런스 게임","title_top":"예산 안에서","title_em":"초능력","title_rest":"골라 담기",
       "budget":"100만원","footer":"내 조합은?","footer_em":"예) 투명2 + 순간1",
       "items":[{"emoji":"🫥","name":"투명인간","levels":[["하루 10초","5"],["하루 1시간","25"],["무제한","60"]]}, ...]}
3~4 items, exactly 3 levels each. Prices are numbers in 만원 (shown as e.g. 25만)."""
import json, sys, html, subprocess, os
from playwright.sync_api import sync_playwright

spec = json.load(open(sys.argv[1], encoding="utf-8")); out = sys.argv[2]
e = html.escape
CSS = """*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;font-family:"Noto Sans CJK KR","Noto Sans CJK JP",sans-serif;
background:radial-gradient(120% 70% at 50% 0%,#3b1670 0%,#1a0b3a 60%,#120828 100%);color:#fff;overflow:hidden}
.top{padding:60px 50px 0;text-align:center}
.tag{display:inline-block;background:#ff4d4d;font-weight:900;font-size:36px;padding:6px 26px;border-radius:12px}
h1{font-size:68px;font-weight:900;line-height:1.18;margin-top:16px}
h1 em{font-style:normal;color:#ffd84d}
.budget{display:inline-block;margin-top:22px;background:#ffd84d;color:#111;border-radius:20px;padding:6px 40px;font-size:38px;font-weight:900}
.budget b{font-size:60px}
.wrap{padding:0 50px}
.legend{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:28px 0 12px;padding:0 20px;text-align:center;font-size:30px;font-weight:900}
.legend div{border-radius:999px;padding:4px 0}
.list{display:flex;flex-direction:column;gap:18px}
.card{background:#fff;color:#111;border-radius:26px;padding:16px 20px 20px}
.title{font-size:46px;font-weight:900;line-height:1.15;margin:0 0 12px 4px}
.lvs{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.lv{border-radius:16px;padding:12px 16px;color:#fff}
.lv .d{font-size:30px;font-weight:700;line-height:1.25;white-space:nowrap;overflow:hidden}
.lv .p{font-size:52px;font-weight:900;line-height:1.1;margin-top:4px}
.lv .p small{font-size:30px}
.l1{background:#5c6b80}.l2{background:#2f6fe0}.l3{background:#d62839}
.foot{margin-top:28px;text-align:center}
.foot span{display:inline-block;background:#fff;color:#111;font-size:46px;font-weight:900;padding:14px 36px;border-radius:20px}
.foot em{font-style:normal;color:#d62839}
@keyframes pop{0%{opacity:0;transform:scale(.6)}70%{opacity:1;transform:scale(1.08)}100%{opacity:1;transform:scale(1)}}
@keyframes up{0%{opacity:0;transform:translateY(80px)}100%{opacity:1;transform:translateY(0)}}
@keyframes chip{0%{opacity:0;transform:scale(.4)}70%{transform:scale(1.1)}100%{opacity:1;transform:scale(1)}}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.07)}}"""
cards = "".join(
    f'<div class="card"><div class="title">{e(it["emoji"])} {e(it["name"])}</div><div class="lvs">' +
    "".join(f'<div class="lv l{i+1}"><div class="d">{e(d)}</div><div class="p">{e(str(p))}<small>만</small></div></div>'
            for i, (d, p) in enumerate(it["levels"])) + "</div></div>"
    for it in spec["items"])
doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="top"><div class="tag">{e(spec.get("tag","밸런스 게임"))}</div>
<h1>{e(spec["title_top"])}<br><em>{e(spec["title_em"])}</em> {e(spec["title_rest"])}</h1>
<div class="budget">예산 <b>{e(spec["budget"])}</b></div></div>
<div class="wrap"><div class="legend"><div class="l1">LV1 약</div><div class="l2">LV2 중</div><div class="l3">LV3 강</div></div>
<div class="list">{cards}</div>
<div class="foot"><span>{e(spec["footer"])} <em>{e(spec["footer_em"])}</em> 👇</span></div></div></body></html>"""
JS = """const add=(el,n,d,t)=>{el.style.animation=`${n} ${t}s cubic-bezier(.2,.8,.3,1) ${d}s both`};
add(document.querySelector('.tag'),'pop',0.1,0.5);add(document.querySelector('h1'),'pop',0.3,0.6);
add(document.querySelector('.budget'),'pop',0.8,0.6);
document.querySelectorAll('.legend div').forEach((l,j)=>add(l,'chip',1.2+j*0.1,0.4));
const cs=document.querySelectorAll('.card');cs.forEach((c,i)=>{const t=1.7+i*0.9;add(c,'up',t,0.5);
c.querySelectorAll('.lv').forEach((l,j)=>add(l,'chip',t+0.3+j*0.15,0.45));});
const fd=1.7+cs.length*0.9+0.3;const f=document.querySelector('.foot span');
f.style.animation=`pop 0.6s cubic-bezier(.2,.8,.3,1) ${fd}s both, pulse 1s ease-in-out ${fd+0.7}s infinite`;
document.getAnimations().forEach(a=>a.pause());"""
FPS, DUR = 30, 12.0
tmp = out + ".part.mp4"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.set_content(doc); pg.wait_for_timeout(500)
    over = pg.evaluate("document.body.scrollHeight") > 1920
    if over: sys.exit("layout overflows 1920px: shorten text or use fewer items")
    pg.evaluate(JS)
    ff = subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","image2pipe","-framerate",str(FPS),"-c:v","mjpeg","-i","-",
        "-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",tmp], stdin=subprocess.PIPE)
    for i in range(int(FPS*DUR)):
        pg.evaluate(f"document.getAnimations().forEach(a=>a.currentTime={i*1000/FPS})")
        ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
    ff.stdin.close(); rc = ff.wait(); b.close()
if rc: sys.exit(rc)
os.replace(tmp, out); print("ok", out)
