# Fail closed unless gh is authenticated and can create repos / open PRs.
$ErrorActionPreference = "Stop"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Host "FAIL: gh CLI is not installed. Install GitHub CLI, then gh auth login -s repo" -ForegroundColor Red
    exit 1
}

$authCheck = & gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL: gh is not logged in. Run: gh auth login -s repo" -ForegroundColor Red
    exit 1
}

$login = (& gh api user --jq .login)
Write-Host "OK: authenticated as $login" -ForegroundColor Green

$headers = (& gh api -i user 2>$null)
$scopeLine = $headers | Where-Object { $_ -match "^[Xx]-[Oo]auth-[Ss]copes:\s*(.*)$" } | Select-Object -First 1

if ($scopeLine -match "^[Xx]-[Oo]auth-[Ss]copes:\s*(.*)$") {
    $scopes = $Matches[1].Trim()
} else {
    $scopes = ""
}

if ($scopes) {
    Write-Host "SCOPES: $scopes"
} else {
    Write-Host "SCOPES: <none, likely fine-grained token>"
}

if ($scopes -match "(^|\s|,)repo(\s|,|$)") {
    Write-Host "OK: classic scope repo present (repo create, push, pull requests)" -ForegroundColor Green
    exit 0
}

if (-not $scopes) {
    Write-Host "WARN: no classic X-OAuth-Scopes. Fine-grained tokens need Contents write, Pull requests write, and Administration to create a repo." -ForegroundColor Yellow
    Write-Host "Probe with a user-approved call. Do not create a repo on 403."
    exit 2
}

Write-Host "FAIL: classic token is missing repo scope. Re-login: gh auth login -s repo" -ForegroundColor Red
exit 1
