# hermes-meeting-to-ship

Hermes Agent skills that turn a Calendly booking plus a Read.ai transcript into a scoped MVP slice, then a GitHub repo or pull request.

The booked objective is the hypothesis. The transcript is the evidence. The agent does not cut a slice from either side alone, and it does not create a repo or open a PR until GitHub permissions are checked.

## Install

Copy `skills/` into `~/.hermes/skills/`, or point Hermes at this repo.

```bash
mkdir -p ~/.hermes/skills
cp -R skills/* ~/.hermes/skills/
```

Then in a local Hermes CLI session:

```text
/meeting-workflow-setup
```

Messaging sessions will not collect tokens in chat. Set secrets in the local CLI so they land in `~/.hermes/.env`.

## Skills

| Skill | Role |
| --- | --- |
| `meeting-workflow-setup` | Requests Calendly, Read.ai, and GitHub. Stops if a required check fails. |
| `calendly-meeting-intent` | Normalizes booking objectives and tags into a brief. |
| `readai-signal-extract` | Extracts decisions, problems, constraints, and non-goals with quotes. |
| `meeting-to-mvp-slice` | Joins brief to extract and writes one thin slice, or a delta for an update. |
| `slice-to-build-prompt` | Emits a Cursor or Claude Code prompt from an approved slice. |
| `github-from-slice` | Creates a private-by-default repo or opens a PR after the scope check. Loads the bundled `github` skill. |

## Integrations the setup skill requests

- Calendly personal access token: Integrations, API and Webhooks. Invitee questions: Meeting objective (required), Tags, Product area, Constraints, Decision needed. `invitee.created` webhook needs a paid plan.
- Read.ai MCP: `hermes mcp add read-ai --url https://api.read.ai/mcp --auth oauth` then `/reload-mcp`. Fallback `READ_API_TOKEN`. Enable Downloads in workspace settings.
- GitHub: `gh auth status` and classic scope `repo`. Fine-grained needs Contents write, Pull requests write, and Administration to create a repo. Never push to `main`.

No tokens belong in this repo.
