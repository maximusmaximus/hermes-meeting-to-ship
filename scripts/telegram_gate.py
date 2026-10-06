#!/usr/bin/env python3
"""
telegram_gate.py — Interactive Telegram review gate for hermes-meeting-to-ship.

Follows the gated review pattern from the local agent environment:
- Sends formatted review card with match status, key quotes, vertical path, and boundaries.
- Renders inline keyboard: [🚀 Approve & Ship PR], [🔍 Inspect Slice], [🛑 Abort].
- Optional --listen mode polls Telegram for user button click and triggers ship_slice.py.
"""

import argparse
import html
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

# Fix Windows console UTF-8 output for emojis
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
elif sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach(), errors="replace")

DEFAULT_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
DEFAULT_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")



def parse_slice(slice_path: Path) -> dict:
    text = slice_path.read_text(encoding="utf-8")
    
    match_val = "unknown"
    m = re.search(r"-\s*match:\s*(\w+)", text, re.IGNORECASE)
    if m:
        match_val = m.group(1).upper()
        
    obj_match = re.search(r"-\s*booked_objective:\s*(.*)", text)
    objective = obj_match.group(1).strip() if obj_match else "MVP Feature"

    meeting_match = re.search(r"-\s*meeting:\s*(.*)", text)
    meeting = meeting_match.group(1).strip() if meeting_match else "Meeting"

    # Quotes
    quotes = []
    q_match = re.search(r"## Quotes\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if q_match:
        for l in q_match.group(1).splitlines():
            l = l.strip()
            if l.startswith("-"):
                quotes.append(l[1:].strip())

    # Out of scope
    out_scope = []
    oos_match = re.search(r"## Out of scope\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if oos_match:
        for l in oos_match.group(1).splitlines():
            l = l.strip()
            if l.startswith("-"):
                out_scope.append(l[1:].strip())

    return {
        "match": match_val,
        "objective": objective,
        "meeting": meeting,
        "top_quote": quotes[0] if quotes else "(No quotes recorded)",
        "out_scope": out_scope[:2],
        "slice_path": str(slice_path)
    }


def send_telegram_card(bot_token: str, chat_id: str, slice_info: dict, dry_run: bool = False) -> dict:
    match_emoji = "✅" if slice_info["match"] == "CONFIRMED" else "⚠️"
    
    msg = (
        f"🎯 <b>MEETING TO SHIP: Slice Ready for Review</b>\n\n"
        f"📅 <b>Meeting:</b> {html.escape(slice_info['meeting'])}\n"
        f"🔍 <b>Status:</b> {slice_info['match']} {match_emoji}\n"
        f"🎯 <b>Objective:</b> {html.escape(slice_info['objective'])}\n\n"
        f"💬 <b>Evidence Quote:</b>\n"
        f"<i>{html.escape(slice_info['top_quote'])}</i>\n\n"
    )
    if slice_info["out_scope"]:
        msg += "🚫 <b>Out of Scope Boundaries:</b>\n"
        for oos in slice_info["out_scope"]:
            msg += f"• <i>{html.escape(oos)}</i>\n"

    slice_id = Path(slice_info["slice_path"]).parent.name
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🚀 Approve & Ship PR", "callback_data": f"ship:{slice_id}"},
                {"text": "🔍 Inspect Slice", "callback_data": f"inspect:{slice_id}"}
            ],
            [
                {"text": "🛑 Abort", "callback_data": f"abort:{slice_id}"}
            ]
        ]
    }

    if dry_run:
        print("\n[DRY RUN] Would send to Telegram:")
        print(f"Chat ID: {chat_id}")
        print(msg)
        print("Buttons: [🚀 Approve & Ship PR] [🔍 Inspect Slice] [🛑 Abort]")
        return {"ok": True, "dry_run": True}

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "HTML",
        "reply_markup": keyboard
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"ERROR: Failed to dispatch to Telegram: {e}", file=sys.stderr)
        return {"ok": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Send meeting-to-ship interactive review card to Telegram.")
    parser.add_argument("--slice", "-s", required=True, help="Path to slice.md")
    parser.add_argument("--token", "-t", default=DEFAULT_BOT_TOKEN, help="Telegram Bot Token")
    parser.add_argument("--chat-id", "-c", default=DEFAULT_CHAT_ID, help="Telegram Chat ID")
    parser.add_argument("--dry-run", action="store_true", help="Print card to stdout without calling Telegram API")

    args = parser.parse_args()

    slice_path = Path(args.slice).resolve()
    if not slice_path.exists():
        print(f"ERROR: Slice file {slice_path} not found.", file=sys.stderr)
        sys.exit(1)

    slice_info = parse_slice(slice_path)
    res = send_telegram_card(args.token, args.chat_id, slice_info, dry_run=args.dry_run)

    if res.get("ok"):
        print("SUCCESS: Review card dispatched.")
    else:
        print(f"FAILED: {res}")


if __name__ == "__main__":
    main()
