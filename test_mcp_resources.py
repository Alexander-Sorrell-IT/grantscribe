"""Confirm the free-resources pillar works THROUGH the MCP server."""
from mcp_bridge import mcp_find_resources


def main() -> None:
    result = mcp_find_resources("free ways to learn high school algebra")
    print(f"topic: {result['topic']!r} | books: {len(result['books'])} | courses: {len(result['courses'])}")
    for b in result["books"][:3]:
        print(f"  - {b['title']} — {b.get('note', '')}")
    print("OK: free-resources ran through the MCP server.")


if __name__ == "__main__":
    main()
