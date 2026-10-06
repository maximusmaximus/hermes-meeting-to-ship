#!/usr/bin/env python3
"""
orchestrator.py — End-to-end execution pipeline for hermes-meeting-to-ship.

Orchestrates:
1. Verification Gate (verify_setup)
2. Calendly Intent Ingestion (parse_calendly)
3. Read.ai Signal Extraction (extract_signals)
4. Hypothesis vs Evidence Joiner (generate_slice)
5. Interactive Review Gate (telegram_gate)
6. Engineer Build Prompt Compilation (compile_build_prompt)
7. GitHub Shipping / PR Creation (ship_slice)
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Fix Windows console UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
elif sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach(), errors="replace")


ROOT_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT_DIR / "skills" / "productivity"


def run_step(cmd: list, desc: str) -> subprocess.CompletedProcess:
    print(f"\n========================================================")
    print(f"==> STEP: {desc}")
    print(f"    Running: {' '.join(cmd)}")
    print(f"========================================================")
    res = subprocess.run(cmd, text=True)
    if res.returncode != 0:
        print(f"\n[ABORT] Step '{desc}' failed with exit code {res.returncode}.", file=sys.stderr)
        sys.exit(res.returncode)
    return res


def main():
    parser = argparse.ArgumentParser(description="Run complete meeting-to-ship pipeline.")
    parser.add_argument("--calendly", "-c", help="Path to Calendly booking JSON payload")
    parser.add_argument("--transcript", "-t", help="Path to Read.ai transcript file (txt or json)")
    parser.add_argument("--brief", "-b", help="Existing Calendly brief path in meetings/")
    parser.add_argument("--extract", "-e", help="Existing Read.ai extract path in meetings/")
    parser.add_argument("--slice", "-s", help="Existing slice.md path")
    parser.add_argument("--repo-dir", "-r", help="Target git repo for PR (if modifying existing repo)")
    parser.add_argument("--repo-name", help="New private repo name (OWNER/NAME)")
    parser.add_argument("--auto-ship", action="store_true", help="Automatically ship to GitHub without manual wait")
    parser.add_argument("--dry-run", action="store_true", help="Simulate pipeline without modifying remote repos or sending messages")
    parser.add_argument("--skip-setup-check", action="store_true", help="Skip integration verification check")

    args = parser.parse_args()

    # Step 1: Verification Check
    if not args.skip_setup_check:
        verify_script = SKILLS_DIR / "meeting-workflow-setup" / "scripts" / "verify_setup.py"
        run_step([sys.executable, str(verify_script)], "Verify Integration Setup")

    # Step 2: Calendly Intent Ingestion
    brief_path = Path(args.brief) if args.brief else None
    if not brief_path and args.calendly:
        parse_script = SKILLS_DIR / "calendly-meeting-intent" / "scripts" / "parse_calendly.py"
        run_step([sys.executable, str(parse_script), "--input", args.calendly], "Normalize Calendly Booking Intent")
        # Find newest brief in meetings/
        briefs = sorted(list(Path("meetings").glob("*__*.json")), key=os.path.getmtime, reverse=True)
        briefs = [b for b in briefs if not b.name.endswith(".extract.json")]
        if briefs:
            brief_path = briefs[0]

    # Step 3: Read.ai Signal Extraction
    extract_path = Path(args.extract) if args.extract else None
    if not extract_path and args.transcript:
        extract_script = SKILLS_DIR / "readai-signal-extract" / "scripts" / "extract_signals.py"
        cmd = [sys.executable, str(extract_script), "--transcript", args.transcript]
        run_step(cmd, "Extract Verbatim Signals from Read.ai Transcript")
        if brief_path:
            extract_path = brief_path.with_suffix(".extract.json")

    # Step 4: Join Hypothesis & Evidence into MVP Slice
    slice_path = Path(args.slice) if args.slice else None
    if not slice_path:
        if not brief_path:
            print("ERROR: Neither --slice nor --brief/--calendly provided.", file=sys.stderr)
            sys.exit(1)
        gen_slice_script = SKILLS_DIR / "meeting-to-mvp-slice" / "scripts" / "generate_slice.py"
        cmd = [sys.executable, str(gen_slice_script), "--brief", str(brief_path)]
        if extract_path:
            cmd.extend(["--extract", str(extract_path)])
        run_step(cmd, "Join Intent with Evidence (Generate slice.md)")
        slice_path = brief_path.parent / brief_path.stem.replace(".json", "") / "slice.md"

    # Step 5: Telegram Review Gate
    tg_gate_script = ROOT_DIR / "scripts" / "telegram_gate.py"
    cmd = [sys.executable, str(tg_gate_script), "--slice", str(slice_path)]
    if args.dry_run:
        cmd.append("--dry-run")
    run_step(cmd, "Trigger Telegram Interactive Review Gate")

    # Step 6: Compile Build Prompt
    compile_script = SKILLS_DIR / "slice-to-build-prompt" / "scripts" / "compile_build_prompt.py"
    run_step([sys.executable, str(compile_script), "--slice", str(slice_path)], "Compile Engineer Build Prompt")

    # Step 7: Ship to GitHub
    ship_script = SKILLS_DIR / "github-from-slice" / "scripts" / "ship_slice.py"
    ship_cmd = [sys.executable, str(ship_script), "--slice", str(slice_path)]
    if args.repo_dir:
        ship_cmd.extend(["--repo-dir", args.repo_dir])
    if args.repo_name:
        ship_cmd.extend(["--repo-name", args.repo_name])
    if args.dry_run or not (args.auto_ship or args.repo_dir or args.repo_name):
        ship_cmd.append("--dry-run")

    run_step(ship_cmd, "Ship Slice to GitHub PR")

    print("\n========================================================")
    print(" PIPELINE COMPLETED SUCCESSFULLY! ")
    print(f" Slice: {slice_path}")
    print(f" Build Prompt: {slice_path.parent / 'build_prompt.md'}")
    print("========================================================\n")


if __name__ == "__main__":
    main()
