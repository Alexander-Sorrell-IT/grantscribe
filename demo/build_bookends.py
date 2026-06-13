"""Build intro.html (title) and outro.html (the two live verifications + close),
to bookend the real-Slack recording. Same styling as build_player.py."""
from __future__ import annotations
import html, json
from pathlib import Path

T = Path("/tmp")
vloi = (T / "verify_loi_out.txt").read_text()
vpath = (T / "verify_pathway_out.txt").read_text()

CSS = """*{margin:0;padding:0;box-sizing:border-box}
body{width:1440px;height:900px;background:#1a1d21;font-family:-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;color:#e8e8e8;overflow:hidden}
.scene{position:absolute;inset:0;display:none;padding:54px 80px;opacity:0;transition:opacity .6s}
.scene.on{display:flex;flex-direction:column;justify-content:center;align-items:center;opacity:1}
.logo{font-size:64px;font-weight:800;color:#fff;margin-bottom:28px}
.tag{font-size:42px;line-height:1.35;color:#fff;font-weight:300;text-align:center}
.tag b{font-weight:700;color:#36c5ab}
.sub{margin-top:32px;font-size:22px;color:#9aa0a6;text-align:center}
.caption{font-size:32px;color:#fff;font-weight:300;margin-bottom:24px;text-align:center}
.term{background:#0c0c0c;border-radius:12px;padding:28px 34px;font-family:'SFMono-Regular',Consolas,monospace;font-size:18px;line-height:1.5;color:#d6f5e3;white-space:pre-wrap;text-align:left;width:1180px;height:560px;overflow:hidden;box-shadow:0 0 0 1px #2a2a2a,0 24px 60px rgba(0,0,0,.5)}
.term .pass{color:#36c5ab;font-weight:800}"""

JS = """const scenes=[...document.querySelectorAll('.scene')];
function colorize(t){return t.replace(/PASS/g,'<span class="pass">PASS</span>').replace(/✓/g,'<span class="pass">✓</span>');}
function typeInto(el,text){let i=0;el.innerHTML='';const step=()=>{if(i>=text.length){el.innerHTML=colorize(text);return;}el.textContent=text.slice(0,i);i+=Math.max(3,Math.floor(text.length/200));el.scrollTop=el.scrollHeight;setTimeout(step,16);};step();}
let idx=0;function play(){if(idx>=scenes.length){document.body.setAttribute('data-done','1');return;}
scenes.forEach(s=>s.classList.remove('on'));const s=scenes[idx];s.classList.add('on');
const t=s.querySelector('.term');if(t){typeInto(t,t.id==='t1'?T1:T2);}idx++;setTimeout(play,parseFloat(s.dataset.dur)*1000);}window.__start=play;"""


def page(scenes, data_js=""):
    divs = "".join(f'<section class="scene" data-dur="{d}">{h}</section>' for d, h in scenes)
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{divs}<script>{data_js}{JS}</script></body></html>"


intro = [(7, """<div class="logo">📄 GrantScribe</div>
    <div class="tag">You describe what you do.<br>The Letter of Intent appears — <b>in your voice</b>, ready to submit.</div>
    <div class="sub">A Slack agent that removes the money barrier — grants, and a funded path to a job.</div>""")]

outro = [
    (30, """<div class="caption">The funder verifies the letter — without trusting the sender</div><div class="term" id="t1"></div>"""),
    (22, """<div class="caption">A workforce board verifies the plan — against the U.S. DOL training list</div><div class="term" id="t2"></div>"""),
    (12, """<div class="logo">📄 GrantScribe</div>
    <div class="tag">We deleted the blank page.<br>And we invented <b>the receipt</b> — twice.</div>
    <div class="sub">Two verifiable receipts, one pattern: draft, then prove. · Slack Agent for Good</div>"""),
]

Path(__file__).with_name("intro.html").write_text(page(intro))
data = f"const T1={json.dumps(vloi)},T2={json.dumps(vpath)};"
Path(__file__).with_name("outro.html").write_text(page(outro, data))
print("wrote intro.html (7s) + outro.html (~64s)")
