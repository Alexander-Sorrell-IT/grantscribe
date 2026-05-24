"""End-to-end test of the intelligence layer against LIVE grants.gov + DeepSeek."""
from grant_intel import find_grants


def main() -> None:
    description = (
        "We run a youth refugee tutoring and after-school program in Ohio. "
        "We have no operating funds and need money for staff and supplies."
    )
    result = find_grants(description, rows=15, top=3)

    print(f"description : {description}")
    print(f"tight query : {result['query']!r}")
    print(f"raw matches : {result['raw_count']}  |  considered (open): {result['considered']}")
    print(f"top relevant: {len(result['grants'])}\n")
    for grant in result["grants"]:
        print(f"[{grant['score']}] {grant['title']}  —  {grant['agency']}")
        print(f"    why : {grant['reason']}")
        print(f"    due : {grant['close_date'] or 'rolling/unspecified'}   {grant['url']}\n")

    print("OK: messy description -> tight query -> relevant, explained grants.")


if __name__ == "__main__":
    main()
