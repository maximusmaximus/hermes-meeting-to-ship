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

## Skills & Scripts

| Skill | Role | Executable Script |
| --- | --- | --- |
| `meeting-workflow-setup` | Requests Calendly, Read.ai, and GitHub. Stops if a required check fails. | `verify_setup.py` |
| `calendly-meeting-intent` | Normalizes booking objectives and tags into a brief. | `parse_calendly.py` |
| `readai-signal-extract` | Extracts decisions, problems, constraints, and non-goals with quotes. | `extract_signals.py` |
| `meeting-to-mvp-slice` | Joins brief to extract and writes one thin slice, or a delta for an update. | `generate_slice.py` |
| `slice-to-build-prompt` | Emits a Cursor, Claude Code, or Antigravity prompt from an approved slice. | `compile_build_prompt.py` |
| `github-from-slice` | Creates a private-by-default repo or opens a PR after the scope check. | `ship_slice.py`, `check_github.sh`, `check_github.ps1` |

## Pipeline Execution

Run the complete pipeline end-to-end via `orchestrator.py`:

```bash
# Full dry-run simulation
python scripts/orchestrator.py --calendly booking.json --transcript meeting.txt --dry-run

# Run against existing brief and extract with Telegram review gate
python scripts/orchestrator.py --brief meetings/20261006T180000Z__alice.json

# Ship approved slice directly to a GitHub pull request in an existing repository
python skills/productivity/github-from-slice/scripts/ship_slice.py \
  --slice meetings/20261006T180000Z__alice/slice.md \
  --repo-dir path/to/repo
```

## Telegram Interactive Review Gate

Before shipping code or opening a PR, the review gate dispatches an interactive card with inline buttons directly to your Telegram chat (`chat_id: $TELEGRAM_CHAT_ID`):

```bash
python scripts/telegram_gate.py --slice meetings/<id>/slice.md
```

Buttons:
- `[🚀 Approve & Ship PR]` — Executes the build prompt and opens a GitHub PR.
- `[🔍 Inspect Slice]` — Displays the full Markdown slice.
- `[🛑 Abort]` — Cancels deployment.

## Integrations the setup skill requests

- Calendly personal access token: Integrations, API and Webhooks. Invitee questions: Meeting objective (required), Tags, Product area, Constraints, Decision needed. `invitee.created` webhook needs a paid plan.
- Read.ai MCP: `hermes mcp add read-ai --url https://api.read.ai/mcp --auth oauth` then `/reload-mcp`. Fallback `READ_API_TOKEN`. Enable Downloads in workspace settings.
- GitHub: `gh auth status` and classic scope `repo`. Fine-grained needs Contents write, Pull requests write, and Administration to create a repo. Never push to `main`. Cross-platform checks supported via `check_github.sh` and `check_github.ps1`.

No tokens belong in this repo.

