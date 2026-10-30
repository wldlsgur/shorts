"""Render a balance-game short (1080x1920, 12s, 30fps) from a JSON spec.
Usage: python3 generator/render.py specs/<file>.json out.mp4
Spec: {"tag":"밸런스 게임","title_top":"예산 안에서","title_em":"초능력","title_rest":"골라 담기",
       "budget":"100만원","footer":"내 조합은?","footer_em":"예) 투명2 + 순간1",
       "items":[{"emoji":"🫥","name":"투명인간","levels":[["하루 10초","5"],["하루 1시간","25"],["무제한","60"]]}, ...]}
3~4 items, exactly 3 levels each. Prices are numbers in 만원 (shown as e.g. 25만원; 10000 → 1억원)."""
import json, sys, html, subprocess, os
from playwright.sync_api import sync_playwright

spec = json.load(open(sys.argv[1], encoding="utf-8")); out = sys.argv[2]
e = html.escape
CSS = """*{margin:0;padding:0;box-sizing:border-box}
body{width:1080px;height:1920px;font-family:"Noto Sans CJK KR","Noto Sans CJK JP",sans-serif;
background:linear-gradient(180deg,#22124a 0%,#160c33 100%);color:#fff;overflow:hidden}
.top{padding:44px 48px 0;text-align:center}
.tag{display:inline-block;background:#ff4d4d;font-weight:900;font-size:34px;padding:6px 24px;border-radius:12px;letter-spacing:2px}
h1{font-size:66px;font-weight:900;line-height:1.14;margin-top:12px;letter-spacing:-1px}
h1 em{font-style:normal;color:#ffd84d}
.budget{display:inline-flex;align-items:baseline;gap:14px;margin-top:18px;background:#ffd84d;color:#1a1033;border-radius:22px;padding:4px 40px;font-size:36px;font-weight:900}
.budget b{font-size:62px;letter-spacing:-1px}
.wrap{padding:0 40px}
.list{display:flex;flex-direction:column;gap:14px;margin-top:28px}
.card{background:#fff;color:#1a1033;border-radius:26px;padding:14px 16px 16px}
.title{font-size:44px;font-weight:900;line-height:1.1;margin:0 0 10px 8px;letter-spacing:-1px}
.lvs{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
.lv{border-radius:16px;padding:8px 14px 10px;border:4px solid transparent}
.lv .b{display:inline-block;font-size:24px;font-weight:900;color:#fff;border-radius:8px;padding:1px 10px}
.lv .d{font-size:31px;font-weight:700;line-height:1.25;white-space:nowrap;overflow:hidden;margin-top:4px;color:#2a2440}
.lv .p{font-weight:900;line-height:1;margin-top:6px;letter-spacing:-1px;white-space:nowrap}
.lv .p span{font-size:60px}
.lv .p small{font-size:32px;margin-left:2px;letter-spacing:0}
.l1{background:#eef0f5}.l1 .b{background:#6b7489}.l1 .p{color:#4a5368}
.l2{background:#e7efff}.l2 .b{background:#2f6fe0}.l2 .p{color:#1f5bd0}
.l3{background:#ffe9eb;border-color:#ff9aa5}.l3 .b{background:#e0283c}.l3 .p{color:#d61f33}
.foot{margin-top:26px;text-align:center}
.foot span{display:inline-block;background:#ffd84d;color:#1a1033;font-size:46px;font-weight:900;padding:16px 38px;border-radius:22px}
.foot em{font-style:normal;color:#d61f33}
@keyframes pop{0%{opacity:0;transform:scale(.6)}70%{opacity:1;transform:scale(1.08)}100%{opacity:1;transform:scale(1)}}
@keyframes up{0%{opacity:0;transform:translateY(80px)}100%{opacity:1;transform:translateY(0)}}
@keyframes chip{0%{opacity:0;transform:scale(.4)}70%{transform:scale(1.1)}100%{opacity:1;transform:scale(1)}}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.07)}}"""
def won(p):
    n = int(str(p).replace(",", ""))
    if n >= 10000:
        eok, man = divmod(n, 10000)
        return f'<span>{eok}</span><small>억{(" "+str(man)+"만") if man else ""}원</small>'
    return f'<span>{n:,}</span><small>만원</small>'
LV = ["LV1 약", "LV2 중", "LV3 강"]
cards = "".join(
    f'<div class="card"><div class="title">{e(it["emoji"])} {e(it["name"])}</div><div class="lvs">' +
    "".join(f'<div class="lv l{i+1}"><div class="b">{LV[i]}</div><div class="d">{e(d)}</div><div class="p">{won(p)}</div></div>'
            for i, (d, p) in enumerate(it["levels"])) + "</div></div>"
    for it in spec["items"])
doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="top"><div class="tag">{e(spec.get("tag","밸런스 게임"))}</div>
<h1>{e(spec["title_top"])}<br><em>{e(spec["title_em"])}</em> {e(spec["title_rest"])}</h1>
<div class="budget">예산 <b>{e(spec["budget"])}</b></div></div>
<div class="wrap"><div class="list">{cards}</div>
<div class="foot"><span>{e(spec["footer"])} <em>{e(spec["footer_em"])}</em> 👇</span></div></div></body></html>"""
JS = """const add=(el,n,d,t)=>{el.style.animation=`${n} ${t}s cubic-bezier(.2,.8,.3,1) ${d}s both`};
add(document.querySelector('.tag'),'pop',0.1,0.5);add(document.querySelector('h1'),'pop',0.3,0.6);
add(document.querySelector('.budget'),'pop',0.8,0.6);
const cs=document.querySelectorAll('.card');cs.forEach((c,i)=>{const t=1.4+i*0.9;add(c,'up',t,0.5);
c.querySelectorAll('.lv').forEach((l,j)=>add(l,'chip',t+0.3+j*0.15,0.45));});
const fd=1.4+cs.length*0.9+0.3;const f=document.querySelector('.foot span');
f.style.animation=`pop 0.6s cubic-bezier(.2,.8,.3,1) ${fd}s both, pulse 1s ease-in-out ${fd+0.7}s infinite`;
document.getAnimations().forEach(a=>a.pause());"""
FPS, DUR = 30, 12.0
tmp = out + ".part.mp4"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.set_content(doc); pg.wait_for_timeout(500)
    over = pg.evaluate("document.querySelector('.foot').getBoundingClientRect().bottom") > 1640  # keep clear of the Shorts bottom overlay
    if over: sys.exit("layout overflows 1920px: shorten text or use fewer items")
    pg.evaluate(JS)
    if os.environ.get("PREVIEW"):  # PREVIEW=8 → save one JPEG frame at 8s instead of a video
        pg.evaluate(f"document.getAnimations().forEach(a=>a.currentTime={float(os.environ['PREVIEW'])*1000})")
        pg.screenshot(path=out, type="jpeg", quality=92); b.close(); print("frame", out); sys.exit(0)
    ff = subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","image2pipe","-framerate",str(FPS),"-c:v","mjpeg","-i","-",
        "-c:v","libx264","-preset","veryfast","-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",tmp], stdin=subprocess.PIPE)
    for i in range(int(FPS*DUR)):
        pg.evaluate(f"document.getAnimations().forEach(a=>a.currentTime={i*1000/FPS})")
        ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
    ff.stdin.close(); rc = ff.wait(); b.close()
if rc: sys.exit(rc)
os.replace(tmp, out); print("ok", out)
