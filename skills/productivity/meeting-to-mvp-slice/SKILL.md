---
name: meeting-to-mvp-slice
description: Join Calendly objectives and tags with the Read.ai extract and write a one-page MVP or update slice.
version: 1.0.0
author: Max Infeld
license: MIT
metadata:
  hermes:
    tags: [MVP, PRD, Meetings]
    related_skills: [calendly-meeting-intent, readai-signal-extract, slice-to-build-prompt, github-from-slice]
---

# Meeting to MVP slice

## When to Use

Both the Calendly brief and the Read.ai extract exist, or the user asks to turn this meeting into an MVP or product update.

## Procedure

1. Join on start time plus or minus 15 minutes and an overlapping email. Title is fallback only. If either side is missing, stop and name it.
2. Treat Calendly objectives and tags as the booked hypothesis. Transcript quotes are evidence. If the meeting diverged, list the divergence first. Mark the objective confirmed, drifted, unresolved, or never discussed.
3. Tags limit the search. A tag is not a feature.
4. Greenfield output: user, job, one vertical slice (entry, action, outcome), in scope, out of scope, acceptance criteria, failure signal.
5. Update output: delta only, plus what must not regress.
6. Every requirement cites a quote or is marked assumption.
7. Write `meetings/<id>/slice.md`. Do not create a repo here.

## Pitfalls

Do not build the full feature list from booking tags. Do not detach a requirement from its quote.

## Verification

Slice is one path, out of scope is explicit, and the match status is stated.
