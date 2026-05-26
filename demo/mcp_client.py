"""Standalone MCP client — proves the GrantScribe MCP server is portable.

This script does NOT import from grantscribe. It is a generic MCP client that talks
to whatever MCP server is running at $GRANTSCRIBE_MCP_URL (defaults to
http://localhost:8000/mcp) and invokes the same four tools the Slack app uses
(find_grants, draft_loi, find_resources, answer_question).

If this runs successfully against the running grants_server.py, MCP is genuinely
load-bearing: any MCP-compliant client (Claude desktop, MCP Inspector, this CLI)
can reuse the same tools unchanged.

Usage:
  python demo/mcp_client.py list
  python demo/mcp_client.py find-grants "youth refugee tutoring Ohio"
  python demo/mcp_client.py ask "what is photosynthesis?"
  python demo/mcp_client.py learn "free ways to learn high school algebra"
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_URL = os.environ.get("GRANTSCRIBE_MCP_URL", "http://localhost:8000/mcp")


def _first_text(result: Any) -> str:
    for chunk in getattr(result, "content", []) or []:
        text = getattr(chunk, "text", None)
        if text:
            return text
    return ""


async def _call(tool: str, arguments: dict) -> Any:
    async with streamablehttp_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool, arguments)
            if result.isError:
                raise RuntimeError(f"MCP tool {tool!r} failed: {_first_text(result) or 'unknown'}")
            payload = _first_text(result)
            try:
                return json.loads(payload)
            except json.JSONDecodeError:
                return payload


async def _list() -> list[str]:
    async with streamablehttp_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            return [t.name for t in tools.tools]


def cmd_list(_: argparse.Namespace) -> None:
    names = asyncio.run(_list())
    print(f"Tools advertised by {MCP_URL}:")
    for name in names:
        print(f"  - {name}")


def cmd_find_grants(args: argparse.Namespace) -> None:
    out = asyncio.run(_call("find_grants", {"description": args.description, "rows": 15, "top": 3}))
    print(f"query: {out['query']!r}  |  raw {out['raw_count']}  ->  ranked {len(out['grants'])}")
    for g in out["grants"]:
        print(f"\n  [{g['score']}] {g['title']} — {g['agency']}")
        print(f"      RE: {g['opportunity_number']}  •  due {g['close_date'] or 'rolling'}")
        print(f"      why: {g['reason']}")
        print(f"      url: {g['url']}")


def cmd_ask(args: argparse.Namespace) -> None:
    out = asyncio.run(_call("answer_question", {"question": args.question}))
    print((out.get("answer") or out.get("note") or "")[:1200])
    if out.get("sources"):
        print("\nSources (open textbooks):")
        for s in out["sources"]:
            print(f"  - {s['site']}: {s['title']} → {s['url']}")


def cmd_learn(args: argparse.Namespace) -> None:
    out = asyncio.run(_call("find_resources", {"goal": args.goal}))
    print(f"topic: {out['topic']!r}  |  books: {len(out['books'])}  |  courses: {len(out['courses'])}")
    for b in out["books"][:5]:
        print(f"  - {b['title']} — {b.get('note', '')}")
        print(f"      {b['url']}")
    print()
    for c in out["courses"][:5]:
        print(f"  - {c['title']} — {c['url']}")


def main() -> None:
    p = argparse.ArgumentParser(description="Standalone MCP client for the GrantScribe MCP server.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List tools exposed by the MCP server")

    g = sub.add_parser("find-grants", help="Find ranked grants for a plain-language description")
    g.add_argument("description")
    g.set_defaults(func=cmd_find_grants)

    a = sub.add_parser("ask", help="Ask a tutor question, answered from open textbooks")
    a.add_argument("question")
    a.set_defaults(func=cmd_ask)

    l = sub.add_parser("learn", help="Find free learning resources for a goal")
    l.add_argument("goal")
    l.set_defaults(func=cmd_learn)

    args = p.parse_args()
    if args.cmd == "list":
        cmd_list(args)
    else:
        args.func(args)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
