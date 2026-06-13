"""Build demo/player.html — a self-contained, timed demo of GrantScribe's REAL output.

All content is real: real grants.gov results, the real LOI + plan (in-voice), and the
two receipts re-verifying LIVE (verify_loi.py / verify_pathway.py output verbatim).
record_player.py loads this and records it to video.
"""
from __future__ import annotations
import html
import json
from pathlib import Path

T = Path("/tmp")
summary = json.loads((T / "demo_summary.json").read_text())
loi = (T / "demo_loi.txt").read_text()
plan = (T / "demo_plan.txt").read_text()
vloi = (T / "verify_loi_out.txt").read_text()
vpath = (T / "verify_pathway_out.txt").read_text()


def esc(s: str) -> str:
    return html.escape(s)


def split_receipt(doc: str, marker: str):
    if marker in doc:
        body, _, rec = doc.partition(marker)
        return body.strip(), (marker + rec).strip()
    return doc.strip(), ""


loi_body, loi_rec = split_receipt(loi, "--- BEGIN GRANTSCRIBE RECEIPT ---")
plan_body, plan_rec = split_receipt(plan, "--- BEGIN GRANTSCRIBE PATHWAY RECEIPT ---")

grant_cards = "".join(
    f"""<div class="card"><div class="ct"><a>{esc(g['title'])}</a></div>
    <div class="cm">{esc(g['agency'])} &nbsp;•&nbsp; due <b>{esc(g.get('close_date') or 'rolling')}</b> &nbsp;•&nbsp; fit <b>{g['score']}/100</b></div>
    <div class="cr">▸ {esc(g['reason'])}</div>
    <div class="cb">✍️ Draft LOI</div></div>"""
    for g in summary["grants_all"]
)

occ = summary.get("occupation") or {}
occ_line = f"{esc(occ.get('title',''))} (O*NET {esc(occ.get('onet_code',''))})" if occ else "—"
creds = ", ".join(summary.get("credentials") or []) or "varies"
prog_cards = "".join(
    f"""<div class="card"><div class="ct">{esc(p['program'] or 'Program')}</div>
    <div class="cm">{esc(p['credential'] or p['award_level'] or 'credential varies')} &nbsp;•&nbsp; {esc(p['format'])} &nbsp;•&nbsp; {esc(', '.join(x for x in (p['city'],p['state']) if x))}</div>
    <div class="cb">📝 Draft my plan</div></div>"""
    for p in summary["programs_all"]
)

SCENES = [
    # (seconds, html) — durations aligned to demo/VOICEOVER.md beats (~3:05 total)
    (15, f"""<div class="title"><div class="logo">📄 GrantScribe</div>
        <div class="tag">You describe what you do.<br>The Letter of Intent appears — <b>in your voice</b>, ready to submit.</div>
        <div class="sub">A Slack agent for the people who can't afford the grant-writer, the college counselor, the tutor.</div></div>"""),
    (18, f"""<div class="slack"><div class="hd"># general</div>
        <div class="usr">🧑 <b>/setreport</b></div>
        <div class="bot"><b>GrantScribe</b> · saved your org report. Now I know your voice — your cities, programs, student counts, partners.<br><span class="dim">The moat isn't a marketing line. It's a stored file.</span></div></div>"""),
    (22, f"""<div class="slack"><div class="hd"># general</div>
        <div class="usr">🧑 <b>/grants</b> youth refugee tutoring in Ohio, need operating funds</div>
        <div class="bot"><b>GrantScribe</b> · 🎯 grants that fit — narrowed from hundreds of live grants.gov matches:</div>
        {grant_cards}</div>"""),
    (25, f"""<div class="slack"><div class="hd">Letter of Intent — in your org's voice</div>
        <div class="doc">{esc(loi_body)}</div>
        <div class="note">↑ opportunity number, agency, URL & deadline copied <b>verbatim from live grants.gov</b>. The drafter <b>refuses</b> to return a letter missing them.</div></div>"""),
    (30, f"""<div class="termwrap"><div class="caption">The funder verifies it — without trusting the sender</div>
        <div class="term" id="t1"></div></div>"""),
    (22, f"""<div class="slack"><div class="hd"># general</div>
        <div class="usr">🧑 <b>/pathway</b> registered nurse near 45241</div>
        <div class="bot"><b>GrantScribe</b> · 🎯 <b>{occ_line}</b> — a real occupation<br>🎓 credential you need: <b>{esc(creds)}</b><br>🏫 real funded programs near you:</div>
        {prog_cards}</div>"""),
    (26, f"""<div class="slack"><div class="hd">Funded-path plan — in the student's voice</div>
        <div class="doc">{esc(plan_body)}</div>
        <div class="note">↑ names a <b>real ETPL program</b> verbatim, grounded in the student's own story.</div></div>"""),
    (20, f"""<div class="termwrap"><div class="caption">A workforce board verifies it against the U.S. DOL training list</div>
        <div class="term" id="t2"></div></div>"""),
    (12, f"""<div class="title"><div class="logo">📄 GrantScribe</div>
        <div class="tag">We deleted the blank page.<br>And we invented <b>the receipt</b> — twice.</div>
        <div class="sub">Two verifiable receipts, one pattern: draft, then prove. · Slack Agent for Good</div></div>"""),
]

scene_divs = "".join(f'<section class="scene" data-dur="{d}">{h}</section>' for d, h in SCENES)

HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:1440px;height:900px;background:#1a1d21;font-family:-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;color:#e8e8e8;overflow:hidden}}
.scene{{position:absolute;inset:0;display:none;padding:54px 80px;opacity:0;transition:opacity .6s}}
.scene.on{{display:flex;flex-direction:column;justify-content:center;opacity:1}}
.title{{text-align:center;align-items:center;display:flex;flex-direction:column;justify-content:center;height:100%}}
.logo{{font-size:62px;font-weight:800;color:#fff;margin-bottom:30px}}
.tag{{font-size:40px;line-height:1.35;color:#fff;font-weight:300}}
.tag b{{font-weight:700;color:#36c5ab}}
.sub{{margin-top:34px;font-size:21px;color:#9aa0a6}}
.slack{{background:#fff;color:#1d1c1d;border-radius:14px;padding:26px 30px;max-height:792px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.4)}}
.hd{{font-size:22px;font-weight:800;border-bottom:1px solid #eee;padding-bottom:14px;margin-bottom:18px;color:#1d1c1d}}
.usr{{font-size:21px;margin:10px 0 16px;color:#1d1c1d}}
.usr b{{color:#1264a3}}
.bot{{font-size:20px;line-height:1.5;background:#f6f8fa;border-left:4px solid #36c5ab;padding:14px 18px;border-radius:8px;margin-bottom:14px}}
.dim{{color:#616061;font-size:18px}}
.card{{border:1px solid #e3e6ea;border-radius:10px;padding:14px 18px;margin:10px 0}}
.ct a{{color:#1264a3;font-weight:700;font-size:20px}} .ct{{font-size:20px;font-weight:700}}
.cm{{color:#616061;font-size:17px;margin:5px 0}} .cr{{font-size:18px;color:#1d1c1d;margin:6px 0}}
.cb{{display:inline-block;margin-top:8px;background:#007a5a;color:#fff;font-weight:700;font-size:16px;padding:8px 16px;border-radius:6px}}
.doc{{white-space:pre-wrap;font-size:17px;line-height:1.5;color:#1d1c1d;max-height:640px;overflow:hidden;font-family:Georgia,serif}}
.note{{margin-top:16px;font-size:17px;color:#616061;border-top:1px dashed #ddd;padding-top:12px}}
.termwrap{{align-items:center;text-align:center}}
.caption{{font-size:30px;color:#fff;font-weight:300;margin-bottom:24px}}
.term{{background:#0c0c0c;border-radius:12px;padding:28px 34px;font-family:'SFMono-Regular',Consolas,monospace;font-size:18px;line-height:1.5;color:#d6f5e3;white-space:pre-wrap;text-align:left;width:1180px;height:560px;overflow:hidden;box-shadow:0 0 0 1px #2a2a2a,0 24px 60px rgba(0,0,0,.5)}}
.term .pass{{color:#36c5ab;font-weight:800}}
</style></head><body>{scene_divs}
<script>
const T1={json.dumps(vloi)}, T2={json.dumps(vpath)};
const scenes=[...document.querySelectorAll('.scene')];
function colorize(t){{return t.replace(/PASS/g,'<span class="pass">PASS</span>').replace(/✓/g,'<span class="pass">✓</span>');}}
function typeInto(el,text,cb){{let i=0;el.innerHTML='';const step=()=>{{if(i>=text.length){{el.innerHTML=colorize(text);cb&&cb();return;}}el.textContent=text.slice(0,i);i+=Math.max(3,Math.floor(text.length/220));el.scrollTop=el.scrollHeight;setTimeout(step,16);}};step();}}
let idx=0;
function play(){{
  if(idx>=scenes.length){{document.body.setAttribute('data-done','1');return;}}
  scenes.forEach(s=>s.classList.remove('on'));
  const s=scenes[idx]; s.classList.add('on');
  const dur=parseFloat(s.dataset.dur)*1000;
  const term=s.querySelector('.term');
  if(term){{const txt=term.id==='t1'?T1:T2; typeInto(term,txt);}}
  idx++; setTimeout(play,dur);
}}
window.__start=play;
</script></body></html>"""

OUT = Path(__file__).with_name("player.html")
OUT.write_text(HTML)
print(f"wrote {OUT} ({len(HTML)} bytes); total scenes={len(SCENES)}; duration≈{sum(d for d,_ in SCENES)}s")
