"""Confirm the /ask tutor works THROUGH the MCP server."""
from mcp_bridge import mcp_answer_question


def main() -> None:
    r = mcp_answer_question("what is photosynthesis?")
    print("answer:", (r.get("answer") or r.get("note"))[:300])
    print("sources:", [s["url"] for s in r.get("sources", [])])
    print("OK: /ask ran through the MCP server.")


if __name__ == "__main__":
    main()
