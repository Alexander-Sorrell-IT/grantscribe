"""Education-to-employment pathway.

A messy goal job ("i want to be a nurse") ->
  1. is it a real occupation? (CareerOneStop Occupation search -> canonical title + O*NET)
  2. what credential do you need? (the awards the real training programs grant)
  3. where do you get it? (real, enrollable training programs near you)

Composes two CareerOneStop services that are independently verified live
(Occupation search + Training Finder). No silent fallbacks; honest empty states.
"""
from __future__ import annotations

from occupation_api import find_occupations
from training_api import find_training


def build_pathway(goal: str, location: str = "0", rows: int = 4) -> dict:
    """Map a goal job to: the real occupation, the credential, and local programs.

    Args:
        goal: the job/career to aim for (e.g. "registered nurse", "electrician").
        location: ZIP or "City, ST" to search programs near; "0" for nationwide.
        rows: how many programs to return (1-20).

    Raises on missing creds or any API/network failure.
    """
    if not goal or not goal.strip():
        raise ValueError("goal must be a non-empty job/career to aim for")
    goal = goal.strip()

    occ = find_occupations(goal, rows=1)
    occupation = occ["occupations"][0] if occ["occupations"] else None

    train = find_training(goal, location=location, rows=rows)
    programs = train["programs"]

    # The credentials these real programs grant ARE the education you need.
    credentials: list[str] = []
    for p in programs:
        cred = p["credential"] or p["award_level"]
        if cred and "no data" not in cred.lower() and cred not in credentials:
            credentials.append(cred)

    return {
        "goal": goal,
        "occupation": occupation,          # {title, onet_code} or None
        "occupation_matches": occ["count"],
        "credentials": credentials,        # distinct, in program order
        "programs": programs,
        "program_count": train["count"],
        "location": location,
        "source": "U.S. DOL CareerOneStop",
    }
