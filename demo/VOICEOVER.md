# GrantScribe — Voiceover Read-Script (record your lines to this)

Read these lines straight through, at an even pace. Each block has a **[timecode]** and a tiny
**[on-screen]** cue so you know what the video shows while you speak. `(beat)` = pause ~1s.
Total target ≈ 3:05. Record in one take per block; leave 2s of silence between blocks so the
audio lines up cleanly when it's laid over the screen recording.

> Recording tips: quiet room, mic ~a hand's width away, slightly slower than feels natural.
> Re-read any block you stumble on — keep the best take. Don't worry about exact sync; the
> compositing pass aligns your audio to the on-screen beats.

---

## [0:00–0:15] Hook  · [on-screen: empty Slack channel, cursor blinking]
The U.S. high school class of 2024 left **four-point-four billion dollars** in Pell Grants on the
table — because not applying was easier than applying.
(beat)
GrantScribe inverts that. **You describe what you do. The Letter of Intent appears, in your voice,
ready to submit.**

## [0:15–0:38] /setreport · [on-screen: the modal opens, report pasted]
First, you tell GrantScribe how your organization writes — paste any prior grant report. It stays
in your workspace, private.
Now the agent knows your voice: your cities, your programs, your numbers. The moat isn't a
marketing line — it's a stored file.

## [0:38–1:25] /grants → Draft LOI · [on-screen: /grants typed, 3 cards, click Draft LOI]
A nonprofit serving refugee youth types what they actually do — no grant-writer jargon.
Under the hood: a tight grants.gov query, expired listings dropped, the results re-ranked for
genuine fit — each card shows a score and *why* it fits before you click anything.
One click. The letter is grounded in the report you pasted, and the opportunity number and URL come
verbatim from the live grants.gov API. The function **refuses to return a draft missing the real
identifiers.** Submittable, or it doesn't exist.
(beat)
That's the headline. The blank page was the barrier. **We deleted the blank page.**

## [1:25–2:00] The LOI receipt · [on-screen: terminal — `python verify_loi.py --letter loi.txt --live`]
Every letter ships with a verification receipt — hashes of the live grants.gov payload, the
org-report content, a timestamp.
A funder runs *one command*. It re-fetches the grant from grants.gov, recomputes the hash, and
confirms it matches. **PASS** — without the funder having to trust the sender.
Tamper with the opportunity number, and the hash breaks.
(beat)
This is a new category: **verifiable application infrastructure.**

## [2:00–2:38] /pathway → Draft my plan → second receipt · [on-screen: /pathway, click Draft my plan, then `python verify_pathway.py --plan plan.txt --live`]
And it ships **twice.** There's no free scholarship API — so instead of faking one, GrantScribe built
the route that actually removes the money barrier to a *job.*
`/pathway` takes a goal — *registered nurse* — and maps it to a real occupation, the credential it
needs, and real funded training programs near you. One click drafts the plan, in the student's own
voice, naming a real program it will not misname.
And it carries a **second receipt** — re-checkable, by one command, against the Department of Labor's
training list. **PASS.** A workforce board can fund this enrollment without trusting the applicant.
(beat)
Two receipts, one pattern: draft, then prove.

## [2:38–2:55] The pattern · [on-screen: architecture diagram]
One pattern under everything: take plain language, pull from live free data, draft in the user's
voice — or refuse. Seven commands, one MCP server, two verifiable receipts. Honest tech, honest
claims, honest code.

## [2:55–3:05] Close · [on-screen: GrantScribe logo / channel]
We didn't build another grants chatbot. **We deleted the blank page, and we invented the receipt.**
After this, every application an AI tool submits needs verification metadata — and we built the
first one.
(beat)
Built for the Slack Agent Builder Challenge — *Agent for Good.*
