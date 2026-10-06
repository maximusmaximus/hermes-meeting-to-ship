#!/usr/bin/env python3
"""
parse_calendly.py — Normalize Calendly booking payload into a pre-meeting brief.

Adheres strictly to calendly-meeting-intent skill specifications:
- Maps questions mentioning objective, goal, agenda to `objective`.
- Maps tags/product/area questions + event type + utm_campaign to `tags[]`.
- Leaves objective null if unanswered; never invents one.
- Outputs meetings/<iso-start>__<email-slug>.json.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text)


def normalize_iso(dt_str: str) -> str:
    """Normalize ISO-8601 string to filesystem-safe string YYYY-MM-DDTHHMMSSZ."""
    dt_str = dt_str.replace(":", "").replace("-", "")
    return dt_str.split(".")[0]


def extract_brief_from_payload(payload: dict) -> dict:
    """Extract standard brief from Calendly webhook payload or event JSON."""
    event_payload = payload.get("payload", payload)
    
    # Extract invitee details
    email = ""
    name = ""
    if "email" in event_payload:
        email = event_payload.get("email", "")
        name = event_payload.get("name", "")
    elif "invitee" in event_payload:
        email = event_payload["invitee"].get("email", "")
        name = event_payload["invitee"].get("name", "")
    
    # Event metadata
    event_uri = event_payload.get("event") or event_payload.get("uri", "")
    event_name = event_payload.get("event_type_name") or event_payload.get("name", "Meeting")
    start_time = event_payload.get("start_time") or event_payload.get("scheduled_event", {}).get("start_time", "")
    
    q_and_a = event_payload.get("questions_and_answers", [])
    tracking = event_payload.get("tracking", {})
    
    objective = None
    tags = []
    constraints = []
    decision_needed = None
    product_area = None
    
    # Always include event type name as a tag (not the objective!)
    if event_name:
        tags.append(event_name)
    
    # Include UTM campaign if present
    utm_campaign = tracking.get("utm_campaign")
    if utm_campaign:
        tags.append(utm_campaign)
        
    for item in q_and_a:
        question = item.get("question", "").lower()
        answer = item.get("answer")
        if not answer:
            continue
            
        if any(keyword in question for keyword in ["objective", "goal", "agenda", "hypothesis"]):
            objective = answer.strip()
        elif any(keyword in question for keyword in ["tag", "tags"]):
            # Split tags by comma or newline if string
            if isinstance(answer, list):
                tags.extend([str(t).strip() for t in answer if str(t).strip()])
            elif isinstance(answer, str):
                tags.extend([t.strip() for t in re.split(r"[,;\n]", answer) if t.strip()])
        elif any(keyword in question for keyword in ["product area", "area", "module"]):
            product_area = answer.strip()
            tags.append(product_area)
        elif "constraint" in question:
            constraints.append(answer.strip())
        elif "decision" in question:
            decision_needed = answer.strip()
            
    # Deduplicate tags
    deduped_tags = []
    for t in tags:
        if t and t not in deduped_tags:
            deduped_tags.append(t)
            
    attendees = []
    if email:
        attendees.append({"name": name, "email": email, "role": "invitee"})
        
    brief = {
        "event_name": event_name,
        "calendly_uri": event_uri,
        "start_time": start_time,
        "attendees": attendees,
        "objective": objective,
        "tags": deduped_tags,
        "product_area": product_area,
        "constraints": constraints,
        "decision_needed": decision_needed,
        "source": "calendly"
    }
    return brief


def save_brief(brief: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    start_iso = brief.get("start_time") or datetime.utcnow().isoformat()
    clean_ts = normalize_iso(start_iso)
    
    invitee_email = "participant"
    if brief.get("attendees"):
        invitee_email = brief["attendees"][0].get("email", "participant").split("@")[0]
        
    slug = slugify(invitee_email)
    filename = f"{clean_ts}__{slug}.json"
    target_path = output_dir / filename
    
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(brief, f, indent=2)
        
    return target_path


def main():
    parser = argparse.ArgumentParser(description="Normalize Calendly booking payload to pre-meeting brief.")
    parser.add_argument("--input", "-i", help="Path to raw Calendly JSON file")
    parser.add_argument("--json", "-j", help="Raw JSON string")
    parser.add_argument("--outdir", "-o", default="meetings", help="Directory to save brief")
    
    args = parser.parse_args()
    
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            payload = json.load(f)
    elif args.json:
        payload = json.loads(args.json)
    elif not sys.stdin.isatty():
        payload = json.load(sys.stdin)
    else:
        parser.print_help()
        sys.exit(1)
        
    brief = extract_brief_from_payload(payload)
    saved_path = save_brief(brief, Path(args.outdir))
    print(f"SUCCESS: Saved Calendly brief to {saved_path}")
    print(json.dumps(brief, indent=2))


if __name__ == "__main__":
    main()
