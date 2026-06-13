"""Generate the REAL demo artifacts from the live engine, for the video.

Saves /tmp/demo_loi.txt and /tmp/demo_plan.txt (each with its real receipt) and
prints a JSON summary the Slack poster + terminal beats reuse. All live: grants.gov,
CareerOneStop, DeepSeek.
"""
from __future__ import annotations
import json
from pathlib import Path

from grant_intel import find_grants
from loi_drafter import draft_loi
from pathway import build_pathway
from pathway_drafter import draft_pathway_plan

ROOT = Path(__file__).parent.parent
report = (ROOT / "sample_data" / "org_report.md").read_text()

print("→ find_grants (live grants.gov + DeepSeek rerank)…", flush=True)
g = find_grants("youth refugee tutoring in Ohio, after-school literacy, need operating funds", rows=15, top=3)
grant = g["grants"][0]
print(f"  top grant: {grant['opportunity_number']} — {grant['title'][:50]}", flush=True)

print("→ draft_loi (in the org's voice + receipt)…", flush=True)
loi = draft_loi(grant, report)
Path("/tmp/demo_loi.txt").write_text(loi)
print(f"  LOI saved ({len(loi)} chars) → /tmp/demo_loi.txt", flush=True)

print("→ build_pathway (live CareerOneStop)…", flush=True)
p = build_pathway("registered nurse", location="45241", rows=3)
prog = p["programs"][0]
occ = p["occupation"]
goal = f"{occ['title']} (O*NET {occ['onet_code']})" if occ else "Registered Nurse"
print(f"  occupation: {goal} | program: {prog['program'][:40]} @ {prog['school']}", flush=True)

print("→ draft_pathway_plan (in the student's voice + receipt)…", flush=True)
story = ("My name is Marcus. I'm 26, living in Cincinnati. I left community college when my mom got "
         "sick and needed me. I've been doing warehouse work, but I'm good with people and I want "
         "stable healthcare work with a real future. I can start training in the fall.")
plan = draft_pathway_plan(prog, story, goal_occupation=goal)
Path("/tmp/demo_plan.txt").write_text(plan)
print(f"  plan saved ({len(plan)} chars) → /tmp/demo_plan.txt", flush=True)

summary = {
    "grant": grant,
    "grants_all": g["grants"],
    "occupation": occ,
    "credentials": p.get("credentials"),
    "program": prog,
    "programs_all": p["programs"],
}
Path("/tmp/demo_summary.json").write_text(json.dumps(summary, indent=2))
print("→ summary → /tmp/demo_summary.json\nDONE", flush=True)
