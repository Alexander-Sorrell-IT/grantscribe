"""Synchronous MCP client bridge.

The Slack app calls the GrantScribe capabilities THROUGH this bridge, which
talks to the MCP server over streamable-HTTP. That keeps MCP on the live path
(the agent's powers come from the MCP server, not a direct import).

No silent fallbacks: if the MCP server is unreachable or a tool errors, raise.
"""
from __future__ import annotations

import asyncio
import json
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_URL = os.environ.get("GRANTSCRIBE_MCP_URL", "http://localhost:8000/mcp")


async def _call_tool(tool: str, arguments: dict):
    async with streamablehttp_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool, arguments)
            if result.isError:
                detail = _first_text(result) or "unknown MCP error"
                raise RuntimeError(f"MCP tool {tool!r} failed: {detail}")
            return result


def _first_text(result) -> str | None:
    """Safely pull text from the first content block (blocks are a union type)."""
    if result.content:
        return getattr(result.content[0], "text", None)
    return None


def mcp_find_grants(description: str, rows: int = 15, top: int = 3) -> dict:
    result = asyncio.run(_call_tool("find_grants", {"description": description, "rows": rows, "top": top}))
    if result.structuredContent is not None:
        return result.structuredContent
    text = _first_text(result)
    if text:
        return json.loads(text)
    raise RuntimeError("find_grants returned no usable content")


def mcp_draft_loi(grant: dict, org_report: str) -> str:
    result = asyncio.run(_call_tool("draft_loi", {"grant": grant, "org_report": org_report}))
    text = _first_text(result)
    if text:
        return text
    if isinstance(result.structuredContent, dict) and "result" in result.structuredContent:
        return result.structuredContent["result"]
    raise RuntimeError("draft_loi returned no text content")


def mcp_find_resources(description: str, rows: int = 12, top: int = 4) -> dict:
    result = asyncio.run(_call_tool("find_resources", {"description": description, "rows": rows, "top": top}))
    if result.structuredContent is not None:
        return result.structuredContent
    text = _first_text(result)
    if text:
        return json.loads(text)
    raise RuntimeError("find_resources returned no usable content")


def mcp_answer_question(question: str) -> dict:
    result = asyncio.run(_call_tool("answer_question", {"question": question}))
    if result.structuredContent is not None:
        return result.structuredContent
    text = _first_text(result)
    if text:
        return json.loads(text)
    raise RuntimeError("answer_question returned no usable content")
