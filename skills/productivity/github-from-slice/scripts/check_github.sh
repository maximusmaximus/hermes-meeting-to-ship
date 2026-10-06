#!/usr/bin/env bash
# Fail closed unless gh is authenticated and can create repos / open PRs.
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "FAIL: gh CLI is not installed. Install GitHub CLI, then gh auth login -s repo"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "FAIL: gh is not logged in. Run: gh auth login -s repo"
  exit 1
fi

login=$(gh api user --jq .login)
echo "OK: authenticated as ${login}"

scopes=$(gh api -i user 2>/dev/null | awk 'BEGIN{IGNORECASE=1} /^x-oauth-scopes:/ {print; exit}')
echo "SCOPES: ${scopes:-<none, likely fine-grained token>}"

if echo "${scopes}" | grep -qi 'repo'; then
  echo "OK: classic scope repo present (repo create, push, pull requests)"
  exit 0
fi

if [ -z "${scopes}" ] || echo "${scopes}" | grep -qi 'x-oauth-scopes:[[:space:]]*$'; then
  echo "WARN: no classic X-OAuth-Scopes. Fine-grained tokens need Contents write, Pull requests write, and Administration to create a repo."
  echo "Probe with a user-approved call. Do not create a repo on 403."
  exit 2
fi

echo "FAIL: classic token is missing repo scope. Re-login: gh auth login -s repo"
exit 1
