"""GrantScribe MCP server — exposes the agent's capabilities as MCP tools.

Any MCP client can call these: the GrantScribe Slack app (via mcp_bridge),
Claude, the MCP Inspector, or Slack's own MCP client. This is what makes MCP
load-bearing — the Slack agent's powers are delivered *through* this server.

Run:  uv run --with-requirements requirements.txt python grants_server.py
      (serves streamable-HTTP at http://localhost:8000/mcp)
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from grants_api import _fetch_grants
from grant_intel import find_grants as _find_grants
from loi_drafter import draft_loi as _draft_loi
from resources import find_resources as _find_resources
from ask import answer_question as _answer_question

mcp = FastMCP("grantscribe", json_response=True)


@mcp.tool()
def search_grants(keyword: str, rows: int = 5) -> dict:
    """Raw grants.gov keyword search for open federal opportunities.

    Args:
        keyword: search keywords.
        rows: max opportunities to return (1-25).
    """
    return _fetch_grants(keyword, rows)


@mcp.tool()
def find_grants(description: str, rows: int = 15, top: int = 3) -> dict:
    """Smart grant discovery: a messy plain-language description of what an org
    does -> a tight query -> the few open federal grants that genuinely fit,
    each with a fit score and a one-line reason.

    Args:
        description: what the organization does / needs.
        rows: how many raw grants.gov matches to consider.
        top: how many relevant grants to return.
    """
    return _find_grants(description, rows=rows, top=top)


@mcp.tool()
def draft_loi(grant: dict, org_report: str) -> str:
    """Draft a grant Letter of Intent in the organization's own voice.

    Args:
        grant: a grant dict with at least `title` and `agency`.
        org_report: the org's prior grant report (voice + facts to ground in).
    """
    return _draft_loi(grant, org_report)


@mcp.tool()
def find_resources(description: str, rows: int = 12, top: int = 4) -> dict:
    """Free ways to learn something: real free books (Internet Archive, re-ranked
    for fit) + links to free-course providers (OpenStax/MIT OCW/Khan/freeCodeCamp).
    No application to draft — this surfaces what's free to learn from right now.

    Args:
        description: what the person wants to learn / their situation.
        rows: how many raw candidates to consider.
        top: how many books to return.
    """
    return _find_resources(description, rows=rows, top=top)


@mcp.tool()
def answer_question(question: str) -> dict:
    """Tutor: answer a learning question GROUNDED in free open textbooks
    (Wikibooks/Wikiversity), with citations. No invented facts.

    Args:
        question: the learner's question.

    Returns dict: {question, answer, sources:[{title,site,url}]}.
    """
    return _answer_question(question)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
