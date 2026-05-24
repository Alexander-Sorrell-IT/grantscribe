"""Smoke test: hit the LIVE grants.gov API through the server's core function."""
import json

from grants_api import _fetch_grants


def main() -> None:
    query = "youth refugee tutoring Ohio operating funds"
    result = _fetch_grants(query, rows=3)

    print(f"query   : {query!r}")
    print(f"count   : {result['count']}")
    for grant in result["grants"]:
        print(json.dumps(grant, indent=2))

    assert isinstance(result["count"], int)
    assert isinstance(result["grants"], list)
    for grant in result["grants"]:
        assert grant["title"], "grant missing title"
        assert grant["url"].startswith("https://"), "grant missing url"
    print("\nOK: live grants.gov fetch + parse succeeded.")


if __name__ == "__main__":
    main()
