"""Test the free-resources pillar against LIVE Internet Archive + DeepSeek."""
from resources import find_resources


def main() -> None:
    goal = "I'm a parent who can't afford tutoring — I want free ways to learn high school algebra"
    result = find_resources(goal)

    print(f"goal  : {goal}")
    print(f"topic : {result['topic']!r}\n")
    print("Free books (Internet Archive, re-ranked for fit):")
    for b in result["books"]:
        print(f"  - {b['title']}  [{b['year']}]")
        print(f"      {b.get('note', '')}")
        print(f"      {b['url']}")
    print("\nFree courses/textbooks (providers):")
    for c in result["courses"]:
        print(f"  - {c['title']}  {c['url']}")

    assert result["topic"]
    assert isinstance(result["books"], list)
    print("\nOK: learning goal -> free books + course providers (live).")


if __name__ == "__main__":
    main()
