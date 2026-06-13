"""GrantScribe — workforce-board-side pathway receipt verifier.

A WIOA workforce board / ETPL funder who receives a GrantScribe pathway plan can
verify that it names a real CareerOneStop ETPL training program at draft time,
without trusting the applicant:

    python verify_pathway.py --plan received_plan.txt              # offline
    python verify_pathway.py --plan received_plan.txt --live       # also re-fetch from CareerOneStop

Or pipe the plan via stdin:

    cat received_plan.txt | python verify_pathway.py

Offline checks:
- The pathway receipt block is present and well-formed.
- The receipt's `program_canonical_sha256` matches a recomputed hash over the
  receipt's own program identity fields (detail_id / program / school /
  credential / cip_code). Proves the identifiers haven't been internally tampered with.
- The `training_source` is CareerOneStop.

Live check (with `--live`):
- The program is re-fetched from CareerOneStop by DetailId.
- The canonical hash of the *live* record is recomputed and compared to the
  receipt's `program_canonical_sha256`. If they match, the receipt is anchored
  in the live CareerOneStop ETPL record at verification time.

Exit code 0 iff every check passes.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pathway_receipt import (
    parse_pathway_receipt,
    verify_pathway_receipt_live,
    verify_pathway_receipt_offline,
)


def _read_plan(path_or_dash: str | None) -> str:
    if path_or_dash and path_or_dash != "-":
        return Path(path_or_dash).read_text()
    return sys.stdin.read()


def _print_result(result: dict) -> None:
    overall = "PASS" if result["verified"] else "FAIL"
    print(f"\nReceipt verification: {overall}\n")
    for c in result["checks"]:
        mark = "✓" if c["passed"] else "✗"
        print(f"  {mark} {c['name']}")
        if c.get("detail"):
            print(f"      {c['detail']}")
    if result.get("note"):
        print(f"\nnote: {result['note']}")
    if result.get("live_program"):
        p = result["live_program"]
        print("\nLive CareerOneStop ETPL record at verification time:")
        print(f"  program:    {p.get('program')}")
        print(f"  school:     {p.get('school')}")
        print(f"  credential: {p.get('credential')}")
        print(f"  detail_id:  {p.get('detail_id')}")
        print(f"  location:   {', '.join(x for x in (p.get('city', ''), p.get('state', '')) if x)}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Verify a GrantScribe pathway receipt — workforce-board-side audit tool."
    )
    p.add_argument("--plan", help="Path to a file containing the pathway plan (with receipt block). Use '-' or omit to read from stdin.")
    p.add_argument("--live", action="store_true",
                   help="Also re-fetch the program from CareerOneStop and verify the canonical hash matches the live record.")
    args = p.parse_args(argv)

    text = _read_plan(args.plan)
    receipt = parse_pathway_receipt(text)
    if receipt is None:
        print("FAIL: no GRANTSCRIBE PATHWAY RECEIPT block found in input.", file=sys.stderr)
        print("      This plan does not carry a verifiable receipt; treat with the same trust", file=sys.stderr)
        print("      as any unsigned LLM-generated prose.", file=sys.stderr)
        return 2

    print("Parsed receipt:")
    for k, v in receipt.items():
        if k.startswith("_"):
            continue
        print(f"  {k}: {v}")

    result = verify_pathway_receipt_live(receipt) if args.live else verify_pathway_receipt_offline(receipt)
    _print_result(result)
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    sys.exit(main())
