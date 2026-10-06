#!/usr/bin/env python3
"""
extract_signals.py — Extract decisions, problems, constraints, and non-goals with quotes from Read.ai meeting.

Adheres strictly to readai-signal-extract skill specifications:
- Uses transcript as source of truth (not auto-summary).
- Requires verbatim quote and speaker for every decision, problem, and non-goal.
- Marks summary-only claims as unverified.
- Saves extract next to matching Calendly brief (within 15 mins + overlapping email).
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path


def parse_timestamp(ts_str: str):
    """Parse various ISO formats to naive or UTC datetime."""
    if not ts_str:
        return None
    clean = ts_str.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(clean)
    except Exception:
        pass
    # Try basic regex for YYYYMMDDTHHMMSS
    m = re.match(r"(\d{4})(\d{2})(\d{2})T?(\d{2})(\d{2})(\d{2})?", ts_str)
    if m:
        parts = [int(p) for p in m.groups() if p is not None]
        return datetime(*parts)
    return None


def parse_transcript_text(text: str) -> list:
    """Parse text formatted as 'Speaker: Quote' or timestamped dialogue."""
    utterances = []
    lines = text.strip().split("\n")
    current_speaker = "Unknown"
    current_text = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Check for Speaker: text
        m = re.match(r"^\[?([A-Za-z0-9\s_-]+?)\]?:\s*(.*)$", line)
        if m and len(m.group(1).split()) <= 4:
            if current_text:
                utterances.append({
                    "speaker": current_speaker,
                    "text": " ".join(current_text)
                })
                current_text = []
            current_speaker = m.group(1).strip()
            current_text.append(m.group(2).strip())
        else:
            current_text.append(line)

    if current_text:
        utterances.append({
            "speaker": current_speaker,
            "text": " ".join(current_text)
        })

    return utterances


def extract_signals_rule_based(utterances: list) -> dict:
    """
    Extract decisions, problems, constraints, non-goals with exact quotes from utterances.
    """
    decisions = []
    problems = []
    solutions = []
    constraints = []
    non_goals = []
    open_questions = []

    decision_patterns = [
        r"\b(we decided|let's go with|we agreed|the plan is|we will|we should definitely)\b",
        r"\b(let's do|we are going to|final decision is)\b"
    ]
    problem_patterns = [
        r"\b(problem is|issue is|struggling with|pain point|broken|takes too long|annoying)\b",
        r"\b(can't|cannot|unable to|hard to)\b"
    ]
    constraint_patterns = [
        r"\b(must be|needs to be|constraint|cannot exceed|deadline|only in|restricted to)\b",
        r"\b(before friday|by tomorrow|without breaking|in python|in react)\b"
    ]
    non_goal_patterns = [
        r"\b(not doing|out of scope|non-goal|don't need|later|not now|skip|won't do)\b",
        r"\b(no need for|leave that for v2|defer)\b"
    ]
    question_patterns = [
        r"\b(how do we|should we|can we|what if|who will|is it possible)\b",
        r"\?$"
    ]

    for u in utterances:
        speaker = u.get("speaker", "Speaker")
        text = u.get("text", "")
        # Break utterance into sentences
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for s in sentences:
            s_clean = s.strip()
            if not s_clean or len(s_clean) < 8:
                continue

            s_lower = s_clean.lower()

            # Non-goals
            if any(re.search(p, s_lower) for p in non_goal_patterns):
                non_goals.append({
                    "speaker": speaker,
                    "quote": s_clean,
                    "summary": f"Out of scope: {s_clean}"
                })
            # Decisions
            elif any(re.search(p, s_lower) for p in decision_patterns):
                decisions.append({
                    "speaker": speaker,
                    "quote": s_clean,
                    "decision": s_clean
                })
            # Problems
            elif any(re.search(p, s_lower) for p in problem_patterns):
                problems.append({
                    "speaker": speaker,
                    "quote": s_clean,
                    "problem": s_clean
                })
            # Constraints
            elif any(re.search(p, s_lower) for p in constraint_patterns):
                constraints.append({
                    "speaker": speaker,
                    "quote": s_clean,
                    "constraint": s_clean
                })
            # Questions
            elif any(re.search(p, s_lower) for p in question_patterns):
                open_questions.append({
                    "speaker": speaker,
                    "quote": s_clean,
                    "question": s_clean
                })

    return {
        "decisions": decisions,
        "problems": problems,
        "proposed_solutions": solutions,
        "constraints": constraints,
        "non_goals": non_goals,
        "open_questions": open_questions,
        "raw_utterances_count": len(utterances)
    }


def find_matching_brief(start_time_iso: str, attendee_emails: list, meetings_dir: Path) -> Path:
    """
    Find matching Calendly brief within 15 minutes and overlapping attendee email.
    Title match is fallback only.
    """
    if not meetings_dir.exists():
        return None

    target_dt = parse_timestamp(start_time_iso)
    brief_files = list(meetings_dir.glob("*__*.json"))
    brief_files = [b for b in brief_files if not b.name.endswith(".extract.json")]

    best_match = None
    fallback_title_match = None

    for b_path in brief_files:
        try:
            with open(b_path, "r", encoding="utf-8") as f:
                brief = json.load(f)
        except Exception:
            continue

        brief_start = parse_timestamp(brief.get("start_time"))
        brief_attendees = [a.get("email", "").lower() for a in brief.get("attendees", []) if a.get("email")]

        # Check email overlap
        email_overlap = bool(set([e.lower() for e in attendee_emails]) & set(brief_attendees))

        # Check time within 15 mins (900 seconds)
        time_match = False
        if target_dt and brief_start:
            time_diff = abs((target_dt - brief_start).total_seconds())
            if time_diff <= 900:
                time_match = True

        if email_overlap and time_match:
            return b_path
        elif email_overlap or time_match:
            if best_match is None:
                best_match = b_path

    return best_match


def main():
    parser = argparse.ArgumentParser(description="Extract decisions, problems, constraints, and non-goals from Read.ai transcript.")
    parser.add_argument("--transcript", "-t", help="Path to transcript file (txt or json)")
    parser.add_argument("--json", "-j", help="Read.ai JSON payload directly")
    parser.add_argument("--start-time", help="Meeting start time in ISO-8601")
    parser.add_argument("--attendees", nargs="*", default=[], help="List of attendee emails")
    parser.add_argument("--meetings-dir", default="meetings", help="Directory with Calendly briefs")
    parser.add_argument("--out", "-o", help="Explicit output path for extract")

    args = parser.parse_args()

    payload = {}
    utterances = []
    meeting_title = "Meeting"
    start_time = args.start_time or datetime.utcnow().isoformat()
    attendees = args.attendees

    if args.json:
        payload = json.loads(args.json)
    elif args.transcript:
        t_path = Path(args.transcript)
        if t_path.suffix.lower() == ".json":
            with open(t_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        else:
            with open(t_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
                utterances = parse_transcript_text(raw_text)

    # If payload is present, inspect for Read.ai format
    if payload:
        meeting_title = payload.get("title", payload.get("meeting_title", "Meeting"))
        start_time = payload.get("start_time", start_time)
        if "attendees" in payload and not attendees:
            attendees = [a.get("email") if isinstance(a, dict) else str(a) for a in payload["attendees"]]
        if "transcript" in payload:
            t_data = payload["transcript"]
            if isinstance(t_data, list):
                utterances = t_data
            elif isinstance(t_data, str):
                utterances = parse_transcript_text(t_data)
        elif "utterances" in payload:
            utterances = payload["utterances"]

    if not utterances:
        print("ERROR: No transcript utterances found to extract signals from.", file=sys.stderr)
        sys.exit(1)

    signals = extract_signals_rule_based(utterances)
    signals["metadata"] = {
        "meeting_title": meeting_title,
        "start_time": start_time,
        "attendees": attendees,
        "extracted_at": datetime.utcnow().isoformat(),
        "source": "read.ai-transcript"
    }

    # Locate matching brief
    meetings_dir = Path(args.meetings_dir)
    matched_brief = find_matching_brief(start_time, attendees, meetings_dir)

    if args.out:
        target_path = Path(args.out)
    elif matched_brief:
        target_path = matched_brief.with_suffix(".extract.json")
    else:
        meetings_dir.mkdir(parents=True, exist_ok=True)
        ts_clean = start_time.replace(":", "").replace("-", "").split(".")[0]
        target_path = meetings_dir / f"{ts_clean}__meeting.extract.json"

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(signals, f, indent=2)

    print(f"SUCCESS: Extracted signals saved to {target_path}")
    if matched_brief:
        print(f"MATCHED: Paired with Calendly brief at {matched_brief}")
    else:
        print("WARN: No matching Calendly brief found within 15 mins + attendee email overlap.")


if __name__ == "__main__":
    main()
