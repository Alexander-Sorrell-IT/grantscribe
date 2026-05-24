"""Prove the MCP path: the Slack app's exact calls, but routed THROUGH the
MCP bridge -> MCP server -> tools. If this works, MCP is genuinely load-bearing.
"""
from pathlib import Path

from mcp_bridge import mcp_draft_loi, mcp_find_grants

ORG_REPORT = (Path(__file__).parent / "sample_data" / "org_report.md").read_text()
DESC = (
    "We run a youth refugee tutoring and after-school program in Ohio. "
    "We have no operating funds and need money for staff and supplies."
)


def main() -> None:
    found = mcp_find_grants(DESC, rows=15, top=3)
    print(f"query: {found.get('query')!r} | raw: {found.get('raw_count')} | grants: {len(found.get('grants', []))}")
    for g in found["grants"]:
        print(f"  [{g['score']}] {g['title']} — {g['agency']}")

    if found["grants"]:
        letter = mcp_draft_loi(found["grants"][0], ORG_REPORT)
        print("\nLOI via MCP (first 280 chars):\n" + letter[:280])

    print("\nOK: full flow ran THROUGH the MCP server (find_grants + draft_loi).")


if __name__ == "__main__":
    main()
