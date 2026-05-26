"""Full pipeline demo: messy description + org report -> top grant -> LOI in org voice."""
from pathlib import Path

from grant_intel import find_grants
from loi_drafter import draft_loi

REPORT = (Path(__file__).parent / "sample_data" / "org_report.md").read_text()

DESCRIPTION = (
    "We run a youth refugee tutoring and after-school program in Ohio. "
    "We have no operating funds and need money for staff and supplies."
)


def main() -> None:
    found = find_grants(DESCRIPTION, rows=15, top=3)
    if not found["grants"]:
        raise SystemExit("No relevant grants found to draft for.")
    grant = found["grants"][0]

    print(f"Top grant : {grant['title']}  ({grant['agency']})")
    print(f"Why       : {grant['reason']}\n")
    print("Drafting LOI in the org's voice...\n")

    letter = draft_loi(grant, REPORT)
    print("=" * 72)
    print(letter)
    print("=" * 72)

    # Submittability checks: the LOI must carry the grant's identifiers verbatim,
    # straight from grants.gov, so a small nonprofit can submit it without manual lookup.
    assert grant["opportunity_number"] in letter, "LOI missing opportunity number"
    assert grant["url"] in letter, "LOI missing grants.gov URL"
    if grant.get("close_date"):
        assert grant["close_date"] in letter, "LOI missing submission deadline"

    print(
        "\nOK: full pipeline — messy description -> relevant grant -> "
        "submittable LOI in org voice (opportunity number, URL, and deadline present)."
    )


if __name__ == "__main__":
    main()
