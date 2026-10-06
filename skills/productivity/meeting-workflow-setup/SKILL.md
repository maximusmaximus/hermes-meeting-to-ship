---
name: meeting-workflow-setup
description: Request and verify Calendly, Read.ai, and GitHub before the meeting-to-ship workflow runs.
version: 1.0.0
author: Max Infeld
license: MIT
metadata:
  hermes:
    tags: [Meetings, Calendly, ReadAI, GitHub, Setup]
    related_skills: [calendly-meeting-intent, readai-signal-extract, meeting-to-mvp-slice, github-from-slice]
required_environment_variables:
  - name: CALENDLY_TOKEN
    prompt: Calendly personal access token
    help: Create at https://calendly.com/integrations/api_webhooks (Integrations > API & Webhooks). Webhooks need a paid plan.
    required_for: pulling booking objectives and tags
  - name: READ_API_TOKEN
    prompt: Read.ai API token, fallback if MCP OAuth is not connected
    help: Prefer MCP OAuth at https://api.read.ai/mcp. Token is the fallback. Enable Downloads in workspace settings.
    required_for: transcript extract when MCP is unavailable
  - name: GITHUB_TOKEN
    prompt: GitHub token only if gh auth status is not already logged in
    help: Prefer gh auth login -s repo. Classic scope repo covers private repo create, push, and pull requests. Do not request delete_repo.
    required_for: creating a repo or opening a pull request
---

# Meeting workflow setup

Gate for the meeting-to-ship pack. Do not extract, cut a slice, create a repo, or open a pull request until the checks below pass or the user explicitly overrides with a pasted brief and transcript.

## When to Use

- First run of this pack.
- Any later skill reports a missing credential.
- The user asks to connect Calendly, Read.ai, or GitHub for this workflow.

## Procedure

1. On a messaging gateway, do not collect secrets in chat. Tell the user to run `/meeting-workflow-setup` in the local CLI. Missing `required_environment_variables` prompt there and land in `~/.hermes/.env`.
2. Calendly: `GET https://api.calendly.com/users/me` with `Authorization: Bearer $CALENDLY_TOKEN`. Stop on 401 and name the missing token. Also ask the user to add invitee questions: Meeting objective (required, multiple lines), Tags (checkboxes), Product area (dropdown), Constraints, Decision needed. Ask for an `invitee.created` webhook if they want automatic briefs. Calendly has no native tag field.
3. Read.ai: prefer MCP.

```bash
hermes mcp add read-ai --url https://api.read.ai/mcp --auth oauth
hermes mcp test read-ai
```

Then `/reload-mcp`. If OAuth is missing, accept `READ_API_TOKEN` as fallback and say which path was used. Ask them to enable Downloads in Workspace Settings.
4. GitHub: run `skills/productivity/github-from-slice/scripts/check_github.sh` logic. Require `gh auth status` and classic scope `repo`, or fine-grained Contents write, Pull requests write, and Administration for repo create. A 403 or missing `gh` stops shipping only. It does not block writing the one-page slice.
5. Write `meetings/integrations.json` with calendly, read_ai, and github status. Do not write token values.

## Pitfalls

- Do not invent a Calendly MCP. There is not an official one.
- Do not treat event type name as the objective.
- Do not request `delete_repo`.

## Verification

Checklist printed with pass or fail for each integration, and `meetings/integrations.json` written without secrets.
