---
name: github-from-slice
description: Create a repo or open a pull request from an approved MVP slice after GitHub permissions are checked.
version: 1.0.0
author: Max Infeld
license: MIT
metadata:
  hermes:
    tags: [GitHub, PR, Repo]
    related_skills: [github, meeting-to-mvp-slice, meeting-workflow-setup]
---

# GitHub from slice

Uses the bundled Hermes `github` skill at `skills/software-development/github`. Do not reimplement `gh`. Read `references/auth.md` first, then `references/repo-management.md` or `references/pr-workflow.md`.

## When to Use

An approved slice should become a new repository or a pull request.

## Procedure

1. Run `scripts/check_github.sh`. If it fails, stop and ask for `gh auth login -s repo`. Do not create or push.
2. Classic token: `X-OAuth-Scopes` must include `repo`. Add `workflow` only if the commit adds Actions files. Add `read:org` only for an organization. Do not request `delete_repo`.
3. Fine-grained token: Contents write, Pull requests write, and Administration to create a repo. A 403 stops the skill and names the missing permission.
4. No repo yet: ask once for the name. Default private unless the user said public. `gh repo create OWNER/NAME --private --clone --description "..."`, then branch `feat/<slice>` and open a PR. An empty repo is not the finished artifact.
5. Existing repo: branch from the default branch, commit only slice-scoped files, `gh pr create` with quotes and acceptance criteria. Never push to `main` or `master`. Never merge.
6. One repo per confirmed slice. Tags do not become repos. Multiple repos only if the slice explicitly split services.

## Pitfalls

A missing GitHub scope does not block the one-page slice. It blocks the repo and the PR.

## Verification

`gh auth status` succeeded, scope check passed, and the PR URL is returned. No direct push to the default branch.
