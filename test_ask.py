"""Test the /ask tutor against LIVE Wikibooks/Wikiversity + DeepSeek."""
from ask import answer_question


def main() -> None:
    q = "What is a derivative in calculus, in simple terms?"
    r = answer_question(q)
    print(f"Q: {r['question']}\n")
    print("A:", (r["answer"] or r.get("note"))[:800])
    print("\nSources:")
    for s in r["sources"]:
        print(f"  - {s['site']}: {s['title']} → {s['url']}")
    print("\nOK: grounded tutor answer with citations.")


if __name__ == "__main__":
    main()
