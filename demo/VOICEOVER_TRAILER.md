# GrantScribe — Trailer voiceover (fits the 150s real-footage cut)

Five blocks, each timed to a slot in `GrantScribe_trailer_REAL_silent.mp4`
(intro 0:00–0:09 · real Slack 0:09–1:24 · verify_loi 1:24–1:55 · verify_pathway 1:55–2:18 · close 2:18–2:30).
`synth_trailer_vo.py` synthesizes each block in the cloned voice, pads it to its slot,
and concatenates — so every beat lands on what's on screen. Total: 2:30.

## Block 1 · 0:00–0:14 · [intro card → Slack fades in]
The U.S. high school class of 2024 left four point four billion dollars in Pell Grants
on the table — because not applying was easier than applying. GrantScribe inverts that.

## Block 2 · 0:14–1:24 · [real Slack: LOI + receipt, then pathway plan + receipt]
You describe what you do — and the Letter of Intent appears, in your voice, ready to submit.
First, you paste any prior grant report. It stays in your workspace, private. Now the agent
knows your voice — your cities, your programs, your numbers.
Type what you actually do — no grant-writer jargon. The letter is grounded in your report,
and the opportunity number, URL, and deadline come verbatim from the live grants dot gov API.
The function refuses to return a draft missing the real identifiers. Submittable, or it
doesn't exist.
And there is no free scholarship API — so instead of faking one, GrantScribe builds the route
that removes the money barrier to a job. Pathway takes a goal — registered nurse — and maps it
to a real occupation, the credential it needs, and real funded training near you, drafted in
the student's own voice.
The blank page was the barrier. We deleted the blank page.

## Block 3 · 1:24–1:55 · [terminal: verify_loi.py → PASS]
Every letter ships with a verification receipt — hashes of the live grants dot gov payload,
the org report, a timestamp. The funder runs one command. It re-fetches the grant, recomputes
the hash, and confirms the match. PASS — without the funder having to trust the sender.
Tamper with the opportunity number, and the hash breaks. This is a new category: verifiable
application infrastructure.

## Block 4 · 1:55–2:18 · [terminal: verify_pathway.py → PASS]
And it ships twice. The plan carries a second receipt — re-checked, with one command, against
the Department of Labor's live training list. PASS. A workforce board can fund this enrollment
without trusting the applicant. Two receipts, one pattern: draft, then prove.

## Block 5 · 2:18–2:30 · [close card]
We didn't build another grants chatbot. We deleted the blank page, and we invented the
receipt — twice. Built for the Slack Agent Builder Challenge: Agent for Good.
