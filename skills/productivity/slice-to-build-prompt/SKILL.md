---
name: slice-to-build-prompt
description: Turn an approved MVP slice into a Cursor or Claude Code prompt. Does not push code.
version: 1.0.0
author: Max Infeld
license: MIT
metadata:
  hermes:
    tags: [Build, Cursor, Claude]
    related_skills: [meeting-to-mvp-slice, github-from-slice]
---

# Slice to build prompt

## When to Use

The user says implement the slice, or the slice file is marked approved.

## Procedure

1. Refuse if match status is unresolved unless the user overrides.
2. Put 2 or 3 verbatim quotes at the top.
3. Paste the slice. Instruct the builder to implement only in-scope items, match the quotes, and stop if the transcript and the spec conflict.
4. Hand the prompt to Cursor or Claude Code. Shipping to GitHub is `github-from-slice`, not this skill.

## Verification

Prompt contains quotes, in scope, and out of scope. No extra features.
