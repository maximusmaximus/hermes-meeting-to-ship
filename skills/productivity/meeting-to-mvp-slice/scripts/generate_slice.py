#!/usr/bin/env python3
"""
generate_slice.py — Join Calendly booking hypothesis with Read.ai evidence into a 1-page MVP slice.

Adheres strictly to meeting-to-mvp-slice skill specifications and templates/slice.md:
- Requires both Calendly brief and Read.ai extract.
- Classifies match: confirmed | drifted | unresolved | never_discussed.
- Cites quotes for requirements; marks assumptions explicitly.
- Enforces single vertical slice with clear out-of-scope boundaries.
- Writes meetings/<id>/slice.md.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def evaluate_hypothesis_match(objective: str, extract: dict) -> tuple:
    """
    Compare booked objective (hypothesis) with transcript extract (evidence).
    Returns (status, explanation).
    """
    if not objective:
        return "never_discussed", "No booked objective provided in Calendly."

    decisions = extract.get("decisions", [])
    problems = extract.get("problems", [])
    all_evidence_text = " ".join([d.get("quote", "") for d in decisions + problems]).lower()

    obj_words = set(re.findall(r"\w{4,}", objective.lower()))
    if not obj_words:
        return "unresolved", "Objective lacked substantive keywords to match."

    matched_words = [w for w in obj_words if w in all_evidence_text]
    overlap_ratio = len(matched_words) / len(obj_words) if obj_words else 0

    if not decisions and not problems:
        return "never_discussed", "Transcript contains no recorded decisions or problems matching objective."

    if overlap_ratio >= 0.4:
        return "confirmed", f"Transcript quotes confirm booked objective ({', '.join(matched_words)})."
    elif decisions:
        return "drifted", f"Meeting made decisions, but diverged from booked objective ('{objective}')."
    else:
        return "unresolved", "Discussion touched on topics but reached no confirmed decision."


def build_slice_markdown(brief: dict, extract: dict, match_status: str, match_reason: str, kind: str = "mvp") -> str:
    objective = brief.get("objective") or "<none stated>"
    tags = brief.get("tags", [])
    meeting_title = extract.get("metadata", {}).get("meeting_title", brief.get("event_name", "Meeting"))
    start_time = brief.get("start_time", "")

    # Collect verbatim quotes
    quotes = []
    for d in extract.get("decisions", []):
        quotes.append(f'"{d["quote"]}" — {d.get("speaker", "Attendee")}')
    for p in extract.get("problems", []):
        quotes.append(f'"{p["quote"]}" — {p.get("speaker", "Attendee")}')
    for c in extract.get("constraints", []):
        quotes.append(f'"{c["quote"]}" — {c.get("speaker", "Attendee")}')
    for ng in extract.get("non_goals", []):
        quotes.append(f'"{ng["quote"]}" — {ng.get("speaker", "Attendee")}')

    # Limit to top 4 quotes
    selected_quotes = quotes[:4] if quotes else ['"<No explicit quotes recorded>"']

    # Path derivation
    primary_speaker = "User"
    if brief.get("attendees"):
        primary_speaker = brief["attendees"][0].get("name", "User")

    # In scope
    in_scope_items = []
    for d in extract.get("decisions", []):
        in_scope_items.append(f"- Implement: {d['quote']} (Quote: {d.get('speaker', 'Attendee')})")
    if not in_scope_items:
        in_scope_items.append(f"- Core objective: {objective} (Assumption: inferred from brief)")

    # Out of scope
    out_of_scope_items = []
    for ng in extract.get("non_goals", []):
        out_of_scope_items.append(f"- {ng['quote']} (Quote: {ng.get('speaker', 'Attendee')})")
    if not out_of_scope_items:
        out_of_scope_items.append("- Advanced configurations, multiple formats, or unrequested automations")

    # Constraints / Must not regress
    regress_items = []
    for c in extract.get("constraints", []):
        regress_items.append(f"- {c['quote']} (Quote: {c.get('speaker', 'Attendee')})")
    if not regress_items:
        regress_items.append("- Existing production routes and user workflows must remain unchanged")

    # Acceptance criteria
    acceptance_items = [
        "- Vertical flow operates end-to-end for the designated trigger and action",
        "- All out-of-scope boundaries are strictly respected"
    ]
    if extract.get("decisions"):
        acceptance_items.insert(0, f"- Verified delivery matching: \"{extract['decisions'][0]['quote']}\"")

    # Construct Markdown matching templates/slice.md
    tags_formatted = ", ".join(tags) if tags else "none"

    md = f"""# Slice

- kind: {kind}
- match: {match_status}
- match_explanation: {match_reason}
- booked_objective: {objective}
- tags: {tags_formatted}
- meeting: {meeting_title} ({start_time})

## Quotes

"""
    for q in selected_quotes:
        md += f"- {q}\n"

    md += f"""
## Path

- who: {primary_speaker}
- job: Accomplish stated objective without manual friction
- trigger: User clicks export / trigger in interface
- action: System processes request against current data
- outcome: Desired artifact is delivered directly

## In scope

"""
    for item in in_scope_items:
        md += f"{item}\n"

    md += """
## Out of scope

"""
    for item in out_of_scope_items:
        md += f"{item}\n"

    md += """
## Acceptance

"""
    for item in acceptance_items:
        md += f"{item}\n"

    md += """
## Must not regress

"""
    for item in regress_items:
        md += f"{item}\n"

    md += """
## Failure

- Unhandled exception, timeout, or missing required payload data triggers an explicit error state

## Assumptions

- Standard authentication and network availability
"""
    return md


def main():
    parser = argparse.ArgumentParser(description="Generate 1-page MVP slice from Calendly brief and Read.ai extract.")
    parser.add_argument("--brief", "-b", help="Path to Calendly brief JSON")
    parser.add_argument("--extract", "-e", help="Path to Read.ai extract JSON")
    parser.add_argument("--kind", choices=["mvp", "update"], default="mvp", help="Slice kind")
    parser.add_argument("--outdir", "-o", default=None, help="Output directory for slice.md")

    args = parser.parse_args()

    if not args.brief:
        print("ERROR: --brief path is required.", file=sys.stderr)
        sys.exit(1)

    brief_path = Path(args.brief)
    if not brief_path.exists():
        print(f"ERROR: Brief file {brief_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    with open(brief_path, "r", encoding="utf-8") as f:
        brief = json.load(f)

    # Locate extract if not provided
    extract_path = Path(args.extract) if args.extract else brief_path.with_suffix(".extract.json")
    if not extract_path.exists():
        print(f"ERROR: Missing Read.ai extract at {extract_path}. Cannot cut slice without evidence.", file=sys.stderr)
        sys.exit(1)

    with open(extract_path, "r", encoding="utf-8") as f:
        extract = json.load(f)

    match_status, match_reason = evaluate_hypothesis_match(brief.get("objective", ""), extract)

    slice_content = build_slice_markdown(brief, extract, match_status, match_reason, kind=args.kind)

    # Output directory: meetings/<id>/
    if args.outdir:
        meeting_dir = Path(args.outdir)
    else:
        meeting_dir = brief_path.parent / brief_path.stem.replace(".json", "")

    meeting_dir.mkdir(parents=True, exist_ok=True)
    slice_path = meeting_dir / "slice.md"

    with open(slice_path, "w", encoding="utf-8") as f:
        f.write(slice_content)

    print(f"SUCCESS: Generated MVP slice at {slice_path}")
    print(f"MATCH STATUS: {match_status.upper()} ({match_reason})")


if __name__ == "__main__":
    main()
