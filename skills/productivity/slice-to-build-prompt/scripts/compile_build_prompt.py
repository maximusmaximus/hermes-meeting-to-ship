#!/usr/bin/env python3
"""
compile_build_prompt.py — Turn an approved MVP slice into a Cursor, Claude Code, or Antigravity build prompt.

Adheres strictly to slice-to-build-prompt skill specifications:
- Refuses if match status is 'unresolved' unless forced.
- Places 2-3 verbatim quotes at the top.
- Enforces implementing only in-scope items.
- Strict negative constraints against out-of-scope creep.
"""

import argparse
import os
import re
import sys
from pathlib import Path


def parse_slice_md(content: str) -> dict:
    data = {
        "match": "unknown",
        "quotes": [],
        "in_scope": [],
        "out_of_scope": [],
        "acceptance": [],
        "regress": [],
        "assumptions": []
    }

    # Match status
    m = re.search(r"-\s*match:\s*(\w+)", content, re.IGNORECASE)
    if m:
        data["match"] = m.group(1).lower().strip()

    # Extract sections
    sections = re.split(r"^##\s+", content, flags=re.MULTILINE)
    for sec in sections:
        lines = sec.strip().split("\n")
        title = lines[0].strip().lower()
        items = [l.strip() for l in lines[1:] if l.strip().startswith("-")]

        if title == "quotes":
            data["quotes"] = [re.sub(r"^-\s*", "", it) for it in items]
        elif title == "in scope":
            data["in_scope"] = [re.sub(r"^-\s*", "", it) for it in items]
        elif title == "out of scope":
            data["out_of_scope"] = [re.sub(r"^-\s*", "", it) for it in items]
        elif title == "acceptance":
            data["acceptance"] = [re.sub(r"^-\s*", "", it) for it in items]
        elif title == "must not regress":
            data["regress"] = [re.sub(r"^-\s*", "", it) for it in items]
        elif title == "assumptions":
            data["assumptions"] = [re.sub(r"^-\s*", "", it) for it in items]

    return data


def generate_prompt(slice_content: str, parsed: dict) -> str:
    top_quotes = parsed["quotes"][:3]
    quote_block = "\n".join([f"> {q}" for q in top_quotes]) if top_quotes else "> (No quotes provided)"

    prompt = f"""# TASK: IMPLEMENT SCOPED MVP SLICE

You are an expert engineer implementing a scoped MVP vertical slice.

## EVIDENCE (VERBATIM TRANSCRIPT QUOTES)
{quote_block}

## MANDATES & CONSTRAINTS
1. **IMPLEMENT ONLY IN-SCOPE ITEMS**: Do not implement extra features, unrequested abstraction layers, or hypothetical future requirements.
2. **HONOR ALL QUOTES**: If your implementation conflicts with the verbatim quotes above, stop immediately.
3. **STRICT OUT-OF-SCOPE BOUNDARIES**: Anything listed under "Out of scope" is strictly prohibited.
4. **DO NOT BREAK EXISTING CONTRACTS**: Respect all "Must not regress" constraints.

---

## SLICE SPECIFICATION

{slice_content.strip()}

---

## IMPLEMENTATION INSTRUCTIONS
- Create or update the necessary files to make the slice fully functional.
- Ensure that tests verify the acceptance criteria.
- Produce clean, production-ready code with no placeholder stubs for in-scope items.
"""
    return prompt


def main():
    parser = argparse.ArgumentParser(description="Compile slice.md into an execution prompt.")
    parser.add_argument("--slice", "-s", required=True, help="Path to slice.md")
    parser.add_argument("--out", "-o", help="Path to write compiled build prompt")
    parser.add_argument("--force", action="store_true", help="Force build even if match status is unresolved")

    args = parser.parse_args()

    slice_path = Path(args.slice)
    if not slice_path.exists():
        print(f"ERROR: File {slice_path} not found.", file=sys.stderr)
        sys.exit(1)

    with open(slice_path, "r", encoding="utf-8") as f:
        content = f.read()

    parsed = parse_slice_md(content)

    if parsed["match"] == "unresolved" and not args.force:
        print("REFUSED: Slice match status is 'unresolved'. Divergence/conflicts require user review or --force override.", file=sys.stderr)
        sys.exit(1)

    prompt = generate_prompt(content, parsed)

    if args.out:
        out_path = Path(args.out)
    else:
        out_path = slice_path.parent / "build_prompt.md"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(prompt)

    print(f"SUCCESS: Build prompt compiled to {out_path}")


if __name__ == "__main__":
    main()
