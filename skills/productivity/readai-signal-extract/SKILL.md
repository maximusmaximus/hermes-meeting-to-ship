---
name: readai-signal-extract
description: Extract decisions, problems, constraints, and non-goals with quotes from a Read.ai meeting. Do not write a PRD.
version: 1.0.0
author: Max Infeld
license: MIT
metadata:
  hermes:
    tags: [ReadAI, Meetings, Decisions]
    related_skills: [meeting-workflow-setup, calendly-meeting-intent, meeting-to-mvp-slice]
required_environment_variables:
  - name: READ_API_TOKEN
    prompt: Read.ai API token fallback
    help: Prefer MCP at https://api.read.ai/mcp
    required_for: transcript extract when MCP is unavailable
---

# Read.ai signal extract

## When to Use

A Read.ai `meeting_end` webhook arrived, or the user points at a session id or report.

## Procedure

1. Prefer Read MCP `https://api.read.ai/mcp` (`list_meetings`, `get_meeting_by_id`). If OAuth fails, use `READ_API_TOKEN` or a downloaded transcript. Say which path was used.
2. Use the transcript, not the summary, as source of truth. Output decisions, problems in the speaker's words, proposed solutions kept separate, constraints, non-goals, and open questions. Each item needs a quote and speaker.
3. Save the extract next to the Calendly brief when start time is within 15 minutes and an attendee email overlaps. Title match is fallback only.

## Pitfalls

Do not promote the auto-summary into requirements. Do not write the slice in this skill.

## Verification

Every decision or non-goal has a quote. Summary-only claims are marked unverified.
